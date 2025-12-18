#!/usr/bin/env python3
"""
File: template_quiz_json_generator.py
Purpose: Calculates timings and asset data, generates the final audio file, 
         and SAVES the resulting VisualScenario dictionary as scenario_data.json 
         directly in the 'public' folder.
"""

import imagemagick_setup
import os
import math
import concurrent.futures
import json 
import glob
import random 
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from voice_manager import VoiceManager 
from sfx_manager import SFXManager
from video_processor import VideoProcessor
from usp_content_variations import USPContent 
from visual_effects_quiz import res_scale, set_resolution

# --- CONSTANTS ---
WIDTH = 1080
HEIGHT = 1920
FPS = 24 
AUDIO_SAMPLE_RATE = 44100 

# --- (LayoutGaps and LayoutPositions classes omitted for brevity) ---

class QuizTemplate:
    def __init__(self, engine):
        self.engine = engine
    
    def generate(self, video_path, script, config, output_path):
        print("📝 Generating VisualScenario JSON structure...")
    
        # ============================================================
        # RESOLUTION & VOICE SETUP 
        # ============================================================
        target_width = config.get('width', 1080)
        target_height = config.get('height', 1920)

        set_resolution(target_width, target_height)
        
        global WIDTH, HEIGHT
        WIDTH = target_width
        HEIGHT = target_height
        
        voice_mgr = self.engine.voice_manager
        sfx_mgr = SFXManager()
        
        voice_name = config.get('voice', 'NeeraNeural2')
        selected_voice_key = voice_name if voice_name else voice_mgr.get_random_voice_name()
        video_proc = VideoProcessor(temp_dir=self.engine.config['DIRS']['TEMP'])
        
        vid_id = os.path.basename(output_path).split('.')[0]
        temp_dir = self.engine.config['DIRS']['TEMP']
        audio_files = [] 
        
        # Define the base directory for public assets and the corrected JSON path
        BASE_PUBLIC_DIR = "visual_engine_v3/public"
        FINAL_ASSETS_DIR = f"{BASE_PUBLIC_DIR}/assets"
        
        # CORRECTED JSON OUTPUT PATH: directly in public folder
        JSON_OUTPUT_PATH = f"{BASE_PUBLIC_DIR}/scenario_data.json" 
        
        # Define asset file paths (relative to BASE_PUBLIC_DIR/assets)
        FINAL_AUDIO_FILENAME = f"{vid_id}_final_audio.mp3"
        FINAL_AUDIO_PATH = f"{FINAL_ASSETS_DIR}/{FINAL_AUDIO_FILENAME}"

        SOURCE_VIDEO_PATH = f"{FINAL_ASSETS_DIR}/source_video.mp4"
        
        # Asset URLs (All relative to the public root)
        FINAL_AUDIO_URL = f"/assets/{FINAL_AUDIO_FILENAME}"
        SOURCE_VIDEO_URL = "/assets/source_video.mp4" 
        CHANNEL_LOGO_URL = "/assets/logo.png"
        THUMBNAIL_URL = "/assets/thumbnail.jpg"
        FONT_URL = "/assets/font.woff"
        ENV_MAP_URL = "/assets/environment.hdr"
        CLOUD_MAP_URL = "/assets/cloud.png"
        
        # 1. Sequential Audio Generation (Individual Voice Tracks)
        print("   🎙️  Synthesizing voiceover tracks...")
        audio_tasks = {
            'hook': script['hook_spoken'], 'question': script['question_spoken'],
            'opt_a': f"A: {script['opt_a_spoken']}", 'opt_b': f"B: {script['opt_b_spoken']}",
            'opt_c': f"C: {script['opt_c_spoken']}", 'opt_d': f"D: {script['opt_d_spoken']}",
            'think': "Think fast!",
            'explanation': f"The answer is {script['correct_opt']}! {script['explanation_spoken']}",
            'cta': script['cta_spoken']
        }
        
        generated_audio_paths = {}
        aud_clips = {}
        
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

        # for k, t in audio_tasks.items():
        #     try:
        #         k_result, path = generate_single_audio(k, t)
        #         generated_audio_paths[k_result] = path
        #         audio_files.append(path)
        #         aud_clips[k_result] = AudioFileClip(path) 
        #     except Exception as e:
        #         print(f"Error processing task for key {k}: {e}. Halting operation.")
        #         if self.engine.config.get('DELETE_TEMP_FILES', True):
        #             for f in audio_files:
        #                 if os.path.exists(f): os.remove(f)
        #         raise 
        aud_hook = AudioFileClip(generated_audio_paths['hook'])
        aud_q = AudioFileClip(generated_audio_paths['question'])
        aud_a = AudioFileClip(generated_audio_paths['opt_a'])
        aud_b = AudioFileClip(generated_audio_paths['opt_b'])
        aud_c = AudioFileClip(generated_audio_paths['opt_c'])
        aud_d = AudioFileClip(generated_audio_paths['opt_d'])
        aud_think = AudioFileClip(generated_audio_paths['think'])
        aud_expl = AudioFileClip(generated_audio_paths['explanation'])
        aud_cta = AudioFileClip(generated_audio_paths['cta'])
   
        # 2. Timing Calculations
        # aud_hook, aud_q, aud_a, aud_b, aud_c, aud_d, aud_expl, aud_cta = (
        #     aud_clips['hook'], aud_clips['question'], aud_clips['opt_a'], aud_clips['opt_b'], 
        #     aud_clips['opt_c'], aud_clips['opt_d'], aud_clips['explanation'], aud_clips['cta']
        # )
        
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
        t_outro = t_cta + max(aud_cta.duration,6)
        
        OUTRO_DURATION = 7.0
        total_dur = t_outro + OUTRO_DURATION

        print(f"   🧠 AI Watching video to find relevant clips ({int(total_dur)}s)...")
        src_vid = video_proc.prepare_video_for_short(video_path, total_dur, script=script, width=WIDTH)
        src_vid.write_videofile(
            SOURCE_VIDEO_PATH,
            codec='libx264',  # Standard codec for MP4 files # Standard audio codec
            fps=30             # Set the desired frames per second (e.g., 24, 30, or original fps)
        )

        # 3. Final Audio Generation
        print("   🔊 Compiling final audio track...")
        sfx_timings = {
            'q': t_q, 'a': t_a, 'b': t_b, 'c': t_c, 'd': t_d,
            'think': t_think, 'ans': t_ans, 'cta': t_cta, 'outro': t_outro
        }
        sfx_clips = sfx_mgr.generate_quiz_sfx(sfx_timings)
        
        audio_list = [
            aud_hook.set_start(t_hook), aud_q.set_start(t_q), aud_a.set_start(t_a),
            aud_b.set_start(t_b), aud_c.set_start(t_c), aud_d.set_start(t_d),
            aud_think.set_start(t_think), aud_expl.set_start(t_ans), aud_cta.set_start(t_cta)
        ]
        full_audio_stack = audio_list + sfx_clips
        composite_audio = CompositeAudioClip(full_audio_stack)
        final_audio = self.engine.add_background_music(composite_audio, total_dur)
        
        # FIX: Explicitly set the sampling frequency (fps)
        final_audio.fps = AUDIO_SAMPLE_RATE 
        
        # Write the final audio
        os.makedirs(os.path.dirname(FINAL_AUDIO_PATH), exist_ok=True)
        final_audio.write_audiofile(FINAL_AUDIO_PATH, logger=None)
        print(f"   ✅ Final audio saved to {FINAL_AUDIO_PATH}")
        
        # 4. Dynamic Content Lookups
        hook_text = USPContent.get_random_hook()
        timer_label_text = USPContent.get_random_timer_label()
        social_text, link_text = USPContent.get_random_cta()
        outro_line_1, outro_line_2 = USPContent.get_random_outro() 
        
        # Options Setup
        option_start_times = {'A': t_a, 'B': t_b, 'C': t_c, 'D': t_d}
        options_array = []
        option_keys = ['A', 'B', 'C', 'D']
        for key in option_keys:
            options_array.append({
                'id': key,
                'text': script[f'opt_{key.lower()}_visual'],
                'start_time': option_start_times[key]
            })

        progress_end = t_ans + 1.0

        # 5. Build VisualScenario Dictionary
        scenario_data = {
            "meta": {
                "version": config.get('version', '1.0.0'), 
                "resolution": {"w": WIDTH, "h": HEIGHT},
                "seed": config.get('seed', random.randint(1000, 9999)),
                "duration_seconds": round(total_dur, 2),
            },
            "assets": {
                "audio_url": FINAL_AUDIO_URL,
                "video_source_url": SOURCE_VIDEO_URL,
                "thumbnail_url": THUMBNAIL_URL,
                "channel_logo_url": CHANNEL_LOGO_URL,
                "font_url": FONT_URL,
                "env_map_url": ENV_MAP_URL,     
                "cloud_map_url": CLOUD_MAP_URL,   
            },
            "timeline": {
                "hook": {"start_time": t_hook, "text_content": hook_text},
                "quiz": {
                    "question": {"text": script['question_visual'], "start_time": t_q},
                    "options": options_array,
                },
                "timer": {"start_time": t_think, "duration": THINK_TIME, "label_text": timer_label_text},
                "answer": {
                    "start_time": t_ans,
                    "correct_option_id": script['correct_opt'],
                    "explanation_text": script['explanation_visual'],
                    "celebration_text": script.get('celebration_text', 'Great job!') 
                },
                "cta": {"start_time": t_cta, "social_text": social_text, "link_text": link_text},
                "outro": {
                    "start_time": t_outro, 
                    "line_1": outro_line_1, 
                    "line_2": outro_line_2
                },
            },
            "yt_overlay": {"progress_start": t_q, "progress_end": progress_end},
        }

        # 6. WRITE JSON FILE TO TARGET PATH
        # Ensure the 'public' directory exists
        os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)
        with open(JSON_OUTPUT_PATH, 'w') as f:
            json.dump(scenario_data, f, indent=4)
        
        print(f"   ✅ JSON Scenario successfully written to: {JSON_OUTPUT_PATH}")

        # 7. Cleanup (Clean intermediate voice tracks)
        if self.engine.config.get('DELETE_TEMP_FILES', True):
            for f in audio_files:
                if os.path.exists(f): os.remove(f)

        return {'duration': total_dur}