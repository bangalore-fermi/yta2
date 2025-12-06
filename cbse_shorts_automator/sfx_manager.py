"""
File: sfx_manager.py
Handles the mixing and timing of sound effects.
"""
import os
import random  # <--- NEW
from moviepy.editor import AudioFileClip
from moviepy.audio.fx.all import audio_normalize # <--- NEW

class SFXManager:
    def __init__(self, config_dir='config/sfx'):
        self.config_dir = config_dir
        # Map logical names to filenames
        self.assets = {
            # Quiz Assets
            'whoosh': 'whoosh.wav',      
            'tick': 'tick.wav',          
            'success': 'correct.wav',    
            'pop': 'pop_soft.mp3',       
            'flip': 'paper-slide.wav',   
            'swish_low': 'swish_low.wav',

            # Fact Assets (Randomized Pools)
            'glitch': ['glitch.wav', 'glitch1.wav', 'glitch2.wav', 'glitch3.mp3', 'glitch4.wav'],
            'shutter': ['dslr1.wav', 'dslr2.wav', 'dslr3.wav', 'dslr4.wav'],
            'notification': ['notification.wav', 'ping1.mp3', 'ping2.wav', 'ping3.mp3'],

            # Tip Assets (Randomized Pools)
            'zip': ['zip.wav', 'zip1.wav', 'zip2.wav'],
            'marker': 'marker.wav',
            'keyboard': ['keyboard1.wav', 'keyboard2.wav']
        }

    def get_clip(self, name, start_time, volume=1.0):
        """
        Loads an audio clip, sets its start time and volume.
        Handles list randomization and audio normalization.
        """
        asset = self.assets.get(name)
        if not asset: return None
        
        # Handle Randomization
        filename = random.choice(asset) if isinstance(asset, list) else asset
        
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            if name == 'pop': path = path.replace('.mp3', '.wav')
            if not os.path.exists(path): return None

        try:
            clip = AudioFileClip(path)
            
            # 1. NORMALIZE (Equalize volume across different files)
            try:
                clip = clip.fx(audio_normalize)
            except Exception: pass # Fallback if normalization fails

            # 2. APPLY MIXING RULES (Adjust relative to normalized 0dB)
            if name == 'whoosh': volume *= 0.15      # Reduced for normalized audio
            if name == 'swish_low': volume *= 0.25
            if name == 'flip': volume *= 0.15
            
            # New Categories
            if name == 'glitch': volume *= 0.12      # High energy, keep low
            if name == 'shutter': volume *= 0.15     # Sharp transient
            if name == 'notification': volume *= 0.15
            if name == 'zip': volume *= 0.2
            if name == 'keyboard': volume *= 0.25
            if name == 'marker': volume *= 0.2
            
            return clip.set_start(start_time).volumex(volume)
        except Exception as e:
            print(f"⚠️ SFX Load Error ({name}): {e}")
            return None

    def generate_quiz_sfx(self, timings):
        """
        Generates the standard SFX layer for a Quiz.
        timings: dict with keys 'q', 'a', 'b', 'c', 'd', 'think', 'ans'
        """
        sfx_layer = []

        # 1. Transition to Question (Whoosh)
        if 'q' in timings:
            # Trigger 0.2s before the text appears
            clp = self.get_clip('whoosh', start_time=timings['q'] - 0.2, volume=0.5)
            if clp: sfx_layer.append(clp)

        # 2. Options appearing (Pop)
        for key in ['a', 'b', 'c', 'd']:
            if key in timings:
                # Volume reduced to 0.15 (15%) as requested (further reduction from 0.2)
                clp = self.get_clip('pop', start_time=timings[key], volume=0.15)
                if clp: sfx_layer.append(clp)

        # 3. The Timer (Quad Speed Ticks)
        # We want 4 ticks per second for 3 seconds = 12 ticks total
        if 'think' in timings:
            start = timings['think']
            # Create ticks at 0.0, 0.25, 0.50, 0.75...
            for i in range(12): 
                offset = i * 0.25
                clp = self.get_clip('tick', start_time=start + offset, volume=0.6)
                if clp: sfx_layer.append(clp)

        # 4. The Answer Reveal (Chime)
        if 'ans' in timings:
            clp = self.get_clip('success', start_time=timings['ans'], volume=0.7)
            if clp: sfx_layer.append(clp)

        # 5. The CTA (Paper Slide - Subtle Transition)
        if 'cta' in timings:
            clp = self.get_clip('flip', start_time=timings['cta'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # 6. The Outro (Deep Swish - Finality)
        if 'outro' in timings:
            clp = self.get_clip('swish_low', start_time=timings['outro'], volume=0.6)
            if clp: sfx_layer.append(clp)

        return sfx_layer
    
    def generate_fact_sfx(self, timings):
        """
        SFX layer for FACT Template (Digital/Documentary).
        """
        sfx_layer = []
        
        # Hook -> Title (Glitch)
        if 'title' in timings:
            clp = self.get_clip('glitch', start_time=timings['title'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # Reveal (Shutter)
        if 'details' in timings:
            clp = self.get_clip('shutter', start_time=timings['details'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # CTA (Notification)
        if 'cta' in timings:
            clp = self.get_clip('notification', start_time=timings['cta'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # Outro (Deep Swish)
        if 'outro' in timings:
            clp = self.get_clip('swish_low', start_time=timings['outro'], volume=1.0)
            if clp: sfx_layer.append(clp)

        return sfx_layer

    def generate_tip_sfx(self, timings):
        """
        SFX layer for TIP Template (Productivity/Hacker).
        """
        sfx_layer = []

        # Hook -> Title (Zip)
        if 'title' in timings:
            clp = self.get_clip('zip', start_time=timings['title'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # Reveal (Marker)
        if 'content' in timings:
            clp = self.get_clip('marker', start_time=timings['content'], volume=1.0)
            if clp: sfx_layer.append(clp)
            
        # Bonus (Pop)
        if 'bonus' in timings:
            clp = self.get_clip('pop', start_time=timings['bonus'], volume=0.2)
            if clp: sfx_layer.append(clp)

        # CTA (Keyboard)
        if 'cta' in timings:
            clp = self.get_clip('keyboard', start_time=timings['cta'], volume=1.0)
            if clp: sfx_layer.append(clp)

        # Outro (Deep Swish)
        if 'outro' in timings:
            clp = self.get_clip('swish_low', start_time=timings['outro'], volume=1.0)
            if clp: sfx_layer.append(clp)

        return sfx_layer