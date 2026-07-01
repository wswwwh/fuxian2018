# McCarthy 2018 论文级复现报告

## 摘要

本报告整理当前 McCarthy 2018 拟周期轨道复现项目的论文级材料。项目已经完成 54 张目标图的一版覆盖，并建立了逐图验证表、Fig. 3.10 period-q halo 审计、Chapter 4 DG manifold 审计，以及 Chapter 3 quasi-DRO validation、extension、PALC diagnostic 和 bottleneck diagnosis。当前结论应保持克制：项目已经形成可汇报的 reproduction package，但尚不能声称 complete McCarthy 2018 numerical reproduction。特别是 Fig. 3.16 和 Fig. 3.17 仍是 partial physical-consistency baseline，不是 full numerical reproduction；Chapter 5 仍应作为 baseline/proxy 层处理。

## 研究背景

McCarthy 2018 研究了 Sun-Earth 和 Earth-Moon 多体系统中的 quasi-periodic orbits，重点包括 CR3BP 中二维 invariant tori 的计算、continuation、stability characterization，以及 quasi-periodic trajectories 在任务设计中的应用。对于复现项目而言，难点不只是生成与论文相似的图像，还包括建立可审计的数值链条：周期轨道校正、Jacobi 常数、state transition matrix、stroboscopic map、invariant curve residual、DG eigenstructure、manifold propagation 和高保真应用层之间必须保持一致。

本项目当前选择先完成 Route C，即论文级复现报告包；Route A 可继续寻找 McCarthy 原始数据或 digitization 来源；Route B 的 quasi-DRO formulation replacement 暂不编码，除非报告阶段已经明确 residual equations、continuation variables、phase constraints 和 acceptance thresholds。

## McCarthy 2018 论文复现目标

复现目标分为三层。

第一层是基础 CR3BP 与周期轨道层。该层包括 normalized dynamics、Jacobi constant、zero-velocity curves、libration points、periodic orbit correction、monodromy matrix 和 stability indices。

第二层是 Chapter 3 和 Chapter 4 的 quasi-periodic orbit 核心层。该层包括 stroboscopic invariant curve correction、constant energy / constant frequency / constant mapping time families、period-q resonance examples、quasi-DRO families、DG stability 和 torus manifold propagation。

第三层是 Chapter 5 应用层。该层包括 quasi-DRO resonance、line-of-sight / eclipse geometry、Earth-Moon / Sun-Earth transfer baselines、BCR4BP 或 ephemeris-oriented scenes。由于该层依赖前两层的可靠 branch data，当前不应在 quasi-DRO branch 尚未通过高幅值审计时进行数值升级。

## 当前 54 图复现覆盖情况

当前逐图状态来自 `data/computed/figure_validation_table.csv`，并已整理为 `docs/reproduction_report/figure_status_appendix.md`。54 张图的当前分类为：

| current_repro_level | count |
|---|---:|
| numerical reproduction | 16 |
| physical-consistency baseline | 6 |
| physical-consistency baseline (partial) | 2 |
| proxy/schematic only | 13 |
| shape-match with local numerical overlay | 17 |

这说明项目已完成图级覆盖，但覆盖质量并不均匀。numerical reproduction 类图可以作为较强复现证据；physical-consistency baseline 类图支持物理机制与局部数值链条；shape-match with local numerical overlay 类图包含局部可审计数值但仍依赖 proxy 或 thesis-scale reference；proxy/schematic only 类图只承担概念、结构或视觉占位功能。

## 数值审计体系设计

本项目采用逐图分级审计，而不是只按图像相似度判断是否复现。核心审计指标包括：

- residual evidence：周期轨道 closure、invariant curve map residual、multiple-shooting patch residual、BVP 或 correction residual。
- Jacobi evidence：Jacobi drift、curve Jacobi span、one-map sweep Jacobi drift、long-return Jacobi span。
- periodicity evidence：periodicity error、trajectory closure、single-shoot vs multiple-shoot consistency。
- stability evidence：monodromy multipliers、DG eigenvalues、growth ratio、stability index。
- proxy evidence：是否使用 proxy/schematic/local overlay/grey reference，以及 proxy 的功能边界。

这种体系的目标是避免把视觉上相似的图误判为完全数值复现。当前最重要的负面证据也被保留下来：例如 q=8 halo 的 single-shoot closure 失败、quasi-DRO 11,000 km 附近 residual/Jacobi audit 失败，以及 Chapter 4 global manifold sheet 仍保留 proxy reference。

## Fig. 3.10 period-q halo 审计

Fig. 3.10 当前仍是 shape-match with local numerical overlay。项目已为 q=2、q=3 和 q=8 period-q halo examples 建立了 `data/computed/period_q_halo_examples.csv`、`data/computed/period_q_halo_examples.npz` 和 `data/computed/period_q_halo_closure_audit.csv`。

q=2 与 q=3 的 resonance angle error、multiple-shooting residual、Jacobi drift 和 closure 指标支持局部数值近似。q=8 的 patch-to-patch continuity residual 和 terminal symmetry residual 可达到 roundoff 量级，但 full-period single integration closure error 为 `3.906984451743337`，且 max monodromy multiplier magnitude 为 `3.431052642945378e+16`。因此 q=8 只能称为 unstable multiple-shooting local approximation，不能称为 robust single-shoot periodic orbit。

## Chapter 4 DG manifold 审计

Chapter 4 已建立 `data/computed/chapter4_manifold_validation.csv` 和 `docs/chapter4_manifold_validation.md`。Figures 4.3-4.8 均记录 source-curve residual、DG mapping time、rotation angle、selected unstable multiplier、perturbation scale、growth ratio、Jacobi drift 和 terminal bounds。

当前 Chapter 4 corrected DG sheets 可作为 physical-consistency baseline。其理由是：局部 source curves 和 DG eigenvector propagation 有可审计数值证据，Jacobi drift 保持较小，quasi-vertical local branches 的 growth ratio 接近线性 DG 预测。但是这些图仍保留 proxy thesis-scale backgrounds 或 grey reference，且没有完成 thesis-scale continued torus family 上的 dense global manifold sheet。因此不能声称 Chapter 4 已达到 full thesis-level numerical reproduction。

## Chapter 3 quasi-DRO continuation 与 bottleneck 诊断

Chapter 3 quasi-DRO 是当前复现项目的主要瓶颈。已完成的工作包括：

- 原始 local branch validation。
- fixed-mapping-time extension。
- PALC diagnostic。
- `N=61` spectral lift。
- fixed-rotation fallback candidates。
- fixed-mean-Jacobi/free-rho/free-time local experiment。
- bottleneck diagnostics 与 experiments tables。

当前 accepted branch 最大只到 `max_abs_z = 10164.02309965055 km`，对应 rho 约 `1.443877875293695 rad`。没有 accepted member 超过 10,500 km 或 11,000 km。`N=61` 可降低 Fourier tail energy，但不能把 accepted branch 推过 10,164 km。fixed-rotation candidates 能生成超过 11,000 km 的高幅值候选，例如 rho 1.4465 附近达到 `max_abs_z = 11188.08244697768 km`，但 residual 为 `7.841846983001098e-02`，Jacobi span 为 `1.814140488309413e-03`，因此审计失败。

当前最可信解释是 fixed-mapping-time formulation 在 rho 约 `1.44388` 附近存在局部参数化或 Newton basin failure，而不是单纯谱阶不足。Fig. 3.16 和 Fig. 3.17 因此必须保持 partial physical-consistency baseline 标签，不能升级为 full numerical reproduction。

## Chapter 5 当前为什么只能作为 baseline/proxy 层

Chapter 5 的 quasi-DRO 应用依赖可靠的 Chapter 3 quasi-DRO branch。如果 Chapter 3 accepted branch 尚未通过 10,500 km 或 11,000 km，直接升级 Chapter 5 会把 rejected candidate 或 proxy trend 传递到 ephemeris/BCR4BP 应用层，导致 line-of-sight、eclipse avoidance、transfer initial guess 等结论缺少可靠 CR3BP 基线。

因此当前 Chapter 5 应保持为 baseline/proxy 层：部分图是 CR3BP baseline，部分图是 DE421-oriented baseline，部分图是 local direct-shooting baseline，部分图是 geometric proxy 或 proxy corridor。它们可用于报告应用方向和当前实现能力，但不能声称为完整 BCR4BP 或 optimized transfer reproduction。

## 外部资源与原始数据缺口

外部资源已整理在 `docs/external_reproduction_resources.md`。最有价值的资源包括 McCarthy 2018 Purdue Hammer thesis record、local PDF、Olikara and Howell 2010、Tor/COCO、JPL Three-Body Periodic Orbits API、NAIF SPICE / generic kernels，以及 McCarthy and Howell 2019/2021 相关应用论文。

当前最大原始数据缺口是：尚未找到 McCarthy 2018 的公开 branch data、initial states、appendix tables、official code repository 或 thesis-specific supplementary material。JPL periodic orbits API 可验证 periodic orbit baseline，但不提供 McCarthy quasi-periodic torus branch。外部资源搜索应继续作为 Route A，但报告不能假设原始数据存在。

## 下一阶段路线：Route A / Route B / Route C

Route A 是 McCarthy 原始数据 / digitization 路线。目标是继续寻找 original branch data、initial states、tables、high-resolution figures、appendices 或作者公开材料；如果找不到，则对关键图进行可追溯 digitization。

Route B 是 quasi-DRO formulation replacement 路线。目标是从当前 fixed-mapping invariant-curve correction 转向 Fourier/collocation torus BVP、COCO/Tor 风格 continuation，或其他能处理 fold/parameterization failure 的 formulation。该路线暂不编码，除非先完成 residual equations、continuation variables、phase constraints 和 acceptance thresholds 的定义。

Route C 是论文级复现报告完善路线。目标是把当前 54 图覆盖、审计证据、proxy 使用边界、外部资源缺口和下一阶段计划整理成可用于组会、开题或投稿准备的报告包。本轮执行的正是 Route C。

## 结论

当前项目已经从“能否生成 54 张图”推进到“能否为每张图建立复现等级和数值证据”的阶段。已有 16 张图可归为 numerical reproduction，6 张图为 physical-consistency baseline，2 张 quasi-DRO 核心图为 partial physical-consistency baseline，17 张图为 shape-match with local numerical overlay，13 张图为 proxy/schematic only。

最主要未完成缺口是 McCarthy 原始数据缺失、quasi-DRO branch 未通过 10,500/11,000 km 审计、Chapter 4 thesis-scale global manifold sheets 未完全复现，以及 Chapter 5 仍未进入可靠 BCR4BP/ephemeris optimized transfer 层。下一轮建议继续完善 Route C 报告材料，同时以 Route A 有边界地寻找原始数据；Route B 应作为后续算法研究任务单独立项。
## Route A search and digitization update

The 2026-07-01 bounded Route A search checked the Purdue Hammer/Figshare thesis
record, Purdue/Howell publication routes, the local McCarthy 2018 PDF,
McCarthy and Howell 2019/2021/2022 related papers, Olikara method sources, the
JPL periodic-orbits API, and required GitHub API queries. It did not find
McCarthy original quasi-DRO branch data, initial states, appendix tables,
thesis-specific supplementary files, or official code. The strongest negative
evidence is the Hammer/Figshare API metadata: only `thesisMcCarthySubmit.pdf`
is attached.

Fig. 3.17 has now been digitized as a lower-authority reference trend from
`outputs/reference_pages/fig_3_17_reference.png`. The digitized trend covers
about rho `1.436..1.508 rad` in the z-amplitude panel and reaches about
`30714.3 km`. The accepted corrected branch covers only rho
`1.431231722670483..1.443877875293695 rad` and reaches
`max_abs_z = 10164.02309965055 km`. At the accepted endpoint, the digitized
reference trend is about `13204.1 km`, roughly `3040.1 km` above the corrected
branch. Points beyond the accepted rho range are marked outside range and are
not matched by extrapolation.

Fig. 3.16 is documented only through feasibility and annotations. Its static 3D
surface rendering cannot be inverted into precise 3D coordinates without raw
branch data, camera/projection metadata, or a new accepted numerical branch.
Therefore digitized Fig. 3.17 and annotated Fig. 3.16 support audit and gap
documentation only; they do not upgrade Fig. 3.16/Fig. 3.17 to full numerical
reproduction.
