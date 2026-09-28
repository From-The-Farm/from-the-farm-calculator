"""Plan outlines on the orthophoto. sim: plan metres -> levelled units: p_l = s R(theta) p + t.
python3 align/overlay2.py ORTHO.png ORTHO.json SIM.json OUT.jpg [crop x0 y0 x1 y1]"""
import sys, json, math, numpy as np
sys.path.insert(0, '../scripts')
from PIL import Image, ImageDraw
import plan as P

def to_level(pts, sim):
    s, th, tx, ty = sim['s'], sim['theta'], sim['tx'], sim['ty']
    c, sn = math.cos(th), math.sin(th)
    pts = np.asarray(pts, float)
    return np.c_[s * (c * pts[:, 0] - sn * pts[:, 1]) + tx, s * (sn * pts[:, 0] + c * pts[:, 1]) + ty]

def main():
    img, meta, simf, out = sys.argv[1:5]
    m = json.load(open(meta)); sim = json.load(open(simf))
    x0, y0, x1, y1 = m['box']; cell = m['cell']
    im = Image.open(img).convert('RGB'); dr = ImageDraw.Draw(im)
    def px(q): return [((x - x0) / cell, (y1 - y) / cell) for x, y in q]
    shapes = [('OUTER', P.OUTER, (255, 255, 255)), ('INNER', P.INNER, (220, 220, 220)), ('LOUNGE_OUT', P.LOUNGE_OUT, (255, 0, 160)),
              ('PAVILION', P.PAVILION, (0, 200, 255)), ('NOOK', P.NOOK, (255, 220, 0)), ('HOT_TUB', None, (255, 60, 60))]
    from shapely.geometry import box as sbox
    for k, g, col in shapes:
        if k == 'PAVILION': g = sbox(*P.PAVILION)
        if k == 'HOT_TUB': g = sbox(*P.HOT_TUB)
        geoms = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        for p in geoms:
            ring = to_level(np.array(p.exterior.coords), sim)
            dr.line(px(ring), fill=col, width=2)
    # 1 m grid ticks every 2 m
    for gx in range(int(x0), int(x1) + 1, 2):
        dr.line(px([(gx, y0), (gx, y1)]), fill=(90, 130, 255) if gx % 10 else (0, 60, 255), width=1)
        dr.text((px([(gx, 0)])[0][0] + 2, 3), str(gx), fill=(0, 0, 140))
    for gy in range(int(y0), int(y1) + 1, 2):
        dr.line(px([(x0, gy), (x1, gy)]), fill=(90, 130, 255) if gy % 10 else (0, 60, 255), width=1)
        dr.text((3, px([(0, gy)])[0][1] + 2), str(gy), fill=(0, 0, 140))
    if len(sys.argv) > 5:
        cx0, cy0, cx1, cy1 = map(float, sys.argv[5:9])
        a = px([(cx0, cy1)])[0]; b = px([(cx1, cy0)])[0]
        im = im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1])))
    im.save(out, quality=90)
main()
