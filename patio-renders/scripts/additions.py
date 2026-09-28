"""New ideas on top of the plan (Sept 28 owner notes):
  * gray vinyl privacy fence continued all the way around (replaces the wood plank and wire fences)
  * a black 24" or 30" privacy fence on the sunken lounge's brick wall
  * the garden cleared for artificial turf: putting green + a fire pit, or a big above-ground pool in summer
  * bubbling fountains in the big red boulders
  * paths to the office
Every object's name starts with the layer prefix the web viewer toggles
(fence_, screen24_, screen30_, turf_, pool_, fountain_, path_)."""
import math, random
import bpy
from mathutils import Vector
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from bl import MeshBuilder, obj, obox, cylinder_mesh, coll, ring_ccw
import mats
from mats import lin
import sunken
import plan as P

FT = 0.3048


def _flat(z_at):
    return z_at if z_at is not None else (lambda x, y: 0.0)


# ------------------------------------------------------------------ materials
def M():
    g = mats._get
    return dict(
        vinyl=g('vinyl_gray', mats.simple, lin((192, 191, 186)), rough=0.38, spec=0.45),
        vinyl_groove=g('vinyl_groove', mats.simple, lin((150, 149, 145)), rough=0.5),
        black_metal=g('black_metal', mats.simple, lin((24, 24, 25)), rough=0.42, metal=0.35, spec=0.5),
        slat=g('slat_black', mats.simple, lin((30, 30, 31)), rough=0.55, spec=0.4, bump=0.02, bump_scale=60.0),
        turf=g('turf', turf_material),
        green=g('putting_green', turf_material, fine=True),
        cup=g('cup_white', mats.simple, lin((236, 236, 232)), rough=0.4),
        hole=g('hole_black', mats.simple, lin((10, 10, 10)), rough=0.9),
        flag_red=g('flag_red', mats.simple, lin((196, 36, 30)), rough=0.7, sheen=0.4),
        flag_yel=g('flag_yellow', mats.simple, lin((230, 186, 30)), rough=0.7, sheen=0.4),
        steel=g('corten', mats.simple, lin((104, 58, 34)), rough=0.8, metal=0.2, bump=0.15, bump_scale=40.0),
        flagstone=g('flagstone_red', mats.red_rock),
        gravel=g('gravel_tan', gravel_material),
        water=g('water', mats.water),
        wet=g('wet_rock', mats.simple, lin((70, 34, 22)), rough=0.08, spec=0.6, coat=1.0),
        pool_frame=g('pool_frame', mats.simple, lin((96, 108, 116)), rough=0.4, metal=0.3),
        pool_liner=g('pool_liner', mats.simple, lin((70, 120, 150)), rough=0.35),
        pool_water=g('pool_water', mats.water),
        chair=g('chair_teak', mats.simple, lin((150, 112, 76)), rough=0.6),
        pebble=g('river_rock', pebble_material),
    )


def turf_material(name, fine=False):
    from bl import new_material, principled, finish
    m, nt = new_material(name)
    P_ = nt.n('ShaderNodeNewGeometry').outputs['Position']
    n1 = nt.n('ShaderNodeTexNoise', Vector=P_, Scale=0.6 if not fine else 1.2, Detail=3.0).outputs['Factor']
    n2 = nt.n('ShaderNodeTexNoise', Vector=P_, Scale=260.0, Detail=2.0).outputs['Factor']
    a = lin((64, 104, 38)) if not fine else lin((70, 122, 44))
    b = lin((96, 132, 52)) if not fine else lin((88, 140, 56))
    col = nt.mix(nt.math('MULTIPLY_ADD', n1, 0.7, nt.math('MULTIPLY', n2, 0.3)), a, b)
    bump = nt.n('ShaderNodeBump', Strength=0.35 if not fine else 0.15, Distance=0.003, Height=n2)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.78, Sheen_Weight=0.4, Sheen_Tint=(0.8, 1.0, 0.6), Normal=bump.outputs[0]))
    return m


def gravel_material(name):
    from bl import new_material, principled, finish
    m, nt = new_material(name)
    P_ = nt.n('ShaderNodeNewGeometry').outputs['Position']
    v = nt.n('ShaderNodeTexVoronoi', Vector=P_, Scale=90.0)
    n = nt.n('ShaderNodeTexNoise', Vector=P_, Scale=40.0, Detail=4.0).outputs['Factor']
    col = nt.mix(v.outputs['Color'], lin((176, 138, 106)), lin((210, 176, 140)))
    col = nt.mix(nt.math('MULTIPLY', n, 0.4), col, lin((120, 88, 66)))
    bump = nt.n('ShaderNodeBump', Strength=0.6, Distance=0.004, Height=v.outputs['Distance'])
    finish(nt, principled(nt, Base_Color=col, Roughness=0.92, Normal=bump.outputs[0]))
    return m


def pebble_material(name):
    from bl import new_material, principled, finish
    m, nt = new_material(name)
    a = nt.n('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='prand').outputs['Factor']
    ramp = nt.n('ShaderNodeValToRGB', Fac=a)
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (*lin((62, 58, 54)), 1)
    els[1].position = 1.0; els[1].color = (*lin((150, 118, 96)), 1)
    finish(nt, principled(nt, Base_Color=ramp.outputs['Color'], Roughness=0.25, Coat_Weight=0.6))
    return m


# ------------------------------------------------------------------ gray vinyl privacy fence
def vinyl_fence(c, pts, name='fence_new', h=6 * FT, oc=8 * FT, post=5 * 0.0254, z_at=None, skip=()):
    """6 ft tongue-and-groove vinyl privacy fence along the polyline pts (plan metres).
    skip: list of (i_segment) indexes to leave open (gates, existing fence)."""
    z_at = _flat(z_at)
    mm = M()
    mb = MeshBuilder()
    posts = []
    for si in range(len(pts) - 1):
        a, b = Vector(pts[si]), Vector(pts[si + 1])
        L = (b - a).length
        if L < 0.05:
            continue
        n = max(1, math.ceil(L / oc - 1e-6))
        for k in range(n + 1):
            p = a.lerp(b, k / n)
            if not posts or (posts[-1][0] - p).length > 0.05:
                posts.append((p, si))
        if si in skip:
            continue
        t = (b - a).normalized(); nrm = Vector((-t.y, t.x))
        for k in range(n):
            pa, pb = a.lerp(b, k / n), a.lerp(b, (k + 1) / n)
            za, zb = z_at(pa.x, pa.y), z_at(pb.x, pb.y)
            z0 = min(za, zb) + 0.04
            ua, ub = pa + t * (post / 2), pb - t * (post / 2)
            span = (ub - ua).length
            mid = (ua + ub) / 2
            tv, nv, up = Vector((t.x, t.y, 0)), Vector((nrm.x, nrm.y, 0)), Vector((0, 0, 1))
            # boards (one slab), bottom and top rails
            obox(mb, Vector((mid.x, mid.y, z0 + 0.12 + (h - 0.25) / 2)), tv, nv, up, span, 0.028, h - 0.25, mi=0)
            obox(mb, Vector((mid.x, mid.y, z0 + 0.07)), tv, nv, up, span, 0.05, 0.10, mi=0)
            obox(mb, Vector((mid.x, mid.y, z0 + h - 0.07)), tv, nv, up, span, 0.055, 0.14, mi=0)
            # tongue-and-groove lines, both faces
            nb = max(1, int(span / 0.178))
            for j in range(1, nb):
                q = ua + t * (span * j / nb)
                for s in (1, -1):
                    cen = Vector((q.x, q.y, z0 + 0.12 + (h - 0.25) / 2)) + nv * (s * 0.0146)
                    obox(mb, cen, tv, nv, up, 0.006, 0.0015, h - 0.27, mi=1)
    # posts with pyramid caps
    for p, si in posts:
        z0 = z_at(p.x, p.y) - 0.05
        obox(mb, Vector((p.x, p.y, z0 + (h + 0.13) / 2)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), post, post, h + 0.13, mi=0)
        top = z0 + h + 0.13
        cs = post / 2 + 0.012
        A = [mb.vert((p.x + dx * cs, p.y + dy * cs, top + 0.012)) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        Bv = [mb.vert((p.x + dx * cs, p.y + dy * cs, top)) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        apex = mb.vert((p.x, p.y, top + 0.05))
        for i in range(4):
            j = (i + 1) % 4
            mb.add_face([A[i], A[j], apex], 0)
            mb.add_face([Bv[i], Bv[j], A[j], A[i]], 0)
    o = obj(name, mb.build(name), c, [mm['vinyl'], mm['vinyl_groove']])
    return o


# ------------------------------------------------------------------ black privacy fence on the lounge wall
def lounge_screen(c, height_in=24, name=None, post_oc=1.5):
    """Horizontal black slat screen standing on the brick cap, all round the sunken lounge except the stair."""
    mm = M()
    name = name or 'screen%d_lounge' % height_in
    runs, st = sunken.layout()
    # centreline of the wall ring: LOUNGE_OUT inset by half the wall thickness, minus the stair opening
    ring = P.LOUNGE_OUT.buffer(-sunken.BW / 2, join_style=2)
    ring = orient(ring, 1.0)
    line = LineString(list(ring.exterior.coords))
    gap = box(st['x0'] - 0.02, st['y_top'] - 0.6, st['x1'] + sunken.BW + 0.02, st['y_top'] + 0.6)
    pieces = line.difference(gap)
    geoms = [pieces] if pieces.geom_type == 'LineString' else list(pieces.geoms)
    z0 = sunken.WALL_TOP + 0.002
    H = height_in * 0.0254
    slat_h, gap_h, slat_t = 0.14, 0.014, 0.022
    mb = MeshBuilder()
    for g in geoms:
        pts = [Vector(p) for p in g.coords]
        # post positions: vertices + subdivisions
        for si in range(len(pts) - 1):
            a, b = pts[si], pts[si + 1]
            L = (b - a).length
            if L < 0.03:
                continue
            n = max(1, math.ceil(L / post_oc))
            t = (b - a).normalized(); nrm = Vector((-t.y, t.x))
            tv, nv, up = Vector((t.x, t.y, 0)), Vector((nrm.x, nrm.y, 0)), Vector((0, 0, 1))
            for k in range(n + 1):
                p = a.lerp(b, k / n)
                obox(mb, Vector((p.x, p.y, z0 + (H + 0.02) / 2)), tv, nv, up, 0.05, 0.05, H + 0.02, mi=0)
            # slats span the whole run (posts overlap them)
            z = z0 + 0.03
            mid = (a + b) / 2
            while z + slat_h <= z0 + H + 0.001:
                obox(mb, Vector((mid.x, mid.y, z + slat_h / 2)), tv, nv, up, L, slat_t, slat_h, mi=1)
                z += slat_h + gap_h
            # cap rail
            obox(mb, Vector((mid.x, mid.y, z0 + H + 0.015)), tv, nv, up, L + 0.05, 0.06, 0.02, mi=0)
    return obj(name, mb.build(name), c, [mm['black_metal'], mm['slat']])


# ------------------------------------------------------------------ turf, putting green, fire pit
def _blob(center, rx, ry, rot, seed, n=48, wob=0.12):
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.283) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 6.283185 * i / n
        r = 1 + wob * (0.6 * math.sin(2 * a + ph[0]) + 0.3 * math.sin(3 * a + ph[1]) + 0.2 * math.sin(5 * a + ph[2]))
        x, y = rx * r * math.cos(a), ry * r * math.sin(a)
        pts.append((center[0] + x * math.cos(rot) - y * math.sin(rot), center[1] + x * math.sin(rot) + y * math.cos(rot)))
    return Polygon(pts).buffer(0)


def turf_area(c, poly, z_at=None, green=None, cups=(), firepit=None, tees=()):
    """poly: turf outline (shapely, plan metres). green: shapely polygon of the putting green.
    cups: [(x, y, flag_colour)], firepit: (x, y) centre."""
    z_at = _flat(z_at)
    mm = M()
    zc = lambda x, y: z_at(x, y) + 0.025
    # turf surface (earcut, raised 2.5 cm), minus the green and the fire pit pad
    pad = Point(firepit).buffer(1.55, 48) if firepit else None
    body = poly
    if green is not None:
        body = body.difference(green)
    if pad is not None:
        body = body.difference(pad)
    mb = MeshBuilder()
    _draped(mb, body, zc, 0)
    o = obj('turf_surface_ground', mb.build('turf_surface'), c, mm['turf'])
    if green is not None:
        mb = MeshBuilder(); _draped(mb, green.difference(pad) if pad else green, lambda x, y: zc(x, y) + 0.004, 0)
        obj('turf_green_ground', mb.build('turf_green'), c, mm['green'])
    # steel edging round the turf
    mb = MeshBuilder()
    ring = list(orient(poly, 1.0).exterior.coords)
    for a, b in zip(ring[:-1], ring[1:]):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        if L < 0.02: continue
        t = (b - a).normalized(); nrm = Vector((-t.y, t.x)); mid = (a + b) / 2
        obox(mb, Vector((mid.x, mid.y, z_at(mid.x, mid.y) + 0.03)), Vector((t.x, t.y, 0)), Vector((nrm.x, nrm.y, 0)), Vector((0, 0, 1)), L + 0.01, 0.008, 0.07)
    obj('turf_edging', mb.build('turf_edging'), c, mm['black_metal'])
    # cups and flags (hidden in pool mode)
    for i, (x, y, col) in enumerate(cups):
        z = zc(x, y) + 0.005
        mb = MeshBuilder()
        _disc(mb, x, y, z + 0.001, 0.0635, 24, 1)
        _ring(mb, x, y, z + 0.0012, 0.0635, 0.072, 24, 0)
        obj('turf_cup%d_summerhide' % i, mb.build('cup%d' % i), c, [mm['cup'], mm['hole']])
        mb = MeshBuilder()
        pole_h = 1.2
        obox(mb, Vector((x, y, z + pole_h / 2)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.012, 0.012, pole_h, mi=0)
        obox(mb, Vector((x + 0.15, y, z + pole_h - 0.1)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.28, 0.004, 0.19, mi=1)
        obj('turf_flag%d_summerhide' % i, mb.build('flag%d' % i), c, [mm['cup'], mm['flag_red'] if col == 'red' else mm['flag_yel']])
    for i, (x, y, rot) in enumerate(tees):
        mb = MeshBuilder()
        obox(mb, Vector((x, y, zc(x, y) + 0.006)), Vector((math.cos(rot), math.sin(rot), 0)), Vector((-math.sin(rot), math.cos(rot), 0)), Vector((0, 0, 1)), 0.9, 0.45, 0.012)
        obj('turf_tee%d_summerhide' % i, mb.build('tee%d' % i), c, mm['green'])
    if firepit:
        firepit_set(c, firepit, z_at)
    return o


def firepit_set(c, center, z_at):
    """Round corten fire pit on a red flagstone pad, four Adirondack chairs."""
    mm = M()
    x, y = center
    z = z_at(x, y)
    rng = random.Random(7)
    # flagstone pad: irregular stones inside a 1.55 m circle
    mb = MeshBuilder()
    pad = Point(center).buffer(1.55, 48)
    for poly in _voronoi_stones(pad, 0.33, rng):
        pts = ring_ccw(poly.buffer(-0.018))
        if len(pts) < 3: continue
        mb.prism(pts, z - 0.02, z + 0.035, ch=0.006, bottom=False, prand=rng.random())
    obj('turf_firepad_ground_summerhide', mb.build('firepad'), c, mm['flagstone'])
    mb = MeshBuilder(); _disc(mb, x, y, z + 0.02, 1.55, 48, 0)
    obj('turf_firepad_joint_summerhide', mb.build('firepad_joint'), c, mm['gravel'])
    # corten bowl ring (outer 1.0 m dia, 0.4 m tall) with dark fill
    ring = cylinder_mesh('firepit_ring', 0.5, 0.40, seg=48, smooth=True)
    o = obj('turf_firepit_summerhide', ring, c, mm['steel']); o.location = (x, y, z + 0.03)
    inner = MeshBuilder(); _disc(inner, x, y, z + 0.36, 0.47, 32, 0)
    obj('turf_firepit_coals_summerhide', inner.build('coals'), c, mm['hole'])
    # four chairs facing the pit
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cy = x + 1.75 * math.cos(a), y + 1.75 * math.sin(a)
        adirondack(c, (cx, cy, z_at(cx, cy)), a + math.pi, 'turf_chair%d_summerhide' % k)


def adirondack(c, loc, yaw, name):
    mm = M()
    mb = MeshBuilder()
    fx, fy = math.cos(yaw), math.sin(yaw)       # facing direction
    rx, ry = -fy, fx
    X = lambda u, v, w: Vector((loc[0] + fx * u + rx * v, loc[1] + fy * u + ry * v, loc[2] + w))
    tv, nv, up = Vector((fx, fy, 0)), Vector((rx, ry, 0)), Vector((0, 0, 1))
    # seat slats
    for i in range(6):
        u = 0.25 - i * 0.075
        obox(mb, X(u, 0, 0.36 - i * 0.012), tv, nv, up, 0.065, 0.56, 0.02)
    # back slats, leaning back 25 degrees
    lean = math.radians(25)
    bdir = Vector((-fx * math.sin(lean), -fy * math.sin(lean), math.cos(lean)))
    for j in range(5):
        v = -0.22 + j * 0.11
        base = X(-0.18, v, 0.34)
        obox(mb, base + bdir * 0.42, bdir.cross(nv).normalized(), nv, bdir, 0.02, 0.09, 0.84)
    # arms
    for s in (-1, 1):
        obox(mb, X(0.05, s * 0.34, 0.62), tv, nv, up, 0.62, 0.13, 0.02)
        obox(mb, X(0.28, s * 0.34, 0.31), tv, nv, up, 0.06, 0.04, 0.62)
        obox(mb, X(-0.2, s * 0.30, 0.2), tv, nv, up, 0.05, 0.04, 0.4)
    return obj(name, mb.build(name), c, mm['chair'])


def _voronoi_stones(region, size, rng):
    from shapely.ops import voronoi_diagram
    from shapely.geometry import MultiPoint
    minx, miny, maxx, maxy = region.bounds
    pts = []
    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            pts.append((x + rng.uniform(-0.35, 0.35) * size, y + rng.uniform(-0.35, 0.35) * size))
            x += size
        y += size * 0.9
    vd = voronoi_diagram(MultiPoint(pts), envelope=region.buffer(1))
    out = []
    for cell in vd.geoms:
        g = cell.intersection(region)
        if g.is_empty: continue
        for p in ([g] if g.geom_type == 'Polygon' else [q for q in getattr(g, 'geoms', []) if q.geom_type == 'Polygon']):
            if p.area > 0.004: out.append(p)
    return out


def _draped(mb, poly, zf, mi, step=0.5):
    """Flat-triangulated polygon whose vertices follow zf(x, y); long edges subdivided."""
    polys = [poly] if poly.geom_type == 'Polygon' else [g for g in getattr(poly, 'geoms', []) if g.geom_type == 'Polygon']
    import numpy as np
    import mapbox_earcut as earcut
    for p in polys:
        if p.area < 1e-4: continue
        p = orient(p, 1.0)
        rings = []
        for r in [p.exterior] + list(p.interiors):
            cs = list(r.coords)[:-1]
            dense = []
            for a, b in zip(cs, cs[1:] + cs[:1]):
                L = math.dist(a, b); n = max(1, int(L / step))
                for k in range(n):
                    dense.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
            rings.append(dense)
        flat = np.array([q for r in rings for q in r], dtype=np.float64)
        ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
        tri = earcut.triangulate_float64(flat, ends).reshape(-1, 3)
        base = len(mb.v)
        for q in flat:
            mb.v.append((q[0], q[1], zf(q[0], q[1])))
        for t in tri:
            mb.add_face([base + int(t[0]), base + int(t[1]), base + int(t[2])], mi)


def _disc(mb, x, y, z, r, n, mi):
    c = mb.vert((x, y, z))
    R = [mb.vert((x + r * math.cos(6.283185 * i / n), y + r * math.sin(6.283185 * i / n), z)) for i in range(n)]
    for i in range(n):
        mb.add_face([c, R[i], R[(i + 1) % n]], mi)


def _ring(mb, x, y, z, r0, r1, n, mi):
    A = [mb.vert((x + r0 * math.cos(6.283185 * i / n), y + r0 * math.sin(6.283185 * i / n), z)) for i in range(n)]
    B = [mb.vert((x + r1 * math.cos(6.283185 * i / n), y + r1 * math.sin(6.283185 * i / n), z)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        mb.add_face([A[i], B[i], B[j], A[j]], mi)


# ------------------------------------------------------------------ summer pool
def above_ground_pool(c, center, length=24 * FT, width=12 * FT, depth=52 * 0.0254, yaw=0.0, z_at=None, name='pool_frame'):
    """Rectangular frame pool (e.g. 24' x 12' x 52") standing on the turf."""
    z_at = _flat(z_at)
    mm = M()
    x, y = center
    z = z_at(x, y) + 0.03
    ca, sa = math.cos(yaw), math.sin(yaw)
    L2, W2 = length / 2, width / 2
    X = lambda u, v, w: Vector((x + ca * u - sa * v, y + sa * u + ca * v, z + w))
    tv, nv, up = Vector((ca, sa, 0)), Vector((-sa, ca, 0)), Vector((0, 0, 1))
    mb = MeshBuilder()
    # liner walls (thin box ring)
    for (u, v, lu, lv) in ((0, W2, length, 0.02), (0, -W2, length, 0.02), (L2, 0, 0.02, width), (-L2, 0, 0.02, width)):
        obox(mb, X(u, v, depth / 2), tv, nv, up, lu, lv, depth, mi=1)
    # top rail and legs (U-frames)
    for (u, v, lu, lv) in ((0, W2 + 0.03, length + 0.12, 0.06), (0, -W2 - 0.03, length + 0.12, 0.06), (L2 + 0.03, 0, 0.06, width + 0.12), (-L2 - 0.03, 0, 0.06, width + 0.12)):
        obox(mb, X(u, v, depth + 0.02), tv, nv, up, lu, lv, 0.05, mi=0)
    nleg = int(length / 1.0)
    for k in range(nleg + 1):
        u = -L2 + length * k / nleg
        for s in (1, -1):
            obox(mb, X(u, s * (W2 + 0.09), depth / 2), tv, nv, up, 0.05, 0.05, depth, mi=0)
            obox(mb, X(u, s * (W2 + 0.18), 0.02), tv, nv, up, 0.06, 0.25, 0.04, mi=0)
    for k in range(1, 4):
        v = -W2 + width * k / 4
        for s in (1, -1):
            obox(mb, X(s * (L2 + 0.09), v, depth / 2), tv, nv, up, 0.05, 0.05, depth, mi=0)
    obj(name, mb.build(name), c, [mm['pool_frame'], mm['pool_liner']])
    # water
    mb = MeshBuilder()
    obox(mb, X(0, 0, depth * 0.45), tv, nv, up, length - 0.04, width - 0.04, depth * 0.9)
    obj('pool_water', mb.build('pool_water'), c, mm['pool_water'])
    # A-frame ladder on one long side
    mb = MeshBuilder()
    for s in (-1, 1):
        for side in (-1, 1):
            p0 = X(s * 0.25, side * (W2 + 0.02), 0); p1 = X(s * 0.25, side * (W2 + 0.75), -0.03 * 0)
    for side in (1,):
        for s in (-0.25, 0.25):
            obox(mb, X(s, W2 + 0.35, depth / 2 + 0.2), tv, nv, up, 0.04, 0.7, 0.04, mi=0)
            obox(mb, X(s, W2 + 0.62, (depth + 0.3) / 2), tv, nv, up, 0.04, 0.04, depth + 0.3, mi=0)
        for k in range(4):
            obox(mb, X(0, W2 + 0.62 - 0.02 * k, 0.3 + k * 0.28), tv, nv, up, 0.5, 0.1, 0.03, mi=0)
    obj('pool_ladder', mb.build('pool_ladder'), c, mm['pool_frame'])


# ------------------------------------------------------------------ bubbling boulder fountains
def boulder_fountain(c, idx, top, base_center, base_r, spill=0.35):
    """top: (x, y, z) of the rock's crown; base_center/base_r: river-rock ring where the rock meets the ground."""
    mm = M()
    rng = random.Random(11 + idx)
    tx, ty, tz = top
    mb = MeshBuilder()
    # bubbling dome of water at the drilled top
    n, rings = 24, 5
    for i in range(rings):
        r0, r1 = 0.11 * i / rings, 0.11 * (i + 1) / rings
        h0, h1 = 0.05 * math.cos(math.pi / 2 * i / rings), 0.05 * math.cos(math.pi / 2 * (i + 1) / rings)
        A = [mb.vert((tx + r0 * math.cos(6.283 * k / n), ty + r0 * math.sin(6.283 * k / n), tz + h0)) for k in range(n)]
        B = [mb.vert((tx + r1 * math.cos(6.283 * k / n), ty + r1 * math.sin(6.283 * k / n), tz + h1)) for k in range(n)]
        for k in range(n):
            j = (k + 1) % n
            mb.add_face([A[k], B[k], B[j], A[j]], 0)
    obj('fountain_bubble%d' % idx, mb.build('bubble%d' % idx), c, mm['water'])
    # river-rock ring at the base (hides the reservoir grate)
    mb = MeshBuilder()
    bx, by, bz = base_center
    for k in range(int(260 * base_r)):
        a = rng.uniform(0, 6.283); r = base_r + rng.uniform(-0.05, 0.45)
        px, py = bx + r * math.cos(a), by + r * math.sin(a)
        s = rng.uniform(0.035, 0.08)
        obox(mb, Vector((px, py, bz + s * 0.3)), Vector((math.cos(a * 3), math.sin(a * 3), 0)), Vector((-math.sin(a * 3), math.cos(a * 3), 0)), Vector((0, 0, 1)),
             s * 1.5, s, s * 0.7, prand=rng.random())
    obj('fountain_rocks%d' % idx, mb.build('rocks%d' % idx), c, mm['pebble'])
    # thin wet sheen on the crown
    mb = MeshBuilder()
    _disc(mb, tx, ty, tz + 0.004, spill, 32, 0)
    obj('fountain_wet%d' % idx, mb.build('wet%d' % idx), c, mm['water'])


# ------------------------------------------------------------------ paths
def paver_path(c, pts, width=4 * FT, z_at=None, name='path_pavers', angle=45.0):
    """Gray herringbone pavers (same blend as the patio) inside a charcoal soldier border, following the polyline."""
    z_at = _flat(z_at)
    import hardscape
    line = LineString(pts)
    body = line.buffer(width / 2, cap_style=2, join_style=1)
    inner = line.buffer(width / 2 - 0.16, cap_style=2, join_style=1)
    rng = random.Random(5)
    mb = MeshBuilder()
    _draped(mb, body.difference(inner), lambda x, y: z_at(x, y) + 0.03, 0, step=0.3)
    obj(name + '_border_ground', mb.build(name + '_border'), c, mats._get('pavers_border', mats.pavers, border=True))
    mb = MeshBuilder()
    for g, cut in hardscape.herringbone(inner.buffer(-hardscape.PJ / 2, join_style=2), angle=angle, origin=pts[0]):
        g = g.simplify(0.0005)
        cx, cy = g.centroid.x, g.centroid.y
        z = z_at(cx, cy)
        mb.poly_prism(g, z - 0.02, z + 0.03, ch=0.0035, prand=rng.random(), simplify=0)
    o = obj(name + '_field_ground', mb.build(name + '_field'), c, mats._get('pavers', mats.pavers))
    mb = MeshBuilder()
    _draped(mb, inner, lambda x, y: z_at(x, y) + 0.022, 0, step=0.3)
    obj(name + '_sand', mb.build(name + '_sand'), c, mats._get('sand', mats.sand))
    return o


def stepping_path(c, pts, width=3 * FT, z_at=None, name='path_flagstone', seed=3):
    """Red flagstone stepping stones in tan decomposed granite."""
    z_at = _flat(z_at)
    mm = M()
    rng = random.Random(seed)
    line = LineString(pts)
    strip = line.buffer(width / 2 + 0.25, cap_style=1, join_style=1)
    mb = MeshBuilder()
    _draped(mb, strip, lambda x, y: z_at(x, y) + 0.015, 0, step=0.3)
    obj(name + '_gravel_ground', mb.build(name + '_gravel'), c, mm['gravel'])
    mb = MeshBuilder()
    L = line.length
    d = 0.35
    while d < L - 0.2:
        p = line.interpolate(d)
        q = line.interpolate(min(L, d + 0.05))
        ang = math.atan2(q.y - p.y, q.x - p.x)
        w, h = rng.uniform(0.55, 0.7) * width / 0.9144, rng.uniform(0.38, 0.5)
        stone = _blob((p.x, p.y), h / 2, w / 2, ang, rng.randint(0, 10 ** 6), n=14, wob=0.18)
        pts2 = ring_ccw(stone)
        z = z_at(p.x, p.y)
        mb.prism(pts2, z - 0.02, z + 0.035, ch=0.008, prand=rng.random())
        d += h + rng.uniform(0.12, 0.18)
    obj(name + '_stones_ground', mb.build(name + '_stones'), c, mm['flagstone'])
