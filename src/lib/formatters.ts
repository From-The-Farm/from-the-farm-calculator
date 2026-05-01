const currencyFmt = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const currencyFmt2 = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const lbsFmt = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 0,
});

const lbsFmt1 = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 1,
});

const pctFmt = new Intl.NumberFormat('en-US', {
  style: 'percent',
  maximumFractionDigits: 1,
});

export function fmtCurrency(n: number): string {
  if (!Number.isFinite(n)) return '$0';
  return currencyFmt.format(n);
}

export function fmtCurrency2(n: number): string {
  if (!Number.isFinite(n)) return '$0.00';
  return currencyFmt2.format(n);
}

export function fmtLbs(n: number): string {
  if (!Number.isFinite(n)) return '0 lbs';
  return `${lbsFmt.format(n)} lbs`;
}

export function fmtLbs1(n: number): string {
  if (!Number.isFinite(n)) return '0 lbs';
  return `${lbsFmt1.format(n)} lbs`;
}

export function fmtPct(n: number): string {
  if (!Number.isFinite(n)) return '0%';
  return pctFmt.format(n / 100);
}

export function fmtNumber(n: number, decimals = 2): string {
  if (!Number.isFinite(n)) return '0';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n);
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
