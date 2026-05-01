import type { HTMLAttributes } from 'react';
import { cn } from '../../lib/cn';

type Tone = 'navy' | 'gold' | 'green' | 'amber' | 'red' | 'muted';

const TONE: Record<Tone, string> = {
  navy: 'bg-navy/10 text-navy',
  gold: 'bg-gold/15 text-gold',
  green: 'bg-green-brand/10 text-green-brand',
  amber: 'bg-amber-brand/10 text-amber-brand',
  red: 'bg-red-brand/10 text-red-brand',
  muted: 'bg-line text-muted',
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = 'muted', className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide',
        TONE[tone],
        className,
      )}
      {...rest}
    />
  );
}
