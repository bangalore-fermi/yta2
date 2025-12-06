#!/usr/bin/env python3
"""
File: sfx_generator.py
Generates synthetic sound effects (Tick & Ding) using math.
"""
import numpy as np
from scipy.io import wavfile
import os

def generate_sfx():
    if not os.path.exists('config'):
        os.makedirs('config')

    rate = 44100  # Sample rate

    # --- 1. GENERATE "TICK" (Woodblock style) ---
    # Short sine wave with fast decay
    duration_tick = 0.1
    t_tick = np.linspace(0, duration_tick, int(rate * duration_tick), False)
    frequency = 800
    # Sine wave * Exponential Decay
    tick_wave = np.sin(frequency * 2 * np.pi * t_tick) * np.exp(-t_tick * 40)
    
    # Normalize and save
    tick_data = (tick_wave * 32767).astype(np.int16)
    wavfile.write('config/tick.wav', rate, tick_data)
    print("✅ Created config/tick.wav")

    # --- 2. GENERATE "DING" (Correct Answer Chime) ---
    # Bell sound: Fundamental + Harmonic with long decay
    duration_ding = 1.5
    t_ding = np.linspace(0, duration_ding, int(rate * duration_ding), False)
    
    f1 = 660 # High E
    f2 = 1320 # Octave up
    
    # Mix frequencies with decay
    ding_wave = (0.6 * np.sin(f1 * 2 * np.pi * t_ding) + 
                 0.4 * np.sin(f2 * 2 * np.pi * t_ding)) * np.exp(-t_ding * 3)
    
    # Normalize and save
    ding_data = (ding_wave * 32767).astype(np.int16)
    wavfile.write('config/correct.wav', rate, ding_data)
    print("✅ Created config/correct.wav")

if __name__ == "__main__":
    try:
        generate_sfx()
    except ImportError:
        print("❌ Error: numpy or scipy missing.")
        print("👉 Run: pip install numpy scipy")