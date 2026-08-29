/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#070a13',
        card: '#0d1322',
        cardBorder: '#1c2740',
        brandCyan: '#06b6d4',
        brandEmerald: '#10b981',
        brandRose: '#f43f5e',
        brandAmber: '#f59e0b',
        brandIndigo: '#6366f1',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
};
