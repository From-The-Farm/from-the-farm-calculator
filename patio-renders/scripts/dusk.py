"""Evening / dusk extras: gas flames on the fire tables, fire glow lights, pavilion downlights, spa light."""
import math, random
import bpy
from mathutils import Vector
from bl import MeshBuilder, obj
import mats

def flame_material(name='flame'):
    m, nt = mats.new_material(name)
    uv = nt.n('ShaderNodeUVMap', uv_map='UVMap').outputs['UV']
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=uv)
    u, v = sep.outputs['X'], sep.outputs['Y']
    # colour along height: blue base -> orange -> yellow tip
    ramp = nt.n('ShaderNodeValToRGB', Fac=v)
    cr = ramp.color_ramp
    cols = [(0.0, (0.15, 0.25, 1.0)), (0.12, (1.0, 0.30, 0.04)), (0.45, (1.0, 0.52, 0.10)), (1.0, (1.0, 0.78, 0.30))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols): el.position = p; el.color = (*c, 1.0)
    # alpha: fades toward edges and tip, flickery noise
    edge = nt.math('SUBTRACT', 1.0, nt.math('POWER', nt.math('ABSOLUTE', nt.math('MULTIPLY', nt.math('SUBTRACT', u, 0.5), 2.0)), 1.5))
    tip = nt.math('SUBTRACT', 1.0, nt.math('POWER', v, 1.6))
    oc = nt.n('ShaderNodeTexCoord').outputs['Object']
    n = nt.n('ShaderNodeTexNoise', Vector=oc, Scale=18.0, Detail=3.0).outputs['Factor']
    a = nt.math('MULTIPLY', nt.math('MULTIPLY', edge, tip), nt.math('MULTIPLY_ADD', n, 1.2, 0.2), clamp=True)
    em = nt.n('ShaderNodeEmission', Color=ramp.outputs['Color'], Strength=14.0)
    tr = nt.n('ShaderNodeBsdfTransparent')
    mix = nt.n('ShaderNodeMixShader', Fac=a)
    nt.link(tr.outputs[0], mix.inputs[1]); nt.link(em.outputs[0], mix.inputs[2])
    mats.finish(nt, mix)
    return m

def add_flames(c, fires, seed=3):
    """fires: list of (cx, cy, z, kind) with kind 'round' (r) or 'rect' (half extents)."""
    rng = random.Random(seed)
    mat = mats._get('flame', flame_material)
    objs = []
    for fi, f in enumerate(fires):
        cx, cy, z = f[:3]
        kind = f[3] if len(f) > 3 else ('round', 0.16)
        mb = MeshBuilder()
        uvs = []
        n = 34 if kind[0] == 'round' else 48
        for k in range(n):
            if kind[0] == 'round':
                a = rng.uniform(0, 2 * math.pi); r = kind[1] * math.sqrt(rng.uniform(0.1, 1.0))
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            else:
                x = cx + rng.uniform(-kind[1], kind[1]); y = cy + rng.uniform(-kind[2], kind[2])
            h = rng.uniform(0.12, 0.30); w = rng.uniform(0.05, 0.10)
            rot = rng.uniform(0, math.pi)
            dx, dy = math.cos(rot) * w / 2, math.sin(rot) * w / 2
            lean = Vector((rng.gauss(0, 0.02), rng.gauss(0, 0.02), 0))
            seg = 5
            base = len(mb.v)
            for s in range(seg + 1):
                t = s / seg
                off = lean * (t * t) * 3
                ww = 1.0 - 0.6 * t
                mb.vert((x - dx * ww + off.x, y - dy * ww + off.y, z + h * t)); uvs.append((0.0, t))
                mb.vert((x + dx * ww + off.x, y + dy * ww + off.y, z + h * t)); uvs.append((1.0, t))
            for s in range(seg):
                i = base + 2 * s
                mb.add_face([i, i + 1, i + 3, i + 2])
        me = mb.build('flames%d' % fi)
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = uvs[me.loops[li].vertex_index]
        o = obj('Flames%d' % fi, me, c, mat)
        o.visible_shadow = False
        objs.append(o)
        ld = bpy.data.lights.new('FireGlow%d' % fi, 'POINT'); ld.energy = 55.0 if kind[0] == 'round' else 75.0
        ld.color = (1.0, 0.52, 0.18); ld.shadow_soft_size = 0.12
        lo = bpy.data.objects.new('FireGlow%d' % fi, ld); c.objects.link(lo)
        lo.location = (cx, cy, z + 0.22)
        objs.append(lo)
    return objs
