"""7' x 7' hot tub on the herringbone lounge (open, with water)."""
import math, random
import bpy
from mathutils import Vector
from shapely.geometry import box
import plan as P
from bl import MeshBuilder, obj, prism_holes, rrect, obox, cylinder_mesh, bevel_box_mesh
import mats
from hardscape import Z_TOP

def build_hottub(c):
    x0, y0, x1, y1 = P.HOT_TUB
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    S = x1 - x0
    z_skirt = Z_TOP + 0.88
    z_lip = z_skirt + 0.05
    z_floor = Z_TOP + 0.12
    z_bench = Z_TOP + 0.50
    z_water = z_lip - 0.11
    cab = mats._get('spa_cabinet', mats.wood, base=mats.lin((96, 88, 80)), dark=mats.lin((74, 67, 60)), rough=0.55, grain_scale=1.6, rough_sawn=False)
    acrylic = mats._get('acrylic', mats.simple, mats.lin((226, 229, 231)), 0.07, 0.0, 0.5, 0.05, 300.0, 0.4)
    trim = mats._get('spa_trim', mats.simple, mats.lin((50, 48, 46)), 0.5, 0.0, 0.4)
    # ---- cabinet: horizontal composite boards per side + corner posts
    mb = MeshBuilder()
    bh, gap = 0.125, 0.008
    zc = Z_TOP + 0.07
    rows = []
    while zc < z_skirt - 0.02:
        rows.append((zc, min(zc + bh, z_skirt - 0.005))); zc += bh + gap
    inset = 0.02
    for side in range(4):
        for (za, zb) in rows:
            if side == 0:   mb.box(x0 + 0.07, y0, za, x1 - 0.07, y0 + 0.03, zb, prand=0)
            elif side == 1: mb.box(x0 + 0.07, y1 - 0.03, za, x1 - 0.07, y1, zb, prand=0)
            elif side == 2: mb.box(x0, y0 + 0.07, za, x0 + 0.03, y1 - 0.07, zb, prand=0)
            else:           mb.box(x1 - 0.03, y0 + 0.07, za, x1, y1 - 0.07, zb, prand=0)
    me = mb.build('spa_boards')
    o = obj('SpaCabinetBoards', me, c, cab)
    mb = MeshBuilder()
    mb.box(x0 + 0.02, y0 + 0.02, Z_TOP, x1 - 0.02, y1 - 0.02, z_skirt - 0.01)          # inner body (dark)
    for (px, py) in [(x0, y0), (x1 - 0.08, y0), (x0, y1 - 0.08), (x1 - 0.08, y1 - 0.08)]:
        mb.box(px - 0.004, py - 0.004, Z_TOP, px + 0.084, py + 0.084, z_skirt)
    mb.box(x0 - 0.005, y0 - 0.005, Z_TOP, x1 + 0.005, y1 + 0.005, Z_TOP + 0.07)       # base trim
    obj('SpaCabinetTrim', mb.build('spa_trim'), c, trim)
    # ---- acrylic shell: lip slab with cavity hole, inner walls, bench ring, floor
    outer = rrect(cx, cy, S + 0.02, S + 0.02, 0.10)
    cav = rrect(cx, cy, S - 0.26, S - 0.26, 0.30)
    mb = MeshBuilder()
    prism_holes(mb, outer.difference(cav), z_skirt, z_lip)
    # cavity wall (inward normals) from floor to lip
    ring = list(cav.exterior.coords)[:-1]
    from shapely.geometry.polygon import orient
    ring = list(orient(cav, 1.0).exterior.coords)[:-1]
    n = len(ring)
    T = [mb.vert((p[0], p[1], z_lip)) for p in ring]
    B = [mb.vert((p[0], p[1], z_floor)) for p in ring]
    for i in range(n):
        j = (i + 1) % n
        mb.add_face([B[j], B[i], T[i], T[j]])
    # bench ring + inner footwell floor
    well = rrect(cx, cy, S - 1.26, S - 1.26, 0.22)
    prism_holes(mb, cav.buffer(-0.002).difference(well), z_floor, z_bench)
    mb.flat_poly(cav.buffer(-0.001), z_floor)
    obj('SpaShell', mb.build('spa_shell'), c, acrylic)
    # ---- jets (stainless rings visible through the water)
    ss = mats._get('stainless', mats.stainless)
    mbj = MeshBuilder()
    rng = random.Random(5)
    half = (S - 0.26) / 2 - 0.002
    for side in range(4):
        for k in range(5):
            u = -0.55 + k * 0.275
            for zz in (z_bench + 0.12, z_bench + 0.26):
                if side == 0:   cen, ax, nrm = (cx + u, cy - half, zz), (1, 0, 0), (0, 1, 0)
                elif side == 1: cen, ax, nrm = (cx - u, cy + half, zz), (-1, 0, 0), (0, -1, 0)
                elif side == 2: cen, ax, nrm = (cx - half, cy - u, zz), (0, -1, 0), (1, 0, 0)
                else:           cen, ax, nrm = (cx + half, cy + u, zz), (0, 1, 0), (-1, 0, 0)
                obox(mbj, Vector(cen) + Vector(nrm) * 0.004, Vector(ax), Vector(nrm), Vector((0, 0, 1)), 0.05, 0.008, 0.05)
    obj('SpaJets', mbj.build('jets'), c, ss)
    # ---- headrest pillows at the four corners
    pil = mats._get('spa_pillow', mats.simple, mats.lin((58, 60, 63)), 0.45, 0.0, 0.4)
    for k, (sx, sy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        me = bevel_box_mesh('pillow%d' % k, 0.30, 0.10, 0.16, bevel=0.04, segments=3)
        o = obj('SpaPillow%d' % k, me, c, pil)
        d = (S - 0.26) / 2 - 0.12
        o.location = (cx + sx * d, cy + sy * d, z_lip - 0.12)
        o.rotation_euler = (0, 0, math.atan2(sy, sx) + math.pi / 2)
    # ---- water (closed volume)
    wmb = MeshBuilder()
    wpoly = cav.buffer(-0.004)
    prism_holes(wmb, wpoly, z_floor + 0.004, z_water)
    obj('SpaWater', wmb.build('water'), c, mats._get('water', mats.water))
    # ---- control panel on the lip
    cp = obj('SpaControl', bevel_box_mesh('spactl', 0.16, 0.07, 0.012, bevel=0.004, segments=2), c,
             mats._get('black_plastic', mats.simple, mats.lin((20, 20, 20)), 0.35, 0.0, 0.5))
    cp.location = (cx + 0.35, y0 + 0.055, z_lip)
    return dict(center=(cx, cy), z_water=z_water, z_lip=z_lip)

def build_spa_light(c, strength=0.0):
    x0, y0, x1, y1 = P.HOT_TUB
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ld = bpy.data.lights.new('SpaLight', 'POINT'); ld.energy = strength; ld.shadow_soft_size = 0.1
    ld.color = (0.75, 0.92, 1.0)
    lo = bpy.data.objects.new('SpaLight', ld); c.objects.link(lo)
    lo.location = (cx, cy, Z_TOP + 0.35)
    return lo
