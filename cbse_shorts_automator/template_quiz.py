#!/usr/bin/env python3
"""
File: template_quiz.py
Quiz template for YouTube Shorts
UPDATED: 
- Parallel Audio (Fast)
- CTA moved up & bigger (Visual Polish)
- Karaoke readability (Black Stroke)
"""

import imagemagick_setup
import os
import concurrent.futures
from moviepy.editor import CompositeVideoClip, CompositeAudioClip, ColorClip, AudioFileClip, TextClip, vfx
from voice_manager import VoiceManager
from karaoke_manager import KaraokeManager
from video_processor import VideoProcessor
from sfx_manager import SFXManager  # <--- NEW IMPORT

WIDTH = 1080
HEIGHT = 1920

class QuizTemplate:
    def __init__(self, engine):
        self.engine = engine
    
    def generate(self, video_path, script, config, output_path):
        print("📝 Generating Quiz Template (Parallel Processing)...")
        
        theme = self.engine.get_theme(config.get('theme', 'energetic_yellow'))
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
        
        # 1. Parallel Audio Generation
        print("   🎙️  Synthesizing 8 voiceover tracks...")
        audio_tasks = {
            'hook': script['hook_spoken'],
            'question': script['question_spoken'],
            'opt_a': f"A: {script['opt_a_spoken']}",
            'opt_b': f"B: {script['opt_b_spoken']}",
            'opt_c': f"C: {script['opt_c_spoken']}",
            'opt_d': f"D: {script['opt_d_spoken']}",
            'think': "Think fast!",
            # SEPARATED: Explanation and CTA are now distinct files
            'explanation': f"The answer is {script['correct_opt']}! {script['explanation_spoken']}",
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

        aud_hook = AudioFileClip(generated_audio_paths['hook'])
        aud_q = AudioFileClip(generated_audio_paths['question'])
        aud_a = AudioFileClip(generated_audio_paths['opt_a'])
        aud_b = AudioFileClip(generated_audio_paths['opt_b'])
        aud_c = AudioFileClip(generated_audio_paths['opt_c'])
        aud_d = AudioFileClip(generated_audio_paths['opt_d'])
        aud_think = AudioFileClip(generated_audio_paths['think'])
        aud_expl = AudioFileClip(generated_audio_paths['explanation'])
        aud_cta = AudioFileClip(generated_audio_paths['cta'])
        
       

        # 2. Timing
        THINK_TIME = 3.0 
        t_hook = 0
        t_q = t_hook + aud_hook.duration
        t_a = t_q + aud_q.duration
        t_b = t_a + aud_a.duration
        t_c = t_b + aud_b.duration
        t_d = t_c + aud_c.duration
        t_think = t_d + aud_d.duration
        t_ans = t_think + THINK_TIME
        
        t_cta = t_ans + aud_expl.duration
        t_outro = t_cta + aud_cta.duration
        
        OUTRO_DURATION = 4.0
        total_dur = t_outro + OUTRO_DURATION
        
        # 3. Visuals
        print(f"   🧠 AI Watching video to find relevant clips ({int(total_dur)}s)...")
        src_vid = video_proc.prepare_video_for_short(video_path, total_dur, script=script, width=WIDTH)
        src_vid = src_vid.set_position(('center', 0))
        
        bg = self.engine.create_background(config.get('theme'), total_dur, video_clip=src_vid)
        clips = [bg, src_vid]
        
        def force_rgb(clip):
            try:
                if hasattr(clip, 'img') and clip.img is not None and clip.img.ndim == 2:
                    return clip.fx(vfx.to_RGB)
            except: pass
            return clip

        CARD_START_Y = 750 
        
        # 4. Text Overlays
        # Watch Till End
        hook_box = theme['highlight']
        hook_txt = self.engine.get_contrast_color(hook_box)
        
        hook_clip = TextClip("🔥 WATCH TILL END 🔥", fontsize=45, color=hook_txt, bg_color=hook_box, font='Arial-Bold', method='label', size=(WIDTH, 110))
        hook_clip = hook_clip.set_position(('center', CARD_START_Y)).set_start(0).set_duration(2)
        clips.append(force_rgb(hook_clip))
        
        # Question
        QUESTION_Y = CARD_START_Y + 130 
        q_clip = self.engine.create_text_clip(script['question_visual'], fontsize=55, color=theme['highlight'], bold=True, wrap_width=25, align='North', stroke_color='black', stroke_width=2)
        q_clip = q_clip.set_position(('center', QUESTION_Y)).set_start(t_q).set_duration(total_dur - t_q)
        clips.append(force_rgb(q_clip))
        
        # Options
        OPT_START_Y = QUESTION_Y + 350
        GAP = 110
        opt_bg = theme['bg_color']
        
        if isinstance(opt_bg, str):
             if opt_bg.startswith('#'):
                opt_bg = opt_bg.lstrip('#')
                opt_bg = tuple(int(opt_bg[i:i+2], 16) for i in (0, 2, 4))
        
        options = [(f"A) {script['opt_a_visual']}", t_a), (f"B) {script['opt_b_visual']}", t_b), 
                   (f"C) {script['opt_c_visual']}", t_c), (f"D) {script['opt_d_visual']}", t_d)]
        
        for i, (txt, t) in enumerate(options):
            o_clip = self.engine.create_text_clip(txt, fontsize=45, color='white', bg_color=opt_bg, wrap_width=30, align='West')
            o_clip = o_clip.set_position(('center', OPT_START_Y + GAP * i)).set_start(t).set_duration(total_dur - t)
            clips.append(force_rgb(o_clip))

        # Timer
        timer_base_y = OPT_START_Y + GAP * 4 + 30
        timer_bar_y = timer_base_y + 160
        bar_color = theme['correct']
        if isinstance(bar_color, str) and bar_color.startswith('#'):
             bar_color = tuple(int(bar_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
             
        segments = 10
        seg_w = WIDTH // segments
        for i in range(segments):
            seg = ColorClip(size=(seg_w - 2, 40), color=bar_color).set_position((i * seg_w, timer_bar_y))
            dt = t_think + (THINK_TIME * (i + 1) / segments)
            seg = seg.set_start(t_think).set_end(dt)
            clips.append(seg) 

        for i in range(int(THINK_TIME)):
            num = int(THINK_TIME) - i
            n_clip = TextClip(str(num), fontsize=140, color='white', font='Arial-Bold', stroke_color='black', stroke_width=5)
            n_clip = n_clip.set_position(('center', timer_base_y)).set_start(t_think + i).set_duration(1)
            clips.append(force_rgb(n_clip))
        
        # Answer
        ans_bg = theme['correct']
        ans_txt = self.engine.get_contrast_color(ans_bg)
        
        # FIX: Stroke logic for green backgrounds
        stroke_col = 'black' if ans_txt == 'white' else None
        stroke_wid = 3 if ans_txt == 'white' else 0

        # Create the visual summary text (e.g., "✅ A: H₂O")
        # Fallback to spoken text if visual is missing, but visual is preferred
        visual_content = script.get('explanation_visual', script.get('explanation_spoken', ''))
        visual_display = f"✅ {script['correct_opt']}: {visual_content}"
        
        summary_clip = self.engine.create_text_clip(
            visual_display, 
            fontsize=50, 
            color=ans_txt, 
            bg_color=ans_bg, 
            stroke_color=stroke_col, # Readability Fix
            stroke_width=stroke_wid,
            bold=True, 
            wrap_width=25, 
            align='center'
        )
        
        # Position: Replaces the Options area. 
        # Duration: Matches exactly the length of the spoken explanation audio.
        summary_clip = summary_clip.set_position(('center', OPT_START_Y)).set_start(t_ans).set_duration(aud_expl.duration)
        clips.append(force_rgb(summary_clip))

        # CTA - UPGRADE (Bigger, Moved Up, Highlight Color)
        cta_bg = theme['highlight']
        cta_txt_color = 'black' # High contrast
        cta_display = f"🚀 {script['cta_spoken']}"
        cta_duration = aud_cta.duration # CHANGED: Duration now matches CTA audio length
        
        clips.append(self.engine.create_text_clip(
            cta_display, 
            fontsize=65, 
            color=cta_txt_color, 
            bg_color=cta_bg, 
            bold=True, 
            wrap_width=20
        ).set_position(('center', HEIGHT - 350)).set_start(t_cta).set_duration(cta_duration)) # CHANGED: Start time is t_cta

        # Outro
        outro = self.engine.create_outro(
            duration=OUTRO_DURATION, 
            cta_text="SUBSCRIBE FOR MORE!"
        ).set_start(t_outro) # CHANGED: Start time is t_outro
        clips.append(outro)

        # Audio
        # === NEW SFX IMPLEMENTATION ===
        print("   🔊 Engineering SFX Layer...")
        
        # Map current timings for the SFX Manager
        # Map current timings for the SFX Manager
        sfx_timings = {
            'q': t_q,
            'a': t_a, 'b': t_b, 'c': t_c, 'd': t_d,
            'think': t_think,
            'ans': t_ans,
            'cta': t_cta,
            'outro': t_outro
        }
        
        # Get professionally mixed SFX clips
        sfx_clips = sfx_mgr.generate_quiz_sfx(sfx_timings)
        
        # Combine: Voice + SFX
        audio_list = [aud_hook.set_start(t_hook), aud_q.set_start(t_q), aud_a.set_start(t_a),
                      aud_b.set_start(t_b), aud_c.set_start(t_c), aud_d.set_start(t_d),
                      aud_think.set_start(t_think), aud_expl.set_start(t_ans), aud_cta.set_start(t_cta)] # CHANGED: aud_ans -> aud_expl, added aud_cta
        
        # Flatten the list (Voice + SFX)
        full_audio_stack = audio_list + sfx_clips
        
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