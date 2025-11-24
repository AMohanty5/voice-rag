"""
Language-Aware Voice Switcher - Automatic Language Detection and TTS Voice Switching

This module provides a custom FrameProcessor that:
1. Detects the language of user speech from STT transcriptions
2. Automatically switches the TTS voice to match the detected language
3. Ensures responses are in the same language as the user's input

The processor sits between STT and LLM in the pipeline and:
- Ignores interim (partial) transcription frames
- Processes only final transcription frames
- Extracts detected language from Gladia STT
- Switches Cartesia TTS voice accordingly
- Passes transcription to LLM for response generation
"""

from pipecat.frames.frames import Frame, TranscriptionFrame, InterimTranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from loguru import logger
from typing import Dict, Optional


class LanguageAwareVoiceSwitcher(FrameProcessor):
    """
    A frame processor that detects the language of user speech and switches
    the TTS voice accordingly for multilingual conversations.
    
    This processor enables seamless multilingual conversations by:
    1. Monitoring transcription frames from STT
    2. Extracting the detected language
    3. Switching the TTS voice to match the language
    4. Maintaining language context for the conversation
    
    Example:
        User speaks in Hindi → Gladia detects 'hi' → Switch to Hindi voice
        User switches to English → Gladia detects 'en' → Switch to English voice
    """
    
    def __init__(
        self,
        tts_service,
        language_to_voice: Dict[str, str],
        default_voice: str,
        default_language: str = "en"
    ):
        """
        Initialize the language-aware voice switcher.
        
        Args:
            tts_service: The TTS service to control (CartesiaTTSService)
            language_to_voice: Dict mapping language codes to Cartesia voice IDs
                              Example: {"en": "voice-id-1", "hi": "voice-id-2"}
            default_voice: Fallback voice ID if language not in mapping
            default_language: Default language code (default: "en")
        """
        super().__init__()
        self._tts_service = tts_service
        self._language_to_voice = language_to_voice
        self._default_voice = default_voice
        self._default_language = default_language
        
        # Track current state
        self._current_voice = default_voice
        self._current_language = default_language
        
        logger.info(f"LanguageAwareVoiceSwitcher initialized")
        logger.info(f"  Default language: {default_language}")
        logger.info(f"  Default voice: {default_voice}")
        logger.info(f"  Supported languages: {', '.join(language_to_voice.keys())}")
    
    def _extract_language_code(self, language_value) -> Optional[str]:
        """
        Extract language code from various language value formats.
        
        Handles:
        - String format: "en", "en-US", "hi-IN"
        - Object format: Language object with .value attribute
        
        Args:
            language_value: Language value from transcription frame
            
        Returns:
            Two-letter language code (e.g., "en", "hi") or None
        """
        if not language_value:
            return None
        
        # Handle string format
        if isinstance(language_value, str):
            lang_code = language_value
        # Handle object format (e.g., Language enum)
        elif hasattr(language_value, 'value'):
            lang_code = language_value.value
        else:
            lang_code = str(language_value)
        
        # Extract base language code (e.g., "en" from "en-US")
        if '-' in lang_code:
            lang_code = lang_code.split('-')[0]
        
        return lang_code.lower()
    
    def _switch_voice(self, detected_lang: str):
        """
        Switch the TTS voice based on detected language.
        
        Only switches if the new voice is different from the current one
        to avoid unnecessary TTS reconfiguration.
        
        Args:
            detected_lang: ISO language code (e.g., 'en', 'hi', 'or')
        """
        # Look up the appropriate voice for this language
        new_voice = self._language_to_voice.get(detected_lang, self._default_voice)
        
        if new_voice != self._current_voice:
            # Voice needs to change - update TTS service
            old_voice = self._current_voice
            old_language = self._current_language
            
            self._current_voice = new_voice
            self._current_language = detected_lang
            
            # Update the TTS service voice
            self._tts_service.set_voice(new_voice)
            
            logger.info(f"🎤 Voice switched: {old_language} ({old_voice[:8]}...) → "
                       f"{detected_lang} ({new_voice[:8]}...)")
        else:
            # Voice is already correct
            logger.debug(f"Voice already set for language: {detected_lang}")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process frames flowing through the pipeline.
        
        Frame types handled:
          - InterimTranscriptionFrame: Ignored (partial results we don't need)
          - TranscriptionFrame: Processed for language detection and voice switching
          - All others: Passed through unchanged
        
        Args:
            frame: The frame to process
            direction: Direction of frame flow (upstream/downstream)
        """
        await super().process_frame(frame, direction)
        
        # CRITICAL: Ignore interim/partial transcripts
        # These are incomplete and shouldn't trigger voice changes or reach the LLM
        if isinstance(frame, InterimTranscriptionFrame):
            # Log interim transcripts for debugging (optional)
            if hasattr(frame, 'text') and frame.text:
                logger.debug(f"⏸️  Interim transcript (ignored): '{frame.text[:50]}...'")
            # Don't push interim frames downstream
            return
        
        # Process only FINAL TranscriptionFrames
        if isinstance(frame, TranscriptionFrame):
            text = frame.text if hasattr(frame, 'text') else ""
            
            logger.info(f"📝 Final transcript: '{text}'")
            
            # Extract language from the frame
            detected_lang = None
            if hasattr(frame, 'language') and frame.language:
                detected_lang = self._extract_language_code(frame.language)
                
                if detected_lang:
                    logger.info(f"🌍 Language detected: {detected_lang}")
                    # Switch voice to match detected language
                    self._switch_voice(detected_lang)
                else:
                    logger.warning(f"⚠️  Could not extract language code from: {frame.language}")
            else:
                logger.warning(f"⚠️  No language detected in transcript: '{text[:50]}'")
                # Use default language if no detection
                if self._current_language != self._default_language:
                    logger.info(f"Reverting to default language: {self._default_language}")
                    self._switch_voice(self._default_language)
            
            # Pass the final transcript downstream to the LLM
            await self.push_frame(frame, direction)
            return
        
        # Pass all other frames through unchanged
        await self.push_frame(frame, direction)
    
    def get_current_language(self) -> str:
        """
        Get the currently active language.
        
        Returns:
            Current language code (e.g., "en", "hi", "or")
        """
        return self._current_language
    
    def get_current_voice(self) -> str:
        """
        Get the currently active voice ID.
        
        Returns:
            Current Cartesia voice ID
        """
        return self._current_voice
