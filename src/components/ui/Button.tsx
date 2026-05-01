import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/cn';

type Variant = 'primary' | 'secondary' | 'ghost' | 'gold';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-navy text-white hover:bg-navy/90 active:bg-navy/95 disabled:bg-navy/40',
  secondary:
    'bg-white text-navy border border-navy/20 hover:border-navy/50 hover:bg-navy/5 disabled:opacity-50',
  ghost:
    'bg-transparent text-navy hover:bg-navy/5 disabled:opacity-50',
  gold:
    'bg-gold text-white hover:bg-gold/90 active:bg-gold/95 disabled:bg-gold/40',
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'h-10 px-4 text-sm',
  md: 'h-12 px-5 text-[15px]',
  lg: 'h-14 px-6 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', fullWidth, className, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-heading uppercase tracking-wide font-semibold transition-colors no-tap-highlight disabled:cursor-not-allowed',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        fullWidth && 'w-full',
        className,
      )}
      {...rest}
    />
  );
});
