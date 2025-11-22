#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
Voice RAG Bot - Pipecat-based Voice Agent with Retrieval-Augmented Generation

This is the main bot application that creates a voice-enabled AI assistant with
RAG capabilities for answering questions about Odisha Tourism.

Architecture Overview:
    User speaks → WebRTC/Daily → STT (Cartesia) → RAG Processor → LLM (OpenAI) → TTS (Cartesia) → User hears

The bot supports two transport modes:
1. SmallWebRTC: Local browser-based WebRTC (default, runs on localhost:7860)
2. Daily.co: Cloud-based WebRTC rooms for production deployment

Required AI Services:
- Cartesia: Speech-to-Text and Text-to-Speech
- OpenAI: Large Language Model (GPT-4)
- ChromaDB: Vector database for RAG (initialized via ingest.py)

Environment Variables Required:
- CARTESIA_API_KEY: API key for Cartesia STT/TTS
- CARTESIA_VOICE_ID: Voice ID for TTS output
- OPENAI_API_KEY: API key for OpenAI LLM and embeddings
- DAILY_API_KEY: (Optional) For Daily.co transport mode

Usage:
    uv run bot.py                    # Starts local WebRTC server on port 7860
    uv run bot.py --transport daily  # Uses Daily.co rooms instead

Before running:
    1. Run `uv run ingest.py` to populate the vector database
    2. Ensure all API keys are set in .env file
"""

# ============================================================================
# Imports
# ============================================================================

# Pipecat core components
from pipecat.audio.vad.silero import SileroVADAnalyzer  # Voice Activity Detection
from pipecat.runner.types import DailyRunnerArguments, SmallWebRTCRunnerArguments
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.runner.types import RunnerArguments
from pipecat.audio.vad.vad_analyzer import VADParams

# AI Services
from pipecat.services.cartesia.stt import CartesiaSTTService  # Speech-to-Text
from pipecat.services.cartesia.tts import CartesiaTTSService  # Text-to-Speech
from pipecat.services.openai.llm import OpenAILLMService      # Language Model

# Transports (WebRTC connections)
from pipecat.transports.daily.transport import DailyTransport, DailyParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

# Processors and Aggregators
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frameworks.rtvi import RTVIObserver, RTVIProcessor

# Frames
from pipecat.frames.frames import LLMRunFrame

# Observers (for debugging and monitoring)
from pipecat_tail.observer import TailObserver
from pipecat_whisker import WhiskerObserver

# RAG components (custom)
from rag import RAGEngine, RAGProcessor

# Utilities
from dotenv import load_dotenv
from loguru import logger
import os

# Load environment variables from .env file
# override=True ensures .env values take precedence over system environment
load_dotenv(override=True)


# ============================================================================
# Main Bot Logic
# ============================================================================

async def run_bot(transport: BaseTransport):
    """
    Initialize and run the voice bot pipeline.
    
    This function sets up the complete processing pipeline:
    1. Audio Input (microphone) → STT → Text
    2. Text → RAG Processor (retrieves context) → LLM Context
    3. LLM Context → OpenAI → Response Text
    4. Response Text → TTS → Audio Output (speaker)
    
    Args:
        transport: The transport layer (WebRTC connection) for audio I/O
    
    Pipeline Flow:
        transport.input()           # Receives audio from user's microphone
        ↓
        rtvi                        # RTVI protocol handler for client communication
        ↓
        stt                         # Converts speech to text (Cartesia)
        ↓
        rag_processor               # Queries vector DB and injects context
        ↓
        context_aggregator.user()   # Adds user message to conversation history
        ↓
        llm                         # Generates response (OpenAI GPT-4)
        ↓
        tts                         # Converts text to speech (Cartesia)
        ↓
        transport.output()          # Sends audio to user's speaker
        ↓
        context_aggregator.assistant()  # Adds assistant response to history
    """
    logger.info("Starting bot")

    # ========================================================================
    # Initialize AI Services
    # ========================================================================
    
    # Speech-to-Text: Converts user's spoken words to text
    # Uses Cartesia's real-time STT service
    stt = CartesiaSTTService(api_key=os.getenv("CARTESIA_API_KEY"))

    # Text-to-Speech: Converts bot's text responses to natural speech
    # voice_id determines the voice characteristics (accent, tone, etc.)
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=os.getenv("CARTESIA_VOICE_ID")
    )

    # Large Language Model: Generates intelligent responses
    # Using GPT-4 for high-quality, context-aware answers
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )

    # ========================================================================
    # Initialize Conversation Context
    # ========================================================================
    
    # System message defines the bot's personality and behavior
    # This message is always present in the conversation history
    messages = [
        {
            "role": "system",
            "content": "You are a knowledgeable assistant for Odisha Tourism. Use the provided context to answer questions. If you don't know the answer, say so politely.",
        },
    ]

    # LLMContext maintains the conversation history (messages)
    # This allows the LLM to have context about previous exchanges
    context = LLMContext(messages)
    
    # ContextAggregator manages adding user and assistant messages to context
    # It has two endpoints: user() and assistant() for the pipeline
    context_aggregator = LLMContextAggregatorPair(context)

    # ========================================================================
    # Initialize RAG System
    # ========================================================================
    
    # RAG Engine: Loads the vector database and handles similarity search
    # This connects to the ChromaDB instance populated by ingest.py
    rag_engine = RAGEngine()
    
    # RAG Processor: Sits in the pipeline and injects retrieved context
    # When it receives user text, it queries the vector DB and adds context
    # to the conversation before the LLM generates a response
    rag_processor = RAGProcessor(rag_engine, context)

    # ========================================================================
    # Initialize RTVI Protocol Handler
    # ========================================================================
    
    # RTVI (Real-Time Voice Inference) handles client-server communication
    # It manages the WebRTC signaling and control messages
    rtvi = RTVIProcessor()

    # ========================================================================
    # Assemble the Processing Pipeline
    # ========================================================================
    
    # The pipeline is a linear sequence of processors
    # Each processor receives frames, processes them, and passes them downstream
    pipeline = Pipeline([
        transport.input(),              # Audio input from user's microphone
        rtvi,                           # RTVI protocol handling
        stt,                            # Speech → Text conversion
        rag_processor,                  # RAG context injection
        context_aggregator.user(),      # Add user message to history
        llm,                            # Generate AI response
        tts,                            # Text → Speech conversion
        transport.output(),             # Audio output to user's speaker
        context_aggregator.assistant(), # Add assistant message to history
    ])

    # ========================================================================
    # Create Pipeline Task with Observers
    # ========================================================================
    
    # PipelineTask wraps the pipeline and manages its execution
    # Observers provide debugging, monitoring, and metrics
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,        # Track performance metrics
            enable_usage_metrics=True,  # Track API usage (tokens, costs)
        ),
        observers=[
            RTVIObserver(rtvi),         # RTVI protocol observer
            WhiskerObserver(pipeline),  # Pipecat Whisker debugging UI
            TailObserver(),             # Pipecat Tail logging observer
        ],
    )

    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """
        Called when a user connects to the bot.
        
        This handler:
        1. Logs the connection
        2. Adds a greeting instruction to the conversation
        3. Triggers the LLM to generate and speak the greeting
        
        The greeting is generated by the LLM based on the system prompt
        and the instruction "Say hello and briefly introduce yourself."
        """
        logger.info("Client connected")
        
        # Add a system message instructing the bot to greet the user
        messages.append({
            "role": "system", 
            "content": "Say hello and briefly introduce yourself."
        })
        
        # Queue an LLMRunFrame to trigger the LLM to process the greeting
        # This will cause the LLM to generate a response, which flows through
        # TTS and is spoken to the user
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """
        Called when a user disconnects from the bot.
        
        This handler:
        1. Logs the disconnection
        2. Cancels the pipeline task to clean up resources
        
        Cancelling the task stops all processors and releases resources
        like WebSocket connections, API clients, etc.
        """
        logger.info("Client disconnected")
        await task.cancel()

    # ========================================================================
    # Run the Pipeline
    # ========================================================================
    
    # PipelineRunner manages the asyncio event loop and task lifecycle
    # handle_sigint=False prevents the runner from handling Ctrl+C
    # (the main() function handles this instead)
    runner = PipelineRunner(handle_sigint=False)
    
    # Start the pipeline and run until the task completes or is cancelled
    await runner.run(task)


# ============================================================================
# Transport Initialization
# ============================================================================

async def bot(runner_args: RunnerArguments):
    """
    Initialize the transport layer and start the bot.
    
    This function acts as a router that selects the appropriate transport
    based on the runner arguments. It supports:
    
    1. DailyRunnerArguments: Uses Daily.co for cloud-based WebRTC
       - Requires DAILY_API_KEY
       - Suitable for production deployment
       - Provides room URLs that can be shared
    
    2. SmallWebRTCRunnerArguments: Uses local WebRTC server
       - No cloud service required
       - Runs on localhost:7860
       - Suitable for development and testing
    
    Args:
        runner_args: Runner arguments provided by the Pipecat CLI
                    Contains transport type and connection details
    
    The transport handles:
    - WebRTC peer connection establishment
    - Audio stream encoding/decoding
    - Network transmission
    - Voice Activity Detection (VAD)
    - Turn-taking analysis
    """
    transport = None
    
    # Pattern match on the runner arguments type to select transport
    match runner_args:
        case DailyRunnerArguments():
            # Daily.co transport for cloud-based WebRTC
            # Requires a room URL and authentication token
            transport = DailyTransport(
                runner_args.room_url,           # Daily.co room URL
                runner_args.token,              # Authentication token
                "Pipecat Bot",                  # Bot display name
                params=DailyParams(
                    audio_in_enabled=True,      # Enable microphone input
                    audio_out_enabled=True,     # Enable speaker output
                    # VAD detects when user stops speaking (0.2s silence)
                    vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
                    # Smart turn analyzer manages conversation flow
                    turn_analyzer=LocalSmartTurnAnalyzerV3(),
                ),
            )
            
        case SmallWebRTCRunnerArguments():
            # Local WebRTC transport for browser-based connections
            # Runs a web server on localhost:7860
            transport = SmallWebRTCTransport(
                webrtc_connection=runner_args.webrtc_connection,
                params=TransportParams(
                    audio_in_enabled=True,      # Enable microphone input
                    audio_out_enabled=True,     # Enable speaker output
                    # VAD detects when user stops speaking (0.2s silence)
                    vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
                    # Smart turn analyzer manages conversation flow
                    turn_analyzer=LocalSmartTurnAnalyzerV3(),
                )
            )
            
        case _:
            # Unsupported transport type
            logger.error(f"Unsupported runner arguments type: {type(runner_args)}")
            return

    # Start the bot with the initialized transport
    await run_bot(transport)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Import and run the Pipecat CLI main function
    # This handles:
    # - Command-line argument parsing
    # - Transport selection (--transport flag)
    # - Web server setup (for SmallWebRTC)
    # - Calling the bot() function with appropriate runner_args
    from pipecat.runner.run import main
    
    main()