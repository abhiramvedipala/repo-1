import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0d0f14",
          panel: "#12151c",
          raised: "#181c25",
          border: "#242936",
        },
        text: {
          DEFAULT: "#e6e8ee",
          dim: "#8b93a7",
          faint: "#5a6478",
        },
        accent: {
          DEFAULT: "#6366f1", // indigo-500
          hover: "#818cf8",
          dim: "#3730a3",
        },
        pass: {
          DEFAULT: "#22c55e",
          dim: "#14532d",
        },
        fail: {
          DEFAULT: "#ef4444",
          dim: "#7f1d1d",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
