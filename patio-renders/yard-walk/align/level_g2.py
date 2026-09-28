"""Levelled metric frame for the g2 model: x_l = R (s x_sfm - c0); z up, ground at z ~ 0."""
import numpy as np, pycolmap, json
S = 3.19
r = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
C, UP, N = [], [], []
for im in r.images.values():
    M = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
    C.append(-M[:, :3].T @ M[:, 3] * S); UP.append(-M[1, :3]); N.append(im.name)
C = np.array(C); up0 = np.mean(UP, 0); up0 /= np.linalg.norm(up0)
ex = np.cross([0, 0, 1.0] if abs(up0[2]) < 0.9 else [1.0, 0, 0], up0); ex /= np.linalg.norm(ex); ey = np.cross(up0, ex)
R0 = np.stack([ex, ey, up0]); L = (C - C.mean(0)) @ R0.T
A = np.c_[L[:, 0], L[:, 1], np.ones(len(L))]; w = np.ones(len(L))
for it in range(12):
    sol, *_ = np.linalg.lstsq(A * w[:, None], L[:, 2] * w, rcond=None)
    res = L[:, 2] - A @ sol; sc = 1.4826 * np.median(np.abs(res)) + 1e-9
    w = 1 / np.maximum(1, np.abs(res) / (2 * sc))
n = np.array([-sol[0], -sol[1], 1.0]); n /= np.linalg.norm(n)
n_w = R0.T @ n                                  # plane normal in (scaled) SfM coords
ex = np.cross([0, 0, 1.0] if abs(n_w[2]) < 0.9 else [1.0, 0, 0], n_w); ex /= np.linalg.norm(ex); ey = np.cross(n_w, ex)
R = np.stack([ex, ey, n_w])
cam_plane_pt = C.mean(0) + R0.T @ np.array([0, 0, sol[2]])
c0 = cam_plane_pt - 1.45 * n_w                  # ground: 1.45 m below the typical phone height
Lc = (C - c0) @ R.T
print('residual MAD (m) %.3f' % sc, 'tilt from mean camera-up (deg) %.2f' % np.degrees(np.arccos(n_w @ up0)))
print('camera z percentiles', np.percentile(Lc[:, 2], [2, 25, 50, 75, 98]).round(2))
lo, hi = Lc[:, :2].min(0) - 8, Lc[:, :2].max(0) + 8
json.dump(dict(R=R.tolist(), c0=(c0 / S).tolist(), s=S, box=[float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])]), open('align/level_g2.json', 'w'))
# note: render_top applies x_l = s * R (x - c0) with c0 in SfM units
np.savez('align/cams_g2.npz', C=Lc, names=np.array(N))
print('box', lo.round(1), hi.round(1))
