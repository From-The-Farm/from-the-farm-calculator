import sys, json, math, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, 'irr')
import layout as LY

def draw(real, ev, out, title='', pipes=None, zones=None, scale=40):
    W = ev['W']; mean = W[LY.INSIDE].mean()
    x0, y0 = LY._xs[0] - LY._cell / 2, LY._ys[0] - LY._cell / 2
    H, Wd = W.shape
    img = np.zeros((H, Wd, 3), np.uint8) + 235
    v = np.clip(W / mean, 0, 2)
    # diverging: dry (orange) -> ok (white) -> wet (blue); only on the lawn
    col = np.zeros((H, Wd, 3))
    t = np.clip((v - 1.0), -1, 1)
    col[..., 0] = np.where(t < 0, 255, 255 * (1 - t) + 40 * t)
    col[..., 1] = np.where(t < 0, 255 * (1 + t) + 140 * (-t), 255 * (1 - t) + 110 * t)
    col[..., 2] = np.where(t < 0, 255 * (1 + t) + 40 * (-t), 255 * (1 - t) + 200 * t)
    img[LY.INSIDE] = col[LY.INSIDE].astype(np.uint8)
    img = img[::-1]                                             # north up
    im = Image.fromarray(img).resize((Wd * scale // 5, H * scale // 5), Image.NEAREST)
    d = ImageDraw.Draw(im); s = scale / 5 / LY._cell
    P = lambda x, y: ((x - x0) * s, (LY._ys[-1] + LY._cell / 2 - y) * s)
    d.line([P(*c) for c in LY.LAWN.exterior.coords], fill=(20, 90, 20), width=2)
    for i, h in enumerate(real):
        px, py = P(h['x'], h['y'])
        if h['arc'] < 360:
            a0 = -(h['a0'] + h['arc']); a1 = -h['a0']
            r = h['R'] * s
            d.arc((px - r, py - r, px + r, py + r), a0, a1, fill=(90, 90, 200), width=1)
            for a in (h['a0'], h['a0'] + h['arc']):
                d.line([(px, py), (px + r * math.cos(math.radians(a)), py - r * math.sin(math.radians(a)))], fill=(150, 150, 220), width=1)
        else:
            r = h['R'] * s; d.ellipse((px - r, py - r, px + r, py + r), outline=(150, 150, 220), width=1)
        colz = (0, 0, 0) if zones is None else [(200, 30, 30), (30, 90, 220), (20, 150, 60), (150, 60, 170)][zones[i]]
        d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=colz)
        d.text((px + 6, py - 6), str(i), fill=(0, 0, 0))
    if pipes:
        for pp in pipes:
            d.line([P(*q) for q in pp['pts']], fill=tuple(pp.get('rgb', (0, 0, 0))), width=3)
    d.text((6, 6), title, fill=(0, 0, 0))
    im.save(out)
    return im.size

if __name__ == '__main__':
    cands = json.load(open('irr/candidates.json'))
    for c in cands:
        S = c['S_ft'] * LY.FT
        real = LY.realize(c['heads'], S * 1.02); ev = LY.evaluate(real)
        draw(real, ev, 'irr/cand_%d.png' % c['S_ft'], 'S=%d ft  heads %d  DU %.2f' % (c['S_ft'], len(real), ev['du']))
