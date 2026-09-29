"""Sprinkler head layout for the plan's lawn: head-to-head MP Rotator coverage, auto arcs, catch-can simulation.
Units: plan metres (x east, y north). Flows in US GPM, radii reported in feet."""
import json, math, random
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely import contains_xy

FT = 0.3048
try:
    LAWN = Polygon(json.load(open('design/lawn.json'))).buffer(0)
except FileNotFoundError:                                   # fall back to the plan geometry itself
    import sys as _sys; _sys.path.insert(0, '../scripts')
    import plan as _P
    LAWN = _P.LAWN if _P.LAWN.geom_type == 'Polygon' else max(_P.LAWN.geoms, key=lambda g: g.area)
PR_IN_HR = 0.42                      # MP Rotator matched precipitation (square spacing), slightly conservative
MODELS = [('MP1000', 8, 15), ('MP2000', 13, 21), ('MP3000', 22, 30)]
INSET = 0.03                         # modelled on the edge; installed 2-4" inside the concrete

def model_for(R_ft):
    for name, lo, hi in MODELS:
        if R_ft <= hi + 1e-6: return name, max(lo, R_ft)
    return MODELS[-1][0], MODELS[-1][2]

def gpm(R_m, arc):
    R_ft = R_m / FT
    return PR_IN_HR * R_ft * R_ft * (arc / 360.0) / 96.25

# ------------------------------------------------------------------ arcs
_DIRS = np.radians(np.arange(0, 360, 2.0))
def ray_fraction(x, y, R, tol=0.0):
    rs = np.arange(0.25, R + 1e-9, 0.15)
    X = x + np.outer(np.cos(_DIRS), rs); Y = y + np.outer(np.sin(_DIRS), rs)
    ins = contains_xy(LAWN.buffer(tol), X, Y)
    return ins.mean(1)

def auto_arc(x, y, R, tau=0.8):
    """Largest contiguous run of directions whose ray stays mostly on the lawn -> (start_deg, arc_deg), snapped to MP arc ranges."""
    f = ray_fraction(x, y, R)
    ok = f >= tau
    if ok.all():
        return 0.0, 360.0
    if not ok.any():
        return 0.0, 0.0
    n = len(ok); k0 = int(np.argmin(ok))           # start scanning just after a failing direction
    best = (0, 0); run = 0; start = None
    for i in range(1, n + 1):
        j = (k0 + i) % n
        if ok[j]:
            if run == 0: start = j
            run += 1
            if run > best[0]: best = (run, start)
        else:
            run = 0
    run, start = best
    a0, arc = start * 2.0 - 1.0, run * 2.0 + 2.0          # grow by half a step each side
    # MP arc ranges: 90-210, 210-270 (fixed nozzles), 360; below 90 -> 90 (small overspray), 270-360 -> 270 or 360
    mid = a0 + arc / 2
    if arc < 90: arc = 90.0
    elif 270 < arc < 330: arc = 270.0
    elif arc >= 330: return 0.0, 360.0
    return (mid - arc / 2) % 360, arc


def _ang(v): return math.degrees(math.atan2(v[1], v[0]))
def edge_arc(sv):
    """Arc for a head on the lawn edge at arc-length sv: the narrowest interior sector over several look-ahead chords
    (tangent-like for gentle curves, chord-like for rounded corners)."""
    ring = LAWN.exterior; L = ring.length
    p = np.array(ring.interpolate(sv % L).coords[0])
    lo, hi = -1e9, 1e9
    ref = None
    for lam in (0.2, 0.6, 1.2, 2.0, 3.0):
        a = np.array(ring.interpolate((sv + lam) % L).coords[0]) - p
        b = np.array(ring.interpolate((sv - lam) % L).coords[0]) - p
        ta, tb = _ang(a), _ang(b)
        # interior sector: ccw from ta to tb, or ccw from tb to ta; pick the one whose middle points into the lawn
        span1 = (tb - ta) % 360; mid1 = math.radians(ta + span1 / 2)
        q1 = p + 0.6 * np.array([math.cos(mid1), math.sin(mid1)])
        if LAWN.contains(Point(*q1)): start, span = ta, span1
        else: start, span = tb, (ta - tb) % 360
        mid = start + span / 2
        if ref is None: ref = mid
        d = ((mid - ref + 180) % 360) - 180          # express relative to the first sector's middle
        lo = max(lo, d - span / 2); hi = min(hi, d + span / 2)
    arc = max(0.0, hi - lo)
    a0 = (ref + lo) % 360
    mid = a0 + arc / 2
    if arc < 90: arc = 90.0
    elif 270 < arc < 330: arc = 270.0
    elif arc >= 330: return 0.0, 360.0
    return (mid - arc / 2) % 360, arc

# ------------------------------------------------------------------ simulation
_cell = 0.2
_bx0, _by0, _bx1, _by1 = LAWN.bounds
_xs = np.arange(_bx0 - 3.0, _bx1 + 3.0, _cell) + _cell / 2
_ys = np.arange(_by0 - 3.0, _by1 + 3.0, _cell) + _cell / 2
GX, GY = np.meshgrid(_xs, _ys)
INSIDE = contains_xy(LAWN, GX, GY)
CORE = contains_xy(LAWN.buffer(-0.12), GX, GY)          # DU is judged on the lawn minus a 5" edge band (edge cells are a modelling artifact)

def head_field(h):
    dx, dy = GX - h['x'], GY - h['y']; r = np.hypot(dx, dy)
    p = np.clip(1.0 - r / h['R'], 0.0, None)            # triangular radial profile (conservative for rotating streams)
    if h['arc'] < 360:
        ang = np.degrees(np.arctan2(dy, dx)) % 360
        p = np.where(((ang - h['a0']) % 360) <= h['arc'], p, 0.0)
    return p

def evaluate(heads):
    W = np.zeros_like(GX)
    for h in heads: W += head_field(h)
    lawn = W[CORE]
    mean = lawn.mean()
    srt = np.sort(lawn)
    du = srt[: len(srt) // 4].mean() / mean
    sc = mean / max(1e-9, srt[: max(1, len(srt) // 20)].mean())      # scheduling coefficient (driest 5%)
    over = W[~INSIDE].sum() / W.sum()
    dry = (lawn < 0.35 * mean).mean()
    return dict(du=du, sc=sc, over=over, dry=dry, W=W)

# ------------------------------------------------------------------ layout generation
def boundary_corners(turn_deg=35.0):
    s = LAWN.simplify(0.45)
    pts = np.array(s.exterior.coords)[:-1]
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1, v2 = b - a, c - b
        t = math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1 @ v2))
        if abs(t) >= turn_deg:
            q = LAWN.exterior.interpolate(LAWN.exterior.project(Point(b)))
            out.append((LAWN.exterior.project(q), t))
    return sorted(out)

def inset_point(s):
    """Point at arc-length s on the lawn edge, moved INSET into the lawn along the local inward normal."""
    ring = LAWN.exterior; L = ring.length
    p = np.array(ring.interpolate(s % L).coords[0]); q = np.array(ring.interpolate((s + 0.05) % L).coords[0])
    t = q - p; t /= np.linalg.norm(t) + 1e-12
    n = np.array([-t[1], t[0]])
    if not LAWN.contains(Point(*(p + n * 0.3))): n = -n
    c = p + n * INSET
    # at convex corners push along the bisector a bit more so both edges are ~INSET away
    for _ in range(6):
        if LAWN.exterior.distance(Point(*c)) >= INSET * 0.9 and LAWN.contains(Point(*c)): break
        c = c + n * 0.03
    return c

def make_layout(S, grid_off=(0.0, 0.0), tri=False, edge_ratio=1.0):
    ring = LAWN.exterior; L = ring.length
    corners = boundary_corners()
    cs = [c[0] for c in corners]
    heads = []
    for i, s0 in enumerate(cs):
        s1 = cs[(i + 1) % len(cs)] + (L if i == len(cs) - 1 else 0)
        seg = s1 - s0
        n = max(1, math.ceil(seg / (S * edge_ratio) - 1e-6))
        for k in range(n):
            heads.append(dict(kind='edge', s=(s0 + seg * k / n) % L))
    # interior grid
    x0, y0, x1, y1 = LAWN.bounds
    xs = np.arange(x0 + grid_off[0], x1, S)
    rows = np.arange(y0 + grid_off[1], y1, S * (math.sqrt(3) / 2 if tri else 1.0))
    for j, y in enumerate(rows):
        for x in xs + ((S / 2) if (tri and j % 2) else 0.0):
            if LAWN.contains(Point(x, y)) and LAWN.exterior.distance(Point(x, y)) >= 0.55 * S:
                heads.append(dict(kind='int', x=float(x), y=float(y)))
    return heads

def realize(heads, R):
    out = []
    for h in heads:
        if h['kind'] == 'edge':
            x, y = inset_point(h['s'])
        else:
            x, y = h['x'], h['y']
        Rh = h.get('R', R)
        a0, arc = edge_arc(h['s']) if h['kind'] == 'edge' else auto_arc(x, y, Rh)
        if arc <= 0: continue
        out.append(dict(kind=h['kind'], s=h.get('s'), x=float(x), y=float(y), R=Rh, a0=a0, arc=arc))
    return out

def score(ev, nheads, w_over=1.2, w_dry=3.0, w_n=0.0025):
    return ev['du'] - w_over * ev['over'] - w_dry * ev['dry'] - w_n * nheads

def optimize(heads, R, iters=900, seed=1, rmin=None, rmax=None):
    rng = random.Random(seed)
    cur = [dict(h) for h in heads]
    real = realize(cur, R); ev = evaluate(real); best = score(ev, len(real))
    L = LAWN.exterior.length
    for it in range(iters):
        i = rng.randrange(len(cur)); h = dict(cur[i]); step = 0.6 * (1 - it / iters) + 0.08
        r = rng.random()
        if r < 0.25 and rmin is not None:
            h['R'] = float(np.clip(h.get('R', R) + rng.uniform(-0.5, 0.5), rmin, rmax))
        elif h['kind'] == 'edge':
            h['s'] = (h['s'] + rng.uniform(-step, step)) % L
        else:
            nx, ny = h['x'] + rng.uniform(-step, step), h['y'] + rng.uniform(-step, step)
            if not LAWN.contains(Point(nx, ny)) or LAWN.exterior.distance(Point(nx, ny)) < 0.5: continue
            h['x'], h['y'] = nx, ny
        trial = cur[:i] + [h] + cur[i + 1:]
        rt = realize(trial, R); et = evaluate(rt); sc_ = score(et, len(rt))
        if sc_ > best:
            cur, best, ev, real = trial, sc_, et, rt
    return cur, real, ev


def edge_heads(S):
    ring = LAWN.exterior; L = ring.length
    cs = [c[0] for c in boundary_corners()]
    out = []
    for i, s0 in enumerate(cs):
        s1 = cs[(i + 1) % len(cs)] + (L if i == len(cs) - 1 else 0)
        seg = s1 - s0
        n = max(1, math.ceil(seg / S - 0.08))
        for k in range(n):
            out.append(dict(kind='edge', s=(s0 + seg * k / n) % L))
    return out

def greedy_interior(heads, S, R, kmax=6, target=0.87):
    cand = []
    x0, y0, x1, y1 = LAWN.bounds
    for x in np.arange(x0 + 0.5, x1, 0.5):
        for y in np.arange(y0 + 0.5, y1, 0.5):
            pt = Point(x, y)
            if LAWN.contains(pt) and LAWN.exterior.distance(pt) >= 0.45 * S: cand.append((float(x), float(y)))
    cur = list(heads)
    real = realize(cur, R); ev = evaluate(real); best = score(ev, len(real))
    for k in range(kmax):
        if ev['du'] >= target: break
        pick = None
        for (x, y) in cand:
            if any(h['kind'] == 'int' and math.hypot(h['x'] - x, h['y'] - y) < 0.6 * S for h in cur): continue
            trial = cur + [dict(kind='int', x=x, y=y)]
            rt = realize(trial, R); et = evaluate(rt); sc_ = score(et, len(rt))
            if pick is None or sc_ > pick[0]: pick = (sc_, trial, rt, et)
        if pick is None or pick[0] <= best: break
        best, cur, real, ev = pick
    return cur, real, ev

if __name__ == '__main__':
    import sys
    print('lawn %.1f m2 = %.0f sq ft' % (LAWN.area, LAWN.area / FT ** 2))
    results = []
    for S_ft in [float(a) for a in sys.argv[1:]] or (20, 22, 24):
        S = S_ft * FT; R = S * 1.0
        hs = edge_heads(S)
        hs, real, ev = greedy_interior(hs, S, R)
        tot = sum(gpm(h['R'], h['arc']) for h in real)
        print('S=%g ft: heads %d (edge %d, interior %d)  DU %.3f  SC %.2f  overspray %.1f%%  dry %.2f%%  total %.1f GPM' % (
            S_ft, len(real), sum(h['kind'] == 'edge' for h in real), sum(h['kind'] == 'int' for h in real), ev['du'], ev['sc'], 100 * ev['over'], 100 * ev['dry'], tot))
        hs2, real2, ev2 = optimize(hs, R, iters=1500, seed=int(S_ft), rmin=R * 0.85, rmax=min(R * 1.15, 30 * FT))
        tot2 = sum(gpm(h['R'], h['arc']) for h in real2)
        print('      optimised: DU %.3f  SC %.2f  overspray %.1f%%  dry %.2f%%  total %.1f GPM' % (ev2['du'], ev2['sc'], 100 * ev2['over'], 100 * ev2['dry'], tot2))
        results.append(dict(S_ft=S_ft, heads=hs2, tri=False, off=[0, 0]))
    json.dump(results, open('irr/candidates.json', 'w'))
