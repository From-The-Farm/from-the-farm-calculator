"""Camera definitions (world metres). House is to the west (-X)."""
import scene

VIEWS = {
    # name: (location, target, lens, extra)
    'aerial_sw':   ((-21.0, -25.0, 15.5), (1.0, 1.5, 0.0), 26, {}),
    'aerial_se':   ((16.8, -20.8, 17.5), (0.8, 2.6, 0.0), 24, {}),
    'aerial_nw':   ((-24.0, 21.0, 15.5), (2.5, -2.5, 0.0), 24, {}),
    'top':         ((0.0, 0.0, 60.0), (0.0, 0.0, 0.0), None, {'ortho': 31.5}),
    'lawn_north':  ((0.2, -4.2, 1.62), (2.6, 10.0, 1.45), 22, {}),
    'lounge':      ((-8.6, 7.4, 1.62), (-1.0, 12.3, 0.9), 22, {}),
    'kitchen':     ((3.0, 9.4, 1.65), (8.7, 11.0, 1.25), 22, {}),
    'pavilion_out':((0.9, 12.15, 1.60), (4.8, -6.0, 0.55), 22, {}),
    'nook':        ((12.6, -16.2, 1.70), (5.4, -4.2, 0.7), 26, {}),
    'sunken':      ((-5.05, 8.05, 1.02), (-7.3, 14.3, 0.05), 20, {}),
    'photo3':      ((-6.85, 5.0, 1.45), (-6.85, 15.0, 0.40), 12.5, {'res': (1600, 1200)}),
    'photo1':      ((-1.4, 7.6, 1.45), (-11.4, 7.6, 0.40), 12.5, {'res': (1600, 1200)}),
    'walk_west':   ((-5.6, -9.0, 1.62), (6.0, 4.0, 1.0), 22, {}),
}

def make(name):
    loc, tgt, lens, ex = VIEWS[name]
    if 'ortho' in ex:
        return scene.camera('Cam_' + name, loc, tgt, ortho=ex['ortho'])
    return scene.camera('Cam_' + name, loc, tgt, lens=lens, dof=ex.get('dof'))
