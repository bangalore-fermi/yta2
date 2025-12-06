"""
Google Cloud TTS Voice Manager for NCERT QuickPrep
Replaces Edge TTS with high-quality Google Cloud Text-to-Speech Indian voices
"""

import os
import json
import asyncio
from pathlib import Path
from google.cloud import texttospeech
from google.oauth2 import service_account
import re

class GoogleTTSVoiceManager:
    """
    Manages Google Cloud Text-to-Speech synthesis for Indian English voices.
    Supports multiple voice types: Neural2, WaveNet, Journey, and Standard.
    """
    
    # Indian English voices available in Google Cloud TTS
    INDIAN_VOICES = {
        # Journey voices (latest, most natural)
        'en-IN-Journey-D': {'gender': 'MALE', 'type': 'Journey', 'quality': 'Premium'},
        'en-IN-Journey-F': {'gender': 'FEMALE', 'type': 'Journey', 'quality': 'Premium'},
        'en-IN-Journey-O': {'gender': 'NEUTRAL', 'type': 'Journey', 'quality': 'Premium'},
        
        # Neural2 voices (high quality)
        'en-IN-Neural2-A': {'gender': 'FEMALE', 'type': 'Neural2', 'quality': 'High'},
        'en-IN-Neural2-B': {'gender': 'MALE', 'type': 'Neural2', 'quality': 'High'},
        'en-IN-Neural2-C': {'gender': 'MALE', 'type': 'Neural2', 'quality': 'High'},
        'en-IN-Neural2-D': {'gender': 'FEMALE', 'type': 'Neural2', 'quality': 'High'},
        
        # Wavenet voices (good quality)
        'en-IN-Wavenet-A': {'gender': 'FEMALE', 'type': 'Wavenet', 'quality': 'Good'},
        'en-IN-Wavenet-B': {'gender': 'MALE', 'type': 'Wavenet', 'quality': 'Good'},
        'en-IN-Wavenet-C': {'gender': 'MALE', 'type': 'Wavenet', 'quality': 'Good'},
        'en-IN-Wavenet-D': {'gender': 'FEMALE', 'type': 'Wavenet', 'quality': 'Good'},
        
        # Standard voices (basic quality)
        'en-IN-Standard-A': {'gender': 'FEMALE', 'type': 'Standard', 'quality': 'Basic'},
        'en-IN-Standard-B': {'gender': 'MALE', 'type': 'Standard', 'quality': 'Basic'},
        'en-IN-Standard-C': {'gender': 'MALE', 'type': 'Standard', 'quality': 'Basic'},
        'en-IN-Standard-D': {'gender': 'FEMALE', 'type': 'Standard', 'quality': 'Basic'},
    }
    
    def __init__(self, credentials_path=None):
        """
        Initialize Google Cloud TTS client.
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
                             If None, uses GOOGLE_APPLICATION_CREDENTIALS env var
        """
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = texttospeech.TextToSpeechClient(credentials=credentials)
        else:
            # Uses default credentials from environment
            self.client = texttospeech.TextToSpeechClient()
        
        print(f"✓ Google Cloud TTS initialized")
    
    def clean_text(self, text):
        """
        Clean text for TTS synthesis (same as original Edge TTS logic).
        Removes Markdown formatting and special characters.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text suitable for TTS
        """
        # Remove Markdown bold/italic markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def synthesize_speech(
        self,
        text,
        voice_name='en-IN-Neural2-D',
        output_path='output.mp3',
        speaking_rate=1.25,
        pitch=2.0,
        volume_gain_db=0.0
    ):
        """
        Synthesize speech using Google Cloud TTS.
        
        Args:
            text: Text to synthesize
            voice_name: Google Cloud voice name (e.g., 'en-IN-Neural2-D')
            output_path: Output MP3 file path
            speaking_rate: Speech speed (0.25 to 4.0, default 1.25 for high energy)
            pitch: Voice pitch in semitones (-20.0 to 20.0, default 2.0)
            volume_gain_db: Volume adjustment in dB (-96.0 to 16.0)
            
        Returns:
            Path to generated audio file
        """
        # Clean text
        text = self.clean_text(text)
        
        # Validate voice
        if voice_name not in self.INDIAN_VOICES:
            print(f"⚠ Voice '{voice_name}' not found, using default 'en-IN-Neural2-D'")
            voice_name = 'en-IN-Neural2-D'
        
        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Configure voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code='en-IN',
            name=voice_name
        )
        
        # Configure audio output with prosody controls
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db,
            sample_rate_hertz=24000  # High quality 24kHz
        )
        
        try:
            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Write audio to file
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"✓ Audio saved: {output_path} ({voice_name})")
            return output_path
            
        except Exception as e:
            print(f"✗ TTS Error: {e}")
            raise
    
    async def synthesize_speech_with_ssml(
        self,
        ssml_text,
        voice_name='en-IN-Neural2-D',
        output_path='output.mp3',
        speaking_rate=1.25,
        pitch=2.0
    ):
        """
        Synthesize speech using SSML markup for advanced control.
        
        Args:
            ssml_text: SSML-formatted text
            voice_name: Google Cloud voice name
            output_path: Output MP3 file path
            speaking_rate: Speech speed
            pitch: Voice pitch
            
        Returns:
            Path to generated audio file
        """
        # Set up SSML input
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        
        # Configure voice
        voice = texttospeech.VoiceSelectionParams(
            language_code='en-IN',
            name=voice_name
        )
        
        # Configure audio
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            sample_rate_hertz=24000
        )
        
        try:
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"✓ SSML audio saved: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"✗ SSML TTS Error: {e}")
            raise
    
    def get_available_voices(self, quality_filter=None):
        """
        Get list of available Indian English voices.
        
        Args:
            quality_filter: Filter by quality ('Premium', 'High', 'Good', 'Basic')
            
        Returns:
            List of voice names matching filter
        """
        if quality_filter:
            return [
                name for name, info in self.INDIAN_VOICES.items()
                if info['quality'] == quality_filter
            ]
        return list(self.INDIAN_VOICES.keys())
    
    def get_voice_info(self, voice_name):
        """Get detailed information about a specific voice."""
        return self.INDIAN_VOICES.get(voice_name, None)


# Example usage and testing
if __name__ == "__main__":
    async def test_google_tts():
        """Test Google Cloud TTS with Indian voices."""
        
        # Initialize manager (ensure GOOGLE_APPLICATION_CREDENTIALS is set)
        manager = GoogleTTSVoiceManager()
        
        # Test text
        test_text = """
        Hello friends! Welcome to NCERT QuickPrep. 
        Today we'll learn about **photosynthesis** - the amazing process 
        where plants make their own food using sunlight!
        """
        
        # Test different voice types
        test_voices = [
            ('en-IN-Neural2-D', 'neural2_female.mp3'),
            ('en-IN-Neural2-B', 'neural2_male.mp3'),
            ('en-IN-Journey-F', 'journey_female.mp3'),
        ]
        
        print("\n🎤 Testing Google Cloud TTS Indian Voices\n")
        
        for voice_name, filename in test_voices:
            voice_info = manager.get_voice_info(voice_name)
            print(f"\nTesting: {voice_name}")
            print(f"  Type: {voice_info['type']}, Gender: {voice_info['gender']}")
            
            await manager.synthesize_speech(
                text=test_text,
                voice_name=voice_name,
                output_path=filename,
                speaking_rate=1.25,  # High energy like original Edge TTS
                pitch=2.0
            )
        
        # Test SSML
        ssml_text = """
        <speak>
            <prosody rate="fast" pitch="+2st">
                Did you know? <break time="500ms"/>
                The mitochondria is the powerhouse of the cell!
            </prosody>
        </speak>
        """
        
        print("\n\nTesting SSML:")
        await manager.synthesize_speech_with_ssml(
            ssml_text=ssml_text,
            voice_name='en-IN-Neural2-D',
            output_path='ssml_test.mp3'
        )
        
        # Show available voices
        print("\n\n📋 Available Premium Voices:")
        for voice in manager.get_available_voices(quality_filter='Premium'):
            print(f"  • {voice}")
    
    # Run test
    asyncio.run(test_google_tts())