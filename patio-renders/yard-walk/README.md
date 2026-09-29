# Yard walk-through (Gaussian splat + plan)

A walkable 3D reconstruction of the backyard, built from the owner's phone video, with the 9.25.26 plan
and the Sept 28 ideas placed in it at true size. The ideas are the gray vinyl fence all the way around,
a 24"/30" black privacy screen on the sunken lounge, turf with a putting green and fire pit (or a summer
pool) where the garden is, bubbling boulder fountains and an office path. The viewer also lets the owner
draw paths and areas and describe them, and saves those marks for Claude.

Nothing in this folder is imported by the pricing calculator. The video, its frames, the reconstruction
and the satellite screenshot are private, so they are **not** committed. Only the code is here.

## Pipeline

| Step | Code | Notes |
| --- | --- | --- |
| Get the video in | `upload/index.html` | Artifact page. Decodes the MP4 in the browser (WebCodecs + mp4box.js), keeps the sharpest frame per window and uploads JPEG sheets to the artifact's asset store. |
| Camera poses | `gs/sfm.py`, `gs/reverify.py`, `gs/retrieval_pairs.py`, `gs/match_pairs.py`, `gs/map_global.py` | pycolmap on CPU. Uses sequential matching, re-verification against a calibrated camera, VLAD retrieval pairs for loop closure, then global mapping and undistortion. 570 of 601 frames registered. |
| Splat training | `gs/raster.cpp`, `gs/model.py`, `gs/train.py` | CPU 3D Gaussian splatting. The rasteriser, projection, SH, Adam and L1+SSIM loss are fused in C++ with OpenMP and AVX-512, and checked against a torch reference (`gs/test_*.py`). Standard densify, prune and opacity-reset schedule; 15k steps, about 820k Gaussians. Run with `OMP_WAIT_POLICY=PASSIVE`. |
| Levelling and metric scale | `align/level_g2.py`, `align/fence_metrology.py`, `align/depth_pick.py`, `align/camheight.py` | Levels on the camera path. Scale comes from single-view fence-height metrology (6 ft vinyl), the office's French doors, camera height and the Google Maps view. They agree to within about ±8%. |
| Plan placement | `align/frames.py`, `align/fit_sim.py`, `align/ortho.py`, `align/proj_plan.py` | Places the plan with a similarity transform, anchored on the east vinyl fence, the north fence and the porch corner (the lounge's L-notch wraps the porch). It is checked by a true orthophoto from the frames and by projecting the plan into video frames. An ICP of the plan's walk ring onto the walked path lands on the same transform, with 0.2–0.3 m residuals on the east and north walks. |
| Design model | `../scripts/export_design.py`, `../scripts/additions.py` | Blender (bpy 5). Builds the plan from the PDF geometry plus the additions, draped on the reconstructed ground. Every object is prefixed with the viewer layer it belongs to (`plan_`, `roof_`, `fence_`, `screen24_`, `screen30_`, `turf_`, `pool_`, `fountain_`, `path_`). |
| Web export | `gs/export_final.py`, `gs/export_web.py`, `align/ground_plan.py` | Writes splats in plan metres, quantised and base64 JSON-chunked. Adds per-splat hide flags (under the plan, the garden, old fences, fountain beds, tall canopy in the aerial views, haze), walk heightfields for today and the plan, the porch deck, blocked cells, and top-down minimaps. |
| Viewer | `viewer/index.html` | three.js with its own splat shader (instanced quads, a worker-side counting sort) and the design as glTF. Walk, fly and top modes, layer toggles, and a markup tool that saves marks to the artifact database under `marks/<id>`. |
| Lawn sprinklers | `irr/layout.py`, `irr/final_layout.py`, `irr/system.py`, `irr/make_page.py` | Places head-to-head Hunter MP3000 rotary heads on the plan's lawn: corners and edges first, then greedy interior heads. Arcs come from the edge geometry. Positions and radii are tuned on a simulated catch-can grid (lower-quarter DU about 0.87, about 3% overspray). Then zones are balanced by flow, zone pipes run 12" inside the lawn edge, and pipes are sized by velocity with a Hazen-Williams check. The mainline, sleeves and parts list are built from the tie-in (the capped kitchen riser seen in the video) to the PVB and valve box by the east fence. Writes the viewer layer data and the printable plan page. |

## Things the owner should know

- Placement is good to roughly half a metre in the main yard; the far corners are less certain.
- The plan's south-west walk corner runs about 2 m past the existing diagonal fence by the gates. The fence
  is left standing in the viewer so the conflict is visible.
- The plan's north-east walk corner clips the big boulder by the power pole.
- The fountain boulders are modelled stand-ins, placed at the size and spot of the real rocks.
- The sprinkler tie-in assumes the capped riser under the planned kitchen counter is live house water; confirm it (and
  the pressure and flow) before buying parts. Two sleeves must go under the new pad and east walk before they are poured.
