# Zitting backyard – 3D renders

Photoreal renders of the *Zitting Concrete Pad 9.25.26* plan (2-sheet AutoCAD PDF, 3/16" = 1'-0").
Everything in the scene that comes from the plan is traced from the PDF's vector geometry.
That covers the 4' walk and its 6' control joints, the 36'×18' kitchen pad, the 30'×15' pavilion,
the U-shaped kitchen, the L-shaped hot-tub lounge with the 7'×7' tub, the dining nook with its 12"
mow strip, and every furniture position.

This folder is separate from the pricing calculator and nothing in the app imports it.

## From the owner's notes and site photos

- The hot-tub lounge is sunk 2'-0" below the yard.
- The plan's 7½" band around it is a sandy light red brick seat wall, 18" above the yard, with a
  rowlock cap.
- Steps go down on the south side where the existing step is. They are 5' wide with 4 risers of
  about 5¾", paver treads and brick risers.
- The house (two-story stucco, dark trim, wraparound back porch) and the existing back patio are
  placed and sized by eye from the photos. They are not part of the plan.

## Renders (`renders/`)

| File | View |
| --- | --- |
| `01-overview-southeast.jpg` | Aerial from the southeast corner |
| `02-from-the-back-door.jpg` | Matches the owner's photo from the back-door patio (4:3, ultra-wide) |
| `03-from-the-side-walk.jpg` | Matches the owner's photo from the 4' walk (4:3, ultra-wide) |
| `04-sunken-lounge.jpg` | Inside the sunken lounge |
| `05-lawn-to-pavilion.jpg` | Eye level from the lawn, looking north |
| `06-lounge.jpg` | Down into the lounge, pavilion beyond |
| `07-outdoor-kitchen.jpg` | Under the pavilion, U-shaped kitchen |
| `08-from-the-pavilion.jpg` | From the club chairs, looking out to the lawn and nook |
| `09-dining-nook.jpg` | Dining nook and mow strip |
| `10-west-walk.jpg` | From the west walk across the lawn |
| `11-overview-northwest.jpg` | Aerial from the northwest |
| `12-lawn-dusk.jpg`, `13-lounge-dusk.jpg` | After sunset with lights and fire tables on |
| `14-top-roof-on.jpg`, `15-top-roof-off.jpg` | Straight down, same scale/orientation as sheet 1 |
| `plan-sheet-1.jpg` | Sheet 1 cropped to the same frame as the top-down renders |

## Where the plan was silent (assumptions)

- Pavilion: cedar timber frame, 10×10 posts on steel bases, glulam beams, king-post trusses,
  tongue-and-groove ceiling, 6:12 gable, charcoal standing-seam roof, ~9' clear under the beams.
- Kitchen: 36" counters, stacked-stone base, light stone countertop, stainless doors/drawers.
- Pavers: 6"×12" gray/charcoal blend in 45° herringbone.
- Concrete: new work in natural gray broom finish; the mow strip is tinted charcoal.
- Furniture styles, the red-sand yard, fence, trees, neighbouring houses and distant cliffs are placeholders.

## Regenerating

Requires Python 3.11 (the `bpy` wheel is built for it).

```sh
pip install bpy shapely mapbox_earcut pymupdf pillow
python3 scripts/extract_plan.py plan.pdf drawings.json   # only if the plan changes
cd scripts
python3 render.py photo3,aerial_se,photo1,sunken,lawn_north,lounge,kitchen,pavilion_out,nook,walk_west,aerial_nw,lawn_north_dusk,lounge_dusk,top,top_noroof
python3 export_jpgs.py            # numbered JPEGs into ../renders
python3 export_gltf.py model.glb  # simplified web model (no grass/trees)
```

`SAMPLES`, `RX`/`RY` and `OUT` environment variables control quality, resolution and output folder.
Camera positions live in `scripts/views.py`. At 1920×1080 and 128 samples, one view takes about
7–15 minutes on 4 CPU cores.
