/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B1120',
        card: '#1E293B',
        accent: '#10B981',
        'accent-blue': '#3B82F6',
        'accent-pink': '#EC4899',
        'accent-orange': '#F59E0B',
      },
      animation: {
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
