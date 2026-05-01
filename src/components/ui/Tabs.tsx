import { cn } from '../../lib/cn';

interface Tab<T extends string> {
  value: T;
  label: string;
  badge?: string;
}

interface TabsProps<T extends string> {
  tabs: Tab<T>[];
  value: T;
  onChange: (next: T) => void;
}

export function Tabs<T extends string>({ tabs, value, onChange }: TabsProps<T>) {
  return (
    <div
      role="tablist"
      className="flex gap-1 overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0 scrollbar-none"
    >
      {tabs.map((t) => {
        const active = t.value === value;
        return (
          <button
            key={t.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(t.value)}
            className={cn(
              'shrink-0 px-4 h-11 rounded-lg font-heading uppercase tracking-wide text-sm font-semibold transition-colors',
              active
                ? 'bg-navy text-white'
                : 'bg-white text-muted border border-line hover:text-navy',
            )}
          >
            {t.label}
            {t.badge && (
              <span className="ml-2 rounded-full bg-white/20 px-2 py-0.5 text-xs">{t.badge}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
