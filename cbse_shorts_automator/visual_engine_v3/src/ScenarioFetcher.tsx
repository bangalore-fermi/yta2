import React, { useEffect, useState } from 'react';
import { continueRender, delayRender, staticFile } from 'remotion';
import { VisualScenario } from './types/schema';
import { Scene } from './Scene';

// 1. IMPORT THE JSON FILE DIRECTLY (Assuming you moved it to src/data/scenario_mock.json)
import mockData from '../public/scenario_mock.json';

// 2. RESOLVE ALL LOCAL ASSET PATHS IMMEDIATELY
const resolvedAssets = {
    // Remove the leading slash from the path ('/assets/mock_video.mp4' -> 'assets/mock_video.mp4')
    video_source_url: staticFile(mockData.assets.video_source_url.replace(/^\//, '')),
    //font_url: staticFile(mockData.assets.font_url.replace(/^\//, '')),
    audio_url: staticFile(mockData.assets.audio_url.replace(/^\//, '')),
    channel_logo_url: staticFile(mockData.assets.channel_logo_url.replace(/^\//, '')),
    env_map_url: staticFile(mockData.assets.env_map_url.replace(/^\//, '')),
    cloud_map_url: staticFile(mockData.assets.cloud_map_url.replace(/^\//, '')),
    
    // Use the remote path as-is
    thumbnail_url: mockData.assets.thumbnail_url,
};

// 3. CREATE THE FINAL, STATIC SCENARIO OBJECT
const STATIC_SCENARIO: VisualScenario = {
    ...(mockData as VisualScenario),
    assets: resolvedAssets as VisualScenario['assets'],
};

export const ScenarioFetcher: React.FC = () => {
    const [handle] = useState(() => delayRender());
    const [scenario] = useState<VisualScenario>(STATIC_SCENARIO);

    useEffect(() => {// --- PRE-LOAD VIDEO ASSET ---
        const video = document.createElement('video');
        video.src = scenario.assets.video_source_url; // Uses the staticFile-resolved path

        const onLoaded = () => {
            console.log("Video asset pre-loaded successfully! Scene should now render.");
            continueRender(handle); // RELEASE THE LOCK!
        };

        const onError = (e: Event) => {
             console.error("Video failed to load or play!", e);
             continueRender(handle); // Must proceed even on error
        };
        
        video.addEventListener('canplaythrough', onLoaded, { once: true });
        video.addEventListener('error', onError, { once: true });
        video.load();

        return () => {
            video.removeEventListener('canplaythrough', onLoaded);
            video.removeEventListener('error', onError);
        };
        
    }, [handle, scenario.assets.video_source_url]);
    

    if (!scenario)  return (
             <div style={{ width: '100%', height: '100%', background: 'black', color: 'white', display: 'grid', placeContent: 'center' }}>
                 Loading Scene Assets...
             </div>
         );

    return <Scene scenario={scenario} />;
};
