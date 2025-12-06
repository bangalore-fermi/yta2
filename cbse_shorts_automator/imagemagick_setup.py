#!/usr/bin/env python3
"""
File: imagemagick_setup.py
ImageMagick configuration for MoviePy
This MUST be imported before any MoviePy imports
"""

import os
import sys
import shutil

def setup_imagemagick():
    """Setup ImageMagick binary for MoviePy"""
    
    # Find ImageMagick binary
    im_binary = shutil.which("convert")
    if not im_binary:
        if os.path.exists("/usr/bin/convert"):
            im_binary = "/usr/bin/convert"
        elif os.path.exists("/usr/local/bin/convert"):
            im_binary = "/usr/local/bin/convert"
    
    if not im_binary:
        print("❌ CRITICAL: ImageMagick not found.")
        print("   Please install: sudo apt-get install imagemagick")
        sys.exit(1)
    
    # Set environment variable
    os.environ['IMAGEMAGICK_BINARY'] = im_binary
    
    # Configure MoviePy
    import moviepy.config as mp_conf
    import moviepy.tools as mp_tools
    mp_conf.IMAGEMAGICK_BINARY = im_binary
    
    # Patch subprocess_call to handle None values
    original_subprocess_call = mp_tools.subprocess_call
    
    def patched_subprocess_call(cmd, logger=None):
        if cmd:
            fixed_cmd = []
            prev_item = None
            for item in cmd:
                if item is None:
                    if prev_item == '-background':
                        fixed_cmd.append('transparent')
                    else:
                        fixed_cmd.append(im_binary)
                else:
                    fixed_cmd.append(item)
                prev_item = item if item is not None else prev_item
            cmd = fixed_cmd
        return original_subprocess_call(cmd, logger)
    
    mp_tools.subprocess_call = patched_subprocess_call
    
    return im_binary

# Auto-setup when imported
IM_BINARY = setup_imagemagick()