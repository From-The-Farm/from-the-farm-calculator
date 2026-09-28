import sys, json, numpy as np, pycolmap
lev = json.load(open('align/level_g2.json')); S = lev['s']; R = np.array(lev['R']); c0 = np.array(lev['c0'])
r = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
name = sys.argv[1]; pts = [tuple(map(float, a.split(','))) for a in sys.argv[2:]]
im = [i for i in r.images.values() if i.name == name][0]
kp = []
for p2 in im.points2D:
    if p2.has_point3D():
        P = r.points3D[p2.point3D_id]
        kp.append((p2.xy[0], p2.xy[1], *((S * P.xyz - S * c0) @ R.T), P.error, P.track.length()))
kp = np.array(kp)
print(name, 'keypoints with 3D', len(kp))
for (u, v) in pts:
    d = np.hypot(kp[:, 0] - u, kp[:, 1] - v); o = np.argsort(d)[:4]
    print('query (%d,%d):' % (u, v))
    for i in o:
        print('    px (%6.1f,%6.1f) d=%5.1f  3D (%6.2f,%6.2f,%5.2f) err %.2f track %d' % (kp[i, 0], kp[i, 1], d[i], kp[i, 2], kp[i, 3], kp[i, 4], kp[i, 5], kp[i, 6]))
