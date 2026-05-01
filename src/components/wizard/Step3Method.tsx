import { motion } from 'framer-motion';
import { useCalculator } from '../../context/CalculatorContext';
import { StepShell } from './StepShell';
import { NavButtons } from './NavButtons';
import { Field } from '../ui/Field';
import { NumberInput } from '../ui/NumberInput';
import { cn } from '../../lib/cn';
import type { SellingMethod } from '../../lib/types';

interface MethodOption {
  value: SellingMethod;
  label: string;
  emoji: string;
  blurb: string;
  detail: string;
}

const METHODS: MethodOption[] = [
  {
    value: 'cut',
    label: 'By the Cut',
    emoji: '🥩',
    blurb: 'Sell individual cuts at retail-style prices.',
    detail:
      'Highest revenue per pound. Best for online stores, farmers markets, and small repeat orders. Requires more inventory management.',
  },
  {
    value: 'bulk',
    label: 'In Bulk',
    emoji: '📦',
    blurb: 'Whole, half, or quarter animals — sold by hanging weight.',
    detail:
      'Simpler to fulfill and great for freezer-stocking customers. Lower price per pound but moves volume fast.',
  },
  {
    value: 'bundle',
    label: 'Curated Bundles',
    emoji: '🎁',
    blurb: 'Mixed boxes priced as a single unit.',
    detail:
      'Predictable AOV and a low decision-fatigue option for first-time buyers. Lets you balance high- and low-margin cuts.',
  },
];

export function Step3Method() {
  const { state, updateStep3, back, next } = useCalculator();
  const { step3 } = state;

  return (
    <StepShell
      eyebrow="Step 3 of 5"
      title="How are you selling?"
      description="Different channels expect different price points. Pick the model that matches your customer."
    >
      <div className="grid gap-3 sm:grid-cols-3">
        {METHODS.map((m) => {
          const active = step3.method === m.value;
          return (
            <motion.button
              key={m.value}
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: 'spring', stiffness: 400, damping: 24 }}
              onClick={() => updateStep3({ method: m.value })}
              className={cn(
                'flex flex-col gap-2 rounded-lg border bg-white p-5 text-left transition-colors no-tap-highlight',
                active
                  ? 'border-gold ring-2 ring-gold/40 shadow-card'
                  : 'border-line hover:border-navy/40',
              )}
            >
              <span className="text-3xl leading-none" aria-hidden="true">
                {m.emoji}
              </span>
              <span className="font-heading uppercase tracking-wide text-base text-navy">
                {m.label}
              </span>
              <span className="text-sm text-muted leading-snug">{m.blurb}</span>
            </motion.button>
          );
        })}
      </div>

      <div className="mt-5 rounded-lg border border-line bg-white/60 p-4 text-sm text-ink">
        {METHODS.find((m) => m.value === step3.method)?.detail}
      </div>

      {step3.method === 'bundle' && (
        <div className="mt-6 grid sm:grid-cols-2 gap-5">
          <Field
            label="Average Bundle Weight"
            helpText="Total pounds in a typical bundle/box. We'll use this to estimate how many bundles you can build from this batch."
          >
            <NumberInput
              suffix="lbs"
              decimals
              value={step3.bundleWeight}
              onChange={(v) => updateStep3({ bundleWeight: Math.max(0, v) })}
            />
          </Field>
        </div>
      )}

      <NavButtons onBack={back} onNext={next} />
    </StepShell>
  );
}
