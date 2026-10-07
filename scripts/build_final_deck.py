"""Build the Day-3 wrap-up deck (7 slides, 16:9) from figures/ and results/.

    python scripts/build_final_deck.py        # writes pitch/organoid_growth_charts_final.pptx
"""
from pathlib import Path
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIG, RES, OUT = ROOT / "figures", ROOT / "results", ROOT / "pitch" / "organoid_growth_charts_final.pptx"

NAVY, GREY, BLACK, RED = RGBColor(0x1F, 0x5F, 0xA8), RGBColor(0x55, 0x55, 0x55), RGBColor(0x20, 0x20, 0x20), RGBColor(0xB0, 0x30, 0x30)
prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def title(s, text, sub=None):
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(12.3), Inches(1.0)); tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = NAVY
    if sub:
        p2 = tf.add_paragraph(); p2.text = sub; p2.font.size = Pt(15); p2.font.color.rgb = GREY


def bullets(s, items, left, top, width, height, size=17):
    tb = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height)); tf = tb.text_frame; tf.word_wrap = True
    first = True
    for it in items:
        lvl = 0
        if isinstance(it, tuple): it, lvl = it
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.text = ("• " if lvl == 0 else "– ") + it; p.level = lvl
        p.font.size = Pt(size - 3 * lvl); p.font.color.rgb = BLACK; p.space_after = Pt(7)


def footer(s, text):
    tb = s.shapes.add_textbox(Inches(0.5), Inches(6.95), Inches(12.3), Inches(0.4))
    p = tb.text_frame.paragraphs[0]; p.text = text; p.font.size = Pt(11); p.font.color.rgb = GREY


def table(s, rows, left, top, width, col_w=None, size=12, bold_last=False):
    nr, nc = len(rows), len(rows[0])
    t = s.shapes.add_table(nr, nc, Inches(left), Inches(top), Inches(width), Inches(0.33 * nr)).table
    if col_w:
        for j, w in enumerate(col_w): t.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j); cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(size); p.font.bold = (i == 0) or (bold_last and i == nr - 1)
                p.font.color.rgb = BLACK if i else RGBColor(0xFF, 0xFF, 0xFF)
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY if i == 0 else (RGBColor(0xE8, 0xF0, 0xFA) if (bold_last and i == nr - 1) else RGBColor(0xFF, 0xFF, 0xFF))


# ---- numbers from results/
m = pd.read_csv(RES / "blr_metrics.csv").set_index("model")
neg = {}
for name in m.index:
    c = pd.read_csv(RES / name / "centiles.csv"); neg[name] = int((c.p5 < 0).sum())
runs = pd.read_csv(RES / "subsampling" / "runs.csv")
fin = runs[runs.model == "final"].groupby("n")[["p50_dev_pp", "MSLL", "z_sd"]].mean().round(2)
zf = pd.read_csv(RES / "final_velasco_npc" / "zscores.csv"); n_flag = int((zf.z.abs() > 1.96).sum())
ext = pd.read_csv(RES / "final_extensions_metrics.csv").set_index("chart")

# ---- 1 title
s = prs.slides.add_slide(BLANK)
tb = s.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(3.5)); tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = "Organoid growth charts"; p.font.size = Pt(46); p.font.bold = True; p.font.color.rgb = NAVY
p = tf.add_paragraph(); p.text = "Centile curves and z-scores for brain-organoid cell-type composition"; p.font.size = Pt(24); p.font.color.rgb = BLACK
p = tf.add_paragraph(); p.text = " "
p = tf.add_paragraph(); p.text = "Pediatric growth charts place one child on a percentile curve. We built the same for brain organoids from 322 public samples, and measured how many organoids a lab needs to draw one."; p.font.size = Pt(17); p.font.color.rgb = GREY
s.shapes.add_picture(str(FIG / "final_velasco_npc.png"), Inches(7.6), Inches(4.3), width=Inches(5.3))
footer(s, "Brainhack Montreal, Oct 5 to 7, 2026  |  Boting Li, Selene Zhang  |  github.com/Liberty23513/organoid-growth-charts")

# ---- 2 problem
s = prs.slides.add_slide(BLANK); title(s, "Problem: labs make thousands of brain organoids and judge \"normal\" by eye")
bullets(s, [
    "A brain organoid is a 1 to 3 mm ball of human brain tissue grown from stem cells over weeks to months.",
    "Batch-to-batch and lab-to-lab variability is the field's known weakness. The question every lab asks is \"is this batch normal for its age?\"",
    "Pediatrics answers that question with growth charts. Neuroimaging answered it with brain charts (Bethlehem et al. 2022): a reference distribution over age, and a z-score per person.",
    "Organoids had neither. Closest work, Faravelli et al. 2026, predicts an organoid's age from its transcriptome. We ask the reverse: age is known, is the composition typical?",
    "Deliverable we promised on Monday: a centile chart per protocol with a z-score for every organoid. Stretch: how many organoids are needed to draw one.",
], 0.6, 1.4, 12.1, 5.3, size=19)
footer(s, "Normative modelling: learn the distribution of a measure as a function of covariates, then express each individual as a deviation (z) from it.")

# ---- 3 data
s = prs.slides.add_slide(BLANK); title(s, "Data: HNOCA, 1.77 M cells, summarized to 322 organoid samples")
bullets(s, [
    "Human Neural Organoid Cell Atlas (He et al. 2024, Nature). Public on CELLxGENE, CC BY 4.0.",
    "Script reads only the per-cell metadata over HTTP (3 minutes, no 19 GB download), groups cells by sample, counts cell-type fractions.",
    "One row per sample: days in culture, protocol, publication, fraction of progenitors (NPC + IP), neurons, glia, and 17 finer types.",
    "Usable protocols: Velasco 2019 (131 samples, 4 publications, days 21 to 192) and Lancaster 2014 (81 samples, 3 publications, days 9 to 120). 22 of 27 protocols come from a single paper.",
    "One chart per protocol: different protocols follow different trajectories, like separate charts per sex.",
    "Fixed train/test split, stratified by age bin: 105 train, 26 test. Every number on the next slides is on the 26 held-out organoids.",
], 0.6, 1.4, 6.6, 5.3, size=16)
s.shapes.add_picture(str(FIG / "blr_homo_velasco.png"), Inches(7.3), Inches(1.6), width=Inches(5.8))
footer(s, "Right: Velasco protocol, progenitor fraction vs age, coloured by publication. Rings = held-out test samples. Curves shown are the first (naive) model.")

# ---- 4 method + comparison
s = prs.slides.add_slide(BLANK); title(s, "Method: six models, one test set, pick the one whose z-scores behave")
bullets(s, [
    "PCNtoolkit Bayesian linear regression (BLR). Mean = cubic B-spline on age (the curve bends). Centiles = mu(age) +/- k * sigma(age). z = (y - mu) / sigma.",
    "Added one ingredient at a time, each fixing one visible failure:",
    ("Heteroskedastic sigma(age): spread is 3x larger at day 30 than at day 100.", 1),
    ("Publication as batch effect: lab offset in mean and in noise level.", 1),
    ("Logit transform of y: fractions are bounded at 0, Gaussian centiles went negative.", 1),
    "Selection rule, in order: test MSLL (scores the whole predictive distribution), z skewness near 0, per-age-bin z sd near 1, no negative 5th centile.",
], 0.6, 1.3, 6.4, 3.6, size=15)
rows = [["model", "MSLL", "z skew", "p5 < 0 (days)"]]
labels = {"baseline_rolling": "rolling-window quantiles (no model)", "blr_homo": "BLR, constant sigma", "blr_hetero": "+ sigma(age)",
          "blr_hetero_batch": "+ publication batch effect", "blr_warped": "BLR + SinArcsinh warp", "blr_hetero_batch_logit": "+ logit(y)   [final]"}
for name in ["baseline_rolling", "blr_homo", "blr_hetero", "blr_hetero_batch", "blr_warped", "blr_hetero_batch_logit"]:
    rows.append([labels[name], f"{m.loc[name,'MSLL']:.2f}", f"{m.loc[name,'z_skew']:.2f}", neg[name]])
table(s, rows, 0.6, 4.95, 6.4, col_w=[3.1, 1.0, 1.0, 1.3], size=11, bold_last=True)
s.shapes.add_picture(str(FIG / "calibration_blr_hetero_batch_logit.png"), Inches(7.1), Inches(1.5), width=Inches(6.1))
bullets(s, ["Final model calibration on the 26 test organoids: z roughly N(0,1) overall, in every age bin, in every publication. Remaining skew 0.78 is driven by one test organoid at day 70 with 84% progenitors (z = +2.7)."], 7.1, 3.3, 6.1, 1.5, size=13)
footer(s, "MSLL: mean standardized log loss, more negative is better. Baseline is the teammate's model-free rolling-window quantiles (+/- 15 days).")

# ---- 5 result
s = prs.slides.add_slide(BLANK); title(s, f"Result: a growth chart for Velasco-protocol organoids, {n_flag} of 131 flagged as atypical")
s.shapes.add_picture(str(FIG / "final_velasco_npc.png"), Inches(0.4), Inches(1.3), width=Inches(9.0))
bullets(s, [
    "Progenitors: ~60% at day 20, ~8% at day 100, flat after.",
    "Band is wide early (p5 to p95: 14% to 94% at day 30), narrow late (4% to 10% at day 180). A constant-sigma model cannot do this.",
    f"{n_flag} organoids outside |z| > 1.96 (5% expected: 6.5). Three day-32 samples from one paper with almost no progenitors; one day-70 and one day-166 sample with far too many.",
    "Every organoid in HNOCA now has a z-score in results/final_velasco_npc/zscores.csv.",
    "Curves are drawn for Paulsen 2022, the largest publication; other labs have their own offset.",
], 9.5, 1.4, 3.6, 5.4, size=13)
footer(s, "Test EV 0.77, SMSE 0.27, MSLL -1.40. Rings = held-out test samples. Red rings = |z| > 1.96.")

# ---- 6 extensions
s = prs.slides.add_slide(BLANK); title(s, "Same function, other cell types and the second protocol", "src/growth_chart.py: one call per chart")
s.shapes.add_picture(str(FIG / "final_overview_2x2.png"), Inches(0.4), Inches(1.35), width=Inches(8.6))
bullets(s, [
    f"Velasco neuron: mirror image of progenitors. Test MSLL {ext.loc['Velasco neuron','MSLL']:.2f}, z skew {ext.loc['Velasco neuron','z_skew']:.2f}, no sample flagged.",
    f"Velasco glia: near zero before day 90, rises after. MSLL {ext.loc['Velasco glia','MSLL']:.2f}.",
    f"Lancaster NPC: 81 samples but no data between day 63 and 120, test z sd {ext.loc['Lancaster NPC','z_sd']:.1f}. The band balloons where there is nothing to fit. A demo of the method and a warning, not a result.",
    "Each chart: one call to fit_growth_chart(df, y_col) plus one to plot_growth_chart().",
], 9.2, 1.5, 3.9, 5.3, size=13)
footer(s, "All charts drawn for the largest publication of each protocol (Paulsen 2022 for Velasco, Kanton 2019 for Lancaster).")

# ---- 7 subsampling
s = prs.slides.add_slide(BLANK); title(s, "How many organoids does a lab need? About 40 to start, 80 to be stable")
s.shapes.add_picture(str(FIG / "subsampling_summary.png"), Inches(0.4), Inches(1.35), width=Inches(8.4))
rows = [["n train", "median curve moves (pp)", "test MSLL", "test z sd"]]
for n in [20, 40, 80, 105]:
    rows.append([n, f"{fin.loc[n,'p50_dev_pp']:.1f}", f"{fin.loc[n,'MSLL']:.2f}", f"{fin.loc[n,'z_sd']:.2f}"])
table(s, rows, 8.95, 1.45, 4.1, col_w=[0.8, 1.5, 0.9, 0.9], size=11)
bullets(s, [
    "Refit the final model on stratified random subsets of the 105 train organoids, 10 draws each.",
    "n = 20: median curve off by ~5 pp, MSLL positive (worse than guessing the mean), z sd 2.5. Unusable.",
    "n = 40: curve within ~2 pp, MSLL -1.1, z sd 1.2. A first chart.",
    "n = 80: within ~1 pp, MSLL within 0.02 of the full fit. Stable.",
    "Below ~10 organoids per lab the batch-effect model is worse than ignoring labs (orange beats blue at n = 20).",
    "Caveat: subsets are drawn from the same 105 samples, so stability at n = 80 is optimistic.",
], 8.95, 3.3, 4.1, 3.6, size=12)
footer(s, "pp = percentage points of progenitor fraction, averaged over the age grid. This is the number labs currently guess.")

# ---- 8 limits and next
s = prs.slides.add_slide(BLANK); title(s, "What this is, what it is not, what comes next")
bullets(s, [
    "What we have: a working pipeline from a public atlas to a calibrated centile chart with per-organoid z-scores, in one public repo, reproducible in minutes.",
    "Limits:",
    ("131 samples, not 100,000. Bands are honest about that: they carry the posterior uncertainty of the curve.", 1),
    ("A 'sample' is one sequencing library; HNOCA does not say whether it is one organoid or a pool.", 1),
    ("Publication and age are confounded (Velasco 2019 has no sample before day 101). The lab offset for that paper is partly extrapolated.", 1),
    ("Composition fractions sum to 1; we model each one separately. A compositional model is the proper next step.", 1),
    "Next: add new datasets as they appear (every HNOCA update is a free refit); try Dirichlet or logistic-normal likelihood; apply to a disease or drug-treated organoid set and ask which cell types leave the normal band first.",
    "Thanks: Johanna Bayer's normative modelling tutorial (Oct 2), the PCNtoolkit team, the HNOCA authors, Brainhack Montreal organizers.",
], 0.6, 1.4, 12.1, 5.3, size=16)
footer(s, "github.com/Liberty23513/organoid-growth-charts  |  data: He et al. 2024 Nature (CC BY 4.0)  |  method: Rutherford et al. 2022 Nat Protoc, PCNtoolkit 1.3")

OUT.parent.mkdir(exist_ok=True); prs.save(OUT); print(OUT, OUT.stat().st_size, "slides:", len(prs.slides))
