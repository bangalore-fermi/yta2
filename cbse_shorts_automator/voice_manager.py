#!/usr/bin/env python3
"""
File: voice_manager.py
Main orchestrator for text-to-speech with Google Cloud TTS (primary) 
and Edge TTS (fallback). Handles multi-account rotation and quota management.

INTERFACE: Maintains 100% backward compatibility with existing codebase.
"""

import os
import random
from moviepy.editor import AudioFileClip

# Import our modular voice engines
from voice_config import GOOGLE_VOICES, EDGE_VOICES, get_random_google_voice, get_random_edge_voice
from voice_google import GoogleVoiceEngine
from voice_edge import EdgeVoiceEngine
from voice_usage_tracker import VoiceUsageTracker

class VoiceManager:
    """
    Unified voice manager with intelligent provider selection.
    
    BACKWARD COMPATIBLE: Existing code continues to work unchanged.
    New feature: self.last_used_system for logging to Google Sheets.
    """
    
    def __init__(self, voice_name=None, config_dir='config', data_dir='data'):
        """
        Initialize voice manager with auto-detection of available providers.
        
        Args:
            voice_name: Optional specific voice (for backward compatibility)
            config_dir: Where to find google_tts_account*.json files
            data_dir: Where to store usage tracking data
        """
        self.config_dir = config_dir
        self.data_dir = data_dir
        
        # Initialize engines
        self.google_engine = None
        self.edge_engine = EdgeVoiceEngine()
        
        # Try to initialize Google TTS (may not be available)
        try:
            self.google_engine = GoogleVoiceEngine(config_dir)
            self.google_accounts = self.google_engine.get_available_accounts()
        except FileNotFoundError:
            print("⚠️ No Google Cloud TTS accounts found. Using Edge TTS only.")
            self.google_accounts = []
        
        # Initialize usage tracker
        self.tracker = VoiceUsageTracker(data_dir)
        
        # Register all Google accounts
        for account in self.google_accounts:
            self.tracker.register_account(account)
        
        # Voice selection (for backward compatibility)
        self.voice_name = voice_name
        
        # Logging attributes (NEW - for Google Sheets logging)
        self.last_used_system = None  # e.g., "Google-account1-NeeraNeural2" or "Edge-PrabhatNeural"
        self.char_count = 0
    
    @staticmethod
    def get_random_voice_name():
        """
        Get random voice name (backward compatible).
        Returns Google voice if available, else Edge voice.
        """
        try:
            return get_random_google_voice()
        except:
            return get_random_edge_voice()
    
    def clean_text(self, text):
        """
        Clean text for TTS (backward compatible).
        Uses Google engine's clean_text method.
        """
        if self.google_engine:
            return self.google_engine.clean_text(text)
        else:
            return self.edge_engine.clean_text(text)
    
    def _estimate_chars_needed(self, text):
        """
        Estimate characters needed after cleaning.
        
        Args:
            text: Raw text
        
        Returns:
            int: Estimated character count
        """
        clean = self.clean_text(text)
        return len(clean)
    
    def _select_provider_and_voice(self, text):
        """
        Intelligently select provider (Google/Edge) and voice based on quota.
        
        Args:
            text: Text to be synthesized
        
        Returns:
            tuple: (provider: str, account: str or None, voice_config: dict, voice_key: str)
        """
        chars_needed = self._estimate_chars_needed(text)
        
        # Try Google accounts first
        if self.google_engine and self.google_accounts:
            available_account = self.tracker.find_available_account(
                chars_needed, 
                self.google_accounts
            )
            
            if available_account:
                # Select random Google voice
                voice_key = get_random_google_voice()
                voice_config = GOOGLE_VOICES[voice_key]
                
                print(f"   🔵 Using Google TTS (Account: {available_account}, Voice: {voice_key})")
                return 'google', available_account, voice_config, voice_key
            else:
                print(f"   ⚠️ All Google accounts exhausted. Falling back to Edge TTS.")
        
        # Fallback to Edge TTS
        voice_key = get_random_edge_voice()
        voice_config = EDGE_VOICES[voice_key]
        
        print(f"   🟢 Using Edge TTS (Voice: {voice_key})")
        return 'edge', None, voice_config, voice_key
    
    def _synthesize_with_provider(self, text, output_path, provider, account, voice_config):
        """
        Synthesize audio using the selected provider.
        
        Args:
            text: Text to synthesize
            output_path: Where to save audio
            provider: 'google' or 'edge'
            account: Google account name (or None for Edge)
            voice_config: Voice configuration dict
        
        Returns:
            tuple: (success: bool, chars_used: int, error_msg: str or None)
        """
        if provider == 'google':
            return self.google_engine.synthesize(
                text, output_path, voice_config, account
            )
        else:  # edge
            return self.edge_engine.synthesize(
                text, output_path, voice_config
            )
    
    def generate_audio_sync(self, text, output_path, override_voice=None):
        """
        Generate audio synchronously (BACKWARD COMPATIBLE interface).
        
        Args:
            text: Text to synthesize
            output_path: Where to save MP3
            override_voice: Optional voice override (for compatibility)
        
        Returns:
            AudioFileClip: MoviePy audio clip object
        
        Raises:
            Exception: If synthesis fails completely
        """
        # Step 1: Select provider and voice
        provider, account, voice_config, voice_key = self._select_provider_and_voice(text)
        
        # Step 2: Attempt synthesis
        success, chars_used, error_msg = self._synthesize_with_provider(
            text, output_path, provider, account, voice_config
        )
        
        # Step 3: Handle quota exhaustion (try next account or fallback)
        if not success and "QUOTA_EXCEEDED" in str(error_msg):
            print(f"   ⚠️ Quota exceeded for {account}. Trying next option...")
            
            # If Google failed, try Edge
            if provider == 'google':
                provider = 'edge'
                account = None
                voice_key = get_random_edge_voice()
                voice_config = EDGE_VOICES[voice_key]
                
                print(f"   🟢 Falling back to Edge TTS (Voice: {voice_key})")
                success, chars_used, error_msg = self._synthesize_with_provider(
                    text, output_path, provider, account, voice_config
                )
        
        # Step 4: Log usage
        if success:
            account_label = account if account else 'edge'
            self.tracker.log_usage(
                account_name=account_label,
                provider=provider,
                chars_used=chars_used,
                voice_used=voice_key
            )
            
            # Set logging attributes for Google Sheets
            if provider == 'google':
                self.last_used_system = f"Google-{account}-{voice_key}"
            else:
                self.last_used_system = f"Edge-{voice_key}"
            
            self.char_count = chars_used
        
        # Step 5: Verify and return
        if success and os.path.exists(output_path):
            return AudioFileClip(output_path)
        else:
            raise Exception(f"TTS synthesis failed: {error_msg}")
    def generate_audio_with_specific_voice(self, text, output_path, voice_key, provider='google'):
        """
        Generate audio using a specific voice (no randomization).
        Used when a video needs consistent voice across all segments.
        
        Args:
            text: Text to synthesize
            output_path: Where to save MP3
            voice_key: Specific voice to use (e.g., 'NeeraNeural2' from Google or 'NeerjaNeural' from Edge)
            provider: 'google' or 'edge' (default: 'google', falls back to 'edge' if quota exhausted)
        
        Returns:
            AudioFileClip: MoviePy audio clip object
        """

        
        #print(f"1.{provider}")
        # Step 1: Get voice configuration
        if provider == 'google' and voice_key in GOOGLE_VOICES:
            voice_config = GOOGLE_VOICES[voice_key]
        elif provider == 'edge' and voice_key in EDGE_VOICES:
            voice_config = EDGE_VOICES[voice_key]
        else:
            # Fallback: try to find voice in either provider
            if voice_key in GOOGLE_VOICES:
                voice_config = GOOGLE_VOICES[voice_key]
                provider = 'google'
            elif voice_key in EDGE_VOICES:
                voice_config = EDGE_VOICES[voice_key]
                provider = 'edge'
            else:
                raise ValueError(f"Voice '{voice_key}' not found in Google or Edge voices")

        
        #print(f"2.{provider}")
        
        # Step 2: Estimate characters and check quota
        chars_needed = self._estimate_chars_needed(text)
        
        # Step 3: Try Google first if requested
        if provider == 'google' and self.google_engine and self.google_accounts:
            available_account = self.tracker.find_available_account(
                chars_needed,
                self.google_accounts
            )

            print(f"3.{available_account}")
            
            if available_account:
                success, chars_used, error_msg = self._synthesize_with_provider(
                    text, output_path, 'google', available_account, voice_config
                )
                
                if success:
                    self.tracker.log_usage(available_account, 'google', chars_used, voice_key)
                    self.last_used_system = f"Google-{available_account}-{voice_key}"
                    self.char_count = chars_used
                    return AudioFileClip(output_path)
                elif "QUOTA_EXCEEDED" in str(error_msg):
                    print(f"   ⚠️ Google quota exhausted. Falling back to Edge TTS.")
                    provider = 'edge'
            else:
                print(f"   ⚠️ No Google account with sufficient quota. Using Edge TTS.")
                provider = 'edge'

        provider = 'edge'
        # Step 4: Use Edge TTS (fallback or requested)
        if provider == 'edge':
            print(f" provider: {provider}")
            # Map to equivalent Edge voice if we were trying Google
            if voice_key in GOOGLE_VOICES:
                # Try to find similar Edge voice (same gender)
                edge_voice_key = get_random_edge_voice()  # Fallback to random
                voice_config = EDGE_VOICES[edge_voice_key]
                print(f" Voice used for {output_path}: {edge_voice_key}")
                
            else:
                edge_voice_key = voice_key
            
            success, chars_used, error_msg = self._synthesize_with_provider(
                text, output_path, 'edge', None, voice_config
            )

            print(f" 0.edge: {success}:{output_path}")
            try:
                if success:
                
                    print(f" 1.edge: {success}:{output_path}")
                    self.tracker.log_usage('edge', 'edge', chars_used, edge_voice_key)
                    #print(f" 2.edge: {success}:{output_path}")
                    self.last_used_system = f"Edge-{edge_voice_key}"
                    #print(f" 3.edge: {success}:{output_path}")
                    self.char_count = chars_used
                    #print(f" 4.edge: {success}:{output_path}")
                    generated_aud_file=AudioFileClip(output_path);
                    print(f" 5.edge: {success}:{output_path}")
                    return generated_aud_file

            
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
        
        # Step 5: Complete failure
        raise Exception(f"Failed to synthesize audio with voice '{voice_key},{provider}'")

    def get_usage_summary(self):
        """
        Get current usage summary across all accounts.
        
        Returns:
            dict: Usage statistics
        """
        return self.tracker.get_summary()
    
    def print_usage_summary(self):
        """Print usage summary to console."""
        self.tracker.print_summary()


# ============================================================================
# LEGACY COMPATIBILITY LAYER
# These functions maintain compatibility with old code that might call
# module-level functions instead of class methods.
# ============================================================================

def get_random_voice_name():
    """Legacy function for backward compatibility."""
    return VoiceManager.get_random_voice_name()