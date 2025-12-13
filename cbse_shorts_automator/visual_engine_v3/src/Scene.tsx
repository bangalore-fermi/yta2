import React, { Suspense } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { Canvas, useThree } from '@react-three/fiber';
import { ThreeCanvas } from '@remotion/three';
import { AbsoluteFill } from 'remotion';
import { PerspectiveCamera, Environment } from '@react-three/drei';
import { VisualScenario } from './types/schema';
import { getTheme, getVariant } from './utils/theme';
import { ZONES } from './utils/animation';
import { ThreeStage } from './components/ThreeStage';
import { ParticleSystem } from './components/ParticleSystem';
import { NanoText } from './components/Typography';
import { Watermark } from './components/Watermark';
import { AnimatedHook } from './components/AnimatedHook';

interface SceneProps {
    scenario: VisualScenario;
}

// Internal component to access the R3F Context (useThree)
const SceneContent: React.FC<SceneProps> = ({ scenario }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const { height } = useThree((state) => state.viewport); // Dynamic Viewport Height
    const currentTime = frame / fps;

    // --- HELPER: NVU TO WORLD COORDINATES ---
    // NVU 0.0 is Bottom (-height/2)
    // NVU 1.0 is Top (+height/2)
    const nvuToWorld = (nvu: number) => (nvu - 0.5) * height ;

    const theme = getTheme(scenario.meta.seed);
    const variant = getVariant(scenario.meta.seed);
    const { timeline } = scenario;

    // --- DYNAMIC LAYOUT CALCULATIONS ---
    // 1. Stage Center: Average of Top (1.0) and Bridge Top (0.65)
    const stageY = nvuToWorld((ZONES.STAGE_TOP + ZONES.STAGE_BOTTOM) / 2);
    
    // 2. Question Anchor: Slightly above the bottom of the Bridge zone
    const questionY = nvuToWorld(ZONES.BRIDGE_BOTTOM + 0.03); 
    
    // 3. Options Start: Top of Interaction Zone
    const optionsStartY = nvuToWorld(ZONES.INTERACTION_TOP - 0.05);

    // --- STATE MACHINE ---
    const showHook = currentTime < timeline.quiz.question.start_time;
    const showQuestion = currentTime >= timeline.quiz.question.start_time;
    const showOptions = currentTime >= timeline.quiz.options[0].start_time;
    const showAnswer = currentTime >= timeline.answer.start_time;
    const showCTA = currentTime >= timeline.cta.start_time;

    // --- CAMERA ANIMATION ---
    const camZ = interpolate(frame, [0, 50], [6, 5], { extrapolateRight: 'clamp' });

    return (
        <>
            <PerspectiveCamera makeDefault position={[0, 0, camZ]} fov={50} />
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />

            {/* 1. PARTICLE SYSTEM */}
            
            <ParticleSystem variant={variant} color={theme.primary} />

            {/* 2. THE STAGE (Dynamic Positioning) */}
            <group position={[0, stageY, 0]}>
                <Suspense fallback={null}>
                     <ThreeStage videoUrl={scenario.assets.video_source_url} overlayProgress={0.2} />
                </Suspense>
            </group>

            {/* 3. THE BRIDGE (Question Text) */}
            {showQuestion && (
                <NanoText 
                    text={timeline.quiz.question.text}
                    position={[0, questionY, 0]} 
                    fontSize={height * 0.035} // 3.5% of Screen Height
                    color="#ffffff"
                    fontUrl={scenario.assets.font_url}
                />
            )}

            {/* 4. INTERACTION ZONE (Cards) */}
            {showOptions && timeline.quiz.options.map((opt, i) => {
                const entryTime = opt.start_time * fps;
                const opacity = interpolate(frame, [entryTime, entryTime + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                
                // Dynamic Stacking: Each card is ~10% of height down
                const yPos = optionsStartY - (i * (height * 0.11)); 
                
                const isCorrect = opt.id === timeline.answer.correct_option_id;
                const color = (showAnswer && isCorrect) ? theme.primary : "#ffffff";
                
                return (
                    <group key={opt.id} position={[0, yPos, 0]}>
                        <mesh scale={[opacity, opacity, 1]}>
                            {/* Card Width relative to viewport width approx 80% (3 units in world space usually fits) */}
                            <boxGeometry args={[3, height * 0.08, 0.1]} />
                            <meshStandardMaterial color={showAnswer && !isCorrect ? "#333333" : "#222222"} transparent opacity={0.9} />
                        </mesh>
                        <NanoText 
                            text={opt.text} 
                            position={[0, 0, 0.06]} 
                            fontSize={height * 0.025} 
                            color={color} 
                        />
                    </group>
                )
            })}

            {/* 5. HOOK (Overlay) - DYNAMIC ANIMATION */}
            {showHook && (
                <AnimatedHook 
                    text={timeline.hook.text_content}
                    seed={scenario.meta.seed+0}
                    theme={theme}
                    fontSize={height * 0.06}
                    fontUrl={scenario.assets.font_url}
                />
            )}

            <Environment preset="city" />
        </>
    );
};

export const Scene: React.FC<SceneProps> = ({ scenario }) => {
    const theme = getTheme(scenario.meta.seed);
    const { width, height } = useVideoConfig();
    const variant = getVariant(scenario.meta.seed);
    console.log("ParticleSystem Variant:", variant);

    console.log(theme.bg[0],theme.bg[1])

    return (
        
    <div style={{ width: '100%', height: '100%', background: `radial-gradient(circle, ${theme.bg[0]}, ${theme.bg[1]})` }}>
            <ThreeCanvas shadows dpr={[1, 2]} 
            width={width} 
            height={height}            
            >
                
                <SceneContent scenario={scenario} />
            </ThreeCanvas>
            {/* Layer 100: The Ghost UI Overlay */}
            <Watermark scenario={scenario} />
        </div>
       
    );
};