import { motion } from 'framer-motion';

const STEP_LABELS = ['Animal', 'Costs', 'Method', 'Profit', 'Results'];

interface ProgressBarProps {
  step: number;
  total?: number;
}

export function ProgressBar({ step, total = 5 }: ProgressBarProps) {
  const pct = ((step - 1) / (total - 1)) * 100;
  return (
    <div className="container-wizard pt-4 pb-6">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted mb-2">
        <span>
          Step {step} of {total}
        </span>
        <span className="text-navy">{STEP_LABELS[step - 1]}</span>
      </div>
      <div className="relative h-2 w-full rounded-full bg-line overflow-hidden">
        <motion.div
          className="absolute inset-y-0 left-0 bg-gold rounded-full"
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        />
      </div>
      <div className="mt-2 grid grid-cols-5 text-[11px] text-muted">
        {STEP_LABELS.map((label, i) => (
          <span
            key={label}
            className={
              i + 1 <= step
                ? 'text-navy font-semibold'
                : i + 1 === step + 1
                ? 'text-ink'
                : ''
            }
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
