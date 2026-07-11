# McCarthy 2018 后续复现准备文档

更新时间：2026-07-09

本文档用于后续继续复现时快速接手当前状态。它以 2026-07-08 之后的 Route H 和 staged gate 产物为当前口径；早期报告包中关于 Fig. 3.16 / Fig. 3.17 卡在 10500 km 以下的描述，需要视为旧口径，后续汇报前应同步更新。

## 1. 当前总判断

当前项目已经完成一版可审计的 McCarthy 2018 拟周期轨道复现工程框架，并且 Chapter 3 quasi-DRO 的高振幅 source branch 已由 Route H 打通。

可以说：

- 已完成 54 张目标图的一版工程化覆盖。
- 已建立逐图状态表、审计 CSV、生成脚本和报告材料。
- Chapter 3 Fig. 3.16 / Fig. 3.17 的固定映射时间 quasi-DRO figure-source 门槛已通过 Route H。
- Chapter 4 和 Chapter 5 已有 Route H source-layer / BCR4BP / optimization 相关审计产物。

不能直接说：

- 已完全数值等价复现整篇 McCarthy 2018。
- 所有原论文图都已被 corrected numerical data 替换。
- Chapter 4 Fig. 4.3-4.8 的原始 L1 quasi-halo / quasi-vertical thesis-scale global manifolds 已完成替换。
- Chapter 5 的每张原始应用图都已完成高保真或优化等价复现。

## 2. 当前权威证据

以后判断当前状态时，优先读取以下文件：

| 用途 | 文件 |
| --- | --- |
| 全局 staged gate 当前口径 | `docs/mccarthy2018_staged_goal_gate_status.md` |
| 机器可读 gate 表 | `data/computed/mccarthy2018_staged_goal_gate_status.csv` |
| Chapter 3 frontier 决策 | `docs/chapter3_quasi_dro_frontier_decision.md` |
| Route H cache 审计 | `docs/chapter3_fixed_mapping_cache_audit.md` |
| Route H 接受分支 | `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv` |
| Route H 独立验证 | `data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv` |
| Chapter 4 Route H DG/manifold | `docs/chapter4_route_h_quasi_dro_dg_manifold_audit.md` |
| Chapter 4 逐图 source-layer 审计 | `docs/chapter4_per_figure_source_layer_audit.md` |
| Chapter 5 readiness | `docs/chapter5_high_fidelity_optimization_readiness_audit.md` |
| Chapter 5 Sun-Earth L1 long-propagation 逐图审计 | `docs/chapter5_sun_earth_l1_long_propagation_per_figure_audit.md` |
| Chapter 5 halo-Lyapunov 转移逐图审计 | `docs/chapter5_halo_lyapunov_transfer_per_figure_audit.md` |
| Chapter 5 NRHO corridor 逐图审计 | `docs/chapter5_nrho_corridor_per_figure_audit.md` |
| Chapter 5 NRHO 转移逐图审计 | `docs/chapter5_nrho_transfer_per_figure_audit.md` |
| Chapter 5 NRHO rendezvous 逐图审计 | `docs/chapter5_nrho_rendezvous_per_figure_audit.md` |
| Chapter 5 stable-manifold 逐图审计 | `docs/chapter5_stable_manifold_per_figure_audit.md` |
| Chapter 5 逐图 source-layer 审计 | `docs/chapter5_per_figure_source_layer_audit.md` |

如果 `chapter3_quasi_dro_frontier_decision.md` 和 staged gate 在 Chapter 4 / Chapter 5 状态上出现差异，以更新时间更晚的 `docs/mccarthy2018_staged_goal_gate_status.md` 和 `data/computed/mccarthy2018_staged_goal_gate_status.csv` 为准；frontier decision 主要用于 Chapter 3 Route A-H 的来龙去脉。

关键数值：

- Route H validation rows: 30
- Route H max `|z|`: `14573.10318409037 km`
- Route H rows `>= 10500 km`: 30
- Route H rows `>= 11000 km`: 29
- Route H max map residual: `6.469474407020314e-10`
- Route H max curve Jacobi span: `7.759926035078024e-11`
- Route H max one-map Jacobi drift: `7.760059261840979e-11`
- Fig. 3.10 period-q strict single-shoot accepted rows: 2 / 3
- Fig. 3.10 period-q local multiple-shooting accepted rows: 3 / 3
- Fig. 3.10 q=8 full-period single-shoot closure error: `3.906984451743337`
- Fig. 3.10 q=8 max monodromy multiplier magnitude: `3.431052642945378e+16`
- Fig. 5.1 Sun-Earth L1 long-propagation accepted rows: 5 / 5
- Fig. 5.1 propagation duration: `72.50168833048522 days`
- Fig. 5.1 max Jacobi span: `1.332267629550188e-15`
- Fig. 5.1 minimum transverse span: `0.002930000770814965`
- Fig. 5.8 halo-Lyapunov accepted rows: 1 / 1
- Fig. 5.8 total delta-v: `294.6245071767839 m/s`
- Fig. 5.8 endpoint error: `2.083434735432931e-06 km`
- Fig. 5.8 maximum continuity error: `9.280132972015876e-12`
- Fig. 5.8 Jacobi span: `2.472244631235299e-12`
- Fig. 5.9 NRHO corridor marker accepted rows: 2 / 2
- Fig. 5.9 best marker total delta-v: `47.73443414309953 m/s`
- Fig. 5.9 worst marker endpoint error: `2.336264914251333e-05 km`
- Fig. 5.9 max marker Jacobi span: `5.092193333666728e-11`
- Fig. 5.12 rendezvous accepted rows: 36 / 36
- Fig. 5.12 rendezvous coverage: `-24` to `11 h`
- Fig. 5.12 minimum delta-v difference: `-6.029648133534657 m/s`
- Fig. 5.12 maximum endpoint error: `3.714687617288433e-05 km`

当前逐图状态表 `data/computed/figure_validation_table.csv` 的分类统计为：

- `numerical reproduction`: 16
- `proxy/schematic only`: 13
- `shape-match with local numerical overlay`: 2
- `local corrected DG manifold source layer`: 2
- `Route H / DE421 geometry baseline`: 2
- `CR3BP endpoint-corrected NRHO transfer audit`: 2
- `corrected DG finite-amplitude manifold source layer`: 2
- `audited Route H fixed-time source-layer`: 2
- `physical-consistency baseline`: 2
- `shape-match with corrected DG numerical overlay`: 2
- `CR3BP stable-manifold LEO transfer audit`: 1
- `CR3BP stable-manifold periapsis audit`: 1
- `CR3BP fixed-departure rendezvous branch audit`: 1
- `corrected DG global manifold source layer with proxy comparison`: 1
- `corrected DG manifold source layer with proxy comparison`: 1
- `CR3BP corrected NRHO corridor marker audit`: 1
- `CR3BP endpoint-corrected halo-Lyapunov transfer audit`: 1
- `CR3BP Sun-Earth L1 long-propagation audit`: 1
- `period-q multiple-shooting audit with q8 boundary`: 1

Fig. 3.10 update note: the current status table now treats q=2/q=3 as strict
single-shoot accepted period-q rows and q=8 as a local multiple-shooting row
with an explicit single-shoot closure boundary. This is not a full original
branch equivalence claim.

Chapter 5 逐图 source-layer 审计表 `data/computed/chapter5_per_figure_source_layer_audit.csv` 的分类统计为：

- `proxy/schematic only`: 3
- `Route H / DE421 geometry baseline`: 2
- `CR3BP endpoint-corrected NRHO transfer audit`: 2
- `Route H / BCR4BP source-layer optimization audit`: 1
- `CR3BP stable-manifold LEO transfer audit`: 1
- `CR3BP stable-manifold periapsis audit`: 1
- `physical-consistency baseline`: 1
- `CR3BP Sun-Earth L1 long-propagation audit`: 1
- `CR3BP corrected NRHO corridor marker audit`: 1
- `CR3BP endpoint-corrected halo-Lyapunov transfer audit`: 1
- `CR3BP fixed-departure rendezvous branch audit`: 1

注意：Fig. 3.16 / Fig. 3.17 已同步为 Route H fixed-time source-layer。Chapter 4 和 Chapter 5 也已分别建立逐图 source-layer 审计表，但这仍不等于整篇论文 full numerical equivalence。

## 3. 当前成果地图

### Chapter 2

状态：基础 CR3BP 层较稳。

已完成内容：

- 平衡点、零速度曲线、线性模式、部分 Lyapunov / halo / NRHO 周期轨道族。
- 多数数值基础图可作为后续 Chapter 3-5 的可信底座。

后续重点：

- 只在需要精确对齐 McCarthy 原始分支幅值时继续补充。
- 不建议优先投入，除非后续报告要求更严格的原图逐像素或逐表格对照。

### Chapter 3

状态：核心进展已经从 bottleneck 诊断进入 Route H source promotion 阶段。

已完成内容：

- constant energy / constant frequency 的若干 corrected numerical families。
- Fig. 3.10 period-q halo 局部数值审计。
- Fig. 3.16 / Fig. 3.17 已在脚本中接入 Route H accepted family：
  - `figures/fig_3_16.py`
  - `figures/fig_3_17.py`
- Route H cache revalidation 已提供 10500 km 和 11000 km 以上的 accepted fixed-time quasi-DRO source branch。

仍需整理：

- 更新 `data/computed/figure_validation_table.csv` 中 Fig. 3.16 / Fig. 3.17 的旧 partial 描述。
- 更新旧报告包中关于 quasi-DRO 未过 10500 km 的文字。
- 对 Fig. 3.16 / Fig. 3.17 Route H 渲染图做一次视觉检查和报告截图归档。

仍未完全解决：

- Fig. 3.9 的 quasi-halo tail 仍有 proxy / tail 问题。
- Fig. 3.10 的 q=8 仍不能作为稳健 single-shoot full-period closure。
- Fig. 3.11 仍是 local numerical scene，不是原始 Poincare map 数据等价替换。
- Route A 原始 branch data / official code 仍未找到。

### Chapter 4

状态：Route H quasi-DRO source-layer DG/manifold 已通过，但这不是原论文 Fig. 4.3-4.8 的完整替换。

已完成内容：

- `data/computed/chapter4_route_h_quasi_dro_dg.csv`
- `data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv`
- `data/computed/chapter4_per_figure_source_layer_audit.csv`
- `docs/chapter4_per_figure_source_layer_audit.md`
- `outputs/figures_png/fig_4_route_h.png`
- `outputs/figures_pdf/fig_4_route_h.pdf`

后续需要先决策：

- 路线 4A：把 Route H quasi-DRO 作为新增 source-layer 图继续强化。
- 路线 4B：继续复现原论文 Fig. 4.3-4.8 对应的 L1 quasi-halo / quasi-vertical thesis-scale global manifolds。

不要把 4A 的通过结果直接写成 4B 已完成。

### Chapter 5

状态：已有 Route H / DE421 / BCR4BP / optimization source-layer 审计和图件，但仍需要按原始 thesis application figures 逐项对齐。

已完成或已有审计：

- `data/computed/chapter5_upstream_application_gate_audit.csv`
- `data/computed/chapter5_bcr4bp_dynamics_audit.csv`
- `data/computed/chapter5_bcr4bp_segment_correction_audit.csv`
- `data/computed/chapter5_optimized_transfer_audit.csv`
- `data/computed/chapter5_high_fidelity_optimization_readiness_audit.csv`
- `data/computed/chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv`
- `docs/chapter5_sun_earth_l1_long_propagation_per_figure_audit.md`
- `data/computed/chapter5_halo_lyapunov_transfer_per_figure_audit.csv`
- `docs/chapter5_halo_lyapunov_transfer_per_figure_audit.md`
- `data/computed/chapter5_nrho_corridor_per_figure_audit.csv`
- `docs/chapter5_nrho_corridor_per_figure_audit.md`
- `data/computed/chapter5_nrho_transfer_per_figure_audit.csv`
- `docs/chapter5_nrho_transfer_per_figure_audit.md`
- `data/computed/chapter5_nrho_rendezvous_per_figure_audit.csv`
- `docs/chapter5_nrho_rendezvous_per_figure_audit.md`
- `data/computed/chapter5_stable_manifold_per_figure_audit.csv`
- `docs/chapter5_stable_manifold_per_figure_audit.md`
- `data/computed/chapter5_per_figure_source_layer_audit.csv`
- `docs/chapter5_per_figure_source_layer_audit.md`
- `outputs/figures_png/fig_5_6.png`
- `outputs/figures_png/fig_5_7.png`
- `outputs/figures_png/fig_5_bcr4bp_optimized_transfer.png`

Fig. 5.1 当前已有 Sun-Earth L1 CR3BP long-propagation 逐图审计：

- accepted rows: 5 / 5
- duration: `72.50168833048522 days`
- max Jacobi span: `1.332267629550188e-15`
- minimum transverse span: `0.002930000770814965`
- max L1 distance: `605346.6174117256 km`

Fig. 5.8 当前已有 Earth-Moon CR3BP endpoint-corrected halo-Lyapunov transfer 逐图审计：

- accepted rows: 1 / 1
- total delta-v: `294.6245071767839 m/s`
- endpoint error: `2.083434735432931e-06 km`
- maximum continuity error: `9.280132972015876e-12`
- Jacobi span: `2.472244631235299e-12`
- boundary Jacobi difference: `0`

Fig. 5.9 当前已有 Earth-Moon CR3BP corrected NRHO boundary/departure-marker 逐图审计：

- accepted rows: 2 / 2
- best total delta-v: `47.73443414309953 m/s`
- worst endpoint error: `2.336264914251333e-05 km`
- max Jacobi span: `5.092193333666728e-11`
- perilune radii: `4800.000000000002 / 12610 km`

Fig. 5.10 / Fig. 5.11 当前已有 CR3BP endpoint-corrected transfer 逐图审计：

- accepted rows: 4 / 4
- best total delta-v: `47.73443414309953 m/s`
- worst endpoint error: `2.336264914251333e-05 km`
- max Jacobi span: `5.092193333666728e-11`

Fig. 5.12 当前已有 Earth-Moon CR3BP fixed-departure rendezvous arrival-offset branch 逐图审计：

- accepted rows: 36 / 36
- coverage: `-24` to `11 h`
- minimum delta-v difference: `-6.029648133534657 m/s`
- offset at minimum: `6 h`
- maximum endpoint error: `3.714687617288433e-05 km`

Fig. 5.13 / Fig. 5.14 当前已有 Sun-Earth CR3BP stable-manifold 逐图审计：

- accepted rows: 2 / 2
- selected phase: `14.88928693528482 deg`
- periapsis error: `0.0001116857147280825 km`
- transfer time: `407.6352466744673 days`
- Jacobi span: `3.126388037344441e-13`
- periodicity error: `4.66846168370424e-10`

后续重点：

- 对 Fig. 5.1，下一步是把当前 CR3BP center-mode propagation rows 升级为 corrected two-frequency Lissajous/quasi-periodic torus 或 BCR4BP/ephemeris evidence；当前 torus surface 仍是 proxy context。
- 对 Fig. 5.8，下一步是从 CR3BP endpoint-corrected halo-Lyapunov row 继续推进到 BCR4BP/ephemeris per-figure accepted row，或映射到 McCarthy 原始 transfer 初值数据。
- 对 Fig. 5.9，下一步是把当前 corrected-boundary marker rows 升级为 corrected quasi-NRHO torus/corridor 或 BCR4BP/ephemeris corridor；当前 grey corridor 仍不能算 thesis-equivalent torus。
- 对 Fig. 5.10 / Fig. 5.11，下一步是从 CR3BP endpoint-corrected rows 继续推进到 BCR4BP/ephemeris per-figure accepted rows。
- 对 Fig. 5.12，下一步是把当前 CR3BP local rendezvous branch 升级为 robust global quasi-NRHO continuation 或 BCR4BP/ephemeris branch；当前 grey proxy beyond fold 不能算 thesis-equivalent replacement。
- 对 Fig. 5.13 / Fig. 5.14，下一步是从 CR3BP periodic-orbit stable-manifold rows 继续推进到 quasi-periodic Lissajous-torus / ephemeris rows。
- 继续区分 DE421-oriented geometry baseline、BCR4BP dynamics audit、segment correction、optimized-transfer source-layer。
- 若要声称某张原图完成高保真复现，需要补齐对应 residual、endpoint、delta-v、Jacobi 或 ephemeris consistency 证据。

## 4. 需要同步的旧材料

以下文件包含旧口径或可能与 Route H 后状态不一致。后续汇报或提交报告前建议统一更新。

| 文件 | 问题 | 建议 |
| --- | --- | --- |
| `data/computed/figure_validation_table.csv` | Fig. 3.16 / Fig. 3.17 仍写未超过 10500 / 11000 km | 更新两行数据源、数值范围和 next_action |
| `docs/reproduction_report/teacher_package/README.md` | 仍说 Fig. 3.16 / Fig. 3.17 accepted branch 只到 10164 km | 改为 Route H 已过 source gate，同时保留 full-thesis 边界 |
| `docs/reproduction_report/teacher_package/key_results_table.md` | quasi-DRO endpoint 旧值 | 替换为 Route H source branch 指标 |
| `docs/reproduction_report/teacher_package/one_page_summary.md` | 仍以 bottleneck 为当前状态 | 改成 bottleneck 已由 Route H cache revalidation 解决，下一步是 source promotion 和旧材料同步 |
| `docs/reproduction_report/proxy_usage_appendix.md` | Fig. 3.16 / Fig. 3.17 proxy 描述偏旧 | 区分 grey proxy reference 和 Route H corrected overlay |
| `docs/reproduction_report/qa_for_group_meeting.md` | 问答仍以未过 10500 km 为核心结论 | 更新 Q2、Q8、Q9、Q13、Q18 等相关回答 |
| `README.md` | 多处历史状态混合 | 在顶部或状态段添加“当前以 staged gate 为准”的说明 |

上述旧材料同步项目前已由 `scripts/sync_route_h_report_status.py` 覆盖更新；后续如果重新生成旧报告或手工修改材料，应再次运行同步脚本和 staged gate 脚本。

## 5. 建议的下一步任务队列

### P0：统一当前口径（已完成，后续重生成材料时需复跑）

目标：避免后续继续复现时引用旧结论。

已完成任务：

1. 更新 `figure_validation_table.csv` 中 Fig. 3.16 / Fig. 3.17。
2. 更新 teacher package 和 reproduction report 中关于 quasi-DRO frontier 的旧段落。
3. 在 README 添加当前状态短注：Route H 已通过 Chapter 3 source gate，但整篇论文仍不是 full numerical equivalence。
4. 重新生成或至少校验 Fig. 3.16 / Fig. 3.17 PNG/PDF。

当前验收：

- 当前公开汇报材料不再以“accepted branch 只能到 10164 km，因此 Fig. 3.16 / 3.17 不能更新”为当前结论。
- 同时保留“不是整篇论文完全数值等价复现”的边界。

### P1：Fig. 3.16 / Fig. 3.17 Route H 图件提升（已完成，后续只需复核）

目标：把 Route H source branch 从数据通过推进到图件和说明闭环。

具体任务：

1. 运行 `figures/fig_3_16.py` 和 `figures/fig_3_17.py`。
2. 检查图中 corrected branch、grey proxy reference、rho range、amplitude range 的标注。
3. 更新 `docs/chapter3_quasi_dro_validation.md` 或新增 Route H figure note。
4. 对比 `outputs/reference_pages/fig_3_16_reference.png` 和 `outputs/reference_pages/fig_3_17_reference.png`，说明哪些差异来自原始数据不可得，哪些来自 Route H branch 本身。

验收：

- 图件存在且非空。
- 说明文档明确：Route H 是 accepted CR3BP fixed-time source branch；grey reference 不是原始数据。

### P2：Chapter 4 路线选择

目标：决定后续是扩展 Route H quasi-DRO source-layer，还是继续原论文 L1 quasi-halo / quasi-vertical global manifold replacement。

具体任务：

1. 写一页 Chapter 4 decision note。
2. 若选 Route H：继续完善 `fig_4_route_h` 的 DG spectra、local/global manifold probe 和可视化。
3. 若选原论文 replacement：回到 Fig. 4.3-4.8 的 source families，继续 thesis-scale dense global manifold sheets。

验收：

- 后续图件命名和报告表述不会把 Route H quasi-DRO 图误称为原论文 Fig. 4.3-4.8 完成替换。

### P3：Chapter 5 逐图验收表（已完成初版，后续推进 per-figure 高保真替换）

目标：把 high-fidelity / optimization source-layer 结果映射到原论文应用图。

已完成任务：

1. 对 Fig. 5.1-5.14 每张图添加 current source-layer status。
2. 区分 schematic、CR3BP baseline、DE421 baseline、BCR4BP dynamics、segment correction、optimized transfer。
3. 对需要 delta-v、endpoint、ephemeris correction 的图列出缺口。
4. 对 Fig. 5.1、Fig. 5.8、Fig. 5.9、Fig. 5.10、Fig. 5.11、Fig. 5.12、Fig. 5.13、Fig. 5.14 增加 per-figure accepted rows，并在 staged gate 中单列通过项。

当前验收：

- Chapter 5 不再只用一个总 gate 表示完成度，而是逐图说明能否替换原始图。

后续任务：

- 对 Fig. 5.1，将当前 CR3BP center-mode long-propagation rows 升级为 corrected two-frequency Lissajous/quasi-periodic torus 或 BCR4BP/ephemeris evidence。
- 对 Fig. 5.8，将当前 CR3BP endpoint-corrected halo-Lyapunov row 升级为 BCR4BP/ephemeris corrected row，或映射到 McCarthy 原始 transfer 初值数据。
- 对 Fig. 5.9，将当前 CR3BP corrected-boundary marker rows 升级为 corrected quasi-NRHO torus/corridor 或 BCR4BP/ephemeris corrected corridor。
- 对 Fig. 5.10 / Fig. 5.11，将当前 CR3BP endpoint-corrected rows 升级为 BCR4BP/ephemeris corrected rows。
- 对 Fig. 5.12，将当前 CR3BP local rendezvous branch 升级为 robust global quasi-NRHO continuation 或 BCR4BP/ephemeris corrected branch。
- 对 Fig. 5.13 / Fig. 5.14，将当前 CR3BP periodic-orbit stable-manifold rows 升级为 quasi-periodic Lissajous-torus 或 ephemeris corrected rows。

### P4：原始数据和外部对照

目标：继续降低“没有 McCarthy original branch data”的不确定性。

具体任务：

1. 继续维护 `docs/reproduction_report/original_data_search_log.md`。
2. 记录 negative evidence，而不是只记录找到的资源。
3. 若找到 branch data / appendix tables / author code，优先对 Fig. 3.16 / Fig. 3.17 和 Chapter 4 做对照。
4. 若仍找不到，保留 digitization 为 lower-authority reference。

验收：

- 每个外部来源都有日期、链接、搜索词、结论和是否可用于数值对照的判断。

## 6. 后续新结果的验收规则

以后新增 continuation、projection、BCR4BP、optimization 结果时，默认遵守这些规则：

- 区分 trial row、diagnostic row、accepted row、independently revalidated row。
- 不用 rejected candidate 更新论文图。
- 不用 digitized trend 当 raw branch data。
- 不用 grey proxy reference 当 corrected numerical data。
- 每个 accepted family 至少保留 CSV、Markdown audit、脚本入口和图件输出。
- 继续沿用 current seven-gate policy；如果修改门槛，必须在文档中说明新旧门槛差异。
- 对高振幅 quasi-DRO，10500 km 是最低 source gate，11000 km 是 stretch gate；Route H 当前已超过二者。
- 对 Chapter 4 / Chapter 5，必须说明 source-layer 通过和 original thesis figure replacement 的区别。

## 7. 常用验证命令

在 PowerShell 中优先使用显式解释器：

```powershell
$env:PYTHONPATH = "src"
D:\miniconda3\envs\cislunar\python.exe scripts\validate_basics.py
```

复核 Route H cache：

```powershell
$env:PYTHONPATH = "src"
D:\miniconda3\envs\cislunar\python.exe scripts\run_chapter3_fixed_mapping_cache_audit.py
```

复核 staged gate：

```powershell
$env:PYTHONPATH = "src"
D:\miniconda3\envs\cislunar\python.exe scripts\run_mccarthy2018_staged_goal_gate_audit.py
```

重生成 Fig. 3.16 / Fig. 3.17：

```powershell
$env:PYTHONPATH = "src;figures"
D:\miniconda3\envs\cislunar\python.exe figures\fig_3_16.py
D:\miniconda3\envs\cislunar\python.exe figures\fig_3_17.py
```

快速汇总当前状态：

```powershell
@'
import csv, pathlib
from collections import Counter
root = pathlib.Path.cwd()
with (root / "data/computed/figure_validation_table.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
print("figure_count", len(rows))
print(Counter(r["current_repro_level"] for r in rows))
with (root / "data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv").open(newline="", encoding="utf-8") as f:
    vals = list(csv.DictReader(f))
print("route_h_rows", len(vals))
print("route_h_max_z", max(float(r["max_abs_z_km"]) for r in vals))
print("route_h_max_residual", max(float(r["map_residual_norm"]) for r in vals))
print("route_h_max_jacobi_span", max(float(r["curve_jacobi_span"]) for r in vals))
'@ | D:\miniconda3\envs\cislunar\python.exe -
```

## 8. 给后续 Codex 的推荐起始提示

如果下一轮继续推进，建议直接从 P0 开始：

```text
请按 docs/continuation_reproduction_prep.md 的 P0 队列，更新 figure_validation_table.csv、teacher_package 和 README 中关于 Fig. 3.16/3.17 的旧口径。当前口径以 Route H 和 docs/mccarthy2018_staged_goal_gate_status.md 为准，但不要把整篇论文表述成 complete numerical reproduction。更新后运行最小汇总命令和相关图脚本验证。
```

如果导师要求继续数值突破，建议从 P2 或 P3 中选一个明确目标，而不是继续泛泛试 continuation。
