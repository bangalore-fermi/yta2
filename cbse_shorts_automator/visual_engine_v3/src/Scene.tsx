import React, { Suspense } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera, Environment } from '@react-three/drei';
import { VisualScenario } from './types/schema';
import { getTheme, getVariant } from './utils/theme';
import { ThreeStage } from './components/ThreeStage';
import { ParticleSystem } from './components/ParticleSystem';
import { NanoText } from './components/Typography';

interface SceneProps {
    scenario: VisualScenario;
}

export const Scene: React.FC<SceneProps> = ({ scenario }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const currentTime = frame / fps;

    const theme = getTheme(scenario.meta.seed);
    const variant = getVariant(scenario.meta.seed);
    const { timeline } = scenario;

    // --- LOGIC: DETERMINE CURRENT SCENE STATE ---
    // Simple state machine based on timestamps
    const showHook = currentTime < timeline.quiz.question.start_time;
    const showQuestion = currentTime >= timeline.quiz.question.start_time;
    const showOptions = currentTime >= timeline.quiz.options[0].start_time;
    const showAnswer = currentTime >= timeline.answer.start_time;
    const showCTA = currentTime >= timeline.cta.start_time;

    // --- LOGIC: CAMERA MOVEMENTS (Spring-ish interpolation) ---
    // Base Z position
    const camZ = interpolate(frame, [0, 50], [6, 5], { extrapolateRight: 'clamp' });

    return (
        <div style={{ width: '100%', height: '100%', background: `radial-gradient(circle, ${theme.bg[0]}, ${theme.bg[1]})` }}>
            <Canvas shadows dpr={[1, 2]}>
                <PerspectiveCamera makeDefault position={[0, 0, camZ]} fov={50} />
                <ambientLight intensity={0.5} />
                <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
                
                {/* 1. PARTICLE SYSTEM */}
                <ParticleSystem variant={variant} color={theme.primary} />

                {/* 2. THE STAGE (Top 35% Zone) */}
                <group position={[0, 1.8, 0]}> {/* Approximate Y pos for Top Zone */}
                    <Suspense fallback={null}>
                         <ThreeStage videoUrl={scenario.assets.video_source_url} overlayProgress={0.2} />
                    </Suspense>
                </group>

                {/* 3. THE BRIDGE (Question Text) */}
                {/* Visual Anchor in the 7% Bridge Zone */}
                {showQuestion && (
                    <NanoText 
                        text={timeline.quiz.question.text}
                        position={[0, 0.8, 0]} // Just below stage
                        fontSize={0.35}
                        color="#ffffff"
                        fontUrl={scenario.assets.font_url}
                    />
                )}

                {/* 4. INTERACTION ZONE (Cards) */}
                {showOptions && timeline.quiz.options.map((opt, i) => {
                    // Staggered Entrance
                    const entryTime = opt.start_time * fps;
                    const opacity = interpolate(frame, [entryTime, entryTime + 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                    const yPos = 0.0 - (i * 0.6); // Simple stack layout
                    
                    // Highlight Logic
                    const isCorrect = opt.id === timeline.answer.correct_option_id;
                    const color = (showAnswer && isCorrect) ? theme.primary : "#ffffff";
                    
                    return (
                        <group key={opt.id} position={[0, yPos, 0]}>
                            <mesh scale={[opacity, opacity, 1]}>
                                <boxGeometry args={[3, 0.5, 0.1]} />
                                <meshStandardMaterial color={showAnswer && !isCorrect ? "#333333" : "#222222"} transparent opacity={0.9} />
                            </mesh>
                            <NanoText 
                                text={opt.text} 
                                position={[0, 0, 0.06]} 
                                fontSize={0.25} 
                                color={color} 
                            />
                        </group>
                    )
                })}

                {/* 5. HOOK (Overlay) */}
                {showHook && (
                    <NanoText 
                        text={timeline.hook.text_content}
                        position={[0, 0, 1]}
                        fontSize={0.6}
                        color={theme.primary}
                    />
                )}

                <Environment preset="city" />
            </Canvas>
        </div>
    );
};
