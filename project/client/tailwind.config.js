/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      animation: {
        glow: "glow 3s ease-in-out infinite",
        twinkle: "twinkle 5s ease-in-out infinite",
        'stripe-illuminate': "stripe-illuminate 6s ease-in-out infinite",
      },
      keyframes: {
        glow: {
          "0%, 100%": { textShadow: "0 0 10px rgba(229, 57, 53, 0.5)" },
          "50%": { textShadow: "0 0 30px rgba(229, 57, 53, 0.8)" },
        },
        twinkle: {
          "0%, 100%": { opacity: "0.2" },
          "50%": { opacity: "0.5" },
        },
        'stripe-illuminate': {
          "0%, 100%": { filter: "brightness(1) drop-shadow(0 0 0px #e53935)" },
          "50%": { filter: "brightness(1.5) drop-shadow(0 0 20px #e53935)" },
        },
      },
    },
  },
  plugins: [],
}

