"""'Today' ground heightfield in plan metres from splat centres (low percentile per cell, filled, smoothed)."""
import sys, numpy as np, torch
sys.path.insert(0, 'align'); sys.path.insert(0, 'gs')
import frames as F, export_web as X
ck = sys.argv[1]; out = sys.argv[2]
st = torch.load(ck, map_location='cpu')
M = st['means'].numpy().astype(np.float64); op = torch.sigmoid(st['opac']).numpy(); sc = np.exp(st['scales'].numpy()).max(1)
Pp = F.lev2plan((M - F.C0 * F.S) @ F.RL.T)
m = (op > 0.4) & (sc < 0.2) & (Pp[:, 2] > -3) & (Pp[:, 2] < 2.2)
bounds = (-40.0, -26.0, 20.0, 24.0)
info, H = X.heightfield(Pp[m], bounds, cell=0.5, q=0.15, min_pts=4)
np.savez(out, H=H, **info)
print(info, 'H range %.2f..%.2f' % (H.min(), H.max()))
for x, y in [(0, 0), (5, 10), (-18, 11), (-29, 9.6), (9.5, -18.5), (10, 14.7), (-8, -9)]:
    i = int(round((x - info['x0']) / info['cell'])); j = int(round((y - info['y0']) / info['cell']))
    print('  ground at (%g, %g): %.2f' % (x, y, H[j, i]))
