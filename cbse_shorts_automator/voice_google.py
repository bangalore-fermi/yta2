#!/usr/bin/env python3
"""
File: voice_google.py
Google Cloud Text-to-Speech implementation with multi-account rotation.
Handles Neural2 voices for high-quality, natural Indian English output.
"""

import os
import re
from google.cloud import texttospeech
from google.oauth2 import service_account
from pathlib import Path

class GoogleVoiceEngine:
    """
    Google Cloud TTS engine with multi-account support and quota management.
    """
    
    def __init__(self, config_dir='config'):
        """
        Initialize Google TTS with auto-detection of service account files.
        
        Args:
            config_dir: Directory containing google_tts_account*.json files
        """
        self.config_dir = config_dir
        self.accounts = self._discover_accounts()
        self.clients = {}  # Cache of initialized clients
        
        if not self.accounts:
            raise FileNotFoundError(
                f"No google_tts_account*.json files found in {config_dir}/"
            )
        
        print(f"✅ Discovered {len(self.accounts)} Google Cloud TTS account(s)")
    
    def _discover_accounts(self):
        """
        Auto-discover all google_tts_account*.json files.
        
        Returns:
            dict: {account_name: credential_file_path}
        """
        accounts = {}
        config_path = Path(self.config_dir)
        
        for json_file in config_path.glob('google_tts_account*.json'):
            # Extract account number/name from filename
            # e.g., google_tts_account1.json -> account1
            account_name = json_file.stem.replace('google_tts_', '')
            accounts[account_name] = str(json_file)
        
        return accounts
    
    def _get_client(self, account_name):
        """
        Get or create a Google TTS client for the specified account.
        
        Args:
            account_name: Account identifier (e.g., 'account1')
        
        Returns:
            texttospeech.TextToSpeechClient
        """
        if account_name in self.clients:
            return self.clients[account_name]
        
        if account_name not in self.accounts:
            raise ValueError(f"Account '{account_name}' not found")
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            self.accounts[account_name]
        )
        
        # Create client
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        self.clients[account_name] = client
        
        return client
    
    def clean_text(self, text):
        """
        Clean text for TTS (same logic as Edge TTS for consistency).
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
        
        # 5. Fix "Robotic Pauses" (The Quotes Issue)
        # Remove double quotes completely
        text = text.replace('"', '')
        
        # Remove single quotes acting as emphasis (e.g., 'case')
        # BUT keep apostrophes in contractions (don't, can't)
        # Logic: Replace ' if it has a space on either side
        text = re.sub(r" '", " ", text) # Remove starting '
        text = re.sub(r"' ", " ", text) # Remove ending '
        
        # 6. Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def synthesize(self, text, output_path, voice_config, account_name):
        """
        Synthesize speech using Google Cloud TTS.
        
        Args:
            text: Text to synthesize
            output_path: Where to save MP3 file
            voice_config: Voice configuration dict from voice_config.py
            account_name: Which account to use (e.g., 'account1')
        
        Returns:
            tuple: (success: bool, chars_used: int, error_msg: str or None)
        """
        try:
            # Clean text
            clean_text = self.clean_text(text)
            
            if not clean_text or len(clean_text) < 2:
                print(f"⚠️ Warning: Text empty after cleaning. Original: '{text}'")
                clean_text = "Check the description."  # Fallback
            
            chars_used = len(clean_text)
            
            # Get client for this account
            client = self._get_client(account_name)
            
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=clean_text)
            
            # Configure voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config['language_code'],
                name=voice_config['name']
            )
            
            # Configure audio settings
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=voice_config.get('speaking_rate', 1.0),
                pitch=voice_config.get('pitch', 0.0)
            )
            
            # Perform synthesis
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio to file
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            # Verify file was created
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return False, chars_used, "Generated audio file is empty"
            
            return True, chars_used, None
        
        except Exception as e:
            error_msg = str(e)
            
            # Check for quota errors
            if "429" in error_msg or "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                return False, 0, f"QUOTA_EXCEEDED: {error_msg}"
            
            return False, 0, f"Google TTS Error: {error_msg}"
    
    def get_available_accounts(self):
        """
        Get list of available account names.
        
        Returns:
            list: Account names (e.g., ['account1', 'account2'])
        """
        return list(self.accounts.keys())
    
    def test_account(self, account_name):
        """
        Test if an account is properly configured.
        
        Args:
            account_name: Account to test
        
        Returns:
            bool: True if account works
        """
        try:
            client = self._get_client(account_name)
            # List voices as a simple API test
            voices = client.list_voices()
            return True
        except Exception as e:
            print(f"❌ Account '{account_name}' test failed: {e}")
            return False