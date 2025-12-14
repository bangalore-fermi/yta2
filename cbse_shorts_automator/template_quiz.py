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
import math
import concurrent.futures
from moviepy.editor import VideoFileClip, CompositeVideoClip, CompositeAudioClip, ColorClip, AudioFileClip, TextClip, vfx
from voice_manager import VoiceManager
from karaoke_manager import KaraokeManager
from video_processor import VideoProcessor
from sfx_manager import SFXManager  # <--- NEW IMPORT
from usp_content_variations import USPContent
from visual_effects_quiz import QuizVisualEffects
from visual_effects_quiz import res_scale, set_resolution, WIDTH, HEIGHT

YOUTUBE_CONTROLS_ENABLED = True

WIDTH = 1080
HEIGHT = 1920
#WIDTH = 270
#HEIGHT = 480
# ============================================================================
# RELATIVE POSITIONING SYSTEM
# ============================================================================

# Gaps between elements (all scaled)
class LayoutGaps:
    """Relative spacing between UI elements"""
    PIP_TO_HOOK = 20        # Gap from PIP bottom to hook text
    HOOK_TO_QUESTION = 30   # Gap from hook to question
    QUESTION_TO_OPTIONS = 50  # Gap from question to options
    OPTION_HEIGHT = 100     # Height of each option box
    OPTION_SPACING = 30     # Gap between options
    OPTIONS_TO_TIMER = 40   # Gap from last option to timer
    TIMER_LABEL_TO_BAR = 30 # Gap from timer label to bar
    TIMER_BAR_HEIGHT = 50   # Height of timer bar
    OPTIONS_TO_EXPLANATION = 80  # Gap from options to explanation (for answer reveal)
    
    @staticmethod
    def scale_all():
        """Apply res_scale to all gap values"""
        LayoutGaps.PIP_TO_HOOK = res_scale(20)
        LayoutGaps.HOOK_TO_QUESTION = res_scale(30)
        LayoutGaps.QUESTION_TO_OPTIONS = res_scale(50)
        LayoutGaps.OPTION_HEIGHT = res_scale(100)
        LayoutGaps.OPTION_SPACING = res_scale(30)
        LayoutGaps.OPTIONS_TO_TIMER = res_scale(40)
        LayoutGaps.TIMER_LABEL_TO_BAR = res_scale(30)
        LayoutGaps.TIMER_BAR_HEIGHT = res_scale(50)
        LayoutGaps.OPTIONS_TO_EXPLANATION = res_scale(60)

class LayoutPositions:
    """Calculated Y positions for all elements"""
    pip_y = 0
    pip_height = 0
    pip_bottom = 0
    
    hook_y = 0
    question_y = 0
    options_start_y = 0
    timer_label_y = 0
    timer_bar_y = 0
    explanation_y = 0
    cta_y = 0
    
    @staticmethod
    def calculate(pip_y, pip_height):
        """
        Calculate all Y positions based on PIP.
        Call this after PIP dimensions are known.
        """
        LayoutPositions.pip_y = pip_y
        LayoutPositions.pip_height = pip_height
        LayoutPositions.pip_bottom = pip_y + pip_height
        
        # Flow downward from PIP
        LayoutPositions.hook_y = LayoutPositions.pip_bottom + LayoutGaps.PIP_TO_HOOK
        
        # Estimate hook height (fixed 130px box)
        hook_height = res_scale(130)
        LayoutPositions.question_y = LayoutPositions.hook_y + hook_height + LayoutGaps.HOOK_TO_QUESTION
        
        # Estimate question height (background card, typically ~150px)
        question_height = res_scale(150)
        LayoutPositions.options_start_y = LayoutPositions.question_y + question_height + LayoutGaps.QUESTION_TO_OPTIONS
        
        # Calculate position of 4th option bottom
        option_4_bottom = (LayoutPositions.options_start_y + 
                          (LayoutGaps.OPTION_HEIGHT * 4) + 
                          (LayoutGaps.OPTION_SPACING * 3))
        
        # Timer starts below options
        LayoutPositions.timer_label_y = option_4_bottom + LayoutGaps.OPTIONS_TO_TIMER
        LayoutPositions.timer_bar_y = LayoutPositions.timer_label_y + res_scale(80) + LayoutGaps.TIMER_LABEL_TO_BAR
        
        # Explanation replaces options area during answer reveal
        #LayoutPositions.explanation_y = LayoutPositions.options_start_y + LayoutGaps.OPTIONS_TO_EXPLANATION
        LayoutPositions.explanation_y = option_4_bottom + LayoutGaps.OPTIONS_TO_EXPLANATION
        
        # CTA near bottom (fixed distance from bottom edge for safety)
        LayoutPositions.cta_y = HEIGHT - res_scale(420)  # 420px from bottom = safe zone

def validate_layout():
    """
    Validate that all positions fit within screen bounds.
    Raises warning if elements overlap or go off-screen.
    """
    checks = {
        'PIP top': (LayoutPositions.pip_y, 0, 'Too close to top edge'),
        'Hook': (LayoutPositions.hook_y, LayoutPositions.pip_bottom, 'Hook overlaps PIP'),
        'Question': (LayoutPositions.question_y, LayoutPositions.hook_y + res_scale(130), 'Question overlaps hook'),
        'Options': (LayoutPositions.options_start_y, LayoutPositions.question_y + res_scale(150), 'Options overlap question'),
        'Timer': (LayoutPositions.timer_bar_y, LayoutPositions.options_start_y + res_scale(500), 'Timer overlaps options'),
        'CTA': (LayoutPositions.cta_y, HEIGHT - res_scale(500), 'CTA too close to bottom'),
        'Bottom safe': (LayoutPositions.timer_bar_y + res_scale(50), HEIGHT - res_scale(400), 'Timer in YouTube UI zone')
    }
    
    warnings = []
    for name, (pos, min_pos, error_msg) in checks.items():
        if pos < min_pos:
            warnings.append(f"⚠️ {name}: {error_msg} (Y={pos}, min={min_pos})")
        if pos > HEIGHT:
            warnings.append(f"⚠️ {name}: Off-screen! (Y={pos} > HEIGHT={HEIGHT})")
    
    if warnings:
        print("\n⚠️ LAYOUT WARNINGS:")
        for w in warnings:
            print(f"   {w}")
    else:
        print("   ✅ Layout validation passed")
    
    return len(warnings) == 0


class QuizTemplate:
    def __init__(self, engine):
        self.engine = engine
    
    def generate(self, video_path, script, config, output_path):
        print("📝 Generating Quiz Template (Parallel Processing)...")
    
        # ============================================================
        # RESOLUTION SETUP - MUST BE FIRST
        # ============================================================
        target_width = config.get('width', 1080)
        target_height = config.get('height', 1920)
        target_fps = config.get('fps', 24)

        set_resolution(target_width, target_height)
        
        # Update module-level WIDTH/HEIGHT for MoviePy
        global WIDTH, HEIGHT, FPS
        WIDTH = target_width
        HEIGHT = target_height
        FPS = target_fps
        print(f"   📐 Resolution: {target_width}x{target_height}")
        
        import random
        theme = self.engine.get_theme(config.get('theme', 'energetic_yellow'))
        theme_options = ['energetic_yellow', 'calm_blue', 'vibrant_purple', 'fresh_green', 'classic_red']
        default_theme = config.get('theme', random.choice(theme_options))
        theme = self.engine.get_theme(default_theme)
        vfx_quiz = QuizVisualEffects(
            theme=theme,
            config=config,
            timing_data=None,  # Will add after audio generation
            logger=None  # Uses default
        )
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
            voice_mgr.generate_audio_with_specific_voice(text, path, selected_voice_key, provider='edge')
            return key, path

        #with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            #futures = [executor.submit(generate_single_audio, k, t) for k, t in audio_tasks.items()]
            #for future in concurrent.futures.as_completed(futures):
                #k, path = future.result()
                #generated_audio_paths[k] = path
                #audio_files.append(path)
        
        for k, t in audio_tasks.items():
            # 3. Execute the function directly (blocking until it returns)
            try:
                k_result, path = generate_single_audio(k, t)
                
                # 4. Collect the results
                generated_audio_paths[k_result] = path
                audio_files.append(path)
                
            except Exception as e:
                # Handle exceptions from generate_single_audio if necessary
                print(f"Error processing task for key {k}: {e}")
                # Depending on your logic, you might want to break or continue here

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
        
        # OLD (REMOVE THESE):
        # src_vid = src_vid.set_position(('center', 0))
        # bg = self.engine.create_background(config.get('theme'), total_dur, video_clip=src_vid)
        # clips = [bg, src_vid]

        # NEW:
        print(f"   🧠 AI Watching video to find relevant clips ({int(total_dur)}s)...")
        #src_vid = video_proc.prepare_video_for_short(video_path, total_dur, script=script, width=WIDTH)
        src_vid = VideoFileClip(video_path)

        # Configure PIP size
        PIP_HEIGHT = res_scale(333)  # Adjust this value (225 = small, 400 = medium, 495 = large)
        PIP_Y = res_scale(150)  # Top safe zone
        vfx_quiz.pip_size = (int(PIP_HEIGHT * 16 / 9), PIP_HEIGHT)


        LayoutGaps.scale_all()
        # Calculate all positions based on PIP
        LayoutPositions.calculate(PIP_Y, PIP_HEIGHT)
        if not validate_layout():
            print("   ⚠️ Consider adjusting gaps or PIP size")

        print(f"   📐 Layout calculated:")
        print(f"      PIP: Y={PIP_Y}, Height={PIP_HEIGHT}")
        print(f"      Question: Y={LayoutPositions.question_y}")
        print(f"      Options: Y={LayoutPositions.options_start_y}")
        print(f"      Timer: Y={LayoutPositions.timer_bar_y}")

        # Create VFX layers
        backdrop = vfx_quiz.create_particle_backdrop(total_dur)
        pip = vfx_quiz.create_pip_source_video(src_vid, t_outro)

        clips = [backdrop, pip]
        
        def force_rgb(clip):
            try:
                if hasattr(clip, 'img') and clip.img is not None and clip.img.ndim == 2:
                    return clip.fx(vfx.to_RGB)
            except: pass
            return clip

        CARD_START_Y = res_scale(750) 
        
        # 4. Text Overlays
        # Watch Till End
        hook_box = theme['highlight']
        
        hook_txt = self.engine.get_contrast_color(hook_box)
        hook_text = USPContent.get_random_hook()
        hook_clip = TextClip(hook_text, fontsize=res_scale(52), color=hook_txt, bg_color=hook_box, font='Arial-Bold', method='label', size=(WIDTH - res_scale(100), res_scale(130)))

        # Add pulsing animation
        def hook_pulse(t):
            scale = 1.0 + 0.08 * abs(math.sin(t * 3 * math.pi))  # Pulse 3 times in 2 seconds
            offset = (1 - scale) * (WIDTH - res_scale(100)) / 2
            return ('center', CARD_START_Y)

        hook_clip = hook_clip.resize(lambda t: 1.0 + 0.08 * abs(math.sin(t * 3 * math.pi)))
        hook_clip = hook_clip.set_position(('center', LayoutPositions.hook_y)).set_start(0).set_duration(aud_hook.duration)
        clips.append(force_rgb(hook_clip))
        
        # Question
        QUESTION_Y = CARD_START_Y + res_scale(130) 
        question_enhanced = USPContent.enhance_question(script['question_visual'])
        q_clip = vfx_quiz.create_typewriter_text(
            text=question_enhanced,
            audio_duration=aud_q.duration,
            start_time=t_q,
            fontsize=res_scale(55),
            total_remaining_time=t_outro - t_q,
            color=theme['highlight'],
            y_offset=LayoutPositions.question_y
        )
        #q_clip = q_clip.set_position(('center', QUESTION_Y)).set_start(t_q).set_duration(total_dur - t_q)
        clips.append(force_rgb(q_clip))
        
        # Options
        OPT_START_Y = QUESTION_Y + res_scale(350)
        GAP = res_scale(130)
        opt_bg = theme['bg_color']
        
        if isinstance(opt_bg, str):
             if opt_bg.startswith('#'):
                opt_bg = opt_bg.lstrip('#')
                opt_bg = tuple(int(opt_bg[i:i+2], 16) for i in (0, 2, 4))
        
        options = [(f"A) {script['opt_a_visual']}", t_a), (f"B) {script['opt_b_visual']}", t_b), 
                   (f"C) {script['opt_c_visual']}", t_c), (f"D) {script['opt_d_visual']}", t_d)]
                    
        # NEW: Pass relative Y positions
        options_data = [
            {
                'text': f"A) {script['opt_a_visual']}", 
                'start_time': t_a, 
                'duration': t_outro - t_a, 
                'is_correct': False,
                'y_position': LayoutPositions.options_start_y  # Option A
            },
            {
                'text': f"B) {script['opt_b_visual']}", 
                'start_time': t_b, 
                'duration': t_outro - t_b, 
                'is_correct': False,
                'y_position': LayoutPositions.options_start_y + LayoutGaps.OPTION_HEIGHT + LayoutGaps.OPTION_SPACING  # Option B
            },
            {
                'text': f"C) {script['opt_c_visual']}", 
                'start_time': t_c, 
                'duration': t_outro - t_c, 
                'is_correct': False,
                'y_position': LayoutPositions.options_start_y + (LayoutGaps.OPTION_HEIGHT + LayoutGaps.OPTION_SPACING) * 2  # Option C
            },
            {
                'text': f"D) {script['opt_d_visual']}", 
                'start_time': t_d, 
                'duration': t_outro - t_d, 
                'is_correct': False,
                'y_position': LayoutPositions.options_start_y + (LayoutGaps.OPTION_HEIGHT + LayoutGaps.OPTION_SPACING) * 3  # Option D
            }
        ]
        option_clips = vfx_quiz.create_options_sequence(options_data, theme, use_relative_y=True)
        clips.extend(option_clips)

        
        # NEW:
        timer_label_y = LayoutPositions.timer_label_y
        timer_bar_y = LayoutPositions.timer_bar_y
        bar_color = theme['correct']
        if isinstance(bar_color, str) and bar_color.startswith('#'):
             bar_color = tuple(int(bar_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
             
        segments = 12
        timer_clips = vfx_quiz.create_timer_animation(
            start_time=t_think,
            duration=THINK_TIME,
            y_position=timer_bar_y
        )
        clips.extend(timer_clips)

        # Add timer label
        timer_label_text = USPContent.get_random_timer_label()
        timer_label_pulse_freq=4

        # Create flashing effect (2 states alternating)
        for i in range(int(THINK_TIME * timer_label_pulse_freq)):  # Flash twice per second
            opacity = 1.0 if i % 2 == 0 else 0.5  # Alternate full/half
            
            label = TextClip(
                timer_label_text,
                fontsize=res_scale(62),
                color='#FFFF00',  # Bright yellow
                font='Impact',  # Bold, attention-grabbing font
                stroke_color='black',
                stroke_width=res_scale(2),
                method='label'
            ).set_opacity(opacity)
            
            label = label.set_position(('center', timer_label_y))
            label = label.set_start(t_think + (i / timer_label_pulse_freq)).set_duration(1/timer_label_pulse_freq)
            clips.append(label)
        # Answer
        ans_bg = theme['correct']
        ans_txt = self.engine.get_contrast_color(ans_bg)
        
        # FIX: Stroke logic for green backgrounds
        stroke_col = 'black' if ans_txt == 'white' else None
        stroke_wid = 3 if ans_txt == 'white' else 0

        # Create the visual summary text (e.g., "✅ A: H₂O")
        # Fallback to spoken text if visual is missing, but visual is preferred
        #visual_content = script.get('explanation_visual', script.get('explanation_spoken', ''))
        
        visual_content = script.get('explanation_visual', script.get('explanation_spoken', ''))
        answer_enhanced = USPContent.enhance_answer(script['correct_opt'], visual_content)

        summary_clip = self.engine.create_text_clip(
            answer_enhanced,
            fontsize=res_scale(56),  # Bigger
            color=ans_txt,
            bg_color=ans_bg,
            stroke_color='black',  # Always black stroke
            stroke_width=res_scale(2),  # Thicker
            bold=True,
            wrap_width=res_scale(120),  # Wider text
            align='center'
        )

        # Add entrance animation
        def summary_entrance(t):
            if t < 0.4:
                scale = 0.8 + 0.2 * (t / 0.4)  # Scale from 0.8 to 1.0
                return scale
            return 1.0

        summary_clip = summary_clip.resize(summary_entrance)
        #summary_clip = summary_clip.set_position(('center', OPT_START_Y)).set_start(t_ans).set_duration(aud_expl.duration)
        #clips.append(summary_clip)

        # NEW: Pass question Y from LayoutPositions
        reveal_effects = vfx_quiz.create_answer_reveal_animation(
            correct_option_letter=script['correct_opt'],
            options_data=options_data,
            reveal_start_time=t_ans,
            theme=theme,
            total_remaining_time=t_outro - t_ans,
            confetti_y=LayoutPositions.question_y
        )
        clips.extend(reveal_effects)
        
        # Position: Replaces the Options area. 
        # Duration: Matches exactly the length of the spoken explanation audio.
        EXPLANATION_Y = OPT_START_Y + (GAP * 4) + res_scale(80)
        summary_clip = summary_clip.set_position(('center', LayoutPositions.explanation_y)).set_start(t_ans).set_duration(aud_expl.duration)
        clips.append(force_rgb(summary_clip))


        from moviepy.editor import ColorClip

        # Shine sweep effect
        shine = ColorClip(size=(WIDTH + res_scale(200), res_scale(15)), color=(255, 255, 255))
        shine = shine.set_opacity(0.4)

        def shine_move(t):
            progress = min(t / 0.5, 1.0)  # 0.5s sweep
            x = -res_scale(100) + (WIDTH + res_scale(200)) * progress
            return (x, LayoutPositions.explanation_y + res_scale(50))

        shine = shine.set_position(shine_move)
        shine = shine.set_start(t_ans + 0.2).set_duration(0.5)  # Slight delay after text appears
        clips.append(shine)

        # CTA - UPGRADE (Bigger, Moved Up, Highlight Color)
        cta_bg = theme['highlight']
        cta_txt_color = 'black' # High contrast
        
        social_text, link_text = USPContent.get_random_cta()

        cta_banner = vfx_quiz.create_cta_banner(
            social_text=social_text,
            link_text=link_text,
            social_start=t_ans + aud_expl.duration,
            social_duration=aud_cta.duration / 2,
            link_start=t_ans + aud_expl.duration + aud_cta.duration / 2,
            link_duration=aud_cta.duration / 2,
            style='full-banner',
            cta_y=LayoutPositions.cta_y  # NEW parameter
        )

        if cta_banner:
            clips.append(cta_banner)
            
        
        # Optional: Radial wipe transition to outro
        # This creates a circular mask that expands from center
        if True:  # Set to False to disable
            from moviepy.editor import ColorClip
            import numpy as np
            
            # Create a quick flash before outro
            flash = ColorClip(
                size=(WIDTH, HEIGHT),
                color=(255, 255, 255)
            ).set_opacity(0.3).set_start(t_outro - 0.1).set_duration(0.2)
            
            # Insert flash before outro in clips list
            # (You'll need to do this before CompositeVideoClip creation)    
        # Outro
        # Outro - NEW themed version with USP
        outro = self.engine.create_outro_v2(
            duration=OUTRO_DURATION,
            theme=theme,  # Pass theme for colors
            usp_message=None,  # Random USP message
            cta_text="SUBSCRIBE FOR MORE!"
        ).set_start(t_outro)
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
            #self.engine.render_with_effects(final_raw, script, output_path)
            print(f"  Trying:")
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