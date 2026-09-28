import json, numpy as np, pycolmap
lev = json.load(open('align/level_g2.json')); S = lev['s']; R = np.array(lev['R']); c0 = np.array(lev['c0'])
r = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
X = np.array([p.xyz for p in r.points3D.values()]); err = np.array([p.error for p in r.points3D.values()]); tl = np.array([p.track.length() for p in r.points3D.values()])
L = (S * X - S * c0) @ R.T
L = L[(err < 1.5) & (tl >= 3)]
cams = np.load('align/camdirs.npy', allow_pickle=True).item()
from scipy.spatial import cKDTree
tree = cKDTree(L[:, :2])
rows = []
for k in sorted(cams):
    C = np.array(cams[k][0])
    idx = tree.query_ball_point(C[:2], 1.2)
    if len(idx) < 15: continue
    z = L[idx, 2]; z = z[z < C[2] - 0.3]
    if len(z) < 15: continue
    g = np.percentile(z, 30)
    rows.append((k, C[2] - g, len(z)))
rows = np.array(rows)
for a in range(0, 601, 30):
    m = (rows[:, 0] >= a) & (rows[:, 0] < a + 30)
    if m.sum(): print('frames %3d-%3d  n=%2d  cam height above local ground: median %.2f  (p25 %.2f p75 %.2f)' % (a, a + 29, m.sum(), np.median(rows[m, 1]), np.percentile(rows[m, 1], 25), np.percentile(rows[m, 1], 75)))
print('overall median %.2f' % np.median(rows[:, 1]))
