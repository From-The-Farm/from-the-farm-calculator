"""Top-down (near-orthographic) render of a splat checkpoint in a levelled frame.
python3 render_top.py CKPT LEVEL.json OUT.png [--zmax 2.5] [--px 2000] [--box x0 y0 x1 y1]"""
import os, sys, json, math, argparse
os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model
from PIL import Image

def levelled(st, lev):
    """Return a copy of the splat state in the levelled frame x_l = s * R (x - c0)."""
    R = torch.tensor(lev['R'], dtype=torch.float32); c0 = torch.tensor(lev['c0'], dtype=torch.float32); s = float(lev.get('s', 1.0))
    import export_web as X
    q = torch.nn.functional.normalize(st['quats'], dim=1)
    qR = torch.tensor(X.rotmat_to_quat(np.array(lev['R'])), dtype=torch.float32)[None].repeat(q.shape[0], 1)
    out = dict(st)
    out['means'] = ((st['means'] - c0) @ R.T * s).contiguous()
    out['quats'] = torch.nn.functional.normalize(X.quat_mul(qR, q), dim=1).contiguous()
    out['scales'] = (st['scales'] + math.log(s)).contiguous()
    return out

def render_top(S, box, px=2000, zmax=None, zmin=None, height=500.0, bg=(1, 1, 1), sh=0):
    x0, y0, x1, y1 = box
    keep = torch.ones(S['means'].shape[0], dtype=torch.bool)
    if zmax is not None: keep &= S['means'][:, 2] < zmax
    if zmin is not None: keep &= S['means'][:, 2] > zmin
    class _S: pass
    s = _S()
    for k in ('means', 'quats', 'scales', 'opac', 'sh'):
        setattr(s, k, S[k][keep].contiguous())
    W = px; H = int(round(px * (y1 - y0) / (x1 - x0)))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    f = (W / 2) / ((x1 - x0) / 2 / height)
    # camera at (cx, cy, height) looking down -z; image x = +x, image y = -y (north up)
    R = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], np.float64)
    C = np.array([cx, cy, height])
    t = -R @ C
    cam = model.Camera(R, t, f, f, W / 2, H / 2, W, H)
    import train
    img = train.render_view(s, cam, sh, torch.tensor(bg, dtype=torch.float32))
    return (img.clamp(0, 1).numpy() * 255).astype(np.uint8)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('ckpt'); ap.add_argument('level'); ap.add_argument('out')
    ap.add_argument('--zmax', type=float, default=None); ap.add_argument('--zmin', type=float, default=None)
    ap.add_argument('--px', type=int, default=2000)
    ap.add_argument('--box', type=float, nargs=4, default=None)
    a = ap.parse_args()
    st = torch.load(a.ckpt)
    lev = json.load(open(a.level))
    S = levelled(st, lev)
    box = a.box or lev['box']
    im = render_top(S, box, a.px, a.zmax, a.zmin)
    Image.fromarray(im).save(a.out)
    print('saved', a.out, im.shape)
