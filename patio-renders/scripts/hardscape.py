"""Concrete walk, kitchen pad, mow strip, herringbone pavers, lawn + yard ground meshes."""
import math, random
import bpy
from shapely.geometry import Polygon, LineString, box, MultiPolygon, Point
from shapely.ops import unary_union
from shapely.affinity import rotate
from shapely.prepared import prep
import plan as P
from bl import MeshBuilder, obj, coll
import mats

Z_TOP = 0.030          # finished hardscape surface (m above lawn soil)
JOINT = 0.0035         # half-width of tooled joints / slab separation

def _extend(line, d):
    (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    return LineString([(x0 - ux * d, y0 - uy * d), (x1 + ux * d, y1 + uy * d)])

def _dir(line):
    (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
    L = math.hypot(x1 - x0, y1 - y0)
    return ((x1 - x0) / L, (y1 - y0) / L, 0.0)

def _polys(g):
    if g.is_empty: return []
    return [g] if g.geom_type == 'Polygon' else [x for x in g.geoms if x.geom_type == 'Polygon']

def build_concrete(c):
    rng = random.Random(7)
    cuts = unary_union([_extend(j, 0.10).buffer(JOINT, cap_style=2) for j in P.JOINTS])
    pieces = _polys(P.BAND.difference(cuts))
    mb = MeshBuilder()
    for pc in pieces:
        pc = pc.buffer(-JOINT, join_style=2)
        for q in _polys(pc):
            # broom strokes run parallel to the nearest control joint
            j = min(P.JOINTS, key=lambda L: L.distance(q))
            d = _dir(j)
            mb.poly_prism(q, -0.08, Z_TOP, ch=0.006, prand=rng.random(), bdir=d)
    for q in _polys(P.PAD.buffer(-JOINT, join_style=2)):
        mb.poly_prism(q, -0.08, Z_TOP, ch=0.006, prand=rng.random(), bdir=(0.0, 1.0, 0.0))
    # joint bottoms (continuous slab 10mm below the top)
    base = unary_union([P.BAND, P.PAD]).buffer(-0.0005)
    mb.flat_poly(base, Z_TOP - 0.010, prand=0.5, bdir=(1.0, 0.0, 0.0))
    me = mb.build('walk_and_pad', {'bdir': 'FLOAT_VECTOR'})
    o = obj('Concrete_Walk_Pad', me, c, mats._get('concrete', mats.concrete))
    # mow strip (charcoal, smooth)
    mb = MeshBuilder()
    for q in _polys(P.MOW.buffer(-JOINT, join_style=2)):
        mb.poly_prism(q, -0.08, Z_TOP, ch=0.006, prand=0.5, bdir=(1.0, 0.0, 0.0))
    me = mb.build('mow_strip', {'bdir': 'FLOAT_VECTOR'})
    obj('Mow_Strip', me, c, mats._get('concrete_charcoal', mats.concrete, base=mats.lin((72, 72, 72)), rough=0.7, broom=0.05, mott=0.06, charcoal=True))
    return o

# ------------------------------------------------------------------------------------ pavers
FIELD_W = 0.1524       # 6" x 12" field pavers
FIELD_L = 2 * FIELD_W
BORDER_W_SHEET = 8.46  # border width as drawn (7.5")
BORDER_LEN = 0.40      # 8" x 16" border units laid lengthwise (sailor course)
PJ = 0.0045            # paver joint width

def herringbone(region, W=FIELD_W, angle=45.0, origin=(0.0, 0.0), joint=PJ):
    loc = rotate(region, -angle, origin=origin)
    minx, miny, maxx, maxy = loc.bounds
    preg = prep(region)
    out = []
    a0, a1 = int(math.floor(minx / W)) - 4, int(math.ceil(maxx / W)) + 2
    b0, b1 = int(math.floor(miny / W)) - 4, int(math.ceil(maxy / W)) + 2
    h = joint / 2
    for a in range(a0, a1):
        for b in range(b0, b1):
            if (a + b) % 2 or (a - b) % 4: continue
            px, py = W * a, W * b
            for bx in (box(px + h, py + h, px + 2 * W - h, py + W - h), box(px + h, py + W + h, px + W - h, py + 3 * W - h)):
                r = rotate(bx, angle, origin=origin)
                if not preg.intersects(r): continue
                if preg.contains(r):
                    out.append((r, False))
                else:
                    cut = region.intersection(r)
                    for g in _polys(cut):
                        if g.area > 0.0012:
                            out.append((g, True))
    return out

def sailor_border(strips, unit=BORDER_LEN, joint=PJ):
    """strips: list of (x0,y0,x1,y1) world rects; units run along the long side."""
    out = []
    h = joint / 2
    for (x0, y0, x1, y1) in strips:
        horiz = (x1 - x0) >= (y1 - y0)
        L = (x1 - x0) if horiz else (y1 - y0)
        n = max(1, int(round(L / unit)))
        step = L / n
        for i in range(n):
            if horiz:
                out.append(box(x0 + i * step + h, y0 + h, x0 + (i + 1) * step - h, y1 - h))
            else:
                out.append(box(x0 + h, y0 + i * step + h, x1 - h, y0 + (i + 1) * step - h))
    return out

def lounge_border_strips():
    W = P.W; b = BORDER_W_SHEET
    def r(xa, ya, xb, yb):
        p, q = W((xa, ya)), W((xb, yb))
        return (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
    return [
        r(641.52, 300.42, 1038.60, 300.42 + b),          # north (full length)
        r(641.52, 308.88, 641.52 + b, 521.46),           # west
        r(641.52, 521.46, 793.98, 529.92),               # step (horizontal, full)
        r(785.52, 529.92, 793.98, 638.46),               # step (vertical)
        r(785.52, 638.46, 1038.60, 646.92),              # south (full length)
        r(1030.14, 308.88, 1038.60, 638.46),             # east (beside the walk)
    ]

def build_pavers(c):
    rng = random.Random(11)
    field = herringbone(P.LOUNGE_IN.buffer(-PJ / 2, join_style=2)) + herringbone(P.NOOK.buffer(-PJ / 2, join_style=2))
    mb = MeshBuilder()
    for g, cut in field:
        g = g.simplify(0.0005)
        pr = rng.random()
        mb.poly_prism(g, 0.0, Z_TOP, ch=0.0035, prand=pr, simplify=0)
    me = mb.build('pavers_field')
    obj('Pavers_Field', me, c, mats._get('pavers', mats.pavers))
    mb = MeshBuilder()
    for g in sailor_border(lounge_border_strips()):
        mb.poly_prism(g, 0.0, Z_TOP, ch=0.0035, prand=rng.random(), simplify=0)
    me = mb.build('pavers_border')
    obj('Pavers_Border', me, c, mats._get('pavers_border', mats.pavers,
        tones=[(0.0, mats.lin((58, 57, 56))), (0.5, mats.lin((50, 49, 48))), (0.8, mats.lin((44, 43, 43)))]))
    # joint sand bed
    mb = MeshBuilder()
    mb.flat_poly(unary_union([P.LOUNGE_OUT, P.NOOK]), Z_TOP - 0.007)
    obj('Paver_Joint_Sand', mb.build('sand'), c, mats._get('sand', mats.sand))
    return len(field)

# ------------------------------------------------------------------------------------ ground
YARD = dict(x0=-19.0, x1=15.9, y0=-18.9, y1=18.9)    # fenced yard (house side open to the west)

def design_footprint():
    return unary_union([P.OUTER, P.LOUNGE_OUT])

def build_ground(c):
    """Returns (lawn_obj, yard_obj) meshes that the grass system will populate."""
    mb = MeshBuilder()
    mb.flat_poly(P.LAWN, 0.0)
    lawn = obj('Lawn_Proposed', mb.build('lawn'), c, mats._get('soil', mats.soil))
    yard_poly = box(YARD['x0'] - 30.0, YARD['y0'], YARD['x1'], YARD['y1']).difference(design_footprint().buffer(0.01))
    mb = MeshBuilder()
    mb.flat_poly(yard_poly, 0.0)
    yard = obj('Lawn_Yard', mb.build('yard'), c, mats._get('soil', mats.soil))
    # far ground (neighbours) — plain, below grass line
    mb = MeshBuilder()
    far = box(-160, -160, 160, 160).difference(box(YARD['x0'] - 30.0, YARD['y0'], YARD['x1'], YARD['y1']))
    mb.flat_poly(far, -0.005)
    obj('Ground_Far', mb.build('far'), c, mats._get('far_lawn', far_lawn))
    return lawn, yard

def far_lawn(name):
    m, nt = mats.new_material(name)
    Pp = mats._pos(nt)
    n1 = mats._noise(nt, Pp, 0.08, 4, 0.6)
    n2 = mats._noise(nt, Pp, 2.0, 5, 0.6)
    col = nt.mix(n1, mats.lin((44, 70, 22)), mats.lin((60, 82, 30)))
    col = mats._tint(nt, col, mats._centered(nt, n2, 0.15))
    bump = nt.n('ShaderNodeBump', Strength=0.4, Distance=0.02, Height=n2)
    b = mats.principled(nt, Base_Color=col, Roughness=0.9, Normal=bump.outputs[0])
    # aerial perspective: fade toward the horizon colour with camera distance
    lp = nt.n('ShaderNodeLightPath')
    fac = nt.math('SUBTRACT', 1.0, nt.math('EXPONENT', nt.math('DIVIDE', lp.outputs['Ray Length'], -700.0)))
    fac = nt.math('MULTIPLY', fac, lp.outputs['Is Camera Ray'])
    em = nt.n('ShaderNodeEmission', Color=(0.20, 0.27, 0.36), Strength=1.0)
    mix = nt.n('ShaderNodeMixShader', Fac=fac)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(em.outputs[0], mix.inputs[2])
    mats.finish(nt, mix)
    return m
