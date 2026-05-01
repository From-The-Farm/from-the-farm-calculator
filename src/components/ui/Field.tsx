import type { ReactNode } from 'react';
import { Tooltip } from './Tooltip';

interface FieldProps {
  label: string;
  helpText?: ReactNode;
  hint?: string;
  children: ReactNode;
  htmlFor?: string;
}

export function Field({ label, helpText, hint, children, htmlFor }: FieldProps) {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="flex items-center gap-1.5 mb-1.5 text-sm font-semibold text-ink">
        {helpText ? (
          <Tooltip label={label} content={helpText}>
            <span>{label}</span>
          </Tooltip>
        ) : (
          <span>{label}</span>
        )}
      </span>
      {children}
      {hint && <span className="block mt-1 text-xs text-muted">{hint}</span>}
    </label>
  );
}
