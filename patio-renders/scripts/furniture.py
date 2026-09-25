"""Outdoor furniture per the plan: 2 sofas + rectangular fire table (lounge), 4 club chairs + round fire table
(pavilion), round dining table + 4 dining chairs (nook)."""
import math, random
import bpy
from mathutils import Vector, Matrix, Euler
import plan as P
from bl import obj, bevel_box_mesh, cylinder_mesh, MeshBuilder, rrect, prism_holes, obox
import mats
from hardscape import Z_TOP

def M_place(x, y, rotz, z=Z_TOP):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rotz, 4, 'Z')

def part(c, name, me, mat, M, local=(0, 0, 0), rot=(0, 0, 0)):
    o = obj(name, me, c, mat)
    o.matrix_world = M @ Matrix.Translation(local) @ Euler(rot).to_matrix().to_4x4()
    return o

def facing(cx, cy, tx, ty):
    """rotation so local -Y (front) points from (cx,cy) toward (tx,ty)"""
    return math.atan2(tx - cx, -(ty - cy))

def _mats():
    return dict(
        frame=mats._get('alu_charcoal', mats.simple, mats.lin((62, 62, 64)), 0.48, 0.4, 0.5),
        cush=mats._get('cushion', mats.fabric, mats.lin((200, 194, 182))),
        navy=mats._get('pillow_navy', mats.fabric, mats.lin((48, 64, 86))),
        rust=mats._get('pillow_rust', mats.fabric, mats.lin((170, 104, 66))),
        teak=mats._get('teak', mats.wood, base=mats.lin((146, 112, 82)), dark=mats.lin((108, 80, 56)), rough=0.55, grain_scale=2.0, rough_sawn=False),
        gfrc=mats._get('gfrc', mats.concrete, base=mats.lin((150, 148, 144)), rough=0.7, broom=0.0, mott=0.08, charcoal=True),
        glass=mats._get('fire_glass', mats.fire_glass),
        rope=mats._get('rope', mats.fabric, mats.lin((74, 72, 70))),
    )

def sofa(c, name, cx, cy, rotz, W=2.16, D=0.914, seats=3, pillows=('navy', 'rust')):
    m = _mats(); M = M_place(cx, cy, rotz)
    arm = 0.13
    # arms + back frame
    part(c, name + '_armL', bevel_box_mesh('a', arm, D, 0.62, 0.015, 2), m['frame'], M, (-W / 2 + arm / 2, 0, 0))
    part(c, name + '_armR', bevel_box_mesh('a', arm, D, 0.62, 0.015, 2), m['frame'], M, (W / 2 - arm / 2, 0, 0))
    part(c, name + '_back', bevel_box_mesh('b', W - 2 * arm + 0.01, 0.10, 0.68, 0.015, 2), m['frame'], M, (0, D / 2 - 0.05, 0))
    part(c, name + '_deck', bevel_box_mesh('d', W - 2 * arm, D - 0.10, 0.12, 0.01, 1), m['frame'], M, (0, -0.05, 0.20))
    iw = (W - 2 * arm) / seats
    for i in range(seats):
        x = -W / 2 + arm + iw * (i + 0.5)
        part(c, name + '_seat%d' % i, bevel_box_mesh('s', iw - 0.012, D - 0.12, 0.17, 0.05, 4), m['cush'], M, (x, -0.06, 0.32))
        part(c, name + '_bk%d' % i, bevel_box_mesh('k', iw - 0.012, 0.19, 0.44, 0.06, 4), m['cush'], M, (x, D / 2 - 0.20, 0.47), (math.radians(-9), 0, 0))
    for k, pc in enumerate(pillows):
        x = (-W / 2 + arm + 0.30) if k == 0 else (W / 2 - arm - 0.30)
        part(c, name + '_pil%d' % k, bevel_box_mesh('p', 0.46, 0.13, 0.44, 0.06, 4), m[pc], M, (x, D / 2 - 0.36, 0.51), (math.radians(-14), 0, math.radians(8 if k else -8)))

def club_chair(c, name, cx, cy, rotz, W=0.89, D=0.89, pillow=None):
    m = _mats(); M = M_place(cx, cy, rotz)
    arm = 0.12
    part(c, name + '_armL', bevel_box_mesh('a', arm, D, 0.60, 0.015, 2), m['frame'], M, (-W / 2 + arm / 2, 0, 0))
    part(c, name + '_armR', bevel_box_mesh('a', arm, D, 0.60, 0.015, 2), m['frame'], M, (W / 2 - arm / 2, 0, 0))
    part(c, name + '_back', bevel_box_mesh('b', W - 2 * arm + 0.01, 0.10, 0.66, 0.015, 2), m['frame'], M, (0, D / 2 - 0.05, 0))
    part(c, name + '_deck', bevel_box_mesh('d', W - 2 * arm, D - 0.10, 0.12, 0.01, 1), m['frame'], M, (0, -0.05, 0.20))
    part(c, name + '_seat', bevel_box_mesh('s', W - 2 * arm - 0.01, D - 0.12, 0.17, 0.05, 4), m['cush'], M, (0, -0.06, 0.32))
    part(c, name + '_bk', bevel_box_mesh('k', W - 2 * arm - 0.01, 0.19, 0.42, 0.06, 4), m['cush'], M, (0, D / 2 - 0.20, 0.47), (math.radians(-9), 0, 0))
    if pillow:
        part(c, name + '_pil', bevel_box_mesh('p', 0.42, 0.12, 0.40, 0.06, 4), m[pillow], M, (0.02, D / 2 - 0.34, 0.50), (math.radians(-14), 0, math.radians(6)))

def fire_glass_bed(mb, poly, z, rng, count):
    minx, miny, maxx, maxy = poly.bounds
    k = 0; tries = 0
    from shapely.geometry import Point
    while k < count and tries < count * 20:
        tries += 1
        x = rng.uniform(minx, maxx); y = rng.uniform(miny, maxy)
        if not poly.contains(Point(x, y)): continue
        s = rng.uniform(0.012, 0.024)
        ax = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 0.3))).normalized()
        az = Vector((0, 0, 1)); ay = az.cross(ax).normalized(); az = ax.cross(ay)
        obox(mb, (x, y, z + rng.uniform(0, 0.012)), ax, ay, az, s, s * rng.uniform(0.6, 1.0), s * rng.uniform(0.4, 0.8), prand=rng.random())
        k += 1

def round_fire_table(c, name, cx, cy, d=P.ROUND_D, h=0.56, burner_d=0.34):
    m = _mats(); rng = random.Random(3)
    r = d / 2
    body = MeshBuilder()
    outer = rrect(cx, cy, d, d, r - 0.001, seg=16)
    from shapely.geometry import Point
    ring = Point(cx, cy).buffer(r, quad_segs=24)
    hole = Point(cx, cy).buffer(burner_d / 2 + 0.03, quad_segs=16)
    prism_holes(body, ring.difference(hole), Z_TOP + h - 0.06, Z_TOP + h)
    prism_holes(body, Point(cx, cy).buffer(r - 0.04, quad_segs=24), Z_TOP, Z_TOP + h - 0.06)
    obj(name + '_body', body.build(name + 'b'), c, m['gfrc'])
    pan = MeshBuilder()
    pan.flat_poly(hole, Z_TOP + h - 0.035)
    fire_glass_bed(pan, Point(cx, cy).buffer(burner_d / 2 + 0.02), Z_TOP + h - 0.035, rng, 420)
    obj(name + '_glass', pan.build(name + 'g'), c, m['glass'])
    return (cx, cy, Z_TOP + h - 0.03, ('round', burner_d / 2 - 0.01))

def rect_fire_table(c, name, rect, h=0.56):
    m = _mats(); rng = random.Random(4)
    from shapely.geometry import box
    x0, y0, x1, y1 = rect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    outer = box(x0, y0, x1, y1)
    burner = box(cx - 0.45, cy - 0.12, cx + 0.45, cy + 0.12)
    mb = MeshBuilder()
    prism_holes(mb, outer.difference(burner.buffer(0.02, join_style=2)), Z_TOP + h - 0.06, Z_TOP + h)
    prism_holes(mb, outer.buffer(-0.035, join_style=2), Z_TOP, Z_TOP + h - 0.06)
    obj(name + '_body', mb.build(name + 'b'), c, m['gfrc'])
    pan = MeshBuilder()
    pan.flat_poly(burner.buffer(0.02, join_style=2), Z_TOP + h - 0.035)
    fire_glass_bed(pan, burner.buffer(0.015, join_style=2), Z_TOP + h - 0.035, rng, 700)
    obj(name + '_glass', pan.build(name + 'g'), c, m['glass'])
    return (cx, cy, Z_TOP + h - 0.03, ('rect', 0.42, 0.10))

def dining_table(c, name, cx, cy, d=P.ROUND_D, h=0.75):
    m = _mats()
    top = obj(name + '_top', cylinder_mesh('tt', d / 2, 0.035, seg=64), c, m['teak']); top.location = (cx, cy, Z_TOP + h - 0.035)
    inl = obj(name + '_inlay', cylinder_mesh('ti', 0.17, 0.002, seg=48), c, mats._get('alu_charcoal', mats.simple, mats.lin((46, 47, 49)), 0.42, 0.5, 0.5))
    inl.location = (cx, cy, Z_TOP + h)
    col = obj(name + '_col', cylinder_mesh('tc', 0.055, h - 0.05, seg=24), c, m['frame']); col.location = (cx, cy, Z_TOP + 0.02)
    base = obj(name + '_base', cylinder_mesh('tb', 0.30, 0.025, seg=48, r_top=0.26), c, m['frame']); base.location = (cx, cy, Z_TOP)
    apron = obj(name + '_ap', cylinder_mesh('ta', 0.28, 0.05, seg=48), c, m['frame']); apron.location = (cx, cy, Z_TOP + h - 0.085)

def dining_chair(c, name, cx, cy, rotz):
    """Armless dining chair: charcoal aluminium frame, natural rope back, seat cushion."""
    m = _mats(); M = M_place(cx, cy, rotz)
    rope = mats._get('rope_natural', mats.fabric, mats.lin((164, 152, 134)))
    from bl import curve_tube
    seat_z = 0.44
    # legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = cylinder_mesh('leg', 0.014, seat_z - 0.02, seg=12)
            part(c, name + '_leg', leg, m['frame'], M, (sx * 0.205, sy * 0.19, 0))
    # seat frame (rounded square) + cushion
    part(c, name + '_seatframe', bevel_box_mesh('sf', 0.47, 0.45, 0.035, 0.012, 2), m['frame'], M, (0, 0, seat_z - 0.035))
    part(c, name + '_cush', bevel_box_mesh('sc', 0.45, 0.42, 0.055, 0.025, 3), m['cush'], M, (0, -0.01, seat_z))
    # curved back: two posts + top rail + vertical ropes
    R = 0.25
    a0, a1 = math.radians(25), math.radians(155)
    def arc_pt(t, z):
        ang = a0 + (a1 - a0) * t
        v = M @ Vector((R * math.cos(ang), R * math.sin(ang) - 0.03, z, 1.0)) if False else None
        p = Vector((R * math.cos(ang), R * math.sin(ang) - 0.03, z))
        return tuple(M @ p)
    top_z = seat_z + 0.40
    rail = [arc_pt(t / 10, top_z) for t in range(11)]
    curve_tube(name + '_rail', rail, 0.016, m['frame'], c)
    for t in (0.0, 1.0):
        curve_tube(name + '_post%d' % int(t), [arc_pt(t, seat_z - 0.03), arc_pt(t, top_z)], 0.013, m['frame'], c)
    n = 15
    for k in range(1, n):
        t = k / n
        curve_tube(name + '_rope%d' % k, [arc_pt(t, seat_z + 0.02), arc_pt(t, top_z - 0.01)], 0.0065, rope, c)
    # lower rope band
    band = [arc_pt(t / 10, seat_z + 0.06) for t in range(11)]
    curve_tube(name + '_band', band, 0.009, rope, c)

def build_furniture(c):
    # --- lounge: 2 sofas + rectangular fire table
    x0, y0, x1, y1 = P.SOFA_N
    sofa(c, 'SofaN', (x0 + x1) / 2, (y0 + y1) / 2, 0.0, W=x1 - x0, D=y1 - y0)
    x0, y0, x1, y1 = P.SOFA_E
    sofa(c, 'SofaE', (x0 + x1) / 2, (y0 + y1) / 2, -math.pi / 2, W=y1 - y0, D=x1 - x0, pillows=('rust', 'navy'))
    fires = [rect_fire_table(c, 'FireTableRect', P.FIRE_RECT)]
    # --- pavilion: round fire table + 4 club chairs (plan positions)
    tx, ty = P.FIRE_ROUND_C
    fires.append(round_fire_table(c, 'FireTableRound', tx, ty))
    big = [ch for ch in P.LOUNGE_CHAIRS if ch[1][0] > 3.0]
    for i, ((cx, cy), _) in enumerate(big):
        club_chair(c, 'ClubChair%d' % i, cx, cy, facing(cx, cy, tx, ty), pillow=('navy' if i % 2 else 'rust'))
    # --- nook: dining table + 4 chairs
    dx, dy = P.DINING_C
    dining_table(c, 'DiningTable', dx, dy)
    for i, ((cx, cy), _) in enumerate(P.DINING_CHAIRS):
        dining_chair(c, 'DiningChair%d' % i, cx, cy, facing(cx, cy, dx, dy))
    return fires
