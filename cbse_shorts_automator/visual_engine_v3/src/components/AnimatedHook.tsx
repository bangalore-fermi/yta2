import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { useThree } from '@react-three/fiber';
import { NanoText } from './Typography';

interface AnimatedHookProps {
    text: string;
    seed: number;
    theme: { primary: string; [key: string]: any };
    fontSize: number; // This is now your "Target" size (max size)
    fontUrl?: string;
    maxAvailableWidth: number;
}

export const AnimatedHook: React.FC<AnimatedHookProps> = ({
    text,
    seed,
    theme,
    fontSize,
    fontUrl,
    maxAvailableWidth
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const { viewport } = useThree(); 

    // --- NEW: DYNAMIC FONT SCALING ---
    const finalFontSize = useMemo(() => {
        // 1. Define the safe zone (90% of screen width)
        //const maxAvailableWidth = viewport.width * 0.9;
        
        // 2. Estimate current text width
        // Heuristic: Average character width is roughly 0.6x the font size for standard fonts.
        // We add a small buffer (text.length * 0.6)
        const estimatedWidthAtTargetSize = text.length * (fontSize * 0.5);

        // 3. If estimated width exceeds limit, scale down. Otherwise, keep target fontSize.
        if (estimatedWidthAtTargetSize > maxAvailableWidth) {
            // Formula: NewSize = (TargetWidth / CharacterCount) / AspectRatioFactor
            return maxAvailableWidth / (text.length * 0.5);
        }
        
        return fontSize;
    }, [viewport.width, text, fontSize]);


    // --- ANIMATION LOGIC (UNCHANGED) ---
    const variant = seed % 3;

    const driver = spring({
        frame,
        fps,
        config: variant === 0 
            ? { mass: 1, stiffness: 200, damping: 10 } 
            : { mass: 1, stiffness: 170, damping: 26 }
    });

    const transforms = useMemo(() => {
        const t = {
            scale: [1, 1, 1] as [number, number, number],
            position: [0, 0, 1] as [number, number, number],
            rotation: [0, 0, 0] as [number, number, number],
        };

        switch (variant) {
            case 0: // Elastic Pop
                const s = interpolate(driver, [0, 1], [0, 1]);
                t.scale = [s, s, 1];
                break;

            case 1: // SlideX
                // Use viewport width to ensure it starts off-screen regardless of device size
                const startX = -(viewport.width / 2) - 2; 
                const xPos = interpolate(driver, [0, 1], [startX, 0]);
                t.position = [xPos, 0, 1];
                break;

            case 2: // Vortex
                const rotZ = interpolate(driver, [0, 1], [-Math.PI, 0]);
                const scaleV = interpolate(driver, [0, 1], [0, 1]);
                t.rotation = [0, 0, rotZ];
                t.scale = [scaleV, scaleV, 1];
                break;
        }

        return t;
    }, [variant, driver, viewport.width]);

    return (
        <group 
            position={transforms.position} 
            rotation={transforms.rotation} 
            scale={transforms.scale}
        >
            <NanoText 
                text={text}
                position={[0, 0, 0]} 
                // USE THE DYNAMIC SIZE HERE
                fontSize={finalFontSize}
                color={theme.primary}
                fontUrl={fontUrl}
                anchorX="center"
                anchorY="middle"
                maxWidth={viewport.width*0.8}
            />
        </group>
    );
};