# Product

## Register

brand

## Users

Small-to-mid farmers raising beef, hog, lamb, goat, chicken, or turkey for direct-to-consumer sale. Two profiles converge on the same tool:

- **Novices** — first-time or early direct sellers who genuinely don't know what to charge per pound. They're anxious about both undercharging (losing money on every sale) and overcharging (losing the customer). They need a defensible number and the math behind it.
- **Pros** — established farmers refining margins, validating pricing across channels (whole/half, retail cuts, bulk), or testing what a premium-production bump should actually be worth.

Context of use skews mobile and field-side. Many users are older, not deeply tech-fluent, and are filling this out on a phone between chores — sometimes with gloves on, sometimes in sunlight. The desktop case exists (an evening at the kitchen table), but mobile is the canvas to design for.

## Product Purpose

Help a farmer arrive at a confident, defensible price-per-pound for their farm-raised meat — and, in doing so, introduce them to From The Farm as the platform that will keep helping them after the calculator is done.

This is a lead-magnet tool with real math. The funnel only works if the calculator is genuinely useful: a farmer who walks away with a number they trust will remember the brand. A farmer who feels they wasted ten minutes will not. The calculator must earn the relationship before it asks for it.

Success looks like: a farmer completes all five steps, sees a recommended price they understand, can defend the number to a customer or spouse, saves or shares the result, and ends the session with From The Farm filed mentally as "the people who helped me figure that out."

## Brand Personality

**Trusted · Practical · Warm.** Like a knowledgeable neighbor who runs the numbers with you at the kitchen table. Confident, never condescending. Plainspoken, not folksy. Knows the difference between live weight and hanging weight without needing to show off about it.

Voice is direct and reassuring. Uses real numbers, real units, real defaults. Explains the tricky terms once, in plain language, and then trusts the farmer to keep up. Celebrates the moment a price comes together (the existing confetti is on-brand) but doesn't bounce around like a coach app. Optimism is earned, not performed.

## Anti-references

- **Cheap mortgage / insurance / "what's your home worth?" calculators.** Trust-bar gauges, neon CTAs, urgency timers, lead form as paywall, "92% of farmers like you charge more!" social-proof stings. None of it. The lead capture is real but it has to feel like a natural next step, not a bait-and-switch.
- **Childish or twee farm clip-art.** Cartoon barns, hand-drawn marker fonts, crayon-primary palettes, smiling-cow mascots, "Old MacDonald" energy. The farmers using this run real businesses; the tool should look like a real business tool that happens to be warm.
- **Generic SaaS dashboard reflexes.** Indigo gradients, identical KPI cards, hero-metric template, stock illustrations. The category-reflex result for "calculator" is a pastel SaaS dashboard, and that is exactly what this is not.

## Design Principles

1. **Real math first, marketing second.** Every screen has to be useful before it is persuasive. If a farmer would feel cheated by the result, the funnel is dead. Polish serves credibility, not the other way around.
2. **Smart defaults beat empty fields.** Pick an animal, get sensible numbers immediately. The farmer's job is to adjust what's wrong for their operation, never to source values from scratch. The existing `animalDefaults.ts` is the spirit of the whole tool.
3. **Plainspoken expertise.** Use the real terms (carcass yield, cut-and-wrap, hanging weight) because farmers know them — but always one short, plain explanation alongside, in the voice of someone who actually farms. Never jargon for jargon's sake; never dumbed-down either.
4. **Mobile-in-the-field is the default canvas.** Assume a phone, thumbs, sun, and limited patience. Touch targets generous, numbers large enough to read at arm's length, copy short enough to skim while distracted. Desktop inherits from mobile, not the other way around.
5. **From The Farm is the patron, not the protagonist.** The farmer's recommended price is the hero of every screen. The platform appears as a logical next step ("save this", "track changes over time", "list it for sale"), never as an interruption or a paywall.

## Accessibility & Inclusion

- **Target: WCAG 2.1 AA**, with extra care for older and non-tech-fluent users. AA contrast, full keyboard navigation, visible focus, `prefers-reduced-motion` respected for the confetti and any wizard transitions.
- **Touch targets ≥44px**, ideally larger on the animal picker and primary CTAs. Field-use means thumbs, sometimes gloved.
- **Plain language by default.** No jargon without an inline explanation. No copy that requires fluency in startup-speak ("seamlessly", "leverage", "unlock").
- **Mobile-first defaults.** Single-column flows, generous tap zones, inputs that summon the right keyboard (numeric for weights and dollars), no dense desktop tables shrunk down.
- **Color is never the only signal.** Status, validation, and channel comparisons must read through shape, label, or icon as well as hue — important for color-blind users and for low-contrast outdoor screens.
