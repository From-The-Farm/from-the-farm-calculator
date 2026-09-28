"""Fine ground-height map (low percentile of splat centres per cell) in the levelled metric frame."""
import sys, json, numpy as np, torch
from PIL import Image, ImageDraw
ck, out = sys.argv[1], sys.argv[2]
box = [float(v) for v in sys.argv[3:7]] if len(sys.argv) > 6 else [-12, -18, 14, 6]
zr = (float(sys.argv[7]), float(sys.argv[8])) if len(sys.argv) > 8 else (-1.0, 1.0)
qq = float(sys.argv[9]) if len(sys.argv) > 9 else 0.2
lev = json.load(open('align/level_g2m.json'))
R = np.array(lev['R']); c0 = np.array(lev['c0'])
st = torch.load(ck, map_location='cpu')
X = st['means'].numpy().astype(np.float64); op = torch.sigmoid(st['opac']).numpy(); sc = np.exp(st['scales'].numpy()).max(1)
L = (X - c0) @ R.T
sel = (op > 0.3) & (sc < 0.15)
L = L[sel]
cell = 0.1
x0, y0, x1, y1 = box
nx, ny = int((x1 - x0) / cell), int((y1 - y0) / cell)
ix = ((L[:, 0] - x0) / cell).astype(int); iy = ((y1 - L[:, 1]) / cell).astype(int)
ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (L[:, 2] > -3) & (L[:, 2] < 4)
ix, iy, z = ix[ok], iy[ok], L[ok, 2]
key = iy * nx + ix; o = np.lexsort((z, key)); ks = key[o]; zs = z[o]
last = np.r_[np.nonzero(np.diff(ks))[0], len(ks) - 1]; first = np.r_[0, last[:-1] + 1]; cnt = last - first + 1
H = np.full(nx * ny, np.nan); good = cnt >= 3
H[ks[last][good]] = zs[(first + (qq * (cnt - 1)).astype(int))[good]]
H = H.reshape(ny, nx)
np.save(out.replace('.png', '.npy'), dict(H=H, box=box, cell=cell), allow_pickle=True)
t = np.clip((H - zr[0]) / (zr[1] - zr[0]), 0, 1)
stops = np.array([[48, 18, 59], [40, 120, 240], [30, 200, 200], [80, 230, 60], [240, 220, 40], [250, 120, 20], [180, 20, 10]], float)
tt = np.nan_to_num(t) * (len(stops) - 1); i0 = np.clip(tt.astype(int), 0, len(stops) - 2); fr = (tt - i0)[..., None]
rgb = (stops[i0] * (1 - fr) + stops[i0 + 1] * fr).astype(np.uint8); rgb[np.isnan(H)] = 255
S = 3
im = Image.fromarray(rgb).resize((nx * S, ny * S), Image.NEAREST); d = ImageDraw.Draw(im); ppm = S / cell
def P(x, y): return ((x - x0) * ppm, (y1 - y) * ppm)
for gx in range(int(np.ceil(x0)), int(x1) + 1):
    d.line([P(gx, y0), P(gx, y1)], fill=(90, 90, 90) if gx % 5 == 0 else (190, 190, 190), width=1)
    if gx % 2 == 0: d.text((P(gx, y1)[0] + 2, 2), str(gx), fill=(0, 0, 0))
for gy in range(int(np.ceil(y0)), int(y1) + 1):
    d.line([P(x0, gy), P(x1, gy)], fill=(90, 90, 90) if gy % 5 == 0 else (190, 190, 190), width=1)
    if gy % 2 == 0: d.text((2, P(x0, gy)[1] + 2), str(gy), fill=(0, 0, 0))
cams = np.load('align/camdirs.npy', allow_pickle=True).item()
for k in sorted(cams):
    if k % 10 == 0:
        C, f = cams[k]; p = P(C[0], C[1])
        if 0 < p[0] < im.size[0] and 0 < p[1] < im.size[1]:
            d.line([p, P(C[0] + f[0], C[1] + f[1])], fill=(255, 0, 255), width=2); d.text((p[0] + 4, p[1] - 10), str(k), fill=(0, 0, 0))
im.save(out); print(im.size, 'z range', zr)
