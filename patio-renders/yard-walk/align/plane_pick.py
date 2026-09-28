"""Fit a plane to splat-depth points in an image polygon, then intersect rays of picked pixels with it.
python3 align/plane_pick.py FRAME.jpg 'x1,y1;x2,y2;...' u,v u,v ..."""
import sys, json, numpy as np, pycolmap
from PIL import Image, ImageDraw
import os
VERT = os.environ.get('VERT') == '1'
name = sys.argv[1]; poly = [tuple(map(float, p.split(','))) for p in sys.argv[2].split(';')]
pts = [tuple(map(float, a.split(','))) for a in sys.argv[3:]]
S = 3.19
lev = json.load(open('align/level_g2m.json')); RL = np.array(lev['R']); c0 = np.array(lev['c0'])
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
im = [i for i in rec.images.values() if i.name == name][0]
c = rec.cameras[im.camera_id]; fx, fy, cx, cy = c.params[:4]; W, H = c.width, c.height
Rt = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
R, t = Rt[:, :3], Rt[:, 3] * S
D = np.load('align/depth_%s.npy' % name[:-4])
mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(poly, fill=255); mask = np.array(mask) > 0
vv, uu = np.nonzero(mask)
d = D[vv, uu]
Xc = np.stack([(uu - cx) / fx * d, (vv - cy) / fy * d, d], 1)
Lw = ((Xc - t) @ R) @ RL.T - (RL @ c0)       # levelled
rng = np.random.default_rng(0); best = None
for it in range(400):
    i = rng.choice(len(Lw), 3, replace=False); p = Lw[i]
    n = np.cross(p[1] - p[0], p[2] - p[0]); nn = np.linalg.norm(n)
    if nn < 1e-9: continue
    n /= nn
    if VERT and abs(n[2]) > 0.34: continue
    dist = np.abs((Lw - p[0]) @ n); inl = dist < 0.02
    if best is None or inl.sum() > best[0]: best = (inl.sum(), n, p[0])
inl = np.abs((Lw - best[2]) @ best[1]) < 0.02
q0 = Lw[inl].mean(0); U, Sv, Vt = np.linalg.svd(Lw[inl] - q0); n = Vt[2]
print('plane: inliers %d/%d normal %s (tilt from vertical %.1f deg)' % (inl.sum(), len(Lw), n.round(3), np.degrees(np.arcsin(abs(n[2])))))
C = RL @ (R.T @ (-t) - c0)
out = []
for (u, v) in pts:
    ray_c = np.array([(u - cx) / fx, (v - cy) / fy, 1.0])
    ray = RL @ (R.T @ ray_c)
    s = ((q0 - C) @ n) / (ray @ n)
    P = C + s * ray; out.append(P)
    print('px (%6.1f,%6.1f) -> (%6.3f,%6.3f,%6.3f)' % (u, v, *P))
out = np.array(out)
if len(out) > 1:
    dd = np.linalg.norm(np.diff(out, axis=0), axis=1)
    print('consecutive distances:', dd.round(3), 'total %.3f' % np.linalg.norm(out[-1] - out[0]))
