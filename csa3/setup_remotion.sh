#!/bin/bash

# ==========================================
# Remotion + WebGL + React Scaffolding
# Target Env: GitHub Codespaces (Ubuntu)
# ==========================================

echo "🚀 Starting Project Scaffolding..."

# 1. Project Name
PROJECT_NAME="remotion-webgl-starter"
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

echo "📦 Initializing package.json with PINNED versions..."
# We pin React to 18.x and Three to compatible versions to ensure stability.
# Remotion v4 is used.
cat > package.json <<EOF
{
  "name": "$PROJECT_NAME",
  "version": "1.0.0",
  "description": "Remotion WebGL Scaffolding for Codespaces",
  "scripts": {
    "start": "remotion studio",
    "build": "remotion render",
    "upgrade": "remotion upgrade",
    "test": "eslint src --ext ts,tsx,js,jsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "remotion": "4.0.230",
    "three": "^0.169.0",
    "@react-three/fiber": "^8.17.10",
    "@remotion/three": "4.0.230",
    "@remotion/cli": "4.0.230",
    "@remotion/eslint-config": "4.0.230"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/three": "^0.169.0",
    "@types/webgl2": "0.0.6",
    "typescript": "^5.6.3",
    "eslint": "^8.57.0",
    "prettier": "^3.3.3",
    "tsx": "^4.19.0"
  },
  "packageManager": "npm@10.0.0"
}
EOF

echo "⚙️ Creating TypeScript Configuration..."
cat > tsconfig.json <<EOF
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
EOF

echo "🔧 Creating Remotion Config (Crucial for Linux WebGL)..."
# Setting 'angle' is critical for headless rendering stability on Linux
cat > remotion.config.ts <<EOF
import { Config } from '@remotion/cli/config';

// 'angle' forces Chrome to use the ANGLE backend for WebGL, 
// which is more stable in containerized/headless Linux environments.
Config.setChromiumOpenGlRenderer('angle');
Config.setOutputFormat('mp4');
EOF

echo "🙈 Creating .gitignore..."
cat > .gitignore <<EOF
node_modules
dist
.env
.DS_Store
*.mp4
EOF

echo "📂 Creating Source Files..."
mkdir -p src

# Entry Point
cat > src/index.ts <<EOF
import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
EOF

# Root Component
cat > src/Root.tsx <<EOF
import { Composition } from 'remotion';
import { My3DScene } from './Scene';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="My3DVideo"
        component={My3DScene}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
EOF

# The 3D Scene (Integration logic)
cat > src/Scene.tsx <<EOF
import { ThreeCanvas } from '@remotion/three';
import { useVideoConfig, useCurrentFrame } from 'remotion';
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

const RotatingCube = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // In Remotion + R3F, you can use useFrame, but strictly rely on 'frame' 
  // from Remotion for deterministic rendering, OR use standard time delta
  // provided the context is handled correctly.
  // Best practice: Drive animation by 'frame' for perfect reproducibility.
  
  useFrame(() => {
    if (!meshRef.current) return;
    // Rotate 360 degrees (2PI) over 150 frames
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
    <ThreeCanvas width={width} height={height}>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <RotatingCube />
    </ThreeCanvas>
  );
};
EOF

echo "🐧 Installing Linux System Dependencies..."
echo "Note: This requires sudo. If prompted, please enter password."
# These are strictly required for the Remotion headless browser to run in a bare Linux container
sudo apt-get update
sudo apt-get install -y \
  libnss3 \
  libdbus-1-3 \
  libatk1.0-0 \
  libgbm-dev \
  libasound2 \
  libxrandr2 \
  libxkbcommon-dev \
  libxfixes3 \
  libxcomposite1 \
  libxdamage1 \
  libpango-1.0-0 \
  libcairo2 \
  libcups2 \
  libatk-bridge2.0-0

echo "📦 Installing Node Modules..."
npm install

echo "✅ Setup Complete."
echo "=========================================="
echo "👉 To start the preview: npm start"
echo "👉 Codespaces will detect port 3000. Click 'Open in Browser'."
echo "=========================================="