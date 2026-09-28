"""True orthophoto of the site from the video frames: project a surface-height grid into the registered
undistorted frames and take a robust blend of the best (close, steep) views. Levelled metric frame (current scale)."""
import os, sys, json, math, time
import numpy as np, torch, pycolmap
from PIL import Image
t0 = time.time()
S = 3.19
lev = json.load(open('align/level_g2m.json')); RL = np.array(lev['R']); c0 = np.array(lev['c0'])
box = [float(v) for v in sys.argv[1:5]] if len(sys.argv) > 4 else [-20, -20, 16, 24]
cell = float(sys.argv[5]) if len(sys.argv) > 5 else 0.05
out = sys.argv[6] if len(sys.argv) > 6 else 'align/ortho.png'
PLAN = os.environ.get('PLAN') == '1'
if PLAN:
    sys.path.insert(0, 'align'); import frames as FR
ck = 'real/train3/ckpt7000.pt'
# ---- surface model from splat centres
st = torch.load(ck, map_location='cpu')
X = st['means'].numpy().astype(np.float64); op = torch.sigmoid(st['opac']).numpy(); sc = np.exp(st['scales'].numpy()).max(1)
L = (X - c0) @ RL.T
m = (op > 0.4) & (sc < 0.12) & (L[:, 2] > -2.5) & (L[:, 2] < 2.0)
L = L[m]
gc = 0.25
box_out = list(box)
if PLAN:
    cr = FR.plan2lev(np.array([[box[0], box[1]], [box[2], box[1]], [box[0], box[3]], [box[2], box[3]]]))
    box = [cr[:, 0].min() - 1, cr[:, 1].min() - 1, cr[:, 0].max() + 1, cr[:, 1].max() + 1]
x0, y0, x1, y1 = box
gx, gy = int(math.ceil((x1 - x0) / gc)), int(math.ceil((y1 - y0) / gc))
ix = np.clip(((L[:, 0] - x0) / gc).astype(int), 0, gx - 1); iy = np.clip(((L[:, 1] - y0) / gc).astype(int), 0, gy - 1)
inb = (L[:, 0] >= x0) & (L[:, 0] < x1) & (L[:, 1] >= y0) & (L[:, 1] < y1)
key = (iy * gx + ix)[inb]; z = L[inb, 2]
o = np.lexsort((z, key)); ks, zs = key[o], z[o]
last = np.r_[np.nonzero(np.diff(ks))[0], len(ks) - 1]; first = np.r_[0, last[:-1] + 1]; cnt = last - first + 1
G = np.full(gx * gy, np.nan); ok = cnt >= 3
G[ks[last][ok]] = zs[(first + (0.35 * (cnt - 1)).astype(int))[ok]]
G = G.reshape(gy, gx)
for _ in range(300):
    msk = np.isnan(G)
    if not msk.any(): break
    P = np.pad(G, 1, constant_values=np.nan)
    nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
    c = (~np.isnan(nb)).sum(0); avg = np.nansum(nb, 0) / np.maximum(c, 1)
    G = np.where(msk & (c > 0), avg, G)
G = np.nan_to_num(G, nan=0.0)
for _ in range(2):
    P = np.pad(G, 1, mode='edge'); G = 0.5 * G + 0.125 * (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:])
print('surface grid', G.shape, 'z range %.2f..%.2f' % (G.min(), G.max()), '%.0fs' % (time.time() - t0))
# ---- output grid
bx0, by0, bx1, by1 = box_out
nx, ny = int(round((bx1 - bx0) / cell)), int(round((by1 - by0) / cell))
xs = bx0 + (np.arange(nx) + 0.5) * cell; ys = by1 - (np.arange(ny) + 0.5) * cell      # row 0 = north (max y)
XX, YY = np.meshgrid(xs, ys)
if PLAN:
    LL = FR.plan2lev(np.c_[XX.ravel(), YY.ravel()]); XX = LL[:, 0].reshape(ny, nx); YY = LL[:, 1].reshape(ny, nx)
# bilinear surface height
fx_ = (XX - x0) / gc - 0.5; fy_ = (YY - y0) / gc - 0.5
i0 = np.clip(np.floor(fx_).astype(int), 0, gx - 2); j0 = np.clip(np.floor(fy_).astype(int), 0, gy - 2)
ax = np.clip(fx_ - i0, 0, 1); ay = np.clip(fy_ - j0, 0, 1)
ZZ = (G[j0, i0] * (1 - ax) * (1 - ay) + G[j0, i0 + 1] * ax * (1 - ay) + G[j0 + 1, i0] * (1 - ax) * ay + G[j0 + 1, i0 + 1] * ax * ay)
Pl = np.stack([XX.ravel(), YY.ravel(), ZZ.ravel()], 1)                 # levelled metric
Pw = Pl @ RL + c0                                                    # metric SfM-aligned world (x_l = RL (x_w - c0))
np.save(out.replace('.png', '_Z.npy'), ZZ.astype(np.float32))
# ---- cameras
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
cam0 = list(rec.cameras.values())[0]; FX, FY, CX, CY = cam0.params[:4]; W, H = cam0.width, cam0.height
HS = 0.5
views = []
for im in sorted(rec.images.values(), key=lambda i: i.name):
    Rt = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
    views.append((im.name, Rt[:, :3], Rt[:, 3] * S))
N = Pw.shape[0]
K = 4
best_s = np.full((N, K), np.inf, np.float32); best_c = np.zeros((N, K, 3), np.float32)
for vi, (name, R, t) in enumerate(views):
    Pc = Pw @ R.T + t
    zc = Pc[:, 2]
    vis = zc > 0.3
    u = FX * Pc[:, 0] / np.maximum(zc, 1e-6) + CX; v = FY * Pc[:, 1] / np.maximum(zc, 1e-6) + CY
    vis &= (u > 8) & (u < W - 8) & (v > 8) & (v < H - 8)
    C = -R.T @ t
    d = np.linalg.norm(Pw - C, axis=1)
    vis &= d < 9.0
    if not vis.any(): continue
    idx = np.nonzero(vis)[0]
    # steepness: angle between viewing ray and the levelled vertical
    ray = (Pw[idx] - C) / d[idx, None]
    down = -(ray @ RL[2])                         # cos of angle to straight-down
    score = d[idx] * (1.6 - np.clip(down, 0, 1))  # prefer close + steep
    better = score < best_s[idx, -1]
    if not better.any(): continue
    idx = idx[better]; score = score[better]
    img = np.asarray(Image.open('real/sfm_g2/undist/images/' + name).convert('RGB').resize((int(W * HS), int(H * HS)), Image.BILINEAR), np.float32)
    uu = np.clip((u[idx] * HS).astype(int), 0, img.shape[1] - 1); vv = np.clip((v[idx] * HS).astype(int), 0, img.shape[0] - 1)
    col = img[vv, uu]
    # insert into sorted top-K
    S_ = np.concatenate([best_s[idx], score[:, None]], 1); C_ = np.concatenate([best_c[idx], col[:, None]], 1)
    o = np.argsort(S_, 1)[:, :K]
    best_s[idx] = np.take_along_axis(S_, o, 1); best_c[idx] = np.take_along_axis(C_, o[..., None].repeat(3, 2), 1)
    if vi % 50 == 0: print('view', vi, name, 'updated', len(idx), '%.0fs' % (time.time() - t0), flush=True)
valid = np.isfinite(best_s)
cnt = valid.sum(1)
# robust blend: per-channel median of valid samples among the best K
cc = np.where(valid[..., None], best_c, np.nan)
med = np.nanmedian(cc, 1)
med[cnt == 0] = 255
imo = med.reshape(ny, nx, 3).clip(0, 255).astype(np.uint8)
Image.fromarray(imo).save(out)
np.save(out.replace('.png', '_cnt.npy'), cnt.reshape(ny, nx).astype(np.uint8))
json.dump(dict(box=box_out, cell=cell, frame='plan' if PLAN else 'levelled', note='row 0 = max y'), open(out.replace('.png', '.json'), 'w'))
print('saved', out, imo.shape, '%.0fs' % (time.time() - t0))
