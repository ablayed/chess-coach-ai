import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          cyan: "#06b6d4",
          good: "#22c55e",
          inaccuracy: "#eab308",
          mistake: "#f97316",
          blunder: "#ef4444",
        },
      },
      boxShadow: {
        card: "0 8px 24px rgba(0, 0, 0, 0.24)",
      },
    },
  },
  plugins: [],
};

export default config;
