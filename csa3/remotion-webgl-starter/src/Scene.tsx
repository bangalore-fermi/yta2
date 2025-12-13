import { ThreeCanvas } from '@remotion/three';
import { AbsoluteFill, useVideoConfig, useCurrentFrame } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

const RotatingCube = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  useFrame(() => {
    if (!meshRef.current) return;
    const progress = frame / 150; 
    meshRef.current.rotation.x = progress * Math.PI * 2;
    meshRef.current.rotation.y = progress * Math.PI * 2;
  });

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[2.5, 2.5, 2.5]} />
      <meshStandardMaterial color="#4290f5" />
    </mesh>
  );
};

export const My3DScene: React.FC = () => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ 
        // Corrected line below: removed the extra ')' at the end
        background: 'radial-gradient(circle, rgb(255, 26, 21), rgb(0, 0, 0))' 
    }}>
      <ThreeCanvas width={width} height={height}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <RotatingCube />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};