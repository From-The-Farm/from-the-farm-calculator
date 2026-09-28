"""Render splat depth at a training view (full undistorted res) and back-project picked pixels to the levelled metric frame.
python3 align/depth_pick.py CKPT FRAME.jpg u,v [u,v ...]"""
import os, sys, json, math
os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
import numpy as np, torch, pycolmap
sys.path.insert(0, 'gs')
import model
ck, name = sys.argv[1], sys.argv[2]
pts = [tuple(map(float, a.split(','))) for a in sys.argv[3:]]
S = 3.19
lev = json.load(open('align/level_g2m.json')); RL = np.array(lev['R']); c0 = np.array(lev['c0'])
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
im = [i for i in rec.images.values() if i.name == name][0]
c = rec.cameras[im.camera_id]; fx, fy, cx, cy = c.params[:4]; W, H = c.width, c.height
Rt = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
R, t = Rt[:, :3], Rt[:, 3] * S
cam = model.Camera(R, t, fx, fy, cx, cy, W, H)
st = torch.load(ck, map_location='cpu')
E = model.ext()
means = st['means'].contiguous(); quats = st['quats'].contiguous(); scales = st['scales'].contiguous(); opac = st['opac'].contiguous()
m2, co, dp, ex, op = E.project_forward(means, quats, scales, opac, cam.R, cam.t, cam.fx, cam.fy, cam.cx, cam.cy, W, H, 0.1, 0.3)
vis = torch.nonzero(ex[:, 0] > 0).squeeze(1); vis = vis[torch.argsort(dp[vis])]
offsets, ids = E.bin_gaussians(m2[vis].contiguous(), ex[vis].contiguous(), torch.arange(vis.numel()), W, H)
img, fT = E.render_depth(m2[vis].contiguous(), co[vis].contiguous(), dp[vis].contiguous(), op[vis].contiguous(), offsets, ids, W, H)
img = img.numpy()
D = img[..., 0] / np.maximum(img[..., 1], 1e-6)
np.save('align/depth_%s.npy' % name[:-4], D.astype(np.float32))
Rw = R.T
out = []
for (u, v) in pts:
    ui, vi = int(round(u)), int(round(v))
    win = D[max(vi - 1, 0):vi + 2, max(ui - 1, 0):ui + 2]
    d = float(np.median(win)); a = float(img[vi, ui, 1])
    Xc = np.array([(u - cx) / fx * d, (v - cy) / fy * d, d])
    Xw = Rw @ (Xc - t)
    Lp = RL @ (Xw - c0)
    out.append(Lp)
    print('px (%6.1f,%6.1f) depth %.2f alpha %.2f -> levelled (%6.2f,%6.2f,%5.2f)' % (u, v, d, a, *Lp))
out = np.array(out)
if len(out) > 1:
    print('consecutive distances:', np.linalg.norm(np.diff(out, axis=0), axis=1).round(3))
