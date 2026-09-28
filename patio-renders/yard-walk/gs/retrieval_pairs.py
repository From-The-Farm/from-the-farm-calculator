"""VLAD retrieval over the database's SIFT descriptors -> extra image pairs to match (loop closures)."""
import sys, os, time, numpy as np, pycolmap, sqlite3
db_path, out, topk = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 25
t0 = time.time()
db = pycolmap.Database.open(db_path)
ims = sorted(db.read_all_images(), key=lambda im: im.name)
desc = []
for im in ims:
    d = np.asarray(db.read_descriptors(im.image_id).data, dtype=np.float32)
    d = np.sqrt(d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9))   # RootSIFT-ish
    desc.append(d)
print('descriptors loaded %.0fs' % (time.time() - t0), flush=True)
rng = np.random.default_rng(0)
sample = np.concatenate([d[rng.choice(len(d), min(len(d), 400), replace=False)] for d in desc])
K = 64
from scipy.cluster.vq import kmeans2
cent, _ = kmeans2(sample, K, iter=20, minit='++', seed=1)
print('kmeans %.0fs' % (time.time() - t0), flush=True)
V = np.zeros((len(ims), K * 128), np.float32)
cn = (cent ** 2).sum(1)
for i, d in enumerate(desc):
    dist = cn[None] - 2 * d @ cent.T
    a = dist.argmin(1)
    v = np.zeros((K, 128), np.float32)
    np.add.at(v, a, d - cent[a])
    v = np.sign(v) * np.sqrt(np.abs(v))
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9    # intra-normalisation
    v = v.ravel(); V[i] = v / (np.linalg.norm(v) + 1e-9)
S = V @ V.T
names = [im.name for im in ims]
fid = np.array([int(n[1:5]) for n in names])
# existing verified pairs
c = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)
id2name = {im.image_id: im.name for im in ims}
have = set()
for pid, rows in c.execute('select pair_id, rows from two_view_geometries'):
    i2 = pid % 2147483647; i1 = (pid - i2) // 2147483647
    have.add(frozenset((id2name[int(i1)], id2name[int(i2)])))
pairs = set()
for i in range(len(ims)):
    order = np.argsort(-S[i])
    k = 0
    for j in order:
        if j == i or abs(fid[i] - fid[j]) <= 2: continue
        key = frozenset((names[i], names[j]))
        if key not in have: pairs.add(key)
        k += 1
        if k >= topk: break
pairs = sorted(tuple(sorted(p)) for p in pairs)
open(out, 'w').write('\n'.join('%s %s' % p for p in pairs))
print('pairs', len(pairs), 'time %.0fs' % (time.time() - t0), flush=True)
