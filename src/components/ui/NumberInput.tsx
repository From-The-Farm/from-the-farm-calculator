import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../lib/cn';

interface NumberInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'type'> {
  value: number;
  onChange: (value: number) => void;
  prefix?: string;
  suffix?: string;
  decimals?: boolean;
  invalid?: boolean;
}

function strip(raw: string, decimals: boolean): number {
  if (raw === '' || raw === '-') return 0;
  const cleaned = decimals ? raw.replace(/[^\d.-]/g, '') : raw.replace(/[^\d-]/g, '');
  const n = decimals ? parseFloat(cleaned) : parseInt(cleaned, 10);
  return Number.isFinite(n) ? n : 0;
}

export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(function NumberInput(
  { value, onChange, prefix, suffix, decimals = false, invalid, className, ...rest },
  ref,
) {
  return (
    <div
      className={cn(
        'flex items-stretch w-full rounded-lg border bg-white overflow-hidden focus-within:ring-2 focus-within:ring-gold focus-within:ring-offset-1 focus-within:ring-offset-bg',
        invalid ? 'border-red-brand' : 'border-line',
      )}
    >
      {prefix && (
        <span className="flex items-center px-3 text-muted bg-bg/60 border-r border-line text-sm">
          {prefix}
        </span>
      )}
      <input
        ref={ref}
        type="text"
        inputMode={decimals ? 'decimal' : 'numeric'}
        className={cn(
          'min-w-0 flex-1 px-3 py-3 text-base text-ink placeholder:text-muted outline-none bg-transparent',
          className,
        )}
        value={Number.isFinite(value) ? String(value) : ''}
        onChange={(e) => onChange(strip(e.target.value, decimals))}
        onFocus={(e) => e.currentTarget.select()}
        {...rest}
      />
      {suffix && (
        <span className="flex items-center px-3 text-muted bg-bg/60 border-l border-line text-sm">
          {suffix}
        </span>
      )}
    </div>
  );
});
