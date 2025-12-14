/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"Space Mono"', 'monospace'],
        sans: ['"Space Mono"', 'monospace'], // Force mono everywhere for this look
      },
      colors: {
        retro: {
          bg: '#050505',      // Void Black
          surface: '#111111', // Dark Gray
          border: '#333333',  // Border Gray
          primary: '#ffb000', // Amber-500 (Classic Terminal)
          secondary: '#00ff41', // Matrix Green (Alternative accent)
          muted: '#666666',
        }
      },
      animation: {
        'blink': 'blink 1s step-end infinite',
        'scan': 'scan 8s linear infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        }
      }
    },
  },
  plugins: [],
}
