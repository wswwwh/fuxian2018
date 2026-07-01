# McCarthy 2018 论文复现阶段性研究报告

本文档面向导师、组会或开题报告，概括当前 McCarthy 2018 复现项目的完成度、数值证据、主要缺口和下一阶段路线。本文不推进新的 continuation 算法，不修改 Fig. 3.10，不继续 Chapter 4，也不进入 Chapter 5 数值升级。

## 1. 论文复现目标

本项目目标是复现 McCarthy 2018 关于 Sun-Earth 和 Earth-Moon 系统中拟周期轨道的主要数值图像与算法链条。核心内容包括：

- CR3BP 基础量、周期轨道、单/多重 shooting 校正和周期轨道稳定性。
- 基于 stroboscopic map 的二维 invariant torus / quasi-periodic orbit 计算。
- constant energy、constant frequency ratio、constant mapping time 三类 QPO family。
- 基于离散 invariant curve 微分 `DG` 的 torus stability 和 manifold 结构。
- quasi-DRO 在 Earth-Moon / Sun-Earth-Moon 应用场景中的几何与转移设计价值。

复现目标不是只生成相似图片，而是尽量建立可审计的数值链条：输入、状态量、Jacobi 常数、残差、传播一致性、稳定性指标和图像输出应能相互追踪。

## 2. 当前项目完成情况

当前项目已经完成第一版 54 张图覆盖，包含 Chapter 2、Chapter 3、Chapter 4 和 Chapter 5 的全部目标图脚本。总体状态记录在：

- `data/computed/figure_validation_table.csv`
- `docs/figure_consistency_review.md`
- `docs/chapter3_quasi_dro_validation.md`
- `docs/chapter4_manifold_validation.md`
- `docs/fig_3_10_validation.md`
- `docs/fig_3_10_q8_failure_analysis.md`

目前可分为四类：

- numerical reproduction：已有较强数值链条和物理量审计。
- physical-consistency baseline：物理机制和局部数值链条成立，但不是论文原始数值等价。
- shape-match with local numerical overlay：图形结构可对照，局部数值覆盖存在，但仍保留 proxy 或局部化假设。
- proxy/schematic only：用于版面、概念或物理趋势占位，不应声称为完整复现。

重要结论是：本项目已经完成“可汇报的一版覆盖”，但还没有达到“所有关键图完全数值等价”的程度。

## 3. 按章节总结复现状态

Chapter 2 主要是 CR3BP 基础、Lagrange 点、零速度曲线、周期轨道、monodromy 和稳定性。多数图已经达到 numerical reproduction 或可审计物理一致性水平。周期轨道相关脚本可作为 Chapter 3 quasi-periodic orbit 的基础。

Chapter 3 是当前最大难点。多数 constant energy / constant frequency / stroboscopic torus 图已有本地数值实现或局部 overlay。Fig. 3.10 已完成 period-q halo 审计，但仍是 shape-match with local numerical overlay。Fig. 3.16 和 Fig. 3.17 是 quasi-DRO constant mapping time family 的核心图，目前只能定位为 partial physical-consistency baseline，不是 full numerical reproduction。

Chapter 4 已增加 DG manifold audit。Figures 4.3-4.8 具有 source-curve residual、DG mapping time、rotation angle、unstable multiplier、perturbation scale、Jacobi drift、growth ratio 和 terminal bounds 等审计量。但当前仍保留 proxy thesis-scale backgrounds，尚未复现 thesis-scale dense global manifold sheets。

Chapter 5 当前是应用场景 baseline，不是完整 BCR4BP 或 ephemeris multiple-shooting 复现。已有 DE421-oriented baseline、CR3BP quasi-DRO return baseline、local transfer/proxy figures，但其可信度受 Chapter 3 quasi-DRO branch 覆盖范围限制。

## 4. Fig. 3.10 period-q 审计结果

Fig. 3.10 当前定位为 shape-match with local numerical overlay。项目已经对 q=2、q=3、q=8 period-q halo examples 建立了 CSV 审计：

- 数据源包括 `data/computed/period_q_halo_examples.csv` 和 q8 audit CSV。
- q=2 和 q=3 的局部 period-q 行为具有较好的 closure / Jacobi 一致性。
- q=8 保留为不稳定 multiple-shooting overlay，single-shoot closure 尚不够稳健。

因此 Fig. 3.10 可用于展示 period-q halo 的局部数值覆盖，但不应描述为已经完全匹配 McCarthy 原图的所有几何尺度、视角和原始 branch 选择。本轮不继续修改 Fig. 3.10。

## 5. Chapter 4 DG manifold 审计结果

Chapter 4 新增 `data/computed/chapter4_manifold_validation.csv` 和说明文档 `docs/chapter4_manifold_validation.md`。审计覆盖 Figures 4.3-4.8，记录 corrected DG manifold diagnostics。

当前结论：

- Figures 4.1-4.2 仍是 stability-shape figures，带有 corrected local DG samples。
- Figures 4.3-4.6 保留 proxy manifold backgrounds，同时叠加经审计的 corrected DG eigenvector propagation。
- Figures 4.7-4.8 以 corrected DG propagation 作为主要 red sheet，但仍保留 grey proxy reference。
- quasi-vertical local branches 在一映射时间内的 DG growth 与线性预测符合较好。
- quasi-halo finite-amplitude branches 具有物理一致性，但有限扰动和非线性传播使其不是严格 infinitesimal DG 等价。
- Fig. 4.8 是更长时间 global propagation，Jacobi drift 小，但增长比相对线性 DG 预测明显下降，可解释为非线性饱和和投影效应。

因此 Chapter 4 当前可作为 local/finite-amplitude DG physical-consistency baseline，而不是 thesis-level dense global manifold reproduction。本轮不继续 Chapter 4。

## 6. Chapter 3 quasi-DRO extension 与 bottleneck 诊断

Chapter 3 quasi-DRO 是当前复现瓶颈。项目已经完成：

- 原始五个 `N=21` local branch members 的保留。
- `N=41` fixed-mapping-time extension，接受到 10,000 km vertical amplitude target。
- bounded fixed-mapping pseudo-arclength diagnostic。
- `N=61` spectral lift diagnostic。
- fixed-rotation fallback candidates。
- fixed-mean-Jacobi/free-rho/free-time local correction experiment。
- bottleneck diagnostics table 和 experiments table。

当前 accepted branch 的最大值为：

- rho 最大约 `1.443877875293695 rad`。
- `max_abs_z = 10164.02309965055 km`。
- 没有 accepted member 超过 10,500 km 或 11,000 km。

关键数值证据：

- accepted 10,000 km member 的 pointwise map residual 为 `4.147166287852223e-14`，Jacobi span 为 `1.615654277031808e-10`。
- accepted `N=61` PALC member 的 pointwise map residual 为 `7.890714644108212e-10`，Jacobi span 为 `1.794120407794253e-11`，state Fourier tail ratio 为 `1.80077333522803e-17`。
- `N=61` 降低 Fourier tail，但 accepted branch 只推进到 10,164.02309965055 km。
- 11,000 km amplitude-stepping candidate 的 residual 为 `4.227040797634044e-04`，Jacobi span 为 `1.95390551757324e-04`。
- fixed-rotation candidate 可达到 `max_abs_z = 11188.08244697768 km`，但 residual 为 `7.841846983001098e-02`，Jacobi span 为 `1.814140488309413e-03`，不能接受。
- fixed-mean-Jacobi/free-rho/free-time experiment 最好只到约 `10210.30431232785 km`，仍未通过 residual/Jacobi audit。

当前最可信的解释是：瓶颈不是单纯谱阶不足，而是 fixed-mapping-time formulation 在 rho 约 `1.44388` 附近出现局部参数化或 Newton basin failure，可能接近 branch fold 或 remote branch attraction。Fig. 3.16 和 Fig. 3.17 因此必须保持 partial physical-consistency baseline 标签。

## 7. 当前最主要缺口

当前缺口按优先级排序如下：

1. McCarthy 原始 quasi-DRO branch data、initial states、tables 或可数字化高质量图源尚未找到。
2. Fixed-mapping-time quasi-DRO branch 无 accepted member 超过 10,500 km 或 11,000 km，无法覆盖 thesis-scale high-amplitude trend。
3. Fig. 3.16 / Fig. 3.17 的 grey proxy surfaces/trends 仍是参考几何，不是 corrected numerical reproduction。
4. Chapter 4 尚未完成 thesis-scale high-amplitude torus family 上的 dense global manifold sheets。
5. Chapter 5 仍缺少以可靠 quasi-DRO branch 为输入的 BCR4BP / ephemeris-corrected multiple shooting。
6. 全项目虽然已有 54 图覆盖，但不同图的复现等级差异较大，需要在论文/报告中明确分类，避免过度声明。

## 8. 为什么不能直接进入 Chapter 5

Chapter 5 的 quasi-DRO 应用依赖 Chapter 3 的 quasi-DRO family 作为输入。如果当前 branch 只能 accepted 到约 10,164 km，并且无法通过 10,500 km 或 11,000 km 审计，那么直接升级 Chapter 5 会产生三个风险：

1. 应用轨道的三维几何可能来自 rejected candidate 或 proxy trend，而不是可靠 invariant torus member。
2. BCR4BP / ephemeris 模型会引入更多自由度和误差源，掩盖 Chapter 3 formulation 本身的失败。
3. 后续 line-of-sight、eclipse avoidance、transfer initial guess 等结论会缺少可追溯的 CR3BP baseline。

因此当前应先补强外部资源、确认是否存在原始数据、并选择下一阶段算法路线，而不是直接进入 Chapter 5 数值升级。

## 9. 下一阶段外部资源和算法路线

下一阶段建议并行保留三条路线，但短期优先级不同：

路线 A：继续追 McCarthy 原论文数据。重点寻找 Purdue/Hammer 附件、Howell 小组材料、AAS paper、图像 digitization、可能的 supplementary data、作者公开代码或第三方复现。此路线成本低，若找到原始 branch data，对 Fig. 3.10、Fig. 3.16/3.17 和 Chapter 4 对照最直接。

路线 B：替换 quasi-DRO continuation formulation。参考 Olikara/Howell invariant curve method、Schilder/Osinga/Vogt torus continuation、Tor/COCO Fourier-collocation BVP、Baresi/Scheeres method comparison。目标是从 fixed-mapping invariant curve local correction 转向更稳健的 torus BVP 或 COCO/Tor 风格 continuation，用于处理 10,000-11,000 km 附近的 fold/parameterization failure。

路线 C：先完成论文级复现报告。基于 `figure_validation_table.csv` 将每张图分类为 numerical reproduction、physical-consistency baseline、local overlay 或 proxy，并形成可答辩的阶段性成果。这条路线最适合硕士开题、组会汇报或小论文准备，但不能声称完全复现 McCarthy 2018。

短期建议：优先执行路线 C，同时用路线 A 搜索原始数据；路线 B 作为后续实质算法研究题目立项，而不是本轮继续试错。

## 10. 可作为硕士研究方向的技术问题

以下问题可以形成后续研究方向：

1. Fixed-mapping-time quasi-DRO family 在 rho 约 `1.44388` 附近的局部失效机制：是 fold、参数化退化、Newton basin 切换，还是远端 branch attraction？
2. Fourier/collocation torus BVP 是否能比 stroboscopic invariant curve shooting 更稳定地穿越 10,000-11,000 km 区间？
3. Constant mapping time、fixed rotation、fixed energy / fixed Jacobi continuation 在 quasi-DRO family 上的适用边界如何比较？
4. 如何为 quasi-periodic invariant torus 建立自动化 residual、Jacobi、phase、Fourier tail 和 singular-value 诊断体系？
5. DG manifold 的局部 eigenvector propagation 如何扩展为 thesis-scale dense global manifold sheet？
6. 从 CR3BP quasi-DRO 到 BCR4BP / ephemeris model 的过渡应采用何种 continuation 和 multiple shooting 框架？
7. 对论文复现项目，如何定义“完全数值复现”“物理一致性复现”“局部 overlay”和“proxy”的可审计边界？

阶段性结论：当前项目已具备较完整的复现覆盖和审计框架，主要科学问题已经从“能否画出图”转变为“如何获得可接受的 high-amplitude quasi-DRO invariant torus family”。在没有原始 branch data 的情况下，下一阶段应先把复现等级报告做扎实，再决定是否投入 formulation replacement。
