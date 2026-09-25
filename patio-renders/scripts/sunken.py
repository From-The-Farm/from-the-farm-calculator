"""Sunken hot-tub lounge (per owner's note): floor ~2' below grade, sandy light-red brick seat wall
~18" above the yard on the plan's 7.5" border band, and steps down from the lawn on the south side
(paver treads, brick risers)."""
import math, random
from mathutils import Vector
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
import plan as P
from bl import MeshBuilder, obj, obox
import mats
from hardscape import Z_TOP, herringbone, PJ, _polys

SUNK = 0.61                       # 2'-0"
Z_FLOOR = Z_TOP - SUNK            # finished paver floor
WALL_TOP = 0.46                   # ~18" above the yard
CAP_H = 0.092                     # rowlock cap (brick on edge)
CAP_OV = 0.02                     # cap overhang each side
BW = 8.46 * P.M_PER_PT            # wall thickness as drawn (7.5")
STAIR_W = 1.524                   # 5'-0" clear
N_RISE = 4
RISER = -Z_FLOOR / N_RISE if Z_FLOOR < 0 else 0.145   # lawn (z=0) down to the floor
TREAD = 0.35
BR_L, BR_H, BR_J = 0.194, 0.057, 0.0095               # modular brick + joint

def R(xa, ya, xb, yb):
    p, q = P.W((xa, ya)), P.W((xb, yb))
    return (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))

def layout():
    """Wall runs (world rects) + stair geometry. The stair sits at the west end of the south wall,
    right in front of the house's back door (matches the existing step in the owner's photos);
    the lower wing's west wall doubles as the stair's west cheek."""
    runs = {
        'N': (R(641.52, 300.42, 1038.60, 308.88), 'x'),
        'W': (R(641.52, 308.88, 649.98, 521.46), 'y'),
        'SH': (R(641.52, 521.46, 793.98, 529.92), 'x'),
        'SV': (R(785.52, 529.92, 793.98, 638.46), 'y'),
        'E': (R(1030.14, 308.88, 1038.60, 638.46), 'y'),
    }
    s = R(785.52, 638.46, 1038.60, 646.92)          # south run (house/patio side)
    sv = runs['SV'][0]
    xo0 = sv[2]                                     # inner face of the west wing wall
    xo1 = xo0 + STAIR_W
    y_top = s[1]                                    # outer (patio) face
    lines = [y_top, s[3] + TREAD * 0.49]
    for k in range(2, N_RISE):
        lines.append(lines[-1] + TREAD)
    y_bot = lines[-1]
    runs['SW'] = ((s[0], s[1], xo0, s[3]), 'x')    # corner block under the west cheek
    runs['SE'] = ((xo1 + BW, s[1], s[2], s[3]), 'x')
    runs['CE'] = ((xo1, y_top, xo1 + BW, y_bot), 'y')
    return runs, dict(x0=xo0, x1=xo1, lines=lines, y_top=y_top, y_bot=y_bot)

def floor_region():
    runs, st = layout()
    cut = box(st['x0'] - 0.01, st['y_top'] - 0.01, st['x1'] + BW, st['y_bot'])
    return P.LOUNGE_IN.difference(cut)

def _brick_face(mb, a, b, nrm, z0, z1, rng, depth=0.014, back=0.006):
    """Running-bond bricks on the vertical face from a to b (xy Vectors), outward normal nrm."""
    t = (b - a); L = t.length
    if L < 0.03: return
    t.normalize()
    mod_l, mod_h = BR_L + BR_J, BR_H + BR_J
    z = z0 + BR_J / 2
    row = 0
    off0 = rng.uniform(0, mod_l)
    while z + BR_H <= z1 + 0.004:
        off = off0 + (mod_l / 2 if row % 2 else 0.0)
        u = -off
        while u < L:
            ua, ub = max(u + BR_J / 2, 0.002), min(u + mod_l - BR_J / 2, L - 0.002)
            if ub - ua > 0.03:
                um = (ua + ub) / 2
                cen = a + t * um + nrm * (depth / 2 - back)
                obox(mb, Vector((cen.x, cen.y, z + BR_H / 2)), Vector((t.x, t.y, 0)), Vector((nrm.x, nrm.y, 0)), Vector((0, 0, 1)),
                     ub - ua, depth, BR_H, prand=rng.random())
            u += mod_l
        z += mod_h; row += 1

def build_sunken(c):
    rng = random.Random(33)
    brick = mats._get('brick_sandy_red', mats.brick)
    mortar = mats._get('mortar_buff', mats.mortar_buff)
    runs, st = layout()
    wall = unary_union([box(*r) for r, _ in runs.values()])
    cap_bot = WALL_TOP - CAP_H
    # ---- mortar core
    mb = MeshBuilder()
    mb.poly_prism(wall.buffer(-0.006, join_style=2), Z_FLOOR - 0.05, cap_bot, 0.0, simplify=0)
    obj('SunkenWallCore', mb.build('wallcore'), c, mortar)
    # ---- brick faces around the whole wall outline
    mb = MeshBuilder()
    for poly in _polys(wall):
        ring = list(orient(poly, 1.0).exterior.coords)[:-1]
        n = len(ring)
        for i in range(n):
            a = Vector(ring[i]); b = Vector(ring[(i + 1) % n])
            e = b - a
            if e.length < 0.02: continue
            tdir = e.normalized(); nrm = Vector((tdir.y, -tdir.x))
            mid = (a + b) / 2 + nrm * 0.05
            inside = P.LOUNGE_OUT.buffer(-0.001).contains(Point(mid.x, mid.y))
            z0 = Z_FLOOR if inside else -0.06
            _brick_face(mb, a, b, nrm, z0, cap_bot - 0.004, rng)
    obj('SunkenWallBricks', mb.build('wallbricks'), c, brick)
    # ---- rowlock cap
    mb = MeshBuilder()
    mod = BR_H + BR_J
    for key, (r, ax) in runs.items():
        x0, y0, x1, y1 = r
        if ax == 'x':
            L = x1 - x0; nb = max(1, int(round(L / mod)))
            step = L / nb
            for i in range(nb):
                cx = x0 + (i + 0.5) * step
                obox(mb, (cx, (y0 + y1) / 2, cap_bot + CAP_H / 2), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)),
                     step - BR_J, (y1 - y0) + 2 * CAP_OV, CAP_H - 0.003, prand=rng.random())
        else:
            L = y1 - y0; nb = max(1, int(round(L / mod)))
            step = L / nb
            for i in range(nb):
                cy = y0 + (i + 0.5) * step
                obox(mb, ((x0 + x1) / 2, cy, cap_bot + CAP_H / 2), Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1)),
                     step - BR_J, (x1 - x0) + 2 * CAP_OV, CAP_H - 0.003, prand=rng.random())
    obj('SunkenWallCap', mb.build('wallcap'), c, brick)
    # ---- stairs: paver treads + brick risers
    lines = st['lines']
    x0, x1 = st['x0'], st['x1']
    tops = [-(k + 1) * RISER for k in range(N_RISE - 1)]           # tread tops
    core = MeshBuilder(); risers = MeshBuilder(); treads = MeshBuilder()
    paver_t = 0.06
    for k, top in enumerate(tops):
        ya = lines[k]; yb = lines[k + 1] if k + 1 < len(lines) else st['y_bot']
        # solid body under the tread (hidden mostly)
        core.box(x0 + 0.002, ya, Z_FLOOR - 0.02, x1 - 0.002, yb - 0.006, top - paver_t)
        # pavers: 6x12 running bond, long side along x, rows from the nose back
        nose = yb + 0.02
        y = nose; row = 0
        while y > ya + 0.01:
            y_lo = max(ya, y - 0.1524)
            off = 0.0 if row % 2 == 0 else 0.1524
            xx = x0 - off
            while xx < x1 - 0.01:
                xa_, xb_ = max(xx, x0) + PJ / 2, min(xx + 0.3048, x1) - PJ / 2
                if xb_ - xa_ > 0.03:
                    treads.poly_prism(box(xa_, y_lo + PJ / 2, xb_, y - PJ / 2), top - paver_t, top, ch=0.0035, prand=rng.random(), simplify=0)
                xx += 0.3048
            y = y_lo; row += 1
        # riser under the nose: brick face (faces +y, toward the sunken floor)
        z_lo = tops[k + 1] if k + 1 < len(tops) else Z_FLOOR
        _brick_face(risers, Vector((x1, yb)), Vector((x0, yb)), Vector((0, 1)), z_lo, top - paver_t - 0.002, rng, depth=0.012, back=0.012)
    # top riser: lawn edge down to the first tread
    _brick_face(risers, Vector((x1, lines[0] + 0.0)), Vector((x0, lines[0] + 0.0)), Vector((0, 1)), tops[0] - 0.004, -0.01, rng, depth=0.012, back=0.012)
    obj('StairCore', core.build('staircore'), c, mortar)
    obj('StairRisers', risers.build('risers'), c, brick)
    obj('StairTreads', treads.build('treads'), c, mats._get('pavers', mats.pavers))
    return st
