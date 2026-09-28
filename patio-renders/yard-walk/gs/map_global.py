import os, sys, time, pycolmap, numpy as np
db, frames, work = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(work, exist_ok=True)
t = time.time()
recs = pycolmap.global_mapping(db, frames, work)
print('global %.0fs' % (time.time() - t), {k: r.num_reg_images() for k, r in recs.items()}, flush=True)
best = max(recs.values(), key=lambda r: r.num_reg_images())
out = os.path.join(work, 'best'); os.makedirs(out, exist_ok=True); best.write(out)
print(best.summary(), flush=True)
# trajectory sanity: step lengths between consecutive frames
C = {}
for im in best.images.values():
    pose = im.cam_from_world() if callable(getattr(im, 'cam_from_world', None)) else im.cam_from_world
    M = np.asarray(pose.matrix()); C[int(im.name[1:5])] = -M[:, :3].T @ M[:, 3]
ks = sorted(C); steps = [np.linalg.norm(C[b] - C[a]) for a, b in zip(ks, ks[1:]) if b == a + 1]
print('consecutive step pct', np.percentile(steps, [5, 25, 50, 75, 95, 99]).round(4), 'extent', np.ptp(np.array([C[k] for k in ks]), 0).round(2), flush=True)
