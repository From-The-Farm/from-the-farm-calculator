"""Zones, valve manifold, point of connection, trenches, pipe sizing, friction and materials for the lawn sprinklers.
Writes irr/irrigation.json (viewer + plan page)."""
import sys, json, math
import numpy as np
sys.path.insert(0, 'irr'); sys.path.insert(0, '../scripts')
import layout as LY
import plan as P
from shapely.geometry import Point, LineString, box, Polygon
from shapely.ops import substring

FT = LY.FT
d = json.load(open('irr/final_heads.json'))
H = d['heads']
LAWN = LY.LAWN
RING_IN = LAWN.buffer(-0.30, join_style=2).exterior          # laterals run 12" inside the lawn edge
L_IN = RING_IN.length

# ------------------------------------------------------------------ zones and ids (see notes in the plan page)
Z1 = [7, 6, 5, 4, 3, 8]       # north: NE corner, north edge, pad SW corner, lounge notch, west edge (north), east edge (middle)
Z2 = [11, 9, 10, 0, 1, 2]     # south: centre, SE corner, curve, south point, SW corner, west edge (middle)
NAMES = {7: 'NE corner (east walk / kitchen pad)', 6: 'North edge, along the kitchen pad', 5: 'Kitchen pad SW corner',
         4: 'Inside corner by the lounge', 3: 'West edge, north end', 8: 'East edge, middle',
         11: 'Centre of the lawn', 9: 'SE corner (east walk / mow strip)', 10: 'On the mow-strip curve',
         0: 'South point (mow strip / SW walk)', 1: 'SW corner', 2: 'West edge, middle'}
heads = []
for z, ids in ((1, Z1), (2, Z2)):
    for k, i in enumerate(ids):
        h = dict(H[i]); h['id'] = '%d-%d' % (z, k + 1); h['zone'] = z; h['src'] = i
        R_ft = h['R'] / FT
        h['R_ft'] = round(R_ft, 1)
        h['nozzle'] = 'MP3000-360' if h['arc'] >= 360 else ('MP3000-210' if h['arc'] > 210 else 'MP3000-90')   # 90-210 / 210-270 / 360 families
        h['gpm'] = round(LY.gpm(h['R'], h['arc']), 2)
        h['where'] = NAMES[i]
        heads.append(h)
byid = {h['src']: h for h in heads}

# ------------------------------------------------------------------ fixed points
POC = (8.90, 11.30)          # capped riser seen in the video (under the future kitchen back counter) - to be confirmed as live water
DRAIN_STUB = (8.70, 10.52)   # tall white PVC stub at the planned sink (likely its drain) - leave for the kitchen
STUB_B = (9.25, 4.20)        # white PVC stub-up + coil of black poly inside the future lawn
STRIP_X = 11.40              # planting strip between the east walk (x 11.20) and the vinyl fence (x ~11.57)
PVB = (STRIP_X, 8.40)
VALVES = (STRIP_X, 7.05)
ENTRY = (9.70, 7.05)          # laterals come out from under the east walk here
CONTROLLER = (9.05, 8.01)    # on the pavilion's SE post by the kitchen (the kitchen brings power there)

def ring_pos(pt):
    return RING_IN.project(Point(*pt))
def ring_path(s0, s1, forward=True):
    """Sub-path of the inner ring from s0 to s1 (going forward = increasing arc length, wrapping)."""
    if not forward: return ring_path(s1, s0, True)[::-1]
    if s1 >= s0: return list(substring(RING_IN, s0, s1).coords)
    return list(substring(RING_IN, s0, L_IN).coords) + list(substring(RING_IN, 0, s1).coords)[1:]

def near_ring(h):
    return ring_pos((h['x'], h['y']))

# ------------------------------------------------------------------ trenches / pipes
pipes = []   # dict(kind, zone, size, gpm, pts)
def add(kind, zone, pts, flow, size=None, note=''):
    pts = [tuple(map(float, p)) for p in pts]
    if size is None: size = '1"' if flow > 6.0 else '3/4"'
    pipes.append(dict(kind=kind, zone=zone, size=size, gpm=round(flow, 2), pts=pts, note=note,
                      length_m=float(LineString(pts).length)))

# mainline (always pressurised): riser -> under the pad & east walk (sleeve) -> strip -> PVB -> valve box
add('main', 0, [POC, (9.70, POC[1]), (STRIP_X, POC[1]), PVB], 8.0, '1" Sch 40', 'from the kitchen riser, sleeved under the new pad and walk')
add('main', 0, [PVB, VALVES], 8.0, '1" Sch 40')
# zone supply under the east walk (both zones in one 3" sleeve)
e_s = ring_pos(ENTRY)
q = RING_IN.interpolate(e_s); ENTRY_RING = (q.x, q.y)
z1flow = sum(h['gpm'] for h in heads if h['zone'] == 1); z2flow = sum(h['gpm'] for h in heads if h['zone'] == 2)
add('lateral', 1, [(VALVES[0], VALVES[1] + 0.05), (ENTRY[0], ENTRY[1] + 0.05), ENTRY_RING], z1flow, '1"')
add('lateral', 2, [(VALVES[0], VALVES[1] - 0.05), (ENTRY[0], ENTRY[1] - 0.05), ENTRY_RING], z2flow, '1"')

# zone 1: north run (counter-clockwise from the NE corner: 7 -> 6 -> 5 -> 4 -> 3) and east run to head 8
north = [7, 6, 5, 4, 3]
flow = sum(byid[i]['gpm'] for i in north)
s_prev = e_s
for i in north:
    s_h = near_ring(byid[i])
    path = ring_path(s_h, s_prev, True)[::-1]            # going backwards along the ring (decreasing s)
    if len(path) > 1: add('lateral', 1, path, flow)
    flow -= byid[i]['gpm']; s_prev = s_h
# east run for zone 1 (head 8): offset 0.12 m further in so the two zone pipes share one trench side by side
def offset_path(pts, off):
    ls = LineString(pts)
    o = ls.offset_curve(off, join_style=2) if hasattr(ls, 'offset_curve') else ls.parallel_offset(off, 'left', join_style=2)
    return list(o.coords)
s8 = near_ring(byid[8])
add('lateral', 1, offset_path(ring_path(e_s, s8, True), 0.10), byid[8]['gpm'])
# zone 2: east run from the entry down to the SE corner, branch to the centre head, then along the curve and the SW edges
s9 = near_ring(byid[9]); s11_branch = ring_pos((9.68, byid[11]['y']))
flow = z2flow
add('lateral', 2, ring_path(e_s, s11_branch, True), flow)
qb = RING_IN.interpolate(s11_branch)
add('lateral', 2, [(qb.x, qb.y), (byid[11]['x'] + 0.3, byid[11]['y'])], byid[11]['gpm'])
flow -= byid[11]['gpm']
add('lateral', 2, ring_path(s11_branch, s9, True), flow)
s_prev = s9
for i in [9, 10, 0, 1, 2]:
    s_h = near_ring(byid[i])
    if i != 9:
        add('lateral', 2, ring_path(s_prev, s_h, True), flow)
    flow -= byid[i]['gpm']; s_prev = s_h

# swing pipes from the lateral to every head
for h in heads:
    s_h = near_ring(h); q = RING_IN.interpolate(s_h)
    if h['arc'] >= 360: continue
    add('swing', h['zone'], [(q.x, q.y), (h['x'], h['y'])], h['gpm'], '1/2" swing pipe')
add('swing', 2, [(byid[11]['x'] + 0.3, byid[11]['y']), (byid[11]['x'], byid[11]['y'])], byid[11]['gpm'], '1/2" swing pipe')

# ------------------------------------------------------------------ sleeves under the new concrete (lay before the pour)
sleeves = [
    dict(name='Mainline under the kitchen pad and east walk', size='2" Sch 40', pts=[(9.45, POC[1]), (11.25, POC[1])]),
    dict(name='Zone lines + valve wire under the east walk', size='3" Sch 40', pts=[(9.90, VALVES[1]), (11.25, VALVES[1])]),
]
for s_ in sleeves: s_['length_m'] = float(LineString(s_['pts']).length)

# ------------------------------------------------------------------ hydraulics (Hazen-Williams, C = 150)
ID_IN = {'1" Sch 40': 1.049, '1"': 1.189, '3/4"': 0.930, '1/2" swing pipe': 0.49}
def psi_loss(gpm, size, length_m):
    d_ = ID_IN[size]
    hf_ft = 10.44 * (length_m / FT) * gpm ** 1.852 / (150 ** 1.852 * d_ ** 4.8655)
    return 0.433 * hf_ft
for p in pipes:
    p['psi_loss'] = round(psi_loss(p['gpm'], p['size'], p['length_m']), 3)
    p['velocity_fps'] = round(0.4085 * p['gpm'] / ID_IN[p['size']] ** 2, 2)
def zone_worst(z):
    lat = [p for p in pipes if p['zone'] == z and p['kind'] == 'lateral']
    return sum(p['psi_loss'] for p in lat)            # conservative: all lateral segments in series
main_loss = sum(p['psi_loss'] for p in pipes if p['kind'] == 'main')
budget = dict(pvb=7.0, valve=2.5, main=round(main_loss, 2), lateral_z1=round(zone_worst(1), 2), lateral_z2=round(zone_worst(2), 2), swing=0.5, body_min_inlet=45.0)
need = budget['pvb'] + budget['valve'] + budget['main'] + max(budget['lateral_z1'], budget['lateral_z2']) + budget['swing'] + budget['body_min_inlet']

# ------------------------------------------------------------------ materials
def total(kind=None, size=None, zone=None):
    return sum(p['length_m'] for p in pipes if (kind is None or p['kind'] == kind) and (size is None or p['size'] == size) and (zone is None or p['zone'] == zone))
m2ft = lambda m: m / FT
mat = []
mat.append(('Pop-up spray body, 6", pressure regulated to 40 psi', 'Hunter PROS-06-PRS40 (or Rain Bird 1806-PRS)', len(heads)))
n90 = sum(h['nozzle'] == 'MP3000-90' for h in heads); n210 = sum(h['nozzle'] == 'MP3000-210' for h in heads); n360 = sum(h['nozzle'] == 'MP3000-360' for h in heads)
mat.append(('Rotary nozzle, 22-30 ft, adjustable 90-210°', 'Hunter MP3000-90 (or Rain Bird R-VAN24)', n90))
if n210: mat.append(('Rotary nozzle, 22-30 ft, 210-270°', 'Hunter MP3000-210', n210))
mat.append(('Rotary nozzle, 22-30 ft, full circle', 'Hunter MP3000-360 (or Rain Bird R-VAN24-360)', n360))
mat.append(('Swing joint: 1/2" swing pipe, 12-18" per head, with barbed elbows', '', len(heads)))
mat.append(('Valve, 1" globe', 'Hunter PGV-101G (or Rain Bird 100-DV)', 3))
mat.append(('Valve box, standard rectangular', 'Carson 1419 or similar', 1))
mat.append(('Pressure vacuum breaker, 1"', 'Febco 765-1 / Wilkins 720A (check local code)', 1))
mat.append(('Ball valve, 1" (isolation at the tie-in)', '', 1))
mat.append(('Mainline pipe, 1" Sch 40 PVC', '%.0f ft' % m2ft(total('main')), 1))
mat.append(('Lateral pipe, 1" Class 200 PVC', '%.0f ft' % m2ft(total('lateral', '1"')), 1))
mat.append(('Lateral pipe, 3/4" Class 200 PVC', '%.0f ft' % m2ft(total('lateral', '3/4"')), 1))
mat.append(('Sleeves under new concrete', '2" Sch 40: %.0f ft; 3" Sch 40: %.0f ft' % (m2ft(sleeves[0]['length_m']) + 2, m2ft(sleeves[1]['length_m']) + 2), 1))
mat.append(('Irrigation valve wire, 18 AWG 5-conductor, direct burial', '%.0f ft + waterproof wire connectors' % (m2ft(math.hypot(VALVES[0] - CONTROLLER[0], VALVES[1] - CONTROLLER[1])) + 25), 1))
mat.append(('Smart controller, 4+ stations, Wi-Fi, weather-based', 'Hunter Hydrawise HC or Rachio 3', 1))

out = dict(
    version=1, frame='plan metres: x east, y north (lawn grade = 0)',
    lawn=[list(map(float, c)) for c in LAWN.exterior.coords], lawn_sqft=round(LAWN.area / FT ** 2),
    heads=[dict(id=h['id'], zone=h['zone'], x=round(h['x'], 3), y=round(h['y'], 3), R=round(h['R'], 3), R_ft=h['R_ft'], a0=round(h['a0'], 1), arc=round(h['arc'], 1),
                nozzle=h['nozzle'], gpm=h['gpm'], where=h['where'], kind=h['kind']) for h in heads],
    pipes=pipes, sleeves=sleeves,
    poc=dict(x=POC[0], y=POC[1], note='Existing capped riser under the planned outdoor-kitchen back counter; likely the kitchen water supply. Confirm it is live house water before tying in.'),
    stubs=[dict(x=DRAIN_STUB[0], y=DRAIN_STUB[1], note='Tall white PVC stub at the planned sink (probably its drain): leave for the kitchen.'),
           dict(x=STUB_B[0], y=STUB_B[1], note='White PVC stub-up with a coil of black poly inside the new lawn: find out what it is; cap it below grade or use it.')],
    pvb=dict(x=PVB[0], y=PVB[1]), valves=dict(x=VALVES[0], y=VALVES[1], count=3), entry=dict(x=ENTRY[0], y=ENTRY[1]), controller=dict(x=CONTROLLER[0], y=CONTROLLER[1]),
    zones=[dict(zone=1, heads=len(Z1), gpm=round(z1flow, 1)), dict(zone=2, heads=len(Z2), gpm=round(z2flow, 1))],
    sim=dict(du_lq=round(d['du'], 3), overspray_pct=round(100 * d['over'], 1), pr_in_hr=LY.PR_IN_HR),
    pressure=dict(budget, needed_static_psi=round(need, 1)),
    materials=[dict(item=a, spec=b, qty=c) for a, b, c in mat],
)
json.dump(out, open('irr/irrigation.json', 'w'), indent=1)
print('zones: Z1 %.2f GPM, Z2 %.2f GPM' % (z1flow, z2flow))
print('pipe lengths (ft): main %.0f  1in lat %.0f  3/4 lat %.0f  swing %.0f' % (m2ft(total('main')), m2ft(total('lateral', '1"')), m2ft(total('lateral', '3/4"')), m2ft(total('swing'))))
print('pressure budget', budget, 'needed static/dynamic at the tie-in ~%.0f psi' % need)
for p in pipes:
    if p['kind'] != 'swing': print('  %-7s z%d %-10s %5.2f GPM  %5.1f ft  v %.1f ft/s  loss %.2f psi' % (p['kind'], p['zone'], p['size'], p['gpm'], m2ft(p['length_m']), p['velocity_fps'], p['psi_loss']))
for h in heads: print('  head %s %-38s (%6.2f,%6.2f) %s arc %3.0f R %.0f ft %.2f GPM' % (h['id'], h['where'], h['x'], h['y'], h['nozzle'], h['arc'], h['R_ft'], h['gpm']))
for m in mat: print('  BOM', m)
