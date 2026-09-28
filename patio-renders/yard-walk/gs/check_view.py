import os, sys
os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
import numpy as np, torch
sys.path.insert(0, 'gs')
import train, model
from PIL import Image
torch.set_num_threads(2)
views, pts = train.load_colmap(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else 960, float(os.environ.get('SCALE', 1.0)))
st = torch.load(sys.argv[2])
class S_: pass
S = S_()
for k, v in st.items(): setattr(S, k, v)
rows = []
for i in [10, 100, 200, 300, 420, 520]:
    v = views[i]
    gt8, cam = v.level(1)
    im = train.render_view(S, cam, 3, torch.zeros(3))
    p = train.psnr(im, gt8.float() / 255)
    a = (im.clamp(0, 1).numpy() * 255).astype(np.uint8)
    rows.append(np.concatenate([gt8.numpy(), a], 1))
    print(v.name, 'psnr %.2f' % p)
Image.fromarray(np.concatenate(rows, 0)).resize((960, 273 * len(rows))).save(sys.argv[4] if len(sys.argv) > 4 else 'align/check.jpg')
