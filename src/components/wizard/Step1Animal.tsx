import { motion } from 'framer-motion';
import { useCalculator } from '../../context/CalculatorContext';
import { ANIMAL_LIST } from '../../lib/animalDefaults';
import { StepShell } from './StepShell';
import { NavButtons } from './NavButtons';
import { Field } from '../ui/Field';
import { NumberInput } from '../ui/NumberInput';
import { Toggle } from '../ui/Toggle';
import { cn } from '../../lib/cn';

export function Step1Animal() {
  const { state, setAnimal, updateStep1, next } = useCalculator();
  const { step1 } = state;

  const canContinue =
    step1.animal !== null &&
    step1.liveWeight > 0 &&
    step1.carcassYield > 0 &&
    step1.numAnimals > 0;

  return (
    <StepShell
      eyebrow="Step 1 of 5"
      title="Pick your animal"
      description="Choose what you're pricing — we'll auto-fill smart defaults you can adjust."
    >
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {ANIMAL_LIST.map((a) => {
          const active = step1.animal === a.key;
          return (
            <motion.button
              key={a.key}
              type="button"
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              transition={{ type: 'spring', stiffness: 400, damping: 22 }}
              onClick={() => setAnimal(a.key)}
              className={cn(
                'flex flex-col items-center justify-center gap-2 rounded-lg border bg-white p-4 transition-colors no-tap-highlight min-h-[112px]',
                active
                  ? 'border-gold ring-2 ring-gold/40 shadow-card'
                  : 'border-line hover:border-navy/40',
              )}
            >
              <span className="text-3xl leading-none" aria-hidden="true">
                {a.emoji}
              </span>
              <span className="font-heading uppercase tracking-wide text-sm text-navy">
                {a.label}
              </span>
            </motion.button>
          );
        })}
      </div>

      <div className="mt-8 grid sm:grid-cols-2 gap-5">
        <Field
          label="Live Weight"
          helpText="The animal's weight at slaughter, before processing. Typical: beef 1,200 lbs, hog 250 lbs, lamb 120 lbs."
        >
          <NumberInput
            value={step1.liveWeight}
            onChange={(v) => updateStep1({ liveWeight: v })}
            suffix="lbs"
            decimals
          />
        </Field>

        <Field
          label="Carcass Yield"
          helpText="Percent of live weight that becomes hanging carcass after slaughter. Typical: beef 62%, hog 72%, lamb/goat 50%, poultry 72–78%."
        >
          <NumberInput
            value={Number((step1.carcassYield * 100).toFixed(2))}
            onChange={(v) =>
              updateStep1({ carcassYield: Math.max(0, Math.min(100, v)) / 100 })
            }
            suffix="%"
          />
        </Field>

        <Field
          label="Number of Animals"
          helpText="How many animals are in this batch? Smaller poultry batches typically include more birds."
        >
          <NumberInput
            value={step1.numAnimals}
            onChange={(v) => updateStep1({ numAnimals: Math.max(1, v) })}
          />
        </Field>

        <div className="sm:col-span-1 flex items-center">
          <Toggle
            checked={step1.premiumProduction}
            onChange={(v) => updateStep1({ premiumProduction: v })}
            label="Premium production"
            description="Grass-finished, certified organic, or other specialty practices. Adds a 12% premium."
          />
        </div>
      </div>

      <NavButtons onNext={next} hideBack nextDisabled={!canContinue} />
    </StepShell>
  );
}
