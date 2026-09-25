"""Backyard context (not part of the plan): cedar privacy fence and neighbouring trees."""
import math, random
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
from bl import MeshBuilder, obj, mesh, obox, coll
import mats
from hardscape import YARD

FENCE_H = 1.83

def fence_wood(name='fence_cedar'):
    m, nt = mats.new_material(name)
    P = nt.n('ShaderNodeTexCoord').outputs['Object']
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=P)
    pr = mats._attr(nt, 'prand')
    v = nt.n('ShaderNodeCombineXYZ', X=nt.math('ADD', nt.math('MULTIPLY', sep.outputs['X'], 30.0), nt.math('MULTIPLY', pr, 50.0)),
             Y=nt.math('MULTIPLY', sep.outputs['Y'], 30.0), Z=nt.math('MULTIPLY', sep.outputs['Z'], 1.2)).outputs[0]
    grain = mats._noise(nt, v, 1.0, 5, 0.6, dist=1.5)
    ramp = nt.n('ShaderNodeValToRGB', Fac=pr)
    cr = ramp.color_ramp
    cols = [(0.0, mats.lin((124, 110, 96))), (0.5, mats.lin((142, 126, 108))), (1.0, mats.lin((110, 98, 86)))]
    while len(cr.elements) < 3: cr.elements.new(0.5)
    for el, (p, cc) in zip(cr.elements, cols): el.position = p; el.color = (*cc, 1.0)
    col = mats._tint(nt, ramp.outputs['Color'], mats._centered(nt, grain, 0.18))
    bump = nt.n('ShaderNodeBump', Strength=0.3, Distance=0.001, Height=grain)
    mats.finish(nt, mats.principled(nt, Base_Color=col, Roughness=0.8, Normal=bump.outputs[0]))
    return m

def build_fence(c):
    rng = random.Random(9)
    x0, x1, y0, y1 = YARD['x0'] - 14.0, YARD['x1'], YARD['y0'], YARD['y1']
    runs = [((x0, y1), (x1, y1), -1), ((x1, y1), (x1, y0), -1), ((x1, y0), (x0, y0), -1)]
    mb = MeshBuilder()
    for (a, b, inside) in runs:
        a = Vector((*a, 0)); b = Vector((*b, 0))
        d = b - a; L = d.length; t = d / L
        nrm = Vector((-t.y, t.x, 0)) * inside * -1       # points into the yard
        # rails + posts on the outside face, pickets on the yard side
        npost = int(L / 2.44) + 1
        for i in range(npost + 1):
            u = min(i * 2.44, L)
            p = a + t * u - nrm * 0.07
            obox(mb, p + Vector((0, 0, (FENCE_H + 0.08) / 2)), t, nrm, Vector((0, 0, 1)), 0.09, 0.09, FENCE_H + 0.08, prand=rng.random())
        for zr in (0.30, 1.45):
            obox(mb, a + t * (L / 2) - nrm * 0.02 + Vector((0, 0, zr)), t, nrm, Vector((0, 0, 1)), L, 0.038, 0.09, prand=rng.random())
        w, gap = 0.14, 0.005
        n = int(L / (w + gap))
        for i in range(n):
            u = (i + 0.5) * (w + gap)
            h = FENCE_H + rng.uniform(-0.006, 0.006)
            p = a + t * u + nrm * 0.008 + Vector((0, 0, h / 2 + 0.03))
            obox(mb, p, t, nrm, Vector((0, 0, 1)), w, 0.016, h, prand=rng.random())
        # cap board
        obox(mb, a + t * (L / 2) - nrm * 0.03 + Vector((0, 0, FENCE_H + 0.05)), t, nrm, Vector((0, 0, 1)), L + 0.1, 0.16, 0.025, prand=0.5)
    obj('Fence', mb.build('fence'), c, mats._get('fence_cedar', fence_wood))

# ------------------------------------------------------------------------------------------ trees
def _tube(verts, faces, pts, radii, sides):
    base = len(verts)
    for k, (p, r) in enumerate(zip(pts, radii)):
        if k < len(pts) - 1:
            d = (pts[k + 1] - p).normalized()
        else:
            d = (p - pts[k - 1]).normalized()
        a = d.orthogonal().normalized(); b = d.cross(a)
        for s in range(sides):
            ang = 2 * math.pi * s / sides
            v = p + (a * math.cos(ang) + b * math.sin(ang)) * r
            verts.append(tuple(v))
    for k in range(len(pts) - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            i0 = base + k * sides + s; i1 = base + k * sides + s2
            j0 = base + (k + 1) * sides + s; j1 = base + (k + 1) * sides + s2
            faces.append((i0, i1, j1, j0))

def gen_tree(rng, H=10.0, crown_r=4.0, trunk_h=2.4, levels=4, leaf_density=1.0, kind='round'):
    verts, faces = [], []
    leaves = []           # (pos, normal-ish dir)
    crown_c = Vector((0, 0, trunk_h + (H - trunk_h) * 0.5))
    crown_rz = (H - trunk_h) * 0.55

    def inside(p):
        q = p - crown_c
        return (q.x / crown_r) ** 2 + (q.y / crown_r) ** 2 + (q.z / crown_rz) ** 2

    def branch(p, d, L, r, lvl):
        nseg = max(3, int(L / 0.35))
        pts = [p.copy()]; rad = [r]
        cur = p.copy(); dd = d.copy()
        for k in range(nseg):
            jitter = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) * (0.18 if lvl > 0 else 0.06)
            out = Vector((cur.x, cur.y, 0.0))
            outv = out.normalized() * 0.06 if out.length > 0.01 else Vector()
            dd = (dd + jitter + Vector((0, 0, 0.05 if lvl < 2 else -0.02)) + outv).normalized()
            if inside(cur) > 0.85 and lvl > 0:   # steer back toward the crown
                dd = (dd + (crown_c - cur).normalized() * 0.35).normalized()
            cur = cur + dd * (L / nseg)
            pts.append(cur.copy()); rad.append(r * (1 - 0.55 * (k + 1) / nseg))
        sides = 8 if lvl == 0 else (6 if lvl == 1 else 4)
        if r > 0.004:
            _tube(verts, faces, pts, rad, sides)
        if lvl >= levels:
            # leaf clusters along the twig
            for k in range(1, len(pts)):
                for _ in range(int(2 * leaf_density)):
                    q = pts[k] + Vector((rng.gauss(0, 0.12), rng.gauss(0, 0.12), rng.gauss(0, 0.10)))
                    leaves.append((q, dd))
            return
        nchild = rng.randint(2, 4) if lvl > 0 else rng.randint(3, 5)
        for ci in range(nchild):
            t = rng.uniform(0.45, 1.0) if lvl > 0 else rng.uniform(0.85, 1.0)
            idx = min(len(pts) - 1, max(1, int(t * (len(pts) - 1))))
            q = pts[idx]
            axis = d.orthogonal().normalized()
            axis.rotate(Quaternion(d, rng.uniform(0, 2 * math.pi)))
            ang = math.radians(rng.uniform(25, 55) if lvl > 0 else rng.uniform(20, 45))
            nd = d.copy(); nd.rotate(Quaternion(axis, ang))
            if lvl == 0:
                nd = (nd + Vector((0, 0, 0.6))).normalized()
            cl = L * rng.uniform(0.55, 0.78) if lvl > 0 else (H - trunk_h) * rng.uniform(0.45, 0.6)
            cr_ = rad[idx] * rng.uniform(0.55, 0.72)
            branch(q, nd, cl, cr_, lvl + 1)
        # continuation leader
        if lvl > 0 and rng.random() < 0.7:
            branch(pts[-1], (d + Vector((rng.gauss(0, 0.2), rng.gauss(0, 0.2), 0.15))).normalized(), L * 0.6, rad[-1] * 0.8, lvl + 1)

    trunk_d = Vector((rng.gauss(0, 0.05), rng.gauss(0, 0.05), 1.0)).normalized()
    branch(Vector((0, 0, -0.1)), trunk_d, trunk_h + 0.1, 0.16 + 0.012 * H, 0)
    return verts, faces, leaves

def leaf_cluster_mesh(name, rng, n=9, size=0.07):
    verts, faces = [], []
    for i in range(n):
        base = Vector((rng.gauss(0, 0.05), rng.gauss(0, 0.05), rng.gauss(0, 0.04)))
        d = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + 0.4)).normalized()
        a = d.orthogonal().normalized(); b = d.cross(a)
        # rotate leaf plane randomly around d
        s = size * rng.uniform(0.75, 1.25)
        shape = [(0.0, 0.0), (0.35, 0.22), (0.75, 0.28), (1.0, 0.0), (0.75, -0.28), (0.35, -0.22)]
        k = len(verts)
        for (u, v) in shape:
            p = base + d * (u * s) + a * (v * s)
            p += b * (0.08 * s * math.sin(u * math.pi))      # slight cup
            verts.append(tuple(p))
        faces.append(tuple(range(k, k + 6)))
    return mesh(name, verts, faces)

def tree_nodegroup(leafcoll):
    ng = bpy.data.node_groups.new('TreeLeaves_' + leafcoll.name, 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; Lk = ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    ci = N.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value = leafcoll
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    m2p = N.new('GeometryNodeMeshToPoints'); m2p.mode = 'VERTICES'
    Lk.new(gi.outputs[0], m2p.inputs['Mesh'])
    iop = N.new('GeometryNodeInstanceOnPoints')
    Lk.new(m2p.outputs[0], iop.inputs['Points']); Lk.new(ci.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    ri = N.new('FunctionNodeRandomValue'); ri.data_type = 'INT'
    ri.inputs[4].default_value = 0; ri.inputs[5].default_value = len(leafcoll.objects) - 1
    Lk.new(ri.outputs[2], iop.inputs['Instance Index'])
    rr = N.new('FunctionNodeRandomValue'); rr.data_type = 'FLOAT_VECTOR'
    rr.inputs[0].default_value = (0, 0, 0); rr.inputs[1].default_value = (6.283, 6.283, 6.283)
    e2r = N.new('FunctionNodeEulerToRotation'); Lk.new(rr.outputs[0], e2r.inputs[0]); Lk.new(e2r.outputs[0], iop.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
    rs.inputs[2].default_value = 0.8; rs.inputs[3].default_value = 1.3
    Lk.new(rs.outputs[1], iop.inputs['Scale'])
    Lk.new(iop.outputs[0], go.inputs[0])
    return ng

def build_trees(c, specs, seed=1):
    """specs: list of (x, y, height, crown_radius, leaf_palette_index)."""
    rng = random.Random(seed)
    palettes = [
        [(0.0, mats.lin((40, 66, 22))), (0.5, mats.lin((56, 84, 28))), (0.85, mats.lin((70, 96, 32))), (1.0, mats.lin((96, 108, 38)))],
        [(0.0, mats.lin((52, 76, 26))), (0.5, mats.lin((72, 96, 34))), (0.8, mats.lin((110, 118, 44))), (1.0, mats.lin((150, 132, 52)))],
        [(0.0, mats.lin((34, 58, 26))), (0.5, mats.lin((46, 72, 30))), (1.0, mats.lin((62, 86, 34)))],
    ]
    leafcolls = []
    for pi, pal in enumerate(palettes):
        lc = bpy.data.collections.new('Leaves%d' % pi)
        lm = mats._get('leaf%d' % pi, mats.leaf, cols=pal)
        for k in range(6):
            me = leaf_cluster_mesh('leafc%d_%d' % (pi, k), rng, n=rng.randint(9, 13), size=0.10)
            me.materials.append(lm)
            o = bpy.data.objects.new('LeafC%d_%d' % (pi, k), me); lc.objects.link(o)
        leafcolls.append(lc)
    barkm = mats._get('bark', mats.bark)
    import treegen
    groups = [None, None, None]
    for ti, (x, y, H, R, pal) in enumerate(specs):
        N, par, r = treegen.colonize(1000 + ti, H=H, R=R, trunk_h=rng.uniform(1.9, 2.8))
        verts, faces = treegen.tree_mesh(N, par, r)
        wood = obj('Tree%d' % ti, mesh('tree%d' % ti, verts, faces, smooth=True), c, barkm)
        wood.location = (x, y, 0); wood.rotation_euler = (0, 0, rng.uniform(0, 6.28))
        LP = treegen.leaf_points(N, par, r, ti)
        lme = mesh('leafpts%d' % ti, [tuple(p) for p in LP], [])
        lo = obj('TreeLeaves%d' % ti, lme, c)
        lo.location = wood.location; lo.rotation_euler = wood.rotation_euler
        if groups[pal] is None:
            groups[pal] = tree_nodegroup(leafcolls[pal])
        mod = lo.modifiers.new('Leaves', 'NODES'); mod.node_group = groups[pal]
    return len(specs)


# ------------------------------------------------------------------------------------------ neighbours
def house_mats():
    sid = [mats._get('nstucco_%d' % i, mats.stucco, col) for i, col in enumerate([(214, 196, 170), (200, 178, 152), (226, 212, 190), (206, 170, 140)])]
    roof = mats._get('shingle', shingle)
    trim = mats._get('trim_white', mats.simple, mats.lin((226, 224, 218)), 0.5)
    win = mats._get('window_glass', mats.simple, mats.lin((30, 36, 42)), 0.05, 0.0, 0.8)
    return sid, roof, trim, win

def siding(name, col):
    m, nt = mats.new_material(name)
    P = mats._pos(nt)
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=P)
    w = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', Vector=P, Scale=6.0, wave_profile='SAW')
    n = mats._noise(nt, P, 2.0, 3, 0.5)
    c = mats._tint(nt, mats.lin(col), nt.math('MULTIPLY', mats._centered(nt, n, 0.05), nt.math('MULTIPLY_ADD', w.outputs['Factor'], 0.12, 0.88)))
    bump = nt.n('ShaderNodeBump', Strength=0.5, Distance=0.01, Height=w.outputs['Factor'])
    mats.finish(nt, mats.principled(nt, Base_Color=c, Roughness=0.7, Normal=bump.outputs[0]))
    return m

def shingle(name):
    m, nt = mats.new_material(name)
    P = mats._pos(nt)
    n1 = mats._noise(nt, P, 12.0, 4, 0.6)
    n2 = mats._noise(nt, P, 0.6, 3, 0.5)
    c = nt.mix(n1, mats.lin((58, 54, 50)), mats.lin((78, 72, 66)))
    c = mats._tint(nt, c, mats._centered(nt, n2, 0.1))
    bump = nt.n('ShaderNodeBump', Strength=0.6, Distance=0.01, Height=n1)
    mats.finish(nt, mats.principled(nt, Base_Color=c, Roughness=0.9, Normal=bump.outputs[0]))
    return m

def house(c, name, cx, cy, w, d, stories, rot, sid_i, rng):
    sid, roof, trim, win = house_mats()
    h = 2.9 if stories == 1 else 5.6
    M = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot, 4, 'Z')
    mb = MeshBuilder()
    mb.box(-w / 2, -d / 2, 0, w / 2, d / 2, h)
    o = obj(name + '_walls', mb.build(name + 'w'), c, sid[sid_i]); o.matrix_world = M
    # gable roof along x
    pitch = 0.42; ov = 0.45
    rise = (d / 2 + ov) * pitch
    mb = MeshBuilder()
    from bl import extrude_profile_x
    prof = [(-d / 2 - ov, h - ov * pitch), (d / 2 + ov, h - ov * pitch), (d / 2 + ov, h - ov * pitch + 0.12), (0, h + rise - ov * pitch + 0.12 + ov * pitch), (-d / 2 - ov, h - ov * pitch + 0.12)]
    extrude_profile_x(mb, prof, -w / 2 - ov, w / 2 + ov)
    o = obj(name + '_roof', mb.build(name + 'r'), c, roof); o.matrix_world = M
    # gable wall triangles
    mb = MeshBuilder()
    for xs in (-w / 2, w / 2):
        a = mb.vert((xs, -d / 2, h)); b = mb.vert((xs, d / 2, h)); t = mb.vert((xs, 0, h + (d / 2) * pitch))
        mb.add_face([a, b, t] if xs > 0 else [b, a, t])
    o = obj(name + '_gable', mb.build(name + 'g'), c, sid[sid_i]); o.matrix_world = M
    # windows on both long faces
    mb = MeshBuilder(); mt = MeshBuilder()
    for side in (-1, 1):
        y = side * (d / 2 + 0.01)
        nwin = max(2, int(w / 3.2))
        for fl in range(stories):
            z0 = 0.9 + fl * 2.7
            for k in range(nwin):
                x = -w / 2 + (k + 0.5) * w / nwin + rng.uniform(-0.3, 0.3)
                ww = rng.choice([0.9, 1.2, 1.6])
                mb.box(x - ww / 2, y - 0.02, z0, x + ww / 2, y + 0.02, z0 + 1.3)
                mt.box(x - ww / 2 - 0.08, y - 0.015, z0 - 0.08, x + ww / 2 + 0.08, y + 0.015, z0 + 1.38)
    o = obj(name + '_win', mb.build(name + 'wi'), c, win); o.matrix_world = M
    o = obj(name + '_trim', mt.build(name + 'tr'), c, trim); o.matrix_world = M

def build_neighbours(c, seed=5):
    rng = random.Random(seed)
    spots = []
    for x in (-30, -11, 8, 27):
        spots.append((x + rng.uniform(-2, 2), 40 + rng.uniform(-2, 3), 0.0))
    for x in (-25, -6, 13, 31):
        spots.append((x + rng.uniform(-2, 2), -40 - rng.uniform(-2, 3), 0.0))
    for y in (-16, 3, 22):
        spots.append((40 + rng.uniform(-1, 3), y + rng.uniform(-2, 2), math.pi / 2))
    for i, (x, y, rot) in enumerate(spots):
        house(c, 'House%d' % i, x, y, rng.uniform(13, 17), rng.uniform(9, 11), rng.choice([1, 2, 2]), rot + rng.uniform(-0.03, 0.03), rng.randrange(4), rng)

def build_far_trees(c, seed=77):
    """Second / third rings of trees (linked copies of the generated trees)."""
    rng = random.Random(seed)
    src = [o for o in c.objects if o.name.startswith('Tree') and not o.name.startswith('TreeLeaves')]
    leaves = {o.name: o for o in c.objects if o.name.startswith('TreeLeaves')}
    spots = []
    for x in range(-60, 70, 9):
        spots.append((x + rng.uniform(-3, 3), rng.uniform(31, 36)))
        spots.append((x + rng.uniform(-3, 3), rng.uniform(46, 62)))
        spots.append((x + rng.uniform(-3, 3), -rng.uniform(31, 36)))
        spots.append((x + rng.uniform(-3, 3), -rng.uniform(46, 62)))
    for y in range(-45, 50, 9):
        spots.append((rng.uniform(31, 35), y + rng.uniform(-3, 3)))
        spots.append((rng.uniform(46, 62), y + rng.uniform(-3, 3)))
        spots.append((-rng.uniform(52, 58), y + rng.uniform(-3, 3)))
        spots.append((-rng.uniform(64, 78), y + rng.uniform(-3, 3)))
    k = 0
    for (x, y) in spots:
        s = rng.choice(src)
        num = s.name[4:]
        lf = leaves.get('TreeLeaves' + num)
        sc = rng.uniform(0.85, 1.3)
        rot = rng.uniform(0, 6.28)
        o = bpy.data.objects.new('FarTree%d' % k, s.data); c.objects.link(o)
        o.location = (x, y, 0); o.rotation_euler = (0, 0, rot); o.scale = (sc, sc, sc)
        if lf is not None:
            l2 = bpy.data.objects.new('FarTreeLeaves%d' % k, lf.data); c.objects.link(l2)
            l2.location = (x, y, 0); l2.rotation_euler = (0, 0, rot); l2.scale = (sc, sc, sc)
            md = l2.modifiers.new('Leaves', 'NODES'); md.node_group = lf.modifiers[0].node_group
        k += 1
    return k
