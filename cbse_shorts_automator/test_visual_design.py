#!/usr/bin/env python3
"""
File: test_visual_design.py
Purpose: Isolated Unit Test for the NEW Premium Visual Engine.
Uses hardcoded script data to verify:
1. Glassmorphic Panel Rendering
2. Easing Animations
3. New Color Palettes (Midnight Gold)
"""

import os
import json
from shorts_engine import ShortsEngine
from voice_manager import VoiceManager

# --- CONFIGURATION ---
TEST_VIDEO_URL = "https://drive.google.com/file/d/1K78uJRddxY0ewzCHVloQWdOdfYxJT30-/view?usp=drive_link"
OUTPUT_DIR = "shorts"
TEMP_DIR = "temp"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def download_drive_video_simple(url, destination):
    """Simple helper to ensure we have the background video."""
    if os.path.exists(destination): return True
    # In a real scenario, import your main download_drive_video
    # For this test, we assume the file might already be there from previous tests
    # or you can copy the function from main_shorts_generator.py
    from main_shorts_generator import download_drive_video
    return download_drive_video(url, destination)

def run_visual_test():
    print("🎨 STARTING VISUAL DESIGN TEST (Quiz Template Only)")
    print("=" * 60)
    
    # 1. SETUP RESOURCES
    video_path = os.path.join(TEMP_DIR, "test_source.mp4")
    
    print("\n📦 Step 1: Checking Assets...")
    # We only need the video for the background texture
    if not os.path.exists(video_path):
        print(f"   ⬇️  Downloading Video: {TEST_VIDEO_URL}...")
        try:
            download_drive_video_simple(TEST_VIDEO_URL, video_path)
        except ImportError:
            print("   ⚠️  Could not import downloader. Please ensure 'test_source.mp4' is in 'temp/' folder manually.")
            if not os.path.exists(video_path): return
    else:
        print("   ✅ Video background found.")

    # Initialize Engine
    print("\n⚙️  Step 2: Initializing Shorts Engine...")
    engine = ShortsEngine()
    
    # 2. DEFINE MOCK DATA (The "Perfect" Script)
    # This data structure matches the new template_quiz.py requirements EXACTLY.
    mock_script = {
        # 1. Hook
        "hook_spoken": "Can you answer this class 11 chemistry question?",
        
        # 2. Question
        "question_spoken": "Which quantum number determines the shape of an orbital?",
        "question_visual": "Orbital Shape Quantum No.?", 
        
        # 3. Options
        "opt_a_spoken": "Principal quantum number",
        "opt_a_visual": "Principal (n)",
        
        "opt_b_spoken": "Azimuthal quantum number",
        "opt_b_visual": "Azimuthal (l)",
        
        "opt_c_spoken": "Magnetic quantum number",
        "opt_c_visual": "Magnetic (m)",
        
        "opt_d_spoken": "Spin quantum number",
        "opt_d_visual": "Spin (s)",
        
        # 4. Answer Logic
        "correct_opt": "B",
        "explanation_spoken": "The Azimuthal quantum number, l, determines the orbital angular momentum and the shape of the orbital.",
        "explanation_visual": "Determines Shape", 
        
        # 5. CTA
        "cta_spoken": "Subscribe for more exam prep!"
    }

    # 3. RUN TEST
    print(f"\n🎬 TEST: Generating Premium Quiz Layout")
    print("-" * 50)
    
    try:
        # Configuration intended to trigger the new visuals
        test_config = {
            'template': 'quiz',
            'voice': None, # Female voice
            'theme': 'midnight_gold',   # <--- TESTING NEW PALETTE
            'cta_style': 'bookend',
            'class_level': 11,
            'test_render_limit': 25  # <--- WILL RENDER ONLY 10 SECONDS
        }
        
        output_filename = "TEST_VISUAL_QUIZ_FINAL.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"   🗣️  Voice: {test_config['voice']}")
        print(f"   🎨 Theme: {test_config['theme']} (New Premium System)")
        print(f"   📝 Script: Mock Chemistry Question")

        # Generate
        result = engine.generate_short(
            video_path=video_path,
            pdf_path="dummy.pdf", # Not used in mock mode
            script=mock_script,   # PASSING MOCK DATA
            config=test_config,
            output_path=output_path,
            class_level=11
        )
        
        if result['success']:
            print(f"   ✨ SUCCESS: Created {output_path}")
            print("   👉 Please watch this video to verify: ")
            print("      1. Glass panels slide in smoothly.")
            print("      2. Text is inside the panels.")
            print("      3. Correct answer pops with a highlight.")
        else:
            print(f"   ❌ FAILED: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_visual_test()