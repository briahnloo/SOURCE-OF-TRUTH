/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f0f9ff',
                    100: '#e0f2fe',
                    200: '#bae6fd',
                    300: '#7dd3fc',
                    400: '#38bdf8',
                    500: '#0ea5e9',
                    600: '#0284c7',
                    700: '#0369a1',
                    800: '#075985',
                    900: '#0c4a6e',
                },
                confirmed: {
                    50: '#f0fdf4',
                    100: '#dcfce7',
                    light: '#86efac',
                    DEFAULT: '#22c55e',
                    dark: '#16a34a',
                    900: '#14532d',
                },
                developing: {
                    50: '#fffbeb',
                    100: '#fef3c7',
                    light: '#fcd34d',
                    DEFAULT: '#f59e0b',
                    dark: '#d97706',
                    900: '#78350f',
                },
                accent: {
                    DEFAULT: '#14b8a6',
                    dark: '#0d9488',
                },
            },
            fontFamily: {
                sans: [
                    '-apple-system',
                    'BlinkMacSystemFont',
                    'Inter',
                    'Segoe UI',
                    'Roboto',
                    'Helvetica Neue',
                    'Arial',
                    'sans-serif',
                ],
                mono: [
                    'JetBrains Mono',
                    'Consolas',
                    'Monaco',
                    'Courier New',
                    'monospace',
                ],
            },
            fontSize: {
                'xs': ['0.75rem', { lineHeight: '1rem' }],
                'sm': ['0.875rem', { lineHeight: '1.25rem' }],
                'base': ['1rem', { lineHeight: '1.75rem' }],
                'lg': ['1.125rem', { lineHeight: '1.875rem' }],
                'xl': ['1.25rem', { lineHeight: '2rem' }],
                '2xl': ['1.5rem', { lineHeight: '2.25rem' }],
                '3xl': ['1.875rem', { lineHeight: '2.5rem' }],
                '4xl': ['2.25rem', { lineHeight: '2.75rem', letterSpacing: '-0.025em' }],
                '5xl': ['3rem', { lineHeight: '1.2', letterSpacing: '-0.025em' }],
            },
            boxShadow: {
                'glow-sm': '0 0 10px rgba(34, 197, 94, 0.3)',
                'glow-md': '0 0 20px rgba(34, 197, 94, 0.4)',
                'glow-lg': '0 0 30px rgba(34, 197, 94, 0.5)',
                'lift': '0 10px 40px -10px rgba(0, 0, 0, 0.15)',
                'lift-lg': '0 20px 50px -15px rgba(0, 0, 0, 0.25)',
            },
            animation: {
                'fade-in': 'fadeIn 0.6s ease-in-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'fill': 'fill 1.5s ease-out forwards',
                'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
                'count-up': 'countUp 0.8s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                fill: {
                    '0%': { width: '0%' },
                    '100%': { width: 'var(--fill-width)' },
                },
                pulseGlow: {
                    '0%, 100%': { boxShadow: '0 0 15px rgba(34, 197, 94, 0.3)' },
                    '50%': { boxShadow: '0 0 25px rgba(34, 197, 94, 0.6)' },
                },
            },
        },
    },
    plugins: [],
}
