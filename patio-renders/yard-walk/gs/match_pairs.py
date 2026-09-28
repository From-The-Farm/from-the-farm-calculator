import sys, time, sqlite3, collections, pycolmap
db, pf = sys.argv[1], sys.argv[2]
io = pycolmap.ImportedPairingOptions(); io.match_list_path = pf
vo = pycolmap.TwoViewGeometryOptions(); vo.compute_relative_pose = True
t = time.time()
pycolmap.match_image_pairs(db, pairing_options=io, verification_options=vo)
c = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
print('matched in %.0fs' % (time.time() - t), 'tvg', c.execute('select count(*), sum(rows>=15) from two_view_geometries').fetchone(),
      'configs', dict(collections.Counter(r[0] for r in c.execute('select config from two_view_geometries where rows>=15'))), flush=True)
