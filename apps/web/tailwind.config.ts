import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0b6bcb",
          light: "#0ea5e9",
        },
        accent: "#f59e0b",
        ok: "#16a34a",
        ink: "#0f172a",
        muted: "#475569",
        surface: "#ffffff",
        line: "#dbe2ea",
      },
    },
  },
  plugins: [],
};

export default config;
