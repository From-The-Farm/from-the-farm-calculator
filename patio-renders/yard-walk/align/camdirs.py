import numpy as np, pycolmap, json, sys
lev = json.load(open('align/level_g2.json')); S = lev['s']
R = np.array(lev['R']); c0 = np.array(lev['c0'])
r = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
out = {}
for im in r.images.values():
    M = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
    C = -M[:, :3].T @ M[:, 3]
    f = M[2, :3]                       # camera +z (forward) in world
    Cl = R @ (S * C - S * c0)
    fl = R @ f
    fid = int(im.name[1:5])
    out[fid] = (Cl, fl)
np.save('align/camdirs.npy', {k: (v[0].tolist(), v[1].tolist()) for k, v in out.items()}, allow_pickle=True)
for k in [int(a) for a in sys.argv[1:]]:
    if k in out:
        C, f = out[k]
        yaw = np.degrees(np.arctan2(f[1], f[0]))
        print('%4d  C=(%6.2f,%6.2f,%5.2f)  fwd=(%5.2f,%5.2f,%5.2f) yaw=%6.1f pitch=%5.1f' % (k, *C, *f, yaw, np.degrees(np.arcsin(f[2]))))
    else:
        print(k, 'not registered')
