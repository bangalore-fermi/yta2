import React from 'react';
import { VisualScenario } from './types/schema';
import { Scene } from './Scene'; // Assuming Scene component exists

// Define the expected props for this component
interface MainVideoProps {
    scenario?: VisualScenario;
}

// Renamed and refactored from ScenarioFetcher
export const MainVideo: React.FC<MainVideoProps> = ({ scenario }) => {
    
    // The scenario data is already available from RemotionRoot's defaultProps.
    // We can render the main Scene immediately.

    if (!scenario) {
        // This case should theoretically not happen if RemotionRoot loads correctly
        return <div style={{ color: 'red' }}>Error: Scenario data missing.</div>;
    }

    // Pass the complete scenario object to the rendering Scene component
    return <Scene scenario={scenario} />;
};