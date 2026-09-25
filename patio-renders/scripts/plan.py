"""Exact geometry of the Zitting concrete-pad plan (sheet 1, AutoCAD PDF).

Drawing scale is 3/16" = 1'-0"  ->  13.5 PDF points per foot.
World units are meters. +X = sheet right, +Y = sheet up ("north"); house is to the west (-X).
"""
import json, math, os
from shapely.geometry import Polygon, LineString, box, Point, MultiPolygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
PT_PER_FT = 13.5
M_PER_FT = 0.3048
M_PER_PT = M_PER_FT / PT_PER_FT
OX, OY = 1137.42, 931.68          # sheet point that maps to world origin

def W(p):
    """sheet point (x, y down) -> world meters (x, y up)"""
    return ((p[0] - OX) * M_PER_PT, (OY - p[1]) * M_PER_PT)

def ft(v):
    return v * M_PER_FT

_D = json.load(open(os.path.join(HERE, '..', 'drawings.json')))['0']

def _key(r):
    return (r['type'], round(r['color'][0], 3) if r['color'] else None, round(r['width'] or 0, 3))

def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; mt = 1 - t
        out.append((mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0],
                    mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]))
    return out

def path_points(r, n=24):
    pts = []
    for it in r['items']:
        if it[0] == 'l':
            seg = [tuple(it[1]), tuple(it[2])]
        elif it[0] == 'c':
            seg = bez(it[1], it[2], it[3], it[4], n)
        else:
            continue
        if pts and math.dist(pts[-1], seg[0]) < 0.5:
            pts.extend(seg[1:])
        elif pts and math.dist(pts[-1], seg[-1]) < 0.5:
            pts.extend(list(reversed(seg))[1:])
        else:
            pts.extend(seg)
    return pts

HEAVY = [r for r in _D if _key(r) == ('s', 0.0, 1.62)]

def find(pred):
    out = [r for r in HEAVY if pred(r['rect'])]
    return out

def near(a, b, tol=1.0):
    return all(abs(x - y) < tol for x, y in zip(a, b))

def get(rect, tol=1.0):
    m = [r for r in HEAVY if near(r['rect'], rect, tol)]
    assert m, rect
    return m[0]

def chain(segs, tol=6.0):
    """Chain point sequences into one closed loop (greedy, allows reversing)."""
    segs = [list(s) for s in segs]
    loop = segs.pop(0)
    while segs:
        end = loop[-1]
        best = None
        for i, s in enumerate(segs):
            d0 = math.dist(end, s[0]); d1 = math.dist(end, s[-1])
            if best is None or min(d0, d1) < best[0]:
                best = (min(d0, d1), i, d1 < d0)
        d, i, rev = best
        assert d < tol, (d, end)
        s = segs.pop(i)
        if rev: s = s[::-1]
        # snap: average the junction
        mid = ((loop[-1][0] + s[0][0]) / 2, (loop[-1][1] + s[0][1]) / 2)
        loop[-1] = mid
        loop.extend(s[1:])
    assert math.dist(loop[0], loop[-1]) < tol, math.dist(loop[0], loop[-1])
    loop[-1] = loop[0]
    return loop

# ---------------------------------------------------------------- walk (band)
OUTER_RECTS = [
    [1038.6, 300.4, 1633.3, 300.4], [1633.3, 300.4, 1633.3, 1483.0], [1550.9, 1479.4, 1634.1, 1563.2],
    [1309.1, 1562.8, 1552.7, 1562.9], [959.9, 1410.5, 1309.1, 1562.9], [861.5, 1298.7, 960.5, 1410.3],
    [861.3, 825.3, 861.3, 1303.0], [861.3, 699.5, 1000.6, 825.3], [1000.6, 699.7, 1038.6, 699.7],
    [1038.6, 300.4, 1038.6, 699.7]]
INNER_RECTS = [
    [1121.0, 354.4, 1550.3, 354.4], [1550.5, 354.4, 1579.4, 386.3], [1579.3, 385.9, 1579.3, 1482.5],
    [1551.9, 1480.9, 1579.7, 1508.9], [1328.0, 1508.8, 1552.7, 1508.8], [965.7, 1356.7, 1328.0, 1508.8],
    [915.3, 1300.1, 965.7, 1356.8], [915.3, 832.3, 915.3, 1302.5], [915.3, 753.5, 1004.6, 832.3],
    [1004.6, 753.7, 1038.6, 753.7], [1038.7, 698.1, 1093.0, 753.5], [1092.6, 383.9, 1092.6, 699.8],
    [1092.0, 354.3, 1121.0, 386.4]]

outer_sheet = chain([path_points(get(r)) for r in OUTER_RECTS])
inner_sheet = chain([path_points(get(r)) for r in INNER_RECTS])

JOINT_RECTS = []
used = set(map(tuple, OUTER_RECTS + INNER_RECTS))
for r in HEAVY:
    x0, y0, x1, y1 = r['rect']
    if x1 - x0 > 2000: continue                       # sheet border
    if len(r['items']) != 1 or r['items'][0][0] != 'l': continue
    L = math.dist(r['items'][0][1], r['items'][0][2])
    if L < 1: continue
    if any(near(r['rect'], u, 1.0) for u in used): continue
    if abs(y0 - 597.4) < 0.5 and abs(y1 - 597.4) < 0.5: continue    # pad / lawn edge
    JOINT_RECTS.append(r)

PAD_LINE_Y = 597.42
M1 = path_points(get([1196.7, 1185.4, 1579.4, 1425.6]), 64)   # lawn side of the mow strip
M2 = path_points(get([1208.7, 1198.9, 1579.4, 1431.6]), 64)   # nook side

def to_world(pts):
    return [W(p) for p in pts]

OUTER = Polygon(to_world(outer_sheet)).buffer(0)
INNER = Polygon(to_world(inner_sheet)).buffer(0)
BAND = OUTER.difference(INNER)

ypad = W((0, PAD_LINE_Y))[1]
BIG = 200.0
PAD = INNER.intersection(box(-BIG, ypad, BIG, BIG))
REST = INNER.intersection(box(-BIG, -BIG, BIG, ypad))

def nook_side(curve):
    a = curve if curve[0][0] > curve[-1][0] else curve[::-1]      # right -> left
    right, left = a[0], a[-1]
    poly = a + [(left[0] - 46.7, left[1] + 174.4), (1700, 1700), (1700, right[1])]
    return Polygon(to_world(poly)).buffer(0)

N1 = nook_side(M1); N2 = nook_side(M2)
NOOK = REST.intersection(N2)
MOW = REST.intersection(N1).difference(N2)
LAWN = REST.difference(N1)

# control-joint cut lines (world)
JOINTS = [LineString(to_world([r['items'][0][1], r['items'][0][2]])) for r in JOINT_RECTS]

# ---------------------------------------------------------------- lounge (herringbone + border)
LOUNGE_OUT = Polygon(to_world([(1038.60, 300.42), (641.52, 300.42), (641.52, 529.92), (785.52, 529.92),
                               (785.52, 646.92), (1038.60, 646.92)]))
LOUNGE_IN = Polygon(to_world([(1030.14, 308.88), (649.98, 308.88), (649.98, 521.46), (793.98, 521.46),
                              (793.98, 638.46), (1030.14, 638.46)]))
LOUNGE_BORDER = LOUNGE_OUT.difference(LOUNGE_IN)

# ---------------------------------------------------------------- objects
def rect_w(x0, y0, x1, y1):
    a = W((x0, y0)); b = W((x1, y1))
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))

PAVILION = rect_w(1133.10, 374.22, 1538.28, 576.72)
HOT_TUB = rect_w(666.72, 326.52, 761.22, 421.02)
COUNTER_BACK = rect_w(1511.28, 374.22, 1538.28, 576.72)      # 2' deep, 15' long, sink leg
COUNTER_TOP = rect_w(1416.78, 374.22, 1538.28, 401.22)       # grill leg (north)
COUNTER_BOT = rect_w(1416.78, 549.72, 1538.28, 576.72)       # fridge leg (south)
GRILL = rect_w(1420.6, 378.5, 1479.4, 414.5)
SINK = rect_w(1513.4, 464.0, 1537.3, 487.8)
FRIDGE = rect_w(1428.3, 552.6, 1472.2, 574.7)
SOFA_N = rect_w(877.3, 311.2, 972.9, 351.7)                  # back to north, faces south
SOFA_E = rect_w(987.5, 344.7, 1028.0, 440.5)                 # back to east, faces west
FIRE_RECT = rect_w(904.1, 379.1, 958.1, 406.1)
FIRE_ROUND_C = W((1218.0, 476.1)); ROUND_D = ft(3.76)
DINING_C = W((1440.3, 1387.0))

def chairs_in(bb, min_pts=30):
    """cluster 0.54-weight furniture paths inside bb -> list of (center_world, bbox_ft)"""
    rs = [r for r in _D if _key(r) == ('s', 0.2, 0.54)]
    rs = [r for r in rs if r['rect'][0] >= bb[0] - 1 and r['rect'][2] <= bb[2] + 1 and r['rect'][1] >= bb[1] - 1 and r['rect'][3] <= bb[3] + 1]
    cl = []
    for r in rs:
        R = r['rect']
        for c in cl:
            b = c
            if R[0] <= b[2] + 4 and R[2] >= b[0] - 4 and R[1] <= b[3] + 4 and R[3] >= b[1] - 4:
                c[0] = min(c[0], R[0]); c[1] = min(c[1], R[1]); c[2] = max(c[2], R[2]); c[3] = max(c[3], R[3]); break
        else:
            cl.append(list(R))
    out = []
    for c in cl:
        out.append((W(((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)), ((c[2] - c[0]) / PT_PER_FT, (c[3] - c[1]) / PT_PER_FT)))
    return out

LOUNGE_CHAIRS = chairs_in([1147.9, 395.5, 1288.3, 547.4])
DINING_CHAIRS = chairs_in([1382.8, 1337.1, 1497.8, 1447.7])

if __name__ == '__main__':
    def a(p): return p.area / (M_PER_FT ** 2)
    print('outer loop pts', len(outer_sheet), 'inner loop pts', len(inner_sheet))
    print('areas (sq ft): band %.0f  pad %.0f  lawn %.0f  mow %.0f  nook %.0f  lounge %.0f' % (a(BAND), a(PAD), a(LAWN), a(MOW), a(NOOK), a(LOUNGE_OUT)))
    print('joints', len(JOINTS))
    print('pavilion ft', (PAVILION[2]-PAVILION[0]) / M_PER_FT, (PAVILION[3]-PAVILION[1]) / M_PER_FT)
    print('lounge chairs', [(round(c[0][0], 2), round(c[0][1], 2), [round(v, 2) for v in c[1]]) for c in LOUNGE_CHAIRS])
    print('dining chairs', [(round(c[0][0], 2), round(c[0][1], 2), [round(v, 2) for v in c[1]]) for c in DINING_CHAIRS])
    print('fire round', FIRE_ROUND_C, 'dining', DINING_C)
    print('extent', OUTER.union(LOUNGE_OUT).bounds)
    print('mow width check (ft):', MOW.area / M_PER_FT**2 / (LineString(to_world(M1)).length / M_PER_FT))
