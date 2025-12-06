#!/usr/bin/env python3
"""
File: karaoke_manager.py
V2: SMOOTH FLOW EDITION
Generates ONE continuous audio file first, then calculates text timing.
"""

import os
from moviepy.editor import AudioFileClip

class KaraokeManager:
    def __init__(self, voice_manager, temp_dir="temp"):
        self.vm = voice_manager
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def _smart_split(self, text, max_words=4):
        """Splits text into readable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            # Break on punctuation or length
            is_long = len(current_chunk) >= max_words
            ends_sentence = word.endswith(('.', '!', '?', ',', ':'))
            
            if is_long or ends_sentence:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def generate_timed_audio(self, full_text, unique_id, voice_key=None):
        """
        1. Generates ONE continuous audio file (Natural Prosody).
        2. Estimates subtitle timings based on character count.
        
        Args:
            full_text: Complete text to synthesize
            unique_id: Unique identifier for temp file
            voice_key: Specific voice to use (optional, uses random if None)
        """
        filename = f"{unique_id}_full.mp3"
        path = os.path.join(self.temp_dir, filename)
        
        # Use specific voice if provided, otherwise random
        if voice_key:
            full_audio_clip = self.vm.generate_audio_with_specific_voice(full_text, path, voice_key)
        else:
            full_audio_clip = self.vm.generate_audio_sync(full_text, path)
        
        total_duration = full_audio_clip.duration
        
        # 2. Split text for subtitles
        chunks = self._smart_split(full_text)
        
        # 3. Calculate Timings based on "Character Density"
        # (Longer words take longer to say)
        total_chars = len(full_text.replace(" ", "")) # Count chars ignoring spaces
        if total_chars == 0: total_chars = 1 # Avoid div/0
        
        segments = []
        current_start = 0.0
        
        for chunk in chunks:
            chunk_chars = len(chunk.replace(" ", ""))
            
            # Math: (Chunk Chars / Total Chars) * Total Duration
            # We add a tiny buffer (0.1s) to make it feel snappier
            estimated_duration = (chunk_chars / total_chars) * total_duration
            
            segments.append({
                'text': chunk,
                'start': current_start,
                'end': current_start + estimated_duration,
                'duration': estimated_duration
            })
            
            current_start += estimated_duration

        return full_audio_clip, segments