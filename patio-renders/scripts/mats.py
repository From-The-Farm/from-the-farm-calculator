"""Procedural materials (Cycles)."""
import bpy, math
from bl import new_material, principled, finish, NT

_cache = {}

def _get(name, fn, *a, **k):
    if name not in _cache:
        _cache[name] = fn(name, *a, **k)
    return _cache[name]

def lin(srgb):
    """sRGB 0-255 tuple -> linear floats"""
    def c(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(c(v) for v in srgb)

def _pos(nt):
    return nt.n('ShaderNodeNewGeometry').outputs['Position']

def _noise(nt, vec, scale, detail=4.0, rough=0.55, dims='3D', dist=0.0):
    n = nt.n('ShaderNodeTexNoise', noise_dimensions=dims, Vector=vec, Scale=scale, Detail=detail, Roughness=rough, Distortion=dist)
    return n.outputs['Factor']

def _centered(nt, fac, amp):
    """1 + amp*(fac-0.5)*2"""
    return nt.math('MULTIPLY_ADD', nt.math('SUBTRACT', fac, 0.5), 2.0 * amp, 1.0)

def _tint(nt, color, factor):
    return nt.mix(1.0, color, nt.n('ShaderNodeCombineColor', Red=factor, Green=factor, Blue=factor).outputs[0], blend='MULTIPLY')

def _attr(nt, name, out='Factor'):
    return nt.n('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name).outputs[out]

# ---------------------------------------------------------------------------------------------- concrete
def concrete(name='concrete', base=lin((178, 175, 168)), rough=0.86, broom=0.5, mott=0.10, charcoal=False):
    m, nt = new_material(name)
    P = _pos(nt)
    n_mott = _noise(nt, P, 0.45, 5, 0.6)
    n_mid = _noise(nt, P, 7.0, 6, 0.6)
    n_speck = _noise(nt, P, 220.0, 3, 0.5)
    prand = _attr(nt, 'prand')
    f = nt.math('MULTIPLY', _centered(nt, n_mott, mott), _centered(nt, n_mid, 0.05))
    f = nt.math('MULTIPLY', f, _centered(nt, n_speck, 0.07))
    f = nt.math('MULTIPLY', f, _centered(nt, prand, 0.035))
    col = _tint(nt, base, f)
    # broom streaks: attribute 'bdir' holds the stroke direction (parallel to the control joints)
    bdir = _attr(nt, 'bdir', 'Vector')
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=bdir)
    perp = nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', sep.outputs['Y'], -1.0), Y=sep.outputs['X'], Z=0.0).outputs[0]
    s = nt.vmath('DOT_PRODUCT', P, perp, out=1)
    t = nt.vmath('DOT_PRODUCT', P, bdir, out=1)
    v = nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', s, 260.0), Y=nt.math('MULTIPLY', t, 3.5), Z=0.0).outputs[0]
    broom_h = _noise(nt, v, 1.0, 3, 0.55)
    grit = _noise(nt, P, 900.0, 2, 0.5)
    h = nt.math('MULTIPLY_ADD', broom_h, broom, nt.math('MULTIPLY', grit, 0.35))
    bump = nt.n('ShaderNodeBump', Strength=0.35 if not charcoal else 0.2, Distance=0.0012, Height=h)
    r = nt.math('MULTIPLY_ADD', nt.math('SUBTRACT', n_mid, 0.5), 0.08, rough)
    b = principled(nt, Base_Color=col, Roughness=r, Normal=bump.outputs[0], Specular_IOR_Level=0.45)
    finish(nt, b)
    return m

# ---------------------------------------------------------------------------------------------- pavers
def pavers(name='pavers', tones=None, rough=0.84, border=False):
    m, nt = new_material(name)
    P = _pos(nt)
    prand = _attr(nt, 'prand')
    ramp = nt.n('ShaderNodeValToRGB', Fac=prand)
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    tones = tones or [(0.0, lin((126, 124, 121))), (0.42, lin((110, 109, 106))), (0.80, lin((90, 89, 87)))]
    while len(cr.elements) < len(tones):
        cr.elements.new(0.5)
    for el, (pos, c) in zip(cr.elements, tones):
        el.position = pos; el.color = (*c, 1.0)
    # per-paver shade jitter + surface aggregate speckle
    jit = nt.math('FRACT', nt.math('MULTIPLY', prand, 17.137))
    f = _centered(nt, jit, 0.05)
    sp = _noise(nt, P, 260.0, 3, 0.6)
    f = nt.math('MULTIPLY', f, _centered(nt, sp, 0.10))
    wear = _noise(nt, P, 1.3, 4, 0.6)
    f = nt.math('MULTIPLY', f, _centered(nt, wear, 0.05))
    col = _tint(nt, ramp.outputs['Color'], f)
    h = nt.math('ADD', _noise(nt, P, 180.0, 4, 0.65), nt.math('MULTIPLY', _noise(nt, P, 900.0, 2, 0.5), 0.5))
    bump = nt.n('ShaderNodeBump', Strength=0.28, Distance=0.0008, Height=h)
    r = nt.math('MULTIPLY_ADD', nt.math('SUBTRACT', sp, 0.5), 0.1, rough)
    b = principled(nt, Base_Color=col, Roughness=r, Normal=bump.outputs[0], Specular_IOR_Level=0.4)
    finish(nt, b)
    return m

def sand(name='joint_sand'):
    m, nt = new_material(name)
    P = _pos(nt)
    n = _noise(nt, P, 400.0, 3, 0.6)
    col = _tint(nt, lin((66, 63, 58)), _centered(nt, n, 0.15))
    bump = nt.n('ShaderNodeBump', Strength=0.6, Distance=0.001, Height=n)
    finish(nt, principled(nt, Base_Color=col, Roughness=1.0, Normal=bump.outputs[0]))
    return m

# ---------------------------------------------------------------------------------------------- grass
def grass_blade(name='grass_blade'):
    m, nt = new_material(name)
    rnd = nt.n('ShaderNodeObjectInfo').outputs['Random']
    ramp = nt.n('ShaderNodeValToRGB', Fac=rnd)
    cr = ramp.color_ramp
    cols = [(0.0, lin((64, 104, 30))), (0.35, lin((80, 122, 38))), (0.7, lin((96, 134, 44))), (0.93, lin((118, 140, 54))), (1.0, lin((138, 140, 72)))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols):
        el.position = p; el.color = (*c, 1.0)
    uv = nt.n('ShaderNodeUVMap', uv_map='UVMap').outputs['UV']
    ht = nt.n('ShaderNodeSeparateXYZ', Vector=uv).outputs['Y']
    dark = nt.math('MULTIPLY_ADD', nt.math('POWER', ht, 0.6), 0.5, 0.5)
    # large scale lawn variation (world space)
    P = _pos(nt)
    patch = _noise(nt, P, 0.25, 3, 0.5)
    col = _tint(nt, ramp.outputs['Color'], nt.math('MULTIPLY', dark, _centered(nt, patch, 0.12)))
    b = principled(nt, Base_Color=col, Roughness=0.42, Specular_IOR_Level=0.35)
    tr = nt.n('ShaderNodeBsdfTranslucent', Color=_tint(nt, col, 1.6))
    mix = nt.n('ShaderNodeMixShader', Fac=0.32)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(tr.outputs[0], mix.inputs[2])
    finish(nt, mix)
    return m

def soil(name='lawn_soil'):
    m, nt = new_material(name)
    P = _pos(nt)
    n1 = _noise(nt, P, 3.0, 5, 0.6)
    n2 = _noise(nt, P, 40.0, 4, 0.6)
    c = nt.mix(n1, lin((46, 64, 22)), lin((60, 74, 28)))
    c = _tint(nt, c, _centered(nt, n2, 0.2))
    bump = nt.n('ShaderNodeBump', Strength=0.5, Distance=0.003, Height=n2)
    finish(nt, principled(nt, Base_Color=c, Roughness=0.95, Normal=bump.outputs[0]))
    return m

# ---------------------------------------------------------------------------------------------- wood
def wood(name='cedar', base=lin((140, 88, 54)), dark=lin((98, 58, 34)), rough=0.72, grain_scale=1.0, rough_sawn=True, axis='X'):
    """Grain runs along local `axis` of object coordinates."""
    m, nt = new_material(name)
    oc = nt.n('ShaderNodeTexCoord').outputs['Object']
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=oc)
    a = {'X': 'X', 'Y': 'Y', 'Z': 'Z'}[axis]
    others = [k for k in 'XYZ' if k != a]
    # stretched coordinates: long along the grain
    v = nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', sep.outputs[a], 0.08 * grain_scale),
             Y=nt.math('MULTIPLY', sep.outputs[others[0]], 1.0 * grain_scale), Z=nt.math('MULTIPLY', sep.outputs[others[1]], 1.0 * grain_scale)).outputs[0]
    rnd = nt.n('ShaderNodeObjectInfo').outputs['Random']
    v = nt.vmath('ADD', v, nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', rnd, 13.0), Y=nt.math('MULTIPLY', rnd, 7.0), Z=0.0).outputs[0])
    warp = _noise(nt, v, 1.5, 3, 0.5)
    rings = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', Vector=v, Scale=22.0, Distortion=9.0, Detail=3.0, Detail_Scale=1.5)
    fine = _noise(nt, nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', sep.outputs[a], 3.0), Y=nt.math('MULTIPLY', sep.outputs[others[0]], 160.0), Z=nt.math('MULTIPLY', sep.outputs[others[1]], 160.0)).outputs[0], 1.0, 4, 0.6)
    g = nt.math('MULTIPLY_ADD', rings.outputs['Factor'], 0.6, nt.math('MULTIPLY', fine, 0.4))
    col = nt.mix(nt.math('POWER', g, 1.6), base, dark)
    col = _tint(nt, col, _centered(nt, rnd, 0.08))
    hb = nt.math('MULTIPLY_ADD', fine, 1.0 if rough_sawn else 0.3, nt.math('MULTIPLY', g, 0.3))
    bump = nt.n('ShaderNodeBump', Strength=0.35 if rough_sawn else 0.15, Distance=0.001, Height=hb)
    finish(nt, principled(nt, Base_Color=col, Roughness=rough, Normal=bump.outputs[0], Specular_IOR_Level=0.4))
    return m

# ---------------------------------------------------------------------------------------------- misc solids
def simple(name, color, rough=0.5, metal=0.0, spec=0.5, bump=0.0, bump_scale=200.0, coat=0.0, aniso=0.0, sheen=0.0):
    m, nt = new_material(name)
    kw = dict(Base_Color=color, Roughness=rough, Metallic=metal, Specular_IOR_Level=spec)
    if coat: kw['Coat_Weight'] = coat
    if aniso: kw['Anisotropic'] = aniso
    if sheen: kw['Sheen_Weight'] = sheen
    b = principled(nt, **kw)
    if bump:
        P = _pos(nt)
        n = _noise(nt, P, bump_scale, 4, 0.6)
        bb = nt.n('ShaderNodeBump', Strength=bump, Distance=0.0006, Height=n)
        nt.link(bb.outputs[0], b.inputs['Normal'])
    finish(nt, b)
    return m

def standing_seam(name='roof_metal'):
    return simple(name, lin((48, 50, 52)), rough=0.42, metal=0.55, spec=0.5, bump=0.05, bump_scale=30.0)

def stainless(name='stainless'):
    m, nt = new_material(name)
    oc = nt.n('ShaderNodeTexCoord').outputs['Object']
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=oc)
    v = nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', sep.outputs['X'], 2.0), Y=nt.math('MULTIPLY', sep.outputs['Y'], 900.0), Z=nt.math('MULTIPLY', sep.outputs['Z'], 900.0)).outputs[0]
    n = _noise(nt, v, 1.0, 2, 0.5)
    bump = nt.n('ShaderNodeBump', Strength=0.08, Distance=0.0003, Height=n)
    b = principled(nt, Base_Color=lin((196, 196, 192)), Metallic=1.0, Roughness=0.24, Anisotropic=0.6, Normal=bump.outputs[0])
    finish(nt, b)
    return m

def fabric(name='cushion', color=lin((190, 184, 170))):
    m, nt = new_material(name)
    P = _pos(nt)
    w1 = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', Vector=P, Scale=900.0, wave_profile='SIN')
    w2 = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Y', Vector=P, Scale=900.0, wave_profile='SIN')
    h = nt.math('MULTIPLY', w1.outputs['Factor'], w2.outputs['Factor'])
    n = _noise(nt, P, 30.0, 3, 0.5)
    col = _tint(nt, color, _centered(nt, n, 0.04))
    bump = nt.n('ShaderNodeBump', Strength=0.25, Distance=0.0005, Height=h)
    b = principled(nt, Base_Color=col, Roughness=0.92, Sheen_Weight=0.4, Sheen_Roughness=0.4, Normal=bump.outputs[0], Specular_IOR_Level=0.3)
    finish(nt, b)
    return m

def stone_veneer(name='stone_veneer'):
    """Per-stone colour from face attribute 'prand'."""
    m, nt = new_material(name)
    P = _pos(nt)
    prand = _attr(nt, 'prand')
    ramp = nt.n('ShaderNodeValToRGB', Fac=prand)
    cr = ramp.color_ramp
    cols = [(0.0, lin((150, 145, 136))), (0.25, lin((132, 126, 118))), (0.5, lin((158, 150, 136))), (0.72, lin((118, 112, 104))), (0.9, lin((144, 132, 116)))]
    cr.interpolation = 'LINEAR'
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols):
        el.position = p; el.color = (*c, 1.0)
    n1 = _noise(nt, P, 18.0, 6, 0.65)
    n2 = _noise(nt, P, 90.0, 4, 0.6)
    col = _tint(nt, ramp.outputs['Color'], nt.math('MULTIPLY', _centered(nt, n1, 0.14), _centered(nt, n2, 0.08)))
    h = nt.math('MULTIPLY_ADD', n1, 1.0, n2)
    bump = nt.n('ShaderNodeBump', Strength=0.7, Distance=0.004, Height=h)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.9, Normal=bump.outputs[0]))
    return m

def countertop(name='countertop'):
    m, nt = new_material(name)
    P = _pos(nt)
    n1 = _noise(nt, P, 3.0, 5, 0.6)
    n2 = _noise(nt, P, 350.0, 2, 0.5)
    col = nt.mix(n1, lin((196, 193, 186)), lin((178, 175, 168)))
    col = _tint(nt, col, _centered(nt, n2, 0.06))
    finish(nt, principled(nt, Base_Color=col, Roughness=0.28, Specular_IOR_Level=0.5, Coat_Weight=0.15, Coat_Roughness=0.2))
    return m

def water(name='water'):
    m, nt = new_material(name)
    P = _pos(nt)
    n = _noise(nt, P, 6.0, 3, 0.5)
    bump = nt.n('ShaderNodeBump', Strength=0.08, Distance=0.01, Height=n)
    b = principled(nt, Base_Color=(1, 1, 1), Roughness=0.0, IOR=1.333, Transmission_Weight=1.0, Normal=bump.outputs[0])
    lp = nt.n('ShaderNodeLightPath')
    tr = nt.n('ShaderNodeBsdfTransparent')
    mix = nt.n('ShaderNodeMixShader', Fac=lp.outputs['Is Shadow Ray'])
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(tr.outputs[0], mix.inputs[2])
    out = finish(nt, mix)
    vol = nt.n('ShaderNodeVolumeAbsorption', Color=lin((120, 205, 210)), Density=1.3)
    nt.link(vol.outputs[0], out.inputs['Volume'])
    return m

def emission(name, color, strength):
    m, nt = new_material(name)
    e = nt.n('ShaderNodeEmission', Color=color, Strength=strength)
    finish(nt, e)
    return m

def glass(name='glass', tint=(0.9, 0.95, 0.95)):
    m, nt = new_material(name)
    finish(nt, principled(nt, Base_Color=tint, Roughness=0.02, Transmission_Weight=1.0, IOR=1.5))
    return m

def fire_glass(name='fire_glass'):
    """Crushed reflective fire glass (per-face random colour)."""
    m, nt = new_material(name)
    prand = _attr(nt, 'prand')
    ramp = nt.n('ShaderNodeValToRGB', Fac=prand)
    cr = ramp.color_ramp
    cols = [(0.0, lin((30, 40, 48))), (0.5, lin((50, 62, 70))), (1.0, lin((20, 24, 28)))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols):
        el.position = p; el.color = (*c, 1.0)
    finish(nt, principled(nt, Base_Color=ramp.outputs['Color'], Roughness=0.08, Specular_IOR_Level=0.8, Metallic=0.3))
    return m

def leaf(name='leaf', cols=None, translucency=0.35):
    m, nt = new_material(name)
    rnd = nt.n('ShaderNodeObjectInfo').outputs['Random']
    # instance random also used; vary per leaf via attribute if present
    ramp = nt.n('ShaderNodeValToRGB', Fac=rnd)
    cr = ramp.color_ramp
    cols = cols or [(0.0, lin((44, 70, 24))), (0.45, lin((58, 86, 30))), (0.8, lin((72, 98, 34))), (1.0, lin((110, 112, 40)))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols):
        el.position = p; el.color = (*c, 1.0)
    col = ramp.outputs['Color']
    b = principled(nt, Base_Color=col, Roughness=0.5, Specular_IOR_Level=0.4)
    tr = nt.n('ShaderNodeBsdfTranslucent', Color=_tint(nt, col, 1.5))
    mix = nt.n('ShaderNodeMixShader', Fac=translucency)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(tr.outputs[0], mix.inputs[2])
    finish(nt, mix)
    return m

def bark(name='bark', color=lin((84, 74, 64))):
    m, nt = new_material(name)
    oc = nt.n('ShaderNodeTexCoord').outputs['Object']
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=oc)
    v = nt.n('ShaderNodeCombineXYZ', X=nt.math('MULTIPLY', sep.outputs['X'], 30.0), Y=nt.math('MULTIPLY', sep.outputs['Y'], 30.0), Z=nt.math('MULTIPLY', sep.outputs['Z'], 4.0)).outputs[0]
    n = _noise(nt, v, 1.0, 6, 0.6, dist=0.5)
    col = _tint(nt, color, _centered(nt, n, 0.25))
    bump = nt.n('ShaderNodeBump', Strength=0.8, Distance=0.01, Height=n)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.9, Normal=bump.outputs[0]))
    return m

def brick(name='brick_sandy_red'):
    """Sandy light-red brick; per-brick colour from face attribute 'prand'."""
    m, nt = new_material(name)
    P = _pos(nt)
    prand = _attr(nt, 'prand')
    ramp = nt.n('ShaderNodeValToRGB', Fac=prand)
    cr = ramp.color_ramp
    cols = [(0.0, lin((208, 138, 108))), (0.3, lin((216, 146, 114))), (0.55, lin((222, 154, 122))),
            (0.78, lin((210, 142, 112))), (0.9, lin((226, 164, 132))), (1.0, lin((198, 130, 102)))]
    cr.interpolation = 'LINEAR'
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols):
        el.position = p; el.color = (*c, 1.0)
    sand = _noise(nt, P, 420.0, 3, 0.6)
    blot = _noise(nt, P, 22.0, 4, 0.6)
    # sandy speckle: lighter flecks
    fleck = nt.math('GREATER_THAN', sand, 0.62)
    col = nt.mix(nt.math('MULTIPLY', fleck, 0.45), ramp.outputs['Color'], lin((232, 196, 166)))
    col = _tint(nt, col, _centered(nt, blot, 0.08))
    h = nt.math('MULTIPLY_ADD', sand, 1.0, nt.math('MULTIPLY', blot, 0.4))
    bump = nt.n('ShaderNodeBump', Strength=0.45, Distance=0.0012, Height=h)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.9, Normal=bump.outputs[0], Specular_IOR_Level=0.35))
    return m

def mortar_buff(name='mortar_buff'):
    m, nt = new_material(name)
    P = _pos(nt)
    n = _noise(nt, P, 300.0, 3, 0.6)
    col = _tint(nt, lin((196, 188, 174)), _centered(nt, n, 0.08))
    bump = nt.n('ShaderNodeBump', Strength=0.6, Distance=0.001, Height=n)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.97, Normal=bump.outputs[0]))
    return m

def red_sand(name='red_sand'):
    """Southern-Utah red sand / dirt (the existing yard in the owner's photos)."""
    m, nt = new_material(name)
    P = _pos(nt)
    n1 = _noise(nt, P, 0.35, 4, 0.6)
    n2 = _noise(nt, P, 6.0, 5, 0.6)
    n3 = _noise(nt, P, 180.0, 3, 0.6)
    c = nt.mix(n1, lin((190, 104, 70)), lin((206, 122, 84)))
    c = _tint(nt, c, nt.math('MULTIPLY', _centered(nt, n2, 0.10), _centered(nt, n3, 0.12)))
    # footprint ripples / clods
    ripple = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', Vector=P, Scale=9.0, Distortion=6.0, Detail=3.0)
    h = nt.math('ADD', nt.math('MULTIPLY', ripple.outputs['Factor'], 0.25), nt.math('ADD', n2, nt.math('MULTIPLY', n3, 0.5)))
    bump = nt.n('ShaderNodeBump', Strength=0.55, Distance=0.004, Height=h)
    lp = nt.n('ShaderNodeLightPath')
    b = principled(nt, Base_Color=c, Roughness=0.96, Normal=bump.outputs[0], Specular_IOR_Level=0.3)
    fac = nt.math('SUBTRACT', 1.0, nt.math('EXPONENT', nt.math('DIVIDE', lp.outputs['Ray Length'], -900.0)))
    fac = nt.math('MULTIPLY', fac, lp.outputs['Is Camera Ray'])
    em = nt.n('ShaderNodeEmission', Color=(0.28, 0.30, 0.36), Strength=1.0)
    mix = nt.n('ShaderNodeMixShader', Fac=fac)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(em.outputs[0], mix.inputs[2])
    finish(nt, mix)
    return m

def stucco(name='stucco', color=(222, 210, 194)):
    m, nt = new_material(name)
    P = _pos(nt)
    n1 = _noise(nt, P, 90.0, 4, 0.7)
    n2 = _noise(nt, P, 1.2, 3, 0.5)
    col = _tint(nt, lin(color), nt.math('MULTIPLY', _centered(nt, n2, 0.03), _centered(nt, n1, 0.03)))
    bump = nt.n('ShaderNodeBump', Strength=0.35, Distance=0.002, Height=n1)
    finish(nt, principled(nt, Base_Color=col, Roughness=0.9, Normal=bump.outputs[0]))
    return m

def dry_weed(name='dry_weed'):
    m, nt = new_material(name)
    rnd = nt.n('ShaderNodeObjectInfo').outputs['Random']
    ramp = nt.n('ShaderNodeValToRGB', Fac=rnd)
    cr = ramp.color_ramp
    cols = [(0.0, lin((120, 118, 66))), (0.5, lin((150, 138, 84))), (0.8, lin((96, 110, 52))), (1.0, lin((168, 150, 98)))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols): el.position = p; el.color = (*c, 1.0)
    b = principled(nt, Base_Color=ramp.outputs['Color'], Roughness=0.6)
    tr = nt.n('ShaderNodeBsdfTranslucent', Color=ramp.outputs['Color'])
    mix = nt.n('ShaderNodeMixShader', Fac=0.25)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(tr.outputs[0], mix.inputs[2])
    finish(nt, mix)
    return m

def red_rock(name='red_rock'):
    """Distant sandstone cliffs: horizontal strata + haze by distance."""
    m, nt = new_material(name)
    P = _pos(nt)
    sep = nt.n('ShaderNodeSeparateXYZ', Vector=P)
    z = sep.outputs['Z']
    warp = _noise(nt, P, 0.02, 3, 0.5)
    zz = nt.math('ADD', z, nt.math('MULTIPLY', warp, 14.0))
    strata = nt.n('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z',
                  Vector=nt.n('ShaderNodeCombineXYZ', X=0.0, Y=0.0, Z=zz).outputs[0], Scale=0.045, Distortion=2.0, Detail=4.0)
    ramp = nt.n('ShaderNodeValToRGB', Fac=strata.outputs['Factor'])
    cr = ramp.color_ramp
    cols = [(0.0, lin((164, 78, 52))), (0.35, lin((188, 98, 64))), (0.6, lin((150, 70, 48))), (0.8, lin((204, 124, 86))), (1.0, lin((176, 92, 60)))]
    while len(cr.elements) < len(cols): cr.elements.new(0.5)
    for el, (p, c) in zip(cr.elements, cols): el.position = p; el.color = (*c, 1.0)
    n = _noise(nt, P, 0.3, 5, 0.6)
    col = _tint(nt, ramp.outputs['Color'], _centered(nt, n, 0.12))
    # scrub on the flatter ground (normal facing up)
    geo = nt.n('ShaderNodeNewGeometry')
    up = nt.n('ShaderNodeSeparateXYZ', Vector=geo.outputs['Normal']).outputs['Z']
    veg = nt.math('MULTIPLY', nt.math('GREATER_THAN', up, 0.82), nt.math('GREATER_THAN', _noise(nt, P, 0.8, 3, 0.5), 0.52))
    col = nt.mix(nt.math('MULTIPLY', veg, 0.7), col, lin((88, 92, 58)))
    bump = nt.n('ShaderNodeBump', Strength=0.8, Distance=0.6, Height=n)
    b = principled(nt, Base_Color=col, Roughness=0.95, Normal=bump.outputs[0])
    lp = nt.n('ShaderNodeLightPath')
    fac = nt.math('SUBTRACT', 1.0, nt.math('EXPONENT', nt.math('DIVIDE', lp.outputs['Ray Length'], -2600.0)))
    fac = nt.math('MULTIPLY', fac, lp.outputs['Is Camera Ray'])
    em = nt.n('ShaderNodeEmission', Color=(0.36, 0.44, 0.56), Strength=1.0)
    mix = nt.n('ShaderNodeMixShader', Fac=fac)
    nt.link(b.outputs[0], mix.inputs[1]); nt.link(em.outputs[0], mix.inputs[2])
    finish(nt, mix)
    return m
