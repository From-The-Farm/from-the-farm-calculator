"""Single-view metrology: fence height vs camera height at a post; compare with SfM camera height -> scale k."""
import sys, json, numpy as np, pycolmap
from scipy.spatial import cKDTree
lev = json.load(open('align/level_g2.json')); S = lev['s']; RL = np.array(lev['R']); c0 = np.array(lev['c0'])
rec = pycolmap.Reconstruction('real/sfm_g2/undist/sparse')
cam = list(rec.cameras.values())[0]; fx, fy, cx, cy = cam.params[:4]
X = np.array([p.xyz for p in rec.points3D.values()]); err = np.array([p.error for p in rec.points3D.values()]); tl = np.array([p.track.length() for p in rec.points3D.values()])
L = (S * X - S * c0) @ RL.T; L = L[(err < 1.5) & (tl >= 3)]
tree = cKDTree(L[:, :2])
def run(name, u, v_top, v_bot, H=1.85):
    im = [i for i in rec.images.values() if i.name == name][0]
    Rt = np.asarray((im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world).matrix())
    R = Rt[:, :3]; C = -R.T @ Rt[:, 3]
    Cl = RL @ (S * C - S * c0)
    def elev(uu, vv):
        r = RL @ (R.T @ np.array([(uu - cx) / fx, (vv - cy) / fy, 1.0]))
        return np.arcsin(r[2] / np.linalg.norm(r)), r
    et, rt = elev(u, v_top); eb, rb = elev(u, v_bot)
    ratio = np.tan(et) / np.tan(-eb)
    h_m = H / (1 + ratio)
    # SfM camera height above ground near the post base: intersect bottom ray with local ground
    idx = tree.query_ball_point(Cl[:2], 1.0)
    zg = np.percentile(L[idx, 2], 30) if len(idx) > 10 else np.nan
    h_u = Cl[2] - zg
    D = h_u / np.tan(-eb)
    print('%s u=%d top %.1f bot %.1f: elev_top %.2f deg, dep_bot %.2f deg, H/h = %.3f -> cam height %.2f m (fence %.2f m); SfM cam height %.2f units (n=%d); horiz dist to post %.2f units; k = %.3f' % (
        name, u, v_top, v_bot, np.degrees(et), -np.degrees(eb), 1 + ratio, h_m, H, h_u, len(idx), D, h_m / h_u))
    return h_m / h_u
if __name__ == '__main__':
    a = sys.argv[1:]
    run(a[0], float(a[1]), float(a[2]), float(a[3]))
