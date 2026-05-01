import type { AnimalKey, Step1Data, Step2Data } from './types';

export interface AnimalProfile {
  key: AnimalKey;
  label: string;
  emoji: string;
  step1: Omit<Step1Data, 'animal' | 'premiumProduction'>;
  step2: Step2Data;
}

export const ANIMAL_PROFILES: Record<AnimalKey, AnimalProfile> = {
  beef: {
    key: 'beef',
    label: 'Beef',
    emoji: '🐄',
    step1: { liveWeight: 1200, carcassYield: 0.62, numAnimals: 1 },
    step2: {
      feedVet: { feedCost: 1200, vetCost: 80, laborHours: 60, laborRate: 25 },
      processing: { killFee: 95, cutWrapFeePerLb: 1.05, transportToProcessor: 60 },
      shipping: { zone: 4, avgPackageWeight: 8 },
      marketing: { marketingFixed: 75, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 3 },
    },
  },
  hog: {
    key: 'hog',
    label: 'Hog',
    emoji: '🐖',
    step1: { liveWeight: 250, carcassYield: 0.72, numAnimals: 1 },
    step2: {
      feedVet: { feedCost: 320, vetCost: 25, laborHours: 25, laborRate: 25 },
      processing: { killFee: 75, cutWrapFeePerLb: 0.95, transportToProcessor: 45 },
      shipping: { zone: 4, avgPackageWeight: 6 },
      marketing: { marketingFixed: 50, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 2 },
    },
  },
  lamb: {
    key: 'lamb',
    label: 'Lamb',
    emoji: '🐑',
    step1: { liveWeight: 120, carcassYield: 0.5, numAnimals: 1 },
    step2: {
      feedVet: { feedCost: 180, vetCost: 25, laborHours: 18, laborRate: 25 },
      processing: { killFee: 65, cutWrapFeePerLb: 1.1, transportToProcessor: 40 },
      shipping: { zone: 4, avgPackageWeight: 5 },
      marketing: { marketingFixed: 50, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 2 },
    },
  },
  goat: {
    key: 'goat',
    label: 'Goat',
    emoji: '🐐',
    step1: { liveWeight: 80, carcassYield: 0.48, numAnimals: 1 },
    step2: {
      feedVet: { feedCost: 140, vetCost: 25, laborHours: 16, laborRate: 25 },
      processing: { killFee: 65, cutWrapFeePerLb: 1.1, transportToProcessor: 40 },
      shipping: { zone: 4, avgPackageWeight: 5 },
      marketing: { marketingFixed: 50, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 2 },
    },
  },
  chicken: {
    key: 'chicken',
    label: 'Chicken',
    emoji: '🐓',
    step1: { liveWeight: 6, carcassYield: 0.72, numAnimals: 50 },
    step2: {
      feedVet: { feedCost: 8, vetCost: 0.5, laborHours: 0.4, laborRate: 25 },
      processing: { killFee: 4.5, cutWrapFeePerLb: 0, transportToProcessor: 1 },
      shipping: { zone: 4, avgPackageWeight: 4 },
      marketing: { marketingFixed: 1, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 2 },
    },
  },
  turkey: {
    key: 'turkey',
    label: 'Turkey',
    emoji: '🦃',
    step1: { liveWeight: 25, carcassYield: 0.78, numAnimals: 12 },
    step2: {
      feedVet: { feedCost: 40, vetCost: 1, laborHours: 1.2, laborRate: 25 },
      processing: { killFee: 12, cutWrapFeePerLb: 0, transportToProcessor: 4 },
      shipping: { zone: 4, avgPackageWeight: 12 },
      marketing: { marketingFixed: 4, marketingPctRevenue: 5 },
      storage: { coldStorageCostPerLb: 0.04, avgMonthsInStorage: 1 },
    },
  },
};

export const ANIMAL_LIST: AnimalProfile[] = [
  ANIMAL_PROFILES.beef,
  ANIMAL_PROFILES.hog,
  ANIMAL_PROFILES.lamb,
  ANIMAL_PROFILES.goat,
  ANIMAL_PROFILES.chicken,
  ANIMAL_PROFILES.turkey,
];

export const FALLBACK_DEFAULTS: { step1: Step1Data; step2: Step2Data } = {
  step1: { animal: null, liveWeight: 1200, carcassYield: 0.62, numAnimals: 1, premiumProduction: false },
  step2: ANIMAL_PROFILES.beef.step2,
};
