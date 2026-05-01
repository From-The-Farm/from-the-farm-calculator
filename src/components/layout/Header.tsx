import { Button } from '../ui/Button';

export function Header() {
  return (
    <header className="border-b border-line bg-white">
      <div className="container-wizard h-16 flex items-center justify-between gap-4">
        <a href="/" className="flex items-center gap-3">
          <img src="/ftf-logo.svg" alt="From The Farm" className="h-9 w-auto" />
          <span className="hidden sm:block text-xs font-semibold uppercase tracking-wider text-muted border-l border-line pl-3">
            Pricing Calculator
          </span>
        </a>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" disabled aria-disabled="true" title="Coming soon">
            Save Profile
          </Button>
          <Button variant="secondary" size="sm" disabled aria-disabled="true" title="Coming soon">
            Log In
          </Button>
        </div>
      </div>
    </header>
  );
}
