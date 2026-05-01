import type { Config } from 'tailwindcss';
import forms from '@tailwindcss/forms';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#1B3A6B',
        gold: '#B5965A',
        green: { brand: '#16A34A' },
        amber: { brand: '#D97706' },
        red: { brand: '#DC2626' },
        bg: '#F8F6F1',
        ink: '#1A1A1A',
        muted: '#6B6B6B',
        line: '#E5E0D5',
      },
      fontFamily: {
        heading: ['Oswald', 'system-ui', 'sans-serif'],
        body: ['Lato', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(27, 58, 107, 0.06), 0 4px 12px rgba(27, 58, 107, 0.08)',
        pop: '0 8px 24px rgba(27, 58, 107, 0.18)',
      },
      maxWidth: {
        wizard: '720px',
      },
    },
  },
  plugins: [forms({ strategy: 'class' })],
};

export default config;
