"""Export a web-friendly GLB of the design (no grass/trees/neighbours) with simple PBR materials.
python3 export_gltf.py out.glb"""
import sys, os, random, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import main, mats

OUT = sys.argv[1] if len(sys.argv) > 1 else 'patio.glb'

def srgb(c):
    return mats.lin(c)

SIMPLE = {
    'concrete': ((180, 177, 170), 0.9, 0.0),
    'concrete_charcoal': ((74, 74, 74), 0.8, 0.0),
    'pavers_border': ((58, 57, 56), 0.85, 0.0),
    'joint_sand': ((66, 63, 58), 1.0, 0.0),
    'sand': ((66, 63, 58), 1.0, 0.0),
    'soil': ((74, 108, 40), 0.95, 0.0),
    'cedar': ((146, 92, 56), 0.7, 0.0),
    'ceiling_pine': ((182, 132, 88), 0.6, 0.0),
    'steel_black': ((34, 34, 36), 0.5, 0.7),
    'roof_metal': ((50, 52, 54), 0.45, 0.5),
    'mortar': ((90, 88, 84), 0.95, 0.0),
    'countertop': ((192, 189, 182), 0.3, 0.0),
    'stainless': ((196, 196, 192), 0.28, 1.0),
    'black_plastic': ((22, 22, 22), 0.4, 0.0),
    'spa_cabinet': ((96, 88, 80), 0.6, 0.0),
    'acrylic': ((228, 230, 232), 0.12, 0.0),
    'spa_trim': ((50, 48, 46), 0.5, 0.0),
    'spa_pillow': ((58, 60, 63), 0.5, 0.0),
    'alu_charcoal': ((62, 62, 64), 0.5, 0.4),
    'cushion': ((202, 196, 184), 0.95, 0.0),
    'pillow_navy': ((48, 64, 86), 0.95, 0.0),
    'pillow_rust': ((170, 104, 66), 0.95, 0.0),
    'teak': ((146, 112, 82), 0.55, 0.0),
    'gfrc': ((152, 150, 146), 0.75, 0.0),
    'fire_glass': ((40, 52, 60), 0.12, 0.3),
    'rope': ((80, 78, 76), 0.95, 0.0),
    'rope_natural': ((164, 152, 134), 0.95, 0.0),
    'fence_cedar': ((152, 104, 70), 0.8, 0.0),
    'downlight': ((40, 40, 40), 0.5, 0.0),
    'mortar_buff': ((196, 188, 174), 0.97, 0.0),
    'red_sand': ((198, 112, 76), 0.97, 0.0),
    'stucco_house': ((224, 212, 196), 0.9, 0.0),
    'trim_dark': ((34, 34, 36), 0.5, 0.0),
    'shingle': ((56, 55, 56), 0.88, 0.0),
    'window_white': ((236, 236, 232), 0.45, 0.0),
    'window_glass_house': ((26, 32, 38), 0.05, 0.0),
    'soffit': ((218, 214, 204), 0.7, 0.0),
    'deck_composite': ((104, 90, 78), 0.7, 0.0),
    'concrete_existing': ((196, 160, 140), 0.88, 0.0),
    'porch_can': ((230, 226, 214), 0.5, 0.0),
}
PAVER_TONES = [(0.0, (126, 124, 121)), (0.42, (110, 109, 106)), (0.80, (90, 89, 87))]
BRICK_TONES = [(0.0, (208, 138, 108)), (0.3, (216, 146, 114)), (0.55, (222, 154, 122)), (0.78, (210, 142, 112)), (0.9, (226, 164, 132)), (1.0, (198, 130, 102))]
STONE_TONES = [(0.0, (150, 145, 136)), (0.25, (132, 126, 118)), (0.5, (158, 150, 136)), (0.72, (118, 112, 104)), (0.9, (144, 132, 116))]

def ramp_const(tones, v):
    c = tones[0][1]
    for p, col in tones:
        if v >= p: c = col
    return c

def ramp_lin(tones, v):
    for i in range(len(tones) - 1):
        p0, c0 = tones[i]; p1, c1 = tones[i + 1]
        if v <= p1:
            t = (v - p0) / (p1 - p0) if p1 > p0 else 0
            return tuple(c0[k] + (c1[k] - c0[k]) * t for k in range(3))
    return tones[-1][1]

def simple_mat(name, rgb, rough, metal, vcol=False, alpha=1.0):
    m = bpy.data.materials.new('web_' + name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(rgb), 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    if vcol:
        ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'Col'
        nt.links.new(ca.outputs['Color'], b.inputs['Base Color'])
    return m

def face_colors_to_corner(me, fn):
    """Build a CORNER byte colour attribute 'Col' from a per-face function of 'prand'."""
    pr = me.attributes.get('prand')
    n = len(me.polygons)
    vals = np.zeros(n, np.float32)
    if pr is not None and pr.domain == 'FACE':
        pr.data.foreach_get('value', vals)
    col = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    loops = np.zeros(len(me.loops) * 4, np.float32)
    rng = random.Random(1)
    for p in me.polygons:
        c = fn(float(vals[p.index]))
        lc = srgb(c)
        for li in p.loop_indices:
            loops[li * 4:li * 4 + 4] = (*lc, 1.0)
    col.data.foreach_set('color', loops)

def run():
    main.build(grass_on=False, trees_on=False)
    # drop things the web model doesn't need
    for o in list(bpy.data.objects):
        n = o.name
        import re
        if o.type in ('LIGHT', 'CAMERA') or n.startswith(('Tree', 'FarTree', 'Flames', 'Spot', 'FireGlow', 'RedCliffs')) or re.match(r'House\d', n):
            bpy.data.objects.remove(o, do_unlink=True)
    cache = {}
    for o in list(bpy.data.objects):
        if o.type not in ('MESH', 'CURVE'):
            continue
        data = o.data
        mats_ = [s.material for s in o.material_slots]
        if not mats_:
            continue
        src = mats_[0].name if mats_[0] else ''
        if src in ('pavers', 'stone_veneer', 'brick_sandy_red'):
            tones = PAVER_TONES if src == 'pavers' else (STONE_TONES if src == 'stone_veneer' else BRICK_TONES)
            jit = random.Random(3)
            def fn(v, tones=tones, src=src):
                base = ramp_const(tones, v) if src == 'pavers' else ramp_lin(tones, v)
                f = 1.0 + 0.10 * (((v * 17.137) % 1.0) - 0.5)
                return tuple(min(255, c * f) for c in base)
            face_colors_to_corner(data, fn)
            key = src
            if key not in cache:
                cache[key] = simple_mat(key, (255, 255, 255), 0.85, 0.0, vcol=True)
            m = cache[key]
        elif src == 'water':
            m = cache.setdefault('water', simple_mat('water', (110, 196, 204), 0.05, 0.0, alpha=0.55))
        else:
            spec = SIMPLE.get(src)
            if spec is None:
                base = src.split('.')[0]
                spec = SIMPLE.get(base, ((160, 160, 160), 0.7, 0.0))
            m = cache.setdefault(src, simple_mat(src, *spec))
        for i in range(len(o.material_slots)):
            o.material_slots[i].material = m
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_apply=True,
                              export_vertex_color='MATERIAL', export_cameras=False, export_lights=False,
                              export_materials='EXPORT')
    print('exported', OUT, os.path.getsize(OUT) // 1024, 'KB')

run()
