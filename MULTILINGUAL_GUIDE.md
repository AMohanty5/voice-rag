# Multilingual Voice RAG Bot - Complete Guide

This guide explains the multilingual capabilities of the Voice RAG Bot, including automatic language detection, voice switching, and configuration.

---

## Overview

The bot now supports **seamless multilingual conversations** with:
- ✅ **Automatic language detection** via Gladia STT
- ✅ **Dynamic voice switching** based on detected language
- ✅ **Multilingual responses** from GPT-4
- ✅ **Support for multiple languages** (English, Hindi, Odia, and more)
- ✅ **Mid-conversation language switching**

### How It Works

```
User speaks in Hindi → Gladia detects 'hi' → Switch to Hindi voice → LLM responds in Hindi
User switches to English → Gladia detects 'en' → Switch to English voice → LLM responds in English
```

---

## Architecture

### Pipeline Flow

```
Audio Input (User)
    ↓
STT (Gladia) - Detects language automatically
    ↓
Language Switcher - Switches TTS voice based on detected language
    ↓
RAG Processor - Retrieves context from vector DB
    ↓
LLM (GPT-4) - Generates response in user's language
    ↓
TTS (Cartesia) - Converts to speech using language-specific voice
    ↓
Audio Output (User hears response in their language)
```

### Key Components

1. **Gladia STT Service**
   - Performs real-time speech-to-text conversion
   - Automatically detects the language being spoken
   - Supports 100+ languages
   - Returns language code with each transcription

2. **LanguageAwareVoiceSwitcher**
   - Custom processor that sits between STT and RAG
   - Monitors transcription frames for language information
   - Switches Cartesia TTS voice to match detected language
   - Maintains language context throughout conversation

3. **Cartesia TTS Service**
   - Converts text responses to natural speech
   - Voice is dynamically switched based on language
   - Supports multiple voices per language

4. **GPT-4 LLM**
   - Generates responses in the user's language
   - System prompt instructs it to match user's language
   - Excellent multilingual capabilities

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Gladia STT Configuration
GLADIA_API_KEY=your_gladia_api_key_here
GLADIA_REGION=eu-west  # Options: eu-west, us-east

# Cartesia TTS Configuration
CARTESIA_API_KEY=your_cartesia_api_key_here
CARTESIA_VOICE_ID=default_voice_id  # Fallback voice

# Multilingual Settings
SUPPORTED_LANGUAGES=en,hi,or  # Comma-separated list
DEFAULT_LANGUAGE=en

# Language-Specific Voices
CARTESIA_VOICE_ID_EN=english_voice_id
CARTESIA_VOICE_ID_HI=hindi_voice_id
CARTESIA_VOICE_ID_OR=odia_voice_id
```

### Supported Languages

The bot can detect and respond in **any language supported by Gladia STT** (100+ languages). Common examples:

| Language | Code | Example Voice Config |
|----------|------|---------------------|
| English | `en` | `CARTESIA_VOICE_ID_EN` |
| Hindi | `hi` | `CARTESIA_VOICE_ID_HI` |
| Odia | `or` | `CARTESIA_VOICE_ID_OR` |
| Spanish | `es` | `CARTESIA_VOICE_ID_ES` |
| French | `fr` | `CARTESIA_VOICE_ID_FR` |
| German | `de` | `CARTESIA_VOICE_ID_DE` |
| Italian | `it` | `CARTESIA_VOICE_ID_IT` |
| Portuguese | `pt` | `CARTESIA_VOICE_ID_PT` |
| Japanese | `ja` | `CARTESIA_VOICE_ID_JA` |
| Chinese | `zh` | `CARTESIA_VOICE_ID_ZH` |

### Getting Voice IDs

1. **Sign up for Cartesia**: https://cartesia.ai
2. **Browse available voices**: https://docs.cartesia.ai/getting-started/available-voices
3. **Find voices for your languages**:
   - Look for native speakers of each language
   - Consider accent, gender, age, tone
4. **Copy the voice IDs** and add them to your `.env` file

---

## Setup Instructions

### 1. Install Dependencies

```bash
# Sync dependencies (includes Gladia support)
uv sync
```

### 2. Configure API Keys

Update your `.env` file with:
- Gladia API key (get from https://gladia.io)
- Cartesia API key (get from https://cartesia.ai)
- Voice IDs for each language you want to support

### 3. Test Configuration

```bash
# Run the bot
uv run bot.py
```

Check the startup logs for:
```
🌍 Loading multilingual configuration...
  ✓ EN: voice-id-1...
  ✓ HI: voice-id-2...
  ✓ OR: voice-id-3...
```

---

## Usage Examples

### Example 1: English Conversation

**User** (in English): "Tell me about Konark Sun Temple"

**Bot Response**:
- Gladia detects: `en`
- Voice switches to: English voice
- LLM responds in: English
- User hears: English speech about Konark

### Example 2: Hindi Conversation

**User** (in Hindi): "कोणार्क सूर्य मंदिर के बारे में बताइए"

**Bot Response**:
- Gladia detects: `hi`
- Voice switches to: Hindi voice
- LLM responds in: Hindi
- User hears: Hindi speech about Konark

### Example 3: Language Switching Mid-Conversation

**User** (in Hindi): "नमस्ते, मुझे पुरी के बारे में बताओ"
- Bot responds in Hindi

**User** (switches to English): "What about the weather there?"
- Gladia detects language change to `en`
- Voice switches to English
- Bot responds in English

**User** (switches to Odia): "ଧନ୍ୟବାଦ"
- Gladia detects `or`
- Voice switches to Odia
- Bot responds in Odia

---

## How Language Detection Works

### Gladia STT Configuration

```python
stt = GladiaSTTService(
    api_key=os.getenv("GLADIA_API_KEY"),
    url="https://api.gladia.io/v2/live",
    confidence=0.5,  # Minimum confidence threshold
    sample_rate=16000,
    language=None,  # Auto-detect (don't force a language)
    prosody=True,  # Better transcription quality
    language_behaviour="automatic multiple languages",  # Enable multilingual
)
```

### Language Detection Process

1. **User speaks** → Audio sent to Gladia
2. **Gladia analyzes** → Detects language from speech patterns
3. **Transcription returned** → Includes detected language code
4. **LanguageSwitcher processes** → Extracts language from frame
5. **Voice switched** → TTS voice updated to match language
6. **LLM generates response** → In the detected language
7. **Speech output** → Using the language-specific voice

---

## System Prompt

The bot uses a multilingual-aware system prompt:

```
You are a knowledgeable multilingual assistant for Odisha Tourism.

CRITICAL LANGUAGE RULES:
1. ALWAYS respond in the EXACT SAME LANGUAGE as the user's most recent message
2. If the user switches languages mid-conversation, immediately switch to match
3. NEVER mix languages in your response
4. NEVER continue in a previous language when the user has switched
5. Default to English if language is unclear

RESPONSE GUIDELINES:
- Use the provided context to answer questions about Odisha Tourism
- Keep answers concise and conversational (optimized for voice)
- If you don't know the answer, say so politely in the user's language
```

This ensures the LLM always responds in the user's language.

---

## Troubleshooting

### Issue: Bot not detecting language

**Symptoms**: Always uses default language/voice

**Solutions**:
1. Check Gladia API key is correct
2. Verify `language_behaviour="automatic multiple languages"` in STT config
3. Check logs for language detection: `🌍 Language detected: xx`
4. Ensure `language=None` (not forcing a specific language)

### Issue: Voice not switching

**Symptoms**: Language detected but voice stays the same

**Solutions**:
1. Check voice IDs are configured for detected language
2. Verify `CARTESIA_VOICE_ID_{LANG}` format in `.env`
3. Check logs for: `🎤 Voice switched: en → hi`
4. Ensure LanguageAwareVoiceSwitcher is in the pipeline

### Issue: LLM responds in wrong language

**Symptoms**: LLM responds in English even when user speaks another language

**Solutions**:
1. Verify system prompt includes language matching instructions
2. Check that GPT-4 (not GPT-3.5) is being used
3. Ensure conversation context is being maintained
4. Check that language is being passed to LLM context

### Issue: Poor transcription quality

**Symptoms**: Incorrect transcriptions, language misdetection

**Solutions**:
1. Increase `confidence` threshold in Gladia config
2. Ensure good audio quality (reduce background noise)
3. Check `sample_rate` matches your audio input
4. Enable `prosody=True` for better accuracy

---

## Advanced Configuration

### Custom Language Mappings

You can map multiple language codes to the same voice:

```python
# In multilingual_config.py
language_to_voice = {
    "en": "english_voice_id",
    "en-US": "english_voice_id",  # US English
    "en-GB": "british_voice_id",  # British English
    "hi": "hindi_voice_id",
    "hi-IN": "hindi_voice_id",  # Indian Hindi
}
```

### Fallback Behavior

If no voice is configured for a detected language:
1. Bot uses `CARTESIA_VOICE_ID` (default voice)
2. Warning is logged
3. Conversation continues (doesn't fail)

### Regional Variants

Handle regional language variants:

```bash
# In .env
CARTESIA_VOICE_ID_EN_US=american_voice_id
CARTESIA_VOICE_ID_EN_GB=british_voice_id
CARTESIA_VOICE_ID_ES_ES=spain_spanish_voice_id
CARTESIA_VOICE_ID_ES_MX=mexican_spanish_voice_id
```

---

## Performance Considerations

### Latency

Multilingual support adds minimal latency:
- Language detection: ~0ms (part of STT)
- Voice switching: ~10-20ms (one-time per language change)
- Total impact: Negligible

### Cost

- **Gladia STT**: Pay per minute of audio transcribed
- **Cartesia TTS**: Pay per character synthesized (same as before)
- **OpenAI LLM**: Same token costs (multilingual doesn't cost more)

### Optimization Tips

1. **Cache common responses** in each language
2. **Use shorter prompts** to reduce token usage
3. **Limit supported languages** to only what you need
4. **Use regional Gladia endpoints** for lower latency

---

## Testing

### Test Language Detection

```python
# Test script
import asyncio
from language_switcher import LanguageAwareVoiceSwitcher

async def test_language_detection():
    # Create mock TTS service
    class MockTTS:
        def set_voice(self, voice_id):
            print(f"Voice set to: {voice_id}")
    
    # Create switcher
    switcher = LanguageAwareVoiceSwitcher(
        tts_service=MockTTS(),
        language_to_voice={"en": "voice1", "hi": "voice2"},
        default_voice="voice1"
    )
    
    # Test language switching
    # (Create test frames and process them)
```

### Test Voice Switching

1. Start the bot
2. Speak in English → Check logs for `en` detection
3. Speak in Hindi → Check logs for `hi` detection and voice switch
4. Verify voice change in audio output

---

## Migration from Cartesia STT

If you're upgrading from Cartesia STT:

### Changes Made

1. **STT Service**: Cartesia → Gladia
2. **Pipeline**: Added `LanguageAwareVoiceSwitcher`
3. **System Prompt**: Updated for multilingual
4. **Configuration**: Added language/voice mappings

### Backward Compatibility

- TTS still uses Cartesia (no change)
- LLM still uses OpenAI (no change)
- RAG system unchanged
- Metrics system unchanged

### Migration Steps

1. Get Gladia API key
2. Update `.env` with new configuration
3. Run `uv sync` to install Gladia support
4. Test with English first (should work as before)
5. Add other languages incrementally

---

## Best Practices

1. **Start with 2-3 languages** - Don't try to support everything at once
2. **Test each language thoroughly** - Verify transcription and voice quality
3. **Use native speakers** - For voice selection and testing
4. **Monitor language detection accuracy** - Check logs regularly
5. **Provide language hints** - In UI or initial greeting
6. **Handle edge cases** - Mixed language input, unclear speech
7. **Update RAG documents** - Include multilingual content

---

## Future Enhancements

Potential improvements:

- [ ] Language preference persistence (remember user's language)
- [ ] Manual language selection (override auto-detection)
- [ ] Multilingual RAG (search in multiple languages)
- [ ] Translation mode (user speaks X, bot responds in Y)
- [ ] Language confidence scores (show detection certainty)
- [ ] Accent detection (regional variants)
- [ ] Code-switching support (mixing languages in one sentence)

---

## Support

For issues or questions:
1. Check this guide
2. Review logs for language detection and voice switching
3. Test with Gladia API directly
4. Check Cartesia voice availability
5. Verify GPT-4 multilingual capabilities

---

**Last Updated**: 2025-11-24
**Version**: 1.0
