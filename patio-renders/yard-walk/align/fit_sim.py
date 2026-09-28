import json, math, sys, numpy as np
k = float(sys.argv[1]) if len(sys.argv) > 1 else 1.14
off = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0      # fence offset from walk track (units)
ins = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2      # plan inset from fences (units)
dA = np.array([0.498, 0.867]); nA_in = np.array([0.867, -0.498])
pA = np.array([-10.36, 8.74]) - off * nA_in
dB = np.array([-0.847, 0.532]); nB_in = np.array([0.532, 0.847])
pB = np.array([-14.42, -4.11]) - off * nB_in
M = np.array([dA, -dB]).T; t, u = np.linalg.solve(M, pB - pA)
corner = pA + t * dA
th = math.atan2(0.498, -0.867)     # plan +y -> (-sin, cos) = -dA
s = 1 / k
c, sn = math.cos(th), math.sin(th)
ne = np.array([11.2, 14.25])
ne_l = s * np.array([c * ne[0] - sn * ne[1], sn * ne[0] + c * ne[1]])
target = corner + ins * nA_in + ins * nB_in
tr = target - ne_l
sim = dict(s=s, theta=th, tx=float(tr[0]), ty=float(tr[1]), k=k, corner=corner.tolist())
json.dump(sim, open(sys.argv[4] if len(sys.argv) > 4 else 'align/sim_v2.json', 'w'))
print('corner', corner.round(2), 'theta deg %.1f' % math.degrees(th), 'sim', {a: round(b, 3) if isinstance(b, float) else b for a, b in sim.items()})
