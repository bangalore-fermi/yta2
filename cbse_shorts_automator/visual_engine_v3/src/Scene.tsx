import React, { Suspense, useState } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing, spring } from 'remotion';
import { Canvas, useThree } from '@react-three/fiber';
import { ThreeCanvas } from '@remotion/three';
import { AbsoluteFill,staticFile } from 'remotion';
import { Audio } from '@remotion/media';
import { PerspectiveCamera, Environment, OrbitControls } from '@react-three/drei';
import { VisualScenario } from './types/schema';
import { getTheme, getVariant } from './utils/theme';
import { ZONES } from './utils/animation';
import { ThreeStage } from './components/ThreeStage';
import { ParticleSystem } from './components/ParticleSystem';
import { NanoText } from './components/Typography';
import { Watermark } from './components/Watermark';
import { AnimatedHook } from './components/AnimatedHook';
import { TypewriterQuestion, estimateQuestionHeight } from './components/TypewriterQuestion';
import { OptionCard, OptionState, AnimationMode } from './components/OptionCard';
import { TimerVisual } from './components/TimerVisual';
import { ExplanationCard, estimateExplanationLayout } from './components/ExplanationCard';
import { SceneFinale } from './components/SceneFinale';
import { OutroStage } from './components/OutroStage';



interface SceneProps {
    scenario: VisualScenario;
}

// Internal component to access the R3F Context (useThree)
const SceneContent: React.FC<SceneProps> = ({ scenario }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const { height : unscaledheight} = useThree((state) => state.viewport); // Dynamic Viewport Height
    const currentTime = frame / fps;

    const viewport_height_scalefactor=interpolate(frame, [0, 50], [0.8, 1], { extrapolateRight: 'clamp' });

    const height=unscaledheight * viewport_height_scalefactor;

    // --- HELPER: NVU TO WORLD COORDINATES ---
    // NVU 0.0 is Bottom (-height/2)
    // NVU 1.0 is Top (+height/2)
    const nvuToWorld = (nvu: number) => (nvu - 0.5) * height ;

    const theme = getTheme(scenario.meta.seed);
    const variant = getVariant(scenario.meta.seed);
    const { timeline } = scenario;
    const t_cta_start = timeline.cta.start_time; // <--- The mandatory explicit trigger time

    // SAFE ACCESS: timeline.outro might be undefined in older JSON versions
    const t_outro_start = timeline.outro?.start_time ?? (t_cta_start + 4);


    // --- DYNAMIC LAYOUT CALCULATIONS ---
    // 1. Stage Center: Average of Top (1.0) and Bridge Top (0.65)
    const stageY = nvuToWorld((ZONES.STAGE_TOP + ZONES.STAGE_BOTTOM) / 2);
    
    
    // 2. Question Anchor: Slightly above the bottom of the Bridge zone
    //const questionY = nvuToWorld(ZONES.BRIDGE_BOTTOM + 0.03); 
    
    // 3. Options Start: Top of Interaction Zone
    //const optionsStartY = nvuToWorld(ZONES.INTERACTION_TOP - 0.05);

    // --- STATE MACHINE ---
    const isTiming = currentTime >= timeline.timer.start_time && currentTime < timeline.answer.start_time; // <--- NEW STATE
    const showHook = currentTime < timeline.quiz.question.start_time;
    const showQuestion = currentTime >= timeline.quiz.question.start_time;
    const showOptions = currentTime >= timeline.quiz.options[0].start_time-0.4;
    const showAnswer = currentTime >= timeline.answer.start_time;
    // CRITICAL: ExplanationCard must vanish exactly at t_cta_start
    //const showExplanation = currentTime >= t_reveal && currentTime < t_cta_start; // <-- CORRECTED
    //const showCTA = currentTime >= t_cta_start; // <-- NEW
    
// NEW BOOLEAN: All main quiz elements must vanish (implode) exactly at t_cta_start + 0.2s
    const isQuizElementsVisible = currentTime < t_cta_start + 0.2; // Quiz elements visible until Expl.Card Shreds
    //const isImploding = currentTime >= t_cta_start && currentTime < t_cta_start + 0.2; // <--- RETAINED
    
    


    // --- CAMERA ANIMATION ---
    //const camZ = interpolate(frame, [0, 50], [6, 5], { extrapolateRight: 'clamp' });

    // --- CAMERA ANIMATION ---
    const initialCamZ = 5;
    
    // 1. Camera Z-Pull: Pull back by 0.2 units during the timing phase
    const Z_PULL_START_FRAME = timeline.timer.start_time * fps;
    const Z_PULL_END_FRAME = timeline.answer.start_time * fps;
    const camZPull = interpolate(
        frame,
        [Z_PULL_START_FRAME, Z_PULL_END_FRAME],
        [initialCamZ, initialCamZ + 0.2], // 0.2 unit increase
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );
    const camZ = isTiming ? camZPull : initialCamZ;


    // 2. Anxiety Shake (Subtle, high-frequency noise)
    const shakeIntensity = isTiming ? 1 : 0; // Only shake during timing
    const shakeX = Math.sin(frame * 15.7) * 0.005 * shakeIntensity; // Fast X shake
    const shakeY = Math.cos(frame * 12.3) * 0.005 * shakeIntensity; // Fast Y shake
    // Spring X from 0 to 100 starting at t_outro_start
    /*const panProgress = spring({
        frame: frame - (t_outro_start * fps),
        fps,
        config: { stiffness: 60, damping: 15 },
        from: 0,
        to: 100 // Target: Move camera to the Outro Stage at X=100
    });*/
    
    // Apply pan only if we have reached the outro time
    const camPanX = frame >= (t_outro_start * fps) ? 0 : 0;
    const camPanZ = frame >= (t_outro_start * fps) ? 0 : 0;
    
    // UPDATE: Add camPanX to the X position
    const cameraPosition: [number, number, number] = [shakeX + camPanX, shakeY, camZ+camPanZ];
    //const cameraTarget: [number, number, number] = [shakeX + camPanX, 0, 0];

    // 3. THE BLACKOUT (Ambient Light Dimming)
    const AMBIENT_INTENSITY_START = 0.5;
    const AMBIENT_INTENSITY_DIMMED = 0.0; // 70% drop
    const TimerambientIntensity = interpolate(
        frame,
        [Z_PULL_START_FRAME, Z_PULL_END_FRAME], // Use the same timing window
        [AMBIENT_INTENSITY_START, AMBIENT_INTENSITY_DIMMED],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } // Clamp to start/end values
    );

    let ambientIntensity = isTiming ? TimerambientIntensity : AMBIENT_INTENSITY_START;

    // ADD THIS BLOCK: Outro "Fade to Black" Override
    if (currentTime >= t_outro_start) {
         ambientIntensity = interpolate(
            frame,
            [t_outro_start * fps, (t_outro_start + 0.5) * fps],
            [AMBIENT_INTENSITY_START, 0.05], // Drop ambient light to near zero
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
    }


    const viewportWidth = height * (9/16); // Assuming Vertical 9:16 Video
    const questionText = timeline.quiz.question.text;
    const explanationText = timeline.answer.explanation_text; 
    
    // 1. NEW SYMMETRICAL SAFE ZONE (10% - 90%)
    // Left: 0.1, Right: 0.9
    // Center: 0.5 (Perfectly centered, no offset needed)
    const SAFE_OFFSET_X = 0; 
    
    // Width: 0.9 - 0.1 = 0.8 (80% of screen width)
    const SAFE_MAX_WIDTH = viewportWidth * 0.80;
    // 2. DYNAMIC HEIGHT CALCULATION (Auto-Stack)
    const questionHeight = estimateQuestionHeight(questionText, SAFE_MAX_WIDTH, viewportWidth);
    
    // 3. ANCHOR POINTS
    // Question Center Y
    const questionY = nvuToWorld(ZONES.BRIDGE_BOTTOM + 0.03); 
    
    // Options Start Y: Question Y - Half Question Height - Padding
    const GAP = height * 0.03; // 3% vertical gap
    // 1. Calculate Question Bottom (The ceiling for the dock)
    const questionBottomWorld = questionY - (questionHeight / 2);
    const optionsStartY = questionY - (questionHeight / 2) - GAP;
    // --- CHOREOGRAPHY TIMELINE ---
    const t_answer = timeline.answer.start_time;
    const t_clearance = t_answer + 0.4; // Step 2: Drop & Dock
    const t_reveal = t_clearance + 1; // Step 4: Explanation Pop

    // Boolean States
    const isPostAnswer = currentTime >= t_clearance;
    // STRICT CUTOFF: Explanation Card vanishes exactly when CTA starts
    const showExplanation = currentTime >= t_reveal && currentTime < timeline.cta.start_time + .05;
    // --- SAFETY BOUNDARY ---
    // Safe Zone = 0.15 NVU. 
    const SAFE_ZONE_Y = nvuToWorld(-1);

    

    // Timer Visual Positioning: Slightly above the option cards, below the question
    const timerYPos = optionsStartY + height * 0.03;

    // --- COLOR SYNCHRONIZATION ---
    // Define the specific color here to ensure the Card and Particles match exactly.
    // If theme.surface is undefined, fallback to the standard 'Sticky Note' yellow or white.
    const CARD_COLOR = theme.secondary || '#fff9c4';

    const explanationY = questionBottomWorld - 0.6 - GAP - (height * 0.09);
    // --- NEW: CTA LAYOUT CALCULATIONS ---
    const explCardWidth = SAFE_MAX_WIDTH * .9;
    const ExplanationFontSize=0.05*viewportWidth;
    const explLayout = estimateExplanationLayout(explanationText, explCardWidth, ExplanationFontSize);
    
    const EXPLANATION_CARD_HEIGHT = explLayout.boxHeight; // Approximation from ExplanationCard logic (REQUIRED)
    const explanationCardCenterY = questionBottomWorld- 0.6 - GAP - EXPLANATION_CARD_HEIGHT*0.5; // <-- ADDED: Re-introduce the variable

    // --- NEW: CTA LAYOUT CALCULATIONS ---
    const THUMBNAIL_WIDTH = viewportWidth * 0.9; // 90% of viewport width
    const THUMBNAIL_HEIGHT = THUMBNAIL_WIDTH * (9/16) ; // ~70% of the video slate height (Adjust as needed)
    const CTA_PILL_HEIGHT = height * 0.08; // Fixed CTA pill height for the 50% font size rule
    const CTA_GAP = height * 0.02; // Small visual gap between Thumbnail and Pill

    // 1. Thumbnail Final Resting Y: Top edge is slightly below the video slate (stageY - 0.5 * StageHeight)
    // The Video Slate is in ThreeStage (viewportWidth*0.9 wide). Let's anchor to the stage group's Y.
    // Since StageY is the center of the Stage, the top of the video slate is roughly stageY + (StageHeight/2).
    // Let's use a fixed NVU anchor for the thumbnail top: NVU 0.65
    const THUMBNAIL_TOP_NVU = 0.65;
    const THUMBNAIL_TOP_WORLD_Y = nvuToWorld(THUMBNAIL_TOP_NVU); 
    
    // Thumbnail's Final Center Y = Anchor Top Y - Half Thumbnail Height
    const thumbnailFinalY = THUMBNAIL_TOP_WORLD_Y - (THUMBNAIL_HEIGHT / 2);

    // 2. CTA Pill Final Resting Y: Below the bottom of the Thumbnail
    const thumbnailBottomY = thumbnailFinalY - (THUMBNAIL_HEIGHT / 2);
    // CTA Pill Center Y = Thumbnail Bottom Y - Gap - Half Pill Height
    const ctaPillFinalY = thumbnailBottomY - CTA_GAP - (CTA_PILL_HEIGHT / 2);

    const [explCardHeight, setExplCardHeight] = useState(0.6); // Default fallback

    

    return (
        <>
           {/* CAMERA: ANXIETY SHAKE + Z-PULL */}
            <PerspectiveCamera 
                makeDefault 
                position={cameraPosition} // Dynamic position applied here
                fov={50} 
                
            />
            {/* Use OrbitControls to define the target point for the default camera */}
            <OrbitControls 
                // You want the target to be [cameraPosition[0], 0, 0]
                target={[cameraPosition[0], 0, -2000]} 
                // Disable user interaction if you only want it to manage the target
                enableRotate={false} 
                enableZoom={false} 
                enablePan={false}
            />
            {/* LIGHTING: THE BLACKOUT */}
            <ambientLight intensity={ambientIntensity} /> 
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />

            {/* 1. PARTICLE SYSTEM */}
            
            <ParticleSystem variant={variant} color={theme.primary} 
            
                // This is the ExplanationCard's expected Y-Center. ParticleSystem will calculate height.
            />

            {/* 2. THE STAGE (Dynamic Positioning) */}
            <group position={[0, stageY, 0]}>
                <Suspense fallback={null}>
                     <ThreeStage videoUrl={scenario.assets.video_source_url} overlayProgress={0.2} 
                     width={viewportWidth*0.9} // <--- Makes it 50% bigger
                     />
                </Suspense>
            </group>

            {/* 3. TIMER VISUAL (New Component) */}
            {isTiming && (
                <TimerVisual
                    startTime={timeline.timer.start_time}
                    endTime={timeline.answer.start_time}
                    theme={theme}
                    fps={fps}
                    height={height}
                    positionY={timerYPos}
                    seed={scenario.meta.seed+2}
                />
            )}

            {/* 3. THE BRIDGE (Question Card) */}
            
            {showQuestion && isQuizElementsVisible && (
                <TypewriterQuestion
                    text={questionText}
                    theme={theme}
                    viewportWidth={viewportWidth}
                    maxWidth={SAFE_MAX_WIDTH} // Pass strict width
                    startTime={timeline.quiz.question.start_time}
                    finishTime={timeline.quiz.options[0].start_time}
                    position={[SAFE_OFFSET_X, questionY, 0]} // Apply Offset
                    //scale={isImploding ? implosionScale : 1}
                />
            )}

            {/* 4. OPTION CARDS (Centered, Synced, Sliding) */}
            {showOptions && isQuizElementsVisible && timeline.quiz.options.map((opt, i) => {
            //{showOptions && timeline.quiz.options.map((opt, i) => {
                
                const isCorrect = opt.id === timeline.answer.correct_option_id;

                // State Logic
                let cardState: OptionState = 'neutral';
                if (showAnswer) cardState = isCorrect ? 'correct' : 'wrong';

                if (showAnswer) {
                    cardState = opt.id === timeline.answer.correct_option_id 
                        ? 'correct' 
                        : 'wrong';
                }

                // Layout Constants
                const cardHeight = height * 0.09; 
                const cardGap = height * 0.02;
                
                // Final resting Y position for this card
                const finalYPos = optionsStartY - (cardHeight/2) - (i * (cardHeight + cardGap));

                // x=0 for center, z=0 for base depth
                const positionZ = 0; 

                // Docking Layout (Only calculated for correct answer)
                // Target: Strictly below Question Box
                const dockYPos = questionBottomWorld - GAP - (cardHeight / 2);

                // Mode Selector
                let mode: AnimationMode = 'intro';
                if (isPostAnswer) {
                    mode = isCorrect ? 'dock' : 'drop';
                }
                const STAGGER = 0.15;
                return (
                    <OptionCard
                        key={opt.id}
                        text={opt.text}
                        state={cardState}
                        theme={theme}
                        width={SAFE_MAX_WIDTH} 
                        height={cardHeight}
                        landingTime={opt.start_time} // SYNC TRIGGER
                        finalY={finalYPos} // FINAL RESTING Y
                        dockY={dockYPos} // <--- Pass Dock Target
                        sequenceStartTime={t_clearance+(i * STAGGER)} // <--- Sync Trigger
                        mode={mode} // <--- Physics Selector
                        positionZ={positionZ} // BASE Z// --- NEW DETERMINISTIC PROPS ---
                        seed={scenario.meta.seed+1}
                        index={i}
                        //scale={isImploding ? implosionScale : 1} // APPLY IMPLOSION SCALE
                    />
                );
            })}

           

            {/* EXPLANATION CARD (The sticky note) */}
            {showExplanation && (
                <ExplanationCard
                    text={explanationText}
                    width={explCardWidth} // 90% of Layout Width
                    // Anchor is the BOTTOM of the Docked Card
                    // DockedCardY (Center) - HalfHeight = Docked Bottom
                    anchorY={questionBottomWorld - GAP - (height * 0.09)} 
                    safeZoneY={SAFE_ZONE_Y}
                    startTime={t_reveal}
                    ExplanationFontSize={ExplanationFontSize}
                    ExpCardcolor={CARD_COLOR} // <--- Pass Explicit Color to Cardt
                // NEW: Capture the height
                   // onHeightCalculated={(h) => setExplCardHeight(h)}
        />
            )}

           {/* 7. SCENE 6: THE GRAND FINALE (Encapsulated in a single component) */}
            {currentTime >= t_cta_start && (
                <SceneFinale
                    scenario={scenario}
                    fps={fps}
                    viewportWidth={viewportWidth}
                    height={height}
                    thumbnailFinalY={thumbnailFinalY}
                    THUMBNAIL_WIDTH={THUMBNAIL_WIDTH}
                    THUMBNAIL_HEIGHT={THUMBNAIL_HEIGHT}
                    ctaPillFinalY={ctaPillFinalY}
                    CTA_PILL_HEIGHT={CTA_PILL_HEIGHT}
                    explanationCardCenterY={explanationCardCenterY}
                    explanationCardWidth={explCardWidth}
                    explanationCardHeight={EXPLANATION_CARD_HEIGHT}
                    CARD_COLOR={CARD_COLOR}
                />
            )}

            {/* --- NEW: SCENE 7 (OUTRO STAGE) --- */}
            <OutroStage 
                scenario={scenario}
                fps={fps}
                t_outro_start={t_outro_start}
            />


            {/* 5. HOOK (Overlay) - DYNAMIC ANIMATION */}
            {showHook && (
                <AnimatedHook 
                    text={timeline.hook.text_content}
                    seed={scenario.meta.seed+0}
                    theme={theme}
                    fontSize={height * 0.05}
                    fontUrl={scenario.assets.font_url}
                    maxAvailableWidth={viewportWidth}
                />
            )}

            <Environment preset="city" />
        </>
    );
};

export const Scene: React.FC<SceneProps> = ({ scenario }) => {
    const theme = getTheme(scenario.meta.seed+5);
    const { width, height } = useVideoConfig();
    const variant = getVariant(scenario.meta.seed);
    console.log("ParticleSystem Variant:", variant);

    console.log(theme.bg[0],theme.bg[1])
    const audioSource = staticFile(scenario.assets.audio_url);

    return (
        
    <div style={{ width: '100%', height: '100%', background: `radial-gradient(circle, ${theme.bg[0]}, ${theme.bg[1]})` }}>
            
            <Audio 
        src={audioSource} 
        volume={0.7}
      />
            
            <ThreeCanvas shadows dpr={[1, 2]} 
            width={width} 
            height={height}            
            >
                
                <SceneContent scenario={scenario} />
            </ThreeCanvas>
            {/* Layer 100: The Ghost UI Overlay */}
            <Watermark scenario={scenario} />
        </div>
       
    );
};