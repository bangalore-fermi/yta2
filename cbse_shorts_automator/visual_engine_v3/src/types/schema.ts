export interface VisualScenario {
    meta: {
        version: string;
        resolution: { w: number; h: number };
        seed: number;
        duration_seconds: number;
    };
    assets: {
        audio_url: string;
        video_source_url: string;
        thumbnail_url: string;
        channel_logo_url: string;
        font_url?: string;
    };
    timeline: {
        hook: { start_time: number; text_content: string };
        quiz: {
            question: { text: string; start_time: number };
            options: Array<{ id: string; text: string; start_time: number }>;
        };
        timer: { start_time: number; duration: number; label_text: string };
        answer: {
            start_time: number;
            correct_option_id: string;
            explanation_text: string;
            celebration_text: string;
        };
        cta: { start_time: number; social_text: string; link_text: string };
        outro: { start_time: number; line_1: string; line_2: string };
    };
    yt_overlay: {
        progress_start: number;
        progress_end: number;
    };
}
