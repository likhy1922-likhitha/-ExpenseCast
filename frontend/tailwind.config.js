/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eefcf5', 100: '#d6f7e6', 200: '#adeecd', 300: '#78dfad',
          400: '#42c98a', 500: '#22b072', 600: '#158f5c', 700: '#12724b',
          800: '#125b3d', 900: '#104a34',
        },
        ink: {
          50: '#f7f8fa', 100: '#eceef2', 200: '#d5d9e0', 300: '#aab2c0',
          400: '#78839a', 500: '#57647d', 600: '#434f66', 700: '#374053',
          800: '#252b38', 900: '#171b24',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
