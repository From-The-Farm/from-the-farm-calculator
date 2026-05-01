---
name: From The Farm Pricing Calculator
description: A 5-step wizard that helps farmers price farm-raised meat with confidence — designed as a kitchen-table almanac, not a SaaS calculator.
colors:
  almanac-navy: "#1B3A6B"
  bulletin-gold: "#B5965A"
  field-green: "#16A34A"
  stable-amber: "#D97706"
  barn-red: "#DC2626"
  almanac-paper: "#F8F6F1"
  press-ink: "#1A1A1A"
  margin-note: "#6B6B6B"
  page-rule: "#E5E0D5"
  paper-white: "#FFFFFF"
typography:
  display:
    fontFamily: "Oswald, system-ui, sans-serif"
    fontSize: "clamp(1.875rem, 5vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Oswald, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "normal"
  title:
    fontFamily: "Oswald, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.01em"
  body:
    fontFamily: "Lato, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  body-strong:
    fontFamily: "Lato, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Lato, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.08em"
  button:
    fontFamily: "Oswald, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.04em"
  eyebrow:
    fontFamily: "Lato, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.1em"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  wizard-max: "720px"
components:
  button-primary:
    backgroundColor: "{colors.almanac-navy}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.lg}"
    padding: "0 20px"
    height: "48px"
    typography: "{typography.button}"
  button-primary-hover:
    backgroundColor: "#173360"
  button-primary-disabled:
    backgroundColor: "#1B3A6B66"
  button-gold:
    backgroundColor: "{colors.bulletin-gold}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.lg}"
    padding: "0 20px"
    height: "48px"
    typography: "{typography.button}"
  button-secondary:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.almanac-navy}"
    rounded: "{rounded.lg}"
    padding: "0 20px"
    height: "48px"
    typography: "{typography.button}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.almanac-navy}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "40px"
    typography: "{typography.button}"
  card:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.press-ink}"
    rounded: "{rounded.lg}"
    padding: "20px 24px"
  animal-tile:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.almanac-navy}"
    rounded: "{rounded.lg}"
    padding: "16px"
    height: "112px"
  animal-tile-active:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.almanac-navy}"
    rounded: "{rounded.lg}"
    padding: "16px"
    height: "112px"
  input-text:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.press-ink}"
    rounded: "{rounded.lg}"
    padding: "12px"
  badge-navy:
    backgroundColor: "#1B3A6B1A"
    textColor: "{colors.almanac-navy}"
    rounded: "{rounded.pill}"
    padding: "2px 10px"
    typography: "{typography.label}"
  badge-gold:
    backgroundColor: "#B5965A26"
    textColor: "{colors.bulletin-gold}"
    rounded: "{rounded.pill}"
    padding: "2px 10px"
    typography: "{typography.label}"
  tab-active:
    backgroundColor: "{colors.almanac-navy}"
    textColor: "{colors.paper-white}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
    typography: "{typography.button}"
  tab-inactive:
    backgroundColor: "{colors.paper-white}"
    textColor: "{colors.margin-note}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "44px"
    typography: "{typography.button}"
  toggle-on:
    backgroundColor: "{colors.almanac-navy}"
    rounded: "{rounded.pill}"
    width: "48px"
    height: "28px"
  toggle-off:
    backgroundColor: "{colors.page-rule}"
    rounded: "{rounded.pill}"
    width: "48px"
    height: "28px"
  progress-track:
    backgroundColor: "{colors.page-rule}"
    rounded: "{rounded.pill}"
    height: "8px"
  progress-fill:
    backgroundColor: "{colors.bulletin-gold}"
    rounded: "{rounded.pill}"
    height: "8px"
---

# Design System: From The Farm Pricing Calculator

## 1. Overview

**Creative North Star: "The Kitchen-Table Almanac"**

Imagine a farm extension-office bulletin or a county almanac — cream stock, navy ink, a gold seal — but redesigned with the care of a contemporary editorial team. That's the canvas. The page is a warm cream the eye can rest on for ten minutes without fatigue. The display type is condensed and confident, like the masthead on a working publication. Color is rationed: navy carries authority, gold marks what matters, status hues only show up when a number is telling the farmer something. The result is a tool that reads as a real reference document, not a SaaS dashboard.

Three things this system explicitly rejects. It is **not** a cheap mortgage-calculator descendant — no neon CTAs, no "92% of farmers like you charge more!" trust bars, no urgency timers, no lead-form-as-paywall. It is **not** twee farm clip-art — no cartoon barns, no marker fonts, no crayon palette, no smiling-cow mascot. And it is **not** the pastel SaaS calculator that the category-reflex would produce — no indigo gradient hero card, no identical-grid KPI tiles, no stock illustration of a happy farmer. The visual language belongs to the world of working agricultural tools, not the world of growth-marketing landing pages.

**Key Characteristics:**

- Cream paper background everywhere — `almanac-paper` (`#F8F6F1`) is the canvas, not a card.
- Two-color authority structure: navy for action and weight, gold for emphasis and progress.
- Condensed-display + humanist-sans pairing (Oswald + Lato) — the masthead and the article body.
- Generous touch targets and large numbers — designed for thumbs in the field.
- Layered elevation: cards lift, the active animal tile rings up, the primary CTA carries weight.
- Status colors (green / amber / red) appear only when a number is telling a story.

## 2. Colors: The Almanac Palette

A farm bulletin's palette: cream paper, navy ink, gold seal, status hues borrowed from the field.

### Primary

- **Almanac Navy** (`#1B3A6B`): The publication's authority color. Headlines, primary CTA, active states, the toggle "on" rail, the active tab fill. The voice that says *this is what we recommend*. About 15–20% of any screen.
- **Bulletin Gold** (`#B5965A`): The wax-seal accent. Eyebrow labels, the progress bar fill, the celebrating CTA, the ring on a selected animal tile. Reserved for moments of emphasis and progress — never as a fill on long-form text. About 5% of any screen.

### Tertiary — Status

Status hues are signals, not decoration. They appear when a number is communicating something to the farmer — a healthy margin, a thin one, a loss. Never used decoratively; never used as a brand accent.

- **Field Green** (`#16A34A`): Profit, healthy margin, success.
- **Stable Amber** (`#D97706`): Thin margin, caution, "watch this number".
- **Barn Red** (`#DC2626`): Loss, error, "this won't work".

### Neutral

- **Almanac Paper** (`#F8F6F1`): The page. Always the body background. Never `#fff` for the canvas.
- **Paper White** (`#FFFFFF`): Cards, inputs, animal tiles, the header, the footer. The slightly-elevated layer that sits on the cream.
- **Press Ink** (`#1A1A1A`): Body text, input values, headlines that aren't navy.
- **Margin Note** (`#6B6B6B`): Help text, eyebrow alternatives, the "step X of 5" counter, tab-inactive labels. Secondary voice.
- **Page Rule** (`#E5E0D5`): Dividers, card borders, default input strokes, the progress track, the toggle "off" rail. Warm-cream-tinted — never a flat gray.

### Named Rules

**The Two-Color Rule.** Navy and gold do all the brand work. Together they cover at most 25% of any given screen. Status hues are signals layered on top of that — never a third brand color.

**The Cream-Canvas Rule.** The body is `almanac-paper`, never `#fff`. White is reserved for elevated surfaces (cards, inputs, the header bar). The cream-on-white contrast IS the elevation cue. Reversing the two — white body with cream cards — collapses the whole metaphor.

**The Status-as-Story Rule.** Green / amber / red appear only when a number is making a recommendation. A green badge that just means "saved" is a misuse. A green badge under "Your margin: $4.20/lb" is correct.

## 3. Typography

**Display Font:** Oswald (system-ui, sans-serif fallback)
**Body Font:** Lato (system-ui, sans-serif fallback)

**Character:** A condensed-display masthead set against a humanist-sans body — the same pairing logic as a working trade publication. Oswald is upright, slightly narrowed, and authoritative; it carries headlines, button labels, animal-tile names, and active tabs in uppercase with restrained letterspacing. Lato is round, friendly, highly legible at small sizes; it carries everything a farmer actually reads — help text, descriptions, input values. The pairing reads as serious-but-approachable. Lowercase Lato body keeps the tone neighborly; uppercase Oswald headlines keep the tool feeling like real publication, not a chat app.

### Hierarchy

- **Display** (Oswald 700, `clamp(1.875rem, 5vw, 2.25rem)`, line-height 1.1, slight negative tracking): Step titles ("Pick your animal", "Your recommended price"). One per screen, always uppercase, always navy.
- **Headline** (Oswald 600, 1.5rem, line-height 1.2): Section breaks within a step. Uppercase navy.
- **Title** (Oswald 600, 1.125rem, +0.01em tracking): Group labels inside a step (e.g. an animal-tile label, a card header). Uppercase, navy.
- **Body** (Lato 400, 1rem, line-height 1.5): All running text — descriptions, help text, results copy. Press-ink on cream. Cap line length at 65–75ch.
- **Body Strong** (Lato 700, 1rem): Field labels, in-line emphasis, the active price number when not displayed at hero scale.
- **Label** (Lato 700, 0.75rem, +0.08em tracking, uppercase): Form field labels, badge text. Functional shouting, used sparingly.
- **Eyebrow** (Lato 700, 0.75rem, +0.1em tracking, uppercase, gold): The "Step 1 of 5" line above a title. Always gold, always uppercase, always exactly one line above a Display heading.
- **Button** (Oswald 600, 0.9375rem, +0.04em tracking, uppercase): Every button. Uppercase Oswald is the action voice of the system.

### Named Rules

**The Masthead-and-Article Rule.** Oswald and Lato never trade jobs. Headlines are always Oswald uppercase; body is always Lato sentence-case. Reversing them — Lato uppercase headlines or Oswald body copy — collapses the publication metaphor.

**The Eyebrow-Then-Title Rule.** Every step opens with an eyebrow (gold uppercase) directly above a Display title (navy uppercase). Two lines. The pattern is the front page of every bulletin section — never breach it.

## 4. Elevation

Layered. Shadows do real work in this system: they signal which surface the eye should land on next. There are two shadow tokens — a soft ambient lift for cards at rest, and a stronger pop for selected and hovered states. Both are tinted with `almanac-navy` at low opacity, so depth never reads as a generic gray drop-shadow but as a publication's own ink bleeding through paper.

The header and footer sit on `paper-white` against the cream body, separated by a single-pixel `page-rule` divider — flat, no shadow. Cards lift off the cream with `card`. Animal tiles use `card` at rest and `pop` on the active tile; the gold ring around the active tile is layered on top of the pop shadow so the selection reads at a glance. The primary CTA carries the same `card` shadow on hover, which gives the press a small but real sense of weight.

### Shadow Vocabulary

- **card** (`box-shadow: 0 1px 2px rgba(27, 58, 107, 0.06), 0 4px 12px rgba(27, 58, 107, 0.08)`): The default lift for any surface that should read as "elevated paper" — wizard cards, animal tiles at rest, the results dashboard frame.
- **pop** (`box-shadow: 0 8px 24px rgba(27, 58, 107, 0.18)`): The selected / hovered / focused lift. The active animal tile, the primary CTA on hover, anything the system is calling attention to.

### Named Rules

**The Two-Shadow Rule.** Card and pop are the only two shadow tokens. Anything that needs more elevation than `pop` should be a navy fill or a gold ring instead — not a deeper shadow. Stacking shadows or inventing a third elevation is forbidden.

**The Navy-Tint Rule.** Every shadow's RGB is `27, 58, 107` — `almanac-navy`. A flat-gray `rgba(0,0,0,...)` shadow is forbidden anywhere in the system. The tint is the difference between a publication's printed lift and a generic 2014 SaaS card.

## 5. Components

### Buttons

A button is the action voice of the calculator. Always uppercase Oswald, always at least 40px tall (48px for primary), always with enough horizontal padding to read at arm's length on a phone in the field.

- **Shape:** Lozenge with gentle 8px radius (`rounded.lg`). Never pill-shaped (reads cheap), never sharp-cornered (reads enterprise).
- **Primary** (`button-primary`): Navy fill (`almanac-navy`), white text, 48px tall, 20px horizontal padding. The default for any forward-momentum action — "Continue", "Calculate", "Save profile".
- **Gold** (`button-gold`): Bulletin-gold fill, white text. Reserved for celebratory or final-action moments — most often the primary CTA on the Results step. Never used twice on the same screen.
- **Secondary** (`button-secondary`): White fill, navy text, 1px navy-tinted border (`#1B3A6B33`). The companion to a primary — "Save for later", "Edit costs". Hover deepens the border to `#1B3A6B80`.
- **Ghost** (`button-ghost`): Transparent fill, navy text, no border. Tertiary actions — "Back", "Reset", inline edit triggers. 40px tall, 16px horizontal padding.
- **Hover / Focus:** Hover slightly darkens the fill (5–10%) and applies the `card` shadow on filled buttons; focus shows a 2px gold ring (`#B5965A66`) at a 2px offset against the cream canvas. The same focus ring everywhere — predictable for keyboard users.
- **Disabled:** 40% opacity, no shadow, `cursor: not-allowed`. Never gray-out by switching the fill to a neutral; preserve the original color at lower opacity so the meaning of the action is still legible.

### Animal Tile

The signature component. The Step 1 picker that sets the tone of the whole calculator.

- **Shape:** 8px radius, 112px minimum height, 1px `page-rule` border at rest.
- **At rest:** White fill, large emoji (3xl) centered above the label (Oswald uppercase, navy, +0.02em tracking). Hover deepens the border to navy/40 — no shadow change.
- **Active (selected):** Border switches to `bulletin-gold`, a 2px gold ring at 40% opacity surrounds the tile, and the `card` shadow is applied. Framer-motion spring (stiffness 400, damping 22) handles the scale on tap (0.97) and hover (1.04). The interaction must feel mechanical and confident, never bouncy.
- **Emoji is decorative.** Always paired with `aria-hidden="true"`; the label carries the accessible name.

### Cards / Containers

- **Corner Style:** 8px radius (`rounded.lg`).
- **Background:** `paper-white` on the `almanac-paper` body.
- **Border:** 1px `page-rule` at rest. Never a colored stripe — see Don'ts.
- **Shadow Strategy:** `card` at rest, `pop` on hover or selected state. See Elevation section.
- **Internal Padding:** 20px on mobile, 24px on tablet+ (`p-5 sm:p-6` in code). The Card primitive's `CardHeader` adds a `page-rule` divider below — the only place a horizontal rule appears inside a card.

### Inputs / Fields

A farmer types numbers under sunlight on a phone. Every input is built around that.

- **Style:** 1px `page-rule` border, white fill, 8px radius, 12px vertical padding (taller than the SaaS norm — easier to tap), 16px text size. Always min 44px tall.
- **Focus:** Border shifts to `almanac-navy`, with a 2px gold ring at 40% opacity (`ring-gold/40`). The ring is the same as the global focus ring on every other interactive element — keyboard users see one consistent affordance.
- **Error:** Border switches to `barn-red`; the focus ring stays gold but the helper text below the field carries the red voice. Never show error state via background fill.
- **Numeric inputs:** Always invoke a numeric keyboard on mobile (`inputMode="decimal"`); right-align unit suffixes ("lbs", "%", "$") inside the field.
- **Disabled:** 50% opacity, no border-color change. Same logic as buttons — preserve meaning.

### Toggle (Switch)

- **Shape:** Pill rail, 48×28px. Knob is 20px white circle with `card` shadow.
- **On:** Rail is `almanac-navy`, knob translated 24px right.
- **Off:** Rail is `page-rule`, knob translated 4px right.
- **Label:** To the right of the rail, Body Strong above optional Body description. Tap the whole label, not just the rail — entire row is the hit target.

### Tabs / Segmented

The tabbed channel-comparison control on the Results step uses the same vocabulary.

- **Active:** Navy fill, white text, 8px radius, 44px tall, Oswald uppercase.
- **Inactive:** White fill, `margin-note` text, 1px `page-rule` border. Hover: text shifts to navy.
- **Layout:** Horizontal scroll on mobile (`overflow-x-auto`, `-mx-4 px-4`), full row on tablet+. Never wrap to two rows.

### Badges

Subtle tinted pills. Each `tone` uses a 10–15% tint of its base color as fill, with the saturated color as the text.

- **Tones:** navy, gold, green, amber, red, muted (`page-rule` fill, `margin-note` text).
- **Size:** Pill (`rounded-full`), 10px horizontal padding, 2px vertical padding, Label typography.
- **Use:** Status pills on the results page (margin tier, channel tag), "premium production" callout, etc. Never as a button substitute.

### Progress Bar

A sentence and a track. Both carry meaning.

- **Eyebrow row:** "Step 3 of 5" (margin-note) on the left, the step name (navy) on the right. Both are Label typography.
- **Track:** 8px tall, full width of the wizard container, `page-rule` fill, `pill` radius.
- **Fill:** `bulletin-gold`, animated with framer-motion (`duration: 0.4, ease: 'easeOut'`). Never use navy for the fill — gold is the progress signal across the system.
- **Step labels (below the track):** Five evenly-distributed labels in Label typography. Completed steps: navy bold. Current step: press-ink bold. Future steps: margin-note. The hierarchy must read at a glance.

## 6. Do's and Don'ts

### Do:

- **Do** keep `almanac-paper` (`#F8F6F1`) as the body canvas everywhere. The cream-on-white elevation cue is half the system.
- **Do** open every step with a gold eyebrow above a navy uppercase Display title. Two lines. No exceptions.
- **Do** use `bulletin-gold` for the progress bar fill — it's the progress signal across the calculator, not a brand decoration.
- **Do** tint every shadow with `rgba(27, 58, 107, ...)`. Pure black or gray shadows are forbidden.
- **Do** use Oswald uppercase for every button, headline, and active tab. Lato sentence-case for everything a farmer reads.
- **Do** keep status colors (green / amber / red) reserved for moments where a number is telling a story. Never decorative.
- **Do** size touch targets at ≥44px and prefer 48px for primary actions. A glove or thumb in the field has to land it.
- **Do** quote PRODUCT.md's voice in copy: trusted, practical, warm. Plainspoken expertise. Never startup-speak.
- **Do** use the same gold focus ring (`ring-gold/40`, 2px, 2px offset) on every interactive element — buttons, inputs, animal tiles, toggles.

### Don't:

- **Don't** drift toward the cheap mortgage-calculator family — no trust-bar gauges, no neon CTAs, no urgency timers, no "92% of farmers like you charge more!" social-proof stings, no lead-form-as-paywall. Lead capture is real but it must feel earned.
- **Don't** drift toward twee farm clip-art — no cartoon barns, no smiling-cow mascots, no marker / hand-drawn fonts, no crayon-primary palette, no "Old MacDonald" energy.
- **Don't** drift toward generic SaaS — no indigo gradients, no hero-metric template (big number / small label / supporting stats / gradient accent), no identical KPI grid, no stock illustration of a happy farmer.
- **Don't** use side-stripe borders. A `border-left` greater than 1px as a colored accent on cards or callouts is forbidden — rewrite with full borders, fills, or leading icons. (Universal impeccable ban; especially tempting in calculator results — don't.)
- **Don't** use gradient text. `background-clip: text` with a gradient is forbidden. Emphasis comes from weight, size, and color — never from a multi-stop gradient on letterforms.
- **Don't** swap Oswald and Lato's roles. Lato uppercase headlines or Oswald body copy collapses the masthead-and-article metaphor.
- **Don't** introduce a third brand color. Navy and gold are the two-color authority of the system. New status colors require a real new signal, never a brand mood.
- **Don't** add a third elevation shadow. Card and pop are the whole vocabulary — anything that needs more lift becomes a fill or a ring.
- **Don't** use `#000` or `#fff` on the body canvas. The body is always `almanac-paper`. White is reserved for elevated surfaces.
- **Don't** use modal-as-first-thought. Inline disclosures, tooltips on field labels, and progressive reveal beat a modal almost every time in a calculator wizard.
- **Don't** use em dashes in copy. Use commas, colons, semicolons, periods, or parentheses.
