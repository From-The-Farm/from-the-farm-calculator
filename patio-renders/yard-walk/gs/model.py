"""Gaussian splatting on the CPU: projection and SH in PyTorch, tile rasterizer in C++ (raster.cpp)."""
import os, math
import torch
import torch.nn.functional as F

_here = os.path.dirname(os.path.abspath(__file__))
_ext = None


def ext():
    global _ext
    if _ext is None:
        from torch.utils.cpp_extension import load
        _ext = load('gs_raster_cpu', [os.path.join(_here, 'raster.cpp')],
                    extra_cflags=['-O3', '-march=native', '-mprefer-vector-width=512', '-ffast-math', '-fopenmp'],
                    extra_ldflags=['-fopenmp', '-lmvec'], verbose=False)
    return _ext


SH_C0 = 0.28209479177387814
SH_C1 = 0.4886025119029199
SH_C2 = (1.0925484305920792, -1.0925484305920792, 0.31539156525252005, -1.0925484305920792, 0.5462742152960396)
SH_C3 = (-0.5900435899266435, 2.890611442640554, -0.4570457994644658, 0.3731763325901154,
         -0.4570457994644658, 1.445305721320277, -0.5900435899266435)


def eval_sh(deg, sh, dirs):
    """sh (N,K,3) with K >= (deg+1)^2, dirs (N,3) unit. Returns (N,3)."""
    res = SH_C0 * sh[:, 0]
    if deg < 1:
        return res
    x, y, z = dirs[:, 0:1], dirs[:, 1:2], dirs[:, 2:3]
    res = res - SH_C1 * y * sh[:, 1] + SH_C1 * z * sh[:, 2] - SH_C1 * x * sh[:, 3]
    if deg < 2:
        return res
    xx, yy, zz, xy, yz, xz = x * x, y * y, z * z, x * y, y * z, x * z
    res = (res + SH_C2[0] * xy * sh[:, 4] + SH_C2[1] * yz * sh[:, 5] + SH_C2[2] * (2 * zz - xx - yy) * sh[:, 6]
           + SH_C2[3] * xz * sh[:, 7] + SH_C2[4] * (xx - yy) * sh[:, 8])
    if deg < 3:
        return res
    return (res + SH_C3[0] * y * (3 * xx - yy) * sh[:, 9] + SH_C3[1] * xy * z * sh[:, 10]
            + SH_C3[2] * y * (4 * zz - xx - yy) * sh[:, 11] + SH_C3[3] * z * (2 * zz - 3 * xx - 3 * yy) * sh[:, 12]
            + SH_C3[4] * x * (4 * zz - xx - yy) * sh[:, 13] + SH_C3[5] * z * (xx - yy) * sh[:, 14]
            + SH_C3[6] * x * (xx - 3 * yy) * sh[:, 15])


def quat_to_rotmat(q):
    q = F.normalize(q, dim=-1)
    w, x, y, z = q.unbind(-1)
    return torch.stack([
        1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
        2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
        2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1).reshape(q.shape[:-1] + (3, 3))


class Camera:
    """Pinhole camera, world->camera R (3x3) and t (3) in OpenCV convention (x right, y down, z forward)."""

    def __init__(self, R, t, fx, fy, cx, cy, W, H):
        self.R = torch.as_tensor(R, dtype=torch.float32)
        self.t = torch.as_tensor(t, dtype=torch.float32)
        self.fx, self.fy, self.cx, self.cy, self.W, self.H = float(fx), float(fy), float(cx), float(cy), int(W), int(H)

    @property
    def center(self):
        return -self.R.T @ self.t

    def scaled(self, s):
        W, H = max(1, round(self.W * s)), max(1, round(self.H * s))
        sx, sy = W / self.W, H / self.H
        return Camera(self.R, self.t, self.fx * sx, self.fy * sy, self.cx * sx, self.cy * sy, W, H)


class _Raster(torch.autograd.Function):
    @staticmethod
    def forward(ctx, means2d, conics, colors, opac, offsets, ids, W, H, bg, holder):
        img, fT, nc = ext().render_forward(means2d, conics, colors, opac, offsets, ids, W, H, bg)
        ctx.save_for_backward(means2d, conics, colors, opac, offsets, ids, bg, fT, nc)
        ctx.W, ctx.H, ctx.holder = W, H, holder
        ctx.mark_non_differentiable(fT)
        return img, fT

    @staticmethod
    def backward(ctx, dimg, dT):
        means2d, conics, colors, opac, offsets, ids, bg, fT, nc = ctx.saved_tensors
        dm, dc, dcol, dop, dabs = ext().render_backward(means2d, conics, colors, opac, offsets, ids, ctx.W, ctx.H,
                                                         bg, fT, nc, dimg.contiguous())
        if ctx.holder is not None:
            ctx.holder['absgrad'] = dabs
        return dm, dc, dcol, dop, None, None, None, None, None, None


def project(means, quats, log_scales, opac, cam, near=0.1, eps2d=0.3):
    """Returns dict with visible index `idx` and differentiable means2d, conics, depth plus extents."""
    R, t = cam.R, cam.t
    with torch.no_grad():
        z_all = means @ R[2] + t[2]
        idx = torch.nonzero(z_all > near).squeeze(1)
    m = means[idx]
    pc = m @ R.T + t
    x, y, z = pc.unbind(1)
    Rq = quat_to_rotmat(quats[idx])
    S = torch.exp(log_scales[idx])
    Mq = Rq * S[:, None, :]
    Sig = Mq @ Mq.transpose(1, 2)
    Sc = torch.einsum('ij,njk,lk->nil', R, Sig, R)
    limx = 1.3 * max(cam.cx, cam.W - cam.cx) / cam.fx
    limy = 1.3 * max(cam.cy, cam.H - cam.cy) / cam.fy
    tx = torch.clamp(x / z, -limx, limx) * z
    ty = torch.clamp(y / z, -limy, limy) * z
    zero = torch.zeros_like(z)
    J = torch.stack([cam.fx / z, zero, -cam.fx * tx / (z * z), zero, cam.fy / z, -cam.fy * ty / (z * z)], 1).reshape(-1, 2, 3)
    cov = J @ Sc @ J.transpose(1, 2)
    a = cov[:, 0, 0] + eps2d
    b = cov[:, 0, 1]
    c = cov[:, 1, 1] + eps2d
    det = a * c - b * b
    detc = torch.clamp(det, min=1e-12)
    conics = torch.stack([c / detc, -b / detc, a / detc], 1)
    means2d = torch.stack([cam.fx * x / z + cam.cx, cam.fy * y / z + cam.cy], 1)
    with torch.no_grad():
        op = opac[idx]
        k = torch.sqrt(torch.clamp(2.0 * torch.log(torch.clamp(255.0 * op, min=1e-6)), min=0.0))
        ex = k * torch.sqrt(torch.clamp(a, min=0))
        ey = k * torch.sqrt(torch.clamp(c, min=0))
        ok = (det > 1e-12) & (k > 0) & (means2d[:, 0] + ex > 0) & (means2d[:, 0] - ex < cam.W) \
            & (means2d[:, 1] + ey > 0) & (means2d[:, 1] - ey < cam.H)
        ext_ = torch.stack([torch.where(ok, ex, torch.zeros_like(ex)), torch.where(ok, ey, torch.zeros_like(ey))], 1)
        radius = torch.where(ok, torch.maximum(ex, ey), torch.zeros_like(ex))
    return dict(idx=idx, means2d=means2d, conics=conics, depth=z, ext=ext_, ok=ok, radius=radius, pc=pc)


def render(g, cam, sh_degree, bg, holder=None, active_sh=None):
    """g: dict of parameters (means, quats, scales, opacities (logit), sh0 (N,1,3), shN (N,K,3)).
    Returns (image (H,W,3), info)."""
    opac_all = torch.sigmoid(g['opacities'])
    P = project(g['means'], g['quats'], g['scales'], opac_all.detach(), cam)
    idx, ok = P['idx'], P['ok']
    sel = torch.nonzero(ok).squeeze(1)
    gidx = idx[sel]
    means2d = P['means2d'][sel]
    if holder is not None:
        means2d.retain_grad()
        holder['means2d'] = means2d
        holder['gidx'] = gidx
        holder['radius'] = P['radius'][sel]
    conics = P['conics'][sel].contiguous()
    depth = P['depth'][sel]
    sh = torch.cat([g['sh0'], g['shN']], 1)[gidx] if g['shN'].shape[1] else g['sh0'][gidx]
    deg = sh_degree if active_sh is None else active_sh
    if deg > 0:
        dirs = F.normalize(g['means'][gidx] - cam.center, dim=1)
        col = eval_sh(deg, sh, dirs)
    else:
        col = SH_C0 * sh[:, 0]
    col = torch.clamp(col + 0.5, min=0.0)
    opac = opac_all[gidx]
    with torch.no_grad():
        order = torch.argsort(depth.detach())
        offsets, ids = ext().bin_gaussians(means2d.detach().contiguous(), P['ext'][sel].contiguous(), order, cam.W, cam.H)
    img, fT = _Raster.apply(means2d.contiguous(), conics, col.contiguous(), opac.contiguous(), offsets, ids,
                            cam.W, cam.H, bg.contiguous(), holder)
    return img, dict(gidx=gidx, n_pairs=int(ids.numel()), finalT=fT)


def ref_rasterize(means2d, conics, colors, opac, depths, W, H, bg):
    """Dense pure-PyTorch reference (no early stop): for tests on tiny images."""
    order = torch.argsort(depths)
    m, co, cl, op = means2d[order], conics[order], colors[order], opac[order]
    ys, xs = torch.meshgrid(torch.arange(H, dtype=torch.float32) + 0.5, torch.arange(W, dtype=torch.float32) + 0.5, indexing='ij')
    dx = m[:, 0, None, None] - xs
    dy = m[:, 1, None, None] - ys
    power = -0.5 * (co[:, 0, None, None] * dx * dx + co[:, 2, None, None] * dy * dy) - co[:, 1, None, None] * dx * dy
    alpha = torch.clamp(op[:, None, None] * torch.exp(power), max=0.99)
    alpha = torch.where((power > 0) | (alpha < 1.0 / 255.0), torch.zeros_like(alpha), alpha)
    T = torch.cumprod(torch.cat([torch.ones_like(alpha[:1]), 1 - alpha[:-1]], 0), 0)
    w = alpha * T
    img = (w[..., None] * cl[:, None, None, :]).sum(0)
    Tf = T[-1] * (1 - alpha[-1])
    return img + Tf[..., None] * bg
