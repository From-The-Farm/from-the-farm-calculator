import os, sys, time, sqlite3, pycolmap
db_path = sys.argv[1]
c = sqlite3.connect(db_path)
ims = {iid: name for iid, name in c.execute('select image_id, name from images')}
pairs = []
for (pid,) in c.execute('select pair_id from matches where rows > 0'):
    i2 = pid % 2147483647; i1 = (pid - i2) // 2147483647
    pairs.append((ims[int(i1)], ims[int(i2)]))
c.execute('delete from two_view_geometries'); c.commit(); c.close()
pf = os.path.join(os.path.dirname(db_path), 'all_pairs.txt')
open(pf, 'w').write('\n'.join('%s %s' % p for p in pairs))
o = pycolmap.TwoViewGeometryOptions()
o.compute_relative_pose = True
t = time.time()
pycolmap.verify_matches(db_path, pf, o)
print('verified', len(pairs), 'pairs in %.0fs' % (time.time() - t), flush=True)
c = sqlite3.connect(db_path)
import collections
print('configs', dict(collections.Counter(r[0] for r in c.execute('select config from two_view_geometries'))))
