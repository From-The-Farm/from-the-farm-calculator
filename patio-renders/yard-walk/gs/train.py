"""CPU Gaussian-splat trainer (3DGS-style densification, selective Adam, fused C++ kernels).

python3 train.py --data DIR --out OUT [--steps 12000] [--res 960]
DIR holds either cameras.json + images (synthetic) or colmap/ (sparse model) + images/.
"""
import os, sys, json, math, time, argparse, random
os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")  # the default spin-waiting stalls torch ops next to our OpenMP kernels
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

C0 = 0.28209479177387814


# ------------------------------------------------------------------ data
class View:
    def __init__(self, name, cam, img):
        self.name, self.cam = name, cam
        self.levels = {1: img}  # uint8 (H,W,3)

    def level(self, f):
        if f not in self.levels:
            im = self.levels[1]
            H, W = im.shape[:2]
            h, w = max(1, round(H / f)), max(1, round(W / f))
            x = F.interpolate(im.permute(2, 0, 1)[None].float(), size=(h, w), mode='area')[0]
            self.levels[f] = x.round().clamp(0, 255).byte().permute(1, 2, 0).contiguous()
        return self.levels[f], self.cam.scaled(self.levels[f].shape[1] / self.cam.W) if f != 1 else self.cam


def load_image(path, W=None, H=None):
    im = Image.open(path).convert('RGB')
    if W and (im.width != W or im.height != H):
        im = im.resize((W, H), Image.LANCZOS)
    return torch.from_numpy(np.asarray(im).copy())


def load_synth(d, res):
    meta = json.load(open(os.path.join(d, 'cameras.json')))
    s = min(1.0, res / max(meta['w'], meta['h']))
    W, H = round(meta['w'] * s), round(meta['h'] * s)
    views = []
    for fr in meta['frames']:
        p = os.path.join(d, fr['file'])
        if not os.path.exists(p):
            continue
        cam = model.Camera(fr['R'], fr['t'], meta['fx'] * s, meta['fy'] * s, meta['cx'] * s, meta['cy'] * s, W, H)
        views.append(View(fr['file'], cam, load_image(p, W, H)))
    return views, None


def load_colmap(d, res, scale=1.0):
    import pycolmap
    rec = pycolmap.Reconstruction(os.path.join(d, 'sparse'))
    views = []
    for iid, im in sorted(rec.images.items(), key=lambda kv: kv[1].name):
        c = rec.cameras[im.camera_id]
        p = c.params
        if c.model.name in ('PINHOLE',):
            fx, fy, cx, cy = p[0], p[1], p[2], p[3]
        elif c.model.name in ('SIMPLE_PINHOLE',):
            fx = fy = p[0]; cx, cy = p[1], p[2]
        else:
            raise SystemExit('undistort first: camera model %s' % c.model.name)
        s = min(1.0, res / max(c.width, c.height))
        W, H = round(c.width * s), round(c.height * s)
        pose = im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world
        Rt = np.asarray(pose.matrix())
        cam = model.Camera(Rt[:, :3], Rt[:, 3] * scale, fx * W / c.width, fy * H / c.height, cx * W / c.width, cy * H / c.height, W, H)
        views.append(View(im.name, cam, load_image(os.path.join(d, 'images', im.name), W, H)))
    xyz = np.array([pt.xyz for pt in rec.points3D.values()], np.float32) * scale
    rgb = np.array([pt.color for pt in rec.points3D.values()], np.float32) / 255.0
    return views, (xyz, rgb)


# ------------------------------------------------------------------ loss
def _gauss(size=11, sigma=1.5):
    x = torch.arange(size, dtype=torch.float32) - size // 2
    g = torch.exp(-x * x / (2 * sigma * sigma))
    return g / g.sum()


_G = _gauss()


def _blur(x):
    c = x.shape[1]
    k = _G.to(x)
    x = F.conv2d(x, k.view(1, 1, 1, -1).repeat(c, 1, 1, 1), padding=(0, 5), groups=c)
    return F.conv2d(x, k.view(1, 1, -1, 1).repeat(c, 1, 1, 1), padding=(5, 0), groups=c)


def ssim(x, y):
    """x, y (1,3,H,W) in [0,1]"""
    C1, C2 = 0.01 ** 2, 0.03 ** 2
    mx, my = _blur(x), _blur(y)
    sxx = _blur(x * x) - mx * mx
    syy = _blur(y * y) - my * my
    sxy = _blur(x * y) - mx * my
    m = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))
    return m.mean()


def psnr(a, b):
    return -10 * math.log10(max(float(((a - b) ** 2).mean()), 1e-10))


# ------------------------------------------------------------------ model state
class Splats:
    NAMES = ('means', 'quats', 'scales', 'opac', 'sh')

    def __init__(self, xyz, rgb, K=16):
        n = xyz.shape[0]
        self.K = K
        self.means = torch.as_tensor(xyz, dtype=torch.float32).contiguous()
        d = knn_dist(self.means)
        self.scales = torch.log(torch.clamp(d, 1e-4, 1e3))[:, None].repeat(1, 3).contiguous()
        self.quats = torch.zeros(n, 4); self.quats[:, 0] = 1
        self.opac = torch.logit(torch.full((n,), 0.1))
        self.sh = torch.zeros(n, K, 3)
        self.sh[:, 0] = (torch.as_tensor(rgb, dtype=torch.float32) - 0.5) / C0
        self.m = {k: torch.zeros_like(getattr(self, k)) for k in self.NAMES}
        self.v = {k: torch.zeros_like(getattr(self, k)) for k in self.NAMES}

    @property
    def n(self):
        return self.means.shape[0]

    def keep(self, mask):
        for k in self.NAMES:
            setattr(self, k, getattr(self, k)[mask].contiguous())
            self.m[k] = self.m[k][mask].contiguous(); self.v[k] = self.v[k][mask].contiguous()

    def append(self, new):
        for k in self.NAMES:
            setattr(self, k, torch.cat([getattr(self, k), new[k]], 0).contiguous())
            self.m[k] = torch.cat([self.m[k], torch.zeros_like(new[k])], 0).contiguous()
            self.v[k] = torch.cat([self.v[k], torch.zeros_like(new[k])], 0).contiguous()

    def state(self):
        return {k: getattr(self, k) for k in self.NAMES}


def knn_dist(x, k=3):
    try:
        from scipy.spatial import cKDTree
        d, _ = cKDTree(x.numpy()).query(x.numpy(), k=k + 1)
        return torch.from_numpy(np.sqrt((d[:, 1:] ** 2).mean(1))).float()
    except ImportError:
        out = torch.empty(x.shape[0])
        for i in range(0, x.shape[0], 4096):
            dd = torch.cdist(x[i:i + 4096], x)
            out[i:i + 4096] = torch.sqrt((dd.topk(k + 1, largest=False).values[:, 1:] ** 2).mean(1))
        return out


def quat_rotmat(q):
    return model.quat_to_rotmat(q)


# ------------------------------------------------------------------ training
def train(views, pts, out, steps=12000, sh_degree=3, test_every=8, log=print, cfg=None):
    cfg = cfg or {}
    E = model.ext()
    torch.manual_seed(0); random.seed(0)
    test = [v for i, v in enumerate(views) if test_every and i % test_every == 0]
    trainv = [v for i, v in enumerate(views) if not (test_every and i % test_every == 0)]
    centers = torch.stack([v.cam.center for v in views])
    ctr = centers.mean(0)
    scene_scale = float((centers - ctr).norm(dim=1).max()) * 1.1
    log('views %d train %d test %d scene_scale %.2f' % (len(views), len(trainv), len(test), scene_scale))
    xyz, rgb = pts
    # sky / far shell so the background has something to optimise
    ns = int(cfg.get('sky_points', 20000))
    if ns:
        # upper hemisphere around the cameras; "up" is the average camera up vector (OpenCV y is down)
        up = F.normalize(-torch.stack([v.cam.R[1] for v in views]).mean(0), dim=0)
        d = F.normalize(torch.randn(ns, 3), dim=1)
        s_ = d @ up
        d = torch.where((s_ < -0.05)[:, None], d - 2 * s_[:, None] * up[None], d)
        far = ctr + d * scene_scale * float(cfg.get('sky_radius', 6.0))
        xyz = np.concatenate([xyz, far.numpy()], 0)
        rgb = np.concatenate([rgb, np.tile(np.array([[0.62, 0.72, 0.85]], np.float32), (ns, 1))], 0)
    S = Splats(xyz, rgb)
    log('init gaussians %d' % S.n)
    lr = dict(means=1.6e-4 * scene_scale, quats=1e-3, scales=5e-3, opac=5e-2)
    lr_final_means = 1.6e-6 * scene_scale
    sh_cols = torch.full((S.K * 3,), 2.5e-3 / 20.0); sh_cols[:3] = 2.5e-3
    b1, b2, eps = 0.9, 0.999, 1e-15
    refine_start, refine_stop = cfg.get('refine_start', 500), cfg.get('refine_stop', int(steps * 0.6))
    refine_every, reset_every = cfg.get('refine_every', 100), cfg.get('reset_every', 3000)
    grow_grad2d, grow_scale3d, prune_opa = cfg.get('grow_grad2d', 0.0002), 0.01, 0.005
    prune_scale3d, prune_scale2d = 0.1, 0.15
    max_n = int(cfg.get('max_gaussians', 1_500_000))
    sched = cfg.get('res_schedule', [(0, 4), (1000, 2), (3500, 1)])
    grad2d = torch.zeros(S.n); count = torch.zeros(S.n); radii = torch.zeros(S.n)
    # per-view affine colour correction (auto exposure / white balance of a phone video); identity for export
    use_app = bool(cfg.get('appearance', True))
    nv = len(trainv)
    appA = torch.eye(3).repeat(nv, 1, 1); appb = torch.zeros(nv, 3)
    appM = torch.zeros(nv, 12); appV = torch.zeros(nv, 12); appT = torch.zeros(nv)
    vid = {id(v): i for i, v in enumerate(trainv)}
    app_start = int(cfg.get('app_start', 500))
    t_start = time.time(); order = []
    hist = []
    for step in range(steps + 1):
        f = [fac for st, fac in sched if step >= st][-1]
        if not order:
            order = list(range(len(trainv))); random.shuffle(order)
        v = trainv[order.pop()]
        gt8, cam = v.level(f)
        W, H = cam.W, cam.H
        deg = min(sh_degree, step // 1000)
        bg = torch.rand(3)
        R, t = cam.R, cam.t
        m2, co, dp, ex, op = E.project_forward(S.means, S.quats, S.scales, S.opac, R, t, cam.fx, cam.fy, cam.cx, cam.cy, W, H, 0.1, 0.3)
        vis = torch.nonzero(ex[:, 0] > 0).squeeze(1)
        vis = vis[torch.argsort(dp[vis])]
        m2v, cov, opv, exv = m2[vis].contiguous(), co[vis].contiguous(), op[vis].contiguous(), ex[vis].contiguous()
        campos = cam.center.contiguous()
        col = E.sh_forward(S.sh, S.means, campos, vis, deg)
        offsets, ids = E.bin_gaussians(m2v, exv, torch.arange(vis.numel()), W, H)
        img, fT, nc = E.render_forward(m2v, cov, col, opv, offsets, ids, W, H, bg)
        gt = gt8.float() / 255.0
        vi = vid[id(v)]
        if use_app and step >= app_start:
            A, bb = appA[vi], appb[vi]
            imc = (img.reshape(-1, 3) @ A.T + bb).reshape(img.shape).contiguous()
            loss_t, dimc, _ = E.loss_l1_ssim(imc, gt, 0.2)
            dflat = dimc.reshape(-1, 3)
            dimg = (dflat @ A).reshape(img.shape).contiguous()
            gA = dflat.T @ img.reshape(-1, 3) + 1e-2 * (A - torch.eye(3))
            gb = dflat.sum(0) + 1e-2 * bb
            g = torch.cat([gA.reshape(-1), gb])
            appT[vi] += 1; tt = float(appT[vi])
            appM[vi] = 0.9 * appM[vi] + 0.1 * g
            appV[vi] = 0.999 * appV[vi] + 0.001 * g * g
            upd = 2e-3 * (appM[vi] / (1 - 0.9 ** tt)) / (torch.sqrt(appV[vi] / (1 - 0.999 ** tt)) + 1e-8)
            appA[vi] -= upd[:9].reshape(3, 3); appb[vi] -= upd[9:]
            img_log = imc
        else:
            loss_t, dimg, _ = E.loss_l1_ssim(img, gt, 0.2)
            img_log = img
        loss = float(loss_t)
        dm2, dco, dcol, dop, dabs = E.render_backward(m2v, cov, col, opv, offsets, ids, W, H, bg, fT, nc, dimg)
        dmeans, dq, dls = E.project_backward(S.means, S.quats, S.scales, R, t, cam.fx, cam.fy, cam.cx, cam.cy, W, H, 0.3, vis, dm2, dco)
        dsh = E.sh_backward(dcol, col, S.means, campos, vis, deg, S.K)
        dol = (dop * opv * (1 - opv)).contiguous()
        k = step + 1
        bc1, bc2 = 1 - b1 ** k, 1 - b2 ** k
        lr_means = lr['means'] * (lr_final_means / lr['means']) ** (step / steps)
        E.adam_rows(S.means, dmeans, S.m['means'], S.v['means'], vis, lr_means, b1, b2, eps, bc1, bc2)
        E.adam_rows(S.quats, dq, S.m['quats'], S.v['quats'], vis, lr['quats'], b1, b2, eps, bc1, bc2)
        E.adam_rows(S.scales, dls, S.m['scales'], S.v['scales'], vis, lr['scales'], b1, b2, eps, bc1, bc2)
        E.adam_rows(S.opac, dol, S.m['opac'], S.v['opac'], vis, lr['opac'], b1, b2, eps, bc1, bc2)
        E.adam_rows_cols(S.sh, dsh.reshape(vis.numel(), -1).contiguous(), S.m['sh'], S.v['sh'], vis, sh_cols, b1, b2, eps, bc1, bc2)

        # densification statistics (gradient of the 2D means in NDC units, as in gsplat)
        if step < refine_stop:
            g2 = dm2 * torch.tensor([W / 2.0, H / 2.0])
            grad2d.index_add_(0, vis, g2.norm(dim=1))
            count.index_add_(0, vis, torch.ones(vis.numel()))
            rr = torch.maximum(exv[:, 0], exv[:, 1]) / max(W, H)
            radii[vis] = torch.maximum(radii[vis], rr)

        if refine_start <= step < refine_stop and step % refine_every == 0 and step > 0:
            n0 = S.n
            grads = grad2d / count.clamp(min=1)
            smax = torch.exp(S.scales).max(1).values
            high = grads > grow_grad2d
            small = smax <= grow_scale3d * scene_scale
            dup = high & small
            split = high & ~small
            budget = max_n - S.n
            if budget <= 0:
                dup[:] = False; split[:] = False
            elif int(dup.sum() + split.sum()) > budget:
                thr = torch.topk(grads[high], budget).values[-1]
                dup &= grads >= thr; split &= grads >= thr
            nd, ns_ = int(dup.sum()), int(split.sum())
            if nd:
                S.append({k: getattr(S, k)[dup] for k in S.NAMES})
            if ns_:
                idx = torch.nonzero(split).squeeze(1)
                sc = torch.exp(S.scales[idx])
                Rm = quat_rotmat(S.quats[idx])
                new = {}
                samples = torch.einsum('nij,bnj->bni', Rm, torch.randn(2, idx.numel(), 3) * sc[None])
                new['means'] = (S.means[idx][None] + samples).reshape(-1, 3)
                new['scales'] = torch.log(sc / 1.6).repeat(2, 1)
                for kk in ('quats', 'opac', 'sh'):
                    new[kk] = getattr(S, kk)[idx].repeat((2,) + (1,) * (getattr(S, kk).dim() - 1))
                S.append(new)
            # prune: split originals, transparent ones, and (after the first reset) huge ones
            keep = torch.ones(S.n, dtype=torch.bool)
            if ns_:
                keep[torch.nonzero(split).squeeze(1)] = False
            keep &= torch.sigmoid(S.opac) >= prune_opa
            if step > reset_every:
                dist = (S.means - ctr).norm(dim=1)
                allow = prune_scale3d * scene_scale * torch.clamp(dist / scene_scale, min=1.0)
                big = torch.exp(S.scales).max(1).values > allow
                rad = torch.cat([radii, torch.zeros(S.n - radii.numel())])
                big |= rad > prune_scale2d
                keep &= ~big
            S.keep(keep)
            grad2d = torch.zeros(S.n); count = torch.zeros(S.n); radii = torch.zeros(S.n)
            log('step %d refine: +%d dup +%d split, %d -> %d' % (step, nd, 2 * ns_, n0, S.n))
        if step > 0 and step % reset_every == 0 and step < refine_stop:
            S.opac = torch.clamp(S.opac, max=float(torch.logit(torch.tensor(prune_opa * 2.0)))).contiguous()
            S.m['opac'].zero_(); S.v['opac'].zero_()
            log('step %d opacity reset' % step)
        if step % 100 == 0:
            hist.append((step, float(loss), psnr(img_log, gt)))
            el = time.time() - t_start
            log('step %5d  f%d %dx%d  loss %.4f  psnr %.2f  n %d  vis %d  pairs %d  %.2fs/step  elapsed %.0fs' % (
                step, f, W, H, float(loss), hist[-1][2], S.n, vis.numel(), ids.numel(), el / (step + 1), el))
        if cfg.get('ckpt_every') and step % cfg['ckpt_every'] == 0 and step > 0:
            torch.save(S.state(), os.path.join(out, 'ckpt.pt'))
    # evaluation on held-out views
    ps = []
    for v in test:
        gt8, cam = v.level(1)
        im = render_view(S, cam, sh_degree, torch.zeros(3))
        ps.append(psnr(im, gt8.float() / 255.0))
    if ps:
        log('test PSNR %.2f over %d views' % (sum(ps) / len(ps), len(ps)))
    torch.save(S.state(), os.path.join(out, 'splats.pt'))
    torch.save({'A': appA, 'b': appb, 'names': [v.name for v in trainv]}, os.path.join(out, 'appearance.pt'))
    return S


def render_view(S, cam, deg, bg):
    E = model.ext()
    m2, co, dp, ex, op = E.project_forward(S.means, S.quats, S.scales, S.opac, cam.R, cam.t, cam.fx, cam.fy, cam.cx, cam.cy, cam.W, cam.H, 0.1, 0.3)
    vis = torch.nonzero(ex[:, 0] > 0).squeeze(1)
    vis = vis[torch.argsort(dp[vis])]
    col = E.sh_forward(S.sh, S.means, cam.center.contiguous(), vis, deg)
    offsets, ids = E.bin_gaussians(m2[vis].contiguous(), ex[vis].contiguous(), torch.arange(vis.numel()), cam.W, cam.H)
    img, fT, nc = E.render_forward(m2[vis].contiguous(), co[vis].contiguous(), col, op[vis].contiguous(), offsets, ids, cam.W, cam.H, bg)
    return img


def save_ply(S, path):
    n = S.n
    sh = S.sh
    fields = ['x', 'y', 'z', 'nx', 'ny', 'nz', 'f_dc_0', 'f_dc_1', 'f_dc_2'] + ['f_rest_%d' % i for i in range((S.K - 1) * 3)] + \
             ['opacity', 'scale_0', 'scale_1', 'scale_2', 'rot_0', 'rot_1', 'rot_2', 'rot_3']
    rest = sh[:, 1:].permute(0, 2, 1).reshape(n, -1)  # channel-major like the reference exporter
    arr = torch.cat([S.means, torch.zeros(n, 3), sh[:, 0], rest, S.opac[:, None], S.scales, F.normalize(S.quats, dim=1)], 1).numpy().astype(np.float32)
    with open(path, 'wb') as f:
        f.write(('ply\nformat binary_little_endian 1.0\nelement vertex %d\n' % n).encode())
        for fl in fields:
            f.write(('property float %s\n' % fl).encode())
        f.write(b'end_header\n')
        f.write(arr.tobytes())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--steps', type=int, default=12000)
    ap.add_argument('--res', type=int, default=960)
    ap.add_argument('--max', type=int, default=1500000)
    ap.add_argument('--threads', type=int, default=4)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    os.makedirs(a.out, exist_ok=True)
    logf = open(os.path.join(a.out, 'train.log'), 'a')

    def log(s):
        print(s, flush=True); logf.write(s + '\n'); logf.flush()

    if os.path.exists(os.path.join(a.data, 'cameras.json')):
        views, pts = load_synth(a.data, a.res)
    else:
        cfg0 = json.load(open(os.path.join(a.data, 'train_cfg.json'))) if os.path.exists(os.path.join(a.data, 'train_cfg.json')) else {}
        views, pts = load_colmap(a.data, a.res, float(cfg0.get('scale', 1.0)))
    if pts is None:
        pts = np.load(os.path.join(a.data, 'points.npz'))
        pts = (pts['xyz'].astype(np.float32), pts['rgb'].astype(np.float32))
    cfg = dict(max_gaussians=a.max, ckpt_every=2000)
    if os.path.exists(os.path.join(a.data, 'train_cfg.json')):
        cfg.update(json.load(open(os.path.join(a.data, 'train_cfg.json'))))
    S = train(views, pts, a.out, steps=a.steps, log=log, cfg=cfg, test_every=int(cfg.get('test_every', 8)))
    save_ply(S, os.path.join(a.out, 'splats.ply'))
    log('saved')
