#!/usr/bin/env python3
"""
File: voice_edge.py
Edge TTS implementation (fallback provider when Google quota exhausted).
Extracted from original voice_manager.py with no logic changes.
"""

import asyncio
import edge_tts
import os
import re
import time

class EdgeVoiceEngine:
    """
    Edge TTS engine (Microsoft) - Free unlimited usage.
    Used as fallback when Google Cloud TTS quota is exhausted.
    """
    
    def __init__(self):
        """Initialize Edge TTS engine."""
        print("✅ Edge TTS engine initialized (fallback mode)")
    
    def clean_text(self, text):
        """
        Clean text for TTS (same logic as Google for consistency).
        Removes Markdown, emoji, and problematic symbols.
        
        Args:
            text: Raw text string
        
        Returns:
            str: Cleaned text safe for TTS
        """
        if not text:
            return ""
        
        text = str(text)
        
        # 1. Remove Markdown (*, _, #, ~, `)
        text = re.sub(r'[*_#~`]', '', text)
        
        # 2. Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # 3. Replace common issues
        text = text.replace('&', 'and').replace('+', 'plus').replace('%', ' percent')
        
        # 4. Remove brackets and their content [Ref]
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # 5. Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _generate_audio_async(self, text, output_path, voice_config):
        """
        Async wrapper for Edge TTS synthesis.
        
        Args:
            text: Cleaned text to synthesize
            output_path: Where to save audio file
            voice_config: Voice configuration dict from voice_config.py
        
        Raises:
            Exception: If synthesis fails
        """
        try:
            communicate = edge_tts.Communicate(
                text,
                "en-US-AndrewNeural"#,
                #pitch=voice_config['pitch'],
                #rate=voice_config['rate']
            )
            
            await communicate.save(output_path)

        except Exception as e:
            #print(f"   ❌ {output_path}:ERROR: {e}")
            #print(f"{text}:{voice_config['name']}")
            #import traceback
            #traceback.print_exc()
            raise Exception(f"{e}")

        print(f"{output_path}:{os.path.getsize(output_path)}")
        
        # Verify file was created
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Generated audio file is 0 bytes")
    
    def synthesize(self, text, output_path, voice_config, max_retries=5):
        """
        Synthesize speech using Edge TTS with exponential backoff retry.
        
        Args:
            text: Text to synthesize
            output_path: Where to save MP3 file
            voice_config: Voice configuration dict from voice_config.py
            max_retries: Maximum retry attempts for rate limits
        
        Returns:
            tuple: (success: bool, chars_used: int, error_msg: str or None)
        """
        # Clean text
        clean_text = self.clean_text(text)
        
        if not clean_text or len(clean_text) < 2:
            print(f"⚠️ Warning: Text empty after cleaning. Original: '{text}'")
            clean_text = "Check the description."  # Fallback
        
        chars_used = len(clean_text)
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Run async synthesis
                asyncio.run(
                    self._generate_audio_async(clean_text, output_path, voice_config)
                )
                
                # Verify file exists
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True, chars_used, None
                else:
                    raise FileNotFoundError(f"Audio file not generated: {output_path}")
            
            except Exception as e:
                error_msg = str(e)
                
                # Check for retryable errors (429 rate limits, connection issues)
                if any(keyword in error_msg for keyword in [
                    "429", "Connection", "Handshake", "NoAudioReceived", "received"
                ]):
                    wait_time = 5 + (attempt * 3)  # 5s, 10s, 15s, 20s
                    print(f"   ⚠️ Edge TTS Retry ({attempt+1}/{max_retries}): "
                          f"{error_msg[:50]}... Waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    # Non-retryable error
                    return False, chars_used, f"Edge TTS Error: {error_msg}"
        
        # All retries exhausted
        return False, chars_used, f"Edge TTS failed after {max_retries} retries"
    
    def test_connection(self):
        """
        Test if Edge TTS service is accessible.
        
        Returns:
            bool: True if service is reachable
        """
        try:
            import tempfile
            test_file = os.path.join(tempfile.gettempdir(), 'edge_test.mp3')
            
            # Try synthesizing a short test phrase
            from voice_config import EDGE_VOICES
            test_voice = list(EDGE_VOICES.values())[0]
            
            success, _, _ = self.synthesize(
                "Test",
                test_file,
                test_voice,
                max_retries=1
            )
            
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return success
        
        except Exception as e:
            print(f"❌ Edge TTS test failed: {e}")
            return False