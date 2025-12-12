import json
import random
import os
import urllib.request

# Try to import USPContent from the existing project file
try:
    from usp_content_variations import USPContent
    print("✅ Loaded USPContent variations.")
except ImportError:
    print("⚠️  usp_content_variations.py not found. Using fallback strings.")
    class USPContent:
        HOOKS = ["⚡ 7-MINUTE CHAPTER MASTERY ⚡"]
        TIMER_LABELS = ["⚡ THINK FAST"]
        ANSWER_PREFIXES = ["🎯 PERFECT!"]
        CTA_SOCIAL = ["🔔 SUBSCRIBE FOR MORE"]
        CTA_LINKS = ["Full Chapter Below"]
        OUTRO_MESSAGES = [("🚀 7-MINUTE CHAPTERS", "📚 Zero Boredom")]
        @staticmethod
        def get_random_hook(): return random.choice(USPContent.HOOKS)
        @staticmethod
        def get_random_timer_label(): return random.choice(USPContent.TIMER_LABELS)
        @staticmethod
        def get_random_answer_prefix(): return random.choice(USPContent.ANSWER_PREFIXES)
        @staticmethod
        def get_random_cta(): return (random.choice(USPContent.CTA_SOCIAL), random.choice(USPContent.CTA_LINKS))
        @staticmethod
        def get_random_outro(): return random.choice(USPContent.OUTRO_MESSAGES)

def generate_mock_scenario():
    # 1. Generate Random Seed & ID
    vid_id = f"mock_{random.randint(1000, 9999)}"
    seed = random.randint(0, 999999)
    
    # 2. Get USP Content
    hook_text = USPContent.get_random_hook()
    cta_social, cta_link = USPContent.get_random_cta()
    outro_1, outro_2 = USPContent.get_random_outro()
    
    # 3. Setup Paths (Writes directly to Frontend Public Folder)
    frontend_public_dir = os.path.join("visual_engine_v3", "public")
    os.makedirs(frontend_public_dir, exist_ok=True)

    # 4. Download Audio Asset (Ensures Offline Stability)
    audio_filename = "mock_audio.mp3"
    local_audio_path = os.path.join(frontend_public_dir, audio_filename)
    
    # Public domain test track (SoundHelix)
    remote_audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    if not os.path.exists(local_audio_path):
        print(f"⬇️  Downloading mock audio to {local_audio_path}...")
        try:
            # Attempt download
            urllib.request.urlretrieve(remote_audio_url, local_audio_path)
        except Exception as e:
            print(f"⚠️ Audio download failed: {e}. Creating dummy empty file (Silence).")
            # Create a silent dummy file to prevent Remotion crash
            with open(local_audio_path, 'wb') as f: f.write(b'')

    # 5. Construct the JSON Payload
    scenario = {
        "meta": {
            "version": "3.1",
            "resolution": { "w": 1080, "h": 1920 },
            "seed": seed,
            "duration_seconds": 35.0 
        },
        "assets": {
            "audio_url": f"/{audio_filename}", # Points to the local file in public/
            "video_source_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "thumbnail_url": "https://via.placeholder.com/1080x1920",
            "channel_logo_url": "https://via.placeholder.com/150",
            "font_url": "https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLGT9Z1xlFQ.woff2"
        },
        "timeline": {
            "hook": { "start_time": 0.0, "text_content": hook_text },
            "quiz": {
                "question": { "text": "Orbital Shape Quantum No.?", "start_time": 3.5 },
                "options": [
                    { "id": "A", "text": "Principal (n)", "start_time": 6.0 },
                    { "id": "B", "text": "Azimuthal (l)", "start_time": 7.5 },
                    { "id": "C", "text": "Magnetic (m)", "start_time": 9.0 },
                    { "id": "D", "text": "Spin (s)", "start_time": 10.5 }
                ]
            },
            "timer": { "start_time": 15.0, "duration": 5.0, "label_text": USPContent.get_random_timer_label() },
            "answer": { "start_time": 20.5, "correct_option_id": "B", "explanation_text": "Determines Shape", "celebration_text": USPContent.get_random_answer_prefix() },
            "cta": { "start_time": 25.0, "social_text": cta_social, "link_text": cta_link },
            "outro": { "start_time": 29.0, "line_1": outro_1, "line_2": outro_2 }
        },
        "yt_overlay": { "progress_start": 0.15, "progress_end": 0.25 }
    }
    
    # 6. Write JSON Artifact
    output_path = os.path.join(frontend_public_dir, "scenario_mock.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=4)
    
    print(f"✨ Mock Payload Ready: {output_path}")
    print(f"   Audio Asset: {local_audio_path}")

if __name__ == "__main__":
    generate_mock_scenario()