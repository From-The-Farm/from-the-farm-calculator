"""Build the 2D sprinkler plan page (irr/page/index.html) from irr/irrigation.json and the plan geometry."""
import sys, json, math, html
sys.path.insert(0, '../scripts')
import plan as P
from shapely.geometry import box, Polygon, LineString

FT = 0.3048
D = json.load(open('irr/irrigation.json'))
VB = (-7.2, -15.0, 12.4, 14.9)          # view box in plan metres (x0, y0, x1, y1)
S = 34.0                                  # px per metre in the SVG's own units
W = (VB[2] - VB[0]) * S; Hh = (VB[3] - VB[1]) * S
def X(x): return (x - VB[0]) * S
def Y(y): return (VB[3] - y) * S
def pts(coords): return ' '.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in coords)
def poly_path(g):
    out = []
    for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
        out.append('M' + ' L'.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in p.exterior.coords) + 'Z')
        for r in p.interiors:
            out.append('M' + ' L'.join('%.1f,%.1f' % (X(a), Y(b)) for a, b in r.coords) + 'Z')
    return ' '.join(out)
def rect(r):
    x0, y0, x1, y1 = r
    return X(x0), Y(y1), (x1 - x0) * S, (y1 - y0) * S
def sector_path(x, y, R, a0, arc):
    if arc >= 360:
        return 'M%.1f,%.1f m-%.1f,0 a%.1f,%.1f 0 1,0 %.1f,0 a%.1f,%.1f 0 1,0 -%.1f,0' % (X(x), Y(y), R * S, R * S, R * S, 2 * R * S, R * S, R * S, 2 * R * S)
    a1 = a0 + arc
    p0 = (x + R * math.cos(math.radians(a0)), y + R * math.sin(math.radians(a0)))
    p1 = (x + R * math.cos(math.radians(a1)), y + R * math.sin(math.radians(a1)))
    large = 1 if arc > 180 else 0
    # SVG y is flipped, so a counter-clockwise plan arc is clockwise on screen (sweep 0)
    return 'M%.1f,%.1f L%.1f,%.1f A%.1f,%.1f 0 %d,0 %.1f,%.1f Z' % (X(x), Y(y), X(p0[0]), Y(p0[1]), R * S, R * S, large, X(p1[0]), Y(p1[1]))

svg = []
svg.append('<svg class="plan" viewBox="0 0 %.0f %.0f" role="img" aria-labelledby="plan-title plan-desc">' % (W, Hh))
svg.append('<title id="plan-title">Lawn sprinkler plan, north up</title>')
svg.append('<desc id="plan-desc">Plan view of the lawn inside the new walks with 12 sprinkler heads in two zones, their pipes, the valve box and backflow preventer by the east fence, and the tie-in at the capped riser under the planned kitchen counter.</desc>')
svg.append('<defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" class="sleeve-bg"/><line x1="0" y1="0" x2="0" y2="8" class="sleeve-line"/></pattern></defs>')
# context: walk band, pad, lounge, nook, mow strip, lawn
svg.append('<path class="concrete" d="%s"/>' % poly_path(P.BAND))
svg.append('<path class="concrete" d="%s"/>' % poly_path(P.PAD))
svg.append('<path class="pavers" d="%s"/>' % poly_path(P.LOUNGE_OUT))
svg.append('<path class="nook" d="%s"/>' % poly_path(P.NOOK))
svg.append('<path class="concrete" d="%s"/>' % poly_path(P.MOW))
svg.append('<path class="lawn" d="%s"/>' % poly_path(P.LAWN))
x, y, w, h = rect(P.PAVILION); svg.append('<rect class="pavilion" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, y, w, h))
for r in (P.COUNTER_BACK, P.COUNTER_TOP, P.COUNTER_BOT):
    x, y, w, h = rect(r); svg.append('<rect class="counter" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, y, w, h))
x, y, w, h = rect(P.HOT_TUB); svg.append('<rect class="counter" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (x, y, w, h))
# fence along the east side and the planting strip
svg.append('<rect class="strip" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>' % (X(11.2), Y(VB[3]), 0.37 * S, (VB[3] - VB[1]) * S))
svg.append('<line class="fence" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (X(11.57), Y(VB[3]), X(11.57), Y(VB[1])))
# text labels for context
def label(x, y, t, cls='ctx', anchor='middle', rot=None):
    tr = ' transform="rotate(%d %.1f %.1f)"' % (rot, X(x), Y(y)) if rot else ''
    return '<text class="%s" x="%.1f" y="%.1f" text-anchor="%s"%s>%s</text>' % (cls, X(x), Y(y), anchor, tr, html.escape(t))
svg.append(label(4.2, 10.4, 'KITCHEN PAD & PAVILION'))
svg.append(label(-6.6, 11.3, 'SUNKEN LOUNGE', anchor='start'))
svg.append(label(6.0, -10.3, 'DINING NOOK'))
svg.append(label(-0.6, -6.2, 'LAWN  2,431 sq ft', cls='ctx lawnlbl'))
svg.append(label(11.9, 0.5, 'VINYL FENCE', rot=-90))
svg.append(label(10.6, -13.0, 'WALK', rot=-90))
# spray coverage (toggle)
svg.append('<clipPath id="lawnclip"><path d="%s"/></clipPath>' % poly_path(P.LAWN))
svg.append('<g class="spray" clip-path="url(#lawnclip)">')
for hd in D['heads']:
    svg.append('<path class="cov z%d" d="%s"/>' % (hd['zone'], sector_path(hd['x'], hd['y'], hd['R'], hd['a0'], hd['arc'])))
svg.append('</g>')
# sleeves
for s_ in D['sleeves']:
    (a, b), (c, d) = s_['pts'][0], s_['pts'][-1]
    svg.append('<rect class="sleeve" x="%.1f" y="%.1f" width="%.1f" height="%.1f"><title>%s (%s)</title></rect>' % (X(min(a, c)), Y(max(b, d)) - 7, abs(c - a) * S, 14, html.escape(s_['name']), html.escape(s_['size'])))
# pipes
for p in D['pipes']:
    cls = 'pipe %s z%d' % (p['kind'], p['zone']) + (' big' if p['size'].startswith('1"') else '')
    svg.append('<polyline class="%s" points="%s"><title>%s %s, %.1f GPM</title></polyline>' % (cls, pts(p['pts']), html.escape(p['size']), 'mainline' if p['kind'] == 'main' else ('zone %d' % p['zone']), p['gpm']))
# equipment
def sym(x, y, cls, t, w=0.5, h=0.35):
    return '<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2"><title>%s</title></rect>' % (cls, X(x) - w * S / 2, Y(y) - h * S / 2, w * S, h * S, html.escape(t))
svg.append(sym(D['valves']['x'], D['valves']['y'], 'valvebox', 'Valve box: 3 valves (zone 1, zone 2, spare)', 0.34, 0.5))
svg.append(sym(D['pvb']['x'], D['pvb']['y'], 'pvb', 'Pressure vacuum breaker, 12 in above the lawn', 0.26, 0.4))
svg.append('<circle class="poc" cx="%.1f" cy="%.1f" r="7"><title>Tie-in: existing capped riser</title></circle>' % (X(D['poc']['x']), Y(D['poc']['y'])))
for st in D['stubs']:
    svg.append('<circle class="stub" cx="%.1f" cy="%.1f" r="5"><title>%s</title></circle>' % (X(st['x']), Y(st['y']), html.escape(st['note'])))
svg.append('<rect class="ctrl" x="%.1f" y="%.1f" width="10" height="10"><title>Controller on the pavilion post</title></rect>' % (X(D['controller']['x']) - 5, Y(D['controller']['y']) - 5))
# callouts
def callout(x, y, tx, ty, t, anchor='start'):
    return '<g class="callout"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/><text x="%.1f" y="%.1f" text-anchor="%s">%s</text></g>' % (
        X(x), Y(y), X(tx), Y(ty), X(tx) + (4 if anchor == 'start' else -4), Y(ty) + 4, anchor, html.escape(t))
svg.append(callout(D['poc']['x'], D['poc']['y'], 5.2, 13.9, 'TIE-IN: capped riser', 'end'))
svg.append(callout(D['pvb']['x'] - 0.13, D['pvb']['y'], 7.9, 6.05, 'BACKFLOW (PVB) + VALVE BOX', 'end'))
svg.append('<g class="callout"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/></g>' % (X(D['valves']['x'] - 0.17), Y(D['valves']['y']), X(7.9), Y(6.05)))
svg.append(callout(D['stubs'][1]['x'], D['stubs'][1]['y'], 6.4, 2.8, 'existing stub-up', 'end'))
# heads
for hd in D['heads']:
    r = 0.36
    svg.append('<g class="head z%d" data-zone="%d"><path class="hsym" d="%s"/><circle class="hdot" cx="%.1f" cy="%.1f" r="3.2"/>' % (hd['zone'], hd['zone'], sector_path(hd['x'], hd['y'], r, hd['a0'], hd['arc']), X(hd['x']), Y(hd['y'])))
    # label placed opposite the spray direction
    mid = math.radians(hd['a0'] + hd['arc'] / 2) if hd['arc'] < 360 else math.radians(90)
    lx, ly = hd['x'] - 0.75 * math.cos(mid), hd['y'] - 0.75 * math.sin(mid)
    if hd['arc'] >= 360: lx, ly = hd['x'] + 0.55, hd['y'] + 0.45
    svg.append('<text class="hid" x="%.1f" y="%.1f" text-anchor="middle">%s</text></g>' % (X(lx), Y(ly) + 4, hd['id']))
# dimensions for the centre head
c = [h for h in D['heads'] if h['id'] == '2-1'][0]
def dim(x0, y0, x1, y1, t, off=(0, 0)):
    mx, my = (x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1]
    return '<g class="dim"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/><text x="%.1f" y="%.1f" text-anchor="middle">%s</text></g>' % (X(x0), Y(y0), X(x1), Y(y1), X(mx), Y(my) - 4, html.escape(t))
svg.append(dim(c['x'], c['y'], 9.98, c['y'], '22′2″', (0, 0)))
svg.append(dim(c['x'], c['y'], c['x'], 7.547, '28′11″', (0.6, 0)))
# north arrow and scale bar (feet)
nx, ny = -6.4, -12.6
svg.append('<g class="north"><path d="M%.1f,%.1f l7,20 l-7,-6 l-7,6 Z"/><text x="%.1f" y="%.1f" text-anchor="middle">N</text></g>' % (X(nx), Y(ny) - 22, X(nx), Y(ny) + 12))
sx, sy = -6.9, -14.3
svg.append('<g class="scale">')
for k in range(0, 4):
    x0 = sx + k * 5 * FT
    svg.append('<rect x="%.1f" y="%.1f" width="%.1f" height="6" class="%s"/>' % (X(x0), Y(sy) - 6, 5 * FT * S, 'sb1' if k % 2 == 0 else 'sb2'))
    if k < 4: svg.append('<text x="%.1f" y="%.1f" text-anchor="middle">%d</text>' % (X(x0), Y(sy) + 10, k * 5))
svg.append('<text x="%.1f" y="%.1f" text-anchor="middle">20 ft</text>' % (X(sx + 20 * FT), Y(sy) + 10))
svg.append('</g>')
svg.append('</svg>')
SVG = '\n'.join(svg)

# ------------------------------------------------------------------ tables
heads_rows = []
for hd in D['heads']:
    noz = hd['nozzle'].replace('MP3000-90', 'MP3000 90–210°').replace('MP3000-360', 'MP3000 360°').replace('MP3000-210', 'MP3000 210–270°')
    heads_rows.append('<tr class="z%d"><td class="num"><span class="zchip z%d">%s</span></td><td>%s</td><td>%s</td><td class="num">%d°</td><td class="num">%d ft</td><td class="num">%.2f</td></tr>' % (
        hd['zone'], hd['zone'], hd['id'], html.escape(hd['layout']), noz, round(hd['arc']), round(hd['R_ft']), hd['gpm']))
n90 = sum(h['nozzle'] == 'MP3000-90' for h in D['heads']); n360 = sum(h['nozzle'] == 'MP3000-360' for h in D['heads']); n210 = sum(h['nozzle'] == 'MP3000-210' for h in D['heads'])
def lenft(kind, size): return sum(p_['length_m'] for p_ in D['pipes'] if p_['kind'] == kind and p_['size'] == size) / FT
wire_ft = math.hypot(D['valves']['x'] - D['controller']['x'], D['valves']['y'] - D['controller']['y']) / FT + 25
rows = [
    ('Pop-up spray body, 6\u2033, regulated to 40 psi', 'Hunter PROS-06-PRS40 (or Rain Bird 1806-PRS)', '%d' % len(D['heads'])),
    ('Rotary nozzle, 22\u201330 ft, adjustable 90\u2013210\u00b0', 'Hunter MP3000-90 (or Rain Bird R-VAN24)', '%d' % n90),
] + ([('Rotary nozzle, 22\u201330 ft, 210\u2013270\u00b0', 'Hunter MP3000-210', '%d' % n210)] if n210 else []) + [
    ('Rotary nozzle, 22\u201330 ft, full circle', 'Hunter MP3000-360 (or Rain Bird R-VAN24-360)', '%d' % n360),
    ('Swing pipe, \u00bd\u2033, with barbed elbows', '12\u201318\u2033 per head', '%d' % len(D['heads'])),
    ('Valve, 1\u2033', 'Hunter PGV-101G (or Rain Bird 100-DV)', '3'),
    ('Valve box, standard rectangular', 'Fits 3 valves side by side', '1'),
    ('Pressure vacuum breaker, 1\u2033', 'Febco 765-1 or Wilkins 720A; check your local code', '1'),
    ('Shut-off ball valve, 1\u2033', 'At the tie-in', '1'),
    ('Mainline, 1\u2033 Sch 40 PVC', 'Riser to PVB to valves', '%.0f ft' % lenft('main', '1" Sch 40')),
    ('Zone pipe, 1\u2033 Class 200 PVC', 'First runs from the valves', '%.0f ft' % lenft('lateral', '1"')),
    ('Zone pipe, \u00be\u2033 Class 200 PVC', 'Rest of both zones', '%.0f ft' % lenft('lateral', '3/4"')),
    ('Sleeve, 2\u2033 Sch 40 PVC', 'Mainline under the pad and east walk', '%.0f ft' % (D['sleeves'][0]['length_m'] / FT + 2)),
    ('Sleeve, 3\u2033 Sch 40 PVC', 'Zone pipes and wire under the east walk', '%.0f ft' % (D['sleeves'][1]['length_m'] / FT + 2)),
    ('Valve wire, 18 AWG 5-conductor, direct burial', 'Plus waterproof wire connectors', '%.0f ft' % wire_ft),
    ('Smart controller, Wi-Fi, weather-based, 4+ zones', 'Hunter Hydrawise HC or Rachio 3', '1'),
]
mat_rows = ''.join('<tr><td>%s</td><td>%s</td><td class="num">%s</td></tr>' % (html.escape(a), html.escape(b), html.escape(c)) for a, b, c in rows)
z1, z2 = D['zones']
lp = [p for p in D['pipes'] if p['kind'] == 'lateral']
len_ft = lambda kind, size: sum(p['length_m'] for p in D['pipes'] if p['kind'] == kind and p['size'] == size) / FT
pb = D['pressure']

T = open('irr/page_template.html').read()
out = T.replace('{{SVG}}', SVG)
out = out.replace('{{HEAD_ROWS}}', '\n'.join(heads_rows)).replace('{{MAT_ROWS}}', mat_rows)
out = out.replace('{{Z1GPM}}', '%.1f' % z1['gpm']).replace('{{Z2GPM}}', '%.1f' % z2['gpm']).replace('{{TOTALGPM}}', '%.1f' % (z1['gpm'] + z2['gpm']))
out = out.replace('{{DU}}', '%.2f' % D['sim']['du_lq']).replace('{{OVER}}', '%.0f' % D['sim']['overspray_pct'])
out = out.replace('{{MAIN_FT}}', '%.0f' % len_ft('main', '1" Sch 40')).replace('{{LAT1_FT}}', '%.0f' % len_ft('lateral', '1"')).replace('{{LAT34_FT}}', '%.0f' % len_ft('lateral', '3/4"'))
out = out.replace('{{NEED_PSI}}', '%.0f' % pb['needed_static_psi']).replace('{{SQFT}}', '{:,}'.format(D['lawn_sqft']))
open('irr/page/index.html', 'w').write(out)
print('page written', len(out) // 1024, 'KB')
