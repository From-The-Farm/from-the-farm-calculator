"""Space-colonisation tree generator (numpy)."""
import math, random
import numpy as np

def colonize(seed, H=10.0, R=4.0, trunk_h=2.4, n_attr=1400, step=0.28, di=2.6, dk=0.55, shape='round'):
    rs = np.random.RandomState(seed)
    cz = trunk_h + (H - trunk_h) * 0.52
    rz = (H - trunk_h) * 0.52
    pts = []
    while len(pts) < n_attr:
        p = rs.uniform(-1, 1, size=(4000, 3))
        r2 = (p ** 2).sum(1)
        p = p[r2 < 1.0]
        if shape == 'round':
            # denser toward the shell
            keep = rs.uniform(0, 1, size=len(p)) < (0.35 + 0.65 * np.sqrt((p ** 2).sum(1)))
            p = p[keep]
        pts.extend(list(p))
    A = np.array(pts[:n_attr]) * np.array([R, R, rz]) + np.array([0, 0, cz])
    # slight asymmetry
    A[:, 0] *= rs.uniform(0.85, 1.15); A[:, 1] *= rs.uniform(0.85, 1.15)
    nodes = [np.array([0.0, 0.0, -0.1])]
    parent = [-1]
    lean = rs.normal(0, 0.03, size=3); lean[2] = 1.0; lean /= np.linalg.norm(lean)
    while nodes[-1][2] < trunk_h:
        nodes.append(nodes[-1] + lean * step); parent.append(len(nodes) - 2)
    alive = np.ones(len(A), bool)
    for it in range(260):
        N = np.array(nodes)
        Aa = A[alive]
        if len(Aa) == 0: break
        # nearest node for each attraction point (chunked)
        d2 = ((Aa[:, None, :] - N[None, :, :]) ** 2).sum(-1)
        nn = d2.argmin(1); dmin = np.sqrt(d2[np.arange(len(Aa)), nn])
        infl = dmin < di
        if not infl.any():
            # grow the leader upward a bit to reach points
            nodes.append(nodes[-1] + np.array([0, 0, step])); parent.append(len(nodes) - 2)
            continue
        grow = {}
        for ai in np.where(infl)[0]:
            k = nn[ai]
            v = Aa[ai] - N[k]; v /= (np.linalg.norm(v) + 1e-9)
            grow.setdefault(k, []).append(v)
        added = 0
        for k, vs in grow.items():
            d = np.sum(vs, 0)
            d = d / (np.linalg.norm(d) + 1e-9)
            d = d + np.array([0, 0, 0.12]) + rs.normal(0, 0.08, 3)
            d /= np.linalg.norm(d)
            newp = N[k] + d * step
            nodes.append(newp); parent.append(int(k)); added += 1
        N = np.array(nodes)
        d2 = ((A[:, None, :] - N[None, :, :]) ** 2).sum(-1)
        alive &= np.sqrt(d2.min(1)) > dk
        if added == 0: break
    N = np.array(nodes); par = np.array(parent)
    # pipe-model radii
    nchild = np.zeros(len(N), int)
    for p in par[1:]: nchild[p] += 1
    r = np.full(len(N), 0.010)
    order = np.argsort(-np.arange(len(N)))       # children always have higher index than parents
    acc = np.zeros(len(N))
    for i in order:
        if nchild[i] == 0: acc[i] = 0.011 ** 2.15
        r[i] = acc[i] ** (1 / 2.15)
        if par[i] >= 0: acc[par[i]] += acc[i]
    r = np.maximum(r, 0.008)
    return N, par, r

def tree_mesh(N, par, r, min_r=0.007, sides_fn=None):
    verts = []; faces = []
    for i in range(1, len(N)):
        p = par[i]
        if p < 0: continue
        ra, rb = r[p], r[i]
        if rb < min_r and ra < min_r: continue
        a = N[p]; b = N[i]
        d = b - a; L = np.linalg.norm(d)
        if L < 1e-6: continue
        d /= L
        t = np.cross(d, [0, 0, 1.0] if abs(d[2]) < 0.9 else [1.0, 0, 0]); t /= np.linalg.norm(t)
        u = np.cross(d, t)
        s = 8 if ra > 0.08 else (6 if ra > 0.03 else 4)
        base = len(verts)
        # extend slightly into the parent to hide seams
        a2 = a - d * min(ra, 0.05)
        for (cen, rr) in ((a2, ra), (b, rb)):
            for k in range(s):
                ang = 2 * math.pi * k / s
                verts.append(tuple(cen + (t * math.cos(ang) + u * math.sin(ang)) * rr))
        for k in range(s):
            k2 = (k + 1) % s
            faces.append((base + k, base + k2, base + s + k2, base + s + k))
    return verts, faces

def leaf_points(N, par, r, seed, per=5, max_r=0.03, jitter=0.28):
    rs = np.random.RandomState(seed + 7)
    idx = np.where(r < max_r)[0]
    P = np.repeat(N[idx], per, axis=0) + rs.normal(0, jitter, size=(len(idx) * per, 3)) * np.array([1, 1, 0.8])
    return P
