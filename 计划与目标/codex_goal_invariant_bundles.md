# Codex 目标模式总目标：冻结 McCarthy 2018 复现基线，并建立拟周期轨道实不变子束与可靠流形计算研究体系

## 1. 总目标

将当前仓库从“持续追逐 McCarthy 2018 每张图的严格等价复现”转变为两个清晰、相互隔离但可以复用代码的层次：

1. **复现基线层**
   - 整理、审计并冻结现有 McCarthy 2018 复现成果；
   - 补齐与后续原创研究直接相关的关键未完成项；
   - 保留所有正结果、负结果、boundary 和不可证明边界；
   - 不再把 54 张图全部严格数值等价作为当前主目标。

2. **原创研究层**
   - 围绕拟周期轨道线性化 cocycle 的实稳定/不稳定不变子束提取、连续跟踪、收敛验证和全局流形可靠计算，建立独立研究模块；
   - 完成方法实现、基准数据、对比实验、收敛分析、论文图表和论文初稿；
   - 最终形成一篇可以作为硕士阶段发表论文基础的方法型研究工作。

你需要自主阅读项目、整理架构、实现算法、运行实验、诊断失败并迭代。不得为了“看起来成功”放宽既有门槛或隐藏负结果。

---

## 2. 当前事实基线

开始工作前，必须读取当前仓库权威文件，不能依赖旧报告中的过时结论：

- `data/reproduction_targets.csv`
- `data/computed/figure_validation_table.csv`
- `data/computed/figure_evidence_gap_audit.csv`
- `data/computed/mccarthy2018_staged_goal_gate_status.csv`
- `docs/mccarthy2018_staged_goal_gate_status.md`
- `docs/figure_evidence_gap_audit.md`
- `docs/reproduction_execution_plan_2026-07-13.md`
- `docs/chapter4_per_figure_source_layer_audit.md`
- `docs/chapter4_projection_failure_root_cause.md`
- `docs/chapter5_active_geometry_application_independent_rerun_audit.md`
- `README.md`

必须接受以下事实：

- 54/54 张图已有工程化输出；
- 54 张 PNG 和 54 张 PDF 均存在；
- 13 张是 V0 示意图；
- 41 张是数值或应用图；
- 当前约 16 张归类为 numerical reproduction；
- 其余图中大量已具有真实数值 source layer，但仍存在论文参数、完整分支、投影几何、高保真模型或原始数据不可得边界；
- Chapter 3 Route H 高振幅 fixed-time source branch 已打通；
- Fig. 3.16 四个 Jacobi 锚点已达到论文报告精度并完成独立重积分；
- Chapter 4 Fig. 4.1 的 `nu=1.3837` 目标已复现；
- Fig. 4.2 在共同区间的数字化逐点审计已通过，但仍缺 fold 后尾段；
- Fig. 4.3–4.6 的固定时刻全环面状态空间审计已通过，但冻结论文投影 holdout 为 0/4；
- Fig. 5.13/5.14 的两频环面、稳定流形、约 7033 km 近地点和 LEO 转移已通过 CR3BP 目标门及独立重跑；
- 整篇 McCarthy 2018 尚不是完整论文级数值等价复现。

---

## 3. 成功定义

本目标不要求消除全部 54 图的 boundary。

最终成功定义是：

> 在保留一个完整、可重运行、可审计的 McCarthy 2018 复现基线的同时，提出并实现一种可靠的拟周期轨道实不变子束计算方法，在多个轨道族和多个谱分辨率上证明其相较传统点式特征值选择方法更稳定、更连续或更可解释，并用该方法生成经过收敛审计的稳定/不稳定流形。

最终成果必须能够支持一篇方法型论文初稿。

---

## 4. 仓库架构目标

不要大规模移动现有文件，不要破坏已有脚本路径和报告链接。

在现有项目中新增独立研究层：

```text
mccarthy2018_reproduction/
├── src/
│   └── qp_orbits/
│       ├── ...existing modules...
│       └── invariant_bundles.py
│
├── scripts/
│   ├── ...existing reproduction scripts...
│   ├── run_reproduction_baseline_freeze.py
│   └── run_invariant_bundle_benchmarks.py
│
├── research/
│   └── invariant_bundles/
│       ├── README.md
│       ├── configs/
│       │   ├── benchmark_cases.yaml
│       │   └── method_options.yaml
│       ├── benchmarks/
│       │   ├── benchmark_registry.csv
│       │   └── benchmark_provenance.md
│       ├── experiments/
│       │   ├── baseline_eigendecomposition/
│       │   ├── real_schur_tracking/
│       │   ├── qr_bundle_iteration/
│       │   └── manifold_convergence/
│       ├── results/
│       │   ├── csv/
│       │   ├── npz/
│       │   └── logs/
│       ├── figures/
│       ├── tests/
│       └── paper/
│           ├── manuscript.md
│           ├── abstract.md
│           ├── contributions.md
│           ├── figure_plan.md
│           ├── tables.md
│           └── limitations.md
│
└── docs/
    ├── reproduction_baseline_v1.md
    ├── repository_architecture.md
    └── research_transition_plan.md
```

规则：

- 现有 `figures/fig_x_xx.py` 继续服务于复现基线；
- 原创算法不能只存在于 figure script 中；
- 研究原型先放在 `research/invariant_bundles/experiments/`；
- 稳定、通用、经过测试的算法再放入 `src/qp_orbits/invariant_bundles.py`；
- 不复制大型数据；研究 registry 应引用现有 authoritative CSV/NPZ；
- 所有研究结果必须带来源、参数和 Git commit 信息。

---

## 5. 阶段 A：整理和冻结复现基线

### A1. 建立复现基线总结

新增：

`docs/reproduction_baseline_v1.md`

必须总结：

- 54 图工程覆盖；
- 13 个 V0 和 41 个数值/应用目标；
- 当前 accepted、boundary、diagnostic、proxy 分类；
- Chapter 2、3、4、5 的最强结果；
- 当前明确失败或不可证明的部分；
- 哪些成果将作为原创研究的 benchmark；
- 哪些复现任务从此冻结，不再作为主线。

明确写出：

> 本基线用于支持后续原创方法研究，不代表 McCarthy 2018 全文严格数值等价复现。

### A2. 建立架构和文件地图

新增：

- `docs/repository_architecture.md`
- `docs/research_transition_plan.md`

要求：

- 解释 reproduction layer、shared numerical library 和 research layer 的职责；
- 列出关键 authoritative data；
- 标出 deprecated/legacy status 文件；
- 禁止后续直接从旧 Markdown 推断当前状态；
- 规定所有状态结论优先来自 CSV gate。

### A3. 环境和回归验证

检查并补齐：

- Python 和 Conda 环境说明；
- `skyfield`、SciPy、NumPy、Matplotlib 等真实依赖；
- 可复现环境文件或锁定文件；
- `PYTHONDONTWRITEBYTECODE=1`；
- 当前 unit tests；
- 54 图 smoke；
- target registry `--check`；
- `git diff --check`。

不得因为整理架构而破坏现有 54 图生成路径。

### A4. 不要求继续完成的内容

本阶段不要求：

- 把全部 25 个 boundary 图升级；
- 完成每张图的论文逐像素复现；
- 找回不存在的原始作者数据；
- 把全部 Chapter 5 任务推进到星历等价；
- 继续扩展 Route B；
- 强行让 Chapter 4 projection holdout 通过。

---

## 6. 阶段 B：补齐后续研究所必需的现有缺口

只处理直接服务于 invariant-bundle 论文的 Chapter 4 问题。

### B1. Halo 12.40-day source falsification

完成预先定义的：

`C4-HALO-12P40-SOURCE-FALSIFICATION`

固定候选：

- `JC = 3.1389`
- `T0 = 12.397983401715157 day`
- `N = 21`
- `Ay ≈ 41815 km`
- `Az ≈ 35783 km`

要求：

- 不使用 panel-(d) 重新选择成员；
- 不调整已锁定 camera、epsilon、crop 和 threshold；
- 重建同一物理成员的更高 N 版本；
- 至少尝试 N21、N33、N45；
- phase-align 特征方向；
- 比较 multiplier、principal angle、DG residual、3D manifold HD95 和 Jacobi drift。

输出：

- `data/computed/research_halo_12p40_resolution_audit.csv`
- `data/computed/research_halo_12p40_resolution_states.npz`
- `docs/research_halo_12p40_resolution_audit.md`

### B2. Quasi-vertical N 收敛

固定当前约 12.66-day quasi-vertical member。

至少比较：

- N33
- N45
- N57

记录：

- curve residual；
- Jacobi span；
- selected bundle dimension；
- multiplier；
- eigen/subspace residual；
- phase-aligned principal angle；
- full-sheet 3D convergence；
- Jacobi drift；
- runtime。

### B3. 冻结负对照

完成并记录：

- panel/time mapping；
- mask extraction；
- rasterizer；
- plotted-surface renderer；
- explicit STM transport 与现有 transport 语义。

这些负对照只用于定位问题，不得修改已经冻结的 v1 holdout 结论。

### B4. 阶段结论

必须形成一个明确判断：

- 失败主要来自 source member；
- 来自谱分辨率；
- 来自 pointwise eigenvector selection；
- 来自 renderer/projection semantics；
- 或论文原始 3D 状态和扰动设置不可得。

即使结论为负，也算完成，不得无限调参。

---

## 7. 阶段 C：建立研究 benchmark 数据集

新增：

`research/invariant_bundles/benchmarks/benchmark_registry.csv`

至少包含以下 benchmark：

### C1. Earth–Moon L1 quasi-halo

- 12.40-day halo N21/N33/N45；
- 至少一个较小振幅 halo；
- 当前旧 N9 member 作为低分辨率反例。

### C2. Earth–Moon L1 quasi-vertical

- 12.66-day N33/N45/N57。

### C3. Route H quasi-DRO

- member 68：近实双曲正控制；
- member 17、32：明显复方向负控制；
- 最大振幅成员：复杂谱案例；
- 可选加入 Fig. 3.16 N57/N81/N105 锚点。

### C4. Sun–Earth L1 two-frequency torus

- 当前 accepted active-geometry member 468；
- 至少一个较小振幅成员；
- 使用已保存 checkpoint，不重新盲目扩展振幅。

Registry 字段至少包括：

- `case_id`
- `family`
- `member_id`
- `system`
- `mu`
- `jacobi_or_energy`
- `mapping_time`
- `rho`
- `spectral_samples`
- `state_artifact`
- `source_residual`
- `expected_bundle_type`
- `positive_or_negative_control`
- `provenance`
- `git_commit`

---

## 8. 阶段 D：实现可靠实不变子束算法

### D1. 传统基线方法

保留传统点式方法作为 baseline：

- 对单个 DG 或离散 cocycle 矩阵直接 eigendecomposition；
- 按模长选择稳定/不稳定特征值；
- 相邻 phase 做简单符号对齐。

必须记录它在哪些 benchmark 上失败：

- 复特征值被误选；
- 相位不连续；
- 特征向量跳变；
- N 改变后方向不收敛；
- 生成流形几何不稳定。

### D2. 至少实现两种改进方法

至少实现下列两种；允许根据数值结果调整具体方案。

#### 方法一：real Schur / ordered Schur tracking

目标：

- 识别实一维不变方向或实二维不变子空间；
- 避免把明显复特征向量直接当作实流形方向；
- 做相邻 phase/subspace matching；
- 提供 Schur residual 和 principal-angle continuity。

#### 方法二：QR/SVD cocycle bundle iteration

目标：

- 沿 invariant curve 相位推进 cocycle；
- 使用 forward/backward QR、subspace iteration 或 SVD；
- 构造稳定/不稳定不变子束；
- 计算 bundle invariance residual；
- 区分一维实双曲方向与二维实共轭子空间。

可以增加：

- periodic QR；
- continuous orthogonalization；
- covariant Lyapunov vector iteration；
- cocycle reducibility correction；
- Fourier representation of invariant bundles。

但不得为了复杂而复杂。必须以可靠性、可验证性和论文可解释性为标准。

### D3. 数学要求

不要把 pointwise DG eigenvector 与 cocycle invariant bundle 混为一谈。

对一维 bundle，至少验证：

```text
A(theta) e(theta)
≈ lambda(theta) e(theta + rho)
```

对二维实子空间，至少验证：

```text
A(theta) E(theta)
≈ E(theta + rho) R(theta)
```

其中：

- `E(theta)` 为实正交基；
- `R(theta)` 为局部一维标量或二维小矩阵；
- 必须计算 invariance residual；
- 必须记录 bundle dimension；
- 若只能得到二维实子空间，不得伪称为一维实 stable/unstable direction。

---

## 9. 阶段 E：系统对比实验

新增总入口：

`scripts/run_invariant_bundle_benchmarks.py`

输出至少包括：

- `research/invariant_bundles/results/csv/method_comparison.csv`
- `research/invariant_bundles/results/csv/resolution_convergence.csv`
- `research/invariant_bundles/results/csv/phase_continuity.csv`
- `research/invariant_bundles/results/csv/manifold_convergence.csv`
- `research/invariant_bundles/results/csv/runtime_scaling.csv`
- 对应 NPZ。

每个 case、method 和 N 至少记录：

- bundle dimension；
- max/mean invariance residual；
- eigenpair or Schur residual；
- reciprocal-pair error；
- relative imaginary part；
- phase-to-phase principal angle；
- cross-resolution principal angle；
- multiplier/Lyapunov estimate；
- sign/subspace flips；
- manifold Jacobi drift；
- initial linear growth ratio；
- normalized 3D manifold distance；
- runtime；
- memory；
- accepted/boundary/fail；
- failure reason。

---

## 10. 阶段 F：流形验证

选择至少三个 benchmark 做流形实验：

1. 12.40-day quasi-halo；
2. 12.66-day quasi-vertical；
3. Sun–Earth active-geometry torus或 Route H member 68。

对每种方法生成稳定或不稳定流形，并比较：

- 相同 phase samples；
- 相同 perturbation norm；
- 相同传播时长；
- 相同积分器；
- 相同坐标系；
- 相同事件和停止条件。

重点比较：

- 传统 eigenselection；
- real Schur/subspace；
- QR/SVD invariant bundle。

验收指标：

- Jacobi drift；
- bundle invariance；
- 初始增长与理论倍率；
- N 收敛；
- perturbation sensitivity；
- full-sheet geometry convergence；
- branch sign consistency；
- 是否出现非物理复方向投影。

不得仅凭图像判断方法优劣。

---

## 11. 论文贡献目标

在：

`research/invariant_bundles/paper/contributions.md`

形成清楚的贡献候选。至少包括：

1. 揭示点式 DG 特征值选择在拟周期轨道流形构造中可能产生复方向误选和相位不连续；
2. 提出或系统实现一个实不变子束跟踪方法；
3. 建立 bundle residual、principal angle、cross-resolution convergence 和 manifold geometry convergence 审计体系；
4. 在多个 Earth–Moon 和 Sun–Earth 拟周期轨道族上进行验证；
5. 给出正控制、负控制和失败边界，而不是只展示成功案例。

只有实验结果支持时，才保留“提出新方法”的措辞。

若最终方法只是对已有 QR/Schur 方法进行工程化整合，则论文贡献应准确写成：

> 面向拟周期轨道 cocycle 与全局流形计算的可靠数值框架和系统比较。

不得虚构理论创新。

---

## 12. 论文初稿交付

新增：

`research/invariant_bundles/paper/manuscript.md`

结构至少包括：

1. Introduction
2. Problem formulation
3. Quasi-periodic orbit and cocycle model
4. Failure modes of pointwise eigenselection
5. Proposed invariant-bundle method
6. Numerical implementation
7. Benchmark families
8. Resolution and phase-continuity tests
9. Global manifold experiments
10. Computational cost
11. Discussion
12. Limitations
13. Conclusion

同时新增：

- `abstract.md`
- `figure_plan.md`
- `tables.md`
- `limitations.md`

论文图至少包括：

- 复特征值误选示例；
- phase continuity；
- N 收敛；
- principal-angle 对比；
- bundle invariance residual；
- manifold sheet 对比；
- 多 family 汇总；
- runtime/accuracy tradeoff。

不得使用未经核实的引用。所有外部文献必须保存完整题名、作者、年份、DOI或官方链接信息。

---

## 13. 测试要求

至少新增：

- `tests/test_invariant_bundle_residual.py`
- `tests/test_real_schur_selection.py`
- `tests/test_bundle_phase_alignment.py`
- `tests/test_bundle_resolution_convergence.py`
- `tests/test_complex_pair_subspace_handling.py`
- `tests/test_manifold_direction_consistency.py`
- research-specific regression tests。

测试必须覆盖：

- 明显实双曲正控制；
- 明显复特征负控制；
- 一维 bundle；
- 二维实不变子空间；
- sign flip；
- phase permutation；
- N refinement；
- stored benchmark reproducibility。

---

## 14. 保护规则

不得：

- 删除现有 reproduction artifacts；
- 重写 authoritative accepted CSV 而不经过 promotion audit；
- 把 research result 自动写入 original figure validation status；
- 修改冻结的 Chapter 4 v1 holdout；
- 根据已暴露 panel 重新调 camera、epsilon、crop 或 threshold；
- 把二维实子空间宣称为一维实特征方向；
- 把 Route H derived figure 宣称为原 Fig. 4.3–4.8 replacement；
- 继续无限追逐全部 54 图 V2；
- 隐藏 failed/boundary rows；
- 仅凭视觉相似升级科学结论；
- 将研究脚本继续堆入 figure scripts。

---

## 15. 停止和切换条件

每个实验 campaign 必须有：

- 最大 case 数；
- 最大谱分辨率；
- 最大迭代次数；
- 最大 wall-time；
- residual 趋势停止条件；
- checkpoint。

若某种方法在三个代表性 benchmark 上均不能改善：

- bundle residual；
- phase continuity；
- cross-resolution principal angle；
- manifold geometry convergence；

则停止该方法，保存负结果并转向另一种子空间方法。

若一维实 bundle 不存在，但二维实 invariant subspace 稳定存在，则接受二维结果，不得强行投影为一维。

若论文原始数据不可得导致投影等价不可证明，应保留为 evidence boundary，不得继续无边界调参。

---

## 16. 验证命令

完成阶段 A 后至少运行：

```powershell
python -m unittest discover -s tests -v
python scripts/build_reproduction_targets.py --check
python scripts/validate_reproduction_smoke.py
git diff --check
```

研究阶段至少运行：

```powershell
python -m unittest discover -s tests -v
python scripts/run_invariant_bundle_benchmarks.py
git diff --check
```

所有命令必须使用项目指定 Conda 环境，并设置：

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=src
```

---

## 17. 最终完成门槛

目标模式只有在以下条件全部满足后才可以标记完成。

### 复现基线

- `reproduction_baseline_v1.md` 完成；
- 当前权威状态和文件架构清晰；
- 54 图 smoke 通过；
- 环境和依赖可重建；
- Chapter 4 halo/vertical N 收敛和冻结负对照有明确结论；
- 不要求所有 boundary 消失。

### 研究代码

- 独立 `research/invariant_bundles/` 架构完成；
- benchmark registry 完成；
- 至少三类轨道族、至少六个 benchmark case；
- traditional baseline + 至少两种改进方法；
- 通用方法进入 `src/qp_orbits/invariant_bundles.py`；
- 单元测试通过。

### 数值实验

- 至少一个改进方法在多个 benchmark 上显示可重复优势；
- 至少三组流形实验；
- 有 phase continuity、N convergence、bundle residual 和 manifold convergence 证据；
- 正结果与负结果均保存。

### 论文材料

- manuscript 初稿完成；
- abstract、贡献、图表计划和限制说明完成；
- 主要论文图和表已生成；
- 论文结论不依赖完整复现 McCarthy 全部 54 图。

---

## 18. 最终回复格式

完成后必须报告：

1. 当前复现基线被如何冻结；
2. 哪些旧文件被索引或标为 legacy；
3. 哪些 Chapter 4 缺口被补齐；
4. 新增的研究目录结构；
5. benchmark family 和 case；
6. 实现的方法；
7. 哪种方法表现最好；
8. 哪些 case 仍失败；
9. 流形收敛结果；
10. 单元测试和 smoke 是否通过；
11. 论文初稿和图表是否生成；
12. 推荐的论文题目；
13. 下一步是补实验、写中文论文，还是准备 SCI 初稿。

最终结论必须明确区分：

- McCarthy 2018 复现基线；
- 本项目的数值方法研究；
- 可发表的原创贡献；
- 尚不能证明的论文等价边界。
