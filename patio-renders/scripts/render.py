"""Render driver: python3 render.py VIEW[,VIEW...]  (env: SAMPLES, RX, RY, OUT, MODE)"""
import sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import main, scene, views, dusk, pavilion
from bl import coll

env = os.environ.get
OUT = env('OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'renders', 'png'))
os.makedirs(OUT, exist_ok=True)

ROOF_PREFIX = ('RoofMetal', 'Deck', 'Rafter', 'RidgeBeam', 'Fascia', 'Barge', 'Principal', 'KingPost', 'Strut', 'Tie', 'Downlight')

def set_roof(visible):
    for o in bpy.data.objects:
        if o.name.startswith(ROOF_PREFIX) or o.name.startswith(('Beam', 'Brace')):
            o.hide_render = not visible

def day(elev=32.0, az=215.0, clouds=0.42):
    w = bpy.context.scene.world
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name == 'Sun']:
        bpy.data.objects.remove(o)
    return scene.sky(sun_elev_deg=elev, sun_az_deg=az, clouds=clouds)

def night_on(info, on=True):
    for lo in info['lights']:
        lo.data.energy = 75.0 if on else 0.0
    m = bpy.data.materials.get('downlight')
    if m:
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeEmission': n.inputs['Strength'].default_value = 140.0 if on else 0.0
    info['spa_light'].data.energy = 14.0 if on else 0.0
    for o in info.get('flames', []):
        o.hide_render = not on

def main_run(names):
    info = main.build(grass_on=env('GRASS', '1') == '1', trees_on=env('TREES', '1') == '1')
    scene.render_settings(samples=int(env('SAMPLES', 128)), res=(int(env('RX', 1920)), int(env('RY', 1080))),
                          threshold=float(env('THRESH', 0.02)))
    sc = bpy.context.scene
    try:
        sc.cycles.use_camera_cull = True; sc.cycles.camera_cull_margin = 0.15
        for o in bpy.data.objects:
            if o.name.startswith(('Lawn_', 'Tree', 'FarTree')):
                o.cycles.use_camera_cull = True
    except Exception as e:
        print('cull err', e)
    info['flames'] = dusk.add_flames(coll('NightLights'), info['fires'])
    night_on(info, False)
    for name in names:
        dusk_mode = name.endswith('_dusk')
        base = name.replace('_dusk', '').replace('_noroof', '')
        if dusk_mode:
            day(elev=float(env('DUSK_ELEV', -2.5)), az=float(env('DUSK_AZ', 250)), clouds=0.30)
            sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = float(env('DUSK_SKY', 0.28))
            sun = bpy.data.objects['Sun']; sun.data.energy = 0.0
            sc.view_settings.exposure = float(env('DUSK_EXP', 3.3))
            night_on(info, True)
        elif base == 'top':
            day(elev=64.0, az=205.0, clouds=0.0)
            sc.view_settings.exposure = float(env('TOP_EXP', 0.3))
            night_on(info, False)
        else:
            day(elev=float(env('ELEV', 38.0)), az=float(env('AZ', 215.0)))
            sc.view_settings.exposure = float(env('EXP', 0.25))
            night_on(info, False)
        set_roof(not name.endswith('_noroof'))
        sc.cycles.samples = int(env('SAMPLES', 128)) * (2 if dusk_mode else 1)
        cam = views.make(base)
        sc.camera = cam
        ex = views.VIEWS[base][3]
        if base == 'top':
            sc.render.resolution_x, sc.render.resolution_y = int(env('TX', 1400)), int(env('TY', 1800))
        elif 'res' in ex:
            k = int(env('RX', 1920)) / 1920.0
            sc.render.resolution_x, sc.render.resolution_y = int(ex['res'][0] * k), int(ex['res'][1] * k)
        else:
            sc.render.resolution_x, sc.render.resolution_y = int(env('RX', 1920)), int(env('RY', 1080))
        sc.render.filepath = os.path.join(OUT, '%s.png' % name)
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print('RENDERED %s in %.1fs' % (name, time.time() - t), flush=True)
    if env('SAVE'):
        bpy.ops.wm.save_as_mainfile(filepath=env('SAVE'), compress=True)

if __name__ == '__main__':
    main_run(sys.argv[1].split(','))
