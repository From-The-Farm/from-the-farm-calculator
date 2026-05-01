import type {
  AnimalKey,
  CalculatorInput,
  CalculatorResult,
  ChannelComparison,
} from './types';
import { lookupShippingRate } from './shippingRates';
import {
  CUT_CATEGORY_LABELS,
  CUT_LISTS,
  type CutCategory,
} from './cutLists';

const PREMIUM_MULTIPLIER = 1.12;
const PACKAGED_FROM_CARCASS = 0.75;

function safeDiv(num: number, denom: number): number {
  return denom > 0 ? num / denom : 0;
}

function priceFromCosts(
  costsForPricing: number,
  totalPackagedLbs: number,
  mode: 'dollar' | 'percent',
  profitDollar: number,
  profitPct: number,
): number {
  if (totalPackagedLbs <= 0) return 0;
  if (mode === 'dollar') {
    return safeDiv(costsForPricing + profitDollar, totalPackagedLbs);
  }
  const margin = Math.max(0, Math.min(profitPct, 95)) / 100;
  const costPerLb = safeDiv(costsForPricing, totalPackagedLbs);
  return safeDiv(costPerLb, 1 - margin);
}

export function calculate(input: CalculatorInput): CalculatorResult {
  const { step1, step2, step4 } = input;
  const { feedVet, processing, shipping, marketing, storage } = step2;

  const carcassLbs = step1.liveWeight * step1.carcassYield;
  const packagedLbsPerAnimal = carcassLbs * PACKAGED_FROM_CARCASS;
  const totalPackagedLbs = packagedLbsPerAnimal * Math.max(step1.numAnimals, 0);

  const laborTotal = feedVet.laborHours * feedVet.laborRate;
  const feedVetPerAnimal = feedVet.feedCost + feedVet.vetCost + laborTotal;
  const feedVetTotal = feedVetPerAnimal * step1.numAnimals;

  const processingPerAnimal =
    processing.killFee + processing.cutWrapFeePerLb * carcassLbs + processing.transportToProcessor;
  const processingTotal = processingPerAnimal * step1.numAnimals;

  const shippingCostPerPkg = lookupShippingRate(shipping.avgPackageWeight, shipping.zone);
  const numPackages = safeDiv(totalPackagedLbs, shipping.avgPackageWeight);
  const shippingTotal = shippingCostPerPkg * numPackages;
  const shippingCostPerLb = safeDiv(shippingTotal, totalPackagedLbs);

  const storageTotal = storage.coldStorageCostPerLb * totalPackagedLbs * storage.avgMonthsInStorage;

  const fixedNonMarketing = feedVetTotal + processingTotal + storageTotal;

  const targetPreMarketing = priceFromCosts(
    fixedNonMarketing,
    totalPackagedLbs,
    step4.mode,
    step4.profitDollar,
    step4.profitPct,
  );
  const premiumFactor = step1.premiumProduction ? PREMIUM_MULTIPLIER : 1;
  const estimatedRevenue =
    (targetPreMarketing + shippingCostPerLb) * totalPackagedLbs * premiumFactor;
  const marketingTotal =
    marketing.marketingFixed + (marketing.marketingPctRevenue / 100) * estimatedRevenue;

  const costsForPricing = fixedNonMarketing + marketingTotal;
  const totalCosts = costsForPricing + shippingTotal;
  const costPerLb = safeDiv(totalCosts, totalPackagedLbs);

  const targetPricePerLb = priceFromCosts(
    costsForPricing,
    totalPackagedLbs,
    step4.mode,
    step4.profitDollar,
    step4.profitPct,
  );

  const recommendedPricePerLb = (targetPricePerLb + shippingCostPerLb) * premiumFactor;
  const grossRevenue = recommendedPricePerLb * totalPackagedLbs;
  const netProfit = grossRevenue - totalCosts;
  const marginPct = grossRevenue > 0 ? (netProfit / grossRevenue) * 100 : 0;

  return {
    carcassLbs,
    packagedLbsPerAnimal,
    totalPackagedLbs,
    feedVetTotal,
    processingTotal,
    shippingCostPerPkg,
    numPackages,
    shippingTotal,
    shippingCostPerLb,
    marketingTotal,
    storageTotal,
    costsForPricing,
    totalCosts,
    costPerLb,
    targetPricePerLb,
    recommendedPricePerLb,
    grossRevenue,
    netProfit,
    marginPct,
  };
}

const CHANNEL_DEFS: Array<Omit<ChannelComparison, 'pricePerLb' | 'netPerLb' | 'totalNet' | 'netProfit'>> = [
  { name: 'Local Farmers Market', multiplier: 1.1, commissionPct: 2.9, highlight: false },
  { name: 'FTF — By the Cut', multiplier: 1.0, commissionPct: 2.9, highlight: true },
  { name: 'FTF — Bundles', multiplier: 0.89, commissionPct: 2.9, highlight: true },
  { name: 'Online Marketplace', multiplier: 1.14, commissionPct: 17.9, highlight: false },
];

export function buildComparison(result: CalculatorResult): ChannelComparison[] {
  const baseCosts = result.totalCosts;
  return CHANNEL_DEFS.map((c) => {
    const pricePerLb = result.recommendedPricePerLb * c.multiplier;
    const netPerLb = pricePerLb * (1 - c.commissionPct / 100);
    const totalNet = netPerLb * result.totalPackagedLbs;
    const netProfit = totalNet - baseCosts;
    return { ...c, pricePerLb, netPerLb, totalNet, netProfit };
  });
}

export interface PriceTier {
  key: 'low' | 'medium' | 'high';
  marginPct: number;
  pricePerLb: number;
  profitPerBatch: number;
}

export function targetMarginFromInput(input: CalculatorInput): number {
  const { step4 } = input;
  if (step4.mode === 'percent') {
    return Math.max(0, Math.min(95, step4.profitPct));
  }
  const baseResult = calculate(input);
  if (baseResult.grossRevenue <= 0) return 0;
  return Math.max(0, Math.min(95, baseResult.marginPct));
}

function priceAtMargin(input: CalculatorInput, marginPct: number): PriceTier {
  const altInput: CalculatorInput = {
    ...input,
    step4: { ...input.step4, mode: 'percent', profitPct: marginPct },
  };
  const r = calculate(altInput);
  return {
    key: 'medium',
    marginPct: r.marginPct,
    pricePerLb: r.recommendedPricePerLb,
    profitPerBatch: r.netProfit,
  };
}

export function buildPriceTiers(
  input: CalculatorInput,
  result: CalculatorResult,
): { low: PriceTier; medium: PriceTier; high: PriceTier } {
  const target = targetMarginFromInput(input);
  const lowMargin = Math.max(5, target - 10);
  const highMargin = Math.min(80, target + 10);
  return {
    low: { ...priceAtMargin(input, lowMargin), key: 'low' },
    medium: {
      key: 'medium',
      marginPct: result.marginPct,
      pricePerLb: result.recommendedPricePerLb,
      profitPerBatch: result.netProfit,
    },
    high: { ...priceAtMargin(input, highMargin), key: 'high' },
  };
}

export interface CostSlice {
  name: string;
  value: number;
  color: string;
}

export interface Cut {
  id: string;
  name: string;
  category: CutCategory;
  estimatedLbs: number;
  suggestedPricePerLb: number;
  pricePerLb: number;
  isOverridden: boolean;
  estimatedRevenue: number;
}

export interface CutGroup {
  category: CutCategory;
  label: string;
  cuts: Cut[];
}

export interface CutListResult {
  groups: CutGroup[];
  totalLbs: number;
  recommendedRevenue: number;
  customRevenue: number;
  customAveragePerLb: number;
  overriddenCount: number;
  delta: number;
}

export function buildCutList(
  animal: AnimalKey | null,
  result: CalculatorResult,
  overrides: Record<string, number>,
): CutListResult | null {
  if (!animal) return null;
  const defs = CUT_LISTS[animal];
  if (!defs || defs.length === 0) return null;

  const totalLbs = result.totalPackagedLbs;
  const recommendedPrice = result.recommendedPricePerLb;
  if (
    !Number.isFinite(totalLbs) ||
    totalLbs <= 0 ||
    !Number.isFinite(recommendedPrice)
  ) {
    return null;
  }

  const denom =
    defs.reduce((s, d) => s + d.yieldFraction * d.priceWeight, 0) || 1;

  const cuts: Cut[] = defs.map((d) => {
    const suggestedPrice = recommendedPrice * (d.priceWeight / denom);
    const override = overrides[d.id];
    const isOverridden =
      typeof override === 'number' && Number.isFinite(override) && override >= 0;
    const pricePerLb = isOverridden ? override : suggestedPrice;
    const estimatedLbs = totalLbs * d.yieldFraction;
    return {
      id: d.id,
      name: d.name,
      category: d.category,
      estimatedLbs,
      suggestedPricePerLb: suggestedPrice,
      pricePerLb,
      isOverridden,
      estimatedRevenue: pricePerLb * estimatedLbs,
    };
  });

  const groupMap = new Map<CutCategory, Cut[]>();
  const orderSeen: CutCategory[] = [];
  for (const cut of cuts) {
    if (!groupMap.has(cut.category)) {
      groupMap.set(cut.category, []);
      orderSeen.push(cut.category);
    }
    groupMap.get(cut.category)!.push(cut);
  }

  const groups: CutGroup[] = orderSeen.map((cat) => ({
    category: cat,
    label: CUT_CATEGORY_LABELS[cat],
    cuts: groupMap.get(cat)!,
  }));

  const customRevenue = cuts.reduce((s, c) => s + c.estimatedRevenue, 0);
  const overriddenCount = cuts.filter((c) => c.isOverridden).length;

  return {
    groups,
    totalLbs,
    recommendedRevenue: result.grossRevenue,
    customRevenue,
    customAveragePerLb: totalLbs > 0 ? customRevenue / totalLbs : 0,
    overriddenCount,
    delta: customRevenue - result.grossRevenue,
  };
}

export function buildCostSlices(result: CalculatorResult): CostSlice[] {
  return [
    { name: 'Feed & Vet', value: result.feedVetTotal, color: '#1B3A6B' },
    { name: 'Processing', value: result.processingTotal, color: '#B5965A' },
    { name: 'Shipping', value: result.shippingTotal, color: '#16A34A' },
    { name: 'Marketing', value: result.marketingTotal, color: '#D97706' },
    { name: 'Storage', value: result.storageTotal, color: '#6B6B6B' },
  ].filter((s) => s.value > 0);
}
