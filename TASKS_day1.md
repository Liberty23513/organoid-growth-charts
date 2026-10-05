# Day 1 任务分工（10 月 5 日，下午约 3 小时）

两条线并行，互不等待。A 线不碰 PCNtoolkit，B 线不碰画图细节。中间同步一次（开工 90 分钟后），下班前合一次。

目标：今天结束时 repo 里有 (1) 原始数据的完整图集，(2) 一个不依赖 PCNtoolkit 的基线百分位图，(3) PCNtoolkit BLR 在 Velasco 子集上跑通并输出 z 分数。三样东西用同一套文件格式，明天直接对比。

## 共用约定（先做，10 分钟，Boting）

1. 固定 train/test 划分，两条线都用同一份：
   ```python
   import pandas as pd, numpy as np
   df = pd.read_csv("data/hnoca_sample_composition.csv")
   v = df[df.protocol.str.contains("Velasco")].copy()
   v["age_bin"] = pd.cut(v.age, [0, 30, 60, 90, 120, 200], labels=False)
   rng = np.random.default_rng(2026)
   v["split"] = "train"
   for b, g in v.groupby("age_bin"):
       test_idx = rng.choice(g.index, size=max(1, round(0.2 * len(g))), replace=False)
       v.loc[test_idx, "split"] = "test"
   v[["sample", "split"]].to_csv("data/split_velasco.csv", index=False)
   ```
   按年龄段分层抽 20% 做 test，这样 test 集每个年龄段都有。
2. 结果文件格式，所有模型都输出这两个 CSV 到 `results/<model_name>/`：
   - `centiles.csv`：列 `age, p5, p25, p50, p75, p95`，age 从 20 到 192 每 1 天一行。
   - `zscores.csv`：列 `sample, age, publication, split, y, mu, sigma, z`。
   `model_name` 例如 `baseline_rolling`、`blr_homo`、`blr_hetero`、`blr_hetero_batch`。
3. 文件夹：`notebooks/` 放 notebook，`src/` 放可复用函数，`results/` 放上面的 CSV，`figures/` 放 PNG。各自只在自己的 notebook 里改，避免 git 冲突。

## A 线：数据和基线（组员）

不需要任何 PCNtoolkit 知识。目标是把数据摸透，并做一个"没有模型"的参照，明天用来检验 BLR 是不是真的更好。

**A1. 原始数据图集（60 分钟）** `notebooks/01_raw_plots.ipynb`
- 全部 322 个样本：age 对 frac_NPC_IP 散点，按 protocol 上色。只保留样本数 ≥ 7 的 protocol，其他合并为 other。
- Velasco 子集：age 对 frac_NPC_IP、frac_neuron、frac_glia 三张图，按 publication 上色。看每篇文章覆盖的年龄段（Velasco 2019 只有 101 到 190 天）。
- Lancaster 子集：同样三张。
- 每篇 publication 的样本数和年龄范围表，存成 `results/data_summary.csv`。
- 输出到 `figures/raw_*.png`。
- 看完回答一个问题写进 notebook：Velasco 子集里，有没有哪篇文章整体偏高或偏低？这是明天 batch effect 要处理的东西。

**A2. 无模型基线百分位（60 分钟）** `notebooks/02_baseline_centiles.ipynb`
- Velasco 子集，只用 train 样本。
- 方法：滑动窗口分位数。对 age 从 20 到 192 每一天，取窗口 ±15 天内的 train 样本，算 5/25/50/75/95 分位数。窗口内少于 8 个样本时把窗口加宽到有 8 个为止。
- 存 `results/baseline_rolling/centiles.csv`。
- test 样本的 z：用窗口内 train 样本的均值和标准差算 z = (y − mean) / sd，存 `results/baseline_rolling/zscores.csv`。
- 画图：散点 + 5 条分位数线，test 样本用不同标记。存 `figures/baseline_rolling_velasco.png`。

**A3. 如果还有时间：子采样脚手架（30 分钟）** `src/subsample.py`
- 写一个函数 `stratified_subsample(v, n, seed)`：从 Velasco 的 train 样本里按 age_bin 分层抽 n 个。
- 用它对 n = 20, 40, 80 各抽 10 次，跑 A2 的滑动窗口分位数，画出 p50 线的 10 次重叠图。这是 stretch goal 的雏形，明天换成 BLR 就行。

## B 线：PCNtoolkit BLR（Boting）

目标是跑通，不是跑好。今天只做 Velasco 子集的 frac_NPC_IP。

**B1. 最小 BLR 跑通（60 分钟）** `notebooks/03_pcntoolkit_blr.ipynb`
- 照 tutorial 的 notebook 改参数：covariates = ['age']，response_vars = ['frac_NPC_IP']，先**不加** batch_effects。
- 用 `data/split_velasco.csv` 的划分。
- 跑通后把 test 集的预测均值、方差、z 分数导出成 `results/blr_homo/zscores.csv`。
- 在 age 20 到 192 的网格上预测，导出 `results/blr_homo/centiles.csv`（p5 = mu − 1.645·sigma，依此类推）。
- 卡住超过 20 分钟就记录报错，先跳到 B2 用 sklearn 版本顶上，回头再修。

**B2. 加异方差和 batch effect（60 分钟）**
- 同一个 notebook，第二个模型：打开异方差（PCNtoolkit 的 heteroskedastic 选项），输出到 `results/blr_hetero/`。
- 第三个模型：加 batch_effects = ['publication']，输出到 `results/blr_hetero_batch/`。
- 三个模型的 test 集指标（EV、SMSE、MSLL）汇总成一张表存 `results/blr_metrics.csv`。

**B3. 校准检查（30 分钟）**
- 对每个模型，test 集 z 分数：直方图 + QQ 图；按 age_bin 分组的 z 均值和标准差；按 publication 分组的 z 均值。
- 存 `figures/calibration_<model>.png`。
- 看一眼 z 的偏度。如果明显偏斜，明天第一件事就是 warped BLR。

## 同步点

**90 分钟后（约 16:00）**：各自 push 一次。A 给 B 看原始图集，特别是 publication 偏移；B 告诉 A PCNtoolkit 有没有跑通。如果 B 卡死在安装或 API，A 的 A2 基线就成了今天的主图，B 改去帮 A 做 A3。

**下班前（约 17:30）**：
- 把 `results/baseline_rolling/centiles.csv` 和 `results/blr_*/centiles.csv` 画在同一张图上，存 `figures/day1_comparison.png`。
- 在 README 加一节 "Day 1 status"，三行：做了什么、哪里卡住、明天第一件事。
- 都 push。

## 明天的预告（不用今天做）

- Warped BLR 或 logit 变换处理 0 附近的偏斜。
- Lancaster protocol 重复整条流水线。
- frac_neuron、frac_glia。
- 子采样曲线换成 BLR，n = 20/40/80/131，每个 10 次。
- 最终图：每个 protocol 一张 centile chart，每个 organoid 一个 z。
