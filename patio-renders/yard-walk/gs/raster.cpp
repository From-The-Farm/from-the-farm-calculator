// CPU tile rasterizer for 3D Gaussian splatting: forward and backward, OpenMP + SIMD.
//
// Conventions
//   means2d  (M,2)  pixel coordinates, pixel (x,y) has its centre at (x+0.5, y+0.5)
//   conics   (M,3)  (a,b,c) of the inverse 2D covariance: power = -0.5(a dx^2 + c dy^2) - b dx dy
//   colors   (M,3)
//   opac     (M)    in (0,1)
//   ext      (M,2)  half extents of the screen-space bounding box in pixels (<=0: skip)
//   order    (M)    int64 indices sorted front to back
// Each tile's list is depth ordered because gaussians are binned in `order`.
#include <torch/extension.h>
#include <omp.h>
#include <vector>
#include <cmath>
#include <math.h>
#include <algorithm>
#include <cstring>

namespace {

constexpr int TILE = 16;
constexpr int TP = TILE * TILE;
constexpr float ALPHA_MIN = 1.f / 255.f;
constexpr float ALPHA_MAX = 0.99f;
constexpr float T_EPS = 1e-4f;

struct G9 { float mx, my, ca, cb, cc, op, r, g, b; };

inline void tile_rect(float mx, float my, float ex, float ey, int tx_n, int ty_n,
                      int &x0, int &x1, int &y0, int &y1) {
  x0 = std::max(0, (int)std::floor((mx - ex) / TILE));
  x1 = std::min(tx_n - 1, (int)std::floor((mx + ex) / TILE));
  y0 = std::max(0, (int)std::floor((my - ey) / TILE));
  y1 = std::min(ty_n - 1, (int)std::floor((my + ey) / TILE));
}

}  // namespace

// Returns (offsets[n_tiles+1] int64, ids[n_pairs] int32)
std::vector<torch::Tensor> bin_gaussians(torch::Tensor means2d, torch::Tensor ext, torch::Tensor order,
                                         int64_t W, int64_t H) {
  const int tx_n = (W + TILE - 1) / TILE, ty_n = (H + TILE - 1) / TILE, n_tiles = tx_n * ty_n;
  const int64_t M = order.size(0);
  const float *m2 = means2d.data_ptr<float>();
  const float *ex = ext.data_ptr<float>();
  const int64_t *ord = order.data_ptr<int64_t>();
  const int nt = omp_get_max_threads();
  std::vector<std::vector<int64_t>> cnt(nt, std::vector<int64_t>(n_tiles, 0));
  // pass 1: counts per thread chunk (chunks are contiguous in depth order)
#pragma omp parallel num_threads(nt)
  {
    const int t = omp_get_thread_num();
    const int64_t a = M * t / nt, b = M * (t + 1) / nt;
    auto &c = cnt[t];
    for (int64_t k = a; k < b; ++k) {
      const int64_t g = ord[k];
      const float exx = ex[2 * g], exy = ex[2 * g + 1];
      if (!(exx > 0.f && exy > 0.f)) continue;
      int x0, x1, y0, y1;
      tile_rect(m2[2 * g], m2[2 * g + 1], exx, exy, tx_n, ty_n, x0, x1, y0, y1);
      for (int y = y0; y <= y1; ++y)
        for (int x = x0; x <= x1; ++x) c[y * tx_n + x]++;
    }
  }
  auto offsets = torch::empty({n_tiles + 1}, torch::kInt64);
  int64_t *off = offsets.data_ptr<int64_t>();
  std::vector<std::vector<int64_t>> start(nt, std::vector<int64_t>(n_tiles, 0));
  int64_t run = 0;
  for (int tl = 0; tl < n_tiles; ++tl) {
    off[tl] = run;
    for (int t = 0; t < nt; ++t) { start[t][tl] = run; run += cnt[t][tl]; }
  }
  off[n_tiles] = run;
  auto ids = torch::empty({run}, torch::kInt32);
  int32_t *id = ids.data_ptr<int32_t>();
#pragma omp parallel num_threads(nt)
  {
    const int t = omp_get_thread_num();
    const int64_t a = M * t / nt, b = M * (t + 1) / nt;
    auto &s = start[t];
    for (int64_t k = a; k < b; ++k) {
      const int64_t g = ord[k];
      const float exx = ex[2 * g], exy = ex[2 * g + 1];
      if (!(exx > 0.f && exy > 0.f)) continue;
      int x0, x1, y0, y1;
      tile_rect(m2[2 * g], m2[2 * g + 1], exx, exy, tx_n, ty_n, x0, x1, y0, y1);
      for (int y = y0; y <= y1; ++y)
        for (int x = x0; x <= x1; ++x) id[s[y * tx_n + x]++] = (int32_t)g;
    }
  }
  return {offsets, ids};
}

static std::vector<G9> pack(torch::Tensor means2d, torch::Tensor conics, torch::Tensor colors, torch::Tensor opac) {
  const int64_t M = means2d.size(0);
  std::vector<G9> P(M);
  const float *m2 = means2d.data_ptr<float>(), *co = conics.data_ptr<float>(), *cl = colors.data_ptr<float>(),
              *op = opac.data_ptr<float>();
#pragma omp parallel for schedule(static)
  for (int64_t i = 0; i < M; ++i)
    P[i] = {m2[2 * i], m2[2 * i + 1], co[3 * i], co[3 * i + 1], co[3 * i + 2], op[i], cl[3 * i], cl[3 * i + 1], cl[3 * i + 2]};
  return P;
}

// Returns (image (H,W,3), final_T (H,W), n_contrib (H,W) int32)
std::vector<torch::Tensor> render_forward(torch::Tensor means2d, torch::Tensor conics, torch::Tensor colors,
                                          torch::Tensor opac, torch::Tensor offsets, torch::Tensor ids,
                                          int64_t W, int64_t H, torch::Tensor bg) {
  const int tx_n = (W + TILE - 1) / TILE, ty_n = (H + TILE - 1) / TILE, n_tiles = tx_n * ty_n;
  auto img = torch::empty({H, W, 3}, torch::kFloat32);
  auto fT = torch::empty({H, W}, torch::kFloat32);
  auto nc = torch::empty({H, W}, torch::kInt32);
  float *out = img.data_ptr<float>(), *outT = fT.data_ptr<float>();
  int32_t *outN = nc.data_ptr<int32_t>();
  const int64_t *off = offsets.data_ptr<int64_t>();
  const int32_t *id = ids.data_ptr<int32_t>();
  const float bgr = bg[0].item<float>(), bgg = bg[1].item<float>(), bgb = bg[2].item<float>();
  const std::vector<G9> P = pack(means2d, conics, colors, opac);
  const G9 *Pd = P.data();

#pragma omp parallel for schedule(dynamic, 2)
  for (int tl = 0; tl < n_tiles; ++tl) {
    const int tx = tl % tx_n, ty = tl / tx_n;
    const int px0 = tx * TILE, py0 = ty * TILE;
    alignas(64) float pxf[TP], pyf[TP], T[TP], C0[TP], C1[TP], C2[TP], done[TP];
    alignas(64) int32_t last[TP];
    int n_active = 0;
    for (int p = 0; p < TP; ++p) {
      const int x = px0 + (p % TILE), y = py0 + (p / TILE);
      pxf[p] = x + 0.5f; pyf[p] = y + 0.5f;
      T[p] = 1.f; C0[p] = C1[p] = C2[p] = 0.f; last[p] = 0;
      const bool in = (x < W) && (y < H);
      done[p] = in ? 0.f : 1.f;
      n_active += in;
    }
    const int64_t s = off[tl], e = off[tl + 1];
    for (int64_t k = s; k < e; ++k) {
      const G9 g = Pd[id[k]];
      const int32_t rel = (int32_t)(k - s + 1);
#pragma omp simd
      for (int p = 0; p < TP; ++p) {
        const float dx = g.mx - pxf[p], dy = g.my - pyf[p];
        const float power = -0.5f * (g.ca * dx * dx + g.cc * dy * dy) - g.cb * dx * dy;
        const float alpha = std::min(ALPHA_MAX, g.op * expf(power));
        const bool ok = (power <= 0.f) & (alpha >= ALPHA_MIN) & (done[p] == 0.f);
        const float nT = T[p] * (1.f - alpha);
        const bool stop = ok & (nT <= T_EPS);
        const bool add = ok & !stop;
        const float w = add ? alpha * T[p] : 0.f;
        C0[p] += w * g.r; C1[p] += w * g.g; C2[p] += w * g.b;
        T[p] = add ? nT : T[p];
        last[p] = add ? rel : last[p];
        done[p] = stop ? 1.f : done[p];
      }
      if (((k - s) & 31) == 31) {
        float sd = 0.f;
        for (int p = 0; p < TP; ++p) sd += done[p];
        if (sd >= TP) break;
      }
    }
    for (int p = 0; p < TP; ++p) {
      const int x = px0 + (p % TILE), y = py0 + (p / TILE);
      if (x >= W || y >= H) continue;
      const int64_t i = (int64_t)y * W + x;
      out[3 * i] = C0[p] + T[p] * bgr;
      out[3 * i + 1] = C1[p] + T[p] * bgg;
      out[3 * i + 2] = C2[p] + T[p] * bgb;
      outT[i] = T[p];
      outN[i] = last[p];
    }
  }
  return {img, fT, nc};
}

// Returns (d_means2d (M,2), d_conics (M,3), d_colors (M,3), d_opac (M), d_means2d_abs (M,2))
std::vector<torch::Tensor> render_backward(torch::Tensor means2d, torch::Tensor conics, torch::Tensor colors,
                                           torch::Tensor opac, torch::Tensor offsets, torch::Tensor ids,
                                           int64_t W, int64_t H, torch::Tensor bg, torch::Tensor fT,
                                           torch::Tensor nc, torch::Tensor dimg) {
  const int tx_n = (W + TILE - 1) / TILE, ty_n = (H + TILE - 1) / TILE, n_tiles = tx_n * ty_n;
  const int64_t M = means2d.size(0);
  const int64_t *off = offsets.data_ptr<int64_t>();
  const int32_t *id = ids.data_ptr<int32_t>();
  const float *Tf = fT.data_ptr<float>(), *dI = dimg.data_ptr<float>();
  const int32_t *NC = nc.data_ptr<int32_t>();
  const float bgr = bg[0].item<float>(), bgg = bg[1].item<float>(), bgb = bg[2].item<float>();
  const std::vector<G9> P = pack(means2d, conics, colors, opac);
  const G9 *Pd = P.data();
  const int nt = omp_get_max_threads();
  constexpr int NG = 11;  // mx, my, a, b, c, op, r, g, b, |mx|, |my|
  std::vector<float> acc((size_t)nt * M * NG, 0.f);

#pragma omp parallel num_threads(nt)
  {
    float *A = acc.data() + (size_t)omp_get_thread_num() * M * NG;
#pragma omp for schedule(dynamic, 2)
    for (int tl = 0; tl < n_tiles; ++tl) {
      const int tx = tl % tx_n, ty = tl / tx_n;
      const int px0 = tx * TILE, py0 = ty * TILE;
      alignas(64) float pxf[TP], pyf[TP], T[TP], A0[TP], A1[TP], A2[TP], g0[TP], g1[TP], g2[TP];
      alignas(64) int32_t ncon[TP];
      int32_t maxn = 0;
      for (int p = 0; p < TP; ++p) {
        const int x = px0 + (p % TILE), y = py0 + (p / TILE);
        pxf[p] = x + 0.5f; pyf[p] = y + 0.5f;
        A0[p] = bgr; A1[p] = bgg; A2[p] = bgb;
        if (x < W && y < H) {
          const int64_t i = (int64_t)y * W + x;
          T[p] = Tf[i]; ncon[p] = NC[i];
          g0[p] = dI[3 * i]; g1[p] = dI[3 * i + 1]; g2[p] = dI[3 * i + 2];
        } else {
          T[p] = 1.f; ncon[p] = 0; g0[p] = g1[p] = g2[p] = 0.f;
        }
        maxn = std::max(maxn, ncon[p]);
      }
      const int64_t s = off[tl];
      for (int32_t j = maxn - 1; j >= 0; --j) {
        const int32_t gid = id[s + j];
        const G9 g = Pd[gid];
        float s_mx = 0, s_my = 0, s_a = 0, s_b = 0, s_c = 0, s_op = 0, s_r = 0, s_g = 0, s_bb = 0, s_amx = 0, s_amy = 0;
#pragma omp simd reduction(+ : s_mx, s_my, s_a, s_b, s_c, s_op, s_r, s_g, s_bb, s_amx, s_amy)
        for (int p = 0; p < TP; ++p) {
          const float dx = g.mx - pxf[p], dy = g.my - pyf[p];
          const float power = -0.5f * (g.ca * dx * dx + g.cc * dy * dy) - g.cb * dx * dy;
          const float G = expf(power);
          const float araw = g.op * G;
          const float alpha = std::min(ALPHA_MAX, araw);
          const bool ok = (j < ncon[p]) & (power <= 0.f) & (alpha >= ALPHA_MIN);
          const float Ti = T[p] / (1.f - alpha);
          const float dLda = Ti * ((g.r - A0[p]) * g0[p] + (g.g - A1[p]) * g1[p] + (g.b - A2[p]) * g2[p]);
          const float m = ok ? 1.f : 0.f;
          const float wc = m * alpha * Ti;
          s_r += wc * g0[p]; s_g += wc * g1[p]; s_bb += wc * g2[p];
          const float mu = (ok & (araw < ALPHA_MAX)) ? 1.f : 0.f;
          s_op += mu * G * dLda;
          const float dLdG = mu * g.op * dLda * G;
          const float vx = dLdG * (-(g.ca * dx + g.cb * dy));
          const float vy = dLdG * (-(g.cc * dy + g.cb * dx));
          s_mx += vx; s_my += vy;
          s_amx += std::fabs(vx); s_amy += std::fabs(vy);
          s_a += dLdG * (-0.5f * dx * dx);
          s_b += dLdG * (-dx * dy);
          s_c += dLdG * (-0.5f * dy * dy);
          A0[p] = ok ? alpha * g.r + (1.f - alpha) * A0[p] : A0[p];
          A1[p] = ok ? alpha * g.g + (1.f - alpha) * A1[p] : A1[p];
          A2[p] = ok ? alpha * g.b + (1.f - alpha) * A2[p] : A2[p];
          T[p] = ok ? Ti : T[p];
        }
        float *a = A + (size_t)gid * NG;
        a[0] += s_mx; a[1] += s_my; a[2] += s_a; a[3] += s_b; a[4] += s_c; a[5] += s_op;
        a[6] += s_r; a[7] += s_g; a[8] += s_bb; a[9] += s_amx; a[10] += s_amy;
      }
    }
  }
  auto dm = torch::empty({M, 2}, torch::kFloat32), dc = torch::empty({M, 3}, torch::kFloat32),
       dcol = torch::empty({M, 3}, torch::kFloat32), dop = torch::empty({M}, torch::kFloat32),
       dabs = torch::empty({M, 2}, torch::kFloat32);
  float *pm = dm.data_ptr<float>(), *pc = dc.data_ptr<float>(), *pcol = dcol.data_ptr<float>(),
        *pop = dop.data_ptr<float>(), *pab = dabs.data_ptr<float>();
#pragma omp parallel for schedule(static)
  for (int64_t i = 0; i < M; ++i) {
    float v[NG] = {0};
    for (int t = 0; t < nt; ++t) {
      const float *a = acc.data() + ((size_t)t * M + i) * NG;
      for (int q = 0; q < NG; ++q) v[q] += a[q];
    }
    pm[2 * i] = v[0]; pm[2 * i + 1] = v[1];
    pc[3 * i] = v[2]; pc[3 * i + 1] = v[3]; pc[3 * i + 2] = v[4];
    pop[i] = v[5];
    pcol[3 * i] = v[6]; pcol[3 * i + 1] = v[7]; pcol[3 * i + 2] = v[8];
    pab[2 * i] = v[9]; pab[2 * i + 1] = v[10];
  }
  return {dm, dc, dcol, dop, dabs};
}

// Depth (expected, alpha weighted) and alpha maps for a set of gaussians: used for alignment and masks.
std::vector<torch::Tensor> render_depth(torch::Tensor means2d, torch::Tensor conics, torch::Tensor depths,
                                        torch::Tensor opac, torch::Tensor offsets, torch::Tensor ids,
                                        int64_t W, int64_t H) {
  auto cols = torch::stack({depths, torch::ones_like(depths), torch::zeros_like(depths)}, 1).contiguous();
  auto bg = torch::zeros({3}, torch::kFloat32);
  auto r = render_forward(means2d, conics, cols, opac, offsets, ids, W, H, bg);
  return {r[0], r[1]};
}


// ---------------------------------------------------------------------------------------------
// Fused projection, SH and a row-selective Adam, so a training step never runs large torch graphs.

namespace {
struct Cam { float R[9], t[3], fx, fy, cx, cy; int W, H; };
inline Cam make_cam(torch::Tensor R, torch::Tensor t, double fx, double fy, double cx, double cy, int64_t W, int64_t H) {
  Cam c; auto Ra = R.contiguous(); auto ta = t.contiguous();
  const float *r = Ra.data_ptr<float>(), *tt = ta.data_ptr<float>();
  for (int i = 0; i < 9; ++i) c.R[i] = r[i];
  for (int i = 0; i < 3; ++i) c.t[i] = tt[i];
  c.fx = fx; c.fy = fy; c.cx = cx; c.cy = cy; c.W = W; c.H = H; return c;
}
inline void quat_rot(const float *qu, float *Rq, float *qn) {
  float w = qu[0], x = qu[1], y = qu[2], z = qu[3];
  float n = std::sqrt(w * w + x * x + y * y + z * z);
  if (n < 1e-12f) { w = 1; x = y = z = 0; n = 1; } else { w /= n; x /= n; y /= n; z /= n; }
  qn[0] = w; qn[1] = x; qn[2] = y; qn[3] = z;
  Rq[0] = 1 - 2 * (y * y + z * z); Rq[1] = 2 * (x * y - w * z); Rq[2] = 2 * (x * z + w * y);
  Rq[3] = 2 * (x * y + w * z); Rq[4] = 1 - 2 * (x * x + z * z); Rq[5] = 2 * (y * z - w * x);
  Rq[6] = 2 * (x * z - w * y); Rq[7] = 2 * (y * z + w * x); Rq[8] = 1 - 2 * (x * x + y * y);
}
// Sigma_c = R (Rq S S Rq^T) R^T, also returns M = Rq S
inline void cov_cam(const Cam &c, const float *Rq, const float *s, float *M, float *Sig, float *Sc) {
  for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) M[3 * i + j] = Rq[3 * i + j] * s[j];
  for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) {
    float a = 0; for (int k = 0; k < 3; ++k) a += M[3 * i + k] * M[3 * j + k]; Sig[3 * i + j] = a; }
  float T1[9];
  for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) {
    float a = 0; for (int k = 0; k < 3; ++k) a += c.R[3 * i + k] * Sig[3 * k + j]; T1[3 * i + j] = a; }
  for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j) {
    float a = 0; for (int k = 0; k < 3; ++k) a += T1[3 * i + k] * c.R[3 * j + k]; Sc[3 * i + j] = a; }
}
}  // namespace

// Returns means2d (N,2), conics (N,3), depth (N), ext (N,2) (0 = culled), opac (N)
std::vector<torch::Tensor> project_forward(torch::Tensor means, torch::Tensor quats, torch::Tensor lscales,
                                           torch::Tensor ologit, torch::Tensor R, torch::Tensor t,
                                           double fx, double fy, double cx, double cy, int64_t W, int64_t H,
                                           double near, double eps2d) {
  const Cam c = make_cam(R, t, fx, fy, cx, cy, W, H);
  const int64_t N = means.size(0);
  auto m2 = torch::empty({N, 2}, torch::kFloat32), co = torch::empty({N, 3}, torch::kFloat32),
       dp = torch::empty({N}, torch::kFloat32), ex = torch::empty({N, 2}, torch::kFloat32),
       op = torch::empty({N}, torch::kFloat32);
  const float *pm = means.data_ptr<float>(), *pq = quats.data_ptr<float>(), *ps = lscales.data_ptr<float>(),
              *po = ologit.data_ptr<float>();
  float *om = m2.data_ptr<float>(), *oc = co.data_ptr<float>(), *od = dp.data_ptr<float>(), *oe = ex.data_ptr<float>(),
        *oo = op.data_ptr<float>();
  const float limx = 1.3f * std::max(c.cx, c.W - c.cx) / c.fx, limy = 1.3f * std::max(c.cy, c.H - c.cy) / c.fy;
#pragma omp parallel for schedule(static)
  for (int64_t i = 0; i < N; ++i) {
    const float *m = pm + 3 * i;
    const float x = c.R[0] * m[0] + c.R[1] * m[1] + c.R[2] * m[2] + c.t[0];
    const float y = c.R[3] * m[0] + c.R[4] * m[1] + c.R[5] * m[2] + c.t[1];
    const float z = c.R[6] * m[0] + c.R[7] * m[1] + c.R[8] * m[2] + c.t[2];
    const float o = 1.f / (1.f + std::exp(-po[i]));
    oo[i] = o; od[i] = z;
    oe[2 * i] = 0.f; oe[2 * i + 1] = 0.f;
    om[2 * i] = 0.f; om[2 * i + 1] = 0.f; oc[3 * i] = oc[3 * i + 1] = oc[3 * i + 2] = 0.f;
    if (!(z > near)) continue;
    float Rq[9], qn[4], M[9], Sig[9], Sc[9], s[3];
    quat_rot(pq + 4 * i, Rq, qn);
    for (int k = 0; k < 3; ++k) s[k] = std::exp(ps[3 * i + k]);
    cov_cam(c, Rq, s, M, Sig, Sc);
    const float tx = std::min(limx, std::max(-limx, x / z)) * z, ty = std::min(limy, std::max(-limy, y / z)) * z;
    const float J00 = c.fx / z, J02 = -c.fx * tx / (z * z), J11 = c.fy / z, J12 = -c.fy * ty / (z * z);
    // cov2d = J Sc J^T with J = [[J00,0,J02],[0,J11,J12]]
    const float a = J00 * J00 * Sc[0] + 2 * J00 * J02 * Sc[2] + J02 * J02 * Sc[8] + eps2d;
    const float b = J00 * J11 * Sc[1] + J00 * J12 * Sc[2] + J02 * J11 * Sc[7] + J02 * J12 * Sc[8];
    const float cc = J11 * J11 * Sc[4] + 2 * J11 * J12 * Sc[5] + J12 * J12 * Sc[8] + eps2d;
    const float det = a * cc - b * b;
    if (!(det > 1e-12f)) continue;
    const float mx = c.fx * x / z + c.cx, my = c.fy * y / z + c.cy;
    const float kk2 = 2.f * std::log(std::max(255.f * o, 1e-6f));
    if (!(kk2 > 0.f)) continue;
    const float k = std::sqrt(kk2);
    const float exx = k * std::sqrt(a), eyy = k * std::sqrt(cc);
    if (mx + exx <= 0 || mx - exx >= c.W || my + eyy <= 0 || my - eyy >= c.H) continue;
    om[2 * i] = mx; om[2 * i + 1] = my;
    oc[3 * i] = cc / det; oc[3 * i + 1] = -b / det; oc[3 * i + 2] = a / det;
    oe[2 * i] = exx; oe[2 * i + 1] = eyy;
  }
  return {m2, co, dp, ex, op};
}

// Gradients for the visible rows gidx: returns d_means (M,3), d_quats (M,4), d_lscales (M,3)
std::vector<torch::Tensor> project_backward(torch::Tensor means, torch::Tensor quats, torch::Tensor lscales,
                                            torch::Tensor R, torch::Tensor t, double fx, double fy, double cx, double cy,
                                            int64_t W, int64_t H, double eps2d, torch::Tensor gidx,
                                            torch::Tensor dm2, torch::Tensor dco) {
  const Cam c = make_cam(R, t, fx, fy, cx, cy, W, H);
  const int64_t Mv = gidx.size(0);
  auto gm = torch::empty({Mv, 3}, torch::kFloat32), gq = torch::empty({Mv, 4}, torch::kFloat32),
       gs = torch::empty({Mv, 3}, torch::kFloat32);
  const float *pm = means.data_ptr<float>(), *pq = quats.data_ptr<float>(), *ps = lscales.data_ptr<float>(),
              *pdm = dm2.data_ptr<float>(), *pdc = dco.data_ptr<float>();
  const int64_t *gi = gidx.data_ptr<int64_t>();
  float *om = gm.data_ptr<float>(), *oq = gq.data_ptr<float>(), *os = gs.data_ptr<float>();
  const float limx = 1.3f * std::max(c.cx, c.W - c.cx) / c.fx, limy = 1.3f * std::max(c.cy, c.H - c.cy) / c.fy;
#pragma omp parallel for schedule(static)
  for (int64_t v = 0; v < Mv; ++v) {
    const int64_t i = gi[v];
    const float *m = pm + 3 * i;
    const float x = c.R[0] * m[0] + c.R[1] * m[1] + c.R[2] * m[2] + c.t[0];
    const float y = c.R[3] * m[0] + c.R[4] * m[1] + c.R[5] * m[2] + c.t[1];
    const float z = c.R[6] * m[0] + c.R[7] * m[1] + c.R[8] * m[2] + c.t[2];
    float Rq[9], qn[4], M[9], Sig[9], Sc[9], s[3];
    quat_rot(pq + 4 * i, Rq, qn);
    for (int k = 0; k < 3; ++k) s[k] = std::exp(ps[3 * i + k]);
    cov_cam(c, Rq, s, M, Sig, Sc);
    const float rx = x / z, ry = y / z;
    const bool cxl = rx < -limx || rx > limx, cyl = ry < -limy || ry > limy;
    const float tx = std::min(limx, std::max(-limx, rx)) * z, ty = std::min(limy, std::max(-limy, ry)) * z;
    const float J[6] = {c.fx / z, 0.f, -c.fx * tx / (z * z), 0.f, c.fy / z, -c.fy * ty / (z * z)};
    const float a = J[0] * J[0] * Sc[0] + 2 * J[0] * J[2] * Sc[2] + J[2] * J[2] * Sc[8] + eps2d;
    const float b = J[0] * J[4] * Sc[1] + J[0] * J[5] * Sc[2] + J[2] * J[4] * Sc[7] + J[2] * J[5] * Sc[8];
    const float cc = J[4] * J[4] * Sc[4] + 2 * J[4] * J[5] * Sc[5] + J[5] * J[5] * Sc[8] + eps2d;
    const float det = std::max(a * cc - b * b, 1e-12f);
    const float Q[4] = {cc / det, -b / det, -b / det, a / det};
    // d conic -> d cov2d : G_S = -Q G_Q Q, G_Q = [[ga, gb/2],[gb/2, gc]]
    const float ga = pdc[3 * v], gb = pdc[3 * v + 1], gc = pdc[3 * v + 2];
    const float GQ[4] = {ga, 0.5f * gb, 0.5f * gb, gc};
    float T1[4], GS[4];
    for (int i2 = 0; i2 < 2; ++i2) for (int j2 = 0; j2 < 2; ++j2) T1[2 * i2 + j2] = GQ[2 * i2] * Q[j2] + GQ[2 * i2 + 1] * Q[2 + j2];
    for (int i2 = 0; i2 < 2; ++i2) for (int j2 = 0; j2 < 2; ++j2) GS[2 * i2 + j2] = -(Q[2 * i2] * T1[j2] + Q[2 * i2 + 1] * T1[2 + j2]);
    // d Sc = J^T GS J (3x3);  dJ = 2 GS J Sc (2x3)
    float GSc[9];
    for (int i3 = 0; i3 < 3; ++i3) for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0;
      for (int p = 0; p < 2; ++p) for (int q = 0; q < 2; ++q) acc += J[3 * p + i3] * GS[2 * p + q] * J[3 * q + j3];
      GSc[3 * i3 + j3] = acc; }
    float JS[6], dJ[6];
    for (int p = 0; p < 2; ++p) for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0; for (int k = 0; k < 3; ++k) acc += J[3 * p + k] * Sc[3 * k + j3]; JS[3 * p + j3] = acc; }
    for (int p = 0; p < 2; ++p) for (int j3 = 0; j3 < 3; ++j3) dJ[3 * p + j3] = 2.f * (GS[2 * p] * JS[j3] + GS[2 * p + 1] * JS[3 + j3]);
    // d pc from means2d
    const float dmx = pdm[2 * v], dmy = pdm[2 * v + 1];
    float dx = dmx * c.fx / z, dy = dmy * c.fy / z, dz = -(dmx * c.fx * x + dmy * c.fy * y) / (z * z);
    // d pc from J
    const float dtx_dx = cxl ? 0.f : 1.f, dtx_dz = cxl ? (rx < 0 ? -limx : limx) : 0.f;
    const float dty_dy = cyl ? 0.f : 1.f, dty_dz = cyl ? (ry < 0 ? -limy : limy) : 0.f;
    const float z2 = z * z, z3 = z2 * z;
    dx += dJ[2] * (-c.fx * dtx_dx / z2);
    dy += dJ[5] * (-c.fy * dty_dy / z2);
    dz += dJ[0] * (-c.fx / z2) + dJ[4] * (-c.fy / z2)
        + dJ[2] * (-c.fx * dtx_dz / z2 + 2.f * c.fx * tx / z3)
        + dJ[5] * (-c.fy * dty_dz / z2 + 2.f * c.fy * ty / z3);
    // means: R^T dpc
    om[3 * v] = c.R[0] * dx + c.R[3] * dy + c.R[6] * dz;
    om[3 * v + 1] = c.R[1] * dx + c.R[4] * dy + c.R[7] * dz;
    om[3 * v + 2] = c.R[2] * dx + c.R[5] * dy + c.R[8] * dz;
    // d Sigma (world) = R^T GSc R
    float T2[9], GW[9];
    for (int i3 = 0; i3 < 3; ++i3) for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0; for (int k = 0; k < 3; ++k) acc += c.R[3 * k + i3] * GSc[3 * k + j3]; T2[3 * i3 + j3] = acc; }
    for (int i3 = 0; i3 < 3; ++i3) for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0; for (int k = 0; k < 3; ++k) acc += T2[3 * i3 + k] * c.R[3 * k + j3]; GW[3 * i3 + j3] = acc; }
    // Sigma = M M^T -> dM = (GW + GW^T) M
    float dM[9];
    for (int i3 = 0; i3 < 3; ++i3) for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0; for (int k = 0; k < 3; ++k) acc += (GW[3 * i3 + k] + GW[3 * k + i3]) * M[3 * k + j3]; dM[3 * i3 + j3] = acc; }
    // M = Rq diag(s)
    float G[9];
    for (int i3 = 0; i3 < 3; ++i3) for (int j3 = 0; j3 < 3; ++j3) G[3 * i3 + j3] = dM[3 * i3 + j3] * s[j3];
    for (int j3 = 0; j3 < 3; ++j3) {
      float acc = 0; for (int i3 = 0; i3 < 3; ++i3) acc += dM[3 * i3 + j3] * Rq[3 * i3 + j3];
      os[3 * v + j3] = acc * s[j3]; }
    const float w = qn[0], qx = qn[1], qy = qn[2], qz = qn[3];
    const float dw = 2 * (-qz * G[1] + qy * G[2] + qz * G[3] - qx * G[5] - qy * G[6] + qx * G[7]);
    const float dqx = 2 * (qy * G[1] + qz * G[2] + qy * G[3] - 2 * qx * G[4] - w * G[5] + qz * G[6] + w * G[7] - 2 * qx * G[8]);
    const float dqy = 2 * (-2 * qy * G[0] + qx * G[1] + w * G[2] + qx * G[3] + qz * G[5] - w * G[6] + qz * G[7] - 2 * qy * G[8]);
    const float dqz = 2 * (-2 * qz * G[0] - w * G[1] + qx * G[2] + w * G[3] - 2 * qz * G[4] + qy * G[5] + qx * G[6] + qy * G[7]);
    const float *qu = pq + 4 * i;
    const float n = std::max(std::sqrt(qu[0] * qu[0] + qu[1] * qu[1] + qu[2] * qu[2] + qu[3] * qu[3]), 1e-12f);
    const float dot = w * dw + qx * dqx + qy * dqy + qz * dqz;
    oq[4 * v] = (dw - w * dot) / n; oq[4 * v + 1] = (dqx - qx * dot) / n;
    oq[4 * v + 2] = (dqy - qy * dot) / n; oq[4 * v + 3] = (dqz - qz * dot) / n;
  }
  return {gm, gq, gs};
}

namespace {
inline void sh_basis(int deg, float x, float y, float z, float *B) {
  B[0] = 0.28209479177387814f;
  if (deg < 1) return;
  const float C1 = 0.4886025119029199f;
  B[1] = -C1 * y; B[2] = C1 * z; B[3] = -C1 * x;
  if (deg < 2) return;
  const float xx = x * x, yy = y * y, zz = z * z, xy = x * y, yz = y * z, xz = x * z;
  B[4] = 1.0925484305920792f * xy; B[5] = -1.0925484305920792f * yz; B[6] = 0.31539156525252005f * (2 * zz - xx - yy);
  B[7] = -1.0925484305920792f * xz; B[8] = 0.5462742152960396f * (xx - yy);
  if (deg < 3) return;
  B[9] = -0.5900435899266435f * y * (3 * xx - yy); B[10] = 2.890611442640554f * xy * z;
  B[11] = -0.4570457994644658f * y * (4 * zz - xx - yy); B[12] = 0.3731763325901154f * z * (2 * zz - 3 * xx - 3 * yy);
  B[13] = -0.4570457994644658f * x * (4 * zz - xx - yy); B[14] = 1.445305721320277f * z * (xx - yy);
  B[15] = -0.5900435899266435f * x * (xx - 3 * yy);
}
}  // namespace

// colors (M,3) for rows gidx, from sh (N,K,3). View directions are treated as constants.
torch::Tensor sh_forward(torch::Tensor sh, torch::Tensor means, torch::Tensor campos, torch::Tensor gidx, int64_t deg) {
  const int64_t Mv = gidx.size(0), K = sh.size(1);
  auto out = torch::empty({Mv, 3}, torch::kFloat32);
  const float *ps = sh.data_ptr<float>(), *pm = means.data_ptr<float>();
  const float cpx = campos[0].item<float>(), cpy = campos[1].item<float>(), cpz = campos[2].item<float>();
  const int64_t *gi = gidx.data_ptr<int64_t>();
  float *o = out.data_ptr<float>();
  const int nb = (deg + 1) * (deg + 1);
#pragma omp parallel for schedule(static)
  for (int64_t v = 0; v < Mv; ++v) {
    const int64_t i = gi[v];
    float dx = pm[3 * i] - cpx, dy = pm[3 * i + 1] - cpy, dz = pm[3 * i + 2] - cpz;
    const float n = std::max(std::sqrt(dx * dx + dy * dy + dz * dz), 1e-12f);
    float B[16];
    sh_basis(deg, dx / n, dy / n, dz / n, B);
    const float *s = ps + i * K * 3;
    for (int ch = 0; ch < 3; ++ch) {
      float acc = 0.5f;
      for (int k = 0; k < nb; ++k) acc += B[k] * s[3 * k + ch];
      o[3 * v + ch] = std::max(acc, 0.f);
    }
  }
  return out;
}

// d sh (M,K,3) for rows gidx given d colors (M,3) and the forward colors (for the clamp mask)
torch::Tensor sh_backward(torch::Tensor dcol, torch::Tensor colors, torch::Tensor means, torch::Tensor campos,
                          torch::Tensor gidx, int64_t deg, int64_t K) {
  const int64_t Mv = gidx.size(0);
  auto out = torch::zeros({Mv, K, 3}, torch::kFloat32);
  const float *pd = dcol.data_ptr<float>(), *pc = colors.data_ptr<float>(), *pm = means.data_ptr<float>();
  const float cpx = campos[0].item<float>(), cpy = campos[1].item<float>(), cpz = campos[2].item<float>();
  const int64_t *gi = gidx.data_ptr<int64_t>();
  float *o = out.data_ptr<float>();
  const int nb = (deg + 1) * (deg + 1);
#pragma omp parallel for schedule(static)
  for (int64_t v = 0; v < Mv; ++v) {
    const int64_t i = gi[v];
    float dx = pm[3 * i] - cpx, dy = pm[3 * i + 1] - cpy, dz = pm[3 * i + 2] - cpz;
    const float n = std::max(std::sqrt(dx * dx + dy * dy + dz * dz), 1e-12f);
    float B[16];
    sh_basis(deg, dx / n, dy / n, dz / n, B);
    for (int ch = 0; ch < 3; ++ch) {
      const float g = pc[3 * v + ch] > 0.f ? pd[3 * v + ch] : 0.f;
      for (int k = 0; k < nb; ++k) o[(v * K + k) * 3 + ch] = B[k] * g;
    }
  }
  return out;
}

// Adam on the rows gidx only (the "selective" variant): param/m/v (N,D), grad (M,D)
void adam_rows(torch::Tensor param, torch::Tensor grad, torch::Tensor m, torch::Tensor v, torch::Tensor gidx,
               double lr, double b1, double b2, double eps, double bc1, double bc2) {
  const int64_t Mv = gidx.size(0), D = param.numel() / std::max<int64_t>(param.size(0), 1);
  float *p = param.data_ptr<float>(), *pm = m.data_ptr<float>(), *pv = v.data_ptr<float>();
  const float *g = grad.data_ptr<float>();
  const int64_t *gi = gidx.data_ptr<int64_t>();
  const float fb1 = b1, fb2 = b2, step = lr / bc1, sbc2 = std::sqrt(bc2), feps = eps;
#pragma omp parallel for schedule(static)
  for (int64_t r = 0; r < Mv; ++r) {
    const int64_t i = gi[r];
    for (int64_t d = 0; d < D; ++d) {
      const float gg = g[r * D + d];
      float &mm = pm[i * D + d], &vv = pv[i * D + d];
      mm = fb1 * mm + (1.f - fb1) * gg;
      vv = fb2 * vv + (1.f - fb2) * gg * gg;
      p[i * D + d] -= step * mm / (std::sqrt(vv) / sbc2 + feps);
    }
  }
}


// Adam on rows gidx with a per-column learning rate (for SH: DC vs higher bands)
void adam_rows_cols(torch::Tensor param, torch::Tensor grad, torch::Tensor m, torch::Tensor v, torch::Tensor gidx,
                    torch::Tensor lr_cols, double b1, double b2, double eps, double bc1, double bc2) {
  const int64_t Mv = gidx.size(0), D = param.numel() / std::max<int64_t>(param.size(0), 1);
  float *p = param.data_ptr<float>(), *pm = m.data_ptr<float>(), *pv = v.data_ptr<float>();
  const float *g = grad.data_ptr<float>(), *lr = lr_cols.data_ptr<float>();
  const int64_t *gi = gidx.data_ptr<int64_t>();
  const float fb1 = b1, fb2 = b2, ibc1 = 1.0 / bc1, sbc2 = std::sqrt(bc2), feps = eps;
#pragma omp parallel for schedule(static)
  for (int64_t r = 0; r < Mv; ++r) {
    const int64_t i = gi[r];
    for (int64_t d = 0; d < D; ++d) {
      const float gg = g[r * D + d];
      float &mm = pm[i * D + d], &vv = pv[i * D + d];
      mm = fb1 * mm + (1.f - fb1) * gg;
      vv = fb2 * vv + (1.f - fb2) * gg * gg;
      p[i * D + d] -= lr[d] * ibc1 * mm / (std::sqrt(vv) / sbc2 + feps);
    }
  }
}


// ---------------------------------------------------------------------------------------------
// Loss: (1-lam) * L1 + lam * (1 - SSIM), SSIM with an 11-tap Gaussian (sigma 1.5), zero padding.
namespace {
struct Gauss11 { float w[11]; Gauss11() { float s = 0; for (int i = 0; i < 11; ++i) { const float x = i - 5; w[i] = std::exp(-x * x / (2 * 1.5f * 1.5f)); s += w[i]; } for (int i = 0; i < 11; ++i) w[i] /= s; } };
const Gauss11 GW;
// in/out (H,W,C) interleaved; tmp same size
void blur(const float *in, float *out, float *tmp, int H, int W, int C) {
  // vertical pass (contiguous rows, SIMD over the whole row), then horizontal pass
  const int RW = W * C;
#pragma omp parallel for schedule(static)
  for (int y = 0; y < H; ++y) {
    const int k0 = std::max(0, 5 - y), k1 = std::min(11, H + 5 - y);
    float *o = tmp + (size_t)y * RW;
    {
      const float w = GW.w[k0];
      const float *r = in + (size_t)(y + k0 - 5) * RW;
#pragma omp simd
      for (int i = 0; i < RW; ++i) o[i] = w * r[i];
    }
    for (int k = k0 + 1; k < k1; ++k) {
      const float w = GW.w[k];
      const float *r = in + (size_t)(y + k - 5) * RW;
#pragma omp simd
      for (int i = 0; i < RW; ++i) o[i] += w * r[i];
    }
  }
#pragma omp parallel for schedule(static)
  for (int y = 0; y < H; ++y) {
    const float *r = tmp + (size_t)y * RW;
    float *o = out + (size_t)y * RW;
    for (int x = 0; x < W; ++x) {
      float *oc = o + (size_t)x * C;
      if (x >= 5 && x < W - 5) {
        const float *b = r + (size_t)(x - 5) * C;
#pragma omp simd
        for (int c = 0; c < C; ++c) {
          float a = 0;
          for (int k = 0; k < 11; ++k) a += GW.w[k] * b[k * C + c];
          oc[c] = a;
        }
      } else {
        const int k0 = std::max(0, 5 - x), k1 = std::min(11, W + 5 - x);
        for (int c = 0; c < C; ++c) {
          float a = 0;
          for (int k = k0; k < k1; ++k) a += GW.w[k] * r[(size_t)(x + k - 5) * C + c];
          oc[c] = a;
        }
      }
    }
  }
}
}  // namespace

// returns (loss (1), d_img (H,W,3), ssim (1))
std::vector<torch::Tensor> loss_l1_ssim(torch::Tensor img, torch::Tensor gt, double lam) {
  const int H = img.size(0), W = img.size(1), C = img.size(2);
  const size_t n = (size_t)H * W * C;
  const float *x = img.data_ptr<float>(), *y = gt.data_ptr<float>();
  // 5 stacked maps: x, y, xx, yy, xy -> blurred
  auto tin = torch::empty({(int64_t)n * 5}, torch::kFloat32), tout = torch::empty({(int64_t)n * 5}, torch::kFloat32),
       ttmp = torch::empty({(int64_t)n * 5}, torch::kFloat32);
  float *in_ = tin.data_ptr<float>(), *out_ = tout.data_ptr<float>(), *tmp_ = ttmp.data_ptr<float>();
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < n; ++i) {
    in_[5 * i] = x[i]; in_[5 * i + 1] = y[i]; in_[5 * i + 2] = x[i] * x[i]; in_[5 * i + 3] = y[i] * y[i]; in_[5 * i + 4] = x[i] * y[i];
  }
  blur(in_, out_, tmp_, H, W, C * 5);
  const float *out = out_;
  const float C1 = 0.01f * 0.01f, C2 = 0.03f * 0.03f;
  const float ks = -(float)lam / (float)n;  // d loss / d ssim_map(p)
  double ssum = 0, l1 = 0;
  // gradient maps of the blurred quantities: g_mx, g_exx, g_exy (3 stacked)
  auto tg = torch::empty({(int64_t)n * 3}, torch::kFloat32), tgb = torch::empty({(int64_t)n * 3}, torch::kFloat32),
       tt3 = torch::empty({(int64_t)n * 3}, torch::kFloat32);
  float *g = tg.data_ptr<float>(), *gb = tgb.data_ptr<float>(), *tmp3 = tt3.data_ptr<float>();
#pragma omp parallel for schedule(static) reduction(+ : ssum, l1)
  for (size_t i = 0; i < n; ++i) {
    const float mx = out[5 * i], my = out[5 * i + 1];
    const float sxx = out[5 * i + 2] - mx * mx, syy = out[5 * i + 3] - my * my, sxy = out[5 * i + 4] - mx * my;
    const float A1 = 2 * mx * my + C1, A2 = 2 * sxy + C2, B1 = mx * mx + my * my + C1, B2 = sxx + syy + C2;
    const float s = (A1 * A2) / (B1 * B2);
    ssum += s;
    l1 += std::fabs(x[i] - y[i]);
    const float dA1 = A2 / (B1 * B2), dA2 = A1 / (B1 * B2), dB1 = -s / B1, dB2 = -s / B2;
    g[3 * i] = ks * (dA1 * 2 * my + dA2 * (-2 * my) + dB1 * 2 * mx + dB2 * (-2 * mx));
    g[3 * i + 1] = ks * dB2;
    g[3 * i + 2] = ks * dA2 * 2;
  }
  blur(g, gb, tmp3, H, W, C * 3);
  auto dimg = torch::empty({H, W, C}, torch::kFloat32);
  float *d = dimg.data_ptr<float>();
  const float kl1 = (1.f - (float)lam) / (float)n;
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < n; ++i) {
    const float df = x[i] - y[i];
    d[i] = gb[3 * i] + 2 * x[i] * gb[3 * i + 1] + y[i] * gb[3 * i + 2] + kl1 * (df > 0 ? 1.f : (df < 0 ? -1.f : 0.f));
  }
  const double ss = ssum / n;
  auto loss = torch::full({1}, (float)((1 - lam) * l1 / n + lam * (1 - ss)), torch::kFloat32);
  auto sst = torch::full({1}, (float)ss, torch::kFloat32);
  return {loss, dimg, sst};
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("bin_gaussians", &bin_gaussians);
  m.def("render_forward", &render_forward);
  m.def("render_backward", &render_backward);
  m.def("render_depth", &render_depth);
  m.def("project_forward", &project_forward);
  m.def("project_backward", &project_backward);
  m.def("sh_forward", &sh_forward);
  m.def("sh_backward", &sh_backward);
  m.def("adam_rows", &adam_rows);
  m.def("adam_rows_cols", &adam_rows_cols);
  m.def("loss_l1_ssim", &loss_l1_ssim);
}
