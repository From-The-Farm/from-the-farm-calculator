# Zitting backyard – 3D renders

Photoreal renders of the *Zitting Concrete Pad 9.25.26* plan (2-sheet AutoCAD PDF, 3/16" = 1'-0").
Everything in the scene that comes from the plan is traced from the PDF's vector geometry.
That covers the 4' walk and its 6' control joints, the 36'×18' kitchen pad, the 30'×15' pavilion,
the U-shaped kitchen, the herringbone lounge with the 7'×7' hot tub, the dining nook with its 12"
mow strip, and every furniture position.

This folder is separate from the pricing calculator and nothing in the app imports it.

## Renders (`renders/`)

| File | View |
| --- | --- |
| `01-overview-southeast.jpg` | Aerial from the southeast corner |
| `02-lawn-to-pavilion.jpg` | Eye level from the lawn, looking north |
| `03-lounge.jpg` | Lounge sofas and fire table, pavilion beyond |
| `04-hot-tub.jpg` | Hot tub corner |
| `05-outdoor-kitchen.jpg` | Under the pavilion, U-shaped kitchen |
| `06-from-the-pavilion.jpg` | From the club chairs, looking out to the lawn and nook |
| `07-dining-nook.jpg` | Dining nook and mow strip |
| `08-west-walk.jpg` | From the west walk across the lawn |
| `09-overview-northwest.jpg` | Aerial from the house side |
| `10-lawn-dusk.jpg`, `11-lounge-dusk.jpg` | After sunset with lights and fire tables on |
| `12-top-roof-on.jpg`, `13-top-roof-off.jpg` | Straight down, same scale/orientation as sheet 1 |
| `plan-sheet-1.jpg` | Sheet 1 cropped to the same frame as the top-down renders |

## Where the plan was silent (assumptions)

- Pavilion: cedar timber frame, 10×10 posts on steel bases, glulam beams, king-post trusses,
  tongue-and-groove ceiling, 6:12 gable, charcoal standing-seam roof, ~9' clear under the beams.
- Kitchen: 36" counters, stacked-stone base, light stone countertop, stainless doors/drawers.
- Pavers: 6"×12" gray/charcoal blend in 45° herringbone; 8"×16" charcoal border in the lounge.
- Concrete: natural gray broom finish; the mow strip is tinted charcoal.
- Furniture styles, the fence, trees and neighbouring houses are placeholders. The house is not modelled.

## Regenerating

Requires Python 3.11 (the `bpy` wheel is built for it).

```sh
pip install bpy shapely mapbox_earcut pymupdf pillow
python3 scripts/extract_plan.py plan.pdf drawings.json   # only if the plan changes
cd scripts
python3 render.py aerial_se,lawn_north,lounge,hottub,kitchen,pavilion_out,nook,walk_west,aerial_nw,lawn_north_dusk,lounge_dusk,top,top_noroof
```

`SAMPLES`, `RX`/`RY` and `OUT` environment variables control quality, resolution and output folder.
Camera positions live in `scripts/views.py`. At 1920×1080 and 128 samples, one view takes about
7–15 minutes on 4 CPU cores.
