/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg:      '#0a0e1a',
        panel:   '#111827',
        card:    '#1a2235',
        border:  '#1e2d45',
        bordlt:  '#172035',

        brand:   '#00d9a6',
        branddk: '#00b389',
        brandbg: '#00d9a610',

        hi:  '#f85149',
        mid: '#e3b341',
        lo:  '#3fb950',

        muted: '#8b949e',
        dim:   '#3d4d63',

        accent: '#6366f1',
        accentlt: '#6366f115',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      animation: {
        'blink':     'blink 1.5s ease-in-out infinite',
        'scan':      'scan 2.2s ease-in-out infinite',
        'fade-up':   'fadeUp .4s ease both',
        'fade-in':   'fadeIn .3s ease both',
        'slide-in':  'slideIn .4s cubic-bezier(.16,1,.3,1) both',
        'float':     'float 6s ease-in-out infinite',
        'shimmer':   'shimmer 2.5s linear infinite',
        'pulse-brand': 'pulseBrand 2s ease-in-out infinite',
        'spin-slow':   'spin 8s linear infinite',
      },
      keyframes: {
        blink:      { '0%,100%': {opacity:'1'}, '50%': {opacity:'0.2'} },
        fadeUp:     { from:{opacity:'0',transform:'translateY(12px)'}, to:{opacity:'1',transform:'translateY(0)'} },
        fadeIn:     { from:{opacity:'0'}, to:{opacity:'1'} },
        slideIn:    { from:{opacity:'0',transform:'translateX(-16px)'}, to:{opacity:'1',transform:'translateX(0)'} },
        float:      { '0%,100%':{transform:'translateY(0)'}, '50%':{transform:'translateY(-10px)'} },
        shimmer:    { '0%':{backgroundPosition:'-200% 0'}, '100%':{backgroundPosition:'200% 0'} },
        pulseBrand: { '0%,100%':{boxShadow:'0 0 0 0 rgba(0,217,166,.35)'}, '50%':{boxShadow:'0 0 0 10px rgba(0,217,166,0)'} },
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #00d9a6 0%, #6366f1 100%)',
        'gradient-hero':  'radial-gradient(ellipse at 60% 0%, #00d9a615 0%, transparent 60%), radial-gradient(ellipse at 10% 80%, #6366f110 0%, transparent 50%)',
      },
      boxShadow: {
        'glow-brand': '0 0 20px rgba(0,217,166,.25)',
        'glow-hi':    '0 0 20px rgba(248,81,73,.25)',
        'card':       '0 4px 24px rgba(0,0,0,.35)',
        'card-hover': '0 8px 40px rgba(0,0,0,.5)',
      },
    },
  },
  plugins: [],
}
