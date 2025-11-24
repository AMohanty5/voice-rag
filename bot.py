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
from pipecat.services.gladia import GladiaSTTService  # Speech-to-Text with language detection
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

# Metrics logging (custom)
from metrics_logger import MetricsLogger

# Multilingual support (custom)
from language_switcher import LanguageAwareVoiceSwitcher
from multilingual_config import (
    load_language_voice_mapping,
    get_multilingual_system_prompt,
    validate_multilingual_config
)

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
        context_aggregator.assistant()  # Adds assistant message to history
    """
    logger.info("=" * 80)
    logger.info("🚀 Starting Multilingual Voice RAG Bot")
    logger.info("   STT: Gladia | LLM: OpenAI GPT-4 | TTS: Cartesia")
    logger.info("=" * 80)

    # ========================================================================
    # Validate and Load Multilingual Configuration
    # ========================================================================
    
    logger.info("🌍 Loading multilingual configuration...")
    
    # Validate configuration before proceeding
    if not validate_multilingual_config():
        logger.error("❌ Configuration validation failed. Please check your .env file.")
        return
    
    # Load language-to-voice mappings
    language_to_voice, default_voice, default_language, supported_languages = load_language_voice_mapping()

    # ========================================================================
    # Initialize AI Services
    # ========================================================================
    
    # Speech-to-Text: Converts user's spoken words to text with language detection
    # Uses Gladia's multilingual STT service
    logger.info("🎤 Initializing Gladia STT...")
    stt = GladiaSTTService(
        api_key=os.getenv("GLADIA_API_KEY"),
        url=os.getenv("GLADIA_URL", "https://api.gladia.io/v2/live"),
        confidence=0.5,  # Minimum confidence threshold for transcriptions
        sample_rate=16000,  # Audio sample rate
        language=None,  # Auto-detect language (don't force a specific language)
        prosody=True,  # Enable prosody detection for better transcription
        language_behaviour="automatic multiple languages",  # Enable multilingual detection
    )
    logger.info(f"   ✓ Gladia STT ready (languages: {', '.join([l.upper() for l in supported_languages])})")

    # Text-to-Speech: Converts bot's text responses to natural speech
    # Voice will be switched dynamically based on detected language
    logger.info("🔊 Initializing Cartesia TTS...")
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=default_voice,  # Initial voice (will be switched by LanguageAwareVoiceSwitcher)
    )
    logger.info(f"   ✓ Cartesia TTS ready (default voice: {default_voice[:12]}...)")

    # Large Language Model: Generates intelligent responses
    # Using GPT-4 for high-quality, context-aware, multilingual answers
    logger.info("🧠 Initializing OpenAI LLM...")
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"  # GPT-4 Omni has excellent multilingual capabilities
    )
    logger.info("   ✓ OpenAI LLM ready (model: gpt-4o)")

    # ========================================================================
    # Initialize Conversation Context
    # ========================================================================
    
    # System message defines the bot's personality and multilingual behavior
    # This message is always present in the conversation history
    system_prompt = get_multilingual_system_prompt(default_language)
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
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
    # Initialize Language-Aware Voice Switcher
    # ========================================================================
    
    # LanguageAwareVoiceSwitcher detects language from STT and switches TTS voice
    # This enables seamless multilingual conversations
    logger.info("🌐 Initializing Language-Aware Voice Switcher...")
    language_switcher = LanguageAwareVoiceSwitcher(
        tts_service=tts,
        language_to_voice=language_to_voice,
        default_voice=default_voice,
        default_language=default_language
    )
    logger.info("   ✓ Language switcher ready")

    # ========================================================================
    # Initialize Metrics Logger
    # ========================================================================
    
    # MetricsLogger captures and logs comprehensive pipeline metrics
    # Tracks TTFB, processing time, token usage, character usage, etc.
    metrics_logger = MetricsLogger()

    # ========================================================================
    # Assemble the Processing Pipeline
    # ========================================================================
    
    # The pipeline is a linear sequence of processors
    # Each processor receives frames, processes them, and passes them downstream
    logger.info("🔧 Building multilingual pipeline...")
    pipeline = Pipeline([
        transport.input(),              # Audio input from user's microphone
        rtvi,                           # RTVI protocol handling
        stt,                            # Speech → Text conversion (Gladia with language detection)
        language_switcher,              # Language detection & voice switching
        rag_processor,                  # RAG context injection
        context_aggregator.user(),      # Add user message to history
        llm,                            # Generate AI response
        tts,                            # Text → Speech conversion (Cartesia with dynamic voice)
        transport.output(),             # Audio output to user's speaker
        context_aggregator.assistant(), # Add assistant message to history
        metrics_logger,                 # Capture and log all metrics
    ])
    logger.info("   ✓ Pipeline built successfully")

    # ========================================================================
    # Create Pipeline Task with Observers
    # ========================================================================
    
    # PipelineTask wraps the pipeline and manages its execution
    # Observers provide debugging, monitoring, and metrics
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,              # Track performance metrics (TTFB, processing time)
            enable_usage_metrics=True,        # Track API usage (tokens, characters, costs)
            report_only_initial_ttfb=True,    # Report only first TTFB for better performance
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