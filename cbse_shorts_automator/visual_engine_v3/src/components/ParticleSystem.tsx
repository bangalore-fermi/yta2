import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group } from 'three';
import { Cloud, Sparkles, Stars } from '@react-three/drei';

interface ParticleSystemProps {
    variant: number; // 0, 1, or 2
    color: string;
}

export const ParticleSystem: React.FC<ParticleSystemProps> = ({ variant, color }) => {
    // STRICT TYPING: Use Group type for the ref
    const ref = useRef<Group>(null);

    useFrame((state) => {
        if (ref.current) {
             // Slowly rotate the entire system
             ref.current.rotation.y += 0.001;
        }
    });

    return (
        <group ref={ref}>
            {/* Variant 0: Rising Bubbles (Sparkles) */}
            {variant === 0 && (
                <Sparkles 
                    count={100} 
                    scale={12} 
                    size={4} 
                    speed={0.4} 
                    opacity={0.5} 
                    color={color}
                    noise={0.2}
                />
            )}

            {/* Variant 1: Digital Rain (Downward Sparkles) */}
            {variant === 1 && (
                <Sparkles 
                    count={150} 
                    scale={[10, 10, 10]} 
                    size={3} 
                    speed={-0.5} // Downward
                    opacity={0.6}
                    color="#ffffff" 
                />
            )}

            {/* Variant 2: Cosmic Dust (Stars + Clouds) */}
            {variant === 2 && (
                <>
                    <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
                    <Cloud opacity={0.2} speed={0.4} width={10} depth={1.5} segments={20} color={color} />
                </>
            )}
        </group>
    );
};