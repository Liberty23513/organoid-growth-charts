# Wrap-up talk script (5 minutes, 8 slides)

Spoken in English. Chinese notes under each slide are for you only. Timings add to about 5 minutes; if you are told 3 minutes, speak slides 1, 5, 7, 8 only.

---

## Slide 1, title (20 s)

Hi, I'm Boting, this is the organoid growth charts project. Kids have growth charts: you put one child on a percentile curve for their age. Brain organoids don't have that. Over the last two and a half days we built one from public data, and we measured how many organoids you need to draw one.

> 中文提示：开场一句话讲清类比，不用解释 organoid 是什么，下一页讲。

## Slide 2, problem (40 s)

A brain organoid is a few millimeters of human brain tissue grown from stem cells over weeks to months. Labs make thousands of them, and the field's known weakness is variability: between batches, between lines, between labs. The question every lab asks is "is this batch normal for its age?", and today that's answered by eye.

Pediatrics solved this with growth charts. Neuroimaging solved it with brain charts, which are normative models: learn the distribution of a measure over age, then give every individual a z-score. Organoids had neither. So on Monday we promised a centile chart per protocol with a z-score for every organoid, and as a stretch, the number of organoids you need.

> 中文提示：如果有人问 Faravelli 2026，答：他们从转录组预测年龄，我们反过来，年龄已知，问组成是否典型。

## Slide 3, data (40 s)

The data is HNOCA, the human neural organoid cell atlas, 1.8 million cells, public. We didn't download the 19 gigabytes. A script reads just the per-cell metadata over HTTP, groups cells by sample, and counts cell-type fractions. Three minutes. Out comes one row per organoid sample: days in culture, protocol, publication, and the fraction of progenitors, neurons, glia.

The usable subsets are the Velasco protocol, 131 samples from 4 labs, and Lancaster, 81 samples. One chart per protocol, because different protocols follow different trajectories, like separate charts per sex. We fixed a train/test split on day one: 105 train, 26 held out. Every number from here on is on those 26.

> 中文提示：右图是最初的 naive 模型，带子到处一样宽、p5 掉到负数，正好引出下一页。

## Slide 4, method (60 s)

The tool is PCNtoolkit, Bayesian linear regression. The mean is a B-spline on age, so the curve bends. Centiles are mean plus or minus k times sigma. z is distance from the mean in units of sigma.

We added one ingredient at a time, each fixing one failure you can see in the data. First, sigma that depends on age: the spread is three times larger at day 30 than at day 100. Second, publication as a batch effect: each lab gets its own offset and its own noise level. Third, a logit transform of y, because fractions are bounded at zero and the Gaussian centiles were going negative.

The table shows six models on the same 26 test organoids. We picked by MSLL, which scores the whole predictive distribution, then by whether the z-scores look like a standard normal. The final model has the best MSLL, skewness down from 2.0 to 0.8 (what remains is one day-70 test organoid with far too many progenitors), and a 5th centile that never goes below zero. The calibration plots on the right show z roughly normal in every age bin and every publication.

> 中文提示：被问 MSLL 是什么，一句话：预测分布给每个 test 样本打的分，σ 太宽太窄都扣分，越负越好。被问为什么不用 GAMLSS：同一族方法，PCNtoolkit 是周五 tutorial 教的，有现成人手。

## Slide 5, result (60 s)

This is the chart. Velasco protocol, progenitor fraction. Progenitors start around 60% at day 20, fall to about 8% by day 100, and stay flat. The band is wide early and narrow late. At day 30 the 5th to 95th centile spans 14% to 94%. At day 180 it spans 4% to 10%. A constant-sigma model cannot draw this.

Five of 131 organoids fall outside plus or minus 1.96; about six and a half would be expected by chance, so the chart is not over-flagging. The three at day 32 are from one paper and have almost no progenitors. The one at day 70 and the one at day 166 have far too many. Every organoid in HNOCA now has a z-score in a CSV in the repo.

> 中文提示：被问"那 5 个是不是真的异常"：我们不知道，chart 只能说它们不典型，原因要回到原文章查。这正是这个工具的用途。

## Slide 6, extensions (30 s)

The final model is one function. Same call for neurons, which are the mirror image of progenitors, and for glia, which are near zero before day 90 and rise after. Both calibrate well.

Lancaster is the honest failure: 81 samples but nothing between day 63 and day 120, so the band balloons where there is no data. That's a demo of the method and a warning about the data, not a result.

## Slide 7, how many organoids (50 s)

This was the stretch goal and I think it's the most useful number we produced. We refit the final model on random subsets of the 105 training organoids, stratified by age, ten draws each.

With 20 organoids the median curve is off by about 5 percentage points and the model scores worse than guessing the mean. Unusable. With 40 you get a first chart, within about 2 points. With 80 the curve is within 1 point and the test score is essentially the full-data score. So: about 40 to start, 80 to be stable. And below about 10 organoids per lab, modelling the lab effect hurts; you should drop it.

One caveat: the subsets come from the same 105 samples, so 80 is probably optimistic.

> 中文提示：pp = percentage points，progenitor 比例的百分点。

## Slide 8, limits and next (40 s)

What we have is a pipeline from a public atlas to a calibrated centile chart with per-organoid z-scores, in one public repo, reproducible in minutes.

What it is not: it's 131 samples, not 100,000, and the bands say so. A sample is a sequencing library, not necessarily one organoid. Publication and age are confounded for one lab. And fractions sum to one, which we ignored by modelling each one separately.

Next: every HNOCA update is a free refit. A compositional likelihood is the proper fix. And the real use is to take a disease or drug-treated organoid set and ask which cell type leaves the normal band first.

Thanks to Johanna for the tutorial, to the PCNtoolkit and HNOCA teams, and to the organizers. The repo is on the slide.

> 中文提示：结束后最可能的两个问题：(1) 怎么用到自己实验室的数据：需要每个 organoid 的 scRNA-seq 或任何能给出细胞类型比例的读出，40 个起步。(2) 用 Bayesian 而不是 quantile regression 的理由：样本少时后验给出曲线本身的不确定性，而且层级结构处理多实验室数据；quantile regression 是我们明天想加的交叉验证。
