# Project Index

一句话状态：本项目已完成 McCarthy 2018 论文 54 张目标图的工程化覆盖并冻结 baseline v1；随后完成独立的 invariant-bundle research layer（15-case registry、45-row 方法对比、126-row 流形实验和方法型初稿），但该研究层不改变整篇非 complete numerical-equivalence、Chapter 4 冻结投影 holdout 0/4 的结论。

## Recommended Reading Path

1. `docs/reproduction_baseline_v1.md` - 当前冻结基线、强结果、负结果和不可证明边界。
2. `docs/repository_architecture.md` - reproduction/shared/research 三层职责与权威顺序。
3. `docs/research_transition_plan.md` - Stage A–F 完成状态、门槛与研究/复现隔离。
4. `research/invariant_bundles/benchmarks/benchmark_registry.csv`、`research/invariant_bundles/results/csv/method_comparison.csv` 和 `research/invariant_bundles/results/csv/manifold_convergence.csv` - research layer 权威源。
5. `research/invariant_bundles/paper/manuscript.md` 和 `claim_evidence_matrix.csv` - 方法型初稿及逐 claim 追溯。
6. `data/computed/mccarthy2018_staged_goal_gate_status.csv` 和 `data/computed/figure_validation_table.csv` - reproduction 当前数值状态权威源。
7. `README.md` - 项目总览、运行方式和主要输出；数字仍须回查 CSV。
8. `docs/reproduction_report/main_report.md` - 中文主报告，说明当前复现等级、核心证据和未完成边界。
9. `docs/reproduction_report/figure_status_appendix.md` - 54 张图逐图状态，是 `data/computed/figure_validation_table.csv` 的可读渲染。
10. `docs/reproduction_report/numerical_audit_appendix.md` - Fig. 3.10、Chapter 4 DG manifold、Chapter 3 quasi-DRO 的重点审计。
11. `docs/reproduction_report/proxy_usage_appendix.md` - 哪些图仍使用 proxy、schematic、local overlay 或 grey reference。
12. Route A search / digitization docs:
   - `docs/reproduction_report/original_data_search_log.md`
   - `docs/reproduction_report/digitization_method.md`
   - `docs/reproduction_report/fig_3_16_digitization_feasibility.md`
13. `docs/reproduction_report/presentation_outline.md` - 组会 / 开题 PPT 阅读路径。
14. `docs/reproduction_report/qa_for_group_meeting.md` - 汇报问答和保守表述边界。

## File Classes

| class | paths | purpose | can_modify_directly | usable_for_presentation |
|---|---|---|---|---|
| core code | `src/qp_orbits/`, `scripts/`, `figures/` | 动力学、轨道校正、绘图和批处理入口。 | reproduction 路径需经原审计；`src/qp_orbits/invariant_bundles.py` 属已立项 research 方法代码。 | 可用于解释工程结构，不直接作为结论证据。 |
| invariant-bundle research | `research/invariant_bundles/`, `src/qp_orbits/invariant_bundles.py` | benchmark、方法、结果、图和论文初稿。 | 只能写 research artifacts；禁止回写 canonical reproduction status。 | 可用于方法论文，必须同时展示 fail/boundary。 |
| computed data | `data/computed/` | 当前数值证据、审计表、分支数据和验证表。 | 不可直接手改；必须由脚本或明确审计流程生成。 | 可用于汇报，但要引用对应复现等级。 |
| digitized reference data | `data/digitized/` | Route A 下从参考图提取的低权威趋势和元数据。 | 不应混入 `data/computed/`；修改需保留校准和方法记录。 | 可用于说明 gap 和趋势对照，不能当 raw branch data。 |
| reproduction figures | `outputs/figures_png/`, `outputs/figures_pdf/` | 54 张复现图输出。 | 不直接手改；由 figure scripts 生成。 | 可用于展示当前图像覆盖和具体案例。 |
| diagnostic outputs | `outputs/diagnostics/`, `outputs/figure_qa/`, `outputs/comparison_contact_sheets/` | 对比图、诊断图、分章 montage、逐图 contact sheet。 | 不直接手改；可复制精选图到 presentation 目录。 | 适合展示审计、对比和缺口。 |
| report package | `docs/reproduction_report/` | Route C 报告包：主报告、附录、未来计划、搜索和 digitization 记录。 | 可修改文档层，但不能改写核心结论为更乐观版本。 | 是教师和组会展示的主要文本依据。 |
| presentation materials | `docs/reproduction_report/presentation_outline.md`, `docs/reproduction_report/qa_for_group_meeting.md`, `docs/reproduction_report/teacher_package/`, `outputs/presentation/` | 汇报顺序、问答、精选图和一页总结。 | 可整理和补充，但不得覆盖原始数据或原始图输出。 | 是直接面向老师 / 组会的材料层。 |
| future work docs | `docs/reproduction_execution_plan_2026-07-13.md`, `docs/reproduction_report/future_work_plan.md` | 当前分阶段计划、Route A / B / C 后续路线、成功标准和停止条件。`docs/next_reproduction_roadmap.md` 仅保留为 Route H 之前的历史快照。 | 可更新当前计划，不应把历史快照伪装为当前状态或已完成成果。 | 可用于讨论下一阶段研究任务。 |

## Canonical Sources of Truth

- 跨章 gate 的 canonical source of truth 是 `data/computed/mccarthy2018_staged_goal_gate_status.csv`。
- 逐图复现等级的 canonical source of truth 是 `data/computed/figure_validation_table.csv`。
- accepted / boundary / diagnostic / proxy 的保守分类来自 `data/computed/figure_evidence_gap_audit.csv`。
- baseline v1 的冻结数字和输入哈希来自 `data/computed/reproduction_baseline_v1_summary.csv` 与 `data/computed/reproduction_baseline_v1_manifest.csv`。
- invariant-bundle case 选择与 provenance 来自 `research/invariant_bundles/benchmarks/benchmark_registry.csv` 和 `benchmark_provenance.md`。
- bundle 方法结论来自 `research/invariant_bundles/results/csv/method_comparison.csv`；流形结论来自同目录 `manifold_convergence.csv`，图不是 acceptance authority。
- 方法论文中的数字必须能追溯到 `research/invariant_bundles/paper/claim_evidence_matrix.csv`。
- 54 图可读状态的 canonical report rendering 是 `docs/reproduction_report/figure_status_appendix.md`。
- Fig. 3.10、Chapter 4 DG manifold、Chapter 3 quasi-DRO bottleneck 的审计口径以 `docs/reproduction_report/numerical_audit_appendix.md` 和对应 `data/computed/*.csv` 为准。
- proxy / baseline / local overlay 边界以 `docs/reproduction_report/proxy_usage_appendix.md` 为准。
- Route A 原始数据搜索结论以 `docs/reproduction_report/original_data_search_log.md` 为准。
- Fig. 3.17 digitized trend 的低权威参考数据以 `data/digitized/` 与 `docs/reproduction_report/digitization_method.md` 为准。
- Fig. 3.16 digitization 不可行边界以 `docs/reproduction_report/fig_3_16_digitization_feasibility.md` 为准。

## Reporting Guardrails

- Fig. 3.16 / Fig. 3.17 的 source layer 使用 Route H，但不得升级为整篇论文级数值等价。
- Route H accepted validation 当前有 30 行，`max_abs_z = 14573.10318409037 km`；旧的约 10,164 km 叙述只属于 pre-Route-H 历史。
- Route H monolithic cold-start 的失败与 1/31 real-hyperbolic Chapter 4 边界必须继续保留。
- Route H member 68 的 frozen near-real 正控制使用 legacy seed-rho；physical corrected-rho 是独立 research case，当前为二维/失败，不得混写。
- digitized Fig. 3.17 trend 是 lower-authority reference，不是 raw branch data。
- Fig. 3.16 不能从静态 3D 图中精确 digitize。
- Chapter 5 当前仍应表述为 CR3BP baseline、DE421-oriented baseline、local direct-shooting baseline 或 proxy 层。
- 展示材料和核心复现数据分开：汇报用副本放在 `outputs/presentation/`，不要移动或手改 `data/computed/`、`figures/`、`src/`。
