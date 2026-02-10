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
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "#4F46E5", // Indigo
          foreground: "#FFFFFF",
        },
        success: {
          DEFAULT: "#10B981", // Green
          foreground: "#FFFFFF",
        },
        warning: {
          DEFAULT: "#F59E0B", // Amber
          foreground: "#FFFFFF",
        },
        danger: {
          DEFAULT: "#EF4444", // Red
          foreground: "#FFFFFF",
        },
      },
    },
  },
  plugins: [],
};
export default config;
