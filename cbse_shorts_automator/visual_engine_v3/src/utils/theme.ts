export const THEMES = [
    { name: "Cyber Slime", bg: ["#0a0e17", "#000000"], primary: "#00FF41", secondary: "#9D00FF", rim: "#FFFFFF" },
    { name: "Deep Indigo", bg: ["#0f0f20", "#020205"], primary: "#00F3FF", secondary: "#FF0055", rim: "#FFD700" },
    { name: "Solar Flare", bg: ["#1a0505", "#000000"], primary: "#FF4800", secondary: "#FFD500", rim: "#00FFFF" },
    { name: "Royal Gold",  bg: ["#1a1a1a", "#000000"], primary: "#FFD700", secondary: "#FFFFFF", rim: "#FF00FF" },
    { name: "Mint Fresh",  bg: ["#051a15", "#000000"], primary: "#00FFAA", secondary: "#00AAFF", rim: "#FFFFFF" }
];

export const getTheme = (seed: number) => {
    const index = seed % THEMES.length;
    return THEMES[index];
};

export const getVariant = (seed: number) => {
    // 0 = Elastic Pop/Bubbles, 1 = Slide/Rain, 2 = Vortex/Dust
    return seed % 3;
};
