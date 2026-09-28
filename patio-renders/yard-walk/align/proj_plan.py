"""Project plan outlines (on the reconstructed ground) into video frames to check the alignment."""
import sys, json, math, numpy as np, pycolmap
sys.path.insert(0, '../scripts')
from PIL import Image, ImageDraw
from shapely.geometry import box as sbox
from scipy.spatial import cKDTree
import plan as P
S = 3.19
lev = json.load(open('align/level_g2.json')); RL = np.array(lev['R']); c0 = np.array(lev['c0'])   # SfM units
sim = json.load(open(sys.argv[1])); frames = sys.argv[3:]; out = sys.argv[2]
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
cam = list(rec.cameras.values())[0]; fx, fy, cx, cy = cam.params[:4]; W, H = cam.width, cam.height
X = np.array([p.xyz for p in rec.points3D.values()]); err = np.array([p.error for p in rec.points3D.values()]); tl = np.array([p.track.length() for p in rec.points3D.values()])
Lp = (S * X - S * c0) @ RL.T; Lp = Lp[(err < 1.5) & (tl >= 3)]
tree = cKDTree(Lp[:, :2])
def ground(xy):
    idx = tree.query_ball_point(xy, 1.0)
    return np.percentile(Lp[idx, 2], 25) if len(idx) > 8 else 0.0
def to_level(pts):
    s, th, tx, ty = sim['s'], sim['theta'], sim['tx'], sim['ty']
    c, sn = math.cos(th), math.sin(th); pts = np.asarray(pts, float)
    return np.c_[s * (c * pts[:, 0] - sn * pts[:, 1]) + tx, s * (sn * pts[:, 0] + c * pts[:, 1]) + ty]
def dens(ring, step=0.3):
    o = [ring[0]]
    for a, b in zip(ring[:-1], ring[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for i in range(1, n + 1): o.append(a + (b - a) * i / n)
    return np.array(o)
shapes = [(P.OUTER, (255, 255, 255)), (P.INNER, (230, 230, 230)), (P.LOUNGE_OUT, (255, 0, 170)), (sbox(*P.PAVILION), (0, 210, 255)), (P.NOOK, (255, 220, 0))]
rings = []
for g, col in shapes:
    for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
        r = dens(np.array(p.exterior.coords))
        L2 = to_level(r)
        Z = np.array([ground(q) for q in L2]) + 0.02
        L3 = np.c_[L2, Z]
        Wd = (L3 @ RL) / S + c0            # back to SfM world
        rings.append((Wd, col))
tiles = []
for name in frames:
    im = [i for i in rec.images.values() if i.name == name][0]
    Rt = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
    R, t = Rt[:, :3], Rt[:, 3]
    img = Image.open('real/sfm_g2/undist/images/' + name).convert('RGB'); d = ImageDraw.Draw(img)
    for Wd, col in rings:
        Pc = Wd @ R.T + t
        seg = []
        for q in Pc:
            if q[2] > 0.05:
                seg.append((fx * q[0] / q[2] + cx, fy * q[1] / q[2] + cy))
            else:
                if len(seg) > 1: d.line(seg, fill=col, width=3)
                seg = []
        if len(seg) > 1: d.line(seg, fill=col, width=3)
    d.rectangle((0, 0, 90, 24), fill=(0, 0, 0)); d.text((6, 6), name, fill=(255, 255, 0))
    img.thumbnail((774, 440)); tiles.append(img)
cols = 2; rows = (len(tiles) + 1) // 2
sheet = Image.new('RGB', (774 * cols, 440 * rows))
for i, t_ in enumerate(tiles): sheet.paste(t_, ((i % cols) * 774, (i // cols) * 440))
sheet.save(out, quality=88); print(sheet.size)
