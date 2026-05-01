import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from 'react';
import { animate, motion, useMotionValue, useReducedMotion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { useCalculator } from '../../context/CalculatorContext';
import {
  buildComparison,
  buildCostSlices,
  buildCutList,
  buildPriceTiers,
  buildShippingStrategy,
  calculate,
  type Cut,
  type CutGroup,
  type CutListResult,
  type CostSlice,
  type PriceTier,
  type ShippingStrategy,
} from '../../lib/calculator';
import { ANIMAL_PROFILES } from '../../lib/animalDefaults';
import {
  fmtCurrency,
  fmtCurrency2,
  fmtLbs,
  fmtLbs1,
  fmtPct,
} from '../../lib/formatters';
import { exportPricingPdf } from '../../lib/pdf';
import { captureLead } from '../../lib/leadCapture';
import type {
  AnimalKey,
  CalculatorResult,
  ChannelComparison,
} from '../../lib/types';
import { StepShell } from './StepShell';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { cn } from '../../lib/cn';

const HIGH_PRICE_THRESHOLD: Record<AnimalKey, number> = {
  beef: 25,
  hog: 20,
  lamb: 30,
  goat: 35,
  chicken: 20,
  turkey: 20,
};

type MarginTier = 'healthy' | 'thin' | 'loss';

function marginTier(pct: number): MarginTier {
  if (pct <= 0) return 'loss';
  if (pct < 20) return 'thin';
  return 'healthy';
}

const MARGIN_COPY: Record<MarginTier, string> = {
  healthy: 'Healthy margin',
  thin: 'Thin margin',
  loss: 'Below cost',
};

const MARGIN_CLASSES: Record<MarginTier, string> = {
  healthy: 'bg-green-brand/10 text-green-brand',
  thin: 'bg-amber-brand/15 text-amber-brand',
  loss: 'bg-red-brand/10 text-red-brand',
};

function tierGlyph(tier: MarginTier): string {
  if (tier === 'healthy') return '●';
  if (tier === 'thin') return '◐';
  return '○';
}

export function Step5Results() {
  const {
    state,
    input,
    back,
    reset,
    jumpTo,
    setCutOverride,
    resetCutOverrides,
  } = useCalculator();
  const animal = state.step1.animal;

  const result = useMemo<CalculatorResult>(() => calculate(input), [input]);
  const slices = useMemo(() => buildCostSlices(result), [result]);
  const channels = useMemo(() => buildComparison(result), [result]);
  const tiers = useMemo(() => buildPriceTiers(input, result), [input, result]);
  const shipping = useMemo(
    () => buildShippingStrategy(input, result),
    [input, result],
  );
  const cutList = useMemo(
    () => buildCutList(animal, result, state.step5.cutOverrides),
    [animal, result, state.step5.cutOverrides],
  );

  const [leadEmail, setLeadEmail] = useState('');

  const isEmpty =
    animal === null ||
    !Number.isFinite(result.recommendedPricePerLb) ||
    result.totalPackagedLbs <= 0;

  if (isEmpty) {
    return <EmptyResult onStart={reset} />;
  }

  return (
    <ResultScreen
      result={result}
      slices={slices}
      channels={channels}
      tiers={tiers}
      shipping={shipping}
      cutList={cutList}
      animal={animal as AnimalKey}
      premium={state.step1.premiumProduction}
      leadEmail={leadEmail}
      onLeadEmail={setLeadEmail}
      onSetCutOverride={setCutOverride}
      onResetCutOverrides={resetCutOverrides}
      onBack={back}
      onReset={reset}
      onEditStep={jumpTo}
      onDownloadPdf={() =>
        exportPricingPdf({ input, result, channels, slices, cutList })
      }
    />
  );
}

function EmptyResult({ onStart }: { onStart: () => void }) {
  return (
    <StepShell
      eyebrow="Step 5 of 5"
      title="Let's pick an animal first"
      description="The wizard hasn't been completed yet, so there's no price to recommend. Start at Step 1 and we'll do the math together."
    >
      <div className="rounded-lg border border-line bg-white shadow-card p-6 sm:p-10">
        <p className="text-base text-ink leading-relaxed max-w-prose">
          The pricing calculator works step by step: animal, costs, selling
          method, profit target, then the recommended price. Each step has
          smart defaults so you're adjusting numbers, not sourcing them.
        </p>
        <div className="mt-6">
          <Button variant="primary" onClick={onStart}>
            Start the calculator
          </Button>
        </div>
      </div>
    </StepShell>
  );
}

interface ResultScreenProps {
  result: CalculatorResult;
  slices: CostSlice[];
  channels: ChannelComparison[];
  tiers: { low: PriceTier; medium: PriceTier; high: PriceTier };
  shipping: ShippingStrategy;
  cutList: CutListResult | null;
  animal: AnimalKey;
  premium: boolean;
  leadEmail: string;
  onLeadEmail: (email: string) => void;
  onSetCutOverride: (cutId: string, price: number | null) => void;
  onResetCutOverrides: () => void;
  onBack: () => void;
  onReset: () => void;
  onEditStep: (step: 1 | 2 | 3 | 4 | 5) => void;
  onDownloadPdf: () => void;
}

function ResultScreen({
  result,
  slices,
  channels,
  tiers,
  shipping,
  cutList,
  animal,
  premium,
  leadEmail,
  onLeadEmail,
  onSetCutOverride,
  onResetCutOverrides,
  onBack,
  onReset,
  onEditStep,
  onDownloadPdf,
}: ResultScreenProps) {
  const profile = ANIMAL_PROFILES[animal];
  const tier = marginTier(result.marginPct);
  const reduceMotion = useReducedMotion() ?? false;
  const [revealed, setRevealed] = useState(reduceMotion);
  const onRevealComplete = useCallback(() => setRevealed(true), []);
  const highPrice =
    result.recommendedPricePerLb > (HIGH_PRICE_THRESHOLD[animal] ?? Infinity);

  const firedConfetti = useRef(false);
  useEffect(() => {
    if (reduceMotion) return;
    if (firedConfetti.current) return;
    const t = window.setTimeout(() => {
      firedConfetti.current = true;
      confetti({
        particleCount: 70,
        spread: 60,
        startVelocity: 32,
        origin: { x: 0.3, y: 0.3 },
        colors: ['#B5965A', '#1B3A6B', '#D8C088'],
        scalar: 0.9,
        ticks: 200,
        disableForReducedMotion: true,
      });
    }, 820);
    return () => window.clearTimeout(t);
  }, [reduceMotion]);

  return (
    <StepShell
      eyebrow={`Step 5 of 5 · ${profile.label} pricing`}
      title="Your recommended price"
      description="Here's the per-pound number we'd back, with the math behind it. Edit any cost to see it move in real time."
    >
      <Hero
        result={result}
        tier={tier}
        animal={animal}
        premium={premium}
        highPrice={highPrice}
        reduceMotion={reduceMotion}
        onRevealComplete={onRevealComplete}
        onEditMargin={() => onEditStep(4)}
      />

      <RevealLayer revealed={revealed} className="mt-10 sm:mt-12 space-y-8">
        <PricingOptions
          tiers={tiers}
          onEditMargin={() => onEditStep(4)}
        />

        <ShippingStrategyCard
          shipping={shipping}
          onEditShipping={() => onEditStep(2)}
        />

        {cutList && (
          <CutList
            cutList={cutList}
            animal={animal}
            onSetOverride={onSetCutOverride}
            onResetOverrides={onResetCutOverrides}
          />
        )}

        <CostBreakdown
          slices={slices}
          totalCosts={result.totalCosts}
          onEditCosts={() => onEditStep(2)}
        />

        <ChannelComparisonCard channels={channels} animal={animal} />

        <SaveCard
          leadEmail={leadEmail}
          onLeadEmail={onLeadEmail}
          onDownloadPdf={onDownloadPdf}
        />

        <Assumptions premium={premium} />

        <FooterActions onBack={onBack} onReset={onReset} />
      </RevealLayer>
    </StepShell>
  );
}

function RevealLayer({
  revealed,
  className,
  children,
}: {
  revealed: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <motion.div
      className={className}
      initial={false}
      animate={{ opacity: revealed ? 1 : 0, y: revealed ? 0 : 8 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

interface HeroProps {
  result: CalculatorResult;
  tier: MarginTier;
  animal: AnimalKey;
  premium: boolean;
  highPrice: boolean;
  reduceMotion: boolean;
  onRevealComplete: () => void;
  onEditMargin: () => void;
}

function Hero({
  result,
  tier,
  animal,
  premium,
  highPrice,
  reduceMotion,
  onRevealComplete,
  onEditMargin,
}: HeroProps) {
  return (
    <section className="relative">
      <div className="flex flex-col items-start text-left">
        <PriceNumber
          value={result.recommendedPricePerLb}
          reduceMotion={reduceMotion}
          onComplete={onRevealComplete}
        />

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onEditMargin}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider transition-colors',
              MARGIN_CLASSES[tier],
              'hover:underline underline-offset-4 decoration-current focus:outline-none focus-visible:ring-2 focus-visible:ring-gold ring-offset-2 ring-offset-bg',
            )}
            aria-label={`${MARGIN_COPY[tier]}, ${fmtPct(result.marginPct)}. Edit profit target.`}
            title="Edit profit target"
          >
            <span aria-hidden="true">{tierGlyph(tier)}</span>
            <span>
              {MARGIN_COPY[tier]} · {fmtPct(result.marginPct)}
            </span>
          </button>
          <span className="text-muted text-sm">
            on{' '}
            <strong className="text-ink font-semibold">
              {fmtLbs(result.totalPackagedLbs)}
            </strong>{' '}
            packaged
          </span>
          {premium && (
            <span className="inline-flex items-center rounded-full border border-gold/40 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gold">
              Premium +12%
            </span>
          )}
        </div>

        {highPrice && (
          <p className="mt-3 max-w-md text-sm text-amber-brand">
            This is on the high end for {ANIMAL_PROFILES[animal].label.toLowerCase()}.
            Worth a second look at your inputs before you send a quote.
          </p>
        )}

        {tier === 'loss' && (
          <p className="mt-3 max-w-md text-sm text-red-brand">
            Your recommended price is below cost. Try lowering a cost above or
            raising your target margin in Step 4.
          </p>
        )}
      </div>

      <KpiStrip result={result} />
    </section>
  );
}

function PriceNumber({
  value,
  reduceMotion,
  onComplete,
}: {
  value: number;
  reduceMotion: boolean;
  onComplete: () => void;
}) {
  const mv = useMotionValue(reduceMotion ? value : 0);
  const [display, setDisplay] = useState(reduceMotion ? value : 0);

  useEffect(() => {
    if (reduceMotion) {
      setDisplay(value);
      onComplete();
      return;
    }
    mv.set(0);
    const controls = animate(mv, value, {
      duration: 0.95,
      ease: [0.16, 1, 0.3, 1],
      onComplete,
    });
    const unsub = mv.on('change', (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsub();
    };
  }, [value, reduceMotion, mv, onComplete]);

  return (
    <div className="flex items-baseline">
      <span
        className={cn(
          'font-heading font-bold leading-none text-navy tabular-nums tracking-tight',
          'text-[80px] sm:text-[120px]',
        )}
      >
        {fmtCurrency2(display)}
      </span>
      <span className="ml-2 text-2xl sm:text-4xl font-heading font-semibold text-muted">
        / lb
      </span>
    </div>
  );
}

function KpiStrip({ result }: { result: CalculatorResult }) {
  const items = [
    { label: 'Cost per lb', value: fmtCurrency2(result.costPerLb) },
    { label: 'Profit this batch', value: fmtCurrency(result.netProfit) },
    { label: 'Packaged', value: fmtLbs(result.totalPackagedLbs) },
  ];
  return (
    <div className="mt-8 grid grid-cols-3 divide-x divide-line rounded-lg border border-line bg-white shadow-card">
      {items.map((item) => (
        <div key={item.label} className="px-3 sm:px-5 py-4">
          <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-[0.1em] text-muted">
            {item.label}
          </div>
          <div className="mt-1 text-xl sm:text-2xl font-heading font-semibold text-navy tabular-nums">
            {item.value}
          </div>
        </div>
      ))}
    </div>
  );
}

interface TierCopy {
  label: string;
  story: string;
}

const TIER_COPY: Record<PriceTier['key'], TierCopy> = {
  low: {
    label: 'Low',
    story: 'Tighter margin, faster turn. Good for clearing freezer space or testing a new market.',
  },
  medium: {
    label: 'Recommended',
    story: "Your target margin. The number we'd back as a fair, defensible price.",
  },
  high: {
    label: 'High',
    story: 'Premium positioning. Slower sell, higher per-pound profit when buyers value the story.',
  },
};

function PricingOptions({
  tiers,
  onEditMargin,
}: {
  tiers: { low: PriceTier; medium: PriceTier; high: PriceTier };
  onEditMargin: () => void;
}) {
  const ordered: PriceTier[] = [tiers.low, tiers.medium, tiers.high];
  return (
    <section className="rounded-lg border border-line bg-white shadow-card overflow-hidden">
      <div className="px-5 sm:px-6 pt-5 sm:pt-6 pb-3 border-b border-line flex items-baseline justify-between gap-3">
        <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy">
          Pricing options
        </h2>
        <button
          type="button"
          onClick={onEditMargin}
          className="text-xs sm:text-sm text-muted hover:text-navy underline underline-offset-4 decoration-line focus:outline-none focus-visible:text-navy"
        >
          Edit target margin
        </button>
      </div>
      <ul className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-line">
        {ordered.map((tier) => {
          const copy = TIER_COPY[tier.key];
          const isMid = tier.key === 'medium';
          return (
            <li
              key={tier.key}
              className={cn(
                'relative px-5 sm:px-6 py-5 sm:py-6 flex flex-col gap-3',
                isMid && 'bg-gold/[0.06]',
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'text-[11px] font-bold uppercase tracking-[0.12em]',
                    isMid ? 'text-gold' : 'text-muted',
                  )}
                >
                  {copy.label}
                </span>
                {isMid && (
                  <span className="inline-flex items-center rounded-full bg-gold/15 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-gold">
                    What we'd back
                  </span>
                )}
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-heading font-bold leading-none text-navy tabular-nums text-3xl sm:text-4xl">
                  {fmtCurrency2(tier.pricePerLb)}
                </span>
                <span className="text-sm font-heading font-semibold text-muted">
                  / lb
                </span>
              </div>
              <dl className="text-sm space-y-1">
                <div className="flex items-baseline justify-between gap-3">
                  <dt className="text-muted">Profit this batch</dt>
                  <dd
                    className={cn(
                      'font-heading font-semibold tabular-nums',
                      tier.profitPerBatch >= 0 ? 'text-ink' : 'text-red-brand',
                    )}
                  >
                    {fmtCurrency(tier.profitPerBatch)}
                  </dd>
                </div>
                <div className="flex items-baseline justify-between gap-3">
                  <dt className="text-muted">Margin</dt>
                  <dd className="font-heading font-semibold tabular-nums text-ink">
                    {fmtPct(tier.marginPct)}
                  </dd>
                </div>
              </dl>
              <p className="text-xs text-muted leading-relaxed mt-auto pt-1">
                {copy.story}
              </p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function ShippingStrategyCard({
  shipping,
  onEditShipping,
}: {
  shipping: ShippingStrategy;
  onEditShipping: () => void;
}) {
  const hasViableThreshold =
    shipping.freeShippingThreshold !== null &&
    Number.isFinite(shipping.freeShippingThreshold) &&
    shipping.freeShippingThreshold > 0;

  const roundedThreshold = hasViableThreshold
    ? Math.ceil((shipping.freeShippingThreshold as number) / 5) * 5
    : null;

  return (
    <section className="rounded-lg border border-line bg-white shadow-card overflow-hidden">
      <div className="px-5 sm:px-6 pt-5 sm:pt-6 pb-3 border-b border-line flex items-center justify-between gap-3">
        <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy">
          Shipping strategy
        </h2>
        <button
          type="button"
          onClick={onEditShipping}
          className="text-xs sm:text-sm text-muted hover:text-navy underline underline-offset-4 decoration-line focus:outline-none focus-visible:text-navy"
        >
          Edit shipping inputs
        </button>
      </div>

      <ul className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-line">
        <li className="px-5 sm:px-6 py-5 sm:py-6 flex flex-col gap-3 bg-gold/[0.06]">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-gold">
              Free shipping (built in)
            </span>
            <span className="inline-flex items-center rounded-full bg-gold/15 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-gold">
              Recommended
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-heading font-bold leading-none text-navy tabular-nums text-3xl sm:text-4xl">
              {fmtCurrency2(shipping.withShippingPricePerLb)}
            </span>
            <span className="text-sm font-heading font-semibold text-muted">
              / lb
            </span>
          </div>
          <p className="text-sm text-ink leading-relaxed">
            Shipping is baked into the per-pound price. Customers always see
            <strong className="font-semibold"> free shipping</strong> on every
            order. Best for retail listings and online marketplaces where a
            single sticker price wins trust.
          </p>
        </li>

        <li className="px-5 sm:px-6 py-5 sm:py-6 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted">
              Plus shipping
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-heading font-bold leading-none text-navy tabular-nums text-3xl sm:text-4xl">
              {fmtCurrency2(shipping.withoutShippingPricePerLb)}
            </span>
            <span className="text-sm font-heading font-semibold text-muted">
              / lb
            </span>
            <span className="ml-2 text-xs text-muted">
              + ~{fmtCurrency(shipping.shippingPerPackage)} per box
            </span>
          </div>
          <p className="text-sm text-ink leading-relaxed">
            Lower sticker price; customer pays shipping at checkout. Best for
            wholesale, local pickup, or when buyers expect itemized shipping.
          </p>
        </li>
      </ul>

      <div className="border-t border-line bg-bg/40 px-5 sm:px-6 py-4">
        {hasViableThreshold ? (
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-muted">
              Free shipping over
            </span>
            <span className="text-xl sm:text-2xl font-heading font-bold text-navy tabular-nums">
              {fmtCurrency(roundedThreshold as number)}
            </span>
            <span className="text-xs sm:text-sm text-muted">
              At that order size, your{' '}
              <strong className="text-ink font-semibold">
                {fmtPct(shipping.bareMarginPct)}
              </strong>{' '}
              bare-price margin covers the average{' '}
              <strong className="text-ink font-semibold">
                {fmtCurrency(shipping.shippingPerPackage)}
              </strong>{' '}
              shipping cost per box.
            </span>
          </div>
        ) : (
          <p className="text-xs sm:text-sm text-red-brand">
            At this margin and shipping cost, offering free shipping isn't
            sustainable. Tighten costs above or raise your target margin in
            Step 4.
          </p>
        )}
      </div>
    </section>
  );
}

function CutList({
  cutList,
  animal,
  onSetOverride,
  onResetOverrides,
}: {
  cutList: CutListResult;
  animal: AnimalKey;
  onSetOverride: (cutId: string, price: number | null) => void;
  onResetOverrides: () => void;
}) {
  const profile = ANIMAL_PROFILES[animal];
  const hasOverrides = cutList.overriddenCount > 0;
  const recommendedAvg =
    cutList.totalLbs > 0
      ? cutList.recommendedRevenue / cutList.totalLbs
      : 0;

  return (
    <section className="rounded-lg border border-line bg-white shadow-card overflow-hidden">
      <div className="px-5 sm:px-6 pt-5 sm:pt-6 pb-3 border-b border-line flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-2xl shrink-0" aria-hidden="true">
            {profile.emoji}
          </span>
          <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy truncate">
            Retail cut list
            <span className="text-muted font-normal"> · {profile.label}</span>
          </h2>
        </div>
      </div>

      <p className="px-5 sm:px-6 pt-4 text-xs sm:text-sm text-muted leading-relaxed">
        Per-cut prices that average to your recommended{' '}
        <strong className="text-ink font-semibold">
          {fmtCurrency2(recommendedAvg)}/lb
        </strong>{' '}
        across all cuts. Tap any price to override.
      </p>

      <div className="px-5 sm:px-6 py-5 space-y-5">
        {cutList.groups.map((group) => (
          <CutGroupBlock
            key={group.category}
            group={group}
            onSetOverride={onSetOverride}
          />
        ))}
      </div>

      <div className="border-t border-line bg-bg/40 px-5 sm:px-6 py-4">
        <div className="flex items-baseline gap-3">
          <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-muted">
            Total
          </span>
          <span className="text-xs sm:text-sm text-muted tabular-nums">
            {fmtLbs(cutList.totalLbs)}
          </span>
          <span className="ml-auto text-base sm:text-lg font-heading font-bold text-navy tabular-nums">
            {fmtCurrency(cutList.customRevenue)}
          </span>
          <span className="text-xs sm:text-sm text-muted tabular-nums">
            ({fmtCurrency2(cutList.customAveragePerLb)} avg)
          </span>
        </div>

        {hasOverrides && (
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs sm:text-sm">
            <span
              className={cn(
                'font-semibold tabular-nums',
                cutList.delta >= 0 ? 'text-green-brand' : 'text-red-brand',
              )}
            >
              {cutList.delta >= 0 ? '+' : ''}
              {fmtCurrency(cutList.delta)} vs recommended
            </span>
            <span className="text-muted">
              {cutList.overriddenCount}{' '}
              {cutList.overriddenCount === 1 ? 'cut' : 'cuts'} edited
            </span>
            <button
              type="button"
              onClick={onResetOverrides}
              className="ml-auto text-muted hover:text-navy underline underline-offset-4 decoration-line focus:outline-none focus-visible:text-navy"
            >
              Reset all
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function CutGroupBlock({
  group,
  onSetOverride,
}: {
  group: CutGroup;
  onSetOverride: (cutId: string, price: number | null) => void;
}) {
  return (
    <div>
      <h3 className="text-[11px] font-bold uppercase tracking-[0.12em] text-gold mb-2">
        {group.label}
      </h3>
      <ul className="divide-y divide-line/60">
        {group.cuts.map((cut) => (
          <CutRow key={cut.id} cut={cut} onSetOverride={onSetOverride} />
        ))}
      </ul>
    </div>
  );
}

function CutRow({
  cut,
  onSetOverride,
}: {
  cut: Cut;
  onSetOverride: (cutId: string, price: number | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  const startEdit = () => {
    setDraft(cut.pricePerLb.toFixed(2));
    setEditing(true);
  };

  const commit = () => {
    const cleaned = draft.replace(/[^\d.]/g, '');
    const n = parseFloat(cleaned);
    if (Number.isFinite(n) && n >= 0) {
      onSetOverride(cut.id, n);
    }
    setEditing(false);
  };

  const cancel = () => setEditing(false);

  const reset = () => {
    onSetOverride(cut.id, null);
  };

  return (
    <li className="py-2.5 flex items-center gap-3">
      <span className="flex-1 min-w-0 text-sm sm:text-base text-ink truncate">
        {cut.name}
      </span>
      <span className="shrink-0 text-xs text-muted tabular-nums w-14 sm:w-16 text-right">
        {fmtLbs1(cut.estimatedLbs)}
      </span>
      <span className="shrink-0 flex items-center gap-1 sm:w-36 justify-end">
        {editing ? (
          <span className="inline-flex items-center gap-0.5 rounded-md border border-navy bg-white pl-2 pr-1 py-1 ring-2 ring-gold/40">
            <span className="text-muted text-sm">$</span>
            <input
              ref={inputRef}
              type="text"
              inputMode="decimal"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={commit}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commit();
                if (e.key === 'Escape') cancel();
              }}
              aria-label={`Override price for ${cut.name}`}
              className="w-16 bg-transparent text-right text-sm font-heading font-semibold text-navy outline-none tabular-nums"
            />
            <span className="text-muted text-xs ml-0.5">/ lb</span>
          </span>
        ) : (
          <button
            type="button"
            onClick={startEdit}
            aria-label={`Edit price for ${cut.name}, currently ${fmtCurrency2(cut.pricePerLb)} per lb`}
            className={cn(
              'inline-flex items-baseline gap-1 rounded-md px-2 py-1 -my-1 transition-colors',
              'hover:bg-bg/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold/50',
              cut.isOverridden && 'text-gold',
            )}
          >
            <span
              className={cn(
                'font-heading font-semibold tabular-nums',
                cut.isOverridden ? 'text-gold' : 'text-navy',
              )}
            >
              {fmtCurrency2(cut.pricePerLb)}
            </span>
            <span className="text-xs text-muted">/ lb</span>
          </button>
        )}
        {cut.isOverridden && !editing && (
          <button
            type="button"
            onClick={reset}
            className="inline-flex items-center justify-center w-7 h-7 text-muted hover:text-navy focus:outline-none focus-visible:text-navy focus-visible:ring-2 focus-visible:ring-gold/50 rounded-full"
            aria-label={`Reset ${cut.name} to suggested ${fmtCurrency2(cut.suggestedPricePerLb)}`}
            title={`Reset to suggested ${fmtCurrency2(cut.suggestedPricePerLb)}`}
          >
            <span aria-hidden="true">↺</span>
          </button>
        )}
      </span>
    </li>
  );
}

interface CostBreakdownProps {
  slices: CostSlice[];
  totalCosts: number;
  onEditCosts: () => void;
}

function CostBreakdown({ slices, totalCosts, onEditCosts }: CostBreakdownProps) {
  const total = totalCosts > 0 ? totalCosts : 1;
  const sorted = useMemo(() => [...slices].sort((a, b) => b.value - a.value), [slices]);

  return (
    <section className="rounded-lg border border-line bg-white shadow-card overflow-hidden">
      <div className="px-5 sm:px-6 pt-5 sm:pt-6 pb-3 border-b border-line flex items-baseline justify-between gap-3">
        <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy">
          Where the money goes
        </h2>
        <span className="text-xs sm:text-sm text-muted tabular-nums">
          {fmtCurrency(totalCosts)} total
        </span>
      </div>

      <div className="px-5 sm:px-6 pt-5 sm:pt-6">
        <div
          role="img"
          aria-label={`Cost breakdown: ${sorted
            .map((s) => `${s.name} ${Math.round((s.value / total) * 100)}%`)
            .join(', ')}`}
          className="flex h-3 w-full overflow-hidden rounded-full bg-line"
        >
          {sorted.map((s) => {
            const pct = (s.value / total) * 100;
            if (pct <= 0) return null;
            return (
              <div
                key={s.name}
                style={{ width: `${pct}%`, backgroundColor: s.color }}
                title={`${s.name} · ${fmtPct(pct)}`}
              />
            );
          })}
        </div>
      </div>

      <ul className="px-5 sm:px-6 py-5 sm:py-6 space-y-3">
        {sorted.map((s) => {
          const pct = (s.value / total) * 100;
          return (
            <li
              key={s.name}
              className="flex items-center gap-3 sm:gap-4 text-sm sm:text-base"
            >
              <span
                aria-hidden="true"
                className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="flex-1 text-ink font-medium">{s.name}</span>
              <span className="hidden sm:inline w-16 text-right text-xs font-semibold uppercase tracking-wider text-muted tabular-nums">
                {fmtPct(pct)}
              </span>
              <span className="w-24 text-right font-heading font-semibold text-navy tabular-nums">
                {fmtCurrency(s.value)}
              </span>
            </li>
          );
        })}
      </ul>

      <div className="border-t border-line bg-bg/40 px-5 sm:px-6 py-3 flex items-center justify-between gap-3">
        <p className="text-xs sm:text-sm text-muted">
          Numbers off? Adjust them and the price updates.
        </p>
        <Button variant="ghost" size="sm" onClick={onEditCosts}>
          Edit costs
        </Button>
      </div>
    </section>
  );
}

interface ChannelCardProps {
  channels: ChannelComparison[];
  animal: AnimalKey;
}

function ChannelComparisonCard({ channels, animal }: ChannelCardProps) {
  const sorted = useMemo(
    () => [...channels].sort((a, b) => b.netProfit - a.netProfit),
    [channels],
  );
  const [open, setOpen] = useState<string | null>(null);
  const animalLabel = ANIMAL_PROFILES[animal].label.toLowerCase();

  return (
    <section className="rounded-lg border border-line bg-white shadow-card overflow-hidden">
      <div className="px-5 sm:px-6 pt-5 sm:pt-6 pb-3 border-b border-line">
        <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy">
          How channels compare
        </h2>
        <p className="mt-1 text-xs sm:text-sm text-muted">
          Same {animalLabel}, four ways to sell it. Best net to your pocket
          first.
        </p>
      </div>

      <div className="hidden sm:grid grid-cols-12 gap-3 px-6 pt-4 pb-2 text-[11px] font-bold uppercase tracking-wider text-muted">
        <span className="col-span-5">Channel</span>
        <span className="col-span-2 text-right">Price / lb</span>
        <span className="col-span-2 text-right">Net / lb</span>
        <span className="col-span-3 text-right">Total net</span>
      </div>

      <ul className="divide-y divide-line">
        {sorted.map((c, i) => {
          const isBest = i === 0;
          const isOpen = open === c.name;
          return (
            <li key={c.name}>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? null : c.name)}
                aria-expanded={isOpen}
                className={cn(
                  'w-full grid grid-cols-12 gap-3 px-5 sm:px-6 py-4 text-left transition-colors',
                  'hover:bg-bg/60 focus:outline-none focus-visible:bg-bg/60',
                  isBest && 'bg-gold/[0.06]',
                )}
              >
                <span className="col-span-12 sm:col-span-5 flex items-center gap-2 flex-wrap">
                  {isBest && (
                    <span className="inline-flex items-center rounded-full bg-gold/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gold">
                      Best net
                    </span>
                  )}
                  <span className="font-heading uppercase tracking-wide text-sm font-semibold text-navy">
                    {c.name}
                  </span>
                  {c.highlight && (
                    <span className="inline-flex items-center rounded-full border border-gold/40 bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-gold">
                      From The Farm
                    </span>
                  )}
                </span>
                <span className="col-span-4 sm:col-span-2 text-right tabular-nums">
                  <span className="sm:hidden block text-[10px] uppercase tracking-wider text-muted">
                    Price
                  </span>
                  <span className="font-heading font-semibold text-navy">
                    {fmtCurrency2(c.pricePerLb)}
                  </span>
                </span>
                <span className="col-span-4 sm:col-span-2 text-right tabular-nums">
                  <span className="sm:hidden block text-[10px] uppercase tracking-wider text-muted">
                    Net / lb
                  </span>
                  <span className="font-heading font-semibold text-ink">
                    {fmtCurrency2(c.netPerLb)}
                  </span>
                </span>
                <span className="col-span-4 sm:col-span-3 text-right tabular-nums">
                  <span className="sm:hidden block text-[10px] uppercase tracking-wider text-muted">
                    Total
                  </span>
                  <span
                    className={cn(
                      'font-heading font-bold',
                      c.netProfit >= 0 ? 'text-navy' : 'text-red-brand',
                    )}
                  >
                    {fmtCurrency(c.totalNet)}
                  </span>
                </span>
              </button>

              {isOpen && (
                <div className="px-5 sm:px-6 pb-4 -mt-1">
                  <dl className="grid grid-cols-1 sm:grid-cols-3 gap-3 rounded-md bg-bg/60 px-4 py-3">
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-muted">
                        Price multiplier
                      </dt>
                      <dd className="mt-0.5 text-ink font-heading">
                        {(c.multiplier * 100).toFixed(0)}% of base
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-muted">
                        Commission
                      </dt>
                      <dd className="mt-0.5 text-ink font-heading">
                        {c.commissionPct}% of price
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[10px] font-bold uppercase tracking-wider text-muted">
                        Net profit
                      </dt>
                      <dd
                        className={cn(
                          'mt-0.5 font-heading font-semibold',
                          c.netProfit >= 0 ? 'text-green-brand' : 'text-red-brand',
                        )}
                      >
                        {fmtCurrency(c.netProfit)}
                      </dd>
                    </div>
                  </dl>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function SaveCard({
  leadEmail,
  onLeadEmail,
  onDownloadPdf,
}: {
  leadEmail: string;
  onLeadEmail: (email: string) => void;
  onDownloadPdf: () => void;
}) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [failed, setFailed] = useState(false);
  const [leadIssue, setLeadIssue] = useState(false);
  const failTimerRef = useRef<number | null>(null);
  const sent = leadEmail.length > 0;
  const canSubmit = name.trim().length > 0 && email.trim().length > 0;

  useEffect(() => {
    return () => {
      if (failTimerRef.current !== null) {
        window.clearTimeout(failTimerRef.current);
      }
    };
  }, []);

  const triggerDownload = () => {
    setSubmitting(true);
    setFailed(false);
    setLeadIssue(false);

    void (async () => {
      // Brief "Preparing PDF" delay so the spinner reads as deliberate.
      await new Promise((r) => window.setTimeout(r, 500));

      try {
        onDownloadPdf();
      } catch (err) {
        console.error('PDF generation failed:', err);
        setSubmitting(false);
        setFailed(true);
        if (failTimerRef.current !== null) {
          window.clearTimeout(failTimerRef.current);
        }
        failTimerRef.current = window.setTimeout(() => {
          setFailed(false);
          failTimerRef.current = null;
        }, 6000);
        return;
      }

      // PDF downloaded; capture the lead (only on first submit).
      if (!sent) {
        const result = await captureLead({
          name: name.trim(),
          email: email.trim(),
          source: 'ftf-pricing-calculator',
        });
        if (!result.ok && result.reason !== 'no-url') {
          setLeadIssue(true);
        }
        onLeadEmail(email);
      }

      setSubmitting(false);
    })();
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    triggerDownload();
  };

  return (
    <section className="rounded-lg border border-navy/15 bg-white shadow-card overflow-hidden">
      <div className="grid sm:grid-cols-5">
        <div className="sm:col-span-2 bg-navy/[0.03] px-5 sm:px-6 py-5 sm:py-6 border-b sm:border-b-0 sm:border-r border-line">
          <h2 className="font-heading uppercase tracking-wide text-base sm:text-lg font-semibold text-navy">
            Save your pricing
          </h2>
          <p className="mt-2 text-sm text-muted leading-relaxed">
            Drop your name and email to download a PDF of your pricing. Costs
            change with the season — we'll also email you when Save Profile
            goes live so you can come back and update without starting over.
          </p>
        </div>

        <div className="sm:col-span-3 px-5 sm:px-6 py-5 sm:py-6">
          {sent ? (
            <div className="flex flex-col items-start gap-3">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-green-brand/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-green-brand">
                <span aria-hidden="true">✓</span>
                {leadIssue ? 'Downloaded' : 'Saved & downloaded'}
              </span>
              <p className="text-sm text-ink leading-relaxed">
                Thanks{name ? `, ${name.split(' ')[0]}` : ''}. Your pricing
                report has downloaded.
                {leadIssue
                  ? " We hit a snag saving your info — feel free to try again, or email us at hello@fromthefarm.com and we'll add you manually."
                  : " We'll email you the moment Save Profile is ready."}
              </p>
              {failed && (
                <p
                  role="alert"
                  className="rounded-lg border border-red-brand/40 bg-red-brand/5 px-3 py-2 text-sm text-red-brand"
                >
                  Couldn't generate the PDF this time. Try again, or refresh
                  the page if it keeps happening.
                </p>
              )}
              <Button
                type="button"
                variant="secondary"
                onClick={triggerDownload}
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    <span>Preparing PDF</span>
                  </>
                ) : failed ? (
                  'Try again'
                ) : (
                  'Download again'
                )}
              </Button>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-3">
              <div className="grid sm:grid-cols-2 gap-3">
                <label className="block">
                  <span className="block text-xs font-bold uppercase tracking-wider text-ink mb-1.5">
                    Your name
                  </span>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoComplete="name"
                    className="form-input w-full rounded-lg border border-line bg-white px-3 py-3 text-base text-ink placeholder:text-muted focus:border-navy focus:ring-2 focus:ring-gold/40"
                  />
                </label>
                <label className="block">
                  <span className="block text-xs font-bold uppercase tracking-wider text-ink mb-1.5">
                    Email
                  </span>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    inputMode="email"
                    placeholder="you@yourfarm.com"
                    className="form-input w-full rounded-lg border border-line bg-white px-3 py-3 text-base text-ink placeholder:text-muted focus:border-navy focus:ring-2 focus:ring-gold/40"
                  />
                </label>
              </div>
              {failed && (
                <p
                  role="alert"
                  className="rounded-lg border border-red-brand/40 bg-red-brand/5 px-3 py-2 text-sm text-red-brand"
                >
                  Couldn't generate the PDF. Try again, or refresh the page if
                  it keeps happening.
                </p>
              )}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <p className="text-xs text-muted">
                  We'll never sell your email.
                </p>
                <Button
                  type="submit"
                  variant="gold"
                  disabled={submitting || !canSubmit}
                >
                  {submitting ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      <span>Preparing PDF</span>
                    </>
                  ) : failed ? (
                    'Try again'
                  ) : (
                    'Download PDF'
                  )}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}

function Assumptions({ premium }: { premium: boolean }) {
  const lines: Array<[string, string]> = [
    ['Packaged weight', '75% of carcass weight, after cut & wrap'],
    [
      'Premium production',
      premium ? '+12% markup applied' : 'Standard production (no markup)',
    ],
    ['Shipping rates', 'USPS Priority Mail by zone'],
    ['Channel commissions', 'Current published rates per channel'],
  ];
  return (
    <section className="px-1">
      <h2 className="text-xs font-bold uppercase tracking-[0.1em] text-muted">
        How we got there
      </h2>
      <dl className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-sm">
        {lines.map(([k, v]) => (
          <div
            key={k}
            className="flex items-baseline gap-3 border-b border-line/60 pb-2"
          >
            <dt className="text-muted shrink-0">{k}</dt>
            <dd className="ml-auto text-right text-ink">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function FooterActions({
  onBack,
  onReset,
}: {
  onBack: () => void;
  onReset: () => void;
}) {
  return (
    <div className="pt-2 flex items-center gap-2">
      <Button variant="ghost" onClick={onBack}>
        ← Back
      </Button>
      <Button variant="ghost" onClick={onReset}>
        Start over
      </Button>
    </div>
  );
}
