# From The Farm Pricing Calculator

A 5-step wizard that helps small/mid farmers arrive at a defensible price-per-pound for direct-to-consumer meat sales. Public-facing lead-magnet for the From The Farm platform.

## Design Context

Strategic context lives in [PRODUCT.md](./PRODUCT.md) — register, users, brand personality, anti-references, design principles, accessibility. Read it before any design or copy work.

Visual system lives in [DESIGN.md](./DESIGN.md) (when present) — colors, typography, components, motion. Tokens are also defined in `tailwind.config.ts` and `src/index.css`.

For design tasks, prefer the `/impeccable` skill at `.claude/skills/impeccable/`. It enforces context loading, register-aware references, and craft gates.

## Stack

- React 18 + TypeScript + Vite
- Tailwind CSS 3 (`@tailwindcss/forms`)
- Framer Motion (interaction motion)
- React Hook Form + Zod (form state and validation)
- Recharts (results charts)
- jsPDF, canvas-confetti (export and celebration)

## Structure

- `src/components/wizard/` — the 5 step components and `WizardRouter`
- `src/components/ui/` — primitives (`Button`, `Card`, `Field`, `NumberInput`, `Select`, `Toggle`, `Tooltip`, etc.)
- `src/components/layout/` — `Header`, `Footer`, `ProgressBar`
- `src/context/CalculatorContext.tsx` — wizard state
- `src/lib/animalDefaults.ts` — sensible per-animal defaults (the spirit of the tool)
- `src/lib/calculator.ts` — pricing math
