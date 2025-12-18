#!/usr/bin/env python3
"""
File: video_processor.py
Handles video scene detection using SEMANTIC AUDIO MATCHING (Whisper).
UPDATED: Restored 'Breathing Micro-Zoom' for dynamic visuals.
"""

import os
import json
import random
import whisper
import warnings
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx
import numpy as np
import gc

# Suppress Whisper warnings
warnings.filterwarnings("ignore")

class VideoProcessor:
    """
    Processes static slide videos into dynamic shorts.
    """
    
    def __init__(self, temp_dir="temp", debug=False):
        self.debug = debug
        self.temp_dir = temp_dir
        self.model = None # Lazy load
        self.current_cache_file = None # Track file to delete later
        
        # Ensure temp folder exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def _load_model(self):
        """Lazy loads the Whisper model."""
        if self.model is None:
            # Using 'tiny' for speed/RAM. 
            if self.debug: print("⏳ Loading Whisper Model (tiny)...")
            self.model = whisper.load_model("tiny")

    def get_transcript_map(self, video_path):
        """
        Generates a transcript, saves to temp, returns segments.
        """
        filename = os.path.basename(video_path)
        cache_path = os.path.join(self.temp_dir, f"{filename}.json")
        self.current_cache_file = cache_path 
        
        # 1. Check Cache
        if os.path.exists(cache_path):
            if self.debug: print(f"⚡ Using existing temp transcript: {cache_path}")
            with open(cache_path, 'r') as f:
                return json.load(f)

        # 2. Transcribe
        self._load_model()
        if self.debug: print(f"🎙️ Transcribing audio for indexing: {filename}")
        
        result = self.model.transcribe(video_path)
        segments = result['segments']
        
        # 3. Save to Temp
        with open(cache_path, 'w') as f:
            json.dump(segments, f)
            
        return segments

    def find_best_timestamp(self, segments, keyword, last_end_time):
        """
        Scans transcript for keyword to find best scene.
        """
        # Strategy 1: Semantic Search (Forward only)
        if keyword and len(keyword) > 3:
            for seg in segments:
                if seg['start'] >= last_end_time and keyword.lower() in seg['text'].lower():
                    #if self.debug: print(f"   ✅ Found '{keyword}' at {seg['start']:.2f}s")
                    print(f"   ✅ Found '{keyword}' at {seg['start']:.2f}s")
                    return seg['start']
        
        # Strategy 2: Linear Flow (Fallback)
        # Jumps 1.5s forward to ensure visual change
        return last_end_time + 40

    def apply_micro_zoom(self, clip, index, duration):
        """
        RESTORED: The 'Breathing' Effect.
        Slowly zooms In/Out to make static slides look alive.
        """
        # Calculate speed to hit exactly 5% over the duration
        speed = 0.05 / duration 

        if index % 2 == 0:
            # Even Clips: Zoom IN (1.0 -> 1.05)
            # Starts at normal size, grows slightly
            return clip.resize(lambda t: 1 + speed * t)
        else:
            # Odd Clips: Zoom OUT (1.05 -> 1.0)
            # Starts zoomed in (matching previous clip end), shrinks back
            return clip.resize(lambda t: 1.05 - speed * t)

    def extract_keywords_ordered(self, script):
        """
        Extracts nouns/verbs from script for matching.
        """
        full_text = f"{script.get('question_text', '')} {script.get('explanation_spoken', '')} {script.get('fact_details', '')} {script.get('tip_content', '')}"
        
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'to', 'in', 
            'of', 'and', 'for', 'on', 'with', 'at', 'by', 'this', 'that', 
            'these', 'those', 'which', 'who', 'when', 'where', 'how', 'why'
        }
        words = full_text.lower().split()
        
        clean_words = [w.strip(".,?!") for w in words if w.strip(".,?!") not in stop_words and len(w) > 4]
        
        seen = set()
        ordered = []
        for w in clean_words:
            if w not in seen:
                ordered.append(w)
                seen.add(w)
        return ordered

    def release_resources(self):
        """
        CRITICAL: Cleans RAM and deletes Temp files.
        """
        if self.model is not None:
            if self.debug: print("🧹 Releasing Whisper AI from memory...")
            del self.model
            self.model = None
            gc.collect()

        if self.current_cache_file and os.path.exists(self.current_cache_file):
            try:
                os.remove(self.current_cache_file)
                self.current_cache_file = None
            except: pass

    def prepare_video_for_short(self, video_path, total_duration, script=None, width=1080, style='smart'):
        """
        Main Pipeline: Index -> Match -> Extract -> Cleanup
        """
        video = VideoFileClip(video_path)
        vid_duration = video.duration
        
        # SAFETY: Ignore the last 5 seconds (Outro/Logo Zone)
        safe_duration = vid_duration - 5.0
        if safe_duration < 10: safe_duration = vid_duration 
        
        # Get Intelligence
        transcript = self.get_transcript_map(video_path)
        keywords = self.extract_keywords_ordered(script) if script else []
        
        final_clips = []
        current_generated_duration = 0.0
        current_time_marker = 0.0
        clip_index = 0

        if self.debug: print(f"✂️  Generating variable clips for {total_duration}s video...")

        while current_generated_duration < total_duration:
            
            # 1. Pick a Random Duration (Strict Pacing)
            this_clip_len = random.uniform(1.5, 2.5)
            
            remaining = total_duration - current_generated_duration
            if remaining < this_clip_len:
                this_clip_len = remaining
            
            # 2. Determine Target Keyword
            target_kw = keywords[clip_index] if clip_index < len(keywords) else None
            
            # 3. Find Start Time
            start_t = self.find_best_timestamp(transcript, target_kw, current_time_marker)
            
            # 4. Safety Bounds Check
            if start_t + this_clip_len > safe_duration:
                start_t = random.uniform(1.0, safe_duration / 4)
            
            # 5. Extract
            sub = video.subclip(start_t, start_t + this_clip_len)
            
            # Standardize resolution BEFORE applying effects (saves CPU)
            if sub.w != width:
                sub = sub.resize(width=width)
            
            # 6. Apply Breathing Zoom (Alternating)
            sub = self.apply_micro_zoom(sub, clip_index, this_clip_len)
            
            final_clips.append(sub)
            
            current_generated_duration += this_clip_len
            current_time_marker = start_t + this_clip_len
            clip_index += 1

        final_vid = concatenate_videoclips(final_clips, method="compose")
        
        # Explicitly resize final to ensure 1080 width after dynamic zoom
        # (Just in case small rounding errors occurred)
        final_vid = final_vid.set_position(('center', 0))
        
        self.release_resources()
        
        return final_vid