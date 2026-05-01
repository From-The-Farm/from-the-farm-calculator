# From The Farm — Pricing Calculator

## Developer Brief & Claude Build Prompt

**Prepared by:** AJ, CEO & Co-Founder, From The Farm
**Date:** April 2026
**Confidential — Internal Use Only**

---

## Overview

This document is everything you need to build and deploy the **From The Farm Pricing Calculator** using Claude Opus. It is structured as a straight read-through: context first, then the Claude prompt, then all technical specs. The attached wireframe HTML file is the UX source of truth — open it in any browser before you start.

From The Farm (FTF) is a farm-direct food marketplace. This calculator is the primary lead-generation tool: farmers enter their costs, receive a recommended per-pound selling price, and are invited to list on the FTF platform. The output is a branded pricing report with a GoHighLevel CRM lead capture and a client-side PDF download.

---

## What You Are Building

A mobile-first, multi-step pricing wizard built in **React 18 + TypeScript + Tailwind CSS**, deployed to **Vercel** as a fully static site. No backend, no database, no authentication required for v1. The only external integration is a GoHighLevel webhook for lead capture. PDF generation is client-side via jsPDF.

**User flow:** Animal selection → Input costs (5 tabs) → Selling method → Profit goal → Results dashboard → Lead capture modal → PDF download.

---

## The Claude Prompt

Paste the following into Claude Opus with the wireframe HTML and this document attached:

> You are a senior full-stack engineer building a production-ready web application for **From The Farm (FTF)**, a farm-direct food marketplace. The app is a **Pricing Calculator** that helps small-scale farmers determine the correct per-pound selling price for their meat, accounting for all input costs, yield losses, shipping, and a target profit margin. It is the primary lead-generation tool for the FTF platform.
>
> I am providing you with a fully functional interactive wireframe (HTML file) and a complete developer brief (this document). The wireframe is the UX source of truth. This document is the source of truth for all business logic, integrations, and deployment configuration.
>
> **Build the production version of this application exactly as specified.** Do not deviate from the wireframe screens, calculation logic, or integration specs without asking first.
>
> **Stack:** React 18 + TypeScript + Tailwind CSS 3 + Vite 5. Animations via Framer Motion. Charts via Recharts. PDF via jsPDF + html2canvas. Forms via React Hook Form + Zod. HTTP via Axios. Deploy to Vercel as a static site.
>
> **No backend, no database, no authentication** required for v1. All state is ephemeral per session.
>
> Begin by confirming you have read the wireframe and this brief, then scaffold the project and build each screen in order: Step 1 → Step 2 → Step 3 → Step 4 → Results → Lead Capture Modal. Deliver all source files with a `vercel.json`, `.env.example`, and `README.md`.

---

## Brand Identity

| Token | Value |
| --- | --- |
| Primary Navy | `#1B3A6B` |
| Gold / Tan | `#B5965A` |
| Success Green | `#16A34A` |
| Warning Amber | `#D97706` |
| Danger Red | `#DC2626` |
| Background | `#F8F6F1` (warm off-white) |
| Card Background | `#FFFFFF` |
| Heading Font | Oswald 400/600/700 — Google Fonts |
| Body Font | Lato 400/700 — Google Fonts |
| Border Radius | 8px cards · 6px inputs · 4px badges |
| Card Shadow | `0 2px 8px rgba(0,0,0,0.08)` |
| Modal Shadow | `0 4px 16px rgba(0,0,0,0.12)` |

The FTF logo SVG is attached. Place it top-left in the sticky header. Tagline "Shake the Hand That Feeds You™" appears in the footer.

---

## Application Structure

Single-page application. No multi-page routing. All state lives in a top-level `useReducer` or `useState` context.

```
App
├── Header              (sticky · FTF logo · "Save Farm Profile" placeholder · "Log In" placeholder)
├── ProgressBar         (steps 1–5 · animated fill · labels: Animal / Costs / Method / Profit / Results)
├── WizardRouter
│   ├── Step 1          Animal & Basic Info
│   ├── Step 2          Production & Input Costs (5 tabs: Feed & Vet · Processing · Shipping · Marketing · Storage)
│   ├── Step 3          Selling Method
│   ├── Step 4          Profit Goal
│   └── Step 5          Results Dashboard
├── LeadCaptureModal    (triggered from Results CTA)
└── Footer
```

---

## TypeScript Interfaces

```ts
type AnimalType = 'beef' | 'bison' | 'pork' | 'lamb' | 'chicken' | 'goat';
type SellingMethod = 'cut' | 'bulk' | 'bundle';
type ProfitMode = 'dollar' | 'percent';

interface Step1Data {
  animal: AnimalType;
  liveWeight: number;          // lbs
  carcassYield: number;        // decimal e.g. 0.60
  numAnimals: number;
  premiumProduction: boolean;  // grass-fed / regenerative toggle
}

interface Step2Data {
  feedCost: number;            // $ per animal
  vetCost: number;             // $ per animal
  laborHours: number;          // hours per animal
  laborRate: number;           // $ per hour
  killFee: number;             // $ per animal
  cutWrapFeePerLb: number;     // $ per lb of carcass weight
  transportToProcessor: number;// $ per animal
  shippingMode: 'ups_ground' | 'large_share';
  avgPackageWeight: number;    // lbs per package
  avgShippingZones: number;    // 1–8 UPS zones
  freeShippingThreshold: number;
  marketingBudgetPct: number;  // % of revenue
  coldStorageCostPerLb: number;// $ per lb per month
  avgMonthsInStorage: number;
}

interface Step3Data {
  method: SellingMethod;
  bundleWeightLbs: number;
}

interface Step4Data {
  profitMode: ProfitMode;
  desiredProfitDollar: number;
  desiredProfitPct: number;    // 0–100
}

interface CalculationResults {
  carcassLbs: number;
  packagedLbs: number;
  totalPackagedLbs: number;
  feedVetTotal: number;
  laborTotal: number;
  processingTotal: number;
  shippingTotal: number;
  marketingTotal: number;
  storageTotal: number;
  totalCostPerAnimal: number;
  totalCosts: number;
  breakEvenPricePerLb: number;
  targetPricePerLb: number;
  recommendedPricePerLb: number;
  grossRevenue: number;
  netProfit: number;
  margin: number;              // %
  shippingCostPerLb: number;
}
```

---

## Animal Defaults

| Animal | Live Wt (lbs) | Carcass Yield | Feed Cost | Vet Cost | Kill Fee | Cut & Wrap ($/lb) | Transport |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Beef 🐄 | 1,200 | 60% | $800 | $120 | $400 | $0.65 | $75 |
| Bison 🦬 | 1,000 | 58% | $950 | $150 | $450 | $0.70 | $90 |
| Pork 🐖 | 250 | 72% | $280 | $40 | $150 | $0.55 | $40 |
| Lamb 🐑 | 120 | 50% | $180 | $35 | $120 | $0.60 | $30 |
| Chicken 🐓 | 8 | 75% | $12 | $2 | $5 | $0.30 | $5 |
| Goat 🐐 | 80 | 48% | $140 | $30 | $100 | $0.55 | $25 |

**Step 2 defaults:** Labor 40 hrs @ $18/hr · Shipping mode UPS Ground · Avg package 40 lbs · Zone 3 · Free shipping threshold 150 · Marketing 3% · Cold storage $0.08/lb/month · 2 months storage.

---

## Calculation Engine

All formulas live in `src/lib/calculator.ts`. This is the complete and authoritative logic — do not deviate.

### Yield

```
carcassLbs       = liveWeight × carcassYield
packagedLbs      = carcassLbs × 0.75
totalPackagedLbs = packagedLbs × numAnimals
```

### Costs (per animal)

```
laborTotal        = laborHours × laborRate
feedVetTotal      = feedCost + vetCost + laborTotal
cutWrapTotal      = cutWrapFeePerLb × carcassLbs
processingTotal   = killFee + cutWrapTotal + transportToProcessor
shippingCostPerPkg = lookupShippingRate(avgPackageWeight, avgShippingZones)  // static table below
numPackages      = packagedLbs / avgPackageWeight
shippingTotal    = shippingCostPerPkg × numPackages
shippingCostPerLb = shippingTotal / packagedLbs
storageTotal     = coldStorageCostPerLb × packagedLbs × avgMonthsInStorage

// Marketing is % of gross revenue — solve iteratively (one pass):
totalCostPreMktg  = feedVetTotal + processingTotal + shippingTotal + storageTotal
grossRevEst       = targetPricePerLb × packagedLbs
marketingTotal    = grossRevEst × (marketingBudgetPct / 100)
totalCostPerAnimal = feedVetTotal + processingTotal + shippingTotal + marketingTotal + storageTotal
totalCosts        = totalCostPerAnimal × numAnimals
```

### Pricing

```
breakEvenPricePerLb = totalCostPerAnimal / packagedLbs

// Dollar profit mode:
targetPricePerLb = (totalCostPerAnimal + desiredProfitDollar) / packagedLbs

// Percent margin mode:
targetPricePerLb = totalCostPerAnimal / (packagedLbs × (1 - desiredProfitPct / 100))

// Bake shipping into price so farmer can advertise "free shipping":
recommendedPricePerLb = targetPricePerLb + shippingCostPerLb

// Premium production markup (grass-fed / regenerative toggle):
if (premiumProduction) recommendedPricePerLb × 1.12
```

### Results

```
grossRevenue = recommendedPricePerLb × totalPackagedLbs
netProfit    = grossRevenue - totalCosts
margin       = (netProfit / grossRevenue) × 100
```

### UPS Ground Static Rate Table

`$/package`, estimated averages — no API required for v1:

| Package Weight | Zone 2 | Zone 3 | Zone 4 | Zone 5 | Zone 6 | Zone 7 | Zone 8 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 lbs | $18 | $22 | $26 | $30 | $34 | $38 | $44 |
| 20 lbs | $24 | $29 | $34 | $40 | $46 | $52 | $60 |
| 30 lbs | $30 | $36 | $43 | $50 | $58 | $66 | $76 |
| 40 lbs | $36 | $43 | $51 | $60 | $69 | $79 | $91 |
| 50 lbs | $42 | $50 | $60 | $70 | $81 | $92 | $106 |

Interpolate linearly between rows. If package weight > 50 lbs, switch to **Large Share** mode: flat $25/package local delivery estimate.

### Comparison Table (Results Screen)

Same cost base, four selling scenarios:

| Row | Price Multiplier | Commission | Highlight |
| --- | --- | --- | --- |
| By the Cut — FTF ★ | × 1.10 | 2.9% | Yes (gold) |
| Bundles (40 lb) — FTF ★ | × 1.00 | 2.9% | Yes (gold) |
| ¼ Share — FTF (Pickup) | × 0.89 | 2.9% | No |
| Bundles — Other Platform | × 1.14 | 17.9% | No (muted) |

---

## GoHighLevel Integration

**Environment variable:**

```
VITE_GHL_WEBHOOK_URL=https://services.leadconnectorhq.com/hooks/YOUR_ID/webhook-trigger/YOUR_TRIGGER
```

**Lead capture modal fields:** First Name (req) · Last Name (req) · Farm Name (req) · Email (req) · Phone (optional) · Animals You Raise (checkbox: Beef/Bison/Pork/Lamb/Chicken/Goat) · State (select) · How did you hear about FTF? (select: Social Media / Word of Mouth / Search Engine / Podcast-Interview / Other).

**Webhook POST payload:**

```json
{
  "firstName": "string",
  "lastName": "string",
  "farmName": "string",
  "email": "string",
  "phone": "string | null",
  "animalsRaised": ["beef"],
  "state": "WY",
  "referralSource": "Podcast/Interview",
  "source": "FTF Pricing Calculator",
  "tags": ["pricing-calculator-lead", "v1"],
  "calculatorResults": {
    "animalType": "beef",
    "numAnimals": 1,
    "liveWeight": 1200,
    "packagedLbs": 540,
    "recommendedPricePerLb": 6.15,
    "grossRevenue": 3321,
    "netProfit": 404,
    "margin": 12.2,
    "totalCosts": 2917,
    "sellingMethod": "bundle",
    "premiumProduction": false
  },
  "submittedAt": "ISO 8601 timestamp"
}
```

**Modal UX:** Loading spinner on submit → success state shows green checkmark + "Welcome to the From The Farm family, [First Name]!" + PDF download button. Error state shows inline message with `hello@fromthefarm.com` fallback.

---

## PDF Export

Client-side only via `jsPDF`. No server required. Triggered from Results screen "Download PDF Report" button and from lead capture success state.

**Single letter-size page layout (top to bottom):**

1. Header band — FTF Navy background · logo left · "PRICING REPORT" gold right · farm name + date right
2. Hero price box — gold border · "$X.XX/lb" large Oswald Bold · animal/count/weight subtitle
3. Three KPI cards — Total Revenue · Net Profit (green/red) · Margin % (green ≥15% / amber 5–14% / red <5%)
4. Cost breakdown table — 7 rows: Feed & Vet · Processing · Shipping · Marketing · Storage · Total Costs · Net Profit
5. Selling method comparison table — same 4-row table as Results screen
6. FTF CTA footer band — Navy background · "Ready to list your farm on From The Farm?" · `fromthefarm.com/list`
7. Document footer — generation timestamp · disclaimer

**Filename:** `FTF-Pricing-Report-{animal}-{YYYY-MM-DD}.pdf`

---

## Vercel Deployment

`vercel.json` (project root):

```json
{
  "buildCommand": "vite build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    },
    {
      "source": "/assets/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
    }
  ]
}
```

`vite.config.ts` — include manual chunks to keep initial bundle lean:

```ts
manualChunks: {
  vendor: ['react', 'react-dom'],
  charts: ['recharts'],
  pdf: ['jspdf', 'html2canvas'],
  motion: ['framer-motion'],
}
```

`.env.example`:

```
VITE_GHL_WEBHOOK_URL=https://services.leadconnectorhq.com/hooks/YOUR_WEBHOOK_ID/webhook-trigger/YOUR_TRIGGER_ID
```

**Vercel environment variable to set:** `VITE_GHL_WEBHOOK_URL` → Production + Preview.

**Custom domain (optional):** Add `calculator.fromthefarm.com` in Vercel → CNAME `calculator` → `cname.vercel-dns.com`.

---

## Animations & Interactions

| Element | Behavior |
| --- | --- |
| Step transition forward | Slide left + fade out → slide in from right · 300ms ease-in-out |
| Step transition back | Slide right + fade out → slide in from left · 300ms ease-in-out |
| Animal card select | Scale 1.0 → 1.04 → 1.0 · border color flash · 200ms spring |
| Results price | Count-up from 0 to final value · 800ms ease-out |
| Pie chart | Slices draw clockwise one by one · 1200ms |
| Confetti | Triggered if margin ≥ 15% · 3s physics |
| Progress bar fill | Width transition · 400ms ease-in-out |
| Tooltip | Fade + slide up 4px · 150ms ease-out |
| Modal open | Backdrop fade + scale from 0.95 · 200ms ease-out |

---

## Critical Requirements Checklist

The following are non-negotiable for v1:

**Calculation accuracy.** The results screen must recalculate completely every time it renders. No hardcoded values anywhere in the results. Test by entering extreme values (400 lb vs 1,200 lb animal) and confirming the price changes.

**Mobile-first.** 375px is the primary design target. Touch targets ≥ 44px. No horizontal scroll on mobile. Wizard container max-width 720px centered on desktop.

**Smart defaults.** Every input pre-populated with the animal defaults table above. A farmer should be able to hit Next through every step and receive a valid result without entering a single number.

**Tooltips on every label.** Every input label has an (i) icon. Tap shows a plain-English tooltip with a real small-farm example. Mobile: full-width bottom sheet. Desktop: popover above label. Dismiss on tap-outside, re-tap, or Escape.

**No leading zeros on number inputs.** Parse all `type="number"` fields to `parseInt` / `parseFloat` on change. Display clean values (800, not 0800; 3, not 03).

**GHL webhook fires on lead submit.** POST the full payload above. Handle loading, success, and error states in the modal.

**PDF downloads client-side.** No server call. File named correctly. Renders cleanly on mobile.

---

## Deliverables Expected from Claude

1. Complete Vite + React + TypeScript project source
2. `package.json` with all dependencies pinned
3. `vercel.json`
4. `.env.example`
5. `README.md` with local dev and Vercel deploy instructions

---

*From The Farm — "Shake the Hand That Feeds You™"*
*fromthefarm.com*
