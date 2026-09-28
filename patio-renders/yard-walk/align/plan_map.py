"""Draw plan outlines + grid + camera path + extra polylines on the plan-frame orthophoto."""
import sys, json, numpy as np
sys.path.insert(0, '../scripts'); sys.path.insert(0, 'align')
from PIL import Image, ImageDraw
from shapely.geometry import box as sbox
import plan as P, frames as F
def draw(img_path, out, extra=None, crop=None, scale=1, cams=True, step=2):
    m = json.load(open(img_path.replace('.png', '.json'))); x0, y0, x1, y1 = m['box']; cell = m['cell']
    im = Image.open(img_path).convert('RGB')
    if scale != 1: im = im.resize((im.size[0] * scale, im.size[1] * scale), Image.LANCZOS)
    c = cell / scale; d = ImageDraw.Draw(im)
    px = lambda q: [((x - x0) / c, (y1 - y) / c) for x, y in q]
    for gx in range(int(np.ceil(x0)), int(x1) + 1, step):
        d.line(px([(gx, y0), (gx, y1)]), fill=(70, 110, 255) if gx % 10 else (0, 40, 255), width=1); d.text((px([(gx, 0)])[0][0] + 2, 3), str(gx), fill=(0, 0, 140))
    for gy in range(int(np.ceil(y0)), int(y1) + 1, step):
        d.line(px([(x0, gy), (x1, gy)]), fill=(70, 110, 255) if gy % 10 else (0, 40, 255), width=1); d.text((3, px([(0, gy)])[0][1] + 2), str(gy), fill=(0, 0, 140))
    for g, col in [(P.OUTER, (255, 255, 255)), (P.INNER, (220, 220, 220)), (P.LOUNGE_OUT, (255, 0, 170)), (sbox(*P.PAVILION), (0, 210, 255)), (P.NOOK, (255, 220, 0))]:
        for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
            d.line(px(list(p.exterior.coords)), fill=col, width=2)
    if cams:
        cd = np.load('align/camdirs.npy', allow_pickle=True).item()
        for k in sorted(cd):
            C = F.lev2plan(np.array(cd[k][0])[None])[0]
            q = px([C[:2]])[0]
            d.ellipse((q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2), fill=(255, 0, 255))
            if k % 20 == 0: d.text((q[0] + 3, q[1] - 10), str(k), fill=(255, 0, 255))
    for name, pts, col in (extra or []):
        d.line(px(pts), fill=col, width=3); d.text(px([pts[0]])[0], name, fill=col)
    if crop:
        a = px([(crop[0], crop[3])])[0]; b = px([(crop[2], crop[1])])[0]; im = im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1])))
    im.save(out, quality=90); return im.size
if __name__ == '__main__':
    print(draw(sys.argv[1], sys.argv[2]))
