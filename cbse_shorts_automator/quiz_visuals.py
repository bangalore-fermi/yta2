"""
File: quiz_visuals.py
Handles the visual composition for the Quiz Template.
Currently implements the Standard Static Layout (Legacy).
UPDATED: Added 'test_render_limit' provision for rapid testing.
"""

from moviepy.editor import TextClip, ColorClip, vfx

WIDTH = 1080
HEIGHT = 1920

def force_rgb(clip):
    """Helper to ensure clips are in RGB mode to prevent rendering errors."""
    try:
        if hasattr(clip, 'img') and clip.img is not None and clip.img.ndim == 2:
            return clip.fx(vfx.to_RGB)
    except: pass
    return clip

def filter_and_trim_clips(clips, limit):
    """
    Helper to enforce the render limit on a list of clips.
    Drops clips that start after the limit.
    Trims clips that extend past the limit.
    """
    if not limit or limit <= 0:
        return clips
        
    valid_clips = []
    for clip in clips:
        # Safety check for missing start attribute
        if not hasattr(clip, 'start') or clip.start is None:
            clip.start = 0
            
        # 1. Drop if starts after limit
        if clip.start >= limit:
            continue
            
        # 2. Trim if ends after limit
        # Note: clip.duration might be None for some infinite clips, handle gracefully
        current_dur = clip.duration if clip.duration else (limit - clip.start)
        
        if clip.start + current_dur > limit:
            new_dur = limit - clip.start
            # set_duration works for both TextClip (static) and VideoFileClip (cuts tail)
            clip = clip.set_duration(new_dur)
            
        valid_clips.append(clip)
    
    return valid_clips

def build_quiz_visuals(engine, video_proc, video_path, script, timings, total_dur, config):
    """
    Constructs the visual layers for the quiz.
    Returns a list of MoviePy clips ready for CompositeVideoClip.
    """
    
    # 0. Check for Test Render Limit
    render_limit = config.get('test_render_limit')
    if render_limit and isinstance(render_limit, (int, float)) and render_limit > 0:
        print(f"    ✂️ TEST MODE (Visuals): limiting duration to {render_limit}s")
        # We limit the background generation to this limit immediately
        total_dur = min(total_dur, render_limit)
    
    # 1. Prepare Background & Source Video
    print(f"    🧠 AI Watching video to find relevant clips ({int(total_dur)}s)...")
    src_vid = video_proc.prepare_video_for_short(video_path, total_dur, script=script, width=WIDTH)
    src_vid = src_vid.set_position(('center', 0))
    
    bg = engine.create_background(config.get('theme'), total_dur, video_clip=src_vid)
    clips = [bg, src_vid]

    # 2. Get Theme Data
    theme = engine.get_theme(config.get('theme', 'energetic_yellow'))
    
    # 3. Text Overlays Logic (Legacy Layout)
    CARD_START_Y = 750 
    
    # A. Hook (Watch Till End)
    hook_box = theme['highlight']
    hook_txt = engine.get_contrast_color(hook_box)
    
    hook_clip = TextClip("🔥 WATCH TILL END 🔥", fontsize=45, color=hook_txt, bg_color=hook_box, font='Arial-Bold', method='label', size=(WIDTH, 110))
    hook_clip = hook_clip.set_position(('center', CARD_START_Y)).set_start(0).set_duration(2)
    clips.append(force_rgb(hook_clip))
    
    # B. Question
    QUESTION_Y = CARD_START_Y + 130 
    q_clip = engine.create_text_clip(script['question_visual'], fontsize=55, color=theme['highlight'], bold=True, wrap_width=25, align='North', stroke_color='black', stroke_width=2)
    q_clip = q_clip.set_position(('center', QUESTION_Y)).set_start(timings['t_q']).set_duration(total_dur - timings['t_q'])
    clips.append(force_rgb(q_clip))
    
    # C. Options
    OPT_START_Y = QUESTION_Y + 350
    GAP = 110
    opt_bg = theme['bg_color']
    
    if isinstance(opt_bg, str):
         if opt_bg.startswith('#'):
            opt_bg = opt_bg.lstrip('#')
            opt_bg = tuple(int(opt_bg[i:i+2], 16) for i in (0, 2, 4))
    
    options = [
        (f"A) {script['opt_a_visual']}", timings['t_a']), 
        (f"B) {script['opt_b_visual']}", timings['t_b']), 
        (f"C) {script['opt_c_visual']}", timings['t_c']), 
        (f"D) {script['opt_d_visual']}", timings['t_d'])
    ]
    
    for i, (txt, t) in enumerate(options):
        o_clip = engine.create_text_clip(txt, fontsize=45, color='white', bg_color=opt_bg, wrap_width=30, align='West')
        o_clip = o_clip.set_position(('center', OPT_START_Y + GAP * i)).set_start(t).set_duration(total_dur - t)
        clips.append(force_rgb(o_clip))

    # D. Timer (Segments + Big Number)
    THINK_TIME = 3.0
    timer_base_y = OPT_START_Y + GAP * 4 + 30
    timer_bar_y = timer_base_y + 160
    bar_color = theme['correct']
    if isinstance(bar_color, str) and bar_color.startswith('#'):
         bar_color = tuple(int(bar_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
         
    segments = 10
    seg_w = WIDTH // segments
    for i in range(segments):
        seg = ColorClip(size=(seg_w - 2, 40), color=bar_color).set_position((i * seg_w, timer_bar_y))
        dt = timings['t_think'] + (THINK_TIME * (i + 1) / segments)
        seg = seg.set_start(timings['t_think']).set_end(dt)
        clips.append(seg) 

    for i in range(int(THINK_TIME)):
        num = int(THINK_TIME) - i
        n_clip = TextClip(str(num), fontsize=140, color='white', font='Arial-Bold', stroke_color='black', stroke_width=5)
        n_clip = n_clip.set_position(('center', timer_base_y)).set_start(timings['t_think'] + i).set_duration(1)
        clips.append(force_rgb(n_clip))
    
    # E. Answer Reveal
    ans_bg = theme['correct']
    ans_txt = engine.get_contrast_color(ans_bg)
    
    stroke_col = 'black' if ans_txt == 'white' else None
    stroke_wid = 3 if ans_txt == 'white' else 0

    visual_content = script.get('explanation_visual', script.get('explanation_spoken', ''))
    visual_display = f"✅ {script['correct_opt']}: {visual_content}"
    
    summary_clip = engine.create_text_clip(
        visual_display, 
        fontsize=50, 
        color=ans_txt, 
        bg_color=ans_bg, 
        stroke_color=stroke_col,
        stroke_width=stroke_wid,
        bold=True, 
        wrap_width=25, 
        align='center'
    )
    
    # Use aud_expl duration passed in timings if available, else calculate
    summary_clip = summary_clip.set_position(('center', OPT_START_Y)).set_start(timings['t_ans']).set_duration(timings['expl_duration'])
    clips.append(force_rgb(summary_clip))

    # F. CTA
    cta_bg = theme['highlight']
    cta_txt_color = 'black'
    cta_display = f"🚀 {script['cta_spoken']}"
    
    clips.append(engine.create_text_clip(
        cta_display, 
        fontsize=65, 
        color=cta_txt_color, 
        bg_color=cta_bg, 
        bold=True, 
        wrap_width=20
    ).set_position(('center', HEIGHT - 350)).set_start(timings['t_cta']).set_duration(timings['cta_duration']))

    # G. Outro
    outro = engine.create_outro(
        duration=4.0, 
        cta_text="SUBSCRIBE FOR MORE!"
    ).set_start(timings['t_outro'])
    clips.append(outro)
    
    # 4. FILTER & TRIM (Provision for Render Limit)
    final_clips = filter_and_trim_clips(clips, render_limit)
    
    return final_clips