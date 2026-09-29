import sys, json, math, numpy as np
sys.path.insert(0, 'irr')
import layout as LY
FT = LY.FT
S = 24 * FT
best = None
for seed in (1, 2, 3, 4, 5, 6):
    hs = LY.edge_heads(S)
    hs, real, ev = LY.greedy_interior(hs, S, S)
    hs2, real2, ev2 = LY.optimize(hs, S, iters=2200, seed=seed, rmin=22 * FT, rmax=28 * FT)
    sc = LY.score(ev2, len(real2))
    tot = sum(LY.gpm(h['R'], h['arc']) for h in real2)
    print('seed %d: heads %d  DU %.3f  SC %.2f  over %.1f%%  dry %.2f%%  GPM %.1f  score %.4f' % (seed, len(real2), ev2['du'], ev2['sc'], 100 * ev2['over'], 100 * ev2['dry'], tot, sc))
    if best is None or sc > best[0]: best = (sc, hs2, real2, ev2, seed)
sc, hs, real, ev, seed = best
print('best seed', seed)
json.dump(dict(heads_param=hs, heads=real, du=ev['du'], sc=ev['sc'], over=ev['over'], dry=ev['dry']), open('irr/final_heads.json', 'w'), indent=1)
import plot
plot.draw(real, ev, 'irr/final.png', 'final: %d heads  DU %.2f' % (len(real), ev['du']))
for i, h in enumerate(real):
    print('%2d %-4s (%6.2f, %6.2f)  R %.1f ft  arc %3.0f  start %5.1f  GPM %.2f' % (i, h['kind'], h['x'], h['y'], h['R'] / FT, h['arc'], h['a0'], LY.gpm(h['R'], h['arc'])))
