import type { ReactNode } from 'react';

interface StepShellProps {
  eyebrow?: string;
  title: string;
  description?: string;
  children: ReactNode;
}

export function StepShell({ eyebrow, title, description, children }: StepShellProps) {
  return (
    <section className="container-wizard pb-8">
      <div className="mb-6">
        {eyebrow && (
          <div className="text-xs font-semibold uppercase tracking-wider text-gold mb-2">
            {eyebrow}
          </div>
        )}
        <h1 className="text-3xl sm:text-4xl text-navy uppercase font-bold leading-tight">
          {title}
        </h1>
        {description && <p className="text-muted mt-2 text-base">{description}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}
