import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, staticFile } from 'remotion';
import { VisualScenario } from '../types/schema';

interface WatermarkProps {
    scenario: VisualScenario;
}

export const Watermark: React.FC<WatermarkProps> = ({ scenario }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // --- 1. ASSET PATHS (LOCAL ONLY) ---
    const logoPath = staticFile('/assets/logo.png');
    const fontPath = staticFile('/assets/font.woff');
    const fontName = 'WatermarkFont';

    // --- 2. TIMING LOGIC ---
    // Detect start of Outro
    const outroStartTime = scenario.timeline.outro.start_time;
    const fadeStartFrame = outroStartTime * fps;
    const fadeDurationFrames = 0.5 * fps; // 0.5s duration

    const opacity = interpolate(
        frame,
        [fadeStartFrame, fadeStartFrame + fadeDurationFrames],
        [0.4, 0], // Fades from 0.4 to 0.0
        {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
        }
    );

    // If fully invisible, don't render to save layout calcs
    if (opacity === 0) return null;

    return (
        <>
            {/* Inject Local Font Face */}
            <style>
                {`
                    @font-face {
                        font-family: '${fontName}';
                        src: url('${fontPath}') format('woff');
                        font-weight: 800;
                        font-style: normal;
                    }
                `}
            </style>

            <div
                style={{
                    // Positioning
                    position: 'absolute',
                    top: '8%',
                    left: '5%',
                    zIndex: 100, // Layering Specification
                    
                    // Layout
                    display: 'flex',
                    flexDirection: 'row',
                    alignItems: 'center',
                    gap: '15px', // Space between logo and text

                    // Glassmorphism & Visuals
                    opacity: opacity,
                    backdropFilter: 'blur(10px)',
                    WebkitBackdropFilter: 'blur(10px)', // Safari support
                    
                    // Optional: subtle border/background to enhance glass effect
                    // background: 'rgba(255, 255, 255, 0.05)', 
                    // borderRadius: '12px',
                    // padding: '8px 16px',
                }}
            >
                {/* Logo */}
                <img 
                    src={logoPath} 
                    alt="Channel Logo"
                    style={{
                        height: '6vh', // Responsive to view height
                        width: 'auto',
                        objectFit: 'contain',
                    }} 
                />

                {/* Text "NCERT QuickPrep" */}
                <span
                    style={{
                        fontFamily: fontName,
                        color: 'white',
                        fontWeight: 800,
                        fontSize: '3vh', // Responsive to view height
                        letterSpacing: '0.05em',
                        textShadow: '0 2px 4px rgba(0,0,0,0.5)' // Increases legibility
                    }}
                >
                    NCERT QuickPrep
                </span>
            </div>
        </>
    );
};