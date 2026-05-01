type ZoneRow = { weight: number; rates: Record<number, number> };

const RATE_TABLE: ZoneRow[] = [
  { weight: 5, rates: { 2: 14.5, 3: 16.2, 4: 18.4, 5: 20.6, 6: 23.1, 7: 26.0, 8: 29.5 } },
  { weight: 10, rates: { 2: 18.9, 3: 21.4, 4: 24.6, 5: 28.3, 6: 32.0, 7: 36.4, 8: 41.2 } },
  { weight: 15, rates: { 2: 22.3, 3: 25.8, 4: 30.0, 5: 34.9, 6: 39.7, 7: 45.6, 8: 51.8 } },
  { weight: 20, rates: { 2: 25.4, 3: 29.6, 4: 34.7, 5: 40.9, 6: 47.0, 7: 53.9, 8: 61.6 } },
  { weight: 25, rates: { 2: 28.5, 3: 33.4, 4: 39.6, 5: 47.0, 6: 54.0, 7: 62.2, 8: 71.4 } },
  { weight: 30, rates: { 2: 31.8, 3: 37.4, 4: 44.7, 5: 53.0, 6: 61.2, 7: 70.8, 8: 81.5 } },
  { weight: 40, rates: { 2: 38.6, 3: 45.7, 4: 54.8, 5: 65.4, 6: 75.7, 7: 87.6, 8: 100.7 } },
  { weight: 50, rates: { 2: 45.4, 3: 53.9, 4: 64.8, 5: 77.4, 6: 89.7, 7: 104.0, 8: 119.6 } },
];

const ZONES = [2, 3, 4, 5, 6, 7, 8] as const;

const FLAT_LARGE_SHARE = 25;

export function clampZone(zone: number): number {
  if (!Number.isFinite(zone)) return 4;
  if (zone < 2) return 2;
  if (zone > 8) return 8;
  return Math.round(zone);
}

export function lookupShippingRate(weight: number, zoneInput: number): number {
  if (!Number.isFinite(weight) || weight <= 0) return 0;
  if (weight > 50) return FLAT_LARGE_SHARE;

  const zone = clampZone(zoneInput);
  const first = RATE_TABLE[0];
  const last = RATE_TABLE[RATE_TABLE.length - 1];

  if (weight <= first.weight) return first.rates[zone];
  if (weight >= last.weight) return last.rates[zone];

  for (let i = 0; i < RATE_TABLE.length - 1; i++) {
    const lo = RATE_TABLE[i];
    const hi = RATE_TABLE[i + 1];
    if (weight >= lo.weight && weight <= hi.weight) {
      const ratio = (weight - lo.weight) / (hi.weight - lo.weight);
      return lo.rates[zone] + (hi.rates[zone] - lo.rates[zone]) * ratio;
    }
  }
  return last.rates[zone];
}

export const SHIPPING_ZONES = ZONES.map((z) => ({ value: z, label: `Zone ${z}` }));
