import type { AnimalKey } from './types';

// Cut category vocabulary. Mammals use premium / roasts / everyday / specialty.
// Poultry uses whole / cutup / specialty.
export type CutCategory =
  | 'whole'
  | 'premium'
  | 'roasts'
  | 'cutup'
  | 'everyday'
  | 'specialty';

export interface CutDef {
  id: string;
  name: string;
  category: CutCategory;
  // Fraction of total packaged lbs the cut represents (0–1). Per-animal sums to ~1.
  yieldFraction: number;
  // Relative price weighting. Normalized internally so weighted average price
  // equals the calculator's recommended $/lb.
  priceWeight: number;
}

export const CUT_CATEGORY_LABELS: Record<CutCategory, string> = {
  whole: 'Whole Bird',
  premium: 'Premium Cuts',
  roasts: 'Roasts & Ribs',
  cutup: 'Cut Up',
  everyday: 'Everyday',
  specialty: 'Specialty',
};

// Numbers below are approximate — calibrate against real processor data when available.
export const CUT_LISTS: Record<AnimalKey, CutDef[]> = {
  beef: [
    { id: 'beef-tenderloin', name: 'Tenderloin / Filet Mignon', category: 'premium', yieldFraction: 0.02, priceWeight: 3.5 },
    { id: 'beef-ribeye', name: 'Ribeye Steak', category: 'premium', yieldFraction: 0.05, priceWeight: 2.8 },
    { id: 'beef-ny-strip', name: 'NY Strip', category: 'premium', yieldFraction: 0.04, priceWeight: 2.4 },
    { id: 'beef-tbone', name: 'T-Bone / Porterhouse', category: 'premium', yieldFraction: 0.03, priceWeight: 2.5 },
    { id: 'beef-sirloin', name: 'Sirloin Steak', category: 'premium', yieldFraction: 0.05, priceWeight: 1.7 },
    { id: 'beef-flank-skirt', name: 'Flank / Skirt', category: 'premium', yieldFraction: 0.03, priceWeight: 1.8 },
    { id: 'beef-brisket', name: 'Brisket', category: 'roasts', yieldFraction: 0.03, priceWeight: 1.3 },
    { id: 'beef-chuck', name: 'Chuck Roast', category: 'roasts', yieldFraction: 0.07, priceWeight: 1.0 },
    { id: 'beef-short-ribs', name: 'Short Ribs', category: 'roasts', yieldFraction: 0.04, priceWeight: 1.4 },
    { id: 'beef-round', name: 'Round Roast', category: 'roasts', yieldFraction: 0.07, priceWeight: 0.9 },
    { id: 'beef-stew', name: 'Stew Meat', category: 'everyday', yieldFraction: 0.05, priceWeight: 0.85 },
    { id: 'beef-ground', name: 'Ground Beef', category: 'everyday', yieldFraction: 0.40, priceWeight: 0.7 },
    { id: 'beef-soup-bones', name: 'Soup Bones', category: 'specialty', yieldFraction: 0.08, priceWeight: 0.3 },
    { id: 'beef-offal', name: 'Offal (Liver, Heart, Tongue)', category: 'specialty', yieldFraction: 0.04, priceWeight: 0.6 },
  ],

  hog: [
    { id: 'hog-bacon', name: 'Bacon', category: 'premium', yieldFraction: 0.08, priceWeight: 1.7 },
    { id: 'hog-tenderloin', name: 'Pork Tenderloin', category: 'premium', yieldFraction: 0.015, priceWeight: 2.0 },
    { id: 'hog-chops', name: 'Pork Chops', category: 'premium', yieldFraction: 0.13, priceWeight: 1.4 },
    { id: 'hog-belly', name: 'Pork Belly', category: 'premium', yieldFraction: 0.035, priceWeight: 1.5 },
    { id: 'hog-loin-roast', name: 'Pork Loin Roast', category: 'roasts', yieldFraction: 0.08, priceWeight: 1.2 },
    { id: 'hog-spareribs', name: 'Spareribs', category: 'roasts', yieldFraction: 0.06, priceWeight: 1.2 },
    { id: 'hog-ham', name: 'Fresh Ham', category: 'roasts', yieldFraction: 0.14, priceWeight: 1.1 },
    { id: 'hog-boston-butt', name: 'Boston Butt', category: 'roasts', yieldFraction: 0.12, priceWeight: 0.95 },
    { id: 'hog-sausage', name: 'Sausage', category: 'everyday', yieldFraction: 0.16, priceWeight: 1.0 },
    { id: 'hog-ground', name: 'Ground Pork', category: 'everyday', yieldFraction: 0.14, priceWeight: 0.85 },
    { id: 'hog-hocks', name: 'Hocks / Trotters', category: 'specialty', yieldFraction: 0.03, priceWeight: 0.5 },
    { id: 'hog-lard', name: 'Lard', category: 'specialty', yieldFraction: 0.01, priceWeight: 0.4 },
  ],

  lamb: [
    { id: 'lamb-rack', name: 'Rack of Lamb', category: 'premium', yieldFraction: 0.06, priceWeight: 2.8 },
    { id: 'lamb-loin-chops', name: 'Loin Chops', category: 'premium', yieldFraction: 0.08, priceWeight: 2.3 },
    { id: 'lamb-tenderloin', name: 'Tenderloin', category: 'premium', yieldFraction: 0.015, priceWeight: 2.5 },
    { id: 'lamb-leg', name: 'Leg of Lamb', category: 'roasts', yieldFraction: 0.22, priceWeight: 1.5 },
    { id: 'lamb-shoulder', name: 'Shoulder Roast', category: 'roasts', yieldFraction: 0.14, priceWeight: 1.1 },
    { id: 'lamb-shanks', name: 'Lamb Shanks', category: 'roasts', yieldFraction: 0.06, priceWeight: 1.2 },
    { id: 'lamb-riblets', name: 'Riblets', category: 'roasts', yieldFraction: 0.05, priceWeight: 1.0 },
    { id: 'lamb-stew', name: 'Stew Meat', category: 'everyday', yieldFraction: 0.08, priceWeight: 0.95 },
    { id: 'lamb-ground', name: 'Ground Lamb', category: 'everyday', yieldFraction: 0.22, priceWeight: 0.9 },
    { id: 'lamb-neck', name: 'Neck / Soup Bones', category: 'specialty', yieldFraction: 0.075, priceWeight: 0.5 },
  ],

  goat: [
    { id: 'goat-loin-chops', name: 'Loin Chops', category: 'premium', yieldFraction: 0.07, priceWeight: 2.0 },
    { id: 'goat-rack', name: 'Rack', category: 'premium', yieldFraction: 0.05, priceWeight: 2.2 },
    { id: 'goat-leg', name: 'Leg of Goat', category: 'roasts', yieldFraction: 0.20, priceWeight: 1.4 },
    { id: 'goat-shoulder', name: 'Shoulder Roast', category: 'roasts', yieldFraction: 0.12, priceWeight: 1.0 },
    { id: 'goat-shanks', name: 'Shanks', category: 'roasts', yieldFraction: 0.06, priceWeight: 1.1 },
    { id: 'goat-ribs', name: 'Ribs', category: 'roasts', yieldFraction: 0.06, priceWeight: 1.0 },
    { id: 'goat-stew', name: 'Stew Meat', category: 'everyday', yieldFraction: 0.12, priceWeight: 0.9 },
    { id: 'goat-ground', name: 'Ground Goat', category: 'everyday', yieldFraction: 0.24, priceWeight: 0.9 },
    { id: 'goat-soup-bones', name: 'Soup Bones', category: 'specialty', yieldFraction: 0.08, priceWeight: 0.4 },
  ],

  chicken: [
    { id: 'chicken-whole', name: 'Whole Chicken', category: 'whole', yieldFraction: 0.65, priceWeight: 1.0 },
    { id: 'chicken-breasts', name: 'Boneless Skinless Breasts', category: 'cutup', yieldFraction: 0.12, priceWeight: 1.7 },
    { id: 'chicken-thighs', name: 'Thighs', category: 'cutup', yieldFraction: 0.08, priceWeight: 1.0 },
    { id: 'chicken-drumsticks', name: 'Drumsticks', category: 'cutup', yieldFraction: 0.05, priceWeight: 0.85 },
    { id: 'chicken-wings', name: 'Wings', category: 'cutup', yieldFraction: 0.04, priceWeight: 1.1 },
    { id: 'chicken-leg-quarters', name: 'Leg Quarters', category: 'cutup', yieldFraction: 0.03, priceWeight: 0.9 },
    { id: 'chicken-backs-necks', name: 'Backs / Necks / Feet', category: 'specialty', yieldFraction: 0.02, priceWeight: 0.4 },
    { id: 'chicken-offal', name: 'Livers / Hearts / Gizzards', category: 'specialty', yieldFraction: 0.01, priceWeight: 0.7 },
  ],

  turkey: [
    { id: 'turkey-whole', name: 'Whole Turkey', category: 'whole', yieldFraction: 0.75, priceWeight: 1.0 },
    { id: 'turkey-breast', name: 'Boneless Breast', category: 'cutup', yieldFraction: 0.12, priceWeight: 1.6 },
    { id: 'turkey-thighs', name: 'Thighs', category: 'cutup', yieldFraction: 0.05, priceWeight: 0.9 },
    { id: 'turkey-drumsticks', name: 'Drumsticks', category: 'cutup', yieldFraction: 0.03, priceWeight: 0.7 },
    { id: 'turkey-wings', name: 'Wings', category: 'cutup', yieldFraction: 0.02, priceWeight: 0.85 },
    { id: 'turkey-ground', name: 'Ground Turkey', category: 'cutup', yieldFraction: 0.02, priceWeight: 0.85 },
    { id: 'turkey-backs-necks', name: 'Backs / Necks', category: 'specialty', yieldFraction: 0.01, priceWeight: 0.4 },
  ],
};
