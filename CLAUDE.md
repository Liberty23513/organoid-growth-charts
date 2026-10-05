# CLAUDE.md: context for working in this repo

Read this fully before doing anything. It replaces any need to ask the user what the project is.

## How to work with the user

- The user (Boting, GitHub Liberty23513) is a PhD-level neuroscientist with almost no statistics background. She learned the concepts below yesterday. She is leading this project at a 2.5-day hackathon (Brainhack Montreal, Oct 5 to 7, 2026) with one teammate.
- **Teach step by step.** One step at a time. Before writing code for a step, say in two or three sentences what the step does and why. After running it, say what the output means. Then ask whether to continue. Do not dump a whole pipeline at once.
- Explain in Chinese. Keep code, comments, variable names, file names and all technical terms in English (gene names, PCNtoolkit API names, statistical terms).
- Plain language. Short sentences. No formula derivations. No MCMC internals. When a term comes up for the first time, give a one-line gloss.
- When something fails, show the error, say what you think it means, propose one fix. Do not try three fixes silently.
- Never use the em dash character in any text.
- Time is short: about 3 hours today, 6 tomorrow, 3.5 on the last day. Prefer the simplest thing that runs. Hard-coded parameters are fine. Say so when you cut a corner.

## What the project is

Pediatric growth charts place a child on a percentile curve for their age. We build the same thing for brain organoids: x = days in culture, y = the fraction of one cell type (first: neural progenitors), and a set of centile curves (5th, 25th, 50th, 75th, 95th) with a z-score for every organoid. The method is normative modelling, the family behind brain charts in neuroimaging (Bethlehem et al. 2022). The tool is PCNtoolkit, Bayesian linear regression (BLR). The user went to Johanna Bayer's PCNtoolkit tutorial on Oct 2 and will try to adapt its notebook.

What the user already understands (do not re-teach from scratch, but do refer back to it):
1. Regression gives a distribution of y at each x, not just a line. Centile lines are mu(x) +/- const * sigma(x). z = (y - mu(x)) / sigma(x).
2. "Linear" in BLR means linear in the parameters. A B-spline basis makes the mean curve bend. The mean curve must bend here: progenitors fall from ~65% at day 20 to ~8% at day 100, then plateau.
3. sigma must depend on age (heteroskedastic). In our data sigma is ~0.19 at day 30, ~0.06 at day 100, ~0.08 at day 180.
4. Prior, likelihood, posterior in words. Posterior spread = uncertainty of the curve, wider where there are few points. Predictive distribution = noise + curve uncertainty, and z uses it as denominator.
5. Not yet learned in depth: batch effects / HBR / partial pooling, and evaluation metrics (EV, SMSE, MSLL, calibration). Teach these when they come up.

Full written tutorial: `tutorial/growth_chart_tutorial_zh.md` (Chinese) and `tutorial/growth_chart_tutorial.md` (English). Figures: `tutorial/*.png`.

## The data

`data/hnoca_sample_composition.csv`. 322 rows, one per organoid sample. Derived from the Human Neural Organoid Cell Atlas (HNOCA, He et al. 2024 Nature, CC BY 4.0, 1.77 M cells) by `scripts/build_composition_table.py`: cells grouped by sample, cell-type fractions counted, samples with < 100 cells dropped. A "sample" is one sequencing library; HNOCA does not say whether that is one organoid or several pooled.

Columns:
- `sample`: id. `n_cells`: cells in the sample.
- `age`: days in culture. This is the x-axis. (Not `organoid_age_days`.)
- `protocol`: differentiation protocol as a string with a DOI, e.g. `Velasco, 2019 (doi: 10.1038/s41586-019-1289-x)`. Filter with `df.protocol.str.contains("Velasco")`.
- `publication`: source paper, e.g. `Paulsen, 2022`. This is the batch-effect variable.
- `protocol_type`, `cell_line`.
- `frac_NPC_IP`: progenitor fraction (first y-variable). `frac_neuron`, `frac_glia`, `frac_neuroepithelium_PSC`: other y-variables.
- `l2_*`: 17 individual cell-type fractions.

Subsets:
- Velasco protocol: 131 samples, days 21 to 192, 4 publications (Bhaduri 2020 n=17 days 21-168; Paulsen 2022 n=54 days 28-190; Uzquiano 2022 n=39 days 23-192; Velasco 2019 n=21 days 101-190). **Start here.**
- Lancaster protocol: 81 samples, days 9 to 120, 3 publications. Second.
- The other 25 protocols are too small (22 of them come from a single publication).

Do not confuse the protocol "Velasco" (131 samples) with the publication "Velasco, 2019" (21 samples). One chart per protocol: different protocols follow genuinely different trajectories, like separate growth charts per sex.

`data/split_velasco.csv`: fixed train/test split for the Velasco subset, stratified by age bin, 105 train / 26 test. Always use it. Never refit the split.

## Conventions every model must follow

Each model writes two CSVs to `results/<model_name>/`:
- `centiles.csv`: columns `age, p5, p25, p50, p75, p95`, one row per day from 20 to 192.
- `zscores.csv`: columns `sample, age, publication, split, y, mu, sigma, z` for all 131 samples (train and test), with `split` from `data/split_velasco.csv`.

Model names: `baseline_rolling` (teammate's model-free rolling-window quantiles), `blr_homo`, `blr_hetero`, `blr_hetero_batch`, later `blr_warped`.

Folders: `notebooks/` (one notebook per task, numbered), `src/` (reusable functions), `results/`, `figures/`. The user edits only her own notebooks to avoid git conflicts with the teammate.

Metrics on the test set only: explained variance (EV), SMSE (< 1 beats predicting the mean), MSLL (scores the whole predictive distribution, more negative is better). Calibration: test z-scores should be ~N(0,1) overall, per age bin, per publication.

## Day 1 tasks for the user (B line)

The teammate (A line) does raw plots and the rolling-window baseline; no PCNtoolkit. The user does PCNtoolkit. Full split in `TASKS_day1.md`.

**B1. Minimal BLR (target 60 min).** `notebooks/03_pcntoolkit_blr.ipynb`
1. Check the installed PCNtoolkit: `import pcntoolkit; print(pcntoolkit.__version__)`. The API changed substantially at version 1.0 (2025). Inspect what is actually installed before writing model code; do not assume an API from memory. If the tutorial notebook from Oct 2 is on disk, use its calls as the template and change only: covariates `['age']`, response_vars `['frac_NPC_IP']`, no batch effects yet.
2. Load the CSV, filter Velasco, merge the split, build train and test frames.
3. Fit BLR with a B-spline basis on age, homoskedastic. Predict on the test set and on an age grid 20..192.
4. Write `results/blr_homo/centiles.csv` and `results/blr_homo/zscores.csv` in the formats above (p5 = mu - 1.645 sigma, p25 = mu - 0.674 sigma, etc.).
5. Plot: scatter of all 131 samples, centile lines, test samples marked. Save `figures/blr_homo_velasco.png`.
If stuck for more than 20 minutes on install or API, write down the error in the notebook and fall back to a sklearn version (`SplineTransformer` + `BayesianRidge`, see `scripts/make_teaching_figures.py` for the pattern) so the day still produces a result. Come back to PCNtoolkit after.

**B2. Heteroskedastic and batch effect (60 min).** Same notebook.
6. Second model: turn on heteroskedastic variance. Write to `results/blr_hetero/`.
7. Third model: add `batch_effects=['publication']`. Write to `results/blr_hetero_batch/`. Teach what a batch effect is when you get here (lab offsets inflate sigma if ignored; the known trap is that publication and age are confounded, Velasco 2019 covers only days 101-190).
8. Test-set EV, SMSE, MSLL for the three models in one table: `results/blr_metrics.csv`.

**B3. Calibration (30 min).**
9. For each model: histogram and QQ plot of test z; z mean and sd per age bin; z mean per publication. Save `figures/calibration_<model>.png`.
10. Look at skew. Fractions are bounded at 0, so z may be skewed. If so, tomorrow's first step is warped BLR (`WarpSinArcsinh`) or a logit transform of y.

**End of day.** Overlay `results/baseline_rolling/centiles.csv` (teammate) and the BLR centiles in one figure, `figures/day1_comparison.png`. Add a "Day 1 status" section to README.md: what worked, what is stuck, first thing tomorrow. Commit and push.

## Known pitfalls

- HNOCA's `batch` field is one-to-one with `bio_sample`; never use it as a random effect. Use `publication`.
- Fractions near 0 are skewed; the 5th centile from a Gaussian model can go negative. Expected; fix with warping or logit tomorrow.
- A spline fit to squared residuals for sigma(x) collapsed to zero in a quick test; a quadratic fit to |residual| was stable. PCNtoolkit's own heteroskedastic model is the real solution.
- With small subsets (n = 20) the posterior can be confidently wrong where no data exist. This is the sample-size question, not a bug.
- Stretch goal (not today): refit on stratified subsets of 20/40/80/131 Velasco train samples, 10 draws each, and measure how far the centiles move.

## Git

Working clone: `~/Documents/Claude/Projects/organoid-growth-charts-repo/`. Remote: https://github.com/Liberty23513/organoid-growth-charts. Commit small and often: `git add . && git commit -m "..." && git push`. Pull before starting (`git pull`) because the teammate pushes too.
