import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { VisualScenario } from './types/schema';
import { Scene } from './Scene';

export const ScenarioFetcher: React.FC = () => {
    const [handle] = useState(() => delayRender());
    const [scenario, setScenario] = useState<VisualScenario | null>(null);

    useEffect(() => {
        // In a real app, you might fetch from an API.
        // For local dev, we fetch the generated mock file from public or import it.
        // Here we assume the test_mock_payload.py generated it in the root, 
        // but Remotion needs it in 'public' or imported.
        // For simplicity in this scaffold, we fetch relative path assuming it's served or copied.
        
        // NOTE: In production, the Director passes this data. 
        // For this Scaffold, we will use a hardcoded fetch to the mock we know exists.
        
        fetch(staticFile('scenario_mock.json')) // Assumes file is moved to public/ or served via proxy
            .then(res => res.json())
            .then(data => {
                setScenario(data);
                continueRender(handle);
            })
            .catch(err => {
                console.error("Failed to load scenario", err);
                // Fallback or Error State
            });
    }, [handle]);

    if (!scenario) return null;

    return <Scene scenario={scenario} />;
};
