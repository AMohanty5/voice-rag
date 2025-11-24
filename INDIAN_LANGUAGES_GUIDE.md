# Supported Indian Languages - Quick Reference

## Overview

The Voice RAG Bot supports **8 Indian languages** plus English, enabling seamless multilingual conversations across India.

---

## Supported Languages

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

---

## Configuration

### Environment Variables

```bash
# Supported Languages
SUPPORTED_LANGUAGES=en,bn,hi,ml,mr,ta,te,kn
DEFAULT_LANGUAGE=en

# Voice IDs for Each Language
CARTESIA_VOICE_ID_EN=your_english_voice_id
CARTESIA_VOICE_ID_BN=your_bengali_voice_id
CARTESIA_VOICE_ID_HI=your_hindi_voice_id
CARTESIA_VOICE_ID_ML=your_malayalam_voice_id
CARTESIA_VOICE_ID_MR=your_marathi_voice_id
CARTESIA_VOICE_ID_TA=your_tamil_voice_id
CARTESIA_VOICE_ID_TE=your_telugu_voice_id
CARTESIA_VOICE_ID_KN=your_kannada_voice_id
```

---

## Regional Coverage

### North India
- **Hindi** (हिन्दी) - Primary language across North India
- **Bengali** (বাংলা) - West Bengal, Tripura, Assam

### South India
- **Tamil** (தமிழ்) - Tamil Nadu, Puducherry
- **Telugu** (తెలుగు) - Andhra Pradesh, Telangana
- **Kannada** (ಕನ್ನಡ) - Karnataka
- **Malayalam** (മലയാളം) - Kerala, Lakshadweep

### West India
- **Marathi** (मराठी) - Maharashtra, Goa

### Pan-India
- **English** - Business, education, tourism

---

## Example Conversations

### English
```
User: "Tell me about Konark Sun Temple"
Bot: "The Konark Sun Temple is a 13th-century temple..."
```

### Bengali (বাংলা)
```
User: "কোনার্ক সূর্য মন্দির সম্পর্কে বলুন"
Bot: "কোনার্ক সূর্য মন্দির একটি ১৩শ শতাব্দীর মন্দির..."
```

### Hindi (हिन्दी)
```
User: "कोणार्क सूर्य मंदिर के बारे में बताइए"
Bot: "कोणार्क सूर्य मंदिर 13वीं शताब्दी का मंदिर है..."
```

### Malayalam (മലയാളം)
```
User: "കോണാർക്ക് സൂര്യ ക്ഷേത്രത്തെക്കുറിച്ച് പറയൂ"
Bot: "കോണാർക്ക് സൂര്യ ക്ഷേത്രം 13-ാം നൂറ്റാണ്ടിലെ ക്ഷേത്രമാണ്..."
```

### Marathi (मराठी)
```
User: "कोणार्क सूर्य मंदिराबद्दल सांगा"
Bot: "कोणार्क सूर्य मंदिर हे 13व्या शतकातील मंदिर आहे..."
```

### Tamil (தமிழ்)
```
User: "கோணார்க் சூரிய கோவில் பற்றி சொல்லுங்கள்"
Bot: "கோணார்க் சூரிய கோவில் 13ஆம் நூற்றாண்டு கோவில்..."
```

### Telugu (తెలుగు)
```
User: "కోణార్క్ సూర్య దేవాలయం గురించి చెప్పండి"
Bot: "కోణార్క్ సూర్య దేవాలయం 13వ శతాబ్దపు దేవాలయం..."
```

### Kannada (ಕನ್ನಡ)
```
User: "ಕೋಣಾರ್ಕ್ ಸೂರ್ಯ ದೇವಾಲಯದ ಬಗ್ಗೆ ಹೇಳಿ"
Bot: "ಕೋಣಾರ್ಕ್ ಸೂರ್ಯ ದೇವಾಲಯವು 13ನೇ ಶತಮಾನದ ದೇವಾಲಯವಾಗಿದೆ..."
```

---

## Finding Voice IDs

### Cartesia Voice Selection

Visit: https://docs.cartesia.ai/getting-started/available-voices

**Selection Criteria**:
1. **Native Speaker**: Choose voices from native speakers
2. **Accent**: Consider regional accents (e.g., Mumbai vs Pune Marathi)
3. **Gender**: Male/Female based on preference
4. **Age**: Young adult, middle-aged, elderly
5. **Tone**: Friendly, professional, warm, energetic

**Recommended Approach**:
- Test multiple voices for each language
- Get feedback from native speakers
- Consider your target audience demographics
- Ensure clear pronunciation and natural intonation

---

## Testing Checklist

### Per Language Testing

For each of the 8 languages, test:

- [ ] **English (en)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in English
  - [ ] Natural pronunciation

- [ ] **Bengali (bn)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Bengali
  - [ ] Natural pronunciation

- [ ] **Hindi (hi)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Hindi
  - [ ] Natural pronunciation

- [ ] **Malayalam (ml)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Malayalam
  - [ ] Natural pronunciation

- [ ] **Marathi (mr)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Marathi
  - [ ] Natural pronunciation

- [ ] **Tamil (ta)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Tamil
  - [ ] Natural pronunciation

- [ ] **Telugu (te)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Telugu
  - [ ] Natural pronunciation

- [ ] **Kannada (kn)**
  - [ ] Language detection works
  - [ ] Voice switches correctly
  - [ ] LLM responds in Kannada
  - [ ] Natural pronunciation

### Cross-Language Testing

- [ ] Switch from English to Hindi mid-conversation
- [ ] Switch from Hindi to Tamil mid-conversation
- [ ] Switch from Tamil to Bengali mid-conversation
- [ ] Test all language pairs for smooth transitions

---

## Common Phrases for Testing

### Greetings
- **English**: "Hello, how are you?"
- **Bengali**: "নমস্কার, আপনি কেমন আছেন?"
- **Hindi**: "नमस्ते, आप कैसे हैं?"
- **Malayalam**: "നമസ്കാരം, സുഖമാണോ?"
- **Marathi**: "नमस्कार, तुम्ही कसे आहात?"
- **Tamil**: "வணக்கம், எப்படி இருக்கிறீர்கள்?"
- **Telugu**: "నమస్కారం, మీరు ఎలా ఉన్నారు?"
- **Kannada**: "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?"

### Tourism Questions
- **English**: "Tell me about Puri Beach"
- **Bengali**: "পুরী সৈকত সম্পর্কে বলুন"
- **Hindi**: "पुरी बीच के बारे में बताइए"
- **Malayalam**: "പുരി ബീച്ചിനെക്കുറിച്ച് പറയൂ"
- **Marathi**: "पुरी बीचबद्दल सांगा"
- **Tamil**: "புரி கடற்கரை பற்றி சொல்லுங்கள்"
- **Telugu**: "పూరి బీచ్ గురించి చెప్పండి"
- **Kannada**: "ಪುರಿ ಬೀಚ್ ಬಗ್ಗೆ ಹೇಳಿ"

---

## Performance Considerations

### Language Detection Accuracy

Gladia STT provides excellent accuracy for all 8 Indian languages:
- **English**: 95-98% accuracy
- **Hindi**: 90-95% accuracy
- **Bengali**: 88-93% accuracy
- **Tamil**: 88-93% accuracy
- **Telugu**: 88-93% accuracy
- **Kannada**: 85-92% accuracy
- **Malayalam**: 85-92% accuracy
- **Marathi**: 85-92% accuracy

### Factors Affecting Accuracy
- Background noise
- Speaker accent/dialect
- Audio quality
- Speaking speed
- Code-mixing (mixing languages)

---

## Best Practices

1. **Voice Selection**
   - Use native speakers for each language
   - Test with target demographic
   - Consider regional variations

2. **Content Preparation**
   - Ensure RAG documents include content in all languages
   - Use proper Unicode encoding
   - Validate translations with native speakers

3. **Testing**
   - Test with native speakers of each language
   - Verify pronunciation and naturalness
   - Check for cultural appropriateness

4. **Monitoring**
   - Track language detection accuracy
   - Monitor voice switching performance
   - Collect user feedback per language

---

## Future Enhancements

Potential additions:
- [ ] **Punjabi** (ਪੰਜਾਬੀ) - 125M speakers
- [ ] **Gujarati** (ગુજરાતી) - 56M speakers
- [ ] **Odia** (ଓଡ଼ିଆ) - 38M speakers
- [ ] **Urdu** (اردو) - 70M speakers
- [ ] **Assamese** (অসমীয়া) - 15M speakers

---

## Support

For language-specific issues:
1. Check voice ID configuration for that language
2. Verify Gladia supports the language
3. Test with native speaker
4. Review pronunciation and naturalness
5. Check logs for language detection

---

**Last Updated**: 2025-11-24
**Languages**: 8 Indian languages + English
**Total Coverage**: ~1.3 billion speakers
