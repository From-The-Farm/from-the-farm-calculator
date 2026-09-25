"""Existing-site context from the owner's photos: the house (SW of the lounge, back porch facing it),
the existing concrete back patio, red-sand yard with sparse weeds, and distant red-rock cliffs.
House size/position are estimates from the photos, not from the plan."""
import math, random
import bpy
import numpy as np
from mathutils import Vector
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
import plan as P
from bl import MeshBuilder, obj, obox, mesh, cylinder_mesh, extrude_profile_x
import mats
from hardscape import Z_TOP

# house footprint (world metres) — north facade faces the lounge's notch / back door by the steps
HX0, HX1, HY0, HY1 = -21.5, -8.0, -8.3, 3.9
WALL_H = 5.8
PITCH = 5 / 12
OV = 0.55
PORCH_Y = 5.95          # front line of the porch posts
PORCH_X0 = -19.0
DECK_X1 = -10.6         # raised deck west of here; concrete patio (grade) east of here
DECK_Z = 0.75

def house_footprint():
    return box(HX0, HY0, HX1, HY1)

def patio_poly():
    """Existing concrete back patio: under the east end of the porch and out to the walk / lounge."""
    region = unary_union([box(DECK_X1, HY1 - 0.01, -2.231, 6.429), box(HX1, 2.0, -2.231, 6.429)])
    return region.difference(P.OUTER.buffer(0.005)).difference(P.LOUNGE_OUT.buffer(0.005))

def _hip_roof(mb, x0, y0, x1, y1, z_wall, pitch, ov, mi=0):
    """Hip roof over wall rectangle; eaves extend ov beyond the walls."""
    half = min(x1 - x0, y1 - y0) / 2
    zr = z_wall + half * pitch
    ze = z_wall - ov * pitch
    yc = (y0 + y1) / 2
    if (x1 - x0) >= (y1 - y0):
        ra, rb = (x0 + half, yc), (x1 - half, yc)
    else:
        xc = (x0 + x1) / 2; ra, rb = (xc, y0 + half), (xc, y1 - half)
    E = [mb.vert((x0 - ov, y0 - ov, ze)), mb.vert((x1 + ov, y0 - ov, ze)), mb.vert((x1 + ov, y1 + ov, ze)), mb.vert((x0 - ov, y1 + ov, ze))]
    A = mb.vert((ra[0], ra[1], zr)); B = mb.vert((rb[0], rb[1], zr))
    t = 0.09  # visible roof thickness
    mb.add_face([E[0], E[1], B, A], mi)          # south
    mb.add_face([E[2], E[3], A, B], mi)          # north
    mb.add_face([E[1], E[2], B], mi)             # east
    mb.add_face([E[3], E[0], A], mi)             # west
    return ze

def build_house(c):
    stucco = mats._get('stucco_house', mats.stucco, (224, 212, 196))
    trim = mats._get('trim_dark', mats.simple, mats.lin((34, 34, 36)), 0.5, 0.0, 0.4)
    roof = mats._get('shingle', _shingle)
    white = mats._get('window_white', mats.simple, mats.lin((236, 236, 232)), 0.45)
    glass = mats._get('window_glass_house', mats.simple, mats.lin((26, 32, 38)), 0.04, 0.0, 0.9)
    soffit = mats._get('soffit', mats.simple, mats.lin((218, 214, 204)), 0.7)
    deckm = mats._get('deck_composite', mats.simple, mats.lin((104, 90, 78)), 0.7)
    # walls
    mb = MeshBuilder(); mb.box(HX0, HY0, 0.0, HX1, HY1, WALL_H)
    obj('House_Walls', mb.build('house_walls'), c, stucco)
    # hip roof + fascia + soffit
    mb = MeshBuilder()
    ze = _hip_roof(mb, HX0, HY0, HX1, HY1, WALL_H, PITCH, OV)
    obj('House_Roof', mb.build('house_roof'), c, roof)
    mb = MeshBuilder()
    fx0, fy0, fx1, fy1 = HX0 - OV, HY0 - OV, HX1 + OV, HY1 + OV
    for (a, b) in [((fx0, fy0), (fx1, fy0)), ((fx1, fy0), (fx1, fy1)), ((fx1, fy1), (fx0, fy1)), ((fx0, fy1), (fx0, fy0))]:
        a = Vector((*a, 0)); b = Vector((*b, 0)); d = b - a; L = d.length; t = d / L
        n = Vector((t.y, -t.x, 0))
        obox(mb, (a + b) / 2 + Vector((0, 0, ze - 0.08)) + n * 0.02, t, n, Vector((0, 0, 1)), L + 0.05, 0.04, 0.24)
        # gutter
        obox(mb, (a + b) / 2 + Vector((0, 0, ze - 0.12)) + n * 0.1, t, n, Vector((0, 0, 1)), L + 0.05, 0.12, 0.12)
    obj('House_Fascia', mb.build('house_fascia'), c, trim)
    mb = MeshBuilder()
    mb.flat_poly(box(fx0, fy0, fx1, fy1).difference(box(HX0, HY0, HX1, HY1)), ze - 0.19)
    o = obj('House_Soffit', mb.build('house_soffit'), c, soffit)
    # ---- back porch (north side)
    pz_wall, pz_front = 3.55, 2.98
    mb = MeshBuilder()
    y_eave = PORCH_Y + 0.30
    prof = [(HY1, pz_wall), (y_eave, pz_front), (y_eave, pz_front + 0.09), (HY1, pz_wall + 0.09)]
    extrude_profile_x(mb, prof, PORCH_X0 - 0.3, HX1 + 0.3)
    obj('Porch_Roof', mb.build('porch_roof'), c, roof)
    mb = MeshBuilder()
    obox(mb, ((PORCH_X0 + HX1) / 2, y_eave + 0.02, pz_front - 0.07), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), HX1 - PORCH_X0 + 0.64, 0.04, 0.24)
    obox(mb, ((PORCH_X0 + HX1) / 2, y_eave + 0.10, pz_front - 0.11), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), HX1 - PORCH_X0 + 0.64, 0.12, 0.12)
    # beam over posts
    mb.box(PORCH_X0 - 0.1, PORCH_Y - 0.09, 2.70, HX1 + 0.1, PORCH_Y + 0.09, 2.96)
    posts = [HX1 - 0.12, -10.9, -13.6, -16.3, -18.85]
    for x in posts:
        z0 = DECK_Z if x < DECK_X1 else Z_TOP
        mb.box(x - 0.05, PORCH_Y - 0.05, z0, x + 0.05, PORCH_Y + 0.05, 2.72)   # slim black steel posts
    obj('Porch_Trim', mb.build('porch_trim'), c, trim)
    mb = MeshBuilder()
    mb.box(PORCH_X0 - 0.1, HY1, 2.66, HX1 + 0.1, PORCH_Y + 0.1, 2.70)
    obj('Porch_Ceiling', mb.build('porch_ceiling'), c, soffit)
    # can lights in the porch ceiling
    em = mats._get('porch_can', mats.emission, (1.0, 0.85, 0.65), 0.0)
    for x in [-9.3, -12.2, -15.0, -17.8]:
        o = obj('PorchCan', cylinder_mesh('pc', 0.06, 0.004, seg=20), c, em); o.location = (x, (HY1 + PORCH_Y) / 2, 2.655)
    # wraparound: east-side porch from the NE corner south (seen at the left of photo 1)
    ex0, ex1 = HX1, HX1 + 1.65           # stays west of the new 4' walk
    ey0, ey1 = HY1 - 5.8, HY1
    mb = MeshBuilder()
    bm = __import__('bmesh')
    # shed roof sloping east: profile in (y, z) extruded along x is wrong axis -> build with obox planes
    run = ex1 + 0.3 - ex0
    drop = run * 0.25
    ang = math.atan2(drop, run)
    ctr = Vector(((ex0 + ex1 + 0.3) / 2, (ey0 + ey1) / 2, pz_wall - drop / 2 + 0.045))
    ax = Vector((math.cos(ang), 0, -math.sin(ang))); az = Vector((math.sin(ang), 0, math.cos(ang)))
    obox(mb, ctr, ax, Vector((0, 1, 0)), az, math.hypot(run, drop), (ey1 - ey0) + 0.3, 0.09)
    obj('Porch_Roof_E', mb.build('porch_roof_e'), c, roof)
    mb = MeshBuilder()
    mb.box(ex1 - 0.09, ey0 - 0.1, 2.70, ex1 + 0.09, ey1 + 0.1, 2.96)
    for y in (ey0 + 0.1, (ey0 + ey1) / 2):
        mb.box(ex1 - 0.05, y - 0.05, Z_TOP, ex1 + 0.05, y + 0.05, 2.72)
    obox(mb, (ex1 + 0.32, (ey0 + ey1) / 2, pz_wall - drop - 0.07), Vector((0, 1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), (ey1 - ey0) + 0.3, 0.04, 0.24)
    obj('Porch_Trim_E', mb.build('porch_trim_e'), c, trim)
    mb = MeshBuilder()
    mb.box(ex0, ey0 - 0.1, 2.66, ex1 + 0.1, ey1, 2.70)
    obj('Porch_Ceiling_E', mb.build('porch_ceiling_e'), c, soffit)
    mb = MeshBuilder()
    mb.poly_prism(box(ex0, ey0, ex1 + 0.05, ey1), -0.05, Z_TOP, ch=0.005, prand=0.4, bdir=(0.0, 1.0, 0.0))
    obj('Porch_Slab_E', mb.build('porch_slab_e'), c, mats._get('concrete_existing', mats.concrete, base=mats.lin((196, 160, 140)), rough=0.88, broom=0.3, mott=0.14))
    # raised deck + railing on the west part
    mb = MeshBuilder()
    mb.box(PORCH_X0, HY1, 0.0, DECK_X1, PORCH_Y + 0.05, DECK_Z)
    obj('Porch_Deck', mb.build('porch_deck'), c, deckm)
    mb = MeshBuilder()
    rail_h = 0.95
    for (xa, ya, xb, yb) in [(PORCH_X0, PORCH_Y, DECK_X1, PORCH_Y), (DECK_X1, PORCH_Y, DECK_X1, HY1 + 0.9)]:
        a = Vector((xa, ya, 0)); b = Vector((xb, yb, 0)); d = b - a; L = d.length; t = d / L; n = Vector((t.y, -t.x, 0))
        obox(mb, (a + b) / 2 + Vector((0, 0, DECK_Z + rail_h)), t, n, Vector((0, 0, 1)), L, 0.05, 0.04)
        obox(mb, (a + b) / 2 + Vector((0, 0, DECK_Z + 0.08)), t, n, Vector((0, 0, 1)), L, 0.04, 0.03)
        k = int(L / 0.11)
        for i in range(k + 1):
            p = a + t * (i * L / max(k, 1))
            obox(mb, p + Vector((0, 0, DECK_Z + rail_h / 2 + 0.03)), t, n, Vector((0, 0, 1)), 0.016, 0.016, rail_h - 0.08)
    obj('Porch_Railing', mb.build('porch_rail'), c, trim)
    # windows + back door (north facade), a few on the east facade
    mbw = MeshBuilder(); mbg = MeshBuilder()
    def win_n(x0, x1, z0, z1, y=HY1):
        mbw.box(x0 - 0.07, y - 0.02, z0 - 0.07, x1 + 0.07, y + 0.05, z1 + 0.07)
        mbg.box(x0, y + 0.05, z0, x1, y + 0.058, z1)
        mbw.box((x0 + x1) / 2 - 0.025, y + 0.05, z0, (x0 + x1) / 2 + 0.025, y + 0.07, z1)
    def win_e(y0, y1, z0, z1, x=HX1):
        mbw.box(x - 0.05, y0 - 0.07, z0 - 0.07, x + 0.02, y1 + 0.07, z1 + 0.07)
        mbg.box(x + 0.02, y0, z0, x + 0.028, y1, z1)
    win_n(-9.7, -8.8, Z_TOP, 2.15)                         # back door near the steps
    for x in (-12.2, -15.0, -17.8):
        win_n(x - 0.75, x + 0.75, 1.0, 2.35)
    for x in (-9.4, -12.6, -15.9, -19.2):
        win_n(x - 0.55, x + 0.55, 3.9, 5.05)
    for y in (-5.5, -1.8, 1.8):
        win_e(y - 0.6, y + 0.6, 1.0, 2.3)
        win_e(y - 0.5, y + 0.5, 3.9, 5.0)
    obj('House_WindowFrames', mbw.build('winframes'), c, white)
    obj('House_Glass', mbg.build('winglass'), c, glass)

def _shingle(name):
    m, nt = mats.new_material(name)
    Pp = mats._pos(nt)
    n1 = mats._noise(nt, Pp, 14.0, 4, 0.6)
    rows = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', Vector=Pp, Scale=7.0, wave_profile='SAW')
    c = nt.mix(n1, mats.lin((46, 46, 48)), mats.lin((66, 64, 64)))
    bump = nt.n('ShaderNodeBump', Strength=0.5, Distance=0.006, Height=nt.math('ADD', n1, rows.outputs['Factor']))
    mats.finish(nt, mats.principled(nt, Base_Color=c, Roughness=0.88, Normal=bump.outputs[0]))
    return m

def build_patio(c):
    mb = MeshBuilder()
    for q in [patio_poly()] if patio_poly().geom_type == 'Polygon' else list(patio_poly().geoms):
        mb.poly_prism(q.buffer(-0.004, join_style=2), -0.08, Z_TOP, ch=0.006, prand=0.3, bdir=(1.0, 0.0, 0.0))
    obj('Existing_Patio', mb.build('patio'), c, mats._get('concrete_existing', mats.concrete, base=mats.lin((196, 160, 140)), rough=0.88, broom=0.3, mott=0.14))

# ------------------------------------------------------------------------------------------ cliffs
def build_cliffs(c, seed=4):
    rs = np.random.RandomState(seed)
    def fbm(x, octaves=5):
        v = 0.0; a = 1.0; f = 1.0
        for o in range(octaves):
            v += a * np.sin(x * f * 1.7 + rs_phase[o]) * np.cos(x * f * 0.9 + rs_phase[o + 5])
            a *= 0.5; f *= 2.1
        return v
    rs_phase = rs.uniform(0, 6.28, 20)
    bearings = np.radians(np.linspace(-40, 80, 260))
    radii = np.concatenate([np.linspace(600, 1150, 18), np.linspace(1160, 1420, 40), np.linspace(1440, 2600, 22)])
    verts = []
    for b in bearings:
        Rb = 1250 + 160 * fbm(b * 3.0)
        Hb = 120 + 45 * fbm(b * 5.0 + 3.0) + 20 * np.sin(b * 23)
        for r in radii:
            d = r - Rb
            if d < -350:
                h = 0.0
            elif d < 0:
                t = (d + 350) / 350
                h = (t ** 2.2) * Hb * 0.42                      # talus apron
            elif d < 30:
                h = Hb * (0.42 + 0.58 * (d / 30) ** 0.6)        # cliff face
            else:
                h = Hb + (d - 30) * 0.02 + 6 * fbm(r * 0.01 + b * 7)
            h += 3.0 * fbm(r * 0.03 + b * 11) * (1 if d > -350 else 0)
            verts.append((r * math.sin(b), r * math.cos(b), h - 2.0))
    nb, nr = len(bearings), len(radii)
    faces = []
    for i in range(nb - 1):
        for j in range(nr - 1):
            a = i * nr + j
            faces.append((a, a + 1, a + nr + 1, a + nr))
    me = mesh('cliffs', verts, faces, smooth=True)
    obj('RedCliffs', me, c, mats._get('red_rock', mats.red_rock))

# ------------------------------------------------------------------------------------------ weeds
def weed_collection(seed=8):
    from grass import make_clump
    wc = bpy.data.collections.new('WeedClumps')
    rng = random.Random(seed)
    mat = mats._get('dry_weed', mats.dry_weed)
    for i in range(6):
        me = make_clump('weed%d' % i, rng, nblades=rng.randint(10, 22), h=(0.10, 0.34), spread=0.06)
        me.materials.append(mat)
        o = bpy.data.objects.new('Weed%d' % i, me); wc.objects.link(o)
    return wc
