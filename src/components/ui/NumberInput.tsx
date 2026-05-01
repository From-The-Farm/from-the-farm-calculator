import {
  forwardRef,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FocusEvent,
  type InputHTMLAttributes,
} from 'react';
import { cn } from '../../lib/cn';

interface NumberInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange' | 'type'> {
  value: number;
  onChange: (value: number) => void;
  prefix?: string;
  suffix?: string;
  /** @deprecated decimals are always supported now */
  decimals?: boolean;
  invalid?: boolean;
}

function format(n: number): string {
  if (!Number.isFinite(n)) return '';
  return String(n);
}

// Sanitize a raw input string into a valid intermediate decimal state.
// Allows: digits, a single dot, an optional leading minus.
function clean(raw: string): string {
  let s = raw.replace(/[^\d.-]/g, '');
  const isNeg = s.startsWith('-');
  s = s.replace(/-/g, '');
  const dotIdx = s.indexOf('.');
  if (dotIdx !== -1) {
    s = s.slice(0, dotIdx + 1) + s.slice(dotIdx + 1).replace(/\./g, '');
  }
  return (isNeg ? '-' : '') + s;
}

// Parse a draft string to a number; returns null for partial states like '', '.', '-', '-.'
function parseDraft(s: string): number | null {
  if (s === '' || s === '.' || s === '-' || s === '-.') return null;
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : null;
}

export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(function NumberInput(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  { value, onChange, prefix, suffix, decimals, invalid, className, ...rest },
  ref,
) {
  const focusedRef = useRef(false);
  const [draft, setDraft] = useState(() => format(value));

  // When value changes externally and the input isn't focused, sync draft.
  useEffect(() => {
    if (!focusedRef.current) {
      setDraft(format(value));
    }
  }, [value]);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const cleaned = clean(e.target.value);
    setDraft(cleaned);
    const parsed = parseDraft(cleaned);
    if (parsed !== null) {
      onChange(parsed);
    } else if (cleaned === '') {
      onChange(0);
    }
    // For intermediate states like '95.' or '-', keep the draft, don't propagate.
  };

  const handleFocus = (e: FocusEvent<HTMLInputElement>) => {
    focusedRef.current = true;
    e.currentTarget.select();
  };

  const handleBlur = () => {
    focusedRef.current = false;
    const parsed = parseDraft(draft);
    const finalVal = parsed ?? 0;
    setDraft(format(finalVal));
    if (parsed === null) onChange(finalVal);
  };

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
        inputMode="decimal"
        className={cn(
          'min-w-0 flex-1 px-3 py-3 text-base text-ink placeholder:text-muted outline-none bg-transparent',
          className,
        )}
        value={draft}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
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
