"""
File: visual_fx_utils.py
Core utilities for the Premium Glassmorphic Visual Engine.
Handles procedural asset generation and cinema-grade motion easing.
"""

import numpy as np
from PIL import Image, ImageDraw
from moviepy.editor import ImageClip

# CONSTANTS
WIDTH = 1080
HEIGHT = 1920

# --- 1. PREMIUM COLOR PALETTES ---
PREMIUM_THEMES = {
    'midnight_gold': {
        'bg_tint': (15, 23, 42),      # Deep Blue-Slate
        'glass_fill': (30, 41, 59, 210), # Semi-transparent slate
        'glass_border': (255, 255, 255, 40), # Subtle white stroke
        'accent': '#F59E0B',          # Amber/Gold
        'text_main': '#F8FAFC',       # Off-white
        'text_dim': '#94A3B8'         # Slate-400
    },
    'emerald_city': {
        'bg_tint': (6, 78, 59),
        'glass_fill': (6, 95, 70, 200),
        'glass_border': (167, 243, 208, 40),
        'accent': '#34D399',          # Emerald
        'text_main': '#ECFDF5',
        'text_dim': '#D1FAE5'
    },
    'royal_purple': {
        'bg_tint': (30, 10, 60),
        'glass_fill': (50, 20, 80, 200),
        'glass_border': (216, 180, 254, 40),
        'accent': '#E879F9',          # Fuchsia
        'text_main': '#FAF5FF',
        'text_dim': '#E9D5FF'
    }
}

# --- 2. CINEMA-GRADE EASING FUNCTIONS ---
def ease_out_expo(t):
    """Starts fast, decelerates smoothly to a stop. Best for UI slides."""
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def ease_out_back(t):
    """Overshoots slightly then settles. Good for 'Pop' effects."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def resolve_coord(coord, dimension_size):
    """
    Helper: Converts 'center' to numerical middle point.
    """
    if coord == 'center':
        return dimension_size / 2
    return float(coord)

def make_motion_func(start_pos, end_pos, start_time, duration, easing_func=ease_out_expo):
    """
    Returns a position function pos(t) for MoviePy's set_position.
    Interpolates between start_pos (x,y) and end_pos (x,y) using the easing logic.
    Handles 'center' automatically.
    """
    # Resolve 'center' strings to numbers ONCE
    sx = resolve_coord(start_pos[0], WIDTH)
    sy = resolve_coord(start_pos[1], HEIGHT)
    ex = resolve_coord(end_pos[0], WIDTH)
    ey = resolve_coord(end_pos[1], HEIGHT)

    # We need to account for the object size to center it properly!
    # BUT: MoviePy's set_position('center') does centering automatically.
    # Manual calculation (WIDTH/2 - obj.w/2) is hard inside a closure without knowing 'clip'.
    
    # STRATEGY: We will return the CENTER coordinates.
    # When using this, we must ensure the clip is anchored or handled correctly.
    # For simplicity, we will assume the caller wants the Top-Left coordinate to move.
    
    # Actually, simpler fix: Since MoviePy expects (x, y) tuple from pos(t),
    # let's just return the tuple.
    
    def pos(t):
        if t < start_time: return (sx, sy)
        if t > start_time + duration: return (ex, ey)
        
        # Calculate progress (0.0 to 1.0)
        linear_progress = (t - start_time) / duration
        # Apply easing curve
        eased_progress = easing_func(linear_progress)
        
        # Interpolate X and Y
        x = sx + (ex - sx) * eased_progress
        y = sy + (ey - sy) * eased_progress
        
        # If the original request was 'center', we want to return 'center' 
        # BUT we are animating. 
        # To keep it centered on X while moving Y, we should just return 
        # ('center', y) if start/end X were both 'center'.
        
        final_x = x
        if start_pos[0] == 'center' and end_pos[0] == 'center':
            final_x = 'center'
            
        final_y = y
        if start_pos[1] == 'center' and end_pos[1] == 'center':
             final_y = 'center'
             
        return (final_x, final_y)
        
    return pos

# --- 3. PROCEDURAL ASSET GENERATOR ---
def create_glass_panel(width, height, color=(30, 40, 60, 200), border_color=(255, 255, 255, 50), radius=30, border_width=2):
    """
    Generates a rounded, semi-transparent 'Glass' rectangle using PIL.
    Returns a MoviePy ImageClip.
    """
    # 1. Create a larger canvas for anti-aliasing (Supersampling)
    scale = 2
    w, h = width * scale, height * scale
    r = radius * scale
    b_w = border_width * scale
    
    # 2. Draw using PIL
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw the shape
    draw.rounded_rectangle(
        (0, 0, w, h), 
        radius=r, 
        fill=color, 
        outline=border_color, 
        width=b_w
    )
    
    # 3. Resize back down using High-Quality Lanczos filter for smooth edges
    img = img.resize((width, height), resample=Image.LANCZOS)
    
    # 4. Convert to MoviePy ImageClip
    numpy_img = np.array(img)
    return ImageClip(numpy_img)