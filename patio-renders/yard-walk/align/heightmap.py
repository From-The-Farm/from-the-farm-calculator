"""Height-coded top view of splat centres in the levelled metric frame, with camera path + frame ids."""
import sys, json, numpy as np, torch
from PIL import Image, ImageDraw
ck = sys.argv[1]; out = sys.argv[2]
lev = json.load(open('align/level_g2m.json'))
R = np.array(lev['R']); c0 = np.array(lev['c0'])
st = torch.load(ck, map_location='cpu')
X = st['means'].numpy().astype(np.float64)
op = torch.sigmoid(st['opac']).numpy()
sc = np.exp(st['scales'].numpy()).max(1)
L = (X - c0) @ R.T
sel = (op > 0.5) & (sc < 0.25)
L = L[sel]
box = [-22, -20, 18, 24]
cell = 0.1
nx = int((box[2] - box[0]) / cell); ny = int((box[3] - box[1]) / cell)
ix = ((L[:, 0] - box[0]) / cell).astype(int); iy = ((box[3] - L[:, 1]) / cell).astype(int)
ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (L[:, 2] < 12) & (L[:, 2] > -3)
ix, iy, z = ix[ok], iy[ok], L[ok, 2]
Hmax = np.full((ny, nx), np.nan)
key = iy * nx + ix
o = np.lexsort((z, key)); ks = key[o]; zs = z[o]
last = np.r_[np.nonzero(np.diff(ks))[0], len(ks) - 1]
first = np.r_[0, last[:-1] + 1]
cnt = last - first + 1
# 90th percentile height per cell
q = first + (0.9 * (cnt - 1)).astype(int)
Hm = np.full(nx * ny, np.nan); Hm[ks[last]] = zs[q]
Hm[ks[last][cnt < 2]] = np.nan
Hm = Hm.reshape(ny, nx)
norm = np.clip((Hm + 1.0) / 8.0, 0, 1)
stops = np.array([[48, 18, 59], [40, 120, 240], [30, 200, 200], [80, 230, 60], [240, 220, 40], [250, 120, 20], [180, 20, 10]], float)
t = np.nan_to_num(norm) * (len(stops) - 1); i0 = np.clip(t.astype(int), 0, len(stops) - 2); fr = (t - i0)[..., None]
rgb = (stops[i0] * (1 - fr) + stops[i0 + 1] * fr).astype(np.uint8)
rgb[np.isnan(Hm)] = 255
im = Image.fromarray(rgb).resize((nx * 2, ny * 2), Image.NEAREST)
dr = ImageDraw.Draw(im); ppm = 2 / cell
def P(x, y): return ((x - box[0]) * ppm, (box[3] - y) * ppm)
for gx in range(box[0], box[2] + 1, 5):
    dr.line([P(gx, box[1]), P(gx, box[3])], fill=(160, 160, 160)); dr.text((P(gx, box[3])[0] + 2, 2), str(gx), fill=(0, 0, 0))
for gy in range(box[1], box[3] + 1, 5):
    dr.line([P(box[0], gy), P(box[2], gy)], fill=(160, 160, 160)); dr.text((2, P(box[0], gy)[1] + 2), str(gy), fill=(0, 0, 0))
cams = np.load('align/camdirs.npy', allow_pickle=True).item()
ks_ = sorted(cams)
for a, b in zip(ks_[:-1], ks_[1:]):
    if b == a + 1:
        dr.line([P(*cams[a][0][:2]), P(*cams[b][0][:2])], fill=(0, 0, 0), width=1)
for k in ks_:
    if k % 20 == 0:
        C, f = cams[k]
        p = P(C[0], C[1]); q2 = P(C[0] + f[0] * 1.5, C[1] + f[1] * 1.5)
        dr.line([p, q2], fill=(255, 0, 255), width=2)
        dr.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=(0, 0, 0))
        dr.text((p[0] + 4, p[1] - 10), str(k), fill=(0, 0, 0))
im.save(out); print(im.size)
