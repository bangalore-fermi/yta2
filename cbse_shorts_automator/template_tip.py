#!/usr/bin/env python3
"""
File: template_tip.py
Tip template for YouTube Shorts
UPDATED: Bigger Fonts, Higher Positioning, Better Readability.
"""

import imagemagick_setup
import os
import concurrent.futures
from moviepy.editor import CompositeVideoClip, CompositeAudioClip, TextClip, AudioFileClip, vfx
from voice_manager import VoiceManager
from karaoke_manager import KaraokeManager
from video_processor import VideoProcessor
from sfx_manager import SFXManager  # <--- NEW IMPORT

WIDTH = 1080
HEIGHT = 1920

def hex_to_rgb(hex_color):
    if isinstance(hex_color, str) and hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return hex_color

class TipTemplate:
    def __init__(self, engine):
        self.engine = engine
    
    def generate(self, video_path, script, config, output_path):
        print("📝 Generating Tip Template (Parallel Processing)...")
        
        theme = self.engine.get_theme(config.get('theme', 'fresh_green'))
        voice_name = config.get('voice', 'NeeraNeural2')
        
        voice_mgr = self.engine.voice_manager
        # Select ONE voice for entire video
        selected_voice_key = voice_name if voice_name else voice_mgr.get_random_voice_name()
        print(f"   🎤 Using voice: {selected_voice_key} (consistent across all segments)")
        video_proc = VideoProcessor(temp_dir=self.engine.config['DIRS']['TEMP'])
        karaoke_mgr = KaraokeManager(voice_mgr, self.engine.config['DIRS']['TEMP'])
        sfx_mgr = SFXManager() # <--- NEW INITIALIZATION
        
        vid_id = os.path.basename(output_path).split('.')[0]
        temp_dir = self.engine.config['DIRS']['TEMP']
        audio_files = []
        
        
        # 1. Parallel Audio (Unified)
        print("   🎙️  Synthesizing voiceover tracks...")
        audio_tasks = {
            'hook': script['hook_spoken'],
            'title': script['tip_title'],
            'content': script['tip_spoken'], # Content moved to parallel
            'bonus': script['bonus'],
            'cta': script['cta_spoken']
        }
        
        generated_audio_paths = {}

        def generate_single_audio(key, text):
            path = f"{temp_dir}/{vid_id}_{key}.mp3"
            voice_mgr.generate_audio_with_specific_voice(text, path, selected_voice_key, provider='google')
            return key, path

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_single_audio, k, t) for k, t in audio_tasks.items()]
            for future in concurrent.futures.as_completed(futures):
                k, path = future.result()
                generated_audio_paths[k] = path
                audio_files.append(path)
        
        # Load all clips from the parallel generation dict
        aud_hook = AudioFileClip(generated_audio_paths['hook'])
        aud_title = AudioFileClip(generated_audio_paths['title'])
        aud_content = AudioFileClip(generated_audio_paths['content']) # Loaded from parallel
        aud_bonus = AudioFileClip(generated_audio_paths['bonus'])
        aud_cta = AudioFileClip(generated_audio_paths['cta'])
        
        #print("   🎵 Aligning Karaoke text...")
        #aud_content, content_segments = karaoke_mgr.generate_timed_audio(script['tip_content'], f"{vid_id}_content", voice_key=selected_voice_key)
        # === CHANGE 1: Use 'tip_spoken' for Audio (No Karaoke Splitting) ===
        #print("   🎵 Generating Tip Audio...")
        
        # Use the explicit spoken text from Gemini
        #content_audio_path = f"{temp_dir}/{vid_id}_content.mp3"
        #voice_mgr.generate_audio_with_specific_voice(script['tip_spoken'], content_audio_path, selected_voice_key)
        #audio_files.append(content_audio_path)
        
        #aud_content = AudioFileClip(content_audio_path)
        # Note: We do NOT generate 'content_segments' anymore
        #audio_files.append(f"{temp_dir}/{vid_id}_content.mp3")
        
        # 2. Timing
        t_hook = 0
        t_title = t_hook + aud_hook.duration
        t_content = t_title + aud_title.duration
        t_bonus = t_content + aud_content.duration
        t_cta = t_bonus + aud_bonus.duration
        t_outro = t_cta + aud_cta.duration # NEW: Precise outro start
        
        OUTRO_DURATION = 4.0
        total_dur = t_cta + aud_cta.duration + OUTRO_DURATION
        
        # 3. Visuals
        print(f"   🧠 AI Watching video to find relevant clips ({int(total_dur)}s)...")
        src_vid = video_proc.prepare_video_for_short(video_path, total_dur, script=script, width=WIDTH)
        src_vid = src_vid.set_position(('center', 0))
        bg = self.engine.create_background(config.get('theme'), total_dur, video_clip=src_vid)
        clips = [bg, src_vid]

        # === MISSING FUNCTION ===
        def force_rgb(clip):
            try:
                if hasattr(clip, 'img') and clip.img is not None and clip.img.ndim == 2:
                    return clip.fx(vfx.to_RGB)
            except: pass
            return clip
        # ========================
        
        CARD_START_Y = 750
        
        # 4. Text Overlays
        clips.append(self.engine.create_text_clip("💡 EXAM TIP 💡", fontsize=65, color=theme['highlight'], bold=True, bg_color=(0,0,0)).set_position(('center', CARD_START_Y)).set_start(0).set_duration(total_dur))
        
        TITLE_Y = CARD_START_Y + 120
        clips.append(self.engine.create_text_clip(script['tip_title'], fontsize=60, color='white', bold=True, wrap_width=20, stroke_color='black', stroke_width=2, align='North').set_position(('center', TITLE_Y)).set_start(t_title).set_duration(total_dur - t_title))
        
       # Content (Huge Font)
        CONTENT_Y = TITLE_Y + 250
        ans_bg_color = theme['correct']
        ans_text_color = self.engine.get_contrast_color(ans_bg_color)
        
        # Readability Fix
        stroke_col = 'black' if ans_text_color == 'white' else None
        stroke_wid = 3 if ans_text_color == 'white' else 0
        # === CHANGE 2: Use 'tip_visual' for Static Screen Text ===
        # This shows the Memory Hack/Formula clearly while the voice explains it
        
        tip_card_clip = self.engine.create_text_clip(
            script['tip_visual'], # <--- UPDATED
            fontsize=95,          # Huge font retained for impact
            color=ans_text_color,
            bg_color=ans_bg_color, 
            stroke_color=stroke_col,
            stroke_width=stroke_wid, 
            bold=True,
            wrap_width=20,        # Tighter wrap for big font
            align='center'
        )
        
        # Duration matches the spoken explanation exactly
        tip_card_clip = tip_card_clip.set_position(('center', CONTENT_Y)).set_start(t_content).set_duration(aud_content.duration)
        clips.append(force_rgb(tip_card_clip))

        # (Delete the old 'for seg in content_segments:' loop completely)
        
        # Bonus Tip (Moved Up)
        BONUS_Y = CONTENT_Y + 400 
        clips.append(self.engine.create_text_clip(
            f"⭐ {script['bonus']}", 
            fontsize=55, # Bigger
            color=theme['highlight'], 
            bold=True, 
            wrap_width=20, 
            stroke_color='black', 
            stroke_width=2
        ).set_position(('center', BONUS_Y)).set_start(t_bonus).set_duration(total_dur - t_bonus))
        
        # CTA (Moved Up)
        cta_display = f"🚀 {script['cta_spoken']}"
        cta_duration = aud_cta.duration # CHANGED: Duration matches audio
        
        cta_bg = theme['correct'] 
        cta_txt = 'white'
        
        clips.append(self.engine.create_text_clip(
            cta_display, 
            fontsize=65, 
            color=cta_txt, 
            bg_color=cta_bg, 
            bold=True, 
            wrap_width=18
        ).set_position(('center', HEIGHT - 400)).set_start(t_cta).set_duration(cta_duration))

        # Outro
        outro = self.engine.create_outro(
            duration=OUTRO_DURATION,
            cta_text="SUBSCRIBE FOR TIPS!"
        ).set_start(t_outro) # CHANGED: Start t_outro
        clips.append(outro)

        # NEW: SFX Layering
        print("   🔊 Engineering SFX Layer...")
        sfx_timings = {
            'title': t_title,
            'content': t_content,
            'bonus': t_bonus,
            'cta': t_cta,
            'outro': t_outro
        }
        sfx_clips = sfx_mgr.generate_tip_sfx(sfx_timings)


        audio_list = [
            aud_hook.set_start(t_hook), 
            aud_title.set_start(t_title), 
            aud_content.set_start(t_content), 
            aud_bonus.set_start(t_bonus), 
            aud_cta.set_start(t_cta)
        ]
        
        full_audio_stack = audio_list + sfx_clips # Combine Voice + SFX
        final_audio = self.engine.add_background_music(CompositeAudioClip(full_audio_stack), total_dur)
        final_raw = CompositeVideoClip(clips, size=(WIDTH, HEIGHT)).set_audio(final_audio)
        
        try:
            self.engine.render_with_effects(final_raw, script, output_path)
        finally:
            if self.engine.config.get('DELETE_TEMP_FILES', True):
                import glob
                for f in audio_files:
                    if os.path.exists(f): os.remove(f)
                for pattern in [f'{temp_dir}/{vid_id}*', f'{vid_id}*TEMP_*']:
                    for temp_file in glob.glob(pattern):
                        try: os.remove(temp_file)
                        except: pass

        return {'duration': total_dur}