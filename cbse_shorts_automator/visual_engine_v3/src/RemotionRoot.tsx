import React, { useEffect, useState } from 'react';
import { Composition, staticFile, continueRender, delayRender } from 'remotion';
import { VisualScenario } from './types/schema';
import { MainVideo } from './MainVideo'; // Updated component name
import './style.css'; 

// Define a type for the initial metadata and full scenario we need to fetch
interface DynamicCompositionData {
    scenario: VisualScenario;
    durationInFrames: number;
    width: number;
    height: number;
}

export const RemotionRoot: React.FC = () => {
    const [handle] = useState(() => delayRender());
    const [compData, setCompData] = useState<DynamicCompositionData | null>(null);

    const FPS = 30; // Define a consistent FPS for conversion

    useEffect(() => {
        // 1. Fetch the scenario data from the public folder
        fetch(staticFile('scenario_data.json')) 
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then((data: VisualScenario) => {
                const { resolution, duration_seconds } = data.meta;
                
                // 2. Calculate dynamic properties
                const durationInFrames = Math.ceil(duration_seconds * FPS);
                
                // 3. Store the full scenario and calculated metadata
                setCompData({
                    scenario: data,
                    durationInFrames,
                    width: resolution.w,
                    height: resolution.h,
                });
                
                // 4. Signal Remotion to continue once data is ready
                continueRender(handle);
            })
            .catch(err => {
                console.error("❌ Failed to load scenario data for composition:", err);
                // In a real environment, you might log this error or show a safe fallback.
                // We keep the render delayed to prevent showing an unconfigured Composition.
            });
    }, [handle]);

    if (!compData) {
        // Display loading message while fetching data
        return (
            <div style={{ flex: 1, backgroundColor: '#18181b', color: '#fff', fontSize: 32, padding: 50 }}>
                Loading Composition Metadata...
            </div>
        );
    }

    // 5. Define the Composition using dynamic data from the JSON
    return (
        <>
            <Composition
                id="NCERT-Shorts-V3"
                // Pass the MainVideo component
                component={MainVideo} 
                
                // --- DYNAMIC VALUES FROM JSON METADATA ---
                durationInFrames={compData.durationInFrames}
                fps={FPS} 
                width={compData.width}
                height={compData.height}
                // ----------------------------------------
                
                // Pass the full scenario data as input props to the MainVideo component
                defaultProps={{ scenario: compData.scenario }}
            />
        </>
    );
};