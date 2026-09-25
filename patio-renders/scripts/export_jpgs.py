"""Convert the PNG renders to the numbered JPEGs in ../renders (python3 export_jpgs.py [png_dir])."""
import os, sys
from PIL import Image

NAMES = {
    'aerial_se': '01-overview-southeast',
    'lawn_north': '02-lawn-to-pavilion',
    'lounge': '03-lounge',
    'hottub': '04-hot-tub',
    'kitchen': '05-outdoor-kitchen',
    'pavilion_out': '06-from-the-pavilion',
    'nook': '07-dining-nook',
    'walk_west': '08-west-walk',
    'aerial_nw': '09-overview-northwest',
    'lawn_north_dusk': '10-lawn-dusk',
    'lounge_dusk': '11-lounge-dusk',
    'top': '12-top-roof-on',
    'top_noroof': '13-top-roof-off',
}

here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'renders', 'png')
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, '..', 'renders')
os.makedirs(dst, exist_ok=True)
for key, name in NAMES.items():
    p = os.path.join(src, key + '.png')
    if not os.path.exists(p):
        print('missing', p)
        continue
    im = Image.open(p).convert('RGB')
    out = os.path.join(dst, name + '.jpg')
    im.save(out, 'JPEG', quality=90, optimize=True, progressive=True, subsampling=0)
    print('wrote', out, os.path.getsize(out) // 1024, 'KB')
