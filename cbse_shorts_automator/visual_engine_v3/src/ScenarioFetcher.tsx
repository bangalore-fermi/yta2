import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile, AbsoluteFill } from 'remotion';
import { VisualScenario } from './types/schema';
import { Scene } from './Scene';

export const ScenarioFetcher: React.FC = () => {
    const [handle] = useState(() => delayRender());
    const [scenario, setScenario] = useState<VisualScenario | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Log the exact path we are trying to fetch
        const targetPath = staticFile('scenario_mock.json');
        console.log("Attempting to fetch:", targetPath);

        fetch(targetPath)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP Error: ${res.status} ${res.statusText}`);
                return res.json();
            })
            .then(data => {
                console.log("Data loaded:", data);
                setScenario(data);
                continueRender(handle);
            })
            .catch(err => {
                console.error("Fetch failed:", err);
                setError(err.message);
                continueRender(handle); // Unblock rendering to show error
            });
    }, [handle]);

    // 1. SHOW ERROR STATE
    if (error) {
        return (
            <AbsoluteFill style={{ 
                backgroundColor: 'black', 
                color: 'red', 
                fontSize: 40, 
                padding: 50,
                fontFamily: 'monospace' 
            }}>
                <h1>⚠️ DATA LOAD FAILED</h1>
                <p>{error}</p>
                <p style={{ color: 'white', fontSize: 24 }}>Check console for path details.</p>
            </AbsoluteFill>
        );
    }

    // 2. SHOW LOADING STATE
    if (!scenario) {
        return (
            <AbsoluteFill style={{ 
                justifyContent: 'center', 
                alignItems: 'center', 
                backgroundColor: '#111' 
            }}>
                <h1 style={{ color: 'white' }}>⏳ Loading Scenario...</h1>
            </AbsoluteFill>
        );
    }

    return <Scene scenario={scenario} />;
};