import { useMemo, useState } from 'react';
import { useCalculator } from '../../context/CalculatorContext';
import { StepShell } from './StepShell';
import { NavButtons } from './NavButtons';
import { Tabs } from '../ui/Tabs';
import { Field } from '../ui/Field';
import { NumberInput } from '../ui/NumberInput';
import { Select } from '../ui/Select';
import { Card, CardBody } from '../ui/Card';
import { SHIPPING_ZONES } from '../../lib/shippingRates';
import { fmtCurrency } from '../../lib/formatters';

type CostTab = 'feedVet' | 'processing' | 'shipping' | 'marketing' | 'storage';

const TABS: Array<{ value: CostTab; label: string }> = [
  { value: 'feedVet', label: 'Feed & Vet' },
  { value: 'processing', label: 'Processing' },
  { value: 'shipping', label: 'Shipping' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'storage', label: 'Storage' },
];

export function Step2Costs() {
  const { state, updateStep2, back, next } = useCalculator();
  const { step1, step2 } = state;
  const [tab, setTab] = useState<CostTab>('feedVet');

  const perAnimalDirectCost = useMemo(() => {
    const { feedVet, processing } = step2;
    const labor = feedVet.laborHours * feedVet.laborRate;
    const cutWrap = processing.cutWrapFeePerLb * (step1.liveWeight * step1.carcassYield);
    return (
      feedVet.feedCost +
      feedVet.vetCost +
      labor +
      processing.killFee +
      cutWrap +
      processing.transportToProcessor
    );
  }, [step1.liveWeight, step1.carcassYield, step2]);

  return (
    <StepShell
      eyebrow="Step 2 of 5"
      title="Your costs"
      description="Defaults pre-filled from your animal choice — adjust anything that doesn't match your operation."
    >
      <Tabs tabs={TABS} value={tab} onChange={setTab} />

      <Card className="mt-5">
        <CardBody>
          {tab === 'feedVet' && (
            <div className="grid sm:grid-cols-2 gap-5">
              <Field
                label="Feed Cost (per animal)"
                helpText="Total feed expense from start to finish for one animal."
              >
                <NumberInput
                  prefix="$"
                  decimals
                  value={step2.feedVet.feedCost}
                  onChange={(v) =>
                    updateStep2({ feedVet: { ...step2.feedVet, feedCost: Math.max(0, v) } })
                  }
                />
              </Field>
              <Field
                label="Vet & Health (per animal)"
                helpText="Vaccinations, dewormer, vet visits, and other animal health costs."
              >
                <NumberInput
                  prefix="$"
                  decimals
                  value={step2.feedVet.vetCost}
                  onChange={(v) =>
                    updateStep2({ feedVet: { ...step2.feedVet, vetCost: Math.max(0, v) } })
                  }
                />
              </Field>
              <Field
                label="Labor Hours (per animal)"
                helpText="Hours of labor across the animal's lifecycle — feeding, fence checks, moves, etc."
              >
                <NumberInput
                  suffix="hrs"
                  decimals
                  value={step2.feedVet.laborHours}
                  onChange={(v) =>
                    updateStep2({ feedVet: { ...step2.feedVet, laborHours: Math.max(0, v) } })
                  }
                />
              </Field>
              <Field
                label="Labor Rate"
                helpText="What you pay yourself or your team per hour. Many farmers under-pay themselves — use a fair number."
              >
                <NumberInput
                  prefix="$"
                  suffix="/hr"
                  decimals
                  value={step2.feedVet.laborRate}
                  onChange={(v) =>
                    updateStep2({ feedVet: { ...step2.feedVet, laborRate: Math.max(0, v) } })
                  }
                />
              </Field>
            </div>
          )}

          {tab === 'processing' && (
            <div className="grid sm:grid-cols-2 gap-5">
              <Field
                label="Kill Fee (per animal)"
                helpText="Flat slaughter fee charged by your processor."
              >
                <NumberInput
                  prefix="$"
                  decimals
                  value={step2.processing.killFee}
                  onChange={(v) =>
                    updateStep2({
                      processing: { ...step2.processing, killFee: Math.max(0, v) },
                    })
                  }
                />
              </Field>
              <Field
                label="Cut & Wrap (per lb of carcass)"
                helpText="Charge per hanging-weight pound for breaking down and packaging."
              >
                <NumberInput
                  prefix="$"
                  suffix="/lb"
                  decimals
                  value={step2.processing.cutWrapFeePerLb}
                  onChange={(v) =>
                    updateStep2({
                      processing: {
                        ...step2.processing,
                        cutWrapFeePerLb: Math.max(0, v),
                      },
                    })
                  }
                />
              </Field>
              <Field
                label="Transport to Processor"
                helpText="Fuel, trailer, and time to haul the live animal to the slaughterhouse."
              >
                <NumberInput
                  prefix="$"
                  decimals
                  value={step2.processing.transportToProcessor}
                  onChange={(v) =>
                    updateStep2({
                      processing: {
                        ...step2.processing,
                        transportToProcessor: Math.max(0, v),
                      },
                    })
                  }
                />
              </Field>
            </div>
          )}

          {tab === 'shipping' && (
            <div className="grid sm:grid-cols-2 gap-5">
              <Field
                label="Shipping Zone"
                helpText="USPS/UPS zones run 2 (local) to 8 (cross-country). Pick the average zone for your customers — Zone 4 is a reasonable national default."
              >
                <Select
                  options={SHIPPING_ZONES.map((z) => ({ value: z.value, label: z.label }))}
                  value={step2.shipping.zone}
                  onChange={(e) =>
                    updateStep2({
                      shipping: { ...step2.shipping, zone: Number(e.target.value) },
                    })
                  }
                />
              </Field>
              <Field
                label="Average Package Weight"
                helpText="Typical weight of a single shipped box. Heavier boxes ship more efficiently per pound."
              >
                <NumberInput
                  suffix="lbs"
                  decimals
                  value={step2.shipping.avgPackageWeight}
                  onChange={(v) =>
                    updateStep2({
                      shipping: { ...step2.shipping, avgPackageWeight: Math.max(0, v) },
                    })
                  }
                />
              </Field>
              <div className="sm:col-span-2 rounded-md bg-bg/60 border border-line p-3 text-sm text-muted">
                Shipping cost is interpolated from a real rate table for the chosen zone and box
                weight, then divided across pounds shipped.
              </div>
            </div>
          )}

          {tab === 'marketing' && (
            <div className="grid sm:grid-cols-2 gap-5">
              <Field
                label="Fixed Marketing (per batch)"
                helpText="Photography, design, print materials, market booth fees, and other one-time costs for this batch."
              >
                <NumberInput
                  prefix="$"
                  decimals
                  value={step2.marketing.marketingFixed}
                  onChange={(v) =>
                    updateStep2({
                      marketing: { ...step2.marketing, marketingFixed: Math.max(0, v) },
                    })
                  }
                />
              </Field>
              <Field
                label="Variable Marketing (% of revenue)"
                helpText="Ads, affiliate commissions, and other spend that scales with sales. 3–7% is typical for direct-to-consumer farms."
              >
                <NumberInput
                  suffix="%"
                  decimals
                  value={step2.marketing.marketingPctRevenue}
                  onChange={(v) =>
                    updateStep2({
                      marketing: {
                        ...step2.marketing,
                        marketingPctRevenue: Math.max(0, Math.min(100, v)),
                      },
                    })
                  }
                />
              </Field>
            </div>
          )}

          {tab === 'storage' && (
            <div className="grid sm:grid-cols-2 gap-5">
              <Field
                label="Cold Storage Cost (per lb / month)"
                helpText="Freezer rental, electricity, or shared cold-storage fees, expressed per pound per month."
              >
                <NumberInput
                  prefix="$"
                  suffix="/lb·mo"
                  decimals
                  value={step2.storage.coldStorageCostPerLb}
                  onChange={(v) =>
                    updateStep2({
                      storage: { ...step2.storage, coldStorageCostPerLb: Math.max(0, v) },
                    })
                  }
                />
              </Field>
              <Field
                label="Average Months in Storage"
                helpText="How long packaged product sits in the freezer before it sells, on average."
              >
                <NumberInput
                  suffix="mo"
                  decimals
                  value={step2.storage.avgMonthsInStorage}
                  onChange={(v) =>
                    updateStep2({
                      storage: { ...step2.storage, avgMonthsInStorage: Math.max(0, v) },
                    })
                  }
                />
              </Field>
            </div>
          )}
        </CardBody>
      </Card>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-white px-5 py-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted">
            Direct cost per animal
          </div>
          <div className="text-2xl font-bold text-navy">{fmtCurrency(perAnimalDirectCost)}</div>
        </div>
        <div className="text-xs text-muted max-w-xs text-right">
          Feed, vet, labor, and processing only. Shipping, marketing, and storage are added on the
          results page.
        </div>
      </div>

      <NavButtons onBack={back} onNext={next} />
    </StepShell>
  );
}
