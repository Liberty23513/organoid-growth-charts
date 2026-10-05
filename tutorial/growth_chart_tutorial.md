# Organoid growth charts: a short tutorial for the team

This is the conceptual background for the project, written for someone with little or no statistics
background. It uses our own data throughout. Reading time about 40 minutes. The figures are in this
folder and can be regenerated with `python scripts/make_teaching_figures.py`.

Sections 1 and 2 are complete. Sections 3 and 4 are outlines we will fill in during the hackathon.

## 0. What we are building, in one paragraph

Pediatric growth charts place one child on a percentile curve for their age. We want the same thing for
brain organoids: given an organoid's age in culture and one measurement (to start, the fraction of
progenitor cells), tell me which percentile it falls in compared with other organoids of the same age
grown with the same protocol. The method is normative modelling, the family of methods behind brain
charts in neuroimaging (Bethlehem et al. 2022, Nature). The tool is PCNtoolkit.

## 1. From a regression line to centile curves

Data: `data/hnoca_sample_composition.csv`, Velasco 2019 protocol subset, 131 samples from 4 publications.
x = `age` (days in culture), y = `frac_NPC_IP` (fraction of neural progenitor cells and intermediate progenitors).

![block 1](block1_regression_to_centiles.png)

**Panel a. A straight line and its residuals.** The simplest model is y = a + b·x + noise. Fitting means
choosing a and b so the vertical distances from the points to the line (the residuals, red stems) are as
small as possible overall. Two problems are visible. The residuals are patterned: early points sit above the
line, points near day 100 sit below. Good residuals look random. And the line predicts a negative fraction
after day 190. The straight line is the wrong shape.

**Panel b. A B-spline mean.** Replace x with a set of basis functions: fixed, smooth, bump-shaped
functions of x (here a cubic B-spline with interior knots at days 60, 100 and 140). The model becomes
y = c₁·B₁(x) + c₂·B₂(x) + ... + noise. It is still a *linear* model because y is linear in the
coefficients c, which are the things we estimate. The curvature comes from the basis, not from the
regression. This is why "Bayesian linear regression" can fit a non-linear trajectory.

The mean now follows the data: progenitors fall from about 65% at day 20 to about 8% at day 100, then
plateau. But a mean alone cannot answer "is this organoid normal?" For that we need the spread at each age.

**Panel c. Constant σ.** If the noise is Gaussian, then at any age x the distribution of y is
Normal(μ(x), σ). Centile lines follow directly:

- 50th centile = μ(x)
- 95th centile = μ(x) + 1.64·σ
- 5th centile = μ(x) − 1.64·σ

With a single σ = 0.15 the band is equally wide at every age. That is clearly wrong here. Early samples
scatter widely; samples after day 100 are tight. A constant band is far too wide late, so a day-150
organoid with 30% progenitors (plainly abnormal) would still fall inside it.

**Panel d. Age-dependent σ(x).** Let the spread change with age (heteroskedastic noise). From the
residuals we estimate σ ≈ 0.19 at day 30, 0.06 at day 100, 0.08 at day 180. The band is now wide early and
narrow late. This is what a growth chart looks like.

**The z-score.** For any organoid, z = (y − μ(x)) / σ(x): how many standard deviations it sits from the
reference for its age. The red point is a day-32 sample with 1.5% progenitors; the reference is 60% ± 0.19,
so z = −3.2, below the 1st centile. Our final deliverable is a z like this for every organoid in HNOCA.

Two caveats that the next sections address: this σ(x) is a point estimate with no uncertainty attached,
and the Gaussian assumption fails near 0 (the 5th centile line dips below zero after day 180, which a
fraction cannot do).

### Section 1 takeaways

1. A regression gives a distribution of y at each x, not just a line. The line is the center of it.
2. Centile lines are μ(x) ± constant × σ(x). Both μ and σ have to be estimated as functions of age.
3. In our data early-stage σ is three times late-stage σ. Age-dependent variance is essential, not a refinement.
4. The z-score turns "is this organoid normal?" into one number.

## 2. What Bayesian regression adds

The section-1 model gives one curve. Fit it to a different 131 organoids and you would get a different
curve, but the model has no idea how different. Bayesian regression quantifies that.

![block 2](block2_bayesian_regression.png)

**Prior (panel a).** Before seeing data, the model holds a distribution over the spline coefficients
c₁…c₇, for instance "each coefficient is near 0.35, give or take 0.4". Drawing 30 coefficient sets from
that distribution gives 30 curves. They are all "possible" and look like nothing in particular.

**Likelihood (not drawn).** A scoring function: given one coefficient set, how probable are the 131
observed points? Curves close to the data score high.

**Posterior (panel b).** Reweight the prior curves by their likelihood. Curves far from the data get
weight near zero. Draw 30 curves from the reweighted distribution and they all hug the data. Posterior =
prior × likelihood is exactly this filter-and-reweight step.

The thick line is the posterior mean, the same curve as section 1. The thin lines are posterior samples;
their spread is the **uncertainty of the curve itself**. With n = 131 the curve's standard deviation is
about 0.03 at day 30 and 0.04 at day 180. The spread depends on how many points constrain the curve
locally, not on how scattered those points are (scatter goes into σ, the noise term).

**Panel c: 20 samples.** Same model, 20 random samples. The curve peaks at 0.9 near day 55 and bumps
again near day 140. Neither feature exists in the full data. No samples were drawn between days 70 and 90,
and the curve wanders there. This panel is the motivation for our stretch goal: how many organoids are
needed before the curve stops moving is a measurable question. Refit on 20, 40, 80 and all 131 and watch.

One honest note. The 20-sample posterior still looks confident (thin lines close together). The prior
strength in this implementation (scikit-learn BayesianRidge) is learned from the data, and with 20 points
it learns a weak prior, which barely constrains the curve. That is what a prior is for: with little data it
should hold the curve in place. PCNtoolkit also learns prior strength from data, so expect the same
behavior in small-sample experiments.

**Panel d: the predictive distribution.** What should the denominator of the z-score be? Two parts:

- Noise: the genuine spread between organoids of the same age, σ (constant here; the section-1 σ(x) is the
  heteroskedastic version).
- Curve uncertainty: how imprecisely we know μ(x) itself (red band).

The predictive distribution combines them: variance = σ² + curve variance. The blue band is its 5th to 95th
centile. A Bayesian normative model computes z from this, not from σ alone. With 131 samples the red band
is narrow (0.03 against 0.15), so the blue band is almost the noise band. At day 180, or with 20 samples,
the red band widens and the blue band follows. In effect, where data are scarce the model automatically
loosens its definition of "abnormal". This is what "centile lines carry their own uncertainty" means in the
pitch.

### Section 2 takeaways

1. The prior is the set of curves the model considers possible before data. The posterior is that set after
   filtering and reweighting by the data.
2. The spread of the posterior is the curve's uncertainty. It is wider where there are fewer points.
3. Predictive distribution = noise + curve uncertainty. z-scores use it as the denominator.
4. BLR (Bayesian linear regression) has a closed-form posterior: seconds to fit, no sampling. HBR
   (hierarchical Bayesian regression, section 3) needs MCMC: minutes.

### Self-check

1. Two organoids both have z = 2.0, one at day 40 and one at day 190. Which "abnormal" call is more
   trustworthy? (Hint: panel d. Where is the curve itself less certain, and what does that do to the
   predictive σ and therefore to the true z?)

## 3. Batch effects and hierarchical models (outline, to fill in)

- The 131 Velasco samples come from 4 publications (Bhaduri 2020 n=17, Paulsen 2022 n=54, Uzquiano 2022
  n=39, Velasco 2019 n=21). Each lab may sit systematically above or below the others. Left unmodelled, those
  offsets inflate σ and widen the centiles.
- Option 1, fixed effects: one intercept per publication. Simple; poor for labs with few samples.
- Option 2, HBR: each publication's offset is drawn from a shared distribution, so small labs are pulled
  toward the group mean (partial pooling). In PCNtoolkit this is `batch_effects=['publication']`.
- Known trap: publication and age are confounded. Velasco 2019 covers only days 101 to 190. Any model has
  to separate "this lab is lower" from "this lab only measured late".
- Do not use HNOCA's `batch` field as a random effect: it is one-to-one with `bio_sample`, so every group has
  one member.
- Protocols are not batches. Velasco and Lancaster organoids follow genuinely different trajectories. One
  chart per protocol, like one chart per sex in pediatrics.

## 4. Evaluating the model (outline, to fill in)

- Train/test split first. All metrics on the test set.
- PCNtoolkit outputs: explained variance (EV), SMSE (standardized mean squared error, < 1 beats "predict the
  mean"), MSLL (mean standardized log loss, scores the whole predictive distribution, more negative is better).
- Calibration: test-set z-scores should be approximately N(0,1) overall, within each age bin, and within each
  publication. A publication whose z-scores are all negative means the batch effect was not handled.
- Skew: fractions near 0 are not Gaussian. If z-scores are skewed, try warped BLR (`warp='WarpSinArcsinh'`)
  or a logit transform of y.

## Glossary

- **Normative modelling**: fit the distribution of a measure as a function of covariates in a reference
  population, then express each new individual as a deviation (z) from it.
- **Centile**: percentile. The 50th centile is the median curve.
- **Heteroskedastic**: noise variance changes with x.
- **Basis function / B-spline**: a fixed transformation of x that lets a linear model fit a curve.
- **Prior / likelihood / posterior**: belief before data / how well parameters explain the data / belief after data.
- **Predictive distribution**: the distribution of a new y at a given x, including parameter uncertainty.
- **Batch effect / site effect**: systematic offset between labs or datasets.
- **Partial pooling**: in a hierarchical model, group estimates are shrunk toward the overall mean.
- **BLR / HBR**: Bayesian linear regression / hierarchical Bayesian regression, the two main PCNtoolkit models.
- **Warping**: a learned non-linear transform of y that makes skewed data closer to Gaussian.
- **MSLL / SMSE / EV**: distributional, mean-squared and variance-explained fit metrics.

## References

1. Rutherford et al. 2022, Nature Protocols, "The normative modeling framework for computational psychiatry". The most readable entry point.
2. PCNtoolkit documentation: pcntoolkit.readthedocs.io.
3. Bethlehem et al. 2022, Nature, "Brain charts for the human lifespan".
4. Marquand et al. 2016, Biological Psychiatry. The original normative modelling paper.
5. Fraza et al. 2021, NeuroImage. Warped BLR.
6. Bayer et al. 2022, NeuroImage. HBR for site effects.
7. He, Dony, Fleck et al. 2024, Nature, "An integrated transcriptomic cell atlas of human neural organoids" (HNOCA, the data source).
