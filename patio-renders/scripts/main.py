"""Build the full Zitting patio scene."""
import sys, os, time, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import scene, hardscape, grass, pavilion, kitchen, hottub, furniture, context, sunken, existing, plan as P
from bl import coll

def build(grass_on=True, trees_on=True, lawn_density=420.0, yard_density=260.0):
    t0 = time.time()
    scene.reset()
    cH = coll('Hardscape'); cP = coll('Pavilion'); cK = coll('Kitchen'); cF = coll('Furniture'); cS = coll('HotTub')
    cC = coll('Context'); cL = coll('NightLights')
    hardscape.build_concrete(cH)
    hardscape.build_pavers(cH, lounge_region=sunken.floor_region(), lounge_dz=-sunken.SUNK)
    sunken.build_sunken(cH)
    from shapely.ops import unary_union
    lawn, yard = hardscape.build_ground(cH, exclude=unary_union([existing.house_footprint().buffer(0.02), existing.patio_poly().buffer(0.02),
                                                                  __import__('shapely.geometry', fromlist=['box']).box(existing.PORCH_X0, existing.HY1, existing.DECK_X1, existing.PORCH_Y + 0.05),
                                                                  __import__('shapely.geometry', fromlist=['box']).box(existing.HX1, existing.HY1 - 5.8, existing.HX1 + 1.7, existing.HY1)]))
    existing.build_patio(cH)
    if grass_on:
        clumps = grass.clump_collection()
        grass.add_grass(lawn, clumps, lawn_density, 1)
        grass.add_grass(yard, existing.weed_collection(), 2.2, 2)
    g = pavilion.build_pavilion(cP)
    lights = pavilion.build_lights(cL, g)
    kitchen.build_kitchen(cK)
    spa = hottub.build_hottub(cS)
    spa_light = hottub.build_spa_light(cL)
    fires = furniture.build_furniture(cF)
    # the hot-tub lounge is sunken 2': drop the tub, its light and the lounge furniture onto the lower floor
    for o in list(cS.objects) + [spa_light]:
        o.location.z -= sunken.SUNK
    for o in cF.objects:
        if o.name.startswith(('SofaN', 'SofaE', 'FireTableRect')):
            o.location.z -= sunken.SUNK
    fires = [(f[0], f[1], f[2] - sunken.SUNK, f[3]) if f[3][0] == 'rect' else f for f in fires]
    context.build_fence(cC)
    existing.build_house(cC)
    existing.build_cliffs(cC)
    if trees_on:
        rng = random.Random(42)
        specs = []
        for x in (-30, -21, -12.5, -3, 5.5, 13.5, 23):
            specs.append((x + rng.uniform(-2, 2), rng.uniform(21.5, 27.0), rng.uniform(8.5, 13.0), rng.uniform(3.2, 4.8), rng.randrange(3)))
        for y in (-13, -3.5, 5.5, 13.5):
            specs.append((rng.uniform(19.0, 25.0), y + rng.uniform(-2, 2), rng.uniform(8.5, 12.5), rng.uniform(3.2, 4.6), rng.randrange(3)))
        for x in (-26, -16, -6.5, 3.5, 12, 21):
            specs.append((x + rng.uniform(-2, 2), -rng.uniform(21.5, 27.0), rng.uniform(8.5, 13.0), rng.uniform(3.2, 4.8), rng.randrange(3)))
        context.build_trees(cC, specs)
        context.build_far_trees(cC)
        context.build_neighbours(cC)
    print('scene built in %.1fs' % (time.time() - t0))
    return dict(pav=g, lights=lights, spa=spa, spa_light=spa_light, fires=fires)

if __name__ == '__main__':
    build()
