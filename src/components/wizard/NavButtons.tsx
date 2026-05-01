import { Button } from '../ui/Button';

interface NavButtonsProps {
  onBack?: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  hideBack?: boolean;
}

export function NavButtons({
  onBack,
  onNext,
  nextLabel = 'Continue',
  nextDisabled,
  hideBack,
}: NavButtonsProps) {
  return (
    <div className="mt-8 flex items-center justify-between gap-3">
      {!hideBack ? (
        <Button variant="ghost" onClick={onBack}>
          ← Back
        </Button>
      ) : (
        <span />
      )}
      <Button variant="primary" size="lg" onClick={onNext} disabled={nextDisabled}>
        {nextLabel} →
      </Button>
    </div>
  );
}
