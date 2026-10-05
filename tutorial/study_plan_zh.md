# 今晚学习大纲：Brainhack 前的贝叶斯回归 / normative modelling 速成

总时长约 3.5 到 4 小时。按顺序走，时间不够就砍掉第 5 块（动手）和第 6 块后半部分。

## 明天你真正需要做到的三件事

1. 用两句话讲清项目：x 轴是 organoid 培养天数，y 轴是某个细胞类型的比例（先做 progenitor，即 NPC + IP），数据是 HNOCA 的 322 个样本，目标是画出像儿童生长曲线那样的百分位曲线（centile chart），然后看单个 organoid 落在第几百分位。
2. 用一句话解释为什么用贝叶斯回归而不是普通回归：我们要的不是一条均值线，而是每个年龄上的完整分布（才能画 5%、50%、95% 的线），并且样本只有 322 个，需要模型诚实地给出不确定性。
3. 听懂队友说的词：prior、posterior、centile、z-score、batch effect、partial pooling、MSLL。不需要会推公式。

## 不用学的东西（今晚别碰）

- MCMC 采样算法细节、NUTS、PyMC 内部实现
- 共轭先验的推导
- Variational inference
- GAMLSS 的具体分布族（知道它是 Bethlehem 2022 brain charts 用的方法就够）

---

## 上周五的 tutorial 怎么看（45 到 60 分钟，可以替代第 1 到 4 块的阅读部分）

Tutorial 的结构正好就是第 1 到 4 块的顺序：直线、样条、异方差、site effect、校准检查、PCNtoolkit BLR、warped BLR、病人 z 分数。所以把它当主线，边看边对照下面的要点，比分开读两份材料省时间。代码只看每一步"模型多了什么"，数据整理、画图代码、PCNtoolkit 的参数名全部跳过。

| Tutorial 的阶段 | 需要看懂的一句话 | 跳过 |
|---|---|---|
| 模拟数据介绍 | 输入是年龄，输出是皮层厚度。这不是 brain age 预测，方向和我们一样：年龄已知，看指标是否偏离常模 | 模拟数据怎么生成的 |
| 直线拟合 | 残差是什么，σ 是什么。残差图里能看出直线不够 | 代码 |
| 换成样条 | 均值线弯了，但每个年龄上的散布还是一样宽 | spline 的 knot 怎么选 |
| 异方差（variance 随年龄变） | σ 变成 σ(x)，百分位线的宽度开始随年龄变。这是从"均值线"到"生长曲线"的关键一步 | 方差的参数化方式 |
| site effect 放进均值和方差 | 每个 site 一个偏移，不处理的话偏移会被算进 σ，曲线变宽。看老师怎么说 site 和 age 混淆（某些 site 只有某个年龄段），因为我们的数据有同样的问题：Velasco 2019 实验室的样本只覆盖 101 到 190 天 | 代码 |
| 按年龄组检查校准 | 把 test 集的 z 分数按年龄分组，每组均值应接近 0、方差接近 1。这是"模型对所有年龄都诚实"的检查 | 画图代码 |
| PCNtoolkit BLR | 前面手搓的东西 PCNtoolkit 一行搞定。只需要认出 covariates、batch_effects、response_vars 三个参数对应前面哪一步 | 其他所有参数、文件路径、输出格式 |
| Warped BLR | 皮层厚度有些区域分布偏斜，高斯假设不对，warping 先变换 y。我们的比例数据在 0 附近也偏斜，所以这是我们第一个要试的选项 | warp 函数的数学形式 |
| 病人 z 分数 | 把新样本放到模型里得到 z，z 超出 ±1.96 就是偏离常模。这就是我们"单个 organoid 落在第几百分位"的实现方式 | 代码 |

如果老师讲了 HBR（分层贝叶斯）：只需要记住 partial pooling 这一个概念，见第 3 块。不需要看 PyMC 或采样相关的内容。

看完之后你应该能用自己的话回答：这个 tutorial 一共给模型加了哪四样东西（弯曲、变宽、site 偏移、非高斯），每一样对应我们 organoid 数据里的什么问题。

## 第 1 块（40 分钟）：普通回归到百分位曲线

目标：建立"回归给的是分布，不只是一条线"这个概念。

- 线性回归：y = a + b·x + 噪声。拟合就是找让残差平方和最小的 a 和 b。
- 残差（residual）：观测值减预测值。噪声标准差 σ 描述残差有多散。
- 曲线怎么办：把 x 换成一组基函数（basis functions），比如多项式或 B-spline。模型对参数仍然是线性的，所以还叫线性回归。B-spline 就是把 x 轴切成几段，每段用一个光滑的小曲线。
- 关键一步：如果噪声是高斯的，那么在任意 x 上，y 的分布就是 Normal(μ(x), σ(x))。有了这个分布，就能画出百分位线：
  - 50th centile = μ(x)
  - 95th centile ≈ μ(x) + 1.64·σ(x)
  - 5th centile ≈ μ(x) − 1.64·σ(x)
- z 分数：z = (y_observed − μ(x)) / σ(x)。一个 organoid 的 z = −2 意味着它的 progenitor 比例比同龄 organoid 的常模低 2 个标准差，大约落在第 2 百分位。
- 异方差（heteroskedastic）：σ 随 x 变化。Organoid 早期和晚期的变异度很可能不同，所以我们需要 σ(x) 而不是一个常数 σ。

自检问题：为什么用 LOESS 画一条光滑的均值线不够？答：LOESS 只给 μ(x)，不给 σ(x)，也不给参数不确定性，所以画不出有据可依的百分位线。

## 第 2 块（40 分钟）：贝叶斯的核心思想

目标：能解释 prior、likelihood、posterior 三个词，并说出它们对我们项目的实际好处。

- 频率派回归：参数 a、b 是固定未知数，给一个点估计。
- 贝叶斯回归：参数本身有分布。
  - Prior（先验）：拟合前我们对参数的信念。比如"B-spline 的系数不会特别大"，用一个均值为 0 的高斯分布表达。
  - Likelihood（似然）：给定参数，观测到这些数据的概率。
  - Posterior（后验）：prior × likelihood 再归一化。这是拟合后对参数的信念。
- Bayesian linear regression（BLR）：和普通线性回归是同一个模型，只是参数加了高斯先验。好处是后验有解析解，不需要采样，几秒钟跑完。PCNtoolkit 里的 BLR 就是这个，加上 B-spline 基函数和异方差噪声。
- Predictive distribution（预测分布）：对新的 x，把参数后验和噪声一起积分掉，得到 y 的分布。z 分数和百分位线都从这里算。它比频率派的预测区间宽一点，因为把参数不确定性也算进去了。

对我们项目的三个具体好处：
1. 样本少（322 个，不是 brain charts 的几万个），参数不确定性大。贝叶斯模型把这个不确定性传到百分位线上，所以曲线自带置信带。这正好是我们想量化的东西。
2. 先验起正则化作用，B-spline 不容易过拟合。
3. 层级结构（第 3 块）可以跨实验室共享信息。

一个小坑：高斯噪声假设。比例数据在 0 到 1 之间，靠近 0 时分布会偏斜。PCNtoolkit 的 BLR 有 "warping" 选项（Fraza 2021），把 y 先做一个非线性变换让它更接近高斯。另一个办法是对 y 做 logit 变换。知道这个坑就行，明天讨论时可以提。

## 第 3 块（30 分钟）：层级模型和 batch effect

目标：能解释为什么要把 publication 或 protocol 放进模型，以及 HBR 怎么处理它。

- 问题：322 个样本来自不同实验室、不同 protocol、不同文章。每个实验室的曲线可能整体偏高或偏低。如果不处理，这些偏移会被当成噪声，σ 被高估，百分位线变宽。
- 方案 1：固定效应。每个 publication 一个 dummy 变量，相当于每家一个截距。简单，但样本少的实验室估计很差。
- 方案 2：Hierarchical Bayesian Regression（HBR）。每个 publication 的截距和斜率不是独立估计的，而是假设它们来自一个共同的总体分布。样本少的实验室会被"拉向"总体均值。这个叫 partial pooling（部分池化）。HBR 需要 MCMC 采样，比 BLR 慢，几分钟到几十分钟。
- PCNtoolkit 里 batch_effects=['publication'] 就是在告诉 HBR 把 publication 当作层级。
- 我们数据的一个具体限制：HNOCA 里 batch 和 bio_sample 是一对一的，所以不能把 batch 当随机效应（每组只有一个样本，没法估计组内方差）。要用 publication 或 protocol 这种每组有多个样本的变量。
- Protocol 的问题要分开想：Velasco 和 Lancaster protocol 的 progenitor 曲线形状本身就不同，这不是"偏移"，是不同的常模。合理做法是先只用 Velasco protocol 的样本拟合（这部分样本最多，四个实验室重叠得也好），再决定 protocol 是分开拟合还是作为协变量。

## 第 4 块（20 分钟）：怎么判断模型好不好

目标：队友问"你怎么评估"时能答上来。

- 先分 train / test。所有指标都在 test 集上算。
- 常用指标（PCNtoolkit 会直接输出）：
  - Explained variance（EV）：模型解释了多少 y 的方差。
  - SMSE（standardized mean squared error）：均方误差除以 y 的方差，小于 1 说明比"只猜均值"好。
  - MSLL（mean standardized log loss）：衡量整个预测分布好不好，不只是均值。越负越好。这是 normative modelling 里最重要的指标，因为我们关心的是分布。
  - z 分数的校准：test 集上的 z 应该近似标准正态。看 QQ 图，或者看偏度和峰度。如果 z 系统性偏斜，说明高斯假设不对，需要 warping。
- 一个只有我们项目才有的检查：同一个 publication 内的 z 分数均值应该接近 0。如果某个实验室的 z 全是负的，说明 batch effect 没处理好。

## 第 5 块（60 分钟，可选）：动手跑一次

目标：亲眼看到一条百分位曲线从数据里出来。只要看到图，不求完美。

两条路，选一条：

- 路线 A：跑 Johanna Bayer 的 Normative_modelling_tutorial notebook 前半部分（BLR 部分）。先在模拟数据上跑通，不急着换成我们的数据。
- 路线 B（PCNtoolkit 装不上时的备选）：用 sklearn 做一个最小版本。SplineTransformer 生成 B-spline 基函数，BayesianRidge 做贝叶斯线性回归，predict(return_std=True) 拿到 μ(x) 和 σ。画 μ ± 1.64σ 就是粗糙的 5/50/95 百分位线。这个版本 σ 是常数，不是异方差，但足够建立直觉。数据用 data/hnoca_sample_composition.csv，x 是 organoid_age_days，y 是 frac_NPC_IP，先只筛 Velasco protocol。

如果两条路都卡住，放弃，睡觉比这块重要。

## 第 6 块（20 分钟）：pitch 和问答准备

一分钟 pitch 骨架：

1. 儿童有生长曲线，一个孩子的身高可以放到同龄人的百分位里看。脑 organoid 没有这种东西。
2. 我们用 HNOCA 的 322 个样本，x 轴培养天数，y 轴 progenitor 比例，画出 organoid 的生长曲线。
3. 方法借自 normative modelling，就是神经影像里 brain charts 背后的那一族方法。用贝叶斯回归，所以百分位线自带不确定性。
4. 产出：一张 centile 图（保底），加一条样本量曲线（stretch goal），告诉大家需要多少个 organoid 才能把曲线估稳。
5. 需要的人：会 Python 的，用过 PCNtoolkit 或任何回归的，或者只是想学 normative modelling 的。

注意措辞：不要说我们的方法"和 tutorial 一样"，说"借自 normative modelling 这一族方法"。

预期问题和一句话回答：

- 322 个样本够吗？不够做临床级的图表，但够做 proof of concept。样本量到底够不够，正是 stretch goal 要用子采样回答的问题。
- 为什么贝叶斯？要的是分布不是均值线，样本少所以不确定性必须显式表达，层级结构能处理多实验室数据。
- 和 Faravelli 2026（Arlotta lab）的区别？他们用转录组预测 organoid 的年龄，是一个"时钟"。我们反过来：年龄已知，问的是组成是否偏离同龄常模。
- "异常"怎么定义？z 分数超出 ±1.96，或落在 5% 以下 / 95% 以上。阈值是约定，可以讨论。
- 不同 protocol 怎么办？先只做 Velasco protocol，再把 protocol 当协变量或分开拟合。
- 为什么不用 GAMLSS？GAMLSS 是 Bethlehem 2022 用的，也是 normative modelling。我们用 PCNtoolkit 是因为 Brainhack 上有 tutorial 和会用的人。两者可以互为验证。

---

## 术语表（队友会说的词）

- Prior / likelihood / posterior：先验 / 似然 / 后验。拟合前的信念、数据给的证据、拟合后的信念。
- Predictive distribution：对新 x 预测 y 的整个分布，不只是均值。
- Centile（percentile）：百分位。50th centile 就是中位数曲线。
- z-score：观测值离常模均值多少个标准差。
- Heteroskedastic：噪声方差随 x 变化。
- Basis function / B-spline：把 x 变换成一组特征，让线性模型能拟合曲线。
- Batch effect / site effect：不同实验室或数据集造成的系统性偏移。
- Partial pooling：层级模型里让各组估计向总体靠拢。
- BLR / HBR：Bayesian linear regression / hierarchical Bayesian regression。PCNtoolkit 的两个主力模型。BLR 快、有解析解；HBR 慢、能处理层级 batch effect。
- Warping：对 y 做非线性变换让它更接近高斯。
- MSLL / SMSE / EV：评估分布预测、均方误差、解释方差的指标。

## 参考材料（按优先级）

1. Rutherford et al. 2022, Nature Protocols, "The normative modeling framework for computational psychiatry"。最好读的入门，一步一步讲 PCNtoolkit 流程。只读 Introduction 和 Overview 部分。
2. PCNtoolkit 文档（pcntoolkit.readthedocs.io），看 BLR 和 HBR 的概念页面，不看 API。
3. Bethlehem et al. 2022, Nature, "Brain charts for the human lifespan"。只看 Figure 1，知道成品长什么样。
4. Marquand et al. 2016, Biological Psychiatry。normative modelling 的原始论文，有时间再看。
5. Fraza et al. 2021, NeuroImage, warped BLR。只看摘要，知道 warping 是干什么的。
6. Bayer et al. 2022, NeuroImage, HBR 处理 site effect。只看摘要。
