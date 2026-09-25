"""30' x 15' covered pavilion: 4 corner posts, glulam beams, king-post trusses, T&G ceiling,
standing-seam metal gable roof (ridge along the 30' length)."""
import math
import bpy
from mathutils import Vector
import plan as P
from bl import member, box_obj, obj, MeshBuilder, obox, coll, cylinder_mesh
import mats
from hardscape import Z_TOP

PS = 0.24            # post size (10x10 rough sawn)
POST_TOP = 2.75      # 9'-0" to underside of beams
BEAM_W, BEAM_D = 0.17, 0.46
PITCH = 0.5          # 6:12
TH = math.atan(PITCH); CT = math.cos(TH); ST = math.sin(TH)
RAF_W, RAF_D = 0.09, 0.19
EAVE = 0.55          # horizontal overhang past beam centre line
GABLE = 0.45         # overhang past end trusses
DECK_T = 0.022

def geometry():
    x0, y0, x1, y1 = P.PAVILION
    g = dict(x0=x0, y0=y0, x1=x1, y1=y1)
    g['ybs'] = y0 + PS / 2; g['ybn'] = y1 - PS / 2
    g['yc'] = (y0 + y1) / 2
    g['zr'] = POST_TOP + BEAM_D                      # rafter seat (top of beams)
    g['xs'] = x0 + PS / 2 - GABLE; g['xe'] = x1 - PS / 2 + GABLE
    g['ye_s'] = g['ybs'] - EAVE; g['ye_n'] = g['ybn'] + EAVE
    g['trusses'] = [x0 + PS / 2, (x0 + x1) / 2, x1 - PS / 2]
    return g

def z_under(g, y):
    """underside of common rafters at plan y"""
    if y <= g['yc']:
        return g['zr'] + (y - g['ybs']) * PITCH
    return g['zr'] + (g['ybn'] - y) * PITCH

def z_top(g, y):
    return z_under(g, y) + RAF_D / CT

def build_pavilion(c):
    g = geometry()
    cedar = mats._get('cedar', mats.wood)
    deck_m = mats._get('ceiling_pine', mats.wood, base=mats.lin((178, 128, 84)), dark=mats.lin((140, 94, 58)), rough=0.6, grain_scale=1.3, rough_sawn=False)
    steel = mats._get('steel_black', mats.simple, mats.lin((34, 34, 36)), 0.5, 0.7)
    roof = mats._get('roof_metal', mats.standing_seam)
    x0, y0, x1, y1 = g['x0'], g['y0'], g['x1'], g['y1']
    yc = g['yc']
    # ---- posts with steel standoff bases
    posts = [(x0 + PS / 2, y0 + PS / 2), (x1 - PS / 2, y0 + PS / 2), (x0 + PS / 2, y1 - PS / 2), (x1 - PS / 2, y1 - PS / 2)]
    mb = MeshBuilder()
    for i, (px, py) in enumerate(posts):
        member('Post%d' % i, (px, py, Z_TOP + 0.028), (px, py, POST_TOP), PS, PS, cedar, c, up=(1, 0, 0), bevel=0.006)
        mb.box(px - 0.14, py - 0.14, Z_TOP, px + 0.14, py + 0.14, Z_TOP + 0.012)
        mb.box(px - 0.10, py - PS / 2 - 0.008, Z_TOP, px + 0.10, py - PS / 2, Z_TOP + 0.22)
        mb.box(px - 0.10, py + PS / 2, Z_TOP, px + 0.10, py + PS / 2 + 0.008, Z_TOP + 0.22)
    obj('PostBases', mb.build('postbases'), c, steel)
    # ---- long beams (glulam) along X
    zb = POST_TOP + BEAM_D / 2
    for tag, yy in (('S', g['ybs']), ('N', g['ybn'])):
        member('Beam' + tag, (x0 - 0.30, yy, zb), (x1 + 0.30, yy, zb), BEAM_W, BEAM_D, cedar, c, bevel=0.006)
    # ---- knee braces (along X to beams, along Y to ties)
    for i, (px, py) in enumerate(posts):
        sx = 1 if px < (x0 + x1) / 2 else -1
        sy = 1 if py < yc else -1
        a = 0.70
        member('BraceX%d' % i, (px + sx * PS / 2, py, POST_TOP - a), (px + sx * (PS / 2 + a), py, POST_TOP), 0.09, 0.14, cedar, c,
               up=(0, 1, 0))
        member('BraceY%d' % i, (px, py + sy * PS / 2, POST_TOP - a + 0.02), (px, py + sy * (PS / 2 + a), POST_TOP + 0.02), 0.09, 0.14, cedar, c,
               up=(1, 0, 0))
    # ---- trusses
    zr = g['zr']
    ridge_bot = z_top(g, yc) - 0.30
    for k, xt in enumerate(g['trusses']):
        # tie between the beams (flush top with beams)
        member('Tie%d' % k, (xt, g['ybs'], POST_TOP + BEAM_D - 0.12), (xt, g['ybn'], POST_TOP + BEAM_D - 0.12), 0.17, 0.24, cedar, c)
        member('KingPost%d' % k, (xt, yc, zr), (xt, yc, ridge_bot), 0.17, 0.17, cedar, c, up=(1, 0, 0))
        for side in (-1, 1):
            # principal rafter: deeper, top aligned with the common rafter tops
            ya = g['ye_s'] if side < 0 else g['ye_n']
            yb = yc + side * (-0.085)
            dp = 0.26
            def cen(y):
                zt = z_top(g, y)
                n = Vector((0, side * ST, CT)) if side > 0 else Vector((0, -ST, CT))
                # normal pointing up/outward from the slope surface
                n = Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))
                return Vector((xt, y, zt)) - n * (dp / 2)
            member('Principal%d%s' % (k, 'S' if side < 0 else 'N'), cen(ya), cen(yb), 0.17, dp, cedar, c,
                   up=(Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))))
            # strut from king post foot to quarter point
            yq = yc + side * 1.15
            member('Strut%d%s' % (k, 'S' if side < 0 else 'N'), (xt, yc + side * 0.085, zr + 0.18), tuple(cen(yq) - Vector((0, 0, 0.10))), 0.09, 0.14, cedar, c,
                   up=(1, 0, 0))
    # ---- ridge beam
    member('RidgeBeam', (g['xs'], yc, ridge_bot + 0.15), (g['xe'], yc, ridge_bot + 0.15), 0.14, 0.30, cedar, c)
    # ---- common rafters
    xs, xe = g['xs'], g['xe']
    n = int((xe - xs - 0.1) / 0.61) + 1
    xr = [xs + 0.05 + i * (xe - xs - 0.1) / (n - 1) for i in range(n)]
    for i, x in enumerate(xr):
        if any(abs(x - t) < 0.25 for t in g['trusses']):
            continue
        for side in (-1, 1):
            nrm = Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))
            ya = g['ye_s'] if side < 0 else g['ye_n']
            yb = yc + side * (-0.07)
            p0 = Vector((x, ya, z_under(g, ya))) + nrm * (RAF_D / 2)
            p1 = Vector((x, yb, z_under(g, yb))) + nrm * (RAF_D / 2)
            member('Rafter%d%s' % (i, 'S' if side < 0 else 'N'), p0, p1, RAF_W, RAF_D, cedar, c, up=nrm)
    # ---- tongue & groove ceiling boards (run along X)
    bw = 0.14
    for side in (-1, 1):
        nrm = Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))
        ya = g['ye_s'] if side < 0 else g['ye_n']
        run = abs(yc - ya) / CT
        nb = int(math.ceil(run / bw))
        for i in range(nb):
            s0 = i * bw; s1 = min(run, (i + 1) * bw)
            sm = (s0 + s1) / 2
            y = ya - side * sm * CT
            z = z_top(g, ya) + sm * ST
            cpt = Vector((0, y, z)) + nrm * (DECK_T / 2)
            member('Deck%s%02d' % ('S' if side < 0 else 'N', i), (xs - 0.01, cpt.y, cpt.z), (xe + 0.01, cpt.y, cpt.z), (s1 - s0) - 0.004, DECK_T, deck_m, c,
                   up=nrm, bevel=0.002)
    # ---- fascia + barge boards
    for side in (-1, 1):
        ya = g['ye_s'] if side < 0 else g['ye_n']
        zt = z_top(g, ya) + DECK_T
        zu = z_under(g, ya)
        member('Fascia%s' % ('S' if side < 0 else 'N'), (xs - 0.03, ya + side * 0.0125, (zt + zu) / 2 - 0.01), (xe + 0.03, ya + side * 0.0125, (zt + zu) / 2 - 0.01),
               0.025, (zt - zu) + 0.03, cedar, c)
        for xb, tag in ((xs - 0.0125 - 0.005, 'W'), (xe + 0.0125 + 0.005, 'E')):
            nrm = Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))
            p0 = Vector((xb, ya, z_under(g, ya))) + nrm * 0.13
            p1 = Vector((xb, yc, z_under(g, yc))) + nrm * 0.13
            member('Barge%s%s' % (tag, 'S' if side < 0 else 'N'), p0, p1, 0.025, 0.26, cedar, c, up=nrm)
    # ---- metal roof panels + standing seams + ridge cap
    mb = MeshBuilder()
    for side in (-1, 1):
        nrm = Vector((0, -ST, CT)) if side < 0 else Vector((0, ST, CT))
        ya = g['ye_s'] + (-0.05 if side < 0 else 0.05) if side < 0 else g['ye_n'] + 0.05
        run = abs(yc - ya) / CT
        down = Vector((0, -CT, -ST)) if side < 0 else Vector((0, CT, -ST))   # unit vector down the slope
        top_c = Vector(((xs + xe) / 2, yc, z_top(g, yc) + DECK_T)) + nrm * 0.006
        centre = top_c + down * (run / 2)
        ax = Vector((1, 0, 0))
        obox(mb, centre, ax, down, nrm, (xe - xs) + 0.10, run, 0.012, mi=0)
        k = int(((xe - xs) + 0.06) / 0.41)
        for i in range(k + 1):
            xx = xs - 0.02 + i * ((xe - xs) + 0.04) / k
            cc = Vector((xx, centre.y, centre.z)) + nrm * 0.026
            obox(mb, cc, ax, down, nrm, 0.022, run, 0.04, mi=0)
        # ridge cap half
        cap_c = top_c + down * 0.10 + nrm * 0.05
        obox(mb, cap_c, ax, down, nrm, (xe - xs) + 0.12, 0.24, 0.02, mi=0)
    obj('RoofMetal', mb.build('roofmetal'), c, roof)
    return g

def build_lights(c, g, strength=0.0):
    """Downlights under the ridge beam (emissive discs) + actual spot lights for dusk shots."""
    em = mats._get('downlight', mats.emission, (1.0, 0.78, 0.52), strength)
    rim = mats._get('steel_black', mats.simple, mats.lin((34, 34, 36)), 0.5, 0.7)
    lights = []
    zb = z_top(g, g['yc']) - 0.30
    for i, x in enumerate([g['x0'] + 1.8, (g['x0'] + g['x1']) / 2 - 1.6, (g['x0'] + g['x1']) / 2 + 1.6, g['x1'] - 1.8]):
        me = cylinder_mesh('can%d' % i, 0.055, 0.03, seg=24)
        o = obj('DownlightHousing%d' % i, me, c, rim); o.location = (x, g['yc'], zb - 0.03)
        me2 = cylinder_mesh('lens%d' % i, 0.042, 0.002, seg=24)
        o2 = obj('DownlightLens%d' % i, me2, c, em); o2.location = (x, g['yc'], zb - 0.032)
        ld = bpy.data.lights.new('Spot%d' % i, 'SPOT'); ld.energy = 0.0; ld.spot_size = math.radians(120); ld.spot_blend = 0.6
        ld.shadow_soft_size = 0.04; ld.color = (1.0, 0.76, 0.5)
        lo = bpy.data.objects.new('Spot%d' % i, ld); c.objects.link(lo)
        lo.location = (x, g['yc'], zb - 0.04); lo.rotation_euler = (0, 0, 0)
        lights.append(lo)
    return lights
