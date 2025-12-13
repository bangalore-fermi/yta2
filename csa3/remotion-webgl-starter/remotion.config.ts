import { Config } from '@remotion/cli/config';

// 'angle' is critical for WebGL in Codespaces (Linux headless)
Config.setChromiumOpenGlRenderer('angle');

// Note: Config.setOutputFormat is removed. 
// Output format is now determined automatically by your output filename (e.g., video.mp4) during render.
