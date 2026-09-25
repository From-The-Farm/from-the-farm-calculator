"""Instanced grass blades on lawn meshes (geometry nodes)."""
import math, random
import bpy
from bl import coll, mesh, obj
import mats

def make_clump(name, rng, nblades=36, h=(0.05, 0.085), spread=0.024):
    verts, faces, uvs = [], [], []
    seg = 4
    for _ in range(nblades):
        r = spread * math.sqrt(rng.random()); a = rng.uniform(0, 2 * math.pi)
        bx, by = r * math.cos(a), r * math.sin(a)
        H = rng.uniform(*h)
        if rng.random() < 0.08: H *= 1.35          # a few taller blades
        w = rng.uniform(0.0022, 0.0038)
        lean_a = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.10, 0.42) * H
        face_a = lean_a + math.pi / 2 + rng.uniform(-0.5, 0.5)
        fx, fy = math.cos(face_a), math.sin(face_a)
        lx, ly = math.cos(lean_a), math.sin(lean_a)
        base = len(verts)
        for s in range(seg + 1):
            t = s / seg
            off = lean * t * t
            z = H * (t - 0.18 * (lean / H) * t * t)
            cx, cy = bx + lx * off, by + ly * off
            ww = w * (1.0 - t ** 1.6) if s < seg else 0.0
            if s < seg:
                verts.append((cx - fx * ww / 2, cy - fy * ww / 2, z)); uvs.append((0.0, t))
                verts.append((cx + fx * ww / 2, cy + fy * ww / 2, z)); uvs.append((1.0, t))
            else:
                verts.append((cx, cy, z)); uvs.append((0.5, 1.0))
        for s in range(seg - 1):
            i = base + 2 * s
            faces.append((i, i + 1, i + 3, i + 2))
        i = base + 2 * (seg - 1)
        faces.append((i, i + 1, i + 2))
    me = mesh(name, verts, faces)
    uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uvl.data[li].uv = uvs[vi]
    return me

def clump_collection(n=10, seed=3):
    c = bpy.data.collections.new('GrassClumps')     # not linked to the scene: only instanced
    rng = random.Random(seed)
    mat = mats._get('grass_blade', mats.grass_blade)
    for i in range(n):
        me = make_clump('clump%d' % i, rng, nblades=rng.randint(28, 44))
        me.materials.append(mat)
        o = bpy.data.objects.new('GrassClump%d' % i, me)
        c.objects.link(o)
    return c

def grass_nodegroup(clumps, density, seed=0, name='GrassScatter'):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces'); dist.distribute_method = 'RANDOM'
    dist.inputs['Density'].default_value = density
    dist.inputs['Seed'].default_value = seed
    L.new(gi.outputs[0], dist.inputs['Mesh'])
    ci = N.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value = clumps
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    ci.transform_space = 'ORIGINAL'
    iop = N.new('GeometryNodeInstanceOnPoints')
    L.new(dist.outputs['Points'], iop.inputs['Points'])
    L.new(ci.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    ri = N.new('FunctionNodeRandomValue'); ri.data_type = 'INT'
    ri.inputs[4].default_value = 0; ri.inputs[5].default_value = len(clumps.objects) - 1; ri.inputs['Seed'].default_value = seed + 1
    L.new(ri.outputs[2], iop.inputs['Instance Index'])
    rr = N.new('FunctionNodeRandomValue'); rr.data_type = 'FLOAT_VECTOR'
    rr.inputs[0].default_value = (-0.12, -0.12, 0.0); rr.inputs[1].default_value = (0.12, 0.12, 6.283)
    rr.inputs['Seed'].default_value = seed + 2
    e2r = N.new('FunctionNodeEulerToRotation')
    L.new(rr.outputs[0], e2r.inputs[0]); L.new(e2r.outputs[0], iop.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
    rs.inputs[2].default_value = 0.75; rs.inputs[3].default_value = 1.25; rs.inputs['Seed'].default_value = seed + 3
    L.new(rs.outputs[1], iop.inputs['Scale'])
    join = N.new('GeometryNodeJoinGeometry')
    L.new(iop.outputs[0], join.inputs[0]); L.new(gi.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng

def add_grass(target, clumps, density, seed):
    ng = grass_nodegroup(clumps, density, seed, name='Grass_' + target.name)
    mod = target.modifiers.new('Grass', 'NODES')
    mod.node_group = ng
    return mod
