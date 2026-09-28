import torch, math, time, model
torch.manual_seed(0)
N, W, H = 3000, 320, 200
means = torch.randn(N, 3) * torch.tensor([3.0, 1.5, 3.0]) + torch.tensor([0, 0, 6.0])
quats = torch.randn(N, 4); ls = torch.log(torch.rand(N, 3) * 0.3 + 0.01); ol = torch.randn(N)
a = 0.3; R = torch.tensor([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]], dtype=torch.float32)
t = torch.tensor([0.2, -0.1, 0.5])
cam = model.Camera(R, t, 280.0, 285.0, 161.0, 99.0, W, H)
t0 = time.time(); e = model.ext(); print('compile %.1fs' % (time.time() - t0))
m2, co, dp, ex, op = e.project_forward(means, quats, ls, ol, R, t, cam.fx, cam.fy, cam.cx, cam.cy, W, H, 0.1, 0.3)
P = model.project(means.clone().requires_grad_(True), quats.clone().requires_grad_(True), ls.clone().requires_grad_(True), torch.sigmoid(ol), cam)
vis_c = torch.nonzero(ex[:, 0] > 0).squeeze(1)
vis_t = P['idx'][torch.nonzero(P['ok']).squeeze(1)]
print('visible C++ %d torch %d same %s' % (vis_c.numel(), vis_t.numel(), torch.equal(vis_c, vis_t)))
sel = torch.nonzero(P['ok']).squeeze(1)
print('means2d diff', (m2[vis_c] - P['means2d'][sel]).abs().max().item(), 'conic rel', ((co[vis_c] - P['conics'][sel]).abs() / P['conics'][sel].abs().clamp(min=1e-3)).max().item())
# gradients
means_t = means.clone().requires_grad_(True); q_t = quats.clone().requires_grad_(True); ls_t = ls.clone().requires_grad_(True)
P = model.project(means_t, q_t, ls_t, torch.sigmoid(ol), cam)
sel = torch.nonzero(P['ok']).squeeze(1)
gm2 = torch.randn(sel.numel(), 2); gco = torch.randn(sel.numel(), 3) * 10
(P['means2d'][sel] * gm2).sum().add((P['conics'][sel] * gco).sum()).backward()
dm, dq, dls = e.project_backward(means, quats, ls, R, t, cam.fx, cam.fy, cam.cx, cam.cy, W, H, 0.3, vis_c, gm2.contiguous(), gco.contiguous())
for name, a_, b_ in [('means', dm, means_t.grad[vis_c]), ('quats', dq, q_t.grad[vis_c]), ('lscales', dls, ls_t.grad[vis_c])]:
    d = (a_ - b_).abs().max().item(); s = b_.abs().max().item()
    print('%-8s max|diff| %.3e max|ref| %.3e rel %.2e' % (name, d, s, d / s))
# SH
K = 16
sh = torch.randn(N, K, 3) * 0.3
campos = cam.center
for deg in range(4):
    col = e.sh_forward(sh, means, campos, vis_c, deg)
    sh_t = sh.clone().requires_grad_(True)
    dirs = torch.nn.functional.normalize(means[vis_c] - campos, dim=1)
    ref = torch.clamp(model.eval_sh(deg, sh_t[vis_c], dirs) + 0.5, min=0)
    gc = torch.randn_like(ref)
    (ref * gc).sum().backward()
    dsh = e.sh_backward(gc.contiguous(), col, means, campos, vis_c, deg, K)
    print('sh deg', deg, 'fwd', (col - ref).abs().max().item(), 'bwd', (dsh - sh_t.grad[vis_c]).abs().max().item())
# adam
p = torch.randn(100, 4); g = torch.randn(30, 4); idx = torch.randperm(100)[:30].sort().values
m = torch.zeros(100, 4); v = torch.zeros(100, 4)
pt = p.clone().requires_grad_(True); opt = torch.optim.Adam([pt], lr=0.01, eps=1e-15)
full = torch.zeros(100, 4); full[idx] = g; pt.grad = full; opt.step()
e.adam_rows(p, g.contiguous(), m, v, idx, 0.01, 0.9, 0.999, 1e-15, 1 - 0.9, 1 - 0.999)
print('adam rows diff', (p[idx] - pt.detach()[idx]).abs().max().item())
