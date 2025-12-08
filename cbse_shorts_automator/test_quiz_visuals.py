#!/usr/bin/env python3
"""
File: test_quiz_visuals.py
Purpose: Multi-mode test harness for quiz visual effects.
Supports rapid iteration with configurable quality/speed tradeoffs.
"""

import os
import sys
import argparse
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip
from visual_effects_quiz import QuizVisualEffects
from debug_logger import create_logger, LogLevel
# Add to imports:
from visual_effects_quiz import QuizVisualEffects, res_scale, set_resolution

# ============================================================================
# CONFIGURATION PRESETS
# ============================================================================

class TestMode:
    """Predefined test modes for different scenarios"""
    
    VISUAL_DEV = {
        'name': 'Visual Development',
        'include_audio': False,
        'resolution': (540, 960),
        'segment_duration': 30,
        'fps': 10,
        'use_mock_timings': True,
        'particle_count': 10,
        'render_preset': 'ultrafast',
        'pip_height' : 225,
        'show_timing_markers': False
    }
    
    SYNC_TEST = {
        'name': 'Audio Sync Testing',
        'include_audio': True,
        'resolution': (720, 1280),
        'segment_duration': 15,
        'fps': 24,
        'use_mock_timings': False,
        'particle_count': 20,
        'render_preset': 'fast',
        'pip_height' : 225,
        'show_timing_markers': True
    }
    
    PRODUCTION_PREVIEW = {
        'name': 'Production Preview',
        'include_audio': True,
        'resolution': (1080, 1920),
        'segment_duration': 30,
        'fps': 15,
        'use_mock_timings': False,
        'particle_count': 30,
        'render_preset': 'medium',
        'pip_height' : 225,
        'show_timing_markers': False
    }
    
    PRODUCTION = {
        'name': 'Full Production',
        'include_audio': True,
        'resolution': (1080, 1920),
        'segment_duration': None,
        'fps': 24,
        'use_mock_timings': False,
        'particle_count': 30,
        'render_preset': 'slow',
        'pip_height' : 225,
        'show_timing_markers': False
    }


# ============================================================================
# MOCK DATA (For audio-less testing)
# ============================================================================

MOCK_TIMINGS = {
    'hook': {'start': 0, 'duration': 2.0},
    'question': {'start': 2.0, 'duration': 3.5},
    'opt_a': {'start': 5.5, 'duration': 1.5},
    'opt_b': {'start': 7.0, 'duration': 1.5},
    'opt_c': {'start': 8.5, 'duration': 1.5},
    'opt_d': {'start': 10.0, 'duration': 1.5},
    'think': {'start': 11.5, 'duration': 3.0},
    'explanation': {'start': 14.5, 'duration': 4.5},
    'cta': {'start': 19.0, 'duration': 2.5}
}

# Showcase of Source footage: One of the purposes of these shorts is to showcase  the original source video to coerce the viewers to watch the full video. So, throughout the duration  of the shorts, in any part  of the screen, the source video must be displayed without loss of aspect ratio and without any masking or blurring.
MOCK_SCRIPT = {
    'question_visual': 'What is H₂O?',
    'opt_a_visual': 'Water',
    'opt_b_visual': 'Oxygen',
    'opt_c_visual': 'Hydrogen',
    'opt_d_visual': 'Carbon Dioxide'
}

# All available themes
ALL_THEMES = {
    'energetic_yellow': {
        'bg_color': (15, 23, 42), 'highlight': '#FACC15', 'correct': '#22C55E', 
        'name': 'Energetic Yellow', 'music_mood': 'energetic'
    },
    'calm_blue': {
        'bg_color': (13, 27, 42), 'highlight': '#38BDF8', 'correct': '#34D399', 
        'name': 'Calm Blue', 'music_mood': 'calm'
    },
    'vibrant_purple': {
        'bg_color': (24, 7, 45), 'highlight': '#E879F9', 'correct': '#A78BFA', 
        'name': 'Vibrant Purple', 'music_mood': 'funky'
    },
    'fresh_green': {
        'bg_color': (7, 36, 19), 'highlight': '#84CC16', 'correct': '#4ADE80', 
        'name': 'Fresh Green', 'music_mood': 'calm'
    },
    'classic_red': {
        'bg_color': (28, 25, 23), 'highlight': '#FB923C', 'correct': '#F87171', 
        'name': 'Classic Red', 'music_mood': 'energetic'
    }
}

# Use energetic_yellow as default mock
MOCK_THEME = ALL_THEMES['energetic_yellow']


# ============================================================================
# MAIN TEST FUNCTIONS
# ============================================================================

def test_backdrop(config, logger, theme_str):
    """Test particle backdrop animation"""
    logger.section_start("Testing Backdrop")
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1],config['fps'])
    
    theme=ALL_THEMES[theme_str]
    duration = config.get('segment_duration', 5)
    
    vfx = QuizVisualEffects(
        theme=theme,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    
    output_path = 'shorts/TEST_BACKDROP.mp4'
    os.makedirs('shorts', exist_ok=True)
    
    logger.log(f"Rendering to {output_path}")
    backdrop.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Backdrop")
    return output_path


def test_pip(config, logger, video_path):
    """Test PIP source video positioning"""
    logger.section_start("Testing PIP")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1],config['fps'])
    
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return None
    
    theme=ALL_THEMES[config.get('theme', 'energetic_yellow')]
    duration = config.get('segment_duration', 5)
    
    # Load source video
    logger.log("Loading source video")
    source_vid = VideoFileClip(video_path)
    
    # Resize to fit screen (will be cropped in PIP function)
    if source_vid.h > 1920:
        source_vid = source_vid.resize(height=1920)
    
    vfx = QuizVisualEffects(
        theme=theme,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    # Create backdrop
    backdrop = vfx.create_particle_backdrop(duration)
    
    # Create PIP
    pip = vfx.create_pip_source_video(source_vid.subclip(0, min(duration, source_vid.duration)), duration)
    
    # Composite
    final = CompositeVideoClip([backdrop, pip], size=config['resolution'])
    
    output_path = 'shorts/TEST_PIP.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    # Cleanup
    source_vid.close()
    
    logger.section_end("Testing PIP")
    return output_path


def test_typewriter(config, logger, theme_str):
    """Test typewriter text animation"""
    logger.section_start("Testing TypeWriter Effect")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1],config['fps'])
    
    theme=ALL_THEMES[theme_str]
    duration = 8
    question_text = "What is the chemical formula for water?"
    question_audio_duration = 3.5  # Mock audio length
    
    vfx = QuizVisualEffects(
        theme=theme,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    
    typewriter = vfx.create_typewriter_text(
        text=question_text,
        audio_duration=question_audio_duration,
        start_time=1.0,
        fontsize=55,
        color=theme['highlight'],
        y_offset=900
    )
    
    if typewriter:
        final = CompositeVideoClip([backdrop, typewriter], size=config['resolution'])
    else:
        logger.warning("TypeWriter returned None")
        final = backdrop
    
    output_path = 'shorts/TEST_TYPEWRITER.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing TypeWriter Effect")
    return output_path


def test_options(config, logger):
    """Test options slide-in animation"""
    logger.section_start("Testing Options Sequence")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1],config['fps'])
    
    duration = 12
    
    options_data = [
        {'text': 'A) Water', 'start_time': 2.0, 'duration': 10.0, 'is_correct': True},
        {'text': 'B) Oxygen', 'start_time': 2.3, 'duration': 9.7, 'is_correct': False},
        {'text': 'C) Hydrogen', 'start_time': 2.6, 'duration': 9.4, 'is_correct': False},
        {'text': 'D) Carbon Dioxide', 'start_time': 2.9, 'duration': 9.1, 'is_correct': False}
    ]
    
    vfx = QuizVisualEffects(
        theme=MOCK_THEME,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    options_clips = vfx.create_options_sequence(options_data, MOCK_THEME)
    
    all_clips = [backdrop] + options_clips
    final = CompositeVideoClip(all_clips, size=config['resolution'])
    
    output_path = 'shorts/TEST_OPTIONS.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Options Sequence")
    return output_path


def test_timer(config, logger):
    """Test timer animation"""
    logger.section_start("Testing Timer Animation")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1], config['fps'])
    
    duration = 6
    
    vfx = QuizVisualEffects(
        theme=MOCK_THEME,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    timer_clips = vfx.create_timer_animation(
        start_time=1.0,
        duration=3.0,
        y_position=1550
    )
    
    all_clips = [backdrop] + timer_clips
    final = CompositeVideoClip(all_clips, size=config['resolution'])
    
    output_path = 'shorts/TEST_TIMER.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Timer Animation")
    return output_path


def test_cta_banner(config, logger):
    """Test split-display CTA banner"""
    logger.section_start("Testing Split CTA Banner")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1])
    
    duration = 10
    
    vfx = QuizVisualEffects(
        theme=MOCK_THEME,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    
    # Split CTA: Social action → Link directive
    cta = vfx.create_cta_banner(
        social_text="🔔 SUBSCRIBE FOR MORE!",
        link_text="📎 Full Video in Description",
        social_start=1.0,
        social_duration=4.0,
        link_start=5.0,
        link_duration=4.0,
        style='full-banner'
    )
    
    if cta:
        final = CompositeVideoClip([backdrop, cta], size=config['resolution'])
    else:
        logger.warning("CTA creation returned None")
        final = backdrop
    
    output_path = 'shorts/TEST_CTA_SPLIT.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Split CTA Banner")
    return output_path

def test_outro(config, logger, theme_str):
    """Test outro animation and styling"""
    logger.section_start("Testing Outro")
    
    theme = ALL_THEMES[theme_str]
    
    # Set resolution for this test
    from visual_effects_quiz import set_resolution
    set_resolution(config['resolution'][0], config['resolution'][1], config['fps'])
    
    # Import shorts engine
    from shorts_engine import ShortsEngine
    
    engine = ShortsEngine()
    
    # Create outro with test theme
    outro_duration = 4.0
    
    outro = engine.create_outro_v2(
        duration=outro_duration,
        theme=theme,
        usp_message=None,  # Random message
        cta_text="SUBSCRIBE FOR MORE!"
    )
    
    # Create simple backdrop for context
    from visual_effects_quiz import QuizVisualEffects
    vfx = QuizVisualEffects(
        theme=theme,
        config=config,
        timing_data=None,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(outro_duration)
    
    # Composite backdrop + outro
    final = CompositeVideoClip([backdrop, outro], size=config['resolution'])
    
    output_path = f'shorts/TEST_OUTRO_{theme_str.upper()}.mp4'
    os.makedirs('shorts', exist_ok=True)
    
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Outro")
    return output_path

def test_timing_markers(config, logger):
    """Test timing marker visualization"""
    logger.section_start("Testing Timing Markers")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1])
    
    duration = sum(t['duration'] for t in MOCK_TIMINGS.values())
    
    vfx = QuizVisualEffects(
        theme=MOCK_THEME,
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    backdrop = vfx.create_particle_backdrop(duration)
    markers = vfx.create_timing_markers(MOCK_TIMINGS, duration)
    
    if markers:
        final = CompositeVideoClip([backdrop, markers], size=config['resolution'])
    else:
        final = backdrop
    
    output_path = 'shorts/TEST_TIMING_MARKERS.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    logger.section_end("Testing Timing Markers")
    return output_path


def test_full_base(config, logger, video_path, theme_str):
    """Test complete base layer (backdrop + PIP + markers)"""
    logger.section_start("Testing Full Base Layer")
    
    # Set resolution for this test
    set_resolution(config['resolution'][0], config['resolution'][1])
    
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return None
    
    duration = config.get('segment_duration', 15)
    
    # Load source video
    source_vid = VideoFileClip(video_path)
    if source_vid.h > 1920:
        source_vid = source_vid.resize(height=1920)
    
    vfx = QuizVisualEffects(
        theme=ALL_THEMES[theme_str],
        config=config,
        timing_data=MOCK_TIMINGS,
        logger=logger
    )
    
    clips = []
    
    # Layer 1: Backdrop
    logger.log("Creating backdrop")
    backdrop = vfx.create_particle_backdrop(duration)
    clips.append(backdrop)
    
    # Layer 2: PIP
    logger.log("Creating PIP")
    pip = vfx.create_pip_source_video(source_vid.subclip(0, min(duration, source_vid.duration)), duration)
    clips.append(pip)
    
    # Layer 3: Markers (optional)
    if config.get('show_timing_markers', False):
        logger.log("Creating timing markers")
        markers = vfx.create_timing_markers(MOCK_TIMINGS, duration)
        if markers:
            clips.append(markers)
    
    final = CompositeVideoClip(clips, size=config['resolution'])
    
    output_path = 'shorts/TEST_FULL_BASE.mp4'
    logger.log(f"Rendering to {output_path}")
    final.write_videofile(
        output_path,
        fps=config['fps'],
        codec='libx264',
        preset=config['render_preset'],
        audio=False,
        logger=None if logger.level == LogLevel.SILENT else 'bar'
    )
    
    # Cleanup
    source_vid.close()
    
    logger.section_end("Testing Full Base Layer")
    return output_path


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Test Quiz Visual Effects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fast visual iteration (no audio)
  python test_quiz_visuals.py --mode visual-dev --segment backdrop
  
  # Test sync with timing markers
  python test_quiz_visuals.py --mode sync-test --segment full --video temp/test_source.mp4
  
  # Production preview
  python test_quiz_visuals.py --mode production-preview --segment full --video temp/test_source.mp4 --log-level minimal
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['visual-dev', 'sync-test', 'production-preview', 'production'],
        default='visual-dev',
        help='Test mode preset'
    )

    parser.add_argument(
        '--segment',
        choices=['backdrop', 'pip', 'markers', 'cta', 'typewriter', 'options', 'timer', 'outro', 'full'],
        default='backdrop',
        help='Which segment to test'
    )
    
    parser.add_argument(
        '--video',
        default='temp/test_source.mp4',
        help='Path to source video file'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['silent', 'minimal', 'normal', 'debug', 'verbose'],
        default='normal',
        help='Logging verbosity'
    )
    
    parser.add_argument(
        '--particle-count',
        type=int,
        help='Override particle count (default varies by mode)'
    )
    
    parser.add_argument(
        '--theme',
        choices=list(ALL_THEMES.keys()),
        default='energetic_yellow',
        help='Visual theme to test'
    )
    
    parser.add_argument(
        '--cta-style',
        choices=['full-banner', 'corner-badge'],
        default='full-banner',
        help='CTA visual style'
    )
    
    parser.add_argument(
        '--no-markers',
        action='store_true',
        help='Disable timing markers even in sync-test mode'
    )
    
    parser.add_argument(
        '--pip-height',
        type=int,
        default=400,
        help='PIP height in pixels (width auto-calculated for 16:9)'
    )

    args = parser.parse_args()
    
    # Load mode preset
    mode_map = {
        'visual-dev': TestMode.VISUAL_DEV,
        'sync-test': TestMode.SYNC_TEST,
        'production-preview': TestMode.PRODUCTION_PREVIEW,
        'production': TestMode.PRODUCTION
    }
    
    config = mode_map[args.mode].copy()
    
    # Apply overrides
    if args.particle_count:
        config['particle_count'] = args.particle_count
    
    if args.no_markers:
        config['show_timing_markers'] = False
    
    if args.cta_style:
        config['cta_style'] = args.cta_style

    if args.segment in ['pip', 'full']:
        config['pip_size'] = (int(args.pip_height * 16 / 9), args.pip_height)
    # Select theme
    selected_theme = ALL_THEMES[args.theme]
    
    # Create logger
    logger = create_logger(args.log_level)
    
    # Print configuration
    logger.summary("Test Configuration", {
        "Mode": config['name'],
        "Theme": selected_theme['name'],
        "Segment": args.segment.upper(),
        "Resolution": f"{config['resolution'][0]}x{config['resolution'][1]}",
        "FPS": config['fps'],
        "Particles": config['particle_count'],
        "Audio": "Yes" if config['include_audio'] else "No",
        "Markers": "Yes" if config['show_timing_markers'] else "No",
        "Render Preset": config['render_preset']
    })
    
    # Run test
    try:
        if args.segment == 'backdrop':
            output = test_backdrop(config, logger, args.theme)
        elif args.segment == 'pip':
            set_resolution(config['resolution'][0], config['resolution'][1])
            PIP_HEIGHT = res_scale(225)  # Will scale based on resolution
            config['pip_size'] = (int(PIP_HEIGHT * 16 / 9), PIP_HEIGHT)
            output = test_pip(config, logger, args.video)
        elif args.segment == 'markers':
            output = test_timing_markers(config, logger)
        elif args.segment == 'cta':
            output = test_cta_banner(config, logger)
        elif args.segment == 'typewriter':
            output = test_typewriter(config, logger, args.theme)
        elif args.segment == 'options':
            output = test_options(config, logger)
        elif args.segment == 'timer':
            output = test_timer(config, logger)
        elif args.segment == 'outro':
            output = test_outro(config, logger, args.theme)
        elif args.segment == 'full':
            set_resolution(config['resolution'][0], config['resolution'][1])
            PIP_HEIGHT = res_scale(495)  # Will scale based on resolution
            config['pip_size'] = (int(PIP_HEIGHT * 16 / 9), PIP_HEIGHT)
            output = test_full_base(config, logger, args.video, args.theme)
        else:
            logger.error(f"Unknown segment: {args.segment}")
            return 1
        
        if output:
            logger.summary("Test Complete", {
                "Output": output,
                "Status": "SUCCESS ✅"
            })
            return 0
        else:
            logger.error("Test failed")
            return 1
            
    except Exception as e:
        logger.error(f"Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())