#!/usr/bin/env python3
"""
File: shorts_engine.py
Core engine for generating YouTube Shorts.
UPDATED: Stickers SUSPENDED (Bypass Mode) for stability.
"""

import imagemagick_setup
import os
import json
import random
import textwrap
import glob
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip, 
    AudioFileClip, ColorClip, CompositeAudioClip,
    ImageClip, vfx
)

from moviepy.audio.fx.all import audio_normalize
from voice_manager import VoiceManager
from effects_manager import EffectsManager 

# Theme configurations
THEMES = {
    'energetic_yellow': {
        'bg_color': (15, 23, 42), 'highlight': '#FACC15', 'correct': '#22C55E', 'name': 'Energetic Yellow',
        'music_mood': 'energetic'
    },
    'calm_blue': {
        'bg_color': (13, 27, 42), 'highlight': '#38BDF8', 'correct': '#34D399', 'name': 'Calm Blue',
        'music_mood': 'calm'
    },
    'vibrant_purple': {
        'bg_color': (24, 7, 45), 'highlight': '#E879F9', 'correct': '#A78BFA', 'name': 'Vibrant Purple',
        'music_mood': 'funky'
    },
    'fresh_green': {
        'bg_color': (7, 36, 19), 'highlight': '#84CC16', 'correct': '#4ADE80', 'name': 'Fresh Green',
        'music_mood': 'calm'
    },
    'classic_red': {
        'bg_color': (28, 25, 23), 'highlight': '#FB923C', 'correct': '#F87171', 'name': 'Classic Red',
        'music_mood': 'energetic'
    }
}

FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
WIDTH = 1080
HEIGHT = 1920

class ShortsEngine:
    def __init__(self, config_path='config/generator_config.json'):
        if not os.path.exists('config'): os.makedirs('config')
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump({
                    "MAX_ROWS_TO_PROCESS": 10, 
                    "DELETE_TEMP_FILES": True, 
                    "CHANNEL_NAME": "NCERT QuickPrep",
                    "DIRS": {"TEMP": "temp", "OUTPUT": "shorts", "DOWNLOADS": "downloads"}
                }, f)
        
        with open(config_path, 'r') as f: self.config = json.load(f)
        
        self.channel_name = self.config.get('CHANNEL_NAME', 'SUBSCRIBE NOW')
        self.logo_path = 'config/logo.png'
        
        self.music_dir = 'config/music'
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)
            for mood in ['energetic', 'calm', 'funky']:
                os.makedirs(os.path.join(self.music_dir, mood), exist_ok=True)
        
        # Initialize Visual FX Manager (Loaded but not used in bypass mode)
        self.fx_manager = EffectsManager()

        self.voice_manager = VoiceManager()

        import moviepy.config as mpconf
        temp_dir = self.config['DIRS']['TEMP']
        os.makedirs(temp_dir, exist_ok=True)
        mpconf.TEMP_DIR = temp_dir 

    def get_theme(self, theme_name='energetic_yellow'):
        return THEMES.get(theme_name, THEMES['energetic_yellow'])

    def get_contrast_color(self, bg_color_hex):
        if not bg_color_hex or not isinstance(bg_color_hex, str): return 'white'
        hex_color = bg_color_hex.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Calculate luminance (Human eye perception)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # CHANGED: Threshold lowered from 0.6 to 0.5
        # This means "Black Text" triggers earlier (on medium colors), avoiding white-on-light-green.
        return 'black' if luminance > 0.5 else 'white'

    # === BYPASS MODE: SKIPS STICKERS ===
    def render_with_effects(self, video_clip, script_data, output_path):
        """
        Renders the video to disk.
        NOTE: Visual FX (Stickers) are currently SUSPENDED for stability.
        """
        print("✨ FX SUSPENDED: Rendering clean video (no stickers)...")
        
        # We skip self.fx_manager.apply_visual_effects()
        # and just render the raw clip directly.
        
        print(f"🎬 Rendering final video to: {output_path}")
        video_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='ultrafast' # Keeps the speed gain
        )

    def create_outro(self, duration, cta_text="SUBSCRIBE FOR MORE!"):
        bg_color = (255, 255, 255) 
        bg = ColorClip(size=(WIDTH, HEIGHT), color=bg_color, duration=duration)
        clips = [bg]
        center_y = HEIGHT / 2
        
        if os.path.exists(self.logo_path):
            try:
                logo = ImageClip(self.logo_path).set_duration(duration)
                if logo.w > 450 or logo.h > 450: logo = logo.resize(height=450)
                
                def pulse(t): return 1.0 + 0.05 * (1 - abs((t % 1.0) - 0.5) * 2)
                logo = logo.resize(pulse).set_position(('center', center_y - 200))
                clips.append(logo)
                
                name_clip = TextClip(
                    self.channel_name.upper(),
                    fontsize=60, color='black', font=FONT_BOLD,
                    stroke_color='black', stroke_width=2
                ).set_position(('center', center_y + 300)).set_duration(duration)
                clips.append(name_clip)
            except Exception as e:
                print(f"⚠️ Logo error: {e}")
                txt = TextClip(self.channel_name, fontsize=80, color='black', font=FONT_BOLD).set_position('center').set_duration(duration)
                clips.append(txt)
        else:
            name_clip = TextClip(
                self.channel_name.upper(),
                fontsize=85, color='black', font=FONT_BOLD
            ).set_position(('center', center_y - 50)).set_duration(duration)
            
            cta_clip = TextClip(
                cta_text,
                fontsize=50, color='black', font=FONT_BOLD
            ).set_position(('center', center_y + 100)).set_duration(duration)
            
            clips.extend([name_clip, cta_clip])

        return CompositeVideoClip(clips, size=(WIDTH, HEIGHT)).crossfadein(0.5)

    def add_background_music(self, voice_track, total_duration, theme_name='energetic_yellow'):
        mood = self.get_theme(theme_name).get('music_mood', 'energetic')
        search_path = os.path.join(self.music_dir, mood, "*.mp3")
        tracks = glob.glob(search_path) or glob.glob(os.path.join(self.music_dir, "*.mp3"))
        
        if not tracks:
            legacy = 'config/music.mp3'
            if os.path.exists(legacy): tracks = [legacy]
            else: return voice_track
            
        chosen = random.choice(tracks)
        print(f"🎵 Adding Music: {os.path.basename(chosen)} (Mood: {mood})")
        
        try:
            bgm = AudioFileClip(chosen)
            
            # ATTEMPT NORMALIZATION (Handle failure gracefully)
            vol_level = 0.12
            try:
                # FIXED: Removed 'vfx.' prefix, using imported audio_normalize directly
                bgm = bgm.fx(audio_normalize)
                vol_level = 0.12 # Boost volume if normalized (0.12 is too quiet for normalized peaks)
            except Exception as e:
                print(f"⚠️ Normalization skipped (Error: {e})")
            
            if bgm.duration < total_duration:
                bgm = bgm.loop(n=int(total_duration/bgm.duration)+1)
                
            return CompositeAudioClip([voice_track, bgm.subclip(0, total_duration).volumex(vol_level)])
        except Exception as e:
            print(f"❌ Background Music Failed: {e}")
            return voice_track

    def create_text_clip(self, text, fontsize, color='white', bg_color=None, bold=False, stroke_color=None, stroke_width=0, wrap_width=25, align='center'):
        def to_hex(c): return '#%02x%02x%02x' % (int(c[0]), int(c[1]), int(c[2])) if isinstance(c, (tuple, list)) else c
        color, bg_color, stroke_color = to_hex(color), to_hex(bg_color), to_hex(stroke_color)
        
        if color == 'white' and stroke_width == 0 and bg_color is None:
             stroke_color, stroke_width = 'black', 2

        wrapped = "\n".join(textwrap.wrap(text, width=wrap_width))
        try:
            return TextClip(wrapped, fontsize=int(fontsize), color=color, font=FONT_BOLD if bold else FONT_REGULAR, 
                            bg_color=bg_color, stroke_color=stroke_color, stroke_width=stroke_width, 
                            method='caption', size=(WIDTH - 100, None), align=align)
        except Exception:
            return TextClip(wrapped, fontsize=int(fontsize), color=color, font=FONT_BOLD if bold else FONT_REGULAR)

    def create_background(self, theme_name, duration, video_clip=None):
        theme = self.get_theme(theme_name)
        if video_clip:
            try:
                bg = video_clip.resize(height=HEIGHT)
                x = bg.w / 2
                bg = bg.crop(x1=x - WIDTH/2, y1=0, width=WIDTH, height=HEIGHT).resize(0.05).resize(height=HEIGHT).fx(vfx.colorx, 0.35)
                return bg.set_duration(duration)
            except Exception: pass
        return ColorClip(size=(WIDTH, HEIGHT), color=theme['bg_color'], duration=duration)

    def apply_ken_burns(self, clip, zoom_factor=1.15):
        if not hasattr(clip, 'duration') or not clip.duration: return clip
        return clip.resize(lambda t: 1.0 + (zoom_factor - 1.0) * (t / clip.duration))

    def generate_short(self, video_path, pdf_path, script, config, output_path, class_level=None):
        try:
            t_type = config.get('template', 'quiz')
            if t_type == 'quiz': from template_quiz import QuizTemplate; template = QuizTemplate(self)
            elif t_type == 'fact': from template_fact import FactTemplate; template = FactTemplate(self)
            elif t_type == 'tip': from template_tip import TipTemplate; template = TipTemplate(self)
            else: raise ValueError(f"Unknown template: {t_type}")
            
            result = template.generate(video_path, script, config, output_path)
            return {'success': True, 'output_path': output_path, 'duration': result.get('duration', 0)}
        except Exception as e:
            import traceback; traceback.print_exc()
            return {'success': False, 'error': str(e)}

def generate_random_config(class_level=None):
    templates = ['quiz', 'fact', 'tip']
    themes = list(THEMES.keys())
    opening_styles = ['countdown', 'montage', 'mystery']
    
    config = {
        'template': random.choice(templates),
        'voice': VoiceManager.get_random_voice_name(),
        'theme': random.choice(themes),
        'cta_style': random.choice(['persistent', 'bookend', 'both']),
        'opening_style': random.choice(opening_styles),
        'class_level': class_level or random.randint(6, 12),
        'retention_strategy': random.choice(['cliffhanger', 'teaser', 'curiosity'])
    }
    return config