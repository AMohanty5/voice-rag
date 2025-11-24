7. **Audio Output**: User hears the response

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│                   (Browser WebRTC Client)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Transport Layer                            │
│         (SmallWebRTC or Daily.co)                           │
│  • Audio streaming                                          │
│  • Voice Activity Detection (VAD)                           │
│  • Turn-taking management                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Pipecat Pipeline                           │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │   STT    │ →  │   RAG    │ →  │   LLM    │             │
│  │(Cartesia)│    │Processor │    │ (OpenAI) │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                        ↓                                     │
│                  ┌──────────┐                               │
│                  │   TTS    │                               │
│                  │(Cartesia)│                               │
│                  └──────────┘                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   RAG System                                 │
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                │
│  │  ChromaDB    │ ←───→   │   OpenAI     │                │
│  │ Vector Store │         │  Embeddings  │                │
│  └──────────────┘         └──────────────┘                │
│         ↑                                                   │
│         │                                                   │
│  ┌──────────────┐                                          │
│  │   Odisha     │                                          │
│  │   Tourism    │                                          │
│  │  Documents   │                                          │
│  │   (.docx)    │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
voice-llm/server/
├── bot.py              # Main bot application
├── rag.py              # RAG engine and processor
├── ingest.py           # Document ingestion script
├── metrics_logger.py   # Custom metrics monitoring processor
├── pyproject.toml      # Python dependencies
├── .env                # API keys (DO NOT COMMIT)
├── .env.example        # Template for environment variables
├── README.md           # This file
├── METRICS_GUIDE.md    # Comprehensive metrics monitoring guide
├── Odisha_Tourism/     # Knowledge base documents (.docx files)
└── chroma_db/          # Vector database (generated by ingest.py)
```

## Core Components

### 1. bot.py - Main Application

**Purpose**: Orchestrates the entire voice bot pipeline.

**Key Functions**:
- `run_bot(transport)`: Sets up the processing pipeline
- `bot(runner_args)`: Initializes the transport layer

**Pipeline Stages**:
1. **Input**: Receives audio from user's microphone
2. **RTVI**: Handles WebRTC signaling
3. **STT**: Converts speech to text (Cartesia)
4. **RAG Processor**: Retrieves and injects context
5. **Context Aggregator (User)**: Adds user message to history
6. **LLM**: Generates response (OpenAI GPT-4)
7. **TTS**: Converts text to speech (Cartesia)
8. **Output**: Sends audio to user's speaker
9. **Context Aggregator (Assistant)**: Adds bot response to history
10. **Metrics Logger**: Captures performance and usage metrics

**Event Handlers**:
- `on_client_connected`: Greets user when they connect
- `on_client_disconnected`: Cleans up when user disconnects

### 2. rag.py - RAG System

**RAGEngine Class**:
- **Purpose**: Manages the vector database and document retrieval
- **Methods**:
  - `__init__()`: Initializes or loads ChromaDB
  - `ingest_documents(directory)`: Processes .docx files
  - `query(text, k=3)`: Retrieves k most relevant chunks

**Document Processing**:
1. Load .docx files using `Docx2txtLoader`
2. Split into chunks (1000 chars, 200 overlap)
3. Generate embeddings using OpenAI
4. Store in ChromaDB vector database

**RAGProcessor Class**:
- **Purpose**: Pipecat processor that injects RAG context
- **Flow**:
  1. Receives `TextFrame` with user's transcribed speech
  2. Queries `RAGEngine` for relevant context
  3. Injects context as system message
  4. Passes frame to LLM

**Key Design Decision**:
- Calls `super().process_frame()` first to handle control frames (StartFrame, etc.)
- Only processes `TextFrame` instances
- Injects context before LLM sees the user message

### 3. ingest.py - Document Ingestion

**Purpose**: Standalone script to populate the vector database.

**Process**:
1. Initialize `RAGEngine`
2. Call `ingest_documents("./Odisha_Tourism")`
3. Vector database persists to `./chroma_db`

**When to Run**:
- Before first bot startup
- After adding/updating documents in `Odisha_Tourism/`

## Data Flow

### Conversation Flow

```
1. User: "Tell me about Konark Sun Temple"
   ↓
2. STT: Converts to text "Tell me about Konark Sun Temple"
   ↓
3. RAG Processor:
   - Queries vector DB with "Tell me about Konark Sun Temple"
   - Retrieves 3 most relevant chunks about Konark
   - Injects as system message: "Use the following context: [chunks]"
   ↓
4. Context Aggregator:
   - Adds user message to conversation history
   ↓
5. LLM (OpenAI GPT-4):
   - Sees system prompt + RAG context + user message
   - Generates response using retrieved information
   ↓
6. TTS: Converts response to speech
   ↓
7. User hears: "The Konark Sun Temple is a 13th-century temple..."
```

### RAG Query Process

```
User Query: "Tell me about Konark"
     ↓
OpenAI Embeddings API
     ↓
Query Vector: [0.123, -0.456, 0.789, ...]
     ↓
ChromaDB Similarity Search
     ↓
Top 3 Chunks:
1. "The Konark Sun Temple is a 13th-century temple..."
2. "Located in Odisha, the temple is dedicated to..."
3. "The temple is a UNESCO World Heritage Site..."
     ↓
Concatenated Context
     ↓
Injected into LLM Conversation
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Cartesia (STT/TTS)
CARTESIA_API_KEY=sk_car_xxxxx
CARTESIA_VOICE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# OpenAI (LLM and Embeddings)
OPENAI_API_KEY=sk-xxxxx

# Daily.co (Optional, for cloud deployment)
DAILY_API_KEY=xxxxx
DAILY_SAMPLE_ROOM_URL=https://example.daily.co/room
```

### Transport Modes

**1. SmallWebRTC (Default)**
- Local browser-based WebRTC
- Runs on `http://localhost:7860`
- No cloud service required
- Best for development

**2. Daily.co**
- Cloud-based WebRTC
- Requires `DAILY_API_KEY`
- Provides shareable room URLs
- Best for production

### Metrics Monitoring

The bot includes comprehensive metrics monitoring to track performance and usage:

**Enabled Metrics**:
- ⏱️ **TTFB (Time to First Byte)**: Latency for LLM and TTS responses
- ⚙️ **Processing Time**: Duration of pipeline stages
- 🤖 **LLM Token Usage**: Prompt and completion tokens with cost estimates
- 🔊 **TTS Character Usage**: Characters converted to speech with costs
- 📊 **Smart Turn Prediction**: Conversation turn-taking data

**Configuration** (in `bot.py`):
```python
params=PipelineParams(
    enable_metrics=True,              # Performance metrics
    enable_usage_metrics=True,        # API usage tracking
    report_only_initial_ttfb=True,    # Optimized TTFB reporting
)
```

**Example Output**:
```
📊 TTFB Metric | Current: 245.32ms | Average: 230.15ms | Processor: OpenAILLMService
🤖 LLM Usage Metric | Prompt: 1250 tokens | Completion: 85 tokens | Est. Cost: $0.0425
🔊 TTS Usage Metric | Characters: 142 | Est. Cost: $0.0021
```

**For detailed information**, see [METRICS_GUIDE.md](METRICS_GUIDE.md) which covers:
- Complete list of captured metrics
- Customization options
- Integration with monitoring systems
- Cost tracking and optimization



## Setup Instructions

### 1. Install Dependencies

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 3. Ingest Documents

```bash
# Process Odisha Tourism documents
uv run ingest.py
```

This creates `./chroma_db` with embedded documents.

### 4. Run the Bot

```bash
# Start local WebRTC server
uv run bot.py

# Or use Daily.co
uv run bot.py --transport daily
```

### 5. Connect

- Open `http://localhost:7860/client` in your browser
- Allow microphone access
- Start speaking!

## API Usage

### Cartesia

**STT (Speech-to-Text)**:
- Real-time WebSocket connection
- Streams audio chunks
- Returns transcribed text

**TTS (Text-to-Speech)**:
- Converts text to natural speech
- Configurable voice via `CARTESIA_VOICE_ID`
- Streams audio back to client

### OpenAI

**Embeddings**:
- Model: `text-embedding-ada-002` (default)
- Used for: Document vectorization and query embedding
- Cost: ~$0.0001 per 1K tokens

**LLM**:
- Model: `gpt-4o`
- Used for: Generating conversational responses
- Cost: ~$0.03 per 1K tokens (input), ~$0.06 per 1K tokens (output)

### ChromaDB

**Vector Store**:
- Stores document embeddings locally
- Performs similarity search
- Persists to `./chroma_db` directory

## Performance Considerations

### Latency

Total latency breakdown:
- STT: ~100-300ms
- RAG Query: ~50-100ms
- LLM: ~500-1500ms (depends on response length)
- TTS: ~100-300ms

**Total**: ~750-2200ms from user stops speaking to bot starts speaking

### Optimization Tips

1. **Reduce chunk count**: Use `k=2` instead of `k=3` in RAG queries
2. **Use faster LLM**: Switch to `gpt-4o-mini` for lower latency
3. **Optimize chunking**: Adjust `chunk_size` and `chunk_overlap`
4. **Cache embeddings**: ChromaDB automatically caches

### Cost Estimation

For 100 conversations (avg 10 exchanges each):
- Embeddings: ~$0.10 (one-time ingestion)
- LLM: ~$30-50 (depends on response length)
- STT/TTS: ~$5-10 (Cartesia pricing)

**Total**: ~$35-60 per 1000 exchanges

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'pydantic'"**
- Solution: Run `uv sync` to install dependencies

**2. "HTTP 401" from Cartesia**
- Solution: Check `CARTESIA_API_KEY` in `.env`

**3. "No documents found to ingest"**
- Solution: Ensure `.docx` files exist in `Odisha_Tourism/`

**4. "RAGProcessor: Trying to process but StartFrame not received"**
- Solution: Ensure `RAGProcessor.process_frame()` calls `super().process_frame()`

**5. Empty RAG responses**
- Solution: Run `uv run ingest.py` to populate vector database

### Debug Mode

Enable verbose logging:

```bash
# Set log level
export LOGURU_LEVEL=DEBUG

# Run bot
uv run bot.py
```

## Extending the System

### Adding New Documents

1. Add `.docx` files to `Odisha_Tourism/`
2. Run `uv run ingest.py`
3. Restart bot

### Changing Voice

1. Get voice ID from Cartesia dashboard
2. Update `CARTESIA_VOICE_ID` in `.env`
3. Restart bot

### Using Different LLM

Replace in `bot.py`:

```python
# From:
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# To:
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"  # Faster, cheaper
)
```

### Customizing RAG

Adjust in `rag.py`:

```python
# Change chunk size
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Smaller chunks
    chunk_overlap=100    # Less overlap
)

# Change number of retrieved chunks
context_str = self.rag_engine.query(text, k=5)  # More context
```

## Security Notes

1. **Never commit `.env`**: Contains sensitive API keys
2. **Use `.gitignore`**: Ensure `.env` and `chroma_db/` are ignored
3. **Rotate keys**: Regularly rotate API keys
4. **Limit access**: Use environment-specific keys for dev/prod

## License

BSD 2-Clause License (see bot.py header)

## Support

For issues or questions:
1. Check this README
2. Review code comments in `bot.py`, `rag.py`, `ingest.py`
3. Check Pipecat documentation: https://docs.pipecat.ai
