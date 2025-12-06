#!/usr/bin/env python3
"""
File: effects_manager.py
Handles Context-Sensitive Stickers.
UPDATED: Fixed Transparency, Pro Transitions, and Anchored Positioning.
"""

import os
import random
from moviepy.editor import ImageClip, CompositeVideoClip, vfx

class EffectsManager:
    def __init__(self, assets_dir="config/stickers"):
        self.assets_dir = assets_dir
        self.keyword_map = self._load_keyword_map()
        
        # Verify assets
        if not os.path.exists(self.assets_dir):
            print(f"❌ [FX ERROR] Sticker directory not found: {self.assets_dir}")

    def _load_keyword_map(self):
        return {
            "brain.png": ["think", "know", "mind", "remember", "logic", "smart", "brain", "idea"],
            "science.png": ["science", "experiment", "lab", "study", "research"],
            "dna.png": ["gene", "dna", "code", "life", "genetic", "inherit"],
            "test_tube.png": ["chem", "reaction", "mix", "liquid", "solution"],
            "magnet.png": ["attract", "pole", "force", "magnetic", "field"],
            "telescope.png": ["space", "star", "planet", "sky", "universe"],
            "microbe.png": ["bacteria", "virus", "small", "germ", "disease", "sick"],
            "books.png": ["book", "read", "study", "chapter", "lesson", "syllabus"],
            "graduation.png": ["pass", "exam", "college", "school", "degree", "topper"],
            "pencil.png": ["write", "note", "draw", "sketch", "mark"],
            "calculator.png": ["math", "count", "number", "calculate", "solve", "hard"],
            "ruler.png": ["measure", "size", "long", "short", "distance"],
            "muscle.png": ["strong", "power", "lift", "body", "fit"],
            "heart.png": ["love", "life", "blood", "beat", "core"],
            "bone.png": ["skeleton", "structure", "frame", "calcium"],
            "tooth.png": ["teeth", "bite", "chew", "white", "calcium"],
            "eye.png": ["see", "look", "watch", "vision", "sight"],
            "leaf.png": ["plant", "nature", "grow", "green", "photosynthesis"],
            "drop.png": ["water", "liquid", "rain", "fluid", "aqua"],
            "shock.png": ["wow", "shock", "scary", "wait", "what", "danger"],
            "happy.png": ["fun", "good", "great", "easy", "smile", "happy"],
            "cool.png": ["trick", "hack", "pro", "easy", "cool", "style"],
            "angry.png": ["bad", "wrong", "hate", "fail", "stupid"],
            "mind_blown.png": ["amazing", "unbelievable", "crazy", "impossible", "magic"],
            "star_struck.png": ["famous", "star", "shine", "beautiful", "wow"],
            "nerd.png": ["geek", "fact", "detail", "complex", "tech"],
            "sick.png": ["ill", "bad", "gross", "yuck", "vomit"],
            "sleepy.png": ["boring", "tired", "sleep", "rest", "night"],
            "party.png": ["celebrate", "win", "yay", "party", "fun"],
            "fire.png": ["energy", "hot", "fast", "power", "burn", "heat"],
            "idea.png": ["idea", "tip", "solution", "light", "bright"],
            "trophy.png": ["win", "best", "top", "champion", "first", "score"],
            "target.png": ["focus", "goal", "aim", "point", "spot", "here"],
            "warning.png": ["stop", "caution", "wrong", "mistake", "fail", "alert"],
            "check.png": ["correct", "right", "yes", "true", "done"],
            "cross.png": ["wrong", "no", "false", "bad", "error"],
            "money.png": ["cost", "price", "rich", "value", "rupee", "lakh"],
            "time.png": ["time", "late", "fast", "slow", "clock", "hour"],
            "battery.png": ["charge", "energy", "power", "full", "empty"],
            "search.png": ["find", "search", "look", "detect", "clue"],
            "lock.png": ["secret", "hidden", "safe", "secure"],
            "key.png": ["answer", "key", "unlock", "solution"]
        }

    def get_relevant_sticker(self, text):
        text = text.lower()
        candidates = []
        for filename, keywords in self.keyword_map.items():
            for kw in keywords:
                if kw in text: candidates.append(filename)
        
        if candidates:
            choice = random.choice(candidates)
            full_path = os.path.join(self.assets_dir, choice)
            if os.path.exists(full_path):
                return full_path
        return None

    def create_sliding_sticker(self, image_path, duration, start_time):
        """
        Creates a Pro 'Slide In' Sticker.
        - Fixes Transparency (Black box issue)
        - Anchors to Bottom Right (No random chaos)
        - Smooth Transition
        """
        try:
            # 1. Load with Alpha Channel (Transparent=True is key)
            # Resize immediately to 250px (smaller/cleaner)
            clip = ImageClip(image_path, transparent=True).resize(height=250)
            
            # 2. Define Position: Bottom Right Corner (Professional UI look)
            # Screen width 1080. Sticker width ~250. Padding 50.
            # X = 1080 - 250 - 50 = 780
            # Y = 1350 (Above the CTA area, below the main content)
            TARGET_X = 750
            TARGET_Y = 1350
            
            # 3. Slide Up Animation
            # It starts 200px lower (off-screen or lower) and slides up to TARGET_Y
            TRANSITION_TIME = 0.5
            
            def slide_position(t):
                if t < TRANSITION_TIME:
                    # Smooth ease-out slide
                    progress = t / TRANSITION_TIME
                    offset = 200 * (1 - progress) # Starts at 200, goes to 0
                    return (TARGET_X, TARGET_Y + offset)
                else:
                    # Hold position
                    return (TARGET_X, TARGET_Y)

            clip = clip.set_position(slide_position).set_start(start_time).set_duration(duration)
            
            # 4. Fade In/Out for smoothness
            clip = clip.crossfadein(0.2).crossfadeout(0.2)
            
            return clip

        except Exception as e:
            print(f"❌ [FX ERROR] Could not create sticker: {e}")
            return None

    def apply_visual_effects(self, base_video, script_text):
        print(f"🔍 [FX SCANNING] Script length: {len(script_text)} chars")
        layers = [base_video]
        
        total_dur = base_video.duration
        
        # LIMIT: Max 3 stickers per video to avoid clutter
        # Interval: One every 8-10 seconds
        num_stickers = min(3, int(total_dur / 8))
        if num_stickers < 1: num_stickers = 1
        
        interval = total_dur / (num_stickers + 1)
        words = script_text.split()
        chunk_size = len(words) // num_stickers
        
        added_count = 0
        
        for i in range(num_stickers):
            # Timing: precise intervals, less randomness
            t_start = (i + 1) * interval
            
            # Context Search
            start_idx = i * chunk_size
            end_idx = min(len(words), (i+1) * chunk_size)
            text_chunk = " ".join(words[start_idx:end_idx])
            
            sticker_path = self.get_relevant_sticker(text_chunk)
            
            # Only add if we actually found a relevant keyword match
            # (Removed the random "generic" fallback to avoid childish feel)
            if sticker_path:
                print(f"   ✨ Adding Sticker: {os.path.basename(sticker_path)} at {t_start:.1f}s")
                # Show for 3.5 seconds (Long enough to read)
                sticker_clip = self.create_sliding_sticker(sticker_path, 3.5, t_start)
                if sticker_clip: 
                    layers.append(sticker_clip)
                    added_count += 1

        print(f"✅ [FX DONE] Added {added_count} stickers.")
        return CompositeVideoClip(layers)