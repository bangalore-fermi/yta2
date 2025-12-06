#!/usr/bin/env python3
"""
File: setup_sfx.py
Purpose: Generates unique sonic identities for Quiz, Fact, and Tip templates.
Includes procedural synthesis + stable downloads.
"""
import numpy as np
from scipy.io import wavfile
import os
import requests

SFX_DIR = 'config/sfx'

def ensure_dir():
    if not os.path.exists(SFX_DIR):
        os.makedirs(SFX_DIR)

def download_file(filename, url):
    """Helper to download real audio files."""
    path = os.path.join(SFX_DIR, filename)
    if os.path.exists(path): return

    print(f"⬇️  Downloading {filename}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, allow_redirects=True)
        r.raise_for_status()
        with open(path, 'wb') as f:
            f.write(r.content)
        print(f"✨ Saved {filename}")
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")

def generate_assets():
    ensure_dir()
    rate = 44100

    # ==========================================
    # 1. QUIZ ASSETS (The "Gamified" Palette)
    # ==========================================
    
    # Tick (Woodblock)
    filename = os.path.join(SFX_DIR, 'tick.wav')
    if not os.path.exists(filename):
        print(f"🔨 Generating {filename}...")
        duration = 0.1
        t = np.linspace(0, duration, int(rate * duration), False)
        audio = np.sin(800 * 2 * np.pi * t) * np.exp(-t * 60)
        data = (audio / np.max(np.abs(audio)) * 32767).astype(np.int16)
        wavfile.write(filename, rate, data)

    # Chime (Success)
    filename = os.path.join(SFX_DIR, 'correct.wav')
    if not os.path.exists(filename):
        print(f"🔔 Generating {filename}...")
        duration = 1.5
        t = np.linspace(0, duration, int(rate * duration), False)
        audio = (0.6 * np.sin(660 * 2 * np.pi * t) + 0.4 * np.sin(1320 * 2 * np.pi * t)) * np.exp(-t * 3)
        data = (audio / np.max(np.abs(audio)) * 32767).astype(np.int16)
        wavfile.write(filename, rate, data)

    # Whoosh (Airy)
    filename = os.path.join(SFX_DIR, 'whoosh.wav')
    # Overwrite to ensure volume balance
    duration = 0.6
    t = np.linspace(0, duration, int(rate * duration), False)
    noise = np.random.uniform(-0.5, 0.5, len(t))
    envelope = np.exp(-((t - 0.3)**2) / (2 * 0.08**2))
    audio = noise * envelope
    data = (audio / np.max(np.abs(audio)) * 12000).astype(np.int16)
    wavfile.write(filename, rate, data)

    # ==========================================
    # 2. FACT ASSETS (The "Digital" Palette)
    # ==========================================

    # Glitch (Static Burst for Transitions)
    filename = os.path.join(SFX_DIR, 'glitch.wav')
    if not os.path.exists(filename):
        print(f"👾 Generating {filename}...")
        duration = 0.25
        t = np.linspace(0, duration, int(rate * duration), False)
        # White noise
        noise = np.random.uniform(-0.8, 0.8, len(t))
        # Chop it up (Stutter effect)
        chopper = np.sign(np.sin(2 * np.pi * 30 * t)) # 30Hz stutter
        envelope = np.exp(-t * 10) # Fast decay
        audio = noise * chopper * envelope
        data = (audio / np.max(np.abs(audio)) * 20000).astype(np.int16)
        wavfile.write(filename, rate, data)

    # Notification (Clean Ping for CTA)
    filename = os.path.join(SFX_DIR, 'notification.wav')
    if not os.path.exists(filename):
        print(f"📲 Generating {filename}...")
        duration = 0.4
        t = np.linspace(0, duration, int(rate * duration), False)
        # Sine wave sweep (Chirp)
        f_start, f_end = 800, 1200
        freq = np.linspace(f_start, f_end, len(t))
        audio = np.sin(2 * np.pi * freq * t) * np.exp(-t * 15)
        data = (audio / np.max(np.abs(audio)) * 25000).astype(np.int16)
        wavfile.write(filename, rate, data)

    # Camera Shutter (For Reveal) - Download
    download_file('shutter.mp3', 'https://github.com/joshua-morony/ionic-sounds/raw/master/src/assets/sounds/camera.mp3')

    # ==========================================
    # 3. TIP ASSETS (The "Productivity" Palette)
    # ==========================================

    # Zip (Fast Slide for Transitions)
    filename = os.path.join(SFX_DIR, 'zip.wav')
    if not os.path.exists(filename):
        print(f"🤐 Generating {filename}...")
        duration = 0.3
        t = np.linspace(0, duration, int(rate * duration), False)
        noise = np.random.uniform(-0.5, 0.5, len(t))
        # Rising bandpass filter simulation (Envelope getting sharper)
        envelope = np.exp(-((t - 0.15)**2) / (2 * 0.05**2))
        audio = noise * envelope
        data = (audio / np.max(np.abs(audio)) * 18000).astype(np.int16)
        wavfile.write(filename, rate, data)

    # Keyboard Clack (For CTA) - Download
    download_file('keyboard.mp3', 'https://github.com/joshua-morony/ionic-sounds/raw/master/src/assets/sounds/tap.mp3')

    # Highlighter / Marker (Felt Tip Squeak)
    filename = os.path.join(SFX_DIR, 'marker.wav')
    if not os.path.exists(filename):
        print(f"🖊️ Generating {filename}...")
        duration = 0.2
        t = np.linspace(0, duration, int(rate * duration), False)
        
        # 1. Texture (Filtered Noise)
        noise = np.random.uniform(-0.3, 0.3, len(t))
        
        # 2. Tonal Squeak (Sine wave sweeping slightly up)
        # 1000Hz is a good "squeak" pitch
        f_start, f_end = 1000, 1200
        freq = np.linspace(f_start, f_end, len(t))
        tone = np.sin(2 * np.pi * freq * t) * 0.4
        
        # 3. Mix
        raw_audio = noise + tone
        
        # 4. Envelope (Fast attack, fast release)
        envelope = np.exp(-((t - 0.1)**2) / (2 * 0.05**2))
        
        audio = raw_audio * envelope
        data = (audio / np.max(np.abs(audio)) * 18000).astype(np.int16)
        wavfile.write(filename, rate, data)
    
    # ==========================================
    # 4. SHARED / LEGACY
    # ==========================================
    download_file('pop_soft.mp3', 'https://github.com/joshua-morony/ionic-sounds/raw/master/src/assets/sounds/smart_pop.mp3')
    download_file('paper-slide.wav', 'https://github.com/joshua-morony/ionic-sounds/raw/master/src/assets/sounds/card_slide.mp3')
    
    # Deep Swish (Outro)
    filename = os.path.join(SFX_DIR, 'swish_low.wav')
    if not os.path.exists(filename):
        print(f"📉 Generating {filename}...")
        duration = 0.8
        t = np.linspace(0, duration, int(rate * duration), False)
        noise = np.random.uniform(-0.5, 0.5, len(t))
        envelope = np.exp(-((t - 0.4)**2) / (2 * 0.15**2))
        window = 30
        audio = np.convolve(noise * envelope, np.ones(window)/window, mode='same')
        data = (audio / np.max(np.abs(audio)) * 14000).astype(np.int16)
        wavfile.write(filename, rate, data)

if __name__ == "__main__":
    try:
        generate_assets()
        print("------------------------------------------------")
        print("🎉 Sonic Identity Assets Generated.")
    except ImportError:
        print("❌ Error: numpy or scipy missing.")