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
from visual_effects_quiz import FPS

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
            fps=FPS,
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

    def _get_contrast_text_color(self, bg_color):
        """
        Calculate optimal text color based on background luminance.
        Returns 'white' or 'black' for maximum contrast.
        """
        # Handle different color formats
        if isinstance(bg_color, str):
            if bg_color.startswith('#'):
                hex_color = bg_color.lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                return 'white'  # Fallback
        elif isinstance(bg_color, (tuple, list)):
            r, g, b = bg_color[0], bg_color[1], bg_color[2]
        else:
            return 'white'  # Fallback
        
        # Calculate relative luminance (human eye perception)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        # Return contrasting color
        return 'black' if luminance > 0.5 else 'white'    

    def create_outro_v2(self, duration, theme, usp_message=None, cta_text="SUBSCRIBE FOR MORE!"):
        """
        Creates themed, animated outro with USP messaging.
        
        Args:
            duration: Outro duration (typically 4 seconds)
            theme: Theme dictionary with colors
            usp_message: Tuple of (line1, line2) for USP text, or None for random
            cta_text: Call-to-action text
            
        Returns:
            CompositeVideoClip with animated outro
        """
        from visual_effects_quiz import res_scale, WIDTH, HEIGHT
        from usp_content_variations import USPContent
        import math
        
        clips = []
        
        # ============================================================
        # BACKGROUND - Theme colored with subtle gradient
        # ============================================================
        
        # Main background (theme's bg_color)
        bg_color = theme.get('bg_color', (15, 23, 42))
        bg = ColorClip(size=(WIDTH, HEIGHT), color=bg_color, duration=duration)
        clips.append(bg)
        
        # Radial gradient overlay (theme's highlight color)
        highlight_color = theme.get('highlight', '#FACC15')
        if isinstance(highlight_color, str) and highlight_color.startswith('#'):
            hex_color = highlight_color.lstrip('#')
            highlight_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            highlight_rgb = highlight_color
        
        # Create 3-layer radial gradient (centered)

        num_grd_layers=1
            #for i in range(num_grd_layers):  # 3 gradient layers
                #radius = res_scale(50) + (i * res_scale())v
        for i in range(num_grd_layers):
            radius = res_scale(30) + (i * (HEIGHT//2//num_grd_layers))
            opacity = 0.12 - (i//num_grd_layers * 0.03)
            
            gradient_circle = ColorClip(
                size=(radius*2, radius*2),
                color=highlight_rgb
            ).set_opacity(opacity)
            
            gradient_circle = gradient_circle.set_position(
                (WIDTH//2 - radius, HEIGHT//2 - radius)
            ).set_duration(duration)
            
            clips.append(gradient_circle)
        
        # ============================================================
        # LOGO - Elastic entrance animation
        # ============================================================
        
        center_y = HEIGHT // 2
        
        if os.path.exists(self.logo_path):
            try:
                from moviepy.editor import ImageClip
                
                logo = ImageClip(self.logo_path).set_duration(duration)
                
                # Resize logo to reasonable size
                target_logo_height = res_scale(450)
                print(f"logo target height={target_logo_height}, actual height = {logo.h}")
                if logo.h > target_logo_height:
                    logo = logo.resize(height=target_logo_height)
                
                # Entrance animation: elastic scale-up with rotation
                def logo_animation(t):
                    if t < 0.8:  # 0.8s entrance
                        progress = t / 0.8
                        # Elastic easing with overshoot
                        if progress < 0.5:
                            MIN_SCALE = 0.01
                            scale = MIN_SCALE + (1.0 - MIN_SCALE) * (progress * 2)
                        else:
                            # Overshoot and settle
                            overshoot = math.sin((progress - 0.5) * 2 * math.pi) * 0.15
                            scale = 1.0 + overshoot
                        
                        # Slight rotation during entrance
                        rotation = (1 - progress) * -15  # -15° to 0°
                        
                        return scale
                    else:
                        # Gentle pulse after entrance
                        pulse_t = (t - 0.8) / (duration - 0.8)
                        scale = 1.0 + 0.03 * math.sin(pulse_t * 2 * math.pi)
                        return scale
                print("before logo animation")
                logo = logo.resize(logo_animation)
                
                # Position above center
                logo = logo.set_position(('center', HEIGHT//4))
                clips.append(logo)
                
                logo_present = True
                
            except Exception as e:
                print(f"⚠️ Logo loading failed: {e}")
                logo_present = False
        else:
            logo_present = False
        
        # ============================================================
        # CHANNEL NAME - Fade in with slight rise
        # ============================================================
        
        try:
            from moviepy.editor import TextClip
            
            channel_name_y = center_y + res_scale(50) if logo_present else center_y - res_scale(80)
            # Calculate contrast color for theme background
            text_color = self._get_contrast_text_color(bg_color)
            stroke_color = 'black' if text_color == 'white' else 'white'

            name_clip = TextClip(
                self.channel_name.upper(),
                fontsize=res_scale(70),
                color=text_color,  # ✅ Adaptive
                font='Arial-Bold',
                stroke_color=stroke_color,  # ✅ Contrasting stroke
                stroke_width=res_scale(3),
                method='label'
            )
            
            # Fade in + rise animation
            def name_animation(t):
                if t < 1.0:
                    progress = t / 1.0
                    offset_y = (1 - progress) * res_scale(30)  # Rise 30px
                    return ('center', channel_name_y + offset_y)
                return ('center', channel_name_y)
            
            name_clip = name_clip.set_position(name_animation)
            name_clip = name_clip.set_start(0.5).set_duration(duration - 0.5)
            name_clip = name_clip.crossfadein(0.5)
            
            clips.append(name_clip)
            
        except Exception as e:
            print(f"⚠️ Channel name creation failed: {e}")
        
        # ============================================================
        # USP MESSAGING - Two-line tagline
        # ============================================================
        
        if usp_message is None:
            usp_message = USPContent.get_random_outro()
        
        line1, line2 = usp_message
        
        try:
            # Line 1: Main USP (larger, highlight color)
            usp_y_base = center_y + res_scale(160) if logo_present else center_y + res_scale(40)
            
            usp_line1 = TextClip(
                line1,
                fontsize=res_scale(52),
                color=highlight_color,
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=res_scale(1),
                method='label'
            )
            
            usp_line1 = usp_line1.set_position(('center', usp_y_base))
            usp_line1 = usp_line1.set_start(1.0).set_duration(duration - 1.0)
            usp_line1 = usp_line1.crossfadein(0.4)
            
            clips.append(usp_line1)
            
            usp_line2 = TextClip(
                line2,
                fontsize=res_scale(42),
                color=text_color,  # ✅ Same as channel name
                font='Arial',
                stroke_color=stroke_color,
                stroke_width=res_scale(1),
                method='label'
            )
            
            usp_line2 = usp_line2.set_position(('center', usp_y_base + res_scale(70)))
            usp_line2 = usp_line2.set_start(1.5).set_duration(duration - 1.5)
            usp_line2 = usp_line2.crossfadein(0.4)
            
            clips.append(usp_line2)
            
        except Exception as e:
            print(f"⚠️ USP text creation failed: {e}")
        
        # ============================================================
        # SUBSCRIBE BUTTON - Pulsing call-to-action
        # ============================================================
        
        try:
            button_y = HEIGHT - res_scale(500)
            button_width = res_scale(600)
            button_height = res_scale(500)
            
            # Button background (highlight color)
            button_bg = ColorClip(
                size=(button_width, button_height),
                color=highlight_rgb
            ).set_opacity(0.95)
            
            # Pulsing animation
            def button_pulse(t):
                if t < 2.0:
                    return ('center', button_y)
                else:
                    pulse_t = (t - 2.0) / 1.5
                    scale = 1.0 + 0.08 * abs(math.sin(pulse_t * 3 * math.pi))
                    offset_y = (1 - scale) * button_height / 2
                    return ('center', button_y + offset_y)
            
            button_bg = button_bg.resize(lambda t: 1.0 + 0.08 * abs(math.sin(max(0, t - 2.0) / 1.5 * 3 * math.pi)) if t > 2.0 else 1.0)
            button_bg = button_bg.set_position(button_pulse)
            button_bg = button_bg.set_start(2.0).set_duration(duration - 2.0)
            button_bg = button_bg.crossfadein(0.3)
            
            clips.append(button_bg)
            
            # Button text
            button_text = TextClip(
                "🔔 " + cta_text,
                fontsize=res_scale(48),
                color='white',
                font='Arial-Bold',
                method='label'
            )
            
            button_text = button_text.set_position(('center', button_y - res_scale(100)))
            button_text = button_text.set_start(2.0).set_duration(duration - 2.0)
            button_text = button_text.crossfadein(0.3)
            
            clips.append(button_text)
            
        except Exception as e:
            print(f"⚠️ Button creation failed: {e}")
        
        # ============================================================
        # COMPOSITE & RETURN
        # ============================================================
        
        outro_clip = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        
        # Add subtle fade-in at start
        outro_clip = outro_clip.crossfadein(0.5)
        
        return outro_clip
    
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
            #if t_type == 'quiz': from template_quiz import QuizTemplate; template = QuizTemplate(self)
            if t_type == 'quiz': from template_quiz_json_generator import QuizTemplate; template = QuizTemplate(self)
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