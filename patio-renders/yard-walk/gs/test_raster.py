import time, torch, math
import model
torch.manual_seed(0)
W, H, M = 50, 37, 60
means2d = torch.rand(M, 2) * torch.tensor([W, H]) * 1.2 - 5
L = torch.randn(M, 2, 2) * 3.0
cov = L @ L.transpose(1, 2) + torch.eye(2) * 0.5
inv = torch.linalg.inv(cov)
conics = torch.stack([inv[:, 0, 0], inv[:, 0, 1], inv[:, 1, 1]], 1)
colors = torch.rand(M, 3)
opac = torch.rand(M) * 0.5 + 0.05
depths = torch.rand(M) * 10
bg = torch.tensor([0.2, 0.3, 0.4])
k = torch.sqrt(torch.clamp(2 * torch.log(255 * opac), min=0))
ex = torch.stack([k * torch.sqrt(cov[:, 0, 0]), k * torch.sqrt(cov[:, 1, 1])], 1)

t0 = time.time(); e = model.ext(); print('compiled in %.1fs' % (time.time() - t0))
order = torch.argsort(depths)
offsets, ids = e.bin_gaussians(means2d.contiguous(), ex.contiguous(), order, W, H)
args = [x.clone().requires_grad_(True) for x in (means2d, conics, colors, opac)]
img, fT = model._Raster.apply(*args, offsets, ids, W, H, bg, None)
ref_args = [x.clone().requires_grad_(True) for x in (means2d, conics, colors, opac)]
ref = model.ref_rasterize(*ref_args, depths, W, H, bg)
print('forward max abs diff', (img - ref).abs().max().item(), 'min finalT', fT.min().item())
gout = torch.randn(H, W, 3)
(img * gout).sum().backward()
(ref * gout).sum().backward()
for name, a, b in zip(['means2d', 'conics', 'colors', 'opac'], args, ref_args):
    d = (a.grad - b.grad).abs().max().item(); s = b.grad.abs().max().item()
    print('%-8s max|diff| %.3e  max|ref| %.3e  rel %.2e' % (name, d, s, d / max(s, 1e-12)))
