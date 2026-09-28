import os; os.environ.setdefault('OMP_WAIT_POLICY', 'PASSIVE')
import time, torch, train, model
E = model.ext()
torch.manual_seed(0)
for (W, H) in [(37, 29), (960, 540)]:
    x = torch.rand(H, W, 3); gt = torch.rand(H, W, 3)
    xr = x.clone().requires_grad_(True)
    ref = 0.8 * (xr - gt).abs().mean() + 0.2 * (1 - train.ssim(xr.permute(2, 0, 1)[None], gt.permute(2, 0, 1)[None]))
    ref.backward()
    t0 = time.perf_counter(); l, d, ss = E.loss_l1_ssim(x, gt, 0.2); t1 = time.perf_counter()
    print(W, H, 'loss', float(l), float(ref), 'grad maxdiff %.3e (max %.3e)' % ((d - xr.grad).abs().max(), xr.grad.abs().max()), 'time %.4f' % (t1 - t0))
