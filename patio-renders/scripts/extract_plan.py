import pymupdf, json, collections
import sys
doc = pymupdf.open(sys.argv[1] if len(sys.argv) > 1 else 'plan.pdf')
out = {}
for pi, page in enumerate(doc):
    ds = page.get_drawings()
    recs = []
    for d in ds:
        items = []
        for it in d['items']:
            kind = it[0]
            if kind == 'l':
                items.append(['l', [it[1].x, it[1].y], [it[2].x, it[2].y]])
            elif kind == 'c':
                items.append(['c', [it[1].x, it[1].y], [it[2].x, it[2].y], [it[3].x, it[3].y], [it[4].x, it[4].y]])
            elif kind == 're':
                r = it[1]; items.append(['re', [r.x0, r.y0, r.x1, r.y1]])
            elif kind == 'qu':
                q = it[1]; items.append(['qu', [[q.ul.x,q.ul.y],[q.ur.x,q.ur.y],[q.lr.x,q.lr.y],[q.ll.x,q.ll.y]]])
        recs.append({'type': d.get('type'), 'color': d.get('color'), 'fill': d.get('fill'), 'width': d.get('width'),
                     'rect': [d['rect'].x0, d['rect'].y0, d['rect'].x1, d['rect'].y1], 'items': items, 'closePath': d.get('closePath'), 'dashes': d.get('dashes')})
    out[pi] = recs
    c = collections.Counter((r['type'], str(r['color']), str(r['fill']), round(r['width'] or 0, 3), r['dashes']) for r in recs)
    print('PAGE', pi)
    for k, v in c.most_common():
        print('  ', v, k)
json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else 'drawings.json', 'w'))
