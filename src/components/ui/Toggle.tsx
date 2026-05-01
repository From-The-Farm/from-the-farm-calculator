import { cn } from '../../lib/cn';

interface ToggleProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  label?: string;
  description?: string;
  id?: string;
}

export function Toggle({ checked, onChange, label, description, id }: ToggleProps) {
  return (
    <label
      htmlFor={id}
      className="flex items-start gap-4 cursor-pointer no-tap-highlight"
    >
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors',
          checked ? 'bg-navy' : 'bg-line',
        )}
      >
        <span
          className={cn(
            'inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform',
            checked ? 'translate-x-6' : 'translate-x-1',
          )}
        />
      </button>
      {(label || description) && (
        <span className="flex-1">
          {label && <span className="block font-semibold text-ink leading-tight">{label}</span>}
          {description && (
            <span className="block text-sm text-muted mt-0.5">{description}</span>
          )}
        </span>
      )}
    </label>
  );
}

interface SegmentedProps<T extends string> {
  options: Array<{ value: T; label: string }>;
  value: T;
  onChange: (next: T) => void;
}

export function Segmented<T extends string>({ options, value, onChange }: SegmentedProps<T>) {
  return (
    <div className="inline-flex rounded-lg border border-line bg-white p-1 gap-1">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-semibold transition-colors',
              active ? 'bg-navy text-white' : 'text-muted hover:text-navy',
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
