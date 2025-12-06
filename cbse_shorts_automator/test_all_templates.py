#!/usr/bin/env python3
"""
File: test_all_templates.py
Purpose: End-to-End Test. Generates 3 Shorts (Quiz, Fact, Tip) 
from a SINGLE source PDF and Video to verify the entire pipeline.
"""

import os
import time
import json
import fitz # PyMuPDF

# Import modules from your main codebase
from main_shorts_generator import (
    GeminiManager, 
    download_file, 
    download_drive_video, 
    parse_class_level
)
from shorts_engine import ShortsEngine
from voice_manager import VoiceManager

# --- CONFIGURATION ---
	
#TEST_PDF_URL = "https://ncert.nic.in/textbook/pdf/hepr103.pdf" 

TEST_PDF_URL = "https://ncert.nic.in/textbook/pdf/lech102.pdf"
TEST_VIDEO_URL = "https://drive.google.com/file/d/1K78uJRddxY0ewzCHVloQWdOdfYxJT30-/view?usp=drive_link"
OUTPUT_DIR = "shorts"
TEMP_DIR = "temp"

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def run_full_test():
    print("🚀 STARTING FULL SYSTEM TEST (All 3 Templates)")
    print("=" * 60)
    
    # 1. SETUP RESOURCES
    pdf_path = os.path.join(TEMP_DIR, "test_source.pdf")
    video_path = os.path.join(TEMP_DIR, "test_source.mp4")
    
    print("\n📦 Step 1: Acquiring Assets...")
    
    # Download PDF
    if not os.path.exists(pdf_path):
        print(f"   ⬇️  Downloading PDF: {TEST_PDF_URL}...")
        if not download_file(TEST_PDF_URL, pdf_path):
            print("   ❌ PDF Download Failed. Aborting.")
            return
    else:
        print("   ✅ PDF already exists (skipping download)")

    # Download Video
    if not os.path.exists(video_path):
        print(f"   ⬇️  Downloading Video: {TEST_VIDEO_URL}...")
        if not download_drive_video(TEST_VIDEO_URL, video_path):
            print("   ❌ Video Download Failed. Aborting.")
            return
    else:
        print("   ✅ Video already exists (skipping download)")

    # Read PDF Text
    doc = fitz.open(pdf_path)
    full_text = "".join([page.get_text() for page in doc])
    print(f"   📄 PDF Text Loaded: {len(full_text)} chars")
    
    # Initialize Engines
    print("\n⚙️  Step 2: Initializing Engines...")
    gemini = GeminiManager()
    engine = ShortsEngine()
    
    # 2. TEST LOOP (Quiz -> Fact -> Tip)
    #templates = ['quiz', 'fact', 'tip']
    templates = ['quiz']
    
    for i, template_type in enumerate(templates):
        print(f"\n🎬 TEST {i+1}/3: Generating '{template_type.upper()}' Template")
        print("-" * 50)
        
        try:
            # A. Generate Script
            print(f"   🤖 Asking Gemini for a {template_type} script...")
            script = gemini.get_script(
                full_text, 
                class_level=11, # Assuming Class 11 based on PDF content
                template=template_type
            )
            #print(f"   📝 Script Received:{script.fulltext}")
            
            # Validation Preview
            if template_type == 'quiz':
                preview = f"Q: {script.get('question_text', '')[:40]}..."
            elif template_type == 'fact':
                preview = f"Fact: {script.get('fact_title', '')[:40]}..."
            else:
                preview = f"Tip: {script.get('tip_title', '')[:40]}..."
                
            print(f"   ✅ Script Generated: {preview}")

            # B. Configure Engine
            # We force the config to match the current loop
            test_config = {
                'template': template_type,
                'voice': VoiceManager.get_random_voice_name(),
                'theme': 'energetic_yellow' if template_type == 'quiz' else 
                         ('vibrant_purple' if template_type == 'fact' else 'fresh_green'),
                'cta_style': 'bookend',
                'class_level': 11
            }
            
            output_filename = f"TEST_FULL_{template_type.upper()}_V1.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            print(f"   🗣️  Voice: {test_config['voice']}")
            print(f"   🎨 Theme: {test_config['theme']}")

            # C. Generate Video
            result = engine.generate_short(
                video_path=video_path,
                pdf_path=pdf_path,
                script=script,
                config=test_config,
                output_path=output_path,
                class_level=11
            )
            
            if result['success']:
                print(f"   ✨ SUCCESS: Created {output_path}")
            else:
                print(f"   ❌ FAILED: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ CRITICAL ERROR during {template_type} test: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Full Test Complete! Check the 'shorts/' folder.")

if __name__ == "__main__":
    run_full_test()