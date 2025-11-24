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
│  │   STT    │ →  │ Language │ →  │   RAG    │             │
│  │ (Gladia) │    │ Switcher │    │Processor │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                                        ↓                    │
│                  ┌──────────┐    ┌──────────┐             │
│                  │   TTS    │ ←  │   LLM    │             │
│                  │(Cartesia)│    │ (OpenAI) │             │
│                  └──────────┘    └──────────┘             │
│                        ↓                                     │
│                  ┌──────────┐                               │
│                  │ Grafana  │                               │
│                  │ Exporter │                               │
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
51: └─────────────────────────────────────────────────────────────┘
```

## File Structure

```
voice-llm/server/
├── bot.py                  # Main bot application
├── rag.py                  # RAG engine and processor
├── ingest.py               # Document ingestion script
├── metrics_logger.py       # Console metrics logger
├── grafana_metrics.py      # Grafana Cloud exporter (OpenTelemetry)
├── language_switcher.py    # Multilingual voice switcher
├── multilingual_config.py  # Multilingual configuration
├── check_grafana_config.py # Grafana config validator
├── pyproject.toml          # Python dependencies
├── .env                    # API keys (DO NOT COMMIT)
├── .env.example            # Template for environment variables
├── README.md               # This file
├── METRICS_GUIDE.md        # General metrics guide
├── MULTILINGUAL_GUIDE.md   # Multilingual support guide
├── GRAFANA_GUIDE.md        # Grafana integration guide
├── Odisha_Tourism/         # Knowledge base documents (.docx files)
└── chroma_db/              # Vector database (generated by ingest.py)
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
3. **STT**: Converts speech to text (Gladia - Auto Language Detection)
4. **Language Switcher**: Switches TTS voice based on detected language
5. **RAG Processor**: Retrieves and injects context
6. **Context Aggregator (User)**: Adds user message to history
7. **LLM**: Generates response (OpenAI GPT-4)
8. **TTS**: Converts text to speech (Cartesia - Dynamic Voice)
9. **Output**: Sends audio to user's speaker
10. **Context Aggregator (Assistant)**: Adds bot response to history
11. **Metrics Logger**: Captures performance metrics to console
12. **Grafana Exporter**: Sends metrics to Grafana Cloud

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

### 3. ingest.py - Document Ingestion

**Purpose**: Standalone script to populate the vector database.

**Process**:
1. Initialize `RAGEngine`
2. Call `ingest_documents("./Odisha_Tourism")`
3. Vector database persists to `./chroma_db`

**When to Run**:
- Before first bot startup
- After adding/updating documents in `Odisha_Tourism/`

## Features

### 🌍 Multilingual Support

The bot now supports seamless multilingual conversations with automatic language detection and voice switching.

- **Auto-Detection**: Uses Gladia STT to detect language from speech.
- **Dynamic Voice Switching**: Switches Cartesia TTS voice to match the user's language.
- **Multilingual LLM**: GPT-4 responds in the detected language.
- **Supported Languages**: English, Hindi, Odia, and 100+ others.

👉 **See [MULTILINGUAL_GUIDE.md](MULTILINGUAL_GUIDE.md) for details.**

### 📊 Grafana Cloud Integration

Real-time metrics monitoring using OpenTelemetry.

- **Performance**: Track TTFB and processing times.
- **Usage**: Monitor LLM tokens and TTS characters.
- **Cost**: Real-time cost estimation.
- **Dashboards**: Visualize metrics in Grafana Cloud.

👉 **See [GRAFANA_GUIDE.md](GRAFANA_GUIDE.md) for details.**

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Gladia (STT)
GLADIA_API_KEY=your_gladia_key
GLADIA_REGION=eu-west

# Cartesia (TTS)
CARTESIA_API_KEY=your_cartesia_key
CARTESIA_VOICE_ID=default_voice_id

# OpenAI (LLM and Embeddings)
OPENAI_API_KEY=sk-xxxxx

# Multilingual Settings
SUPPORTED_LANGUAGES=en,hi,or
DEFAULT_LANGUAGE=en
CARTESIA_VOICE_ID_EN=english_voice_id
CARTESIA_VOICE_ID_HI=hindi_voice_id
CARTESIA_VOICE_ID_OR=odia_voice_id

# Grafana Cloud (Metrics)
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-ap-south-1.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64_token>
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

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'pydantic'"**
- Solution: Run `uv sync` to install dependencies

**2. "HTTP 401" from Cartesia/Gladia**
- Solution: Check API keys in `.env`

**3. "No documents found to ingest"**
- Solution: Ensure `.docx` files exist in `Odisha_Tourism/`

**4. "Grafana authentication error"**
- Solution: Check `GRAFANA_GUIDE.md` for correct token format

### Debug Mode

Enable verbose logging:

```bash
# Set log level
export LOGURU_LEVEL=DEBUG

# Run bot
uv run bot.py
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
