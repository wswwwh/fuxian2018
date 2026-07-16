# McCarthy 2018 复现基线 v1

> 由 scripts/run_reproduction_baseline_freeze.py 从当前 CSV/gate 和冻结证据生成。
> 文中的 S:metric_id 对应 data/computed/reproduction_baseline_v1_summary.csv；
> 输入文件哈希见 data/computed/reproduction_baseline_v1_manifest.csv。

## 冻结声明

**本基线用于支持后续原创方法研究，不代表 McCarthy 2018 全文严格数值等价复现。**

- 基线版本：v1 [S:baseline_version]
- 冻结日期：2026-07-15 [S:freeze_date]
- 源快照 Git commit：95a606ef75888fcef7f4d8cb2eedb120efc13b22 [S:source_git_commit]
- 当前 staged gate：chapter3_passed_chapter4_ready [S:staged_goal_status]

复现层从此作为可重运行、可审计的工程基线保留。后续研究代码可以复用 shared numerical library 和已登记 benchmark，但不得把研究结果自动回写为原论文图级 accepted，也不得改变冻结的 Chapter 4 v1 holdout。

## 54 图工程覆盖与保守分类

- 目标注册表：54/54 [S:target_rows]。
- V0：13 [S:v0_targets]；V2：41 [S:v2_targets]。
- 示意目标：13 [S:schematic_targets]；数值/应用目标：41 [S:numeric_application_targets]。
- 当前 exact label 为 numerical reproduction 的行：16 [S:numerical_reproduction_rows]。
- 非空 PNG/PDF：54/54 [S:png_count; S:pdf_count]；缺失证据路径行：0 [S:missing_artifact_rows]。

accepted/boundary/diagnostic/proxy 是 evidence-gap 保守分类，不等同于 V0/V2，也不等同于论文整体等价。

- **accepted (7)**: Fig. 2.15, Fig. 3.5, Fig. 3.6, Fig. 3.12, Fig. 3.13, Fig. 3.14, Fig. 3.15
- **boundary (30)**: Fig. 2.3, Fig. 2.4, Fig. 2.6, Fig. 2.7, Fig. 2.8, Fig. 2.11, Fig. 2.13, Fig. 2.14, Fig. 3.7, Fig. 3.8, Fig. 3.16, Fig. 4.1, Fig. 4.2, Fig. 4.3, Fig. 4.4, Fig. 4.5, Fig. 4.6, Fig. 4.7, Fig. 4.8, Fig. 5.1, Fig. 5.5, Fig. 5.6, Fig. 5.7, Fig. 5.8, Fig. 5.9, Fig. 5.10, Fig. 5.11, Fig. 5.12, Fig. 5.13, Fig. 5.14
- **diagnostic (5)**: Fig. 3.3, Fig. 3.9, Fig. 3.10, Fig. 3.11, Fig. 3.17
- **proxy (12)**: Fig. 2.1, Fig. 2.2, Fig. 2.5, Fig. 2.9, Fig. 2.10, Fig. 2.12, Fig. 3.1, Fig. 3.2, Fig. 3.4, Fig. 5.2, Fig. 5.3, Fig. 5.4

### 分章分类计数

| Chapter | accepted | boundary | diagnostic | proxy |
|---|---:|---:|---:|---:|
| 2 | 1 [S:chapter2_accepted] | 8 [S:chapter2_boundary] | 0 [S:chapter2_diagnostic] | 6 [S:chapter2_proxy] |
| 3 | 6 [S:chapter3_accepted] | 3 [S:chapter3_boundary] | 5 [S:chapter3_diagnostic] | 3 [S:chapter3_proxy] |
| 4 | 0 [S:chapter4_accepted] | 8 [S:chapter4_boundary] | 0 [S:chapter4_diagnostic] | 0 [S:chapter4_proxy] |
| 5 | 0 [S:chapter5_accepted] | 11 [S:chapter5_boundary] | 0 [S:chapter5_diagnostic] | 3 [S:chapter5_proxy] |

## 分章最强结果与边界

### Chapter 2

Chapter 2 已保存 CR3BP 基础、周期轨道、流形以及 L2 halo/NRHO 分支等工程化数值输出。Fig. 2.15 位于 accepted 分类；其余数值图仍按逐图 CSV 中的 physical-consistency 或 boundary 文案解释，V0 示意图不再作为主线升级任务。

### Chapter 3

- Route H accepted validation 有 30 行 [S:route_h_validation_rows]，最大 |z| 为 14573.103184 km [S:route_h_max_abs_z_km]。
- 四个论文报告精度 Jacobi 锚点为 4/4 [S:route_h_paper_precision_targets]；严格 fixed-time 行为 3/4 [S:route_h_strict_fixed_time_targets]。完整 monolithic cold-start 的失败仍保留，hybrid chain 为通过。
- Fig. 3.5、3.6、3.12–3.15 是当前 accepted 组；Fig. 3.10 的 q=8 仍是 single-shoot closure boundary；Fig. 3.17 的参考趋势仍是低权威 context。

### Chapter 4

- Fig. 4.1 的 reported-precision 通过行为 nu=1.383701611 [S:chapter4_fig41_stability_index]，但有限振幅 torus geometry 未证明。
- Fig. 4.2 在共同区间比较 13 点 [S:chapter4_fig42_overlap_rows]，覆盖率 89.026651% [S:chapter4_fig42_coverage_fraction]；fold 后仍缺 0.049450 day [S:chapter4_fig42_tail_gap_days]。
- Fig. 4.3–4.6 fixed-time state-space/local STM 与 configuration-reach 共 16/16 行通过 [S:chapter4_fixed_time_numerical_pass]；静态相机为 16/16 [S:chapter4_static_camera_pass]。
- 冻结 panel-(d) holdout 为 0/4 [S:chapter4_frozen_holdout_pass; S:chapter4_frozen_holdout_total]，paper_projection=fail 且 paper_3d=false；该结论不可被 post-hoc 结果覆盖。
- 12.40-day halo 候选当前仅是 post-hoc N=21 诊断 [S:chapter4_halo_candidate_samples]，T0=12.397983401715 day [S:chapter4_halo_candidate_period_days]，Ay=41820.698 km、Az=35772.490 km [S:chapter4_halo_candidate_ay_km; S:chapter4_halo_candidate_az_km]；阶段 B 的 N33/N45 重建尚未完成。
- Route H 近实双曲严格扫描仍仅 1/31 [S:route_h_real_hyperbolic_pass; S:route_h_real_hyperbolic_total]，阳性成员为 68 [S:route_h_real_positive_member]。复特征对不得伪装为一维实流形方向。

### Chapter 5

- Sun–Earth active-geometry checkpoint 为 member 468 [S:chapter5_active_member]，全环面 max|y|=659439.431 km、max|z|=939944.305 km [S:chapter5_active_max_y_km; S:chapter5_active_max_z_km]。
- 稳定流形近地点为 7034.029835 km [S:chapter5_stable_periapsis_km]；LEO 转移近地点为 7034.028971 km [S:chapter5_leo_periapsis_km]。这些是 CR3BP 应用门结果，不是完整 ephemeris/论文面板等价。
- Fig. 5.10 BCR4BP 数值扩展为 2/2 [S:chapter5_bcr4bp_numerical_pass]，论文等价为 0/2 [S:chapter5_bcr4bp_paper_equivalence_pass]。

## 明确失败、不可证明和冻结边界

- 整篇 McCarthy 2018 不是完整论文级数值等价复现。
- Chapter 4 v1 holdout 维持 paper_projection=fail、paper_3d=false；禁止按 panel (d) 回调 camera、epsilon、crop、renderer 或 threshold。
- Route H 大多数成员呈明显复方向；当前只能把 member 68 当近实双曲阳性控制，不能把 derived Route H 图称为原 Fig. 4.3–4.8 replacement。
- Fig. 4.2 fold-tail、Fig. 4.7–4.8 legacy projection semantics、Chapter 5 原始高保真状态/优化/逐点论文几何仍是 evidence boundary。
- 原作者未公开的 3D 状态、扰动设置或原始数据不能靠视觉相似补造。

## 进入原创研究时可引用的 benchmark 候选

- Earth–Moon L1 halo：12.397983-day N21 是阶段 B 固定起点；N33/N45 未完成前不得注册为收敛 benchmark。
- Earth–Moon L1 quasi-vertical：12.6647965-day N33 是固定起点；N45/N57 未完成前不得宣称 N 收敛。
- Route H quasi-DRO：member 68 是近实双曲阳性控制；member 17、32 是明显复方向负控制；最大振幅成员保留为复杂谱案例。
- Sun–Earth L1：accepted active-geometry member 468 可在阶段 C 注册，但必须引用保存 checkpoint，不重新盲目扩振幅。

## 从复现主线冻结的任务

- 不再以消灭全部 boundary 或 54 图逐像素等价作为当前主目标。
- 不继续无限扩展 Route B，不强行让 Chapter 4 holdout 通过，不追索不存在的原始作者数据。
- V0 示意图和已受控的低影响 boundary 仅保留维护与可重跑责任。
- 只有直接服务 invariant-bundle 方法验证的 Chapter 4 halo/vertical N 收敛与冻结负对照进入阶段 B。

## 权威读取顺序

1. data/computed/mccarthy2018_staged_goal_gate_status.csv 与 figure_validation_table.csv。
2. data/computed/figure_evidence_gap_audit.csv 及 Chapter 4/5 per-figure audit CSV/NPZ。
3. 本基线的 summary/manifest。
4. 生成的 Markdown rendering。
5. README、旧阶段报告和旧 roadmap 仅作导航或历史背景，禁止反向覆盖 CSV gate。

阶段 A 的结构与切换规则见 docs/repository_architecture.md 和 docs/research_transition_plan.md。阶段 B 未完成前，research/invariant_bundles 不得承载可发表结论。
