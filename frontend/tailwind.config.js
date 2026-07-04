/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c2d3ff',
          300: '#93b4ff',
          400: '#6090ff',
          500: '#3d6fff',
          600: '#2451f5',
          700: '#1c3de1',
          800: '#1d33b6',
          900: '#1d2f8f',
          950: '#151e5f',
        },
        surface: {
          DEFAULT: '#0f1117',
          50: '#1a1d2e',
          100: '#1e2235',
          200: '#252942',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
