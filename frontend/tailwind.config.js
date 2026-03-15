/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f8f6ff',
          100: '#f0ecff',
          200: '#e6d9ff',
          300: '#d4b3ff',
          400: '#bb82ff',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7c3aed',
          800: '#6d28d9',
          900: '#5b21b6',
        },
        nepal: {
          red: '#DC143C',
          blue: '#003893',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        nepali: ['Noto Sans Devanagari', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
