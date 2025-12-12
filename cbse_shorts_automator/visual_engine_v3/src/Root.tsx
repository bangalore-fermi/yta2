import React from 'react';
import { Composition } from 'remotion';
import { ScenarioFetcher } from './ScenarioFetcher';
import './style.css'; // Standard css reset

export const RemotionRoot: React.FC = () => {
    return (
        <>
            <Composition
                id="NCERT-Shorts-V3"
                component={ScenarioFetcher}
                durationInFrames={1050} // 35 sec @ 30fps
                fps={30}
                width={1080}
                height={1920}
            />
        </>
    );
};
