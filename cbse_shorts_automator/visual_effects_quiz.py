#!/usr/bin/env python3
"""
File: visual_effects_quiz.py
Purpose: Timing-aware animation system for Quiz template.
Provides Hollywood-grade visual effects synchronized to audio.
"""

import math
import random
from moviepy.editor import (
    ColorClip, CompositeVideoClip, TextClip, 
    ImageClip, vfx
)
from debug_logger import DebugLogger, LogLevel

BASE_WIDTH = 1080
BASE_HEIGHT = 1920

# Current resolution (will be set based on config/mode)
WIDTH = 1080
HEIGHT = 1920
FPS =  24

def res_scale(value, dimension='height'):
    """
    Scale a value based on current resolution vs base resolution.
    
    Args:
        value: The base value to scale (designed for 1080x1920)
        dimension: 'height', 'width', or 'both' (for maintaining aspect ratio)
    
    Returns:
        Scaled integer value
    
    Examples:
        fontsize=res_scale(55)  # Scales 55 based on height
        width=res_scale(400, 'width')  # Scales 400 based on width
    """
    global WIDTH, HEIGHT
    
    if dimension == 'height':
        scale_factor = HEIGHT / BASE_HEIGHT
    elif dimension == 'width':
        scale_factor = WIDTH / BASE_WIDTH
    elif dimension == 'both':
        # Use smaller scale to maintain aspect ratio
        scale_factor = min(WIDTH / BASE_WIDTH, HEIGHT / BASE_HEIGHT)
    else:
        scale_factor = 1.0
    
    return int(value * scale_factor)

def set_resolution(width, height, fps=24):
    """
    Set the current resolution for scaling calculations.
    Call this at the start of video generation.
    """
    global WIDTH, HEIGHT, FPS
    WIDTH = width
    HEIGHT = height
    FPS = fps

# Font paths (same as shorts_engine.py)
FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Device frame configurations
DEVICE_FRAMES = {
    'monitor': {'border': 15, 'corner_radius': 8, 'bezel_color': (30, 30, 35)},
    'tablet': {'border': 12, 'corner_radius': 20, 'bezel_color': (20, 20, 25)},
    'phone': {'border': 8, 'corner_radius': 25, 'bezel_color': (15, 15, 20)},
    'laptop': {'border': 10, 'corner_radius': 5, 'bezel_color': (40, 40, 45)}
}

class EasingFunctions:
    """Collection of easing functions for smooth animations"""
    
    @staticmethod
    def ease_out_elastic(t, overshoot=1.1):
        """
        Elastic easing - overshoots then settles.
        t: progress from 0 to 1
        """
        if t == 0 or t == 1:
            return t
        # Elastic effect with controlled overshoot
        return t * (2 - t) * overshoot
    
    @staticmethod
    def ease_in_out_cubic(t):
        """Smooth acceleration and deceleration"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_out_bounce(t):
        """Bounce effect at the end"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375


class QuizVisualEffects:
    """
    Main class for generating quiz visual effects.
    All animations are timing-aware and sync to audio durations.
    """
    
    def __init__(self, theme, config, timing_data=None, logger=None):
        """
        Args:
            theme: Theme dictionary from THEMES in shorts_engine.py
            config: Configuration dictionary with visual parameters
            timing_data: Dict with audio timing info (optional for mock mode)
            logger: DebugLogger instance (creates default if None)
        """
        self.theme = theme
        self.config = config
        self.timing = timing_data or {}
        self.logger = logger or DebugLogger(LogLevel.NORMAL)
        
        # Extract config parameters with defaults
        self.particle_count = config.get('particle_count', 30)
        self.pip_size = config.get('pip_size', (400, 225))
        self.pip_position = config.get('pip_position', 'top-left')
        
    def _to_hex(self, color):
        """Convert color to hex format"""
        if isinstance(color, (tuple, list)):
            return '#%02x%02x%02x' % (int(color[0]), int(color[1]), int(color[2]))
        return color
    
    def create_particle_backdrop(self, duration):
        """
        Creates animated particle backdrop with drifting circles + energy bursts.
        
        Args:
            duration: Total video duration
            
        Returns:
            CompositeVideoClip with background + particles
        """
        self.logger.section_start("Particle Backdrop Generation")
        self.logger.data("Particle Count", self.particle_count)
        self.logger.data("Duration", f"{duration:.2f}s")
        
        # Base background color
        bg_color = self.theme['bg_color']
        bg = ColorClip(size=(WIDTH, HEIGHT), color=bg_color, duration=duration)
        
        clips = [bg]
        
        # Create gradient overlay (subtle)
        try:
            highlight_color = self._parse_color(self.theme['highlight'])
            num_grd_layers=1
            for i in range(num_grd_layers):  # 3 gradient layers
                radius = res_scale(50) + (i * res_scale(HEIGHT//2//num_grd_layers))
                opacity = 0.05 - (i//num_grd_layers * 0.015)
                
                gradient_circle = ColorClip(
                    size=(radius*2, radius*2), 
                    color=highlight_color
                ).set_opacity(opacity)
                
                gradient_circle = gradient_circle.set_position(
                    (WIDTH//2 - radius, HEIGHT//2 - radius)
                ).set_duration(duration)
                
                clips.append(gradient_circle)
                
            self.logger.log("Gradient overlay created", LogLevel.DEBUG)
        except Exception as e:
            self.logger.warning(f"Gradient creation failed: {e}")
        
        # Create drifting particles
        self.logger.log(f"Generating {self.particle_count} particles", LogLevel.DEBUG)
        
        highlight_color = self._parse_color(self.theme['highlight'])
        
        for i in range(self.particle_count):
            self.logger.progress(i+1, self.particle_count, "Particles")
            
            x = random.randint(0, WIDTH)
            y_start = HEIGHT + random.randint(0, res_scale(200))
            drift_speed = random.uniform(40, 80)
            size = random.choice([res_scale(6), res_scale(8), res_scale(10), res_scale(12)])
            
            particle = ColorClip(
                size=(size, size), 
                color=highlight_color
            ).set_opacity(random.uniform(0.2, 0.4))
            
            def make_drift_func(x_pos, y_start, speed):
                def drift(t):
                    wobble = math.sin(t * 2) * res_scale(10)
                    return (x_pos + wobble, y_start - (speed * t))
                return drift
            
            particle = particle.set_position(
                make_drift_func(x, y_start, drift_speed)
            ).set_duration(duration)
            
            clips.append(particle)
        
        # Add 5 "speed streak" particles (USP: Fast-paced energy)
        self.logger.log("Adding energy burst streaks", LogLevel.DEBUG)
        
        for i in range(5):
            # Random timing
            burst_start = random.uniform(2, duration - 2)
            burst_duration = 1.5
            
            # Diagonal streak
            streak = ColorClip(size=(3, 50), color=highlight_color).set_opacity(0.6)
            
            # Diagonal motion (top-left to bottom-right or reverse)
            direction = random.choice([-1, 1])
            start_x = WIDTH if direction > 0 else 0
            start_y = random.randint(300, 1000)
            
            def make_streak_func(start_x, start_y, direction):
                def streak_motion(t):
                    progress = t / 1.5  # 1.5s duration
                    x = start_x + (direction * -WIDTH * progress)
                    y = start_y + (HEIGHT * 0.3 * progress)
                    return (x, y)
                return streak_motion
            
            streak = streak.set_position(
                make_streak_func(start_x, start_y, direction)
            ).set_start(burst_start).set_duration(burst_duration)
            
            clips.append(streak)
        
        backdrop = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        
        self.logger.section_end("Particle Backdrop Generation")
        return backdrop
    
    def create_pip_source_video(self, source_video_clip, duration):
        """
        Creates Picture-in-Picture with wavy journey motion.
        PIP travels from one edge to the other with gentle wave.
        
        Args:
            source_video_clip: VideoFileClip of source content
            duration: Total video duration
            
        Returns:
            Positioned and styled video clip
        """
        self.logger.section_start("PIP Source Video")
        self.logger.data("Original Size", f"{source_video_clip.w}x{source_video_clip.h}")
        self.logger.data("Target Size", f"{self.pip_size[0]}x{self.pip_size[1]}")
        
        try:
            # Resize maintaining aspect ratio
            pip = source_video_clip.resize(height=self.pip_size[1])
            
            # Crop to exact width if needed (center crop)
            if pip.w > self.pip_size[0]:
                x_center = pip.w / 2
                pip = pip.crop(
                    x1=x_center - self.pip_size[0]/2,
                    x2=x_center + self.pip_size[0]/2
                )
            
            pip = pip.set_duration(duration)
            
            # Determine journey path (random start side)
            import random
            start_side = random.choice(['left', 'right'])
            
            # Random device frame
            device = random.choice(list(DEVICE_FRAMES.keys()))
            frame_config = DEVICE_FRAMES[device]
            border_thickness = res_scale(frame_config['border'])
            border_color = frame_config['bezel_color']
            border_opacity = 0.95  # Solid for device feel

            self.logger.data("Device Frame", device.upper())    
            #border_thickness = 8
            
            if start_side == 'left':
                start_x = res_scale(50) + border_thickness
                end_x = WIDTH - self.pip_size[0] - border_thickness - res_scale(50)
                self.logger.data("Journey", "LEFT → RIGHT")
            else:
                start_x = WIDTH - self.pip_size[0] - border_thickness - res_scale(50)
                end_x = res_scale(50) + border_thickness
                self.logger.data("Journey", "RIGHT → LEFT")
            
            y_base = res_scale(150)  # Safe zone top
            # Complex 4-phase journey with final enlargement
            def wavy_journey(t):
                progress = min(t / duration, 1.0)
                
                # Phase timings
                PHASE_1_END = 0.30  # 30% - reach opposite edge
                PHASE_2_END = 0.55  # 55% - return to start
                PHASE_3_END = 0.85  # 85% - reach center
                # PHASE_4 = 0.85-1.0 (15%) - enlargement
                
                center_x = (WIDTH - self.pip_size[0]) / 2
                
                # ========================================
                # HORIZONTAL POSITION CALCULATION
                # ========================================
                
                if progress < PHASE_1_END:
                    # Phase 1: Start → Opposite
                    phase_progress = progress / PHASE_1_END
                    current_x = start_x + (end_x - start_x) * phase_progress
                    
                elif progress < PHASE_2_END:
                    # Phase 2: Opposite → Start
                    phase_progress = (progress - PHASE_1_END) / (PHASE_2_END - PHASE_1_END)
                    current_x = end_x + (start_x - end_x) * phase_progress
                    
                elif progress < PHASE_3_END:
                    # Phase 3: Start → Center
                    phase_progress = (progress - PHASE_2_END) / (PHASE_3_END - PHASE_2_END)
                    current_x = start_x + (center_x - start_x) * phase_progress
                    
                else:
                    # Phase 4: Hold at center (for enlargement)
                    current_x = center_x
                
                # ========================================
                # VERTICAL POSITION CALCULATION
                # ========================================
                
                if progress < PHASE_3_END:
                    # Phases 1-3: Wavy motion (6 complete cycles)
                    wave_progress = progress * 6 * 2 * math.pi
                    wave_offset = math.sin(wave_progress) * res_scale(15)
                    current_y = y_base + wave_offset
                else:
                    # Phase 4: Settle to vertical center as it enlarges
                    phase_progress = (progress - PHASE_3_END) / (1.0 - PHASE_3_END)
                    
                    # Gradually move to vertical center
                    target_y = (HEIGHT - self.pip_size[1]) / 2 *0 + y_base
                    current_y = y_base + (target_y - y_base) * phase_progress
                
                return (current_x, current_y)
            # Scale function for enlargement in Phase 4
            def pip_scale(t):
                progress = min(t / duration, 1.0)
                                
                # Skip enlargement if PIP already large
                if self.pip_size[0] > res_scale(600):
                    return 1.0  # No scaling needed
                PHASE_3_END = 0.85
                
                if progress < PHASE_3_END:
                    return 1.0  # Normal size during phases 1-3
                else:
                    # Phase 4: Enlarge
                    phase_progress = (progress - PHASE_3_END) / (1.0 - PHASE_3_END)
                    
                    # Calculate target scale to fill width
                    target_width = WIDTH - res_scale(100)  # 50px margin each side
                    target_scale = target_width / self.pip_size[0]
                    
                    # Cap maximum scale (prevent going off-screen top)
                    max_scale = 2.8  # Reasonable limit
                    target_scale = min(target_scale, max_scale)
                    
                    # Smooth easing (ease-out)
                    eased_progress = 1 - pow(1 - phase_progress, 3)  # Cubic ease-out
                    
                    current_scale = 1.0 + (target_scale - 1.0) * eased_progress
                    return current_scale

                # Cache scale values (calculate once, reuse)
            scale_cache = {}

            def pip_scale_cached(t):
                frame = int(t * FPS)  # Assuming 24 fps
                if frame not in scale_cache:
                    scale_cache[frame] = pip_scale(t)
                return scale_cache[frame]

            pip = pip.resize(pip_scale_cached)

            # Apply scale to PIP
            #pip = pip.resize(pip_scale)
            pip = pip.set_position(wavy_journey)
            
            self.logger.log("Wavy journey animation applied", LogLevel.DEBUG)
            
            # Border overlays (follow PIP motion)
            #border_color = (255, 255, 255)
            border_opacity = 0.1
            
            # Top border
            top_border = ColorClip(
                size=(self.pip_size[0] + border_thickness*2, border_thickness),
                color=border_color
            ).set_opacity(border_opacity)
            
            def top_border_pos(t):
                pip_pos = wavy_journey(t)
                return (pip_pos[0] - border_thickness, pip_pos[1] - border_thickness)
            
            top_border = top_border.set_position(top_border_pos).set_duration(duration)
            
            # Bottom border
            bottom_border = ColorClip(
                size=(self.pip_size[0] + border_thickness*2, border_thickness),
                color=border_color
            ).set_opacity(border_opacity)
            
            def bottom_border_pos(t):
                pip_pos = wavy_journey(t)
                return (pip_pos[0] - border_thickness, pip_pos[1] + self.pip_size[1])
            
            bottom_border = bottom_border.set_position(bottom_border_pos).set_duration(duration)
            
            # Left border
            left_border = ColorClip(
                size=(border_thickness, self.pip_size[1]),
                color=border_color
            ).set_opacity(border_opacity)
            
            def left_border_pos(t):
                pip_pos = wavy_journey(t)
                return (pip_pos[0] - border_thickness, pip_pos[1])
            
            left_border = left_border.set_position(left_border_pos).set_duration(duration)
            
            # Right border
            right_border = ColorClip(
                size=(border_thickness, self.pip_size[1]),
                color=border_color
            ).set_opacity(border_opacity)
            
            def right_border_pos(t):
                pip_pos = wavy_journey(t)
                return (pip_pos[0] + self.pip_size[0], pip_pos[1])
            
            right_border = right_border.set_position(right_border_pos).set_duration(duration)
            

            # Top border - only visible when not enlarged
            def top_border_visibility(t):
                progress = min(t / duration, 1.0)
                return 0.4 if progress < 0.85 else 0  # Fade out during phase 4

            #top_border = top_border.set_opacity(top_border_visibility)

            # Apply same to all borders (bottom, left, right)
            #bottom_border = bottom_border.set_opacity(top_border_visibility)
            #left_border = left_border.set_opacity(top_border_visibility)
            #right_border = right_border.set_opacity(top_border_visibility)

            # Subtle glow (pulsing)
            # Subtle glow (pulsing) - FIXED
            glow_size = (self.pip_size[0] + res_scale(80), self.pip_size[1] + res_scale(80))
            glow_color = self._parse_color(self.theme['highlight'])

            glow = ColorClip(size=glow_size, color=glow_color).set_duration(duration)

            # FIXED: Inline lambda for opacity
            self.logger.log("Before Glow  application", LogLevel.DEBUG)
            #glow = glow.set_opacity(lambda t: 0.05 + 0.05 * abs(math.sin(t / 2.0 * math.pi)))
            glow = glow.set_opacity(0.08)
            self.logger.log("Glow  applied", LogLevel.DEBUG)

            def glow_pos(t):
                pip_pos = wavy_journey(t)
                return (pip_pos[0] - res_scale(40), pip_pos[1] - res_scale(40))

            glow = glow.set_position(glow_pos)
            
            # Composite: Glow -> Borders -> PIP
            pip_base = CompositeVideoClip([
                glow, top_border, bottom_border, left_border, right_border, pip
            ], size=(WIDTH, HEIGHT))

            # ADD YOUTUBE CONTROLS OVERLAY
            youtube_controls = self.create_youtube_overlay(
                pip_width=self.pip_size[0],
                pip_height=self.pip_size[1],
                pip_position_func=wavy_journey,
                pip_scale_func=pip_scale_cached,  # NEW: Pass scale function
                duration=duration,
                progress_percent=42,
                timestamp="2:34 / 7:12"
            )

            if youtube_controls:
                pip_with_effects = CompositeVideoClip([
                    pip_base, youtube_controls
                ], size=(WIDTH, HEIGHT))
            else:
                pip_with_effects = pip_base

            self.logger.section_end("PIP Source Video")
            return pip_with_effects
            
            self.logger.section_end("PIP Source Video")
            return pip_with_effects
            
        except Exception as e:
            self.logger.error(f"PIP creation failed: {e}")
            return source_video_clip.set_duration(duration)

    def create_youtube_overlay(self, pip_width, pip_height, pip_position_func, 
                            pip_scale_func=None, duration=None, 
                            progress_percent=40, timestamp="2:34 / 7:12"):
        """
        Creates YouTube-style player controls overlay for PIP.
        
        Args:
            pip_width: Width of PIP video
            pip_height: Height of PIP video
            pip_position_func: Function that returns (x, y) for PIP at time t
            duration: Video duration
            progress_percent: Progress bar fill percentage (0-100)
            timestamp: Time display text (e.g., "2:34 / 7:12")
            
        Returns:
            CompositeVideoClip with control overlays
        """
        import random
        progress_percent = random.randint(35, 55)  # 35-55% progress
        self.logger.section_start("YouTube Player Overlay")
        self.logger.data("Progress", f"{progress_percent}%")
        
        clips = []
        
        # ============================================================
        # CONTROL BAR BACKGROUND (dark gray bar at bottom)
        # ============================================================
        
        control_bar_height = res_scale(40)
        control_bg = ColorClip(
            size=(pip_width, control_bar_height),
            color=(24, 24, 24)  # YouTube dark background
        ).set_opacity(0.9)
        
        def control_bg_pos(t):
            pip_x, pip_y = pip_position_func(t)
            scale = pip_scale_func(t) if pip_scale_func else 1.0
            
            scaled_height = pip_height * scale
            scaled_width = pip_width * scale
            
            # Offset for centered scaling
            x_offset = (scaled_width - pip_width) / 2
            y_offset = (scaled_height - pip_height) / 2
            
            return (pip_x - x_offset, pip_y + scaled_height - control_bar_height - y_offset)

        # Apply same pattern to ALL position functions in youtube controls
        control_bg = control_bg.set_position(control_bg_pos).set_duration(duration)
        clips.append(control_bg)
        
        # ============================================================
        # PROGRESS BAR
        # ============================================================
        
        progress_bar_height = res_scale(4)
        progress_bar_y_offset = res_scale(10)  # From top of control bar
        
        # Background track (unfilled)
        progress_bg = ColorClip(
            size=(pip_width - res_scale(20), progress_bar_height),
            color=(77, 77, 77)  # Medium gray
        ).set_opacity(0.8)
        
        def progress_bg_pos(t):
            pip_x, pip_y = pip_position_func(t)
            return (pip_x + res_scale(10), 
                    pip_y + pip_height - control_bar_height + progress_bar_y_offset)
        
        progress_bg = progress_bg.set_position(progress_bg_pos).set_duration(duration)
        clips.append(progress_bg)
        
        # Filled portion (red)
        filled_width = int((pip_width - res_scale(20)) * (progress_percent / 100))
        progress_fill = ColorClip(
            size=(filled_width, progress_bar_height),
            color=(255, 0, 0)  # YouTube red
        ).set_opacity(1.0)
        
        def progress_fill_pos(t):
            pip_x, pip_y = pip_position_func(t)
            return (pip_x + res_scale(10), 
                    pip_y + pip_height - control_bar_height + progress_bar_y_offset)
        
        progress_fill = progress_fill.set_position(progress_fill_pos).set_duration(duration)
        clips.append(progress_fill)
        
        # ============================================================
        # PLAYER BUTTONS (Previous, Play/Pause, Next)
        # ============================================================
        
        button_size = res_scale(20)
        button_y_offset = res_scale(18)  # From top of control bar
        
        # Button positions (left-aligned)
        button_spacing = res_scale(35)
        button_start_x = res_scale(15)
        
        # Previous button (⏮)
        try:
            prev_btn = TextClip(
                "◄",
                fontsize=res_scale(18),
                color='white',
                font='Noto Color Emoji',
                method='label'
            )
            
            def prev_btn_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + button_start_x, 
                        pip_y + pip_height - control_bar_height + button_y_offset)
            
            prev_btn = prev_btn.set_position(prev_btn_pos).set_duration(duration)
            clips.append(prev_btn)
        except:
            self.logger.warning("Previous button creation failed (emoji font issue)")
        
        # Play/Pause button (⏸) - center of 3 buttons
        try:
            play_btn = TextClip(
                "| |",
                fontsize=res_scale(18),
                color='white',
                font='Noto Color Emoji',
                method='label'
            )
            
            def play_btn_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + button_start_x + button_spacing, 
                        pip_y + pip_height - control_bar_height + button_y_offset)
            
            play_btn = play_btn.set_position(play_btn_pos).set_duration(duration)
            clips.append(play_btn)
        except:
            self.logger.warning("Play button creation failed (emoji font issue)")
        
        # Next button (⏭)
        try:
            next_btn = TextClip(
                "►►",
                fontsize=res_scale(18),
                color='white',
                font='Noto Color Emoji',
                method='label'
            )
            
            def next_btn_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + button_start_x + (button_spacing * 1), 
                        pip_y + pip_height - control_bar_height + button_y_offset)
            
            next_btn = next_btn.set_position(next_btn_pos).set_duration(duration)
            clips.append(next_btn)
        except:
            self.logger.warning("Next button creation failed (emoji font issue)")

        # Volume icon (right side of control bar)
        try:
            volume_icon = TextClip(
                "🔊",  # Or "VOL"
                fontsize=res_scale(14),
                color='white',
                font='Noto Color Emoji',
                method='label'
            )
            
            def volume_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + pip_width - res_scale(100), 
                        pip_y + pip_height - control_bar_height + res_scale(20))
            
            volume_icon = volume_icon.set_position(volume_pos).set_duration(duration)
            clips.append(volume_icon)
        except:
            pass    
        
        # ============================================================
        # TIMESTAMP (right-aligned)
        # ============================================================
        
        try:
            timestamp_clip = TextClip(
                timestamp,
                fontsize=res_scale(14),
                color='white',
                font='Arial',
                method='label'
            )
            
            timestamp_width = timestamp_clip.w
            
            def timestamp_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + pip_width - timestamp_width - res_scale(15), 
                        pip_y + pip_height - control_bar_height + res_scale(20))
            
            timestamp_clip = timestamp_clip.set_position(timestamp_pos).set_duration(duration)
            clips.append(timestamp_clip)
            
        except Exception as e:
            self.logger.warning(f"Timestamp creation failed: {e}")
        
        # ============================================================
        # QUALITY BADGE (optional - shows video quality)
        # ============================================================
        
        try:
            quality_badge = TextClip(
                "HD",
                fontsize=res_scale(12),
                color='white',
                font='Arial-Bold',
                method='label',
                bg_color=self._to_hex((255, 0, 0)),  # Red background
            )
            
            def quality_pos(t):
                pip_x, pip_y = pip_position_func(t)
                return (pip_x + pip_width - res_scale(35), 
                        pip_y + res_scale(10))  # Top-right of video
            
            quality_badge = quality_badge.set_position(quality_pos).set_duration(duration)
            quality_badge = quality_badge.set_opacity(0.8)
            clips.append(quality_badge)
            
        except Exception as e:
            self.logger.warning(f"Quality badge creation failed: {e}")
        
        self.logger.section_end("YouTube Player Overlay")
        
        if clips:
            return CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        else:
            return None

    def create_timing_markers(self, timing_manifest, duration):
        """
        Creates visual timing markers (red=start, green=end) for sync testing.
        
        Args:
            timing_manifest: Dict with timing data
            duration: Total video duration
            
        Returns:
            CompositeVideoClip with marker lines
        """
        self.logger.section_start("Timing Markers")
        
        markers = []
        
        # Define marker positions for each audio segment
        segments = ['hook', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'think', 'explanation', 'cta']
        
        for i, seg in enumerate(segments):
            if seg not in timing_manifest:
                continue
                
            timing = timing_manifest[seg]
            start_time = timing['start']
            end_time = timing['start'] + timing['duration']
            
            # Vertical position (stagger markers)
            y_pos = 400 + (i * 50)
            
            # Start marker (red)
            start_marker = ColorClip(
                size=(5, 60), 
                color=(255, 0, 0)
            ).set_position((100, y_pos)).set_start(start_time).set_duration(0.2)
            
            # End marker (green)
            end_marker = ColorClip(
                size=(5, 60), 
                color=(0, 255, 0)
            ).set_position((200, y_pos)).set_start(end_time).set_duration(0.2)
            
            # Label
            label = TextClip(
                seg.upper(),
                fontsize=res_scale(20),
                color='white',
                font=FONT_REGULAR
            ).set_position((210, y_pos + 20)).set_start(start_time).set_duration(timing['duration'])
            
            markers.extend([start_marker, end_marker, label])
            
            self.logger.data(f"{seg}", f"{start_time:.2f}s -> {end_time:.2f}s", LogLevel.DEBUG)
        
        self.logger.section_end("Timing Markers")
        return CompositeVideoClip(markers, size=(WIDTH, HEIGHT)) if markers else None
    
    # NEW function signature:
    def create_cta_banner(self, social_text, link_text, social_start, social_duration, 
                        link_start, link_duration, style='full-banner', cta_y=None):
        """
        Creates split-display CTA (Call-to-Action) overlay.
        
        Args:
            ...existing args...
            cta_y: Y position for banner (if None, uses default calculation)
        """
        self.logger.section_start("Split CTA Banner")
        self.logger.data("Social Text", social_text)
        self.logger.data("Link Text", link_text)
        self.logger.data("Social Timing", f"{social_start:.2f}s for {social_duration:.2f}s")
        self.logger.data("Link Timing", f"{link_start:.2f}s for {link_duration:.2f}s")
        
        clips = []
        
        if style == 'full-banner':
            # Banner configuration
            banner_width = res_scale(950)
            banner_height = res_scale(140)
            banner_x = (WIDTH - banner_width) // 2
            # NEW:
            if cta_y is not None:
                banner_y = cta_y
            else:
                banner_y = res_scale(1300)  # Fallback
            
            bg_color = self._parse_color(self.theme['highlight'])
            
            # Total duration (from social start to link end)
            total_duration = (link_start + link_duration) - social_start
            
            # Background banner (persists throughout)
            banner_bg = ColorClip(
                size=(banner_width, banner_height),
                color=bg_color
            ).set_opacity(0.92)
            
            # Entrance animation with gentle pulse
            def banner_motion(t):
                if t < 0.5:  # Entrance
                    progress = t / 0.5
                    eased = EasingFunctions.ease_out_elastic(progress, 1.05)
                    offset = (1 - eased) * res_scale(100)
                    return (banner_x, banner_y + offset)
                else:  # Gentle pulse
                    pulse_t = (t - 0.5) / 3.0  # 3-second cycle
                    scale = 1.0 + 0.015 * math.sin(pulse_t * 2 * math.pi)
                    offset = (1 - scale) * banner_height / 2
                    return (banner_x, banner_y + offset)
            
            banner_bg = banner_bg.set_position(banner_motion).set_start(social_start).set_duration(total_duration)
            clips.append(banner_bg)
            
            # White border
            border = ColorClip(
                size=(banner_width + res_scale(8), banner_height + res_scale(8)),
                color=(255, 255, 255)
            ).set_opacity(0.7)
            
            def border_motion(t):
                bg_pos = banner_motion(t)
                return (bg_pos[0] - 4, bg_pos[1] - 4)
            
            border = border.set_position(border_motion).set_start(social_start).set_duration(total_duration)
            clips.insert(0, border)
            
            # PART A: Social Action Text
            try:
                social_clip = TextClip(
                    social_text,
                    fontsize=res_scale(52),
                    color='black',
                    font=FONT_BOLD,
                    method='caption',
                    align='center',
                    size=(banner_width - res_scale(40), None)
                )
                
                def social_text_pos(t):
                    bg_pos = banner_motion(t)
                    text_y = bg_pos[1] + (banner_height - social_clip.h) // 2
                    return (bg_pos[0] + res_scale(20), text_y)
                
                # Social text appears and stays until link starts
                actual_social_duration = (link_start - social_start)  # Full duration until transition
                social_clip = social_clip.set_position(social_text_pos).set_start(social_start).set_duration(actual_social_duration)

                # Fade out at end
                social_clip = social_clip.crossfadeout(0.3)
                clips.append(social_clip)
                
                self.logger.log("Social action text created", LogLevel.DEBUG)
                
            except Exception as e:
                self.logger.warning(f"Social text creation failed: {e}")
            
            # PART B: Link Directive Text
            try:
                link_clip = TextClip(
                    link_text,
                    fontsize=res_scale(52),
                    color='black',
                    font=FONT_BOLD,
                    method='caption',
                    align='center',
                    size=(banner_width - res_scale(40), None)
                )
                
                def link_text_pos(t):
                    bg_pos = banner_motion(t + (link_start - social_start))
                    text_y = bg_pos[1] + (banner_height - link_clip.h) // 2
                    return (bg_pos[0] + res_scale(20), text_y)
                
                link_clip = link_clip.set_position(link_text_pos).set_start(link_start).set_duration(link_duration)
                
                # Fade in at start
                link_clip = link_clip.crossfadein(0.3)
                clips.append(link_clip)
                
                self.logger.log("Link directive text created", LogLevel.DEBUG)
                
            except Exception as e:
                self.logger.warning(f"Link text creation failed: {e}")
        
        self.logger.section_end("Split CTA Banner")
        
        if clips:
            return CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        return None
        """
        Creates CTA (Call-to-Action) overlay with professional styling.
        
        Args:
            cta_text: Text to display (e.g., "Subscribe for more!")
            start_time: When CTA appears
            duration: How long it's visible
            style: 'full-banner', 'corner-badge', or 'split'
            
        Returns:
            CompositeVideoClip with CTA elements
        """
        self.logger.section_start("CTA Banner Creation")
        self.logger.data("Text", cta_text)
        self.logger.data("Style", style)
        self.logger.data("Timing", f"{start_time:.2f}s for {duration:.2f}s")
        
        clips = []
        
        if style == 'full-banner':
            # Full-width banner design
            banner_width = res_scale(950)
            banner_height = res_scale(140)
            banner_x = (WIDTH - banner_width) // 2
            banner_y = res_scale(1300)  # Safe zone (420px from bottom)
            
            # Background card
            bg_color = self._parse_color(self.theme['highlight'])
            banner_bg = ColorClip(
                size=(banner_width, banner_height),
                color=bg_color
            ).set_opacity(0.95)
            
            # Position with slide-up animation
            def banner_entrance(t):
                if t < 0.5:  # 0.5s entrance
                    progress = t / 0.5
                    offset = (1 - EasingFunctions.ease_out_elastic(progress, 1.05)) * res_scale(100)
                    return (banner_x, banner_y + offset)
                else:
                    # Gentle pulse after entrance
                    pulse_progress = (t - 0.5) / 2.0  # 2s cycle
                    scale = 1.0 + 0.01 * math.sin(pulse_progress * 2 * math.pi)
                    offset = (1 - scale) * banner_height / 2
                    return (banner_x, banner_y + offset)
            
            banner_bg = banner_bg.set_position(banner_entrance).set_start(start_time).set_duration(duration)
            clips.append(banner_bg)
            
            # Border overlay
            border_clip = ColorClip(
                size=(banner_width + res_scale(6),banner_height + res_scale(6)),
                color=(255, 255, 255)
            ).set_opacity(0.8)
            
            def border_position(t):
                bg_pos = banner_entrance(t)
                return (bg_pos[0] - res_scale(3), bg_pos[1] - res_scale(3))
            
            border_clip = border_clip.set_position(border_position).set_start(start_time).set_duration(duration)
            clips.insert(0, border_clip)  # Behind background
            
            # Parse CTA text (handle two-line format)
            lines = cta_text.split('\n') if '\n' in cta_text else [cta_text]
            
            # Line 1: Main CTA (larger, bold)
            try:
                main_text = lines[0]
                text_clip_1 = TextClip(
                    main_text,
                    fontsize=res_scale(52),
                    color='black',
                    font=FONT_BOLD,
                    method='caption',
                    align='center',
                    size=(banner_width - res_scale(40), None)
                )
                
                def text1_position(t):
                    bg_pos = banner_entrance(t)
                    text_y = bg_pos[1] + res_scale(25) if len(lines) > 1 else bg_pos[1] + (banner_height - text_clip_1.h) // 2
                    return (bg_pos[0] + res_scale(20), text_y)
                
                text_clip_1 = text_clip_1.set_position(text1_position).set_start(start_time).set_duration(duration)
                clips.append(text_clip_1)
                
                # Line 2: Secondary text (smaller)
                if len(lines) > 1:
                    text_clip_2 = TextClip(
                        lines[1],
                        fontsize=36,
                        color='black',
                        font=FONT_REGULAR,
                        method='caption',
                        align='center',
                        size=(banner_width - 40, None)
                    )
                    
                    def text2_position(t):
                        bg_pos = banner_entrance(t)
                        return (bg_pos[0] + 20, bg_pos[1] + 80)
                    
                    text_clip_2 = text_clip_2.set_position(text2_position).set_start(start_time).set_duration(duration)
                    clips.append(text_clip_2)
                    
            except Exception as e:
                self.logger.warning(f"TextClip creation failed: {e}")
        
        elif style == 'corner-badge':
            # Compact corner badge
            badge_width = 300
            badge_height = 150
            badge_x = WIDTH - badge_width - 60
            badge_y = 1250
            
            bg_color = self._parse_color(self.theme['highlight'])
            badge_bg = ColorClip(
                size=(badge_width, badge_height),
                color=bg_color
            ).set_opacity(0.95).set_position((badge_x, badge_y)).set_start(start_time).set_duration(duration)
            clips.append(badge_bg)
            
            # Compact text
            try:
                text_clip = TextClip(
                    cta_text,
                    fontsize=36,
                    color='black',
                    font=FONT_BOLD,
                    method='caption',
                    align='center',
                    size=(badge_width - 20, None)
                )
                text_clip = text_clip.set_position(
                    (badge_x + 10, badge_y + (badge_height - text_clip.h) // 2)
                ).set_start(start_time).set_duration(duration)
                clips.append(text_clip)
            except Exception as e:
                self.logger.warning(f"Badge text creation failed: {e}")
        
        self.logger.section_end("CTA Banner Creation")
        
        if clips:
            return CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        else:
            return None


    def create_typewriter_text(self, text, audio_duration, start_time, total_remaining_time=None,  fontsize=55, 
                              color='white', position='center', y_offset=900):
        """
        Creates word-by-word typewriter reveal effect, synced to audio duration.
        
        Args:
            text: Text to display
            audio_duration: Length of audio (determines reveal speed)
            start_time: When animation starts
            fontsize: Text size
            color: Text color (hex or tuple)
            position: 'center' or custom (x, y) tuple
            y_offset: Vertical position (if position='center')
            
        Returns:
            CompositeVideoClip with typewriter animation
        """
        self.logger.section_start("TypeWriter Text Effect")
        self.logger.data("Text", text)
        self.logger.data("Audio Duration", f"{audio_duration:.2f}s")
        self.logger.data("Words", len(text.split()))
        
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            self.logger.warning("Empty text provided")
            return None
        
        # Calculate delay per word to match audio duration
        # Reserve 10% for final hold time
        reveal_duration = audio_duration * 0.9
        word_delay = reveal_duration / word_count
        
        self.logger.data("Word Delay", f"{word_delay:.3f}s")
        
        clips = []
        text_color = self._to_hex(color)
        
        # Background card (appears immediately, stays throughout)
        try:
            # Measure text dimensions
            full_text_clip = TextClip(
                text,
                fontsize=int(fontsize),
                color=text_color,
                font=FONT_BOLD,
                stroke_color='black',
                stroke_width=res_scale(3),
                method='caption',
                size=(WIDTH - res_scale(120), None),
                align='center'
            )
            
            # Semi-transparent background card
            card_padding = res_scale(20)
            card_width = min(full_text_clip.w + card_padding * 2, WIDTH - res_scale(100))
            card_height = full_text_clip.h + card_padding * 2
            
            bg_card = ColorClip(
                size=(card_width, card_height),
                color=self.theme['bg_color']
            ).set_opacity(0.8)
            
            # Position calculation
            if position == 'center':
                card_x = (WIDTH - card_width) // 2
                card_y = y_offset
            else:
                card_x, card_y = position
            
            # Entrance animation: scale up
            def card_entrance(t):
                if t < 0.3:
                    scale = EasingFunctions.ease_out_elastic(t / 0.3, 1.05)
                    offset_x = (1 - scale) * card_width / 2
                    offset_y = (1 - scale) * card_height / 2
                    return (card_x + offset_x, card_y + offset_y)
                return (card_x, card_y)
            
            bg_card = bg_card.set_position(card_entrance).set_start(start_time).set_duration(total_remaining_time)
            clips.append(bg_card)
            
            self.logger.log("Background card created", LogLevel.DEBUG)
            
        except Exception as e:
            self.logger.warning(f"Background card creation failed: {e}")
            card_x = (WIDTH - res_scale(800)) // 2
            card_y = y_offset
        
        # Create word-by-word reveal
        for i in range(word_count):
            self.logger.progress(i + 1, word_count, "Text Clips")
            
            # Progressive text (all words up to current)
            progressive_text = " ".join(words[:i+1])
            
            try:
                word_clip = TextClip(
                    progressive_text,
                    fontsize=int(fontsize),
                    color=text_color,
                    font=FONT_BOLD,
                    stroke_color='black',
                    stroke_width=res_scale(3),
                    method='caption',
                    size=(WIDTH - res_scale(140), None),
                    align='center'
                )
                
                # Position relative to card
                text_x = (WIDTH - word_clip.w) // 2
                text_y = card_y + res_scale(20)  # Padding inside card
                
                # Timing: each word appears sequentially
                word_start = start_time + (i * word_delay)
                
                # FIXED: Duration is only until next word appears (not until end)
                if i < word_count - 1:
                    word_duration = word_delay  # Show only until next word
                else:
                    if total_remaining_time:
                        word_duration = total_remaining_time - (i * word_delay)
                    else:
                        word_duration = audio_duration - (i * word_delay)
                
                # Last word gets a subtle pop
                if i == word_count - 1:
                    def last_word_pop(t):
                        if t < 0.2:
                            scale = 1.0 + 0.05 * math.sin(t / 0.2 * math.pi)
                            offset_x = (1 - scale) * word_clip.w / 2
                            offset_y = (1 - scale) * word_clip.h / 2
                            return (text_x + offset_x, text_y + offset_y)
                        return (text_x, text_y)
                    word_clip = word_clip.set_position(last_word_pop)
                else:
                    word_clip = word_clip.set_position((text_x, text_y))
                
                word_clip = word_clip.set_start(word_start).set_duration(word_duration)
                clips.append(word_clip)
                
            except Exception as e:
                self.logger.warning(f"Word clip {i+1} creation failed: {e}")
                continue
        
        self.logger.section_end("TypeWriter Text Effect")
        
        if len(clips) > 0:
            return CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
        return None
    
    # NEW function signature:
    def create_options_sequence(self, options_data, theme, use_relative_y=True):
        """
        Creates staggered slide-in animation for quiz options.
        
        Args:
            options_data: List of dicts with format:
                [
                    {
                        'text': 'A) Water', 
                        'start_time': 5.5, 
                        'duration': 45.0, 
                        'is_correct': False,
                        'y_position': 1200  # NEW: Explicit Y position
                    },
                    ...
                ]
            theme: Theme dictionary
            use_relative_y: If True, use y_position from data; if False, calculate from OPT_START_Y
            
        Returns:
            List of positioned TextClip objects
        """
        self.logger.section_start("Options Sequence")
        self.logger.data("Option Count", len(options_data))
        
        clips = []
        
        # Layout constants
        OPT_START_Y = res_scale(1050)  # Below question
        OPT_GAP = res_scale(130)
        OPT_WIDTH = WIDTH - res_scale(120)
        
        opt_bg_color = self._to_hex(theme.get('bg_color', (15, 23, 42)))
        
        for i, opt in enumerate(options_data):
            self.logger.progress(i + 1, len(options_data), "Options")
            
            text = opt['text']
            start_time = opt['start_time']
            duration = opt['duration']
            
            # Alternating slide direction (left, right, left, right)
            from_left = (i % 2 == 0)
            
            try:
                # Create text clip
                opt_clip = TextClip(
                    text,
                    fontsize=res_scale(52),
                    color='white',
                    font=FONT_REGULAR,
                    bg_color=opt_bg_color,
                    method='caption',
                    size=(OPT_WIDTH, res_scale(100)),
                    align='West'
                )
                
                # NEW:
                if use_relative_y and 'y_position' in opt:
                    final_y = opt['y_position']
                else:
                    # Fallback to old method
                    OPT_START_Y = res_scale(1050)
                    OPT_GAP = res_scale(130)
                    final_y = OPT_START_Y + (i * OPT_GAP)
                # Elastic slide-in animation
                def make_slide_func(from_left_dir, final_y_pos):
                    def slide_position(t):
                        if t < SLIDE_DURATION:  # 0.6s entrance
                            progress = t / SLIDE_DURATION
                            eased = EasingFunctions.ease_out_elastic(progress, 1.08)
                            
                            if from_left_dir:
                                # Slide from left
                                start_x = -OPT_WIDTH
                                final_x = (WIDTH - OPT_WIDTH) // 2
                            else:
                                # Slide from right
                                start_x = WIDTH
                                final_x = (WIDTH - OPT_WIDTH) // 2
                            
                            current_x = start_x + (final_x - start_x) * eased
                            return (current_x, final_y_pos)
                        else:
                            # Settled position
                            return ((WIDTH - OPT_WIDTH) // 2, final_y_pos)
                    return slide_position
                
                
                SLIDE_DURATION = 0.6
                opt_clip = opt_clip.set_position(
                    make_slide_func(from_left, final_y)
                ).set_start(start_time - SLIDE_DURATION).set_duration(duration + SLIDE_DURATION)
                clips.append(opt_clip)
                
                self.logger.data(f"Option {i+1}", f"Slide from {'LEFT' if from_left else 'RIGHT'}", LogLevel.DEBUG)
                
            except Exception as e:
                self.logger.warning(f"Option {i+1} creation failed: {e}")
                continue
        
        self.logger.section_end("Options Sequence")
        return clips

    def create_timer_animation(self, start_time, duration, y_position=1550):
        """
        Creates animated countdown timer with progress bar.
        
        Args:
            start_time: When timer starts
            duration: Countdown duration (e.g., 3.0 seconds)
            y_position: Vertical position of timer
            
        Returns:
            List of clips (progress bars + countdown numbers)
        """
        self.logger.section_start("Timer Animation")
        self.logger.data("Duration", f"{duration:.1f}s")
        self.logger.data("Position", f"Y={y_position}")
        
        clips = []
        
        bar_color = self._parse_color(self.theme.get('correct', '#22C55E'))
        
        # Progress bar segments (10 segments for smooth animation)
        segments = 10
        seg_width = WIDTH // segments
        
        for i in range(segments):
            # Each segment appears at its scheduled time and stays visible
            segment_appear_time = start_time + (duration * i / segments)
            segment_duration = duration - (duration * i / segments)  # FIXED: Stays until timer ends
            
            seg = ColorClip(
                size=(seg_width - res_scale(4), res_scale(50)),  # 4px gap between segments
                color=bar_color
            ).set_position((i * seg_width + 2, y_position))
            
            # Pulse effect on appearance
            def make_pulse(base_y, seg_index):
                def pulse_func(t):
                    if t < 0.15:  # Quick pulse at start
                        offset = -res_scale(10) * math.sin(t / 0.15 * math.pi)
                        return (seg_index * seg_width + 2, base_y + offset)
                    return (seg_index * seg_width + 2, base_y)
                return pulse_func
            
            seg = seg.set_position(make_pulse(y_position, i))
            seg = seg.set_start(segment_appear_time).set_duration(segment_duration)
            clips.append(seg)
        
        self.logger.log(f"Created {segments} progress segments", LogLevel.DEBUG)
        
        # Countdown numbers (3, 2, 1)
        countdown_y = y_position - res_scale(150)
        
        for i in range(int(duration)):
            number = int(duration) - i
            
            try:
                num_clip = TextClip(
                    str(number),
                    fontsize=res_scale(140),
                    color='white',
                    font=FONT_BOLD,
                    stroke_color='black',
                    stroke_width=res_scale(5)
                )
                
                # Pulsing scale animation
                def make_num_pulse(num_w, num_h):
                    def num_pulse_func(t):
                        # Scale: 1.0 → 1.2 → 1.0 over 1 second
                        progress = t % 1.0
                        if progress < 0.5:
                            scale = 1.0 + 0.2 * (progress / 0.5)
                        else:
                            scale = 1.2 - 0.2 * ((progress - 0.5) / 0.5)
                        
                        offset_x = (1 - scale) * num_w / 2
                        offset_y = (1 - scale) * num_h / 2
                        
                        return (WIDTH // 2 - num_w // 2 + offset_x, 
                               countdown_y + offset_y)
                    return num_pulse_func
                
                num_clip = num_clip.set_position(make_num_pulse(num_clip.w, num_clip.h))
                num_clip = num_clip.set_start(start_time + i).set_duration(1.0)
                
                clips.append(num_clip)
                
                self.logger.data(f"Number {number}", "Created", LogLevel.DEBUG)
                
            except Exception as e:
                self.logger.warning(f"Countdown number {number} failed: {e}")
                continue
        
        self.logger.section_end("Timer Animation")
        return clips  

    def create_answer_reveal_animation(self, correct_option_letter, options_data, 
                                  reveal_start_time , theme, total_remaining_time=None, confetti_y=None):
        """
        Creates dramatic answer reveal with shake, explosion, and confetti.
        
        Args:
            correct_option_letter: 'A', 'B', 'C', or 'D'
            options_data: Same format as create_options_sequence
            reveal_start_time: When answer reveals
            theme: Theme dictionary
            
        Returns:
            List of effect clips (shakes, confetti, flash)
        """
        self.logger.section_start("Answer Reveal Animation")
        self.logger.data("Correct Option", correct_option_letter)
        
        clips = []
        
        # Find correct option index
        # NEW: Get Y from options_data
        correct_idx = ord(correct_option_letter) - ord('A')
        if options_data and len(options_data) > correct_idx:
            correct_y = options_data[correct_idx].get('y_position', res_scale(1050))
        else:
            correct_y = res_scale(1050)

        # Confetti Y
        if confetti_y is None:
            confetti_y = correct_y  # Default to correct option position
        
        # Effect 1: Background flash (red -> green)
        #flash_duration = 0.5
        
        #correct_y = res_scale(1050) + (correct_idx * res_scale(130))  # Updated GAP

        # Green glow expansion around correct option
        glow_width = WIDTH - res_scale(100)
        glow_height = res_scale(100)

        def glow_scale(t):
            if t < 0.8:
                return 1.0 + 0.3 * (t / 0.5)  # Expand to 1.3x
            return 1.3

        green_glow = ColorClip(
            size=(glow_width, glow_height),
            color=self._parse_color(theme.get('correct'))
        )

        green_glow = green_glow.resize(glow_scale)
        green_glow = green_glow.set_opacity(0.15)
        green_glow = green_glow.set_position(('center', correct_y))
        #green_glow = green_glow.set_start(0).set_duration(40)
        green_glow = green_glow.set_start(reveal_start_time+0.05).set_duration(total_remaining_time-0.05)

        clips.insert(0, green_glow) 
        
        wrong_option_fades = []
        for i, opt_data in enumerate(options_data):
            opt_letter = chr(ord('A') + i)
            if opt_letter != correct_option_letter:
                # Create fade-to-transparent overlay for wrong options
                fade = ColorClip(
                    size=(WIDTH - res_scale(100), res_scale(100)),
                    color=(0, 0, 0)
                ).set_opacity(0.6)  # Darken wrong options
                
                wrong_y = opt_data.get('y_position', res_scale(1050))
                fade = fade.set_position(('center', wrong_y))
                fade = fade.set_start(reveal_start_time+0.05).set_duration(total_remaining_time-0.05)
                wrong_option_fades.append(fade)

        clips.extend(wrong_option_fades)

        self.logger.log("Background flash created", LogLevel.DEBUG)
        
        # Effect 2: Confetti burst
        confetti_colors = [
            (255, 215, 0),   # Gold
            (255, 105, 180), # Pink
            (0, 206, 209),   # Cyan
            (147, 51, 234),  # Purple
            (34, 197, 94)    # Green
        ]
        
        center_x = WIDTH // 2
        center_y = confetti_y
        
        for i in range(20):
            color = random.choice(confetti_colors)
            angle = (i / 20) * 2 * math.pi
            velocity = random.uniform(res_scale(150), res_scale(250))
            
            confetti = ColorClip(
                size=(res_scale(12), res_scale(12)),
                color=color
            ).set_opacity(0.8)
            
            def make_confetti_func(angle, velocity, center_x, center_y):
                def confetti_motion(t):
                    # Radial burst with gravity
                    x = center_x + (math.cos(angle) * velocity * t)
                    y = center_y + (math.sin(angle) * velocity * t) + (res_scale(200) * t * t)  # Gravity
                    return (x, y)
                return confetti_motion
            
            confetti = confetti.set_position(
                make_confetti_func(angle, velocity, center_x, center_y)
            ).set_start(reveal_start_time + 0.3).set_duration(1.2)
            
            # Fade out
            confetti = confetti.crossfadeout(0.4)
            clips.append(confetti)
    
        self.logger.log(f"Created 20 confetti particles", LogLevel.DEBUG)
        
        self.logger.section_end("Answer Reveal Animation")
        return clips 

    def _parse_color(self, color):
        """Parse color from hex or tuple to tuple"""
        if isinstance(color, str) and color.startswith('#'):
            hex_color = color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif isinstance(color, (tuple, list)):
            return tuple(color)
        else:
            return (255, 255, 255)  # Default white