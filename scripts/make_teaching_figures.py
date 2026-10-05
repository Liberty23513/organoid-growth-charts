"""
Reproduce the two teaching figures and the pitch figure from data/hnoca_sample_composition.csv.

    python scripts/make_teaching_figures.py

Needs numpy, pandas, scipy, matplotlib, scikit-learn.
Writes tutorial/block1_regression_to_centiles.png, tutorial/block2_bayesian_regression.png,
tutorial/pitch_slide_centile_chart.png.

This is a hand-built illustration of the ideas (spline mean, age-dependent sigma, Bayesian
posterior). It is NOT the analysis pipeline. The real fits use PCNtoolkit.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import make_lsq_spline, BSpline
from sklearn.linear_model import BayesianRidge

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "tutorial")
os.makedirs(OUT, exist_ok=True)

C_PTS, C_MU, C_FOCAL = "#7a7a7a", "#1f5fa8", "#d1495b"
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.spines.top": False,
                     "axes.spines.right": False})

# ---------------------------------------------------------------- data
df = pd.read_csv(os.path.join(ROOT, "data", "hnoca_sample_composition.csv"))
v = df[df.protocol.str.contains("Velasco", case=False, na=False)].sort_values("age")
x = v.age.values.astype(float)
y = v.frac_NPC_IP.values
xg = np.linspace(x.min(), x.max(), 300)

# ---------------------------------------------------------------- block 1 pieces
b1, b0 = np.polyfit(x, y, 1)
lin = lambda t: b0 + b1 * t

k = 3
knots = np.r_[[x.min()] * (k + 1), [60, 100, 140], [x.max()] * (k + 1)]   # cubic B-spline, 3 interior knots
spl = make_lsq_spline(x, y, knots, k=k)
mu = lambda t: np.clip(spl(t), 0, 1)
res = y - mu(x)
sig_const = res.std()

# age-dependent sigma: quadratic fit to |residual|; E|r| = sigma*sqrt(2/pi) for Gaussian noise; floor 0.03
pa = np.polyfit(x, np.abs(res), 2)
sig = lambda t: np.clip(np.polyval(pa, t) / np.sqrt(2 / np.pi), 0.03, None)
z = res / sig(x)
lo, hi = mu(xg) - 1.64 * sig(xg), mu(xg) + 1.64 * sig(xg)

cand = np.where((x > 25) & (x < 80))[0]
i_hi = cand[np.argmin(z[cand])]           # one clearly low organoid to highlight


def panel_letter(ax, L):
    ax.text(-0.12, 1.08, L, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top")


def scatter(ax, xx=x, yy=y):
    ax.scatter(xx, yy, s=12, color=C_PTS, alpha=0.6, lw=0, zorder=2)


# ---------------------------------------------------------------- figure 1
fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.6), sharex=True, sharey=True)
a, b, c, d = axs.ravel()
for ax in axs.ravel():
    scatter(ax); ax.set_ylim(-0.08, 1.0)
a.plot(xg, lin(xg), color=C_MU, lw=1.6, zorder=3)
for xi, yi in zip(x[::6], y[::6]):
    a.plot([xi, xi], [lin(xi), yi], color=C_FOCAL, lw=0.8, alpha=0.8, zorder=1)
a.set_title("Straight line misses the curve (red = residuals)", loc="left")
b.plot(xg, mu(xg), color=C_MU, lw=1.6, zorder=3)
b.set_title("B-spline bends the mean, but it is only a mean", loc="left")
c.plot(xg, mu(xg), color=C_MU, lw=1.6, zorder=3)
c.fill_between(xg, mu(xg) - 1.64 * sig_const, mu(xg) + 1.64 * sig_const, color=C_MU, alpha=0.15, lw=0)
c.set_title(f"Constant σ = {sig_const:.2f}: same width at every age", loc="left")
d.plot(xg, mu(xg), color=C_MU, lw=1.6, zorder=3)
d.fill_between(xg, lo, hi, color=C_MU, alpha=0.15, lw=0)
d.plot(xg, hi, color=C_MU, lw=0.8, ls="--"); d.plot(xg, lo, color=C_MU, lw=0.8, ls="--")
d.scatter([x[i_hi]], [y[i_hi]], s=40, color=C_FOCAL, zorder=5)
d.annotate(f"z = {z[i_hi]:.1f}  (below 1st centile)", (x[i_hi], y[i_hi]), xytext=(78, 0.52),
           fontsize=7, color=C_FOCAL, arrowprops=dict(arrowstyle="-", color=C_FOCAL, lw=0.7))
for lab, yy in [("95th", hi[-1]), ("50th", mu(xg[-1])), ("5th", lo[-1] + 0.02)]:
    d.text(xg[-1] + 3, yy, lab, fontsize=6, color=C_MU, ha="left", va="center")
d.set_title("σ(x) changes with age: 5th / 50th / 95th centiles", loc="left")
d.set_xlim(x.min() - 8, x.max() + 22)
for ax, L in zip(axs.ravel(), "abcd"):
    panel_letter(ax, L)
for ax in axs[1]:
    ax.set_xlabel("Organoid age (days in culture)")
for ax in axs[:, 0]:
    ax.set_ylabel("Progenitor fraction (NPC + IP)")
fig.suptitle(f"Velasco protocol, n = {len(x)} samples, 4 publications", x=0.01, ha="left", fontsize=8, color="#666666")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "block1_regression_to_centiles.png"), dpi=200)

# ---------------------------------------------------------------- pitch figure (panel d alone)
fig2, ax = plt.subplots(figsize=(6.0, 3.8))
ax.scatter(x, y, s=16, color=C_PTS, alpha=0.6, lw=0, zorder=2)
ax.plot(xg, mu(xg), color=C_MU, lw=2, zorder=3)
ax.fill_between(xg, lo, hi, color=C_MU, alpha=0.15, lw=0)
ax.plot(xg, hi, color=C_MU, lw=0.9, ls="--"); ax.plot(xg, lo, color=C_MU, lw=0.9, ls="--")
ax.scatter([x[i_hi]], [y[i_hi]], s=50, color=C_FOCAL, zorder=5)
ax.annotate(f"one organoid: z = {z[i_hi]:.1f}\n(below 1st centile)", (x[i_hi], y[i_hi]), xytext=(80, 0.55),
            fontsize=8, color=C_FOCAL, arrowprops=dict(arrowstyle="-", color=C_FOCAL, lw=0.8))
for lab, yy in [("95th", hi[-1]), ("50th", mu(xg[-1])), ("5th", lo[-1] + 0.02)]:
    ax.text(xg[-1] + 3, yy, lab, fontsize=7, color=C_MU, ha="left", va="center")
ax.set_xlim(x.min() - 8, x.max() + 25); ax.set_ylim(-0.08, 1.0)
ax.set_xlabel("Organoid age (days in culture)"); ax.set_ylabel("Progenitor fraction (NPC + IP)")
ax.set_title(f"A growth chart for brain organoids (first draft, HNOCA, Velasco protocol, n = {len(x)})", loc="left")
fig2.tight_layout()
fig2.savefig(os.path.join(OUT, "pitch_slide_centile_chart.png"), dpi=200)

# ---------------------------------------------------------------- figure 2: Bayesian linear regression
rng = np.random.default_rng(0)
design = lambda t: BSpline.design_matrix(np.clip(t, x.min(), x.max()), knots, k).toarray()
X, Xg = design(x), design(xg)
fit_blr = lambda Xa, ya: BayesianRidge(fit_intercept=False).fit(Xa, ya)
m_all = fit_blr(X, y)
idx20 = np.sort(rng.choice(len(x), 20, replace=False))
m_20 = fit_blr(X[idx20], y[idx20])
post_curves = lambda m, n=30: Xg @ rng.multivariate_normal(m.coef_, m.sigma_, size=n).T
prior = Xg @ rng.normal(0.35, 0.4, size=(X.shape[1], 30))

fig3, axs = plt.subplots(2, 2, figsize=(7.2, 5.6), sharex=True, sharey=True)
a, b, c, d = axs.ravel()
a.plot(xg, prior, color=C_MU, lw=0.8, alpha=0.35); a.set_ylim(-0.1, 1.05)
a.set_title("Prior: 30 curves plausible before seeing data", loc="left")
for ax, m, ii, lab in [(b, m_all, np.arange(len(x)), f"Posterior with all n = {len(x)}"),
                       (c, m_20, idx20, "Posterior with n = 20 subsample")]:
    scatter(ax, x[ii], y[ii])
    ax.plot(xg, post_curves(m), color=C_MU, lw=0.8, alpha=0.35, zorder=3)
    ax.plot(xg, Xg @ m.coef_, color=C_MU, lw=1.8, zorder=4)
    ax.set_title(f"{lab}: 30 plausible curves", loc="left")
mu_g, std_g = m_all.predict(Xg, return_std=True)
noise_sd = np.sqrt(1 / m_all.alpha_)
par_sd = np.sqrt(np.clip(std_g ** 2 - noise_sd ** 2, 0, None))
scatter(d)
d.fill_between(xg, mu_g - 1.64 * std_g, mu_g + 1.64 * std_g, color=C_MU, alpha=0.12, lw=0,
               label="predictive: noise + curve uncertainty")
d.fill_between(xg, mu_g - 1.64 * par_sd, mu_g + 1.64 * par_sd, color=C_FOCAL, alpha=0.35, lw=0,
               label="curve uncertainty only")
d.plot(xg, mu_g, color=C_MU, lw=1.8)
d.legend(loc="upper right", fontsize=6, frameon=False)
d.set_title("Predictive band = noise + curve uncertainty", loc="left")
for ax, L in zip(axs.ravel(), "abcd"):
    panel_letter(ax, L)
for ax in axs[1]:
    ax.set_xlabel("Organoid age (days in culture)")
for ax in axs[:, 0]:
    ax.set_ylabel("Progenitor fraction (NPC + IP)")
fig3.suptitle("Bayesian linear regression, cubic B-spline basis, constant σ, Velasco protocol",
              x=0.01, ha="left", fontsize=8, color="#666666")
fig3.tight_layout()
fig3.savefig(os.path.join(OUT, "block2_bayesian_regression.png"), dpi=200)

print(f"n = {len(x)} | noise sd = {noise_sd:.3f} | sigma(x) at day 30/100/180 = "
      f"{sig(30):.3f}/{sig(100):.3f}/{sig(180):.3f} | highlighted z = {z[i_hi]:.2f}")
