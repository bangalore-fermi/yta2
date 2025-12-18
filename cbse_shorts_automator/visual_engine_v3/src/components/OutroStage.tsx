import React, { useRef } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, staticFile } from 'remotion';
import { useFrame, useThree } from '@react-three/fiber';
import { useTexture } from '@react-three/drei';
import * as THREE from 'three';
import { NanoText } from './Typography'; 
import { VisualScenario } from '../types/schema';

interface OutroStageProps {
    scenario: VisualScenario;
    fps: number;
    t_outro_start: number;
}

//const DESIGN_WIDTH = 1920; 

export const OutroStage: React.FC<OutroStageProps> = ({ scenario, fps, t_outro_start }) => {
    const frame = useCurrentFrame();
    const { width } = useVideoConfig(); 
    const { timeline, assets } = scenario;
    const { viewport } = useThree();

    const planeScaleFactor=0.25*.6
    const LogoScaleFactor=0.4

    // Calculate the scale factor based on viewport/design
    const globalScaleFactor = width / scenario.meta.resolution.w *planeScaleFactor;
    // Define the final target scale, including the original factor
    const finalScaleX = globalScaleFactor * 1; 
    const finalScaleY = globalScaleFactor * 1;
    const finalScaleZ = globalScaleFactor * 0.1;
    
    const OutroShowSTartTime=t_outro_start;

    // --- NEW: SCALE-IN ANIMATION LOGIC ---
    const scaleInDuration = 2; 
    const scaleInStartFrame = (OutroShowSTartTime) * fps;
    const scaleInEndTime = (OutroShowSTartTime + scaleInDuration);

    const scaleSpring = spring({
        frame: frame - scaleInStartFrame, // Start spring animation at t_outro_start
        fps,
        // Calculate the number of frames for 0.5 seconds
        durationInFrames: scaleInDuration * fps, 
        // Use a configuration that gives a nice 'slam' or 'bounce' effect
        config: { mass: 1, stiffness: 100, damping: 100 },
        from: 0,
        to: 1
    });

    // Interpolate the spring value (0 to 1) to the actual scale value (0.01 to finalScale)
    const scaleInValue = interpolate(
        scaleSpring, 
        [0, 1], 
        [0.001, 1] // Start from 0.01 (tiny) and go to 1 (full calculated size)
    );
    // ------------------------------------

    // --- PRELOAD TEXTURE ---
    const textureUrl = staticFile(assets.channel_logo_url || assets.thumbnail_url);
    const logoTexture = useTexture(textureUrl);
    
    const showOutro = frame >= (scaleInEndTime) * fps;
    const logoRef = useRef<THREE.Group>(null!);

    // --- ANIMATION 1: CONTINUOUS LOGO ROTATION (TIMELINE BOUND) ---
    useFrame(() => {
        if (logoRef.current && showOutro) {
            const rotationStartFrame = (OutroShowSTartTime + 0.1) * fps;
            const timeDelta = Math.max(0, frame - rotationStartFrame);
            logoRef.current.rotation.y = timeDelta * 0.05; 
        }
    });

    // --- ANIMATION 2: TEXT SLAM PHYSICS (t_outro_start + delay) ---
    const slamAnimation = (delay: number) => {
        const startFrame = (scaleInEndTime + delay) * fps;
        const spr = spring({
            frame: frame - startFrame,
            fps,
            config: { mass: 2, stiffness: 200, damping: 20 },
            from: 0,
            to: 1
        });
        
        return {
            scale: interpolate(spr, [0, 1], [1.5, 1]),
            yOffset: interpolate(spr, [0, 1], [2, 0]),
            visible: frame >= startFrame
        };
    };

    const usp1 = slamAnimation(1); // Starts 1.0s after outro starts
    const usp2 = slamAnimation(2); // Starts 2.0s after outro starts

    if (frame < (OutroShowSTartTime - 1) * fps) return null;

    const line1Text = timeline.outro?.line_1 || "SUBSCRIBE";
    const line2Text = timeline.outro?.line_2 || "FOR MORE";

    return (
        <group 
            position={[0, 0, 1.5]} 
            // Apply both the global scale factor AND the dynamic scale-in value
            scale={[
                finalScaleX * scaleInValue, 
                finalScaleY * scaleInValue, 
                finalScaleZ * scaleInValue
            ]}
        >
            
            {/* Soft Ceramic Lighting */}
            <pointLight position={[-2, 4, 4]} intensity={5.0} distance={10} decay={.20} />
            <pointLight position={[2, 4, 4]} intensity={5.0} distance={10} decay={.20} />

            {/* 1. ROTATING CERAMIC BADGE LOGO */}
            {frame >= (OutroShowSTartTime + 0.0) * fps && (
                <group ref={logoRef} position={[0, 1/(LogoScaleFactor/2), 1]} scale={[1/LogoScaleFactor,1/LogoScaleFactor,.1]}>
                    <mesh>
                        {/* Volumetric Badge */}
                        <boxGeometry args={[2.5, 2.5, 0.08]} />
                        
                        {/* --- CARDBOARD MATERIAL --- */}
                        <meshStandardMaterial 
                            map={logoTexture}
                            transparent={false}
                            side={THREE.DoubleSide} 
                            // Cardboard is non-metallic
                            metalness={0.05} 
                            // Cardboard is rough and matte
                            roughness={0.8} 
                            // Set a base light brown color to simulate the cardboard stock
                            color={new THREE.Color("#A08060")} 
                            
                            // Reduce emissive properties for a duller, non-ceramic look
                            emissive={new THREE.Color("#A08060")}
                            emissiveIntensity={0.00} // Very subtle glow
                            emissiveMap={logoTexture} 
                            envMapIntensity={0.5} // Lower environment map reflection
                            alphaTest={0.5}   
                        />
                    </mesh>
                </group>
            )}
            {/* 4. Z-PLANE SEPARATOR (White Rectangle) */}
            {frame >= (OutroShowSTartTime + 0.0) * fps && (
                <mesh position={[0, 0, -1]}>
                {/* 10 units wide/tall should ensure it covers the visible area */}
                <boxGeometry args={[viewport.width/planeScaleFactor, viewport.height/planeScaleFactor, 0.01]} /> 
                <meshBasicMaterial color={"white"} />
            </mesh>
            )}

            {/* 2. USP TEXT LINE 1 */}
            {usp1.visible && (
                <NanoText
                    text={line1Text}
                    position={[0, -1 + usp1.yOffset, 0.5]}
                    fontSize={1}
                    color="black"
                    anchorX="center"
                    anchorY="middle"
                    fontUrl={assets.font_url} 
                />
            )}

            {/* 3. USP TEXT LINE 2 */}
            {usp2.visible && (
                <NanoText
                    text={line2Text}
                    position={[0, -2.5 + usp2.yOffset, 0.5]}
                    fontSize={0.7}
                    color="#333333" 
                    anchorX="center"
                    anchorY="middle"
                    fontUrl={assets.font_url}
                />
            )}
        </group>
    );
};