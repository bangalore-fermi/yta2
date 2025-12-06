#!/usr/bin/env python3
"""
File: test_audio_only.py
Purpose: RAPID TESTING for Prompt Engineering.
Generates full-mix MP3s (Voice + Music + SFX) without rendering video.
Skips video download and scene detection.
"""

import os
import time
import json
import fitz # PyMuPDF
from moviepy.editor import CompositeAudioClip, AudioFileClip, AudioClip

# Import modules
from main_shorts_generator import (
    GeminiManager, 
    download_file, 
    parse_class_level
)
from shorts_engine import ShortsEngine
from voice_manager import VoiceManager
from karaoke_manager import KaraokeManager
from sfx_manager import SFXManager  # <--- NEW IMPORT

# --- CONFIGURATION ---
#TEST_PDF_URL = "https://ncert.nic.in/textbook/pdf/hepr103.pdf" 
TEST_PDF_URL = "https://ncert.nic.in/textbook/pdf/kemh104.pdf"
# Note: We do NOT need the video URL for audio-only testing
OUTPUT_DIR = "shorts/audio_tests"
TEMP_DIR = "temp"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def build_audio_timeline(script, template_type, voice_mgr, karaoke_mgr, engine, vid_id, selected_voice_key, sfx_mgr):
    """
    Reconstructs the audio timeline logic from the templates,
    but skips all visual processing.
    """
    print(f"   🎙️  Synthesizing Audio for {template_type.upper()}...")
    
    audio_clips = []
    current_time = 0.0
    
    # Helper to generate TTS and place it on timeline
    def add_voice(text, suffix, start_time):
        path = f"{TEMP_DIR}/{vid_id}_{suffix}.mp3"
        clip = voice_mgr.generate_audio_with_specific_voice(text, path, selected_voice_key)
        audio_clips.append(clip.set_start(start_time))
        return clip.duration

    # --- LOGIC BY TEMPLATE ---
    
    if template_type == 'quiz':
        # Track timestamps for SFX Manager
        timestamps = {}

        # 1. Hook
        dur = add_voice(script['hook_spoken'], 'hook', current_time)
        current_time += dur
        
        # 2. Question
        timestamps['q'] = current_time # Capture Start
        dur = add_voice(script['question_spoken'], 'q', current_time)
        current_time += dur
        
        # 3. Options
        timestamps['a'] = current_time
        dur = add_voice(f"A: {script['opt_a_spoken']}", 'opt_a', current_time)
        current_time += dur

        timestamps['b'] = current_time
        dur = add_voice(f"B: {script['opt_b_spoken']}", 'opt_b', current_time)
        current_time += dur

        timestamps['c'] = current_time
        dur = add_voice(f"C: {script['opt_c_spoken']}", 'opt_c', current_time)
        current_time += dur

        timestamps['d'] = current_time
        dur = add_voice(f"D: {script['opt_d_spoken']}", 'opt_d', current_time)
        current_time += dur
        
        # 4. Timer / Think Fast
        timestamps['think'] = current_time
        dur = add_voice("Think fast!", 'think', current_time)
        current_time += dur
        
        # Note: We skip manual tick loading here, SFX Manager handles it based on timestamps['think']
        
        current_time += 3.0 # Wait for timer
        
        # 5. Answer
        timestamps['ans'] = current_time
        full_ans = f"The answer is {script['correct_opt']}! {script['explanation_spoken']} {script['cta_spoken']}"
        ans_path = f"{TEMP_DIR}/{vid_id}_ans.mp3"
        ans_clip = voice_mgr.generate_audio_with_specific_voice(full_ans, ans_path, selected_voice_key, provider='google')
        audio_clips.append(ans_clip.set_start(current_time))
        
        # === NEW: INJECT SFX ===
        # Using the manager to generate ticks, pops, whooshes, and dings
        print("   🔊 Injecting Professional SFX Layer...")
        sfx_layer = sfx_mgr.generate_quiz_sfx(timestamps)
        audio_clips.extend(sfx_layer)
            
        current_time += ans_clip.duration

    elif template_type == 'fact':
        # 1. Hook
        dur = add_voice(script['hook_spoken'], 'hook', current_time)
        current_time += dur
        
        # 2. Title
        dur = add_voice(script['fact_title'], 'title', current_time)
        current_time += dur
        
        # 3. Details (Main Content)
        # Use karaoke manager for long text as it might be better paced
        det_path = f"{TEMP_DIR}/{vid_id}_details.mp3"
        det_clip = voice_mgr.generate_audio_with_specific_voice(script['fact_spoken'], det_path, selected_voice_key)
        audio_clips.append(det_clip.set_start(current_time))
        current_time += det_clip.duration
        
        # 4. CTA
        dur = add_voice(script['cta_spoken'], 'cta', current_time)
        current_time += dur

    elif template_type == 'tip':
        # 1. Hook
        dur = add_voice(script['hook_spoken'], 'hook', current_time)
        current_time += dur
        
        # 2. Title
        dur = add_voice(script['tip_title'], 'title', current_time)
        current_time += dur
        
        # 3. Content
        #cont_clip, _ = karaoke_mgr.generate_timed_audio(script['tip_content'], f"{vid_id}_content", voice_key=selected_voice_key)
        cont_path = f"{TEMP_DIR}/{vid_id}_content.mp3"
        cont_clip = voice_mgr.generate_audio_with_specific_voice(script['tip_spoken'], cont_path, selected_voice_key)
        audio_clips.append(cont_clip.set_start(current_time))
        current_time += cont_clip.duration
        
        # 4. Bonus
        dur = add_voice(script['bonus'], 'bonus', current_time)
        current_time += dur
        
        # 5. CTA
        dur = add_voice(script['cta_spoken'], 'cta', current_time)
        current_time += dur

    # Add 2 seconds for Outro (Silence/Music only)
    current_time += 2.0
    
    return audio_clips, current_time

def run_audio_test():
    print("🎧 STARTING AUDIO-ONLY TEST (Prompt Engineering Tool)")
    print("=" * 60)
    
    # 1. SETUP (PDF ONLY)
    pdf_path = os.path.join(TEMP_DIR, "test_source.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"   ⬇️  Downloading PDF...")
        if not download_file(TEST_PDF_URL, pdf_path):
            print("   ❌ PDF Download Failed.")
            return
    
    doc = fitz.open(pdf_path)
    full_text = "".join([page.get_text() for page in doc])
    print(f"   📄 PDF Loaded: {len(full_text)} chars")
    
    # Init Engines
    gemini = GeminiManager()
    engine = ShortsEngine() # Used for config & music
    sfx_mgr = SFXManager()  # <--- NEW INIT
    
    # 2. LOOP
    #templates = ['quiz', 'fact', 'tip']
    templates = ['quiz']
    
    for template_type in templates:
        print(f"\n🧪 TESTING '{template_type.upper()}' SCRIPT")
        print("-" * 50)
        
        try:
            # A. Generate Script
            start_time = time.time()
            print("   🤖 Generating Script via Gemini...")
            script = gemini.get_script(full_text, class_level=11, template=template_type)
            
            # Print Script for visual verification
            print(f"\n   📜 SCRIPT OUTPUT:")
            print(json.dumps(script, indent=2))
            print("-" * 20)

            # B. Setup Voice
            # You can hardcode a specific voice here to test consistency
            selected_voice_key = VoiceManager.get_random_voice_name()
            print(f"   🗣️  Voice: {selected_voice_key}")

            voice_mgr = VoiceManager()  # Shared instance
            karaoke_mgr = KaraokeManager(voice_mgr, TEMP_DIR)
            
            # C. Build Audio Timeline
            vid_id = f"test_{template_type}"
            # Pass sfx_mgr to the builder
            audio_clips, total_duration = build_audio_timeline(
                script, template_type, voice_mgr, karaoke_mgr, engine, vid_id, selected_voice_key, sfx_mgr
            )
            
            # D. Mix with Music
            print(f"   🎵 Mixing with Background Music (Duration: {total_duration:.1f}s)...")
            voice_track = CompositeAudioClip(audio_clips)
            final_audio = engine.add_background_music(voice_track, total_duration, theme_name='energetic_yellow')
            
            # E. Export MP3
            output_file = os.path.join(OUTPUT_DIR, f"AUDIO_TEST_{template_type.upper()}.mp3")
            final_audio.write_audiofile(output_file, fps=44100, logger=None) # logger=None for less noise
            
            elapsed = time.time() - start_time
            print(f"   ✅ DONE in {elapsed:.1f}s -> {output_file}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_audio_test()