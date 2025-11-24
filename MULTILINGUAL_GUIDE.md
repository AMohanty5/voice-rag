# Multilingual Voice RAG Bot - Complete Guide

This guide explains the multilingual capabilities of the Voice RAG Bot, including automatic language detection, voice switching, and configuration. It consolidates implementation details, setup instructions, and usage examples.

---

## 🎯 Overview

The bot supports **seamless multilingual conversations** with:
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

## 🏗️ Architecture

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

1. **Gladia STT Service**: Performs real-time speech-to-text and automatically detects the language (supports 100+ languages).
2. **LanguageAwareVoiceSwitcher**: Custom processor that monitors transcription frames and switches Cartesia TTS voice to match the detected language.
3. **Cartesia TTS Service**: Converts text responses to natural speech using dynamically switched voices.
4. **GPT-4 LLM**: Generates responses in the user's language, instructed by a multilingual-aware system prompt.

---

## ⚙️ Configuration

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

### Getting Voice IDs

1. **Sign up for Cartesia**: https://cartesia.ai
2. **Browse available voices**: https://docs.cartesia.ai/getting-started/available-voices
3. **Find voices** for your languages (native speakers recommended).
4. **Copy the voice IDs** and add them to your `.env` file.

---

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure API Keys

Update your `.env` file with Gladia API key, Cartesia API key, and Voice IDs.

### 3. Run the Bot

```bash
uv run bot.py
```

Check startup logs for:
```
🌍 Loading multilingual configuration...
  ✓ EN: voice-id-1...
  ✓ HI: voice-id-2...
```

---

## 💡 Usage Examples

### Example 1: Hindi Conversation

**User** (in Hindi): "कोणार्क सूर्य मंदिर के बारे में बताइए"

**Bot Response**:
- Gladia detects: `hi`
- Voice switches to: Hindi voice
- LLM responds in: Hindi
- User hears: Hindi speech about Konark

### Example 2: Language Switching Mid-Conversation

**User** (in Hindi): "नमस्ते, मुझे पुरी के बारे में बताओ"
- Bot responds in Hindi

**User** (switches to English): "What about the weather there?"
- Gladia detects language change to `en`
- Voice switches to English
- Bot responds in English

---

## 🔧 Implementation Details

### Language Detection Process

1. **User speaks** → Audio sent to Gladia
2. **Gladia analyzes** → Detects language from speech patterns
3. **Transcription returned** → Includes detected language code
4. **LanguageSwitcher processes** → Extracts language from frame
5. **Voice switched** → TTS voice updated to match language
6. **LLM generates response** → In the detected language
7. **Speech output** → Using the language-specific voice

### System Prompt

The bot uses a multilingual-aware system prompt:

```
CRITICAL LANGUAGE RULES:
1. ALWAYS respond in the EXACT SAME LANGUAGE as the user's most recent message
2. If the user switches languages mid-conversation, immediately switch to match
3. NEVER mix languages in your response
4. Default to English if language is unclear
```

---

## ❓ Troubleshooting

### Issue: Bot not detecting language
**Symptoms**: Always uses default language/voice
**Solutions**:
1. Check Gladia API key is correct.
2. Verify `language_behaviour="automatic multiple languages"` in STT config.
3. Check logs for language detection: `🌍 Language detected: xx`.

### Issue: Voice not switching
**Symptoms**: Language detected but voice stays the same
**Solutions**:
1. Check voice IDs are configured for detected language.
2. Verify `CARTESIA_VOICE_ID_{LANG}` format in `.env`.
3. Check logs for: `🎤 Voice switched: en → hi`.

### Issue: LLM responds in wrong language
**Symptoms**: LLM responds in English even when user speaks another language
**Solutions**:
1. Verify system prompt includes language matching instructions.
2. Check that GPT-4 (not GPT-3.5) is being used.
3. Ensure conversation context is being maintained.

---

## 📚 Best Practices

1. **Start with 2-3 languages**: Don't try to support everything at once.
2. **Test each language thoroughly**: Verify transcription and voice quality.
3. **Use native speakers**: For voice selection and testing.
4. **Monitor language detection accuracy**: Check logs regularly.

---

**Last Updated**: 2025-11-25

---

## 🇮🇳 Supported Indian Languages Reference

The bot is optimized for **8 Indian languages** plus English, enabling seamless multilingual conversations across India.

### Language Table

| Language | Code | Native Script | Speakers (millions) | Voice Config |
|----------|------|---------------|---------------------|--------------|
| **English** | `en` | English | ~125M (India) | `CARTESIA_VOICE_ID_EN` |
| **Bengali** | `bn` | বাংলা | ~265M | `CARTESIA_VOICE_ID_BN` |
| **Hindi** | `hi` | हिन्दी | ~600M | `CARTESIA_VOICE_ID_HI` |
| **Malayalam** | `ml` | മലയാളം | ~38M | `CARTESIA_VOICE_ID_ML` |
| **Marathi** | `mr` | मराठी | ~83M | `CARTESIA_VOICE_ID_MR` |
| **Tamil** | `ta` | தமிழ் | ~75M | `CARTESIA_VOICE_ID_TA` |
| **Telugu** | `te` | తెలుగు | ~82M | `CARTESIA_VOICE_ID_TE` |
| **Kannada** | `kn` | ಕನ್ನಡ | ~44M | `CARTESIA_VOICE_ID_KN` |

**Total Coverage**: ~1.3 billion speakers across India

### Regional Coverage

#### North India
- **Hindi** (हिन्दी) - Primary language across North India
- **Bengali** (বাংলা) - West Bengal, Tripura, Assam

#### South India
- **Tamil** (தமிழ்) - Tamil Nadu, Puducherry
- **Telugu** (తెలుగు) - Andhra Pradesh, Telangana
- **Kannada** (ಕನ್ನಡ) - Karnataka
- **Malayalam** (മലയാളം) - Kerala, Lakshadweep

#### West India
- **Marathi** (मराठी) - Maharashtra, Goa

#### Pan-India
- **English** - Business, education, tourism
