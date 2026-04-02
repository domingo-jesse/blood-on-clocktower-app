/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        midnight: '#070d1f',
        dusk: '#101d37',
        parchment: '#e8d7ad',
        ember: '#d97d5f',
      },
      boxShadow: {
        glow: '0 0 0 2px rgba(219, 179, 87, 0.7), 0 0 26px rgba(106, 150, 255, 0.28)',
      },
      fontFamily: {
        title: ['"Cinzel"', 'serif'],
      },
    },
  },
  plugins: [],
};
