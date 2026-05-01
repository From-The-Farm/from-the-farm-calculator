import { useMemo } from 'react';
import { useCalculator } from '../../context/CalculatorContext';
import { StepShell } from './StepShell';
import { NavButtons } from './NavButtons';
import { Field } from '../ui/Field';
import { NumberInput } from '../ui/NumberInput';
import { Segmented } from '../ui/Toggle';
import { calculate } from '../../lib/calculator';
import { fmtCurrency, fmtCurrency2, fmtPct } from '../../lib/formatters';
import type { ProfitMode } from '../../lib/types';

const MODE_OPTIONS: Array<{ value: ProfitMode; label: string }> = [
  { value: 'percent', label: 'Margin %' },
  { value: 'dollar', label: 'Dollar profit' },
];

export function Step4Profit() {
  const { state, input, updateStep4, back, next } = useCalculator();
  const { step4 } = state;

  const preview = useMemo(() => calculate(input), [input]);

  return (
    <StepShell
      eyebrow="Step 4 of 5"
      title="Your profit goal"
      description="Tell us how much you want to make on this batch — we'll back-solve the price."
    >
      <div className="flex justify-center">
        <Segmented
          options={MODE_OPTIONS}
          value={step4.mode}
          onChange={(mode) => updateStep4({ mode })}
        />
      </div>

      <div className="mt-6 grid sm:grid-cols-2 gap-5">
        {step4.mode === 'percent' ? (
          <Field
            label="Target Margin"
            helpText="What percent of every dollar of revenue should be profit? 25–35% is a healthy range for direct-to-consumer farms."
          >
            <NumberInput
              suffix="%"
              decimals
              value={step4.profitPct}
              onChange={(v) =>
                updateStep4({ profitPct: Math.max(0, Math.min(95, v)) })
              }
            />
          </Field>
        ) : (
          <Field
            label="Target Profit (per batch)"
            helpText="Total dollars of profit you want from this batch after every cost is paid."
          >
            <NumberInput
              prefix="$"
              value={step4.profitDollar}
              onChange={(v) => updateStep4({ profitDollar: Math.max(0, v) })}
            />
          </Field>
        )}
      </div>

      <div className="mt-8 rounded-lg border border-line bg-white shadow-card p-5 sm:p-6">
        <div className="text-xs font-semibold uppercase tracking-wider text-gold mb-3">
          Live preview
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Stat label="Recommended price" value={fmtCurrency2(preview.recommendedPricePerLb)} suffix="/lb" />
          <Stat label="Total revenue" value={fmtCurrency(preview.grossRevenue)} />
          <Stat label="Net profit" value={fmtCurrency(preview.netProfit)} />
          <Stat label="Margin" value={fmtPct(preview.marginPct)} />
        </div>
      </div>

      <NavButtons onBack={back} onNext={next} nextLabel="See results" />
    </StepShell>
  );
}

function Stat({ label, value, suffix }: { label: string; value: string; suffix?: string }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 text-xl font-bold text-navy leading-tight">
        {value}
        {suffix && <span className="text-sm text-muted font-semibold ml-0.5">{suffix}</span>}
      </div>
    </div>
  );
}
