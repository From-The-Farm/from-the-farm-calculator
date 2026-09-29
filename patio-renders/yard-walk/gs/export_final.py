"""Final web export: splat in plan metres with layer flags, walk heightfields, minimap, places -> viewer/data.
python3 gs/export_final.py CKPT OUT_DIR"""
import os, sys, json, math, base64, shutil
import numpy as np, torch
sys.path.insert(0, 'align'); sys.path.insert(0, 'gs'); sys.path.insert(0, '../scripts')
import frames as F, export_web as X
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import contains_xy
import plan as PL

CK, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
C0 = 0.28209479177387814

# ------------------------------------------------------------------ splat -> plan frame
st = torch.load(CK, map_location='cpu')
M = st['means'].double().numpy()
Lv = (M - F.C0 * F.S) @ F.RL.T
Pp = F.lev2plan(Lv)                                        # plan metres
Rw = F.RZ @ F.RL                                           # rotation world -> plan
q = torch.nn.functional.normalize(st['quats'].float(), dim=1)
qR = torch.tensor(X.rotmat_to_quat(Rw), dtype=torch.float32)[None].repeat(q.shape[0], 1)
quats = torch.nn.functional.normalize(X.quat_mul(qR, q), dim=1)
P = dict(means=torch.tensor(Pp, dtype=torch.float32), quats=quats, scales=st['scales'].float() + math.log(F.K),
         opac=torch.sigmoid(st['opac'].float()), rgb=torch.clamp(st['sh'][:, 0].float() * C0 + 0.5, 0, 1))
x, y, z = Pp[:, 0], Pp[:, 1], Pp[:, 2]
print('splats', len(x))

# ------------------------------------------------------------------ layer flags
FL_PLAN, FL_GARDEN, FL_FENCE, FL_PATHS, FL_AIR, FL_HAZE, FL_FOUNT = 1, 2, 4, 8, 16, 32, 64
flags = np.zeros(len(x), np.uint8)
foot = unary_union([PL.OUTER, PL.LOUNGE_OUT]).buffer(-0.30, join_style=2)
m = contains_xy(foot, x, y) & (z < 5.5)
flags[m] |= FL_PLAN
TURF = box(-24.5, 7.4, -12.4, 14.8)
m = contains_xy(TURF.buffer(-0.08), x, y) & (z < 3.5)
flags[m] |= FL_GARDEN
FENCE_LINE = [(11.57, 15.45), (-34.0, 15.25), (-34.0, 3.0)]
# height above today's ground, for floater handling over the open yard
g_ = np.load('align/ground_plan.npz'); Hg = g_['H']
gi = np.clip(((x - g_['x0']) / g_['cell']).round().astype(int), 0, Hg.shape[1] - 1); gj = np.clip(((y - g_['y0']) / g_['cell']).round().astype(int), 0, Hg.shape[0] - 1)
hag = z - Hg[gj, gi]
opac_np = P['opac'].numpy()
OPEN = unary_union([PL.OUTER, PL.LOUNGE_OUT, box(-24.5, 7.4, -12.4, 14.8), box(-34, 3, -12, 15.2), box(-8, 12.5, 11.5, 15.3)])
inside_open = contains_xy(OPEN, x, y)
site = (x > -36.5) & (x < 12.8) & (y > -21.5) & (y < 17.0)
flags[(hag > 2.4) | ~site] |= FL_AIR       # tree canopies, roofs, sky: hidden in the fly-around / from-above views
flags[inside_open & (hag > 0.8) & (opac_np < 0.18)] |= FL_HAZE  # faint haze over the open yard: always hidden
# fountain beds: clear the weeds round the two boulders (keep the red rock itself)
rgb_np = P['rgb'].numpy()
redrock = (rgb_np[:, 0] > rgb_np[:, 1] + 0.10) & (rgb_np[:, 0] > rgb_np[:, 2] + 0.16) & (rgb_np[:, 0] > 0.33)
SOUTH_BED = box(4.6, -19.55, 11.3, -14.40).buffer(-0.35, join_style=1).buffer(0.35, join_style=1)
NORTH_BED = box(6.4, 14.30, 11.3, 15.15)
for region, (cx, cy), zb in ((SOUTH_BED, (9.17, -18.40), 0.47), (NORTH_BED, (9.83, 14.34), 0.17)):
    bedz = np.minimum(Hg[gj, gi], zb) + 0.02
    rockzone = np.hypot((x - cx) / 0.95, (y - cy) / 0.95) < 1.0                   # the modelled fountain rock replaces the real one here
    m = (contains_xy(region, x, y) | rockzone) & (z < bedz + 1.8)
    flags[m] |= FL_FOUNT
d = X.dist_to_polyline(x, y, FENCE_LINE)
wide = (x > -18.5) & (x < -12.0)                           # trellis panels stand a little proud of the line
m = ((d < 0.45) | (wide & (d < 0.8))) & (z < 1.95) & (hag > 0.10)
m &= np.hypot(x - 10.01, y - 14.66) > 0.95                 # keep the north boulder
flags[m] |= FL_FENCE
# the plan's south-west walk corner runs ~2 m past the existing diagonal gate fence: keep that fence standing so the conflict shows
FENCE_C = [(-4.25 - 0.73 * 4, -7.76 + 0.68 * 4), (-4.25 + 0.73 * 17, -7.76 - 0.68 * 17)]
fc = (X.dist_to_polyline(x, y, FENCE_C) < 0.35) & (hag > 0.25) & (hag < 2.3)
flags[fc] &= np.uint8(255 - FL_PLAN)
print('diagonal fence kept', int((fc & contains_xy(foot, x, y)).sum()))
OFFICE_PATH = [(-20.1, 4.75), (-22.6, 5.05), (-25.0, 5.85), (-26.9, 7.2), (-28.15, 8.75), (-28.55, 9.6)]
m = (X.dist_to_polyline(x, y, OFFICE_PATH) < 0.60) & (z < 0.35)
flags[m] |= FL_PATHS
for k, v in (('plan', FL_PLAN), ('garden', FL_GARDEN), ('fence', FL_FENCE), ('paths', FL_PATHS), ('air', FL_AIR), ('haze', FL_HAZE), ('fountain', FL_FOUNT)):
    print('flag', k, int(((flags & v) > 0).sum()))

# ------------------------------------------------------------------ encode splats
keep = torch.ones(len(x), dtype=torch.bool)
far = np.hypot(x + 8, y) > 400
keep[torch.from_numpy(far)] = False
junk = np.load('align/junk_mask.npy')     # sky seen through leaves hanging at tree height, blobs floating right on the camera path
keep[torch.from_numpy(junk)] = False
print('dropped junk', int(junk.sum()))
header, files, idx = X.encode(P, torch.from_numpy(flags), OUT, name='splat', min_opac=0.02, chunk_bytes=11_500_000, keep=keep)
print('encoded', header['count'], files)

# ------------------------------------------------------------------ heightfields (0.25 m)
sel = (P['opac'].numpy() > 0.4) & (np.exp(P['scales'].numpy()).max(1) < 0.2) & (z > -3) & (z < 2.2)
BOUNDS = (-38.0, -24.0, 16.0, 22.0)
info, today = X.heightfield(Pp[sel], BOUNDS, cell=0.25, q=0.15, min_pts=3)
# extra smoothing for walking
for _ in range(3):
    Pd = np.pad(today, 1, mode='edge'); today = (0.4 * today + 0.15 * (Pd[:-2, 1:-1] + Pd[2:, 1:-1] + Pd[1:-1, :-2] + Pd[1:-1, 2:])).astype(np.float32)
nx, ny, cell = info['nx'], info['ny'], info['cell']
gx = info['x0'] + np.arange(nx) * cell; gy = info['y0'] + np.arange(ny) * cell
GX, GY = np.meshgrid(gx, gy)
plan = today.copy()
ring = PL.OUTER
plan[contains_xy(PL.OUTER, GX, GY)] = 0.03
plan[contains_xy(PL.LAWN, GX, GY)] = 0.0
# sunken lounge: wall ring at seat height, floor 2 ft down, stair treads from the south lawn
SUNK, Z_TOP = 0.61, 0.03
Z_FLOOR = Z_TOP - SUNK
plan[contains_xy(PL.LOUNGE_OUT, GX, GY)] = 0.46
inner = PL.LOUNGE_OUT.buffer(-0.19, join_style=2)
plan[contains_xy(inner, GX, GY)] = Z_FLOOR
json_st = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'design', 'stair.json')))
sx0, sx1, ytop, ybot = json_st['x0'], json_st['x1'], json_st['y_top'], json_st['y_bot']
inst = (GX >= sx0) & (GX <= sx1) & (GY >= ytop - 0.05) & (GY <= ybot + 0.05)
frac = np.clip((GY - ytop) / max(1e-3, (ybot - ytop)), 0, 1)
plan[inst] = (Z_TOP + (Z_FLOOR - Z_TOP) * np.minimum(np.floor(frac * 4 + 0.5) / 4, 1.0))[inst]
# hot tub, kitchen counters, fire table: not walkable (tall)
for r, h in ((PL.HOT_TUB, Z_FLOOR + 0.95), (PL.COUNTER_BACK, 0.95), (PL.COUNTER_TOP, 0.95), (PL.COUNTER_BOT, 0.95)):
    plan[(GX >= r[0]) & (GX <= r[2]) & (GY >= r[1]) & (GY <= r[3])] = h
porch = json.load(open('design/porch.json'))
for poly in porch['polys']:
    pm = contains_xy(Polygon(poly), GX, GY) & ~contains_xy(PL.OUTER.union(PL.LOUNGE_OUT), GX, GY)
    today[pm] = porch['deck']; plan[pm] = porch['deck']
# blocked cells (fences, house) for walking
block = np.zeros_like(today, np.uint8)
def block_line(pts, rad=0.22):
    dd = X.dist_to_polyline(GX.ravel(), GY.ravel(), pts).reshape(GX.shape)
    block[dd < rad] = 1
EAST = [(11.57, 14.62), (11.57, -19.75)]
block_line(EAST)
block_line(FENCE_LINE)
HOUSE = box(-21.6, -8.2, -10.35, 4.0)
block[contains_xy(HOUSE, GX, GY)] = 1
hb = lambda a: base64.b64encode(np.ascontiguousarray(a).tobytes()).decode('ascii')
heights = dict(x0=info['x0'], y0=info['y0'], cell=cell, nx=nx, ny=ny, today=hb(today.astype(np.float32)), plan=hb(plan.astype(np.float32)), block=hb(block))

# ------------------------------------------------------------------ minimap: top-down render of today's yard (tall things cut away), and the same with the plan drawn in
from PIL import Image, ImageDraw, ImageEnhance
import render_top as RT
TOP = (-35.0, -24.0, 15.0, 26.0)
keep_top = (hag < 2.4) & (np.hypot(x + 8, y) < 70) & ~junk & (P['opac'].numpy() > 0.05)
kt = torch.from_numpy(keep_top)
S_top = dict(means=torch.tensor(Pp, dtype=torch.float32)[kt].contiguous(), quats=quats[kt].contiguous(),
             scales=(st['scales'].float() + math.log(F.K))[kt].contiguous(), opac=st['opac'].float()[kt].contiguous(), sh=st['sh'].float()[kt].contiguous())
img = RT.render_top(S_top, TOP, px=1000, height=400.0, bg=(0.82, 0.78, 0.72))
base = ImageEnhance.Contrast(Image.fromarray(img)).enhance(1.06)
base.save(os.path.join(OUT, 'top_today.jpg'), quality=82, optimize=True)
ppm = 1000 / (TOP[2] - TOP[0])
def px(pts): return [((a - TOP[0]) * ppm, (TOP[3] - b) * ppm) for a, b in pts]
lay = base.convert('RGBA'); ov = Image.new('RGBA', lay.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
def fill(geom, col):
    for g in ([geom] if geom.geom_type == 'Polygon' else list(geom.geoms)):
        d.polygon(px(list(g.exterior.coords)), fill=col)
        for h in g.interiors: d.polygon(px(list(h.coords)), fill=(0, 0, 0, 0))
fill(PL.OUTER, (196, 192, 184, 255))
fill(PL.LAWN, (92, 138, 64, 255))
fill(PL.NOOK, (150, 140, 128, 255))
fill(PL.LOUNGE_OUT, (206, 138, 106, 255)); fill(PL.LOUNGE_IN, (104, 102, 99, 255))
fill(box(*PL.HOT_TUB), (228, 230, 232, 255))
fill(box(*PL.PAVILION).buffer(0.35, join_style=2), (52, 54, 56, 255))
fill(TURF, (84, 136, 58, 255)); fill(Point(-14.8, 11.2).buffer(1.55), (170, 100, 72, 255))
fill(LineString(OFFICE_PATH).buffer(0.61, cap_style=2), (110, 108, 104, 255))
for cx_, cy_ in ((9.05, -16.85), (8.75, 14.78)): fill(Point(cx_, cy_).buffer(0.55), (104, 170, 196, 255))
d.line(px(FENCE_LINE), fill=(190, 189, 184, 255), width=5)
d.line(px(EAST), fill=(190, 189, 184, 255), width=5)
lay = Image.alpha_composite(lay, ov).convert('RGB')
lay.save(os.path.join(OUT, 'top.jpg'), quality=82, optimize=True)

# ------------------------------------------------------------------ design + meta
shutil.copy('design/design.json', os.path.join(OUT, 'design.json'))
if os.path.exists('irr/irrigation.json'): shutil.copy('irr/irrigation.json', os.path.join(OUT, 'irrigation.json'))
az, el = math.radians(122.0), math.radians(40.0)
sun = [math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)]
places = [
    dict(name='Back porch', mode='walk', pos=[-9.1, -1.2], look=[6.0, 6.0, 0.8]),
    dict(name='Porch steps', mode='walk', pos=[-6.9, -8.9], look=[3.0, 8.0, 1.0]),
    dict(name='Under the pavilion', mode='walk', pos=[2.2, 10.2], look=[5.0, -8.0, 1.2]),
    dict(name='Hot tub lounge', mode='walk', pos=[-4.4, 9.3], look=[-9.6, 12.4, -0.2]),
    dict(name='Lawn, looking north', mode='walk', pos=[6.4, -8.6], look=[3.5, 10.0, 1.8]),
    dict(name='South fountain', mode='walk', pos=[6.9, -13.3], look=[9.3, -18.2, 1.0]),
    dict(name='North fountain', mode='walk', pos=[3.6, 13.55], look=[9.6, 14.6, 0.8]),
    dict(name='Garden turf', mode='walk', pos=[-11.6, 7.0], look=[-20.0, 11.2, 0.3]),
    dict(name='Office path', mode='walk', pos=[-27.4, 8.3], look=[-18.0, 5.2, 1.2]),
    dict(name='Whole yard from above', mode='orbit', pos=[-24.0, -34.0, 34.0], look=[-6.0, 1.0, 0.0]),
    dict(name='Sprinkler plan', mode='top', pos=[3.2, 0.25, 38.0], look=[3.2, 0.3, 0.0], irr='plan'),
    dict(name='Sprinklers running', mode='walk', pos=[3.0, 7.95], look=[3.0, -6.0, 0.2], irr='run2'),
]
about = ('Built from your walk-around video, with the 9.25.26 plan placed at true size. It is lined up on the vinyl fence, '
         'the back fence and the porch; sizes come from the fence height and the office doors, good to about half a metre. '
         'Two things to check: the plan\u2019s south-west walk corner runs about 2 m past the diagonal fence by the gates, and '
         'its north-east walk corner clips the big rock by the power pole.')
meta = dict(
    version=2, frame='plan metres: x east, y north, z up (lawn grade 0)',
    center=[-6.0, 0.0], topHeight=70,
    splat=dict(header, files=files), design='data/design.json',
    heights=heights, flags=dict(plan=FL_PLAN, garden=FL_GARDEN, fence=FL_FENCE, paths=FL_PATHS, air=FL_AIR, haze=FL_HAZE, fountain=FL_FOUNT),
    turf=dict(box=[-24.5, 7.4, -12.4, 14.8], z=0.06, pool=[-18.6 - 3.66, 11.1 - 1.83, -18.6 + 3.66, 11.1 + 1.83]),
    places=places, start=dict(pos=[-6.9, -8.9], look=[3.0, 8.0, 1.0]),
    walkBounds=[-37.5, -23.5, 15.5, 21.5], sun=sun,
    top=dict(image='data/top.jpg', today='data/top_today.jpg', x0=TOP[0], y0=TOP[1], x1=TOP[2], y1=TOP[3]), about=about,
)
for i, f in enumerate(meta['splat']['files']):
    meta['splat']['files'][i] = 'data/' + f
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), separators=(',', ':'))
tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print('wrote', OUT, sorted(os.listdir(OUT)), 'total %.1f MB' % (tot / 1e6))
