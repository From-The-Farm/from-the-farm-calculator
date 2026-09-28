"""Coordinate frames. SfM world (units u) -> levelled (x_l = RL (3.19 x - 3.19 c0)) -> plan metres.
plan: p_xy = k R(-theta) (l_xy - t);  p_z = k l_z + Z0  (Z0 puts the lawn grade at plan z = 0)."""
import json, math, numpy as np
_lev = json.load(open('align/level_g2.json')); RL = np.array(_lev['R']); C0 = np.array(_lev['c0']); S = _lev['s']
SIM = json.load(open('align/plan_sim.json')); K = SIM['k']; TH = SIM['theta']; T = np.array([SIM['tx'], SIM['ty']])
Z0 = 0.2
_c, _s = math.cos(-TH), math.sin(-TH)
def lev2plan(L):
    L = np.atleast_2d(np.asarray(L, float)); d = L[:, :2] - T
    xy = K * np.c_[_c * d[:, 0] - _s * d[:, 1], _s * d[:, 0] + _c * d[:, 1]]
    return np.c_[xy, K * L[:, 2] + Z0] if L.shape[1] > 2 else xy
def plan2lev(P):
    P = np.atleast_2d(np.asarray(P, float)); c, s = math.cos(TH), math.sin(TH)
    xy = P[:, :2] / K; xy = np.c_[c * xy[:, 0] - s * xy[:, 1], s * xy[:, 0] + c * xy[:, 1]] + T
    return np.c_[xy, (P[:, 2] - Z0) / K] if P.shape[1] > 2 else xy
def sfm2lev(X):
    X = np.atleast_2d(np.asarray(X, float)); return (S * X - S * C0) @ RL.T
def lev2sfm(L):
    L = np.atleast_2d(np.asarray(L, float)); return (L @ RL) / S + C0
def sfm2plan(X): return lev2plan(sfm2lev(X))
def plan2sfm(P): return lev2sfm(plan2lev(P))
# plan rotation as a 3x3 acting on levelled vectors (for quaternions): plan = K * Rz(-TH) * lev
RZ = np.array([[_c, -_s, 0], [_s, _c, 0], [0, 0, 1.0]])
