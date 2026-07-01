# Project Index

一句话状态：本项目已完成 McCarthy 2018 论文 54 张目标图的一版工程化覆盖和可审计报告包，但仍不是 complete McCarthy 2018 numerical reproduction；Fig. 3.16 / Fig. 3.17 仍是 partial physical-consistency baseline。

## Recommended Reading Path

1. `README.md` - 项目总览、当前数值状态、运行方式和主要输出。
2. `docs/reproduction_report/main_report.md` - 中文主报告，说明当前复现等级、核心证据和未完成边界。
3. `docs/reproduction_report/figure_status_appendix.md` - 54 张图逐图状态，是 `data/computed/figure_validation_table.csv` 的可读渲染。
4. `docs/reproduction_report/numerical_audit_appendix.md` - Fig. 3.10、Chapter 4 DG manifold、Chapter 3 quasi-DRO 的重点审计。
5. `docs/reproduction_report/proxy_usage_appendix.md` - 哪些图仍使用 proxy、schematic、local overlay 或 grey reference。
6. Route A search / digitization docs:
   - `docs/reproduction_report/original_data_search_log.md`
   - `docs/reproduction_report/digitization_method.md`
   - `docs/reproduction_report/fig_3_16_digitization_feasibility.md`
7. `docs/reproduction_report/presentation_outline.md` - 组会 / 开题 PPT 阅读路径。
8. `docs/reproduction_report/qa_for_group_meeting.md` - 汇报问答和保守表述边界。

## File Classes

| class | paths | purpose | can_modify_directly | usable_for_presentation |
|---|---|---|---|---|
| core code | `src/qp_orbits/`, `scripts/`, `figures/` | 动力学、轨道校正、绘图和批处理入口。 | 本轮不可修改；后续算法任务需单独立项。 | 可用于解释工程结构，不直接作为结论证据。 |
| computed data | `data/computed/` | 当前数值证据、审计表、分支数据和验证表。 | 不可直接手改；必须由脚本或明确审计流程生成。 | 可用于汇报，但要引用对应复现等级。 |
| digitized reference data | `data/digitized/` | Route A 下从参考图提取的低权威趋势和元数据。 | 不应混入 `data/computed/`；修改需保留校准和方法记录。 | 可用于说明 gap 和趋势对照，不能当 raw branch data。 |
| reproduction figures | `outputs/figures_png/`, `outputs/figures_pdf/` | 54 张复现图输出。 | 不直接手改；由 figure scripts 生成。 | 可用于展示当前图像覆盖和具体案例。 |
| diagnostic outputs | `outputs/diagnostics/`, `outputs/figure_qa/`, `outputs/comparison_contact_sheets/` | 对比图、诊断图、分章 montage、逐图 contact sheet。 | 不直接手改；可复制精选图到 presentation 目录。 | 适合展示审计、对比和缺口。 |
| report package | `docs/reproduction_report/` | Route C 报告包：主报告、附录、未来计划、搜索和 digitization 记录。 | 可修改文档层，但不能改写核心结论为更乐观版本。 | 是教师和组会展示的主要文本依据。 |
| presentation materials | `docs/reproduction_report/presentation_outline.md`, `docs/reproduction_report/qa_for_group_meeting.md`, `docs/reproduction_report/teacher_package/`, `outputs/presentation/` | 汇报顺序、问答、精选图和一页总结。 | 可整理和补充，但不得覆盖原始数据或原始图输出。 | 是直接面向老师 / 组会的材料层。 |
| future work docs | `docs/reproduction_report/future_work_plan.md`, `docs/next_reproduction_roadmap.md` | Route A / B / C 后续路线、成功标准和停止条件。 | 可更新计划，不应伪装为已完成成果。 | 可用于讨论下一阶段研究任务。 |

## Canonical Sources of Truth

- 逐图复现等级的 canonical source of truth 是 `data/computed/figure_validation_table.csv`。
- 54 图可读状态的 canonical report rendering 是 `docs/reproduction_report/figure_status_appendix.md`。
- Fig. 3.10、Chapter 4 DG manifold、Chapter 3 quasi-DRO bottleneck 的审计口径以 `docs/reproduction_report/numerical_audit_appendix.md` 和对应 `data/computed/*.csv` 为准。
- proxy / baseline / local overlay 边界以 `docs/reproduction_report/proxy_usage_appendix.md` 为准。
- Route A 原始数据搜索结论以 `docs/reproduction_report/original_data_search_log.md` 为准。
- Fig. 3.17 digitized trend 的低权威参考数据以 `data/digitized/` 与 `docs/reproduction_report/digitization_method.md` 为准。
- Fig. 3.16 digitization 不可行边界以 `docs/reproduction_report/fig_3_16_digitization_feasibility.md` 为准。

## Reporting Guardrails

- 不要把 Fig. 3.16 / Fig. 3.17 升级为 full numerical reproduction。
- accepted quasi-DRO branch 只到 `max_abs_z = 10164.02309965055 km`。
- digitized Fig. 3.17 trend 是 lower-authority reference，不是 raw branch data。
- Fig. 3.16 不能从静态 3D 图中精确 digitize。
- Chapter 5 当前仍应表述为 CR3BP baseline、DE421-oriented baseline、local direct-shooting baseline 或 proxy 层。
- 展示材料和核心复现数据分开：汇报用副本放在 `outputs/presentation/`，不要移动或手改 `data/computed/`、`figures/`、`src/`。
