# Day 2 任务分工（10 月 6 日，约 6 小时）

## 现状（repo 里的事实）

- 做完：B1 全部 5 步。`blr_homo` 跑通，结果和图都在 repo 里。基线数字：test EXPV 0.786，SMSE 0.236，MSLL −0.707，z 偏度 2.0，p5 在 118/173 天为负，σ 到处 0.16。
- 没做：B2（异方差、batch effect、指标表）、B3（校准）、warp。A 线全部没做（没有 notebook 01/02，没有 results/baseline_rolling）。
- 明天（Day 3）只有 3.5 小时，14:30 开始总结展示。所以**今天结束时必须定下最终模型，并且主图画出来**。明天只做 Lancaster 补充、整理、做 slide。

## 今天的目标，按优先级

1. 最终模型定下来（Velasco，frac_NPC_IP）：hetero 还是 hetero + batch，要不要 warp / logit。
2. 最终 centile chart 一张，带 z 分数标注的离群样本。
3. 子采样曲线（stretch goal）至少跑出 n = 20/40/80/105 的 p50 抖动图。
4. 无模型基线一张，用来说"BLR 确实比最朴素的分位数好"。
5. Lancaster 和 neuron/glia 能跑多少算多少，明天也能补。

## B 线（Boting）：定模型，做主图

**B2-6 异方差（45 分钟）。** `heteroskedastic=True`，其余和 blr_homo 一样。输出 `results/blr_hetero/`。要看的四个数和 blr_homo 比：MSLL 应该比 −0.707 更负；按年龄段的 z 标准差应该都接近 1（昨天是 1.28 和 0.24）；σ 在 90 到 120 天应该掉到 0.05 左右；p5 负数的天数应该减少但不会归零。

**B2-7 batch effect（30 分钟）。** 加 `batch_effects=["publication"]`，输出 `results/blr_hetero_batch/`。预期收益小（昨天按 publication 看 z 均值都在 ±0.2 内），但 Uzquiano 的 z 标准差只有 0.51，说明实验室差别在散布不在均值。跑完看 MSLL 有没有动。
注意：grid 预测时 publication 列要给一个真实存在的值，否则 batch effect 模型不知道用哪个偏移。推荐用 Paulsen 2022（样本最多），并在图注里写明。

**B2-8 指标表（15 分钟）。** 三个模型的 EXPV / SMSE / MSLL / Skewness / Kurtosis 一张表，`results/blr_metrics.csv`。

**B3 校准（45 分钟）。** 每个模型：test z 直方图 + QQ 图，按年龄段的 z 均值和标准差，按 publication 的 z 均值。`figures/calibration_<model>.png`。这组图直接进最终展示。

**偏斜处理（60 分钟）。** 偏度 2.0 和 p5 负数是同一个问题：高斯分布不知道 y 的下界是 0。两条路，先查 `inspect.signature(BLR.__init__)` 里有没有 warp 相关参数：
- 有：`warp="WarpSinArcsinh"`（或该版本的等价写法），输出 `results/blr_warped/`。
- 没有，或者 20 分钟没跑通：对 y 做 logit 变换。`y_logit = log(p / (1 − p))`，p 先 clip 到 [0.005, 0.995]。在 logit 空间拟合 blr_hetero，预测出的 centiles 用 `1 / (1 + exp(−x))` 变回比例空间。z 分数直接用 logit 空间的 z。输出 `results/blr_hetero_logit/`。
两条路都会让 p5 ≥ 0，偏度应该掉到 1 以下。

**午饭前决定最终模型。** 标准按顺序：test MSLL 最负；z 偏度最接近 0；按年龄段 z 标准差最接近 1；p5 不为负。写一行进 README。

**下午 1：把最终模型做成函数（45 分钟）。** `src/growth_chart.py`：
```python
def fit_growth_chart(df, y_col, split_col="split", model_name="final", batch=None, transform=None):
    """Fit the chosen BLR on df (one protocol), write results/<model_name>/{centiles,zscores}.csv, return (centiles, zscores)."""
```
从 notebook 03 里把 to_normdata、模型定义、export_results 搬进去。这是组员下午换 protocol、换 y 的入口。

**下午 2：子采样曲线（60 到 90 分钟）。** `notebooks/05_subsampling.ipynb`。用 `data/split_velasco.csv` 的 105 个 train 样本，按年龄段分层抽 n = 20, 40, 80, 105，每个 n 抽 10 次（n = 105 就是全部，只有 1 次），每次用最终模型拟合，存 p50 和 p5/p95 曲线。图：每个 n 一个小图，10 条 p50 线叠在一起；再一张总结图，x 轴是 n，y 轴是 p50 曲线 10 次之间的平均标准差（或者 p5 到 p95 带宽的变异）。这就是"需要多少个 organoid"的答案图。

**下班前：** `figures/final_velasco_npc.png`（最终 centile chart，test 样本标记，|z| > 1.96 的样本标注）。README 加 "Day 2 status"。push。

## A 线（组员）：复现、基线、扩展

不需要懂贝叶斯。上午的两件事完全独立，下午依赖 B 线的函数。

**A0 环境和复现（45 分钟）。** 装 conda 环境：`conda create -n normative python=3.12 && conda activate normative && pip install pcntoolkit pandas scipy matplotlib scikit-learn jupyter`（PCNtoolkit 1.3.0）。clone repo，从头到尾跑 `notebooks/03_pcntoolkit_blr.ipynb`。对一下数字：EXPV 0.786，SMSE 0.236，MSLL −0.707。对不上就是环境问题，当场解决，否则下午换不了 protocol。

**A2 无模型基线（45 分钟）。** `notebooks/02_baseline_centiles.ipynb`。Velasco train 样本，对 age 20 到 192 每一天，取 ±15 天窗口内的 train 样本，算 5/25/50/75/95 分位数；窗口内不足 8 个样本就加宽到 8 个。test 样本的 z 用窗口内 train 的均值和标准差。输出 `results/baseline_rolling/centiles.csv` 和 `zscores.csv`，格式和 blr 的完全一样（列名见 CLAUDE.md）。图 `figures/baseline_rolling_velasco.png`。
附带算一个和 BLR 可比的数：test 集 z 的均值、标准差、偏度，以及 |z| > 1.96 的个数。

**A1 数据总览（30 分钟）。** 一张图：322 个样本 age 对 frac_NPC_IP，按 protocol 上色，样本数 < 7 的 protocol 合并为 other。一张表 `results/data_summary.csv`：每个 protocol × publication 的样本数、年龄范围。这两样是展示的第一页。

**下午 3：换 protocol 和 y（B 线函数就绪后，2 小时）。** 用 `src/growth_chart.py`：
1. Lancaster protocol，frac_NPC_IP。先要一个 split：照 `data/split_velasco.csv` 的做法做 `data/split_lancaster.csv`（年龄段改成 0-30/30-60/60-90/90-120，Lancaster 只到 120 天），seed 2026。输出 `results/final_lancaster_npc/`，图 `figures/final_lancaster_npc.png`。
2. Velasco，frac_neuron 和 frac_glia。输出 `results/final_velasco_neuron/`、`results/final_velasco_glia/`，各一张图。
3. 做得完的话，一张 2×2 拼图：Velasco NPC / Velasco neuron / Velasco glia / Lancaster NPC。

## 协作方式：fork + pull request

主 repo 是 `Liberty23513/organoid-growth-charts`（下面叫 upstream）。组员在自己的 fork 上工作，通过 pull request 合进来。

**组员，一次性设置：**
```bash
git remote add upstream https://github.com/Liberty23513/organoid-growth-charts.git
git remote -v        # 应该看到 origin（自己的 fork）和 upstream（主 repo）
```

**组员，每次开工前和 15:00 拿 B 线函数时：**
```bash
git fetch upstream
git merge upstream/main
```

**组员，每完成一块：**
```bash
git add <自己的文件>
git commit -m "A2: rolling-window baseline"
git push origin main
```
然后在 GitHub 自己的 fork 页面点 Contribute → Open pull request，目标是 Liberty23513/organoid-growth-charts 的 main。

**Boting：** 在主 repo 的 Pull requests 页面看到 PR，点 Merge pull request。合完之后本地 `git pull` 拿到组员的结果。

**文件归属（避免冲突的唯一规则）。** 每个文件只有一个人改。notebook 文件冲突几乎无法手动合并，所以这条必须守住。

| 归 Boting | 归组员 |
|---|---|
| `notebooks/03_pcntoolkit_blr.ipynb`, `04_*`, `05_subsampling.ipynb` | `notebooks/01_raw_plots.ipynb`, `02_baseline_centiles.ipynb`, `06_extensions.ipynb` |
| `src/growth_chart.py` | `data/split_lancaster.csv` |
| `results/blr_*`, `results/final_velasco_npc/` | `results/baseline_rolling/`, `results/data_summary.csv`, `results/final_lancaster_npc/`, `results/final_velasco_neuron/`, `results/final_velasco_glia/` |
| `figures/calibration_*`, `figures/final_velasco_npc.png`, `figures/subsampling_*` | `figures/raw_*`, `figures/baseline_rolling_*`, `figures/final_lancaster_*`, `figures/final_velasco_neuron*`, `figures/final_velasco_glia*` |
| `README.md`, `CLAUDE.md`, `TASKS_*.md` | `STATUS_A.md`（组员的 Day 2 status 写这里，Boting 合进 README） |

`src/growth_chart.py` 有 bug 或缺参数：组员不要自己改，在 PR 或当面告诉 Boting。组员需要的辅助函数放在自己的 notebook 里。

**节奏：** 组员每完成一块（A0、A2、A1、每个扩展）开一个 PR，不要攒到最后。Boting 每次看到就合，合之前不需要细看代码，只确认改的都是组员名下的文件（PR 页面的 Files changed 标签）。

## 同步点

- **10:30**：组员环境是否跑通 notebook 03。没跑通就改做 A2 和 A1（纯 pandas，不需要 PCNtoolkit），下午的扩展由 Boting 自己跑。
- **午饭**：最终模型定了没有。看 `results/blr_metrics.csv`。
- **15:00**：`src/growth_chart.py` 能不能被组员 import 并跑 Lancaster。
- **17:00**：都 push。各自在 README 的 "Day 2 status" 下写三行。

## 明天（Day 3，3.5 小时）预告

上午：补没做完的扩展，拼最终图，写 README 的结果部分。12:00 开始做 5 分钟展示的 slide（5 页：问题、数据、方法、结果图、样本量曲线）。14:30 展示。
