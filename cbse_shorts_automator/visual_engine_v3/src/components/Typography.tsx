import React from 'react';
import { Text } from '@react-three/drei';

interface NanoTextProps {
    text: string;
    position: [number, number, number];
    fontSize?: number;
    color?: string;
    anchorX?: 'center' | 'left' | 'right';
    anchorY?: 'middle' | 'top' | 'bottom';
    fontUrl?: string; // Optional custom font
}

export const NanoText: React.FC<NanoTextProps> = ({ 
    text, position, fontSize = 0.5, color = 'white', anchorX = 'center', anchorY='middle', fontUrl 
}) => {
    
    // Elastic Logic: Auto-shrink if text is too long
    const adjustedSize = text.length > 20 ? fontSize * 0.75 : fontSize;

    return (
        <Text
            position={position}
            fontSize={adjustedSize}
            color={color}
            font={fontUrl || "https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLGT9Z1xlFQ.woff2"} // Poppins Fallback
            anchorX={anchorX}
            anchorY={anchorY}
            outlineWidth={0.02}
            outlineColor="#000000"
        >
            {text}
        </Text>
    );
};
