/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'enacom-blue-dark': '#002f6c',
        'enacom-blue-main': '#0050b3',
        'enacom-blue-mid': '#0066cc',
        'enacom-blue-soft': '#e6f0ff',
        'enacom-amber': '#d97706',
        'enacom-green': '#15803d',
        'enacom-green-soft': '#dcfce7',
        'enacom-red': '#dc2626',
        'enacom-red-soft': '#fee2e2',
      },
      borderRadius: {
        'enacom': '0.75rem',
        'enacom-sm': '0.5rem',
      },
      boxShadow: {
        'enacom-sm': '0 2px 8px rgba(0, 47, 108, 0.08)',
        'enacom-blue': '0 4px 12px rgba(0, 80, 179, 0.15)',
      },
      fontFamily: {
        'ui': ['Barlow', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
