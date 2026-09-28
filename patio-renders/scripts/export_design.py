"""Design model for the yard-walk viewer: the plan (no placeholder house/fence/ground) plus the Sept 28 additions,
in plan metres (x east, y north, z up; lawn grade z = 0). Every object name starts with the layer prefix the viewer
toggles: plan_, roof_, fence_, screen24_, screen30_, turf_, pool_, fountain_, path_.
python3.11 export_design.py OUT.glb GROUND.npz"""
import sys, os, math, random, re, json, struct, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from mathutils import Vector
from shapely.geometry import box as sbox, Polygon, LineString, Point
import main, mats, bl, additions as A, sunken, plan as P
import export_gltf as EG          # reuses its material tables (module runs nothing on import besides defs? see guard)

OUT = sys.argv[1]
GROUND = sys.argv[2]

# ------------------------------------------------------------------ real ground (plan metres) for the additions
g = np.load(GROUND)
GH, GX0, GY0, GC = g['H'], float(g['x0']), float(g['y0']), float(g['cell'])
def ground(x, y):
    fx = (x - GX0) / GC; fy = (y - GY0) / GC
    i = min(max(int(math.floor(fx)), 0), GH.shape[1] - 2); j = min(max(int(math.floor(fy)), 0), GH.shape[0] - 2)
    ax = min(max(fx - i, 0.0), 1.0); ay = min(max(fy - j, 0.0), 1.0)
    return float(GH[j, i] * (1 - ax) * (1 - ay) + GH[j, i + 1] * ax * (1 - ay) + GH[j + 1, i] * (1 - ax) * ay + GH[j + 1, i + 1] * ax * ay)

# ------------------------------------------------------------------ the plan
main.build(grass_on=False, trees_on=False)
DROP = ('Existing_Patio', 'Ground_Far', 'Yard_Sand', 'Fence', 'RedCliffs')
for o in list(bpy.data.objects):
    n = o.name
    coll = o.users_collection[0].name if o.users_collection else ''
    if o.type in ('LIGHT', 'CAMERA') or n.startswith(DROP) or coll == 'Context' or n.startswith(('Tree', 'FarTree', 'Flames', 'FireGlow')):
        bpy.data.objects.remove(o, do_unlink=True)
ROOF = ('Deck', 'Roof', 'Ridge', 'Fascia', 'Barge', 'Rafter', 'Purlin', 'Gutter', 'Drip', 'Soffit', 'Principal', 'KingPost', 'Brace')
for o in list(bpy.data.objects):
    coll = o.users_collection[0].name if o.users_collection else ''
    if coll == 'Pavilion' and o.name.startswith(ROOF):
        o.name = 'roof_' + o.name
    else:
        o.name = 'plan_' + o.name

# ------------------------------------------------------------------ additions
c = bl.coll('Additions')
# 1. gray vinyl privacy fence: the whole north line (replaces the wire, trellis and wood-plank runs) and a return past the office
NE_POST = (11.57, 14.62)
A.vinyl_fence(c, [NE_POST, (11.57, 15.45), (-34.0, 15.25), (-34.0, 3.0)], name='fence_north', z_at=ground)
# 2. black privacy screen on the sunken lounge's brick wall (24" and 30" variants)
A.lounge_screen(c, 24, name='screen24_lounge')
A.lounge_screen(c, 30, name='screen30_lounge')
# 3. garden cleared for turf: putting green + fire pit (hidden in summer), or a 24' x 12' pool (summer)
TURF = sbox(-24.5, 7.4, -12.4, 14.8)
ZT = 0.06
flat = lambda x, y: ZT
green = A._blob((-20.2, 11.3), 3.3, 1.9, 0.12, 4)
A.turf_area(c, TURF, z_at=flat, green=green, cups=[(-22.0, 11.9, 'red'), (-18.3, 10.6, 'yellow')],
            firepit=(-14.8, 11.2), tees=[(-23.6, 8.6, 0.5), (-16.9, 13.6, -2.6)])
for o in list(c.objects):
    if o.name.startswith(('FirePit', 'Adiron', 'firepit', 'turf_fire', 'chair')) and not o.name.startswith('turf_'):
        o.name = 'turf_' + o.name
# everything of the fire-pit set is hidden in pool mode
for o in list(c.objects):
    if o.name.startswith('turf_') and ('fire' in o.name.lower() or 'adiron' in o.name.lower() or 'chair' in o.name.lower() or 'green' in o.name.lower()) \
            and not o.name.endswith('_summerhide'):
        o.name = o.name + '_summerhide'
A.above_ground_pool(c, (-18.6, 11.1), yaw=0.0, z_at=flat, name='pool_frame')

# 4. bubbling fountains in the two big red boulders, with a cascade into a pebble basin on the lawn side
def cascade(idx, crown, basin, basin_r, zb):
    mm = A.M()
    rng = random.Random(40 + idx)
    cx, cy, cz = crown; bx, by = basin
    # ribbon of water from the crown, bulging out over the rock face, into the basin
    d = Vector((bx - cx, by - cy, 0.0)); L = d.length; d.normalize(); side = Vector((-d.y, d.x, 0))
    mb = bl.MeshBuilder()
    n = 16; w0, w1 = 0.10, 0.34
    rows = []
    for i in range(n + 1):
        t = i / n
        # profile: leaves the crown, hugs the face (bulge), drops into the basin
        r = 0.08 + (L - 0.15) * (t ** 1.3)
        z = cz + 0.02 - (cz - zb - 0.04) * (t ** 1.7)
        bul = 0.10 * math.sin(math.pi * t)
        p = Vector((cx, cy, 0)) + d * (r + bul)
        w = w0 + (w1 - w0) * t
        rows.append([mb.vert((p.x - side.x * w / 2, p.y - side.y * w / 2, z)), mb.vert((p.x + side.x * w / 2, p.y + side.y * w / 2, z))])
    for i in range(n):
        a, b = rows[i], rows[i + 1]
        mb.add_face([a[0], b[0], b[1], a[1]], 0)
    bl.obj('fountain_cascade%d' % idx, mb.build('cascade%d' % idx), c, mm['water'])
    # basin: water disc, pebble rim, a few flat stones
    mb = bl.MeshBuilder(); A._disc(mb, bx, by, zb + 0.05, basin_r, 40, 0)
    bl.obj('fountain_pool%d' % idx, mb.build('fpool%d' % idx), c, mm['water'])
    mb = bl.MeshBuilder()
    for k in range(int(180 * basin_r)):
        a = rng.uniform(0, 6.283); r = basin_r + rng.uniform(-0.04, 0.32)
        px, py = bx + r * math.cos(a), by + r * math.sin(a)
        s = rng.uniform(0.04, 0.09)
        bl.obox(mb, Vector((px, py, zb + s * 0.35)), Vector((math.cos(a * 3), math.sin(a * 3), 0)), Vector((-math.sin(a * 3), math.cos(a * 3), 0)), Vector((0, 0, 1)),
                s * 1.5, s, s * 0.75, prand=rng.random())
    bl.obj('fountain_rim%d' % idx, mb.build('frim%d' % idx), c, mm['pebble'])

def boulder(idx, center, rx, ry, h, zb, yaw=0.0, seed=1):
    """Red sandstone boulder (noise-displaced ellipsoid) standing in for the real rock the fountain is drilled into."""
    import bmesh
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    ph = [(rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28)) for _ in range(4)]
    fr = [1.7, 3.1, 5.9, 11.3]; amp = [0.16, 0.10, 0.05, 0.03]
    ca, sa = math.cos(yaw), math.sin(yaw)
    for v in bm.verts:
        x, y, z = v.co
        n = sum(a * math.sin(f * x + p[0]) * math.sin(f * y + p[1]) * math.sin(f * z + p[2]) for f, a, p in zip(fr, amp, ph))
        r = 1.0 + n
        x, y, z = x * r, y * r, z * r
        z = max(z, -0.15) + 0.15                        # flat, slightly buried base
        u, w = x * rx, y * ry
        v.co = (center[0] + ca * u - sa * w, center[1] + sa * u + ca * w, zb - 0.05 + z * h / 1.15)
    me = bpy.data.meshes.new('boulder%d' % idx)
    bm.to_mesh(me); bm.free()
    m = mats._get('sandstone_boulder', mats.simple, mats.lin((170, 92, 60)), rough=0.85)
    return bl.obj('fountain_boulder%d' % idx, me, c, m)

SOUTH_BED = sbox(4.6, -19.55, 11.3, -14.40).buffer(-0.35, join_style=1).buffer(0.35, join_style=1)
NORTH_BED = sbox(6.4, 14.30, 11.3, 15.15)
def fountain_bed(idx, region, core, zb):
    """River-rock bed replacing the weeds round the boulder, draped on today's ground but never above the rock's base."""
    mm = A.M()
    bed = region
    mb = bl.MeshBuilder()
    A._draped(mb, bed, lambda x, y: min(ground(x, y), zb) + 0.02, 0, step=0.25)
    bl.obj('fountain_bed%d_ground' % idx, mb.build('fbed%d' % idx), c, mm['pebble'])

# south boulder (corner bed at the south end of the lawn): ~1.4 x 1.3 m, crown ~1.15 m above its bed
fountain_bed(0, SOUTH_BED, (9.17, -18.40), 0.47)
boulder(0, (9.17, -18.40), 0.72, 0.66, 1.15, 0.47, yaw=0.4, seed=3)
A.boulder_fountain(c, 0, (9.17, -18.40, 1.66), (9.17, -18.40, 0.47), 0.82, spill=0.2)
cascade(0, (9.10, -18.25, 1.64), (8.95, -16.80), 0.62, 0.45)
# north boulder (north-east corner by the power pole) overlaps the plan's walk corner; basin goes west of it by the fence
fountain_bed(1, NORTH_BED, (9.83, 14.34), 0.17)
boulder(1, (9.83, 14.34), 0.67, 0.72, 1.12, 0.17, yaw=-0.3, seed=8)
A.boulder_fountain(c, 1, (9.83, 14.34, 1.33), (9.83, 14.34, 0.17), 0.78, spill=0.2)
cascade(1, (9.62, 14.45, 1.30), (8.60, 14.78), 0.40, 0.15)
for o in list(c.objects):
    if o.name.startswith('fountain_wet'):
        bpy.data.objects.remove(o, do_unlink=True)

# 5. suggested office path: herringbone pavers from the porch's north stair to the office doors
OFFICE_PATH = [(-20.1, 4.75), (-22.6, 5.05), (-25.0, 5.85), (-26.9, 7.2), (-28.15, 8.75), (-28.55, 9.6)]
A.paver_path(c, OFFICE_PATH, width=4 * A.FT, z_at=lambda x, y: min(ground(x, y), 0.25), name='path_office')

# ------------------------------------------------------------------ simple web materials (vertex-coloured pavers/brick)
EXTRA = {
    'vinyl_gray': ((192, 191, 186), 0.45, 0.0), 'vinyl_groove': ((150, 149, 145), 0.5, 0.0),
    'black_metal': ((26, 26, 27), 0.45, 0.4), 'slat_black': ((32, 32, 33), 0.55, 0.1),
    'turf': ((78, 124, 50), 0.95, 0.0), 'putting_green': ((70, 138, 58), 0.9, 0.0),
    'cup_white': ((236, 236, 232), 0.4, 0.0), 'hole_black': ((10, 10, 10), 0.9, 0.0),
    'flag_red': ((196, 36, 30), 0.7, 0.0), 'flag_yellow': ((230, 186, 30), 0.7, 0.0),
    'corten': ((110, 60, 34), 0.8, 0.2), 'flagstone_red': ((168, 96, 70), 0.9, 0.0), 'gravel_tan': ((186, 162, 128), 0.95, 0.0),
    'wet_rock': ((80, 40, 26), 0.1, 0.0), 'pool_frame': ((96, 108, 116), 0.4, 0.3), 'pool_liner': ((70, 120, 150), 0.35, 0.0),
    'chair_teak': ((150, 112, 76), 0.6, 0.0), 'river_rock': ((150, 142, 132), 0.8, 0.0), 'sandstone_boulder': ((170, 92, 60), 0.85, 0.0),
}
EG.SIMPLE.update(EXTRA)
cache = {}
for o in list(bpy.data.objects):
    if o.type not in ('MESH', 'CURVE'):
        continue
    mats_ = [s.material for s in o.material_slots]
    if not mats_:
        continue
    for si, mt in enumerate(mats_):
        src = mt.name if mt else ''
        base = src.split('.')[0]
        if base in ('pavers', 'stone_veneer', 'brick_sandy_red') and si == 0:
            tones = EG.PAVER_TONES if base == 'pavers' else (EG.STONE_TONES if base == 'stone_veneer' else EG.BRICK_TONES)
            def fn(v, tones=tones, base=base):
                col = EG.ramp_const(tones, v) if base == 'pavers' else EG.ramp_lin(tones, v)
                f = 1.0 + 0.10 * (((v * 17.137) % 1.0) - 0.5)
                return tuple(min(255, cc * f) for cc in col)
            if o.type == 'MESH' and 'Col' not in o.data.color_attributes:
                EG.face_colors_to_corner(o.data, fn)
            m = cache.setdefault(base + '_vc', EG.simple_mat(base, (255, 255, 255), 0.85, 0.0, vcol=True))
        elif base in ('water', 'pool_water'):
            m = cache.setdefault('water', EG.simple_mat('water', (104, 170, 186), 0.05, 0.0, alpha=0.62))
        else:
            spec = EG.SIMPLE.get(base, ((160, 160, 160), 0.7, 0.0))
            m = cache.setdefault(base, EG.simple_mat(base, *spec))
        o.material_slots[si].material = m

names = sorted(o.name for o in bpy.data.objects)
pref = {}
for n in names:
    k = n.split('_')[0]
    pref[k] = pref.get(k, 0) + 1
print('objects by prefix', pref)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_apply=True, export_normals=False, export_texcoords=False,
                          export_vertex_color='MATERIAL', export_cameras=False, export_lights=False, export_materials='EXPORT')
with open(OUT, 'rb') as f:
    data = f.read()
magic, ver, length = struct.unpack_from('<4sII', data, 0)
off = 12; js = None; binchunk = b''
while off < length:
    clen, ctype = struct.unpack_from('<I4s', data, off); off += 8
    chunk = data[off:off + clen]; off += clen
    if ctype == b'JSON': js = json.loads(chunk.decode('utf-8'))
    elif ctype == b'BIN\x00': binchunk = chunk
js['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binchunk).decode('ascii')
jpath = os.path.splitext(OUT)[0] + '.json'
with open(jpath, 'w') as f:
    json.dump(js, f, separators=(',', ':'))
print('exported', OUT, os.path.getsize(OUT) // 1024, 'KB; json', os.path.getsize(jpath) // 1024, 'KB')
