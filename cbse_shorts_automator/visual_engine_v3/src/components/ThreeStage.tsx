import React, { useRef } from 'react';
import { useVideoTexture, RoundedBox, useTexture } from '@react-three/drei';
import { DoubleSide, Group } from 'three';
import { useFrame } from '@react-three/fiber';

interface ThreeStageProps {
    videoUrl: string;
    overlayProgress: number; // For future dynamic updates
}

export const ThreeStage: React.FC<ThreeStageProps> = ({ videoUrl }) => {
    const videoTexture = useVideoTexture(videoUrl, {
        unsuspend: 'canplay',
        loop: true,
        start: true,
        muted: true // Muted because Remotion handles audio separately
    });

    const groupRef = useRef<Group>(null);

    // Continuous slight floating animation
    useFrame((state) => {
        if (groupRef.current) {
            groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
        }
    });

    return (
        <group ref={groupRef}>
            {/* 1. The Video Slate (16:9 Aspect Ratio) */}
            {/* W: 1, H: 0.5625 = 16:9 */}
            <RoundedBox args={[1, 0.5625, 0.05]} radius={0.02} smoothness={4}>
                <meshBasicMaterial map={videoTexture} toneMapped={false} />
            </RoundedBox>

            {/* 2. The Fake UI Overlay (Composite Mesh) */}
            {/* Offset z +0.026 (0.025 half-depth + 0.001 gap) */}
            <mesh position={[0, -0.23, 0.026]}>
                 <planeGeometry args={[0.9, 0.05]} />
                 <meshBasicMaterial color="red" opacity={0.8} transparent />
                 {/* In real prod, load a transparent PNG texture here */}
            </mesh>
            <mesh position={[0, -0.23, 0.027]}>
                 <planeGeometry args={[0.9, 0.01]} />
                 <meshBasicMaterial color="white" opacity={0.3} transparent />
            </mesh>
        </group>
    );
};
