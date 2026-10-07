# Organoid growth charts: starter package

Brainhack Montreal Fall 2026. Project: normative modelling of brain-organoid cell-type composition.
GitHub issue: https://github.com/BrainhackMTL/fall2026/issues/3

## Start here (five minutes)

```python
import pandas as pd
df = pd.read_csv("data/hnoca_sample_composition.csv")          # 322 samples x 28 columns
v = df[df.protocol.str.contains("Velasco")]                     # 131 samples, 4 publications
v.plot.scatter("age", "frac_NPC_IP")                            # already looks like a growth chart
```

Then read `tutorial/growth_chart_tutorial.md` (40 minutes, no statistics background assumed).

## Contents

| Path | What it is |
|---|---|
| `data/hnoca_sample_composition.csv` | The working dataset. One row per organoid sample. Every task starts here. |
| `scripts/build_composition_table.py` | Rebuilds the CSV from the public HNOCA atlas on CELLxGENE. Reads only cell metadata over HTTP, no 19 GB download, about 3 minutes. |
| `scripts/make_teaching_figures.py` | Regenerates the three figures in `tutorial/` from the CSV. Illustration only, not the analysis pipeline. |
| `tutorial/growth_chart_tutorial_zh.md` | 中文教程（内容同英文版） |
| `tutorial/growth_chart_tutorial.md` | Concepts: regression to centiles, Bayesian regression, batch effects, evaluation. Sections 1 and 2 complete, 3 and 4 outlined. |
| `tutorial/*.png` | The three figures the tutorial refers to. |
| `pitch/organoid_growth_charts_pitch.pptx` | The 6-slide pitch deck. |
| `pitch/pitch_slide_text.md` | Slide text in plain form. |

## The dataset

Source: Human Neural Organoid Cell Atlas (HNOCA), He, Dony, Fleck et al. 2024, Nature,
doi 10.1038/s41586-024-08172-8. Public on CELLxGENE Discover under CC BY 4.0. 1,767,346 cells.

How the CSV was made: group cells by sample (dataset id + bio_sample, because bio_sample names repeat
across datasets), check that each sample has one age and one cell line, count the fraction of each of the
17 `annot_level_2` cell types, sum them into four groups, drop samples with fewer than 100 cells. 327
samples become 322.

Columns:

| Column | Meaning |
|---|---|
| `sample` | dataset id + "\|" + bio_sample |
| `n_cells` | cells in the sample |
| `age` | days in culture (x-axis) |
| `publication` | source paper (batch effect) |
| `protocol` | differentiation protocol, string with DOI; filter with `str.contains("Velasco")` |
| `protocol_type` | guided / unguided |
| `cell_line` | stem-cell line |
| `frac_NPC_IP` | progenitors: dorsal + ventral + non-telencephalic NPC + dorsal IP (first y-variable) |
| `frac_neuron` | dorsal + ventral + non-telencephalic neurons |
| `frac_glia` | glioblast + astrocyte + OPC |
| `frac_neuroepithelium_PSC` | neuroepithelium + pluripotent stem cells |
| `l2_*` | the 17 individual cell-type fractions |

Usable subsets: Velasco 2019 protocol (131 samples, 4 publications, days 21 to 192) and Lancaster 2014
(81 samples, 3 publications, days 9 to 120). 22 of the 27 protocols come from a single publication with
single-digit sample counts.

Caveat: a "sample" is one sequencing library. HNOCA metadata do not say whether that is one organoid or
several pooled.

## Plan

- Day 1: raw plots per protocol and publication; PCNtoolkit BLR on Velasco `frac_NPC_IP ~ age`,
  heteroskedastic, `batch_effects=['publication']`; train/test split; z-score calibration by age bin.
- Day 2: warped BLR vs logit transform; Lancaster protocol; neuron and glia fractions; final centile figure.
- Guaranteed deliverable: centile chart per protocol with a z-score for every organoid.
- Stretch: refit on random age-stratified subsets of 20, 40, 80, 131 Velasco samples and measure how much
  the centiles move. Stratify by age bin (counts per bin 0-30/30-60/60-90/90-120/120-200 days are
  11/41/16/34/29), otherwise small subsets miss whole age ranges.

## Final model (decided Day 2, Oct 6)

PCNtoolkit BLR on logit(y), cubic B-spline on age, heteroskedastic, `publication` batch effect (mean offset and per-publication noise). Velasco test set: MSLL -1.40, z skewness 0.78, no negative centiles; best of six models including the model-free baseline (`results/blr_metrics.csv`, `notebooks/03_pcntoolkit_blr.ipynb` step 9). Code: `src/growth_chart.py`, `fit_growth_chart()`.

## Environment

```
pip install pandas numpy scipy matplotlib scikit-learn pcntoolkit
```
`remfile h5py` only if you want to rebuild the CSV.
