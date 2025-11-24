# Multilingual Voice RAG Bot - Quick Start Guide

## 🎯 What's New

Your Voice RAG Bot now supports **multilingual conversations** with automatic language detection and voice switching!

### Key Features
- 🌍 **Auto-detect language** from user speech (Gladia STT)
- 🔄 **Switch voices** automatically based on language
- 💬 **Respond in user's language** (GPT-4 multilingual)
- 🎤 **Support for 100+ languages** (English, Hindi, Odia, and more)

---

## 📋 Setup Checklist

### 1. Get API Keys

- [ ] **Gladia API Key** - Get from https://gladia.io
  - Sign up for free tier or paid plan
  - Copy API key from dashboard

- [ ] **Cartesia Voice IDs** - Get from https://docs.cartesia.ai/getting-started/available-voices
  - Browse available voices
  - Find voices for English, Hindi, Odia
  - Copy voice IDs

- [ ] **OpenAI API Key** - Already have this ✅

### 2. Configure Environment

Update your `.env` file:

```bash
# Gladia STT
GLADIA_API_KEY=your_gladia_key_here
GLADIA_REGION=eu-west

# Cartesia TTS
CARTESIA_API_KEY=your_cartesia_key_here
CARTESIA_VOICE_ID=your_default_voice_id

# Languages
SUPPORTED_LANGUAGES=en,hi,or
DEFAULT_LANGUAGE=en

# Voices per language
CARTESIA_VOICE_ID_EN=english_voice_id_here
CARTESIA_VOICE_ID_HI=hindi_voice_id_here
CARTESIA_VOICE_ID_OR=odia_voice_id_here
```

### 3. Install Dependencies

```bash
uv sync
```

This will install the Gladia package and all dependencies.

### 4. Run the Bot

```bash
uv run bot.py
```

Look for these startup messages:

```
🚀 Starting Multilingual Voice RAG Bot
🌍 Loading multilingual configuration...
  ✓ EN: voice-id...
  ✓ HI: voice-id...
  ✓ OR: voice-id...
🎤 Initializing Gladia STT...
   ✓ Gladia STT ready (languages: EN, HI, OR)
🔊 Initializing Cartesia TTS...
   ✓ Cartesia TTS ready
🌐 Initializing Language-Aware Voice Switcher...
   ✓ Language switcher ready
```

---

## 🧪 Testing

### Test 1: English Conversation

1. Connect to the bot
2. Say: "Tell me about Konark Sun Temple"
3. Check logs for: `🌍 Language detected: en`
4. Bot should respond in English

### Test 2: Hindi Conversation

1. Say: "कोणार्क सूर्य मंदिर के बारे में बताइए"
2. Check logs for: `🌍 Language detected: hi`
3. Check logs for: `🎤 Voice switched: en → hi`
4. Bot should respond in Hindi

### Test 3: Language Switching

1. Start in English: "Hello"
2. Switch to Hindi: "नमस्ते"
3. Check logs for voice switch
4. Bot should adapt immediately

---

## 📁 New Files

| File | Purpose |
|------|---------|
| `language_switcher.py` | Language detection & voice switching processor |
| `multilingual_config.py` | Configuration helper functions |
| `MULTILINGUAL_GUIDE.md` | Complete documentation (400+ lines) |
| `MULTILINGUAL_IMPLEMENTATION.md` | Implementation summary |
| `.env.example` | Updated with multilingual config |

---

## 🔧 Modified Files

| File | Changes |
|------|---------|
| `bot.py` | - Replaced Cartesia STT with Gladia STT<br>- Added language switcher to pipeline<br>- Updated system prompt for multilingual |
| `pyproject.toml` | - Added `gladia` to dependencies |
| `IMPROVEMENTS_CHECKLIST.md` | - Marked multilingual tasks as complete |

---

## 📊 Architecture Changes

### Before (Monolingual)
```
STT (Cartesia) → RAG → LLM → TTS (Cartesia)
```

### After (Multilingual)
```
STT (Gladia) → Language Switcher → RAG → LLM → TTS (Cartesia)
                     ↓
            Detects language & switches voice
```

---

## 🚨 Important Notes

### Gladia vs Cartesia STT

**Why we switched**:
- Gladia has built-in language detection
- Supports 100+ languages
- Better multilingual accuracy
- Returns language code with each transcription

**Cartesia TTS** is still used for speech output (just not for input anymore).

### Voice Quality

Make sure to:
- Choose native speaker voices for each language
- Test voice quality before deploying
- Consider accent, gender, age, tone
- Get feedback from native speakers

### Cost Considerations

- **Gladia STT**: ~$0.0001-0.0005 per second of audio
- **Cartesia TTS**: Same as before
- **OpenAI LLM**: Same as before (multilingual doesn't cost more)

---

## 📖 Documentation

- **Quick Start**: This file
- **Complete Guide**: `MULTILINGUAL_GUIDE.md` (architecture, troubleshooting, best practices)
- **Implementation**: `MULTILINGUAL_IMPLEMENTATION.md` (technical details)
- **Configuration**: `.env.example` (all settings explained)

---

## ❓ Troubleshooting

### Bot not detecting language?

1. Check `GLADIA_API_KEY` is set
2. Verify logs show Gladia initialization
3. Ensure `SUPPORTED_LANGUAGES` includes the language

### Voice not switching?

1. Check `CARTESIA_VOICE_ID_{LANG}` is set
2. Verify logs show language detection
3. Ensure `LanguageAwareVoiceSwitcher` is in pipeline

### LLM responding in wrong language?

1. Verify using GPT-4 (not GPT-3.5)
2. Check system prompt includes language instructions
3. Ensure conversation context is maintained

---

## 🎉 You're Ready!

Your multilingual Voice RAG Bot is now configured and ready to use. Start testing with different languages and enjoy seamless multilingual conversations!

**Next Steps**:
1. Test with all supported languages
2. Get feedback from native speakers
3. Optimize voice selection
4. Add more languages as needed

---

**Questions?** Check `MULTILINGUAL_GUIDE.md` for detailed documentation.

**Issues?** Review logs for language detection and voice switching messages.
