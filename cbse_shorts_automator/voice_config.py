#!/usr/bin/env python3
"""
File: voice_config.py
Voice definitions for Google Cloud TTS and Edge TTS fallback.
Optimized for Indian CBSE educational content with energetic delivery.
"""

# ============================================================================
# GOOGLE CLOUD TTS VOICES (Primary - Neural2 Quality)
# ============================================================================
# Free Tier: 1M characters/month per project
# Cost after free tier: $16 per 1M characters
# Quality: Natural, human-like, warm delivery suitable for education

GOOGLE_VOICES = {
    'NeeraNeural2': {
        'name': 'en-IN-Neural2-A',
        'gender': 'Female',
        'language_code': 'en-IN',
        'speaking_rate': 1.15,      # 15% faster for energy
        'pitch': 1.5,               # Slightly higher for warmth
        'description': 'Warm, friendly female - like a caring tutor'
    },
    'PriyaNeural2': {
        'name': 'en-IN-Neural2-D',
        'gender': 'Female', 
        'language_code': 'en-IN',
        'speaking_rate': 1.20,      # 20% faster for enthusiasm
        'pitch': 2.0,               # Energetic pitch
        'description': 'Energetic, clear female - motivational'
    },
    'RajeshNeural2': {
        'name': 'en-IN-Neural2-B',
        'gender': 'Male',
        'language_code': 'en-IN',
        'speaking_rate': 1.12,      # Slightly faster, authoritative
        'pitch': 0.5,               # Deeper for authority
        'description': 'Authoritative yet friendly male'
    },
    'ArjunNeural2': {
        'name': 'en-IN-Neural2-C',
        'gender': 'Male',
        'language_code': 'en-IN',
        'speaking_rate': 1.18,      # Youthful energy
        'pitch': 1.0,               # Relatable pitch
        'description': 'Youthful, relatable male - peer-like'
    }
}

# ============================================================================
# EDGE TTS VOICES (Fallback - When Google quota exhausted)
# ============================================================================
# Free Tier: Unlimited (Microsoft service)
# Quality: Good but slightly less natural than Google Neural2

EDGE_VOICES = {
    'NeerjaNeural': {
        'name': 'en-IN-NeerjaNeural',
        'gender': 'Female',
        'pitch': '+2Hz',
        'rate': '+25%',
        'description': 'Standard Edge female voice'
    },
    'AnanyaNeural': {
        'name': 'en-IN-AnanyaNeural',
        'gender': 'Female',
        'pitch': '+0Hz',
        'rate': '+30%',
        'description': 'Energetic Edge female voice'
    },
    'KavyaNeural': {
        'name': 'en-IN-KavyaNeural',
        'gender': 'Female',
        'pitch': '+0Hz',
        'rate': '+25%',
        'description': 'Warm Edge female voice'
    },
    'PrabhatNeural': {
        'name': 'en-IN-PrabhatNeural',
        'gender': 'Male',
        'pitch': '+2Hz',
        'rate': '+25%',
        'description': 'Standard Edge male voice'
    },
    'AaravNeural': {
        'name': 'en-IN-AaravNeural',
        'gender': 'Male',
        'pitch': '+0Hz',
        'rate': '+30%',
        'description': 'Energetic Edge male voice'
    },
    'RehaanNeural': {
        'name': 'en-IN-RehaanNeural',
        'gender': 'Male',
        'pitch': '+0Hz',
        'rate': '+20%',
        'description': 'Calm Edge male voice'
    }
}

# ============================================================================
# VOICE SELECTION HELPERS
# ============================================================================

def get_random_google_voice():
    """Returns a random Google Neural2 voice key for variety."""
    import random
    return random.choice(list(GOOGLE_VOICES.keys()))

def get_random_edge_voice():
    """Returns a random Edge TTS voice key for variety."""
    import random
    return random.choice(list(EDGE_VOICES.keys()))

def get_voice_info(voice_key, provider='google'):
    """
    Get voice configuration by key.
    
    Args:
        voice_key: Voice identifier (e.g., 'NeeraNeural2')
        provider: 'google' or 'edge'
    
    Returns:
        dict: Voice configuration or None if not found
    """
    if provider == 'google':
        return GOOGLE_VOICES.get(voice_key)
    elif provider == 'edge':
        return EDGE_VOICES.get(voice_key)
    return None