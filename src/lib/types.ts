export type AnimalKey = 'beef' | 'hog' | 'lamb' | 'goat' | 'chicken' | 'turkey';

export type SellingMethod = 'cut' | 'bulk' | 'bundle';

export type ProfitMode = 'dollar' | 'percent';

export interface Step1Data {
  animal: AnimalKey | null;
  liveWeight: number;
  carcassYield: number;
  numAnimals: number;
  premiumProduction: boolean;
}

export interface FeedVetCosts {
  feedCost: number;
  vetCost: number;
  laborHours: number;
  laborRate: number;
}

export interface ProcessingCosts {
  killFee: number;
  cutWrapFeePerLb: number;
  transportToProcessor: number;
}

export interface ShippingCosts {
  zone: number;
  avgPackageWeight: number;
}

export interface MarketingCosts {
  marketingFixed: number;
  marketingPctRevenue: number;
}

export interface StorageCosts {
  coldStorageCostPerLb: number;
  avgMonthsInStorage: number;
}

export interface Step2Data {
  feedVet: FeedVetCosts;
  processing: ProcessingCosts;
  shipping: ShippingCosts;
  marketing: MarketingCosts;
  storage: StorageCosts;
}

export interface Step3Data {
  method: SellingMethod;
  bundleWeight: number;
}

export interface Step4Data {
  mode: ProfitMode;
  profitDollar: number;
  profitPct: number;
}

export interface Step5Data {
  cutOverrides: Record<string, number>;
}

export interface WizardState {
  step: 1 | 2 | 3 | 4 | 5;
  step1: Step1Data;
  step2: Step2Data;
  step3: Step3Data;
  step4: Step4Data;
  step5: Step5Data;
}

export interface CalculatorInput {
  step1: Step1Data;
  step2: Step2Data;
  step3: Step3Data;
  step4: Step4Data;
}

export interface CalculatorResult {
  carcassLbs: number;
  packagedLbsPerAnimal: number;
  totalPackagedLbs: number;
  feedVetTotal: number;
  processingTotal: number;
  shippingCostPerPkg: number;
  numPackages: number;
  shippingTotal: number;
  shippingCostPerLb: number;
  marketingTotal: number;
  storageTotal: number;
  costsForPricing: number;
  totalCosts: number;
  costPerLb: number;
  targetPricePerLb: number;
  recommendedPricePerLb: number;
  grossRevenue: number;
  netProfit: number;
  marginPct: number;
}

export interface ChannelComparison {
  name: string;
  multiplier: number;
  commissionPct: number;
  pricePerLb: number;
  netPerLb: number;
  totalNet: number;
  netProfit: number;
  highlight: boolean;
}
