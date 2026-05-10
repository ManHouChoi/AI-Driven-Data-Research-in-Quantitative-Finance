import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/stores/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        mercury: {
          blue: "#5266eb",
          ghost: "#cdddff",
          abyss: "#ffffff",
          slate: "#f5f5f7",
          graphite: "#ffffff",
          lead: "#d2d2d7",
          starlight: "#1d1d1f",
          silver: "#707070"
        },
        apple: {
          ink: "#1d1d1f",
          fog: "#f5f5f7",
          snow: "#ffffff",
          mist: "#e8e8ed",
          graphite: "#707070"
        }
      },
      fontFamily: {
        display: ["Inter", "Manrope", "ui-sans-serif", "system-ui"],
        body: ["Inter", "Manrope", "ui-sans-serif", "system-ui"],
        mono: ["SFMono-Regular", "Consolas", "Liberation Mono", "monospace"]
      }
    }
  },
  plugins: []
};

export default config;
