"""Convert a trained splat (splats.pt, SfM frame) into the viewer's compact format, in plan coordinates.

Planar little-endian layout of the decoded byte stream (base64 in N json chunks):
  pos   uint16 x3  quantised in [min, max] (plan metres, x east, y north, z up)
  scale uint8  x3  log-scale quantised in [smin, smax]
  rot   int8   x4  unit quaternion (w, x, y, z) * 127, plan frame
  rgba  uint8  x4  colour (SH DC) and opacity
  flags uint8  x1  bit mask of removals (see meta.flags)
"""
import os, sys, json, math, base64
import numpy as np
import torch

C0 = 0.28209479177387814


def quat_mul(a, b):
    w1, x1, y1, z1 = a.unbind(-1)
    w2, x2, y2, z2 = b.unbind(-1)
    return torch.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], -1)


def rotmat_to_quat(R):
    R = np.asarray(R, np.float64)
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def load_plan_splats(path, sim):
    """sim = dict(s, R (3x3), t (3)) mapping SfM -> plan: x_plan = s R x + t."""
    st = torch.load(path)
    s, R, t = float(sim['s']), torch.tensor(sim['R'], dtype=torch.float32), torch.tensor(sim['t'], dtype=torch.float32)
    means = st['means'] @ R.T * s + t
    q = torch.nn.functional.normalize(st['quats'], dim=1)
    qR = torch.tensor(rotmat_to_quat(sim['R']), dtype=torch.float32)[None].repeat(q.shape[0], 1)
    quats = torch.nn.functional.normalize(quat_mul(qR, q), dim=1)
    scales = st['scales'] + math.log(s)
    opac = torch.sigmoid(st['opac'])
    rgb = torch.clamp(st['sh'][:, 0] * C0 + 0.5, 0, 1)
    return dict(means=means, quats=quats, scales=scales, opac=opac, rgb=rgb, sh=st['sh'])


def encode(P, flags, out_dir, name='splat', min_opac=0.02, chunk_bytes=11_000_000, keep=None):
    os.makedirs(out_dir, exist_ok=True)
    sel = P['opac'] >= min_opac
    if keep is not None:
        sel &= keep
    idx = torch.nonzero(sel).squeeze(1)
    m = P['means'][idx].numpy().astype(np.float64)
    n = m.shape[0]
    lo = m.min(0) - 1e-3; hi = m.max(0) + 1e-3
    qpos = np.round((m - lo) / (hi - lo) * 65535).clip(0, 65535).astype('<u2')
    ls = P['scales'][idx].numpy()
    smin, smax = float(np.percentile(ls, 0.05)), float(np.percentile(ls, 99.95))
    qs = np.round((ls.clip(smin, smax) - smin) / (smax - smin) * 255).astype(np.uint8)
    q = P['quats'][idx].numpy()
    q = q * np.sign(q[:, :1] + 1e-12)  # w >= 0
    qr = np.round(q * 127).clip(-127, 127).astype(np.int8)
    rgba = np.concatenate([np.round(P['rgb'][idx].numpy() * 255), np.round(P['opac'][idx].numpy()[:, None] * 255)], 1).clip(0, 255).astype(np.uint8)
    fl = flags[idx].numpy().astype(np.uint8)
    blob = b''.join([qpos.tobytes(), qs.tobytes(), qr.tobytes(), rgba.tobytes(), fl.tobytes()])
    files = []
    for k, o in enumerate(range(0, len(blob), chunk_bytes)):
        fn = '%s-%d.json' % (name, k)
        with open(os.path.join(out_dir, fn), 'w') as f:
            json.dump({'data': base64.b64encode(blob[o:o + chunk_bytes]).decode('ascii')}, f)
        files.append(fn)
    header = dict(count=int(n), min=lo.round(4).tolist(), max=hi.round(4).tolist(), smin=smin, smax=smax)
    return header, files, idx


def point_in_poly(x, y, poly):
    """Vectorised even-odd test; poly Nx2 (plan metres)."""
    poly = np.asarray(poly, np.float64)
    inside = np.zeros(x.shape, bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        c = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        inside ^= c
        j = i
    return inside


def dist_to_polyline(x, y, pts):
    pts = np.asarray(pts, np.float64)
    d = np.full(x.shape, np.inf)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy + 1e-12
        t = np.clip(((x - x0) * vx + (y - y0) * vy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(x - (x0 + t * vx), y - (y0 + t * vy)))
    return d


def heightfield(xyz, bounds, cell=0.5, q=0.12, min_pts=4):
    """Ground height per cell from points (plan frame): low percentile, then hole filling and smoothing."""
    x0, y0, x1, y1 = bounds
    nx, ny = int(math.ceil((x1 - x0) / cell)) + 1, int(math.ceil((y1 - y0) / cell)) + 1
    ix = np.clip(((xyz[:, 0] - x0) / cell).round().astype(int), 0, nx - 1)
    iy = np.clip(((xyz[:, 1] - y0) / cell).round().astype(int), 0, ny - 1)
    key = iy * nx + ix
    order = np.argsort(key, kind='stable')
    ks, zs = key[order], xyz[order, 2]
    H = np.full(nx * ny, np.nan)
    starts = np.r_[0, np.nonzero(np.diff(ks))[0] + 1]
    ends = np.r_[starts[1:], len(ks)]
    for a, b in zip(starts, ends):
        if b - a >= min_pts:
            H[ks[a]] = np.quantile(zs[a:b], q)
    H = H.reshape(ny, nx)
    # fill holes by repeated neighbour averaging
    for _ in range(200):
        m = np.isnan(H)
        if not m.any():
            break
        P = np.pad(H, 1, constant_values=np.nan)
        nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
        cnt = (~np.isnan(nb)).sum(0)
        avg = np.nansum(nb, 0) / np.maximum(cnt, 1)
        H = np.where(m & (cnt > 0), avg, H)
    H = np.nan_to_num(H, nan=0.0)
    # light smoothing
    for _ in range(2):
        P = np.pad(H, 1, mode='edge')
        H = 0.4 * H + 0.15 * (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:])
    return dict(x0=x0, y0=y0, cell=cell, nx=nx, ny=ny), H.astype(np.float32)
