import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { useMemo } from 'react';
import * as THREE from 'three';

const Box = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Rotate mesh based on current frame (1 rotation every 3 seconds)
  const rotation = (frame / fps) * Math.PI * 2 / 3;

  return (
    <mesh rotation={[rotation, rotation, 0]}>
      <boxGeometry args={[3, 3, 3]} />
      <meshStandardMaterial color="#0b84f3" />
    </mesh>
  );
};

export const My3DScene: React.FC = () => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill>
      <ThreeCanvas
        width={width}
        height={height}
        style={{ backgroundColor: 'white' }}
        camera={{ position: [0, 0, 10] }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Box />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
