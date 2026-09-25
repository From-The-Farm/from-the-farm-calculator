"""World (physical sky), sun, render + colour settings, cameras."""
import math
import bpy
from mathutils import Vector, Euler, Matrix

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def render_settings(samples=256, res=(1920, 1080), threshold=0.02):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = threshold
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces = 10; cy.diffuse_bounces = 4; cy.glossy_bounces = 4
    cy.transmission_bounces = 10; cy.transparent_max_bounces = 12; cy.volume_bounces = 1
    cy.sample_clamp_indirect = 8.0
    cy.caustics_reflective = False; cy.caustics_refractive = False
    cy.use_light_tree = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.threads_mode = 'AUTO'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as e:
        print('look err', e)
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'

def sky(sun_elev_deg=32.0, sun_az_deg=215.0, strength=0.07, sun_strength=4.0, sun_angle_deg=0.6, air=1.0, aerosol=2.0, clouds=0.42, cloud_tint=(1.0, 1.0, 1.0), sun_color=(1.0, 0.93, 0.84), light_sat=0.55):
    """sun_az measured clockwise from +Y (north). Returns sun object."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new('Sky'); sc.world = w
    try: w.use_nodes = True
    except Exception: pass
    nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    skyn = nt.nodes.new('ShaderNodeTexSky')
    skyn.sky_type = 'MULTIPLE_SCATTERING'
    skyn.sun_disc = False
    skyn.sun_elevation = math.radians(sun_elev_deg)
    # Blender sky rotation: 0 = sun toward +Y? we compute from the vector
    skyn.sun_rotation = math.radians(sun_az_deg)
    skyn.altitude = 1400.0
    skyn.air_density = air
    skyn.aerosol_density = aerosol
    bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputWorld')
    sky_col = skyn.outputs[0]
    if clouds:
        sky_col = _clouds(nt, sky_col, clouds, cloud_tint)
    # lighting sees a less saturated sky (real skylight in shadows reads grey-blue, not navy);
    # camera rays still see the full blue sky
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = light_sat
    hs.inputs['Value'].default_value = 1.08
    nt.links.new(sky_col, hs.inputs['Color'])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs['Factor'])
    nt.links.new(hs.outputs[0], mx.inputs[6]); nt.links.new(sky_col, mx.inputs[7])
    nt.links.new(mx.outputs[2], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
    # sun lamp
    ld = bpy.data.lights.new('Sun', 'SUN'); ld.energy = sun_strength; ld.angle = math.radians(sun_angle_deg)
    ld.color = sun_color
    so = bpy.data.objects.new('Sun', ld); sc.collection.objects.link(so)
    el = math.radians(sun_elev_deg); az = math.radians(sun_az_deg)
    # direction TO the sun
    d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    so.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return so, skyn, bg

def camera(name, loc, target, lens=28.0, sensor=36.0, ortho=None, dof=None, shift=(0, 0)):
    cd = bpy.data.cameras.new(name)
    cd.sensor_width = sensor
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_start = 0.05; cd.clip_end = 600.0
    cd.shift_x, cd.shift_y = shift
    if dof:
        cd.dof.use_dof = True; cd.dof.focus_distance = dof[0]; cd.dof.aperture_fstop = dof[1]
    co = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return co

def _clouds(nt, sky_col, cover, tint):
    """Cumulus-ish cloud layer projected on a plane (direction.xy / direction.z)."""
    N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sep.inputs[0])
    # Generated coords on the world = view direction
    z = N.new('ShaderNodeMath'); z.operation = 'MAXIMUM'; L.new(sep.outputs['Z'], z.inputs[0]); z.inputs[1].default_value = 0.02
    px = N.new('ShaderNodeMath'); px.operation = 'DIVIDE'; L.new(sep.outputs['X'], px.inputs[0]); L.new(z.outputs[0], px.inputs[1])
    py = N.new('ShaderNodeMath'); py.operation = 'DIVIDE'; L.new(sep.outputs['Y'], py.inputs[0]); L.new(z.outputs[0], py.inputs[1])
    cv = N.new('ShaderNodeCombineXYZ'); L.new(px.outputs[0], cv.inputs[0]); L.new(py.outputs[0], cv.inputs[1]); cv.inputs[2].default_value = 3.1
    nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'
    L.new(cv.outputs[0], nz.inputs['Vector']); nz.inputs['Scale'].default_value = 0.55; nz.inputs['Detail'].default_value = 9.0
    nz.inputs['Roughness'].default_value = 0.62; nz.inputs['Distortion'].default_value = 0.25
    mr = N.new('ShaderNodeMapRange'); L.new(nz.outputs['Factor'], mr.inputs['Value'])
    mr.inputs['From Min'].default_value = 1.0 - cover * 0.95; mr.inputs['From Max'].default_value = 1.0 - cover * 0.95 + 0.22
    # fade near the horizon
    hz = N.new('ShaderNodeMapRange'); L.new(sep.outputs['Z'], hz.inputs['Value'])
    hz.inputs['From Min'].default_value = 0.03; hz.inputs['From Max'].default_value = 0.25
    m = N.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; L.new(mr.outputs[0], m.inputs[0]); L.new(hz.outputs[0], m.inputs[1])
    # cloud shading: bright tops, greyer bases (use a second noise as fake density)
    nz2 = N.new('ShaderNodeTexNoise'); L.new(cv.outputs[0], nz2.inputs['Vector']); nz2.inputs['Scale'].default_value = 1.6; nz2.inputs['Detail'].default_value = 6.0
    shade = N.new('ShaderNodeMapRange'); L.new(nz2.outputs['Factor'], shade.inputs['Value'])
    shade.inputs['To Min'].default_value = 0.62; shade.inputs['To Max'].default_value = 1.0
    cc = N.new('ShaderNodeCombineColor')
    for i, t in enumerate(tint):
        mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; L.new(shade.outputs[0], mm.inputs[0]); mm.inputs[1].default_value = 9.0 * t
        L.new(mm.outputs[0], cc.inputs[i])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
    L.new(m.outputs[0], mix.inputs['Factor']); L.new(sky_col, mix.inputs[6]); L.new(cc.outputs[0], mix.inputs[7])
    return mix.outputs[2]
