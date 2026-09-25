"""U-shaped outdoor kitchen: stacked-stone base, stone countertop, built-in grill, sink, fridge + ice maker,
stainless access doors/drawers."""
import math, random
import bpy
from mathutils import Vector
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
import plan as P
from bl import MeshBuilder, obj, coll, prism_holes, extrude_profile_x, obox, curve_tube, cylinder_mesh, rrect, box_obj, bevel_box_mesh
import mats
from hardscape import Z_TOP
import pavilion

H_TOP = 0.914 + Z_TOP     # 36" counter
CT_T = 0.04               # countertop thickness
H_BASE = H_TOP - CT_T

def u_poly():
    rs = [P.COUNTER_BACK, P.COUNTER_TOP, P.COUNTER_BOT]
    return unary_union([box(*r) for r in rs])

def openings():
    """per face: list of (u0,u1,z0,z1) rectangles in face-local coords to keep free of stone."""
    top_front = P.COUNTER_TOP[1]      # y of top-leg inner face
    bot_front = P.COUNTER_BOT[3]      # y of bottom-leg inner face
    back_front = P.COUNTER_BACK[0]    # x of back-leg inner face
    gx0, gx1 = P.GRILL[0] + 0.01, P.GRILL[2] - 0.01
    fx0, fx1 = P.FRIDGE[0], P.FRIDGE[2]
    sy = (P.SINK[1] + P.SINK[3]) / 2
    return dict(
        grill=(gx0, gx1), fridge=(fx0, fx1), sink_y=sy,
        top_front=top_front, bot_front=bot_front, back_front=back_front,
        rects=[
            # (axis, plane coordinate, facing sign, a0, a1, z0, z1)
            ('y', top_front, -1, gx0, gx1, Z_TOP + 0.10, H_TOP),                   # grill panel + doors below
            ('y', top_front, -1, gx1 + 0.08, gx1 + 0.08 + 0.46, Z_TOP + 0.10, H_BASE - 0.05),  # drawer stack
            ('x', back_front, -1, sy - 0.40, sy + 0.40, Z_TOP + 0.14, Z_TOP + 0.72),   # sink doors
            ('y', bot_front, 1, fx0, fx1, Z_TOP + 0.0, H_BASE - 0.005),             # fridge + ice maker
            ('y', bot_front, 1, fx1 + 0.12, fx1 + 0.12 + 0.46, Z_TOP + 0.14, Z_TOP + 0.72),  # trash pull-out
        ])

def build_stone(c, rng):
    core = u_poly()
    mortar = mats._get('mortar', mats.simple, mats.lin((88, 86, 82)), 0.95, 0.0, 0.3, 0.3, 120.0)
    mb = MeshBuilder()
    mb.poly_prism(core.buffer(-0.012, join_style=2), Z_TOP, H_BASE, 0.0, simplify=0)
    obj('CounterCore', mb.build('core'), c, mortar)
    ops = openings()['rects']
    poly = orient(core, 1.0)
    pts = list(poly.exterior.coords)[:-1]
    mb = MeshBuilder()
    n = len(pts)
    for i in range(n):
        a = Vector((*pts[i], 0)); b = Vector((*pts[(i + 1) % n], 0))
        e = b - a; L = e.length
        if L < 0.05: continue
        t = e / L
        nrm = Vector((t.y, -t.x, 0))                     # outward for CCW
        # which openings live on this face?
        face_ops = []
        for (axis, coord, sgn, a0, a1, z0, z1) in ops:
            if axis == 'y' and abs(t.y) < 1e-6 and abs(a.y - coord) < 0.02 and nrm.y * sgn > 0:
                u0 = (a0 - a.x) / t.x; u1 = (a1 - a.x) / t.x
                face_ops.append((min(u0, u1), max(u0, u1), z0, z1))
            if axis == 'x' and abs(t.x) < 1e-6 and abs(a.x - coord) < 0.02 and nrm.x * sgn > 0:
                u0 = (a0 - a.y) / t.y; u1 = (a1 - a.y) / t.y
                face_ops.append((min(u0, u1), max(u0, u1), z0, z1))
        z = Z_TOP + 0.005
        while z < H_BASE - 0.02:
            hrow = rng.choice([0.035, 0.045, 0.05, 0.06, 0.07, 0.085])
            hrow = min(hrow, H_BASE - 0.004 - z)
            u = -rng.uniform(0.0, 0.25)
            while u < L:
                sl = rng.uniform(0.16, 0.62)
                ua, ub = max(u, 0.0) + 0.003, min(u + sl, L) - 0.003
                u += sl
                if ub - ua < 0.03: continue
                segs = [(ua, ub)]
                for (o0, o1, oz0, oz1) in face_ops:
                    if z + hrow > oz0 and z < oz1:
                        new = []
                        for (s0, s1) in segs:
                            if s1 <= o0 or s0 >= o1: new.append((s0, s1)); continue
                            if s0 < o0 - 0.01: new.append((s0, o0 - 0.004))
                            if s1 > o1 + 0.01: new.append((o1 + 0.004, s1))
                        segs = new
                for (s0, s1) in segs:
                    if s1 - s0 < 0.025: continue
                    depth = rng.uniform(0.014, 0.036)
                    um = (s0 + s1) / 2
                    cen = a + t * um + nrm * (depth / 2 - 0.012) + Vector((0, 0, z + hrow / 2))
                    obox(mb, cen, t, nrm, Vector((0, 0, 1)), s1 - s0, depth, hrow - 0.006, prand=rng.random())
            z += hrow
    obj('StoneVeneer', mb.build('stones'), c, mats._get('stone_veneer', mats.stone_veneer))

def build_countertop(c):
    g = pavilion.geometry()
    x0, y0, x1, y1 = P.PAVILION
    top = u_poly().buffer(0.03, join_style=2)
    # notch around the two east posts
    for (px, py) in [(x1 - pavilion.PS / 2, y0 + pavilion.PS / 2), (x1 - pavilion.PS / 2, y1 - pavilion.PS / 2)]:
        top = top.difference(box(px - pavilion.PS / 2 - 0.006, py - pavilion.PS / 2 - 0.006, px + pavilion.PS / 2 + 0.006, py + pavilion.PS / 2 + 0.006))
    # grill opening (hood sits in it)
    top = top.difference(box(P.GRILL[0], P.COUNTER_TOP[1] - 0.05, P.GRILL[2], P.COUNTER_TOP[3] - 0.04))
    # sink opening
    sx, sy = sink_centre()
    top = top.difference(rrect(sx, sy, 0.40, 0.52, 0.035))
    mb = MeshBuilder()
    prism_holes(mb, top, H_BASE, H_TOP)
    obj('Countertop', mb.build('countertop'), c, mats._get('countertop', mats.countertop))

def sink_centre():
    return ((P.COUNTER_BACK[0] + P.COUNTER_BACK[2]) / 2 - 0.02, (P.SINK[1] + P.SINK[3]) / 2)

def build_grill(c):
    ss = mats._get('stainless', mats.stainless)
    dark = mats._get('black_plastic', mats.simple, mats.lin((20, 20, 20)), 0.35, 0.0, 0.5)
    gx0, gx1 = P.GRILL[0] + 0.01, P.GRILL[2] - 0.01
    yf = P.COUNTER_TOP[1]                  # counter face (y), grill faces -y
    yb = P.COUNTER_TOP[3] - 0.06
    mb = MeshBuilder()
    # control panel (proud of the stone) + frame/drip tray
    mb.box(gx0, yf - 0.035, H_BASE - 0.20, gx1, yf + 0.02, H_TOP + 0.005)
    # hood: extruded profile along X (y, z), CCW with +y to the right
    yh0, yh1 = yf - 0.02, yb
    zh0 = H_TOP + 0.01
    D = yh1 - yh0
    prof = [(yh0, zh0), (yh1, zh0), (yh1, zh0 + 0.24)]
    for k in range(11, 0, -1):
        s = k / 12
        prof.append((yh0 + s * D, zh0 + 0.10 + 0.14 * math.sin(math.pi / 2 * s)))
    prof.append((yh0, zh0 + 0.10))
    extrude_profile_x(mb, prof, gx0 + 0.03, gx1 - 0.03)
    # grill frame lip on the counter
    mb.box(gx0, yf - 0.02, H_TOP - 0.002, gx1, yb + 0.03, H_TOP + 0.012)
    obj('GrillBody', mb.build('grill'), c, ss)
    # knobs
    kn = 5
    for i in range(kn):
        x = gx0 + 0.16 + i * (gx1 - gx0 - 0.32) / (kn - 1)
        me = cylinder_mesh('knob%d' % i, 0.026, 0.035, seg=24)
        o = obj('GrillKnob%d' % i, me, c, dark)
        o.location = (x, yf - 0.035, H_BASE - 0.09); o.rotation_euler = (math.pi / 2, 0, 0)
    # hood handle
    zhh = H_TOP + 0.13
    curve_tube('GrillHandle', [(gx0 + 0.12, yf - 0.02, zhh), (gx0 + 0.12, yf - 0.085, zhh), (gx1 - 0.12, yf - 0.085, zhh), (gx1 - 0.12, yf - 0.02, zhh)],
               0.012, ss, c)
    # access doors under the grill
    doors(c, 'GrillDoors', 'y', yf, -1, gx0 + 0.02, gx1 - 0.02, Z_TOP + 0.12, H_BASE - 0.24, n=2)

def doors(c, name, axis, plane, facing, a0, a1, z0, z1, n=2, drawer=False):
    """Stainless access doors/drawers set into a counter face."""
    ss = mats._get('stainless', mats.stainless)
    mb = MeshBuilder()
    t = 0.022
    if not drawer:
        w = (a1 - a0) / n
        for i in range(n):
            u0, u1 = a0 + i * w + 0.004, a0 + (i + 1) * w - 0.004
            _panel(mb, axis, plane, facing, u0, u1, z0, z1, t)
    else:
        hs = [0.2, 0.25, 0.3]
        tot = sum(hs); z = z1
        for h in hs:
            hh = (z1 - z0) * h / tot
            _panel(mb, axis, plane, facing, a0, a1, z - hh + 0.004, z - 0.004, t)
            z -= hh
    obj(name, mb.build(name), c, ss)
    # handles
    if not drawer:
        w = (a1 - a0) / n
        for i in range(n):
            ua = a0 + i * w + (w * 0.8 if (i % 2 == 0 and n == 2) else w * 0.2)
            _vhandle(c, name + 'H%d' % i, axis, plane, facing, ua, (z0 + z1) / 2, 0.24)
    else:
        z = z1
        for k, h in enumerate([0.2, 0.25, 0.3]):
            hh = (z1 - z0) * h / 0.75
            _hhandle(c, name + 'H%d' % k, axis, plane, facing, (a0 + a1) / 2, z - 0.06, 0.28)
            z -= hh

def _panel(mb, axis, plane, facing, u0, u1, z0, z1, t):
    if axis == 'y':
        ya, yb = (plane - t, plane + 0.004) if facing < 0 else (plane - 0.004, plane + t)
        mb.box(u0, ya, z0, u1, yb, z1)
    else:
        xa, xb = (plane - t, plane + 0.004) if facing < 0 else (plane - 0.004, plane + t)
        mb.box(xa, u0, z0, xb, u1, z1)

def _vhandle(c, name, axis, plane, facing, u, zc, L):
    ss = mats._get('stainless', mats.stainless)
    off = 0.022 + 0.035
    if axis == 'y':
        y = plane + facing * off; yb = plane + facing * 0.022
        pts = [(u, yb, zc - L / 2), (u, y, zc - L / 2), (u, y, zc + L / 2), (u, yb, zc + L / 2)]
    else:
        x = plane + facing * off; xb = plane + facing * 0.022
        pts = [(xb, u, zc - L / 2), (x, u, zc - L / 2), (x, u, zc + L / 2), (xb, u, zc + L / 2)]
    curve_tube(name, pts, 0.008, ss, c)

def _hhandle(c, name, axis, plane, facing, u, zc, L):
    ss = mats._get('stainless', mats.stainless)
    off = 0.022 + 0.03
    if axis == 'y':
        y = plane + facing * off; yb = plane + facing * 0.022
        pts = [(u - L / 2, yb, zc), (u - L / 2, y, zc), (u + L / 2, y, zc), (u + L / 2, yb, zc)]
    else:
        x = plane + facing * off; xb = plane + facing * 0.022
        pts = [(xb, u - L / 2, zc), (x, u - L / 2, zc), (x, u + L / 2, zc), (xb, u + L / 2, zc)]
    curve_tube(name, pts, 0.008, ss, c)

def build_sink(c):
    ss = mats._get('stainless', mats.stainless)
    sx, sy = sink_centre()
    w, d, depth = 0.40, 0.52, 0.21
    mb = MeshBuilder()
    x0, x1, y0, y1 = sx - w / 2, sx + w / 2, sy - d / 2, sy + d / 2
    zb, zt = H_BASE - depth, H_BASE + 0.002
    V = lambda x, y, z: mb.vert((x, y, z))
    # inward facing basin: floor + 4 walls (normals toward the inside)
    f = [V(x0, y0, zb), V(x1, y0, zb), V(x1, y1, zb), V(x0, y1, zb)]
    mb.add_face(f)
    t = [V(x0, y0, zt), V(x1, y0, zt), V(x1, y1, zt), V(x0, y1, zt)]
    for i in range(4):
        j = (i + 1) % 4
        mb.add_face([f[j], f[i], t[i], t[j]])
    obj('SinkBasin', mb.build('sink'), c, ss)
    drain = obj('SinkDrain', cylinder_mesh('drain', 0.04, 0.003, seg=24), c, mats._get('black_plastic', mats.simple, mats.lin((20, 20, 20)), 0.35, 0.0, 0.5))
    drain.location = (sx, sy, zb + 0.001)
    # gooseneck faucet at the back of the counter
    fx = P.COUNTER_BACK[2] - 0.09
    base = obj('FaucetBase', cylinder_mesh('fb', 0.028, 0.05, seg=24), c, ss); base.location = (fx, sy, H_TOP)
    curve_tube('Faucet', [(fx, sy, H_TOP + 0.04), (fx, sy, H_TOP + 0.30), (fx - 0.10, sy, H_TOP + 0.40), (fx - 0.20, sy, H_TOP + 0.30), (fx - 0.21, sy, H_TOP + 0.22)], 0.014, ss, c)
    curve_tube('FaucetLever', [(fx, sy + 0.02, H_TOP + 0.12), (fx + 0.02, sy + 0.09, H_TOP + 0.15)], 0.007, ss, c)
    doors(c, 'SinkDoors', 'x', P.COUNTER_BACK[0], -1, sy - 0.38, sy + 0.38, Z_TOP + 0.14, Z_TOP + 0.72, n=2)

def build_fridge(c):
    ss = mats._get('stainless', mats.stainless)
    dark = mats._get('black_plastic', mats.simple, mats.lin((20, 20, 20)), 0.35, 0.0, 0.5)
    yf = P.COUNTER_BOT[3]
    x0, x1 = P.FRIDGE[0], P.FRIDGE[2]
    xm = x0 + 0.61
    mb = MeshBuilder()
    mb.box(x0 + 0.003, yf - 0.01, Z_TOP + 0.11, xm - 0.003, yf + 0.028, H_BASE - 0.008)
    mb.box(xm + 0.006, yf - 0.01, Z_TOP + 0.11, x1 - 0.003, yf + 0.028, H_BASE - 0.008)
    obj('FridgeDoors', mb.build('fridge'), c, ss)
    mb = MeshBuilder()
    mb.box(x0 + 0.003, yf - 0.01, Z_TOP + 0.005, x1 - 0.003, yf + 0.012, Z_TOP + 0.105)
    obj('FridgeKick', mb.build('kick'), c, dark)
    for k, xx in enumerate([xm - 0.06, x1 - 0.06]):
        _vhandle(c, 'FridgeHandle%d' % k, 'y', yf + 0.028 - 0.022, 1, xx, (Z_TOP + H_BASE) / 2 + 0.05, 0.5)
    doors(c, 'TrashPullout', 'y', yf, 1, x1 + 0.12, x1 + 0.12 + 0.46, Z_TOP + 0.14, Z_TOP + 0.72, n=1)

def build_kitchen(c):
    rng = random.Random(21)
    build_stone(c, rng)
    build_countertop(c)
    build_grill(c)
    build_sink(c)
    build_fridge(c)
    o = openings()
    doors(c, 'Drawers', 'y', o['top_front'], -1, o['grill'][1] + 0.08, o['grill'][1] + 0.08 + 0.46, Z_TOP + 0.10, H_BASE - 0.05, drawer=True)
