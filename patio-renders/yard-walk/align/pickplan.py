"""Median 3D position (plan metres) of well-tracked SfM points inside an image box. python3 align/pickplan.py FRAME x0,y0,x1,y1 [...]"""
import sys, numpy as np, pycolmap
sys.path.insert(0, 'align'); import frames as F
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
name = sys.argv[1]
im = [i for i in rec.images.values() if i.name == name][0]
kp = []
for p2 in im.points2D:
    if p2.has_point3D():
        P = rec.points3D[p2.point3D_id]
        if P.error < 2.0 and P.track.length() >= 3: kp.append((p2.xy[0], p2.xy[1], *P.xyz))
kp = np.array(kp)
for b in sys.argv[2:]:
    x0, y0, x1, y1 = map(float, b.split(','))
    m = (kp[:, 0] >= x0) & (kp[:, 0] <= x1) & (kp[:, 1] >= y0) & (kp[:, 1] <= y1)
    if m.sum() == 0: print(b, 'no points'); continue
    Pp = F.sfm2plan(kp[m, 2:5])
    med = np.median(Pp, 0)
    print('%s box %s: n=%d plan median (%.2f, %.2f, %.2f)  xy spread p10-p90 x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
        name, b, m.sum(), *med, *np.percentile(Pp[:, 0], [10, 90]), *np.percentile(Pp[:, 1], [10, 90]), *np.percentile(Pp[:, 2], [10, 90])))
