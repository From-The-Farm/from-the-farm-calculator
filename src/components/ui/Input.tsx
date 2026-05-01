import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../lib/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid, className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      className={cn(
        'form-input w-full rounded-lg border bg-white px-3 py-3 text-base text-ink placeholder:text-muted focus:ring-2 focus:ring-gold/40',
        invalid ? 'border-red-brand focus:border-red-brand' : 'border-line focus:border-navy',
        className,
      )}
      {...rest}
    />
  );
});
