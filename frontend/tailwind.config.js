/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                void: {
                    bg: '#000105',
                    text: '#ffffff',
                    accent: '#3b82f6',
                }
            },
            fontFamily: {
                jetbrains: ['JetBrains Mono', 'monospace'],
            },
            backdropBlur: {
                xs: '2px',
            }
        },
    },
    plugins: [],
}
