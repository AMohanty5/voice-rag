"""
Multilingual Configuration Helper

This module provides utility functions to load and manage multilingual
configuration from environment variables, including:
- Supported languages
- Language-to-voice mappings for TTS
- Default language and voice settings
"""

import os
from typing import Dict, List, Tuple
from loguru import logger


def load_language_voice_mapping() -> Tuple[Dict[str, str], str, str, List[str]]:
    """
    Load language-to-voice mappings from environment variables.
    
    This function:
      1. Reads supported languages from SUPPORTED_LANGUAGES env var
      2. For each language, looks for CARTESIA_VOICE_ID_{LANG} env var
      3. Falls back to default voice if no mapping is found
    
    Environment Variables:
        SUPPORTED_LANGUAGES: Comma-separated list (e.g., "en,hi,or")
        DEFAULT_LANGUAGE: Default language code (e.g., "en")
        CARTESIA_VOICE_ID: Default voice ID
        CARTESIA_VOICE_ID_EN: English voice ID
        CARTESIA_VOICE_ID_HI: Hindi voice ID
        CARTESIA_VOICE_ID_OR: Odia voice ID
        ... (more languages as needed)
    
    Returns:
        tuple: (language_to_voice_dict, default_voice, default_language, supported_languages_list)
        
    Example:
        lang_map, default_voice, default_lang, langs = load_language_voice_mapping()
        # lang_map = {"en": "voice-id-1", "hi": "voice-id-2", "or": "voice-id-3"}
        # default_voice = "voice-id-1"
        # default_lang = "en"
        # langs = ["en", "hi", "or"]
    """
    # Parse comma-separated list of supported languages from env
    supported_languages_str = os.getenv("SUPPORTED_LANGUAGES", "en,bn,hi,ml,mr,ta,te,kn")
    supported_languages = [lang.strip().lower() for lang in supported_languages_str.split(",") if lang.strip()]
    
    # Get default language
    default_language = os.getenv("DEFAULT_LANGUAGE", "en").lower()
    
    # Get default voice ID (fallback for all languages)
    default_voice = os.getenv("CARTESIA_VOICE_ID", "")
    
    if not default_voice:
        logger.warning("⚠️  CARTESIA_VOICE_ID not set in .env - TTS may not work!")
    
    language_to_voice = {}
    missing_mappings = []
    
    logger.info("=" * 60)
    logger.info("🌍 Loading Multilingual Configuration")
    logger.info("=" * 60)
    
    # For each supported language, try to find its voice mapping
    for lang in supported_languages:
        # Try language-specific voice first (e.g., CARTESIA_VOICE_ID_EN)
        voice_key = f"CARTESIA_VOICE_ID_{lang.upper()}"
        voice_id = os.getenv(voice_key)
        
        if voice_id:
            # Found a specific voice for this language
            language_to_voice[lang] = voice_id
            logger.info(f"  ✓ {lang.upper()}: {voice_id[:12]}...")
        else:
            # No specific voice found, use default
            missing_mappings.append(lang)
            language_to_voice[lang] = default_voice
            logger.warning(f"  ⚠️  {lang.upper()}: No specific voice (using default)")
    
    # Log summary
    logger.info("=" * 60)
    logger.info(f"Supported Languages: {', '.join([l.upper() for l in supported_languages])}")
    logger.info(f"Default Language: {default_language.upper()}")
    logger.info(f"Default Voice: {default_voice[:12] if default_voice else 'NOT SET'}...")
    
    if missing_mappings:
        logger.warning(f"Missing voice mappings for: {', '.join([l.upper() for l in missing_mappings])}")
        logger.warning("Set CARTESIA_VOICE_ID_{LANG} in .env for language-specific voices")
    
    logger.info("=" * 60)
    
    return language_to_voice, default_voice, default_language, supported_languages


def get_multilingual_system_prompt(default_language: str = "en") -> str:
    """
    Generate a system prompt that instructs the LLM to respond in the user's language.
    
    Args:
        default_language: Default language code (e.g., "en")
        
    Returns:
        System prompt string for the LLM
    """
    language_names = {
        "en": "English",
        "bn": "Bengali",
        "hi": "Hindi",
        "ml": "Malayalam",
        "mr": "Marathi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        # Additional languages (if needed in future)
        "or": "Odia",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ja": "Japanese",
        "zh": "Chinese",
        "ko": "Korean",
        "ar": "Arabic",
        "ru": "Russian",
    }
    
    default_lang_name = language_names.get(default_language, default_language.upper())
    
    return f"""You are a knowledgeable multilingual assistant for Odisha Tourism.

CRITICAL LANGUAGE RULES:
1. ALWAYS respond in the EXACT SAME LANGUAGE as the user's most recent message
2. If the user switches languages mid-conversation, immediately switch to match their new language
3. NEVER mix languages in your response
4. NEVER continue in a previous language when the user has switched
5. Default to {default_lang_name} if language is unclear

RESPONSE GUIDELINES:
- Use the provided context to answer questions about Odisha Tourism
- Keep answers concise and conversational (optimized for voice)
- If you don't know the answer, say so politely in the user's language
- Provide helpful, accurate information about tourist destinations, culture, and travel tips

Remember: Language matching is CRITICAL for user experience!"""


def validate_multilingual_config() -> bool:
    """
    Validate that all required multilingual configuration is present.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    errors = []
    warnings = []
    
    # Check Gladia STT configuration
    if not os.getenv("GLADIA_API_KEY"):
        errors.append("GLADIA_API_KEY not set")
    
    gladia_region = os.getenv("GLADIA_REGION", "eu-west")
    if gladia_region not in ["eu-west", "us-east"]:
        warnings.append(f"GLADIA_REGION '{gladia_region}' may be invalid (use 'eu-west' or 'us-east')")
    
    # Check Cartesia TTS configuration
    if not os.getenv("CARTESIA_API_KEY"):
        errors.append("CARTESIA_API_KEY not set")
    
    if not os.getenv("CARTESIA_VOICE_ID"):
        warnings.append("CARTESIA_VOICE_ID not set (default voice)")
    
    # Check language configuration
    supported_languages = os.getenv("SUPPORTED_LANGUAGES", "")
    if not supported_languages:
        warnings.append("SUPPORTED_LANGUAGES not set (defaulting to en,hi,or)")
    
    # Check OpenAI configuration (for LLM and embeddings)
    if not os.getenv("OPENAI_API_KEY"):
        errors.append("OPENAI_API_KEY not set")
    
    # Log results
    if errors:
        logger.error("❌ Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    if warnings:
        logger.warning("⚠️  Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("✅ Multilingual configuration validated")
    return True
