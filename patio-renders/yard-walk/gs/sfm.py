"""Structure from motion for a walk-through video's frames (pycolmap, CPU).

python3 sfm.py FRAMES_DIR WORK_DIR [--overlap 12] [--kf 6] [--mapper global|incremental]
Writes WORK/sparse/0 (raw) and WORK/undist/{images,sparse} (pinhole, ready for train.py).
"""
import os, sys, time, argparse, itertools
import pycolmap


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def run(frames, work, overlap=12, kf=6, mapper='global', max_size=1600, max_feat=6000, cam_model='OPENCV', names=None):
    os.makedirs(work, exist_ok=True)
    db = os.path.join(work, 'database.db')
    names = names or sorted(n for n in os.listdir(frames) if n.lower().endswith(('.jpg', '.jpeg', '.png')))
    if not os.path.exists(db):
        eo = pycolmap.FeatureExtractionOptions()
        eo.max_image_size = max_size
        eo.sift.max_num_features = max_feat
        eo.num_threads = os.cpu_count()
        ro = pycolmap.ImageReaderOptions()
        ro.camera_model = cam_model
        t = time.time()
        pycolmap.extract_features(db, frames, image_names=names, camera_mode=pycolmap.CameraMode.SINGLE,
                                  reader_options=ro, extraction_options=eo)
        log('features %d images in %.0fs' % (len(names), time.time() - t))
        so = pycolmap.SequentialPairingOptions()
        so.overlap = overlap
        so.quadratic_overlap = True
        so.loop_detection = False
        t = time.time()
        pycolmap.match_sequential(db, pairing_options=so)
        log('sequential matching %.0fs' % (time.time() - t))
        # loop closures: every kf-th frame against every other keyframe
        keys = names[::kf]
        idx = {n: i for i, n in enumerate(names)}
        pairs = []
        for a, b in itertools.combinations(keys, 2):
            d = abs(idx[a] - idx[b])
            if d > overlap and not (d & (d - 1) == 0 and d <= 2 ** overlap):  # skip pairs sequential matching already did
                pairs.append((a, b))
        if pairs:
            pf = os.path.join(work, 'kf_pairs.txt')
            with open(pf, 'w') as f:
                f.write('\n'.join('%s %s' % p for p in pairs))
            io = pycolmap.ImportedPairingOptions()
            io.match_list_path = pf
            t = time.time()
            pycolmap.match_image_pairs(db, pairing_options=io)
            log('keyframe matching %d pairs %.0fs' % (len(pairs), time.time() - t))
    sparse = os.path.join(work, 'sparse')
    os.makedirs(sparse, exist_ok=True)
    t = time.time()
    if mapper == 'global':
        recs = pycolmap.global_mapping(db, frames, sparse)
    else:
        recs = pycolmap.incremental_mapping(db, frames, sparse)
    log('mapping (%s) %.0fs: %s' % (mapper, time.time() - t, {k: r.num_reg_images() for k, r in recs.items()}))
    if not recs:
        raise SystemExit('reconstruction failed')
    best = max(recs.values(), key=lambda r: r.num_reg_images())
    out0 = os.path.join(work, 'best')
    os.makedirs(out0, exist_ok=True)
    best.write(out0)
    log(best.summary())
    und = os.path.join(work, 'undist')
    pycolmap.undistort_images(und, out0, frames)
    log('undistorted ->', und)
    return best


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('frames'); ap.add_argument('work')
    ap.add_argument('--overlap', type=int, default=12)
    ap.add_argument('--kf', type=int, default=6)
    ap.add_argument('--mapper', default='global')
    ap.add_argument('--max_size', type=int, default=1600)
    ap.add_argument('--max_feat', type=int, default=6000)
    ap.add_argument('--model', default='OPENCV')
    a = ap.parse_args()
    run(a.frames, a.work, a.overlap, a.kf, a.mapper, a.max_size, a.max_feat, a.model)
