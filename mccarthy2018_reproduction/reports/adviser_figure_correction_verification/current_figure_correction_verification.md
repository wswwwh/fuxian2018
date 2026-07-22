# 导师指出图像的当前修正验收

- 覆盖：`25` 幅（原 P0 `18`，原 P1 `7`）。
- 当前表达正确性：`25/25` 通过。
- `通过` 的含义：绘图源、代理标记、数值边界、PNG/PDF 产物与人工查看过的 PNG 哈希一致。
- 这里**不声明论文逐点等价**；所有未完成的论文等价条件仍保留在 `remaining_boundary`。

| 图 | 原优先级 | 修正方式 | 表达门槛 | 代理 | 数值证据 | 尚存边界 |
|---|---|---|---|---|---|---|
| 3.5 | P0 | rendering_and_anchor_boundary | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | The 12.03-day paper y/z amplitude anchor is not matched. |
| 3.6 | P0 | quantitative_anchor_disclosure | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | The full paper curves still require digitized pointwise comparison. |
| 3.7 | P0 | transparent_topology_boundary | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | Late-family paper topology/projection is not matched. |
| 3.9 | P1 | proxy_tail_disclosure | pass | partial | source-layer/boundary evidence is tracked by the per-figure audit | The dashed halo tail is not a numerical continuation. |
| 3.10 | P1 | strict_vs_local_acceptance_split | pass | partial | q2/q3 strict pass; q8 strict fail retained | q=8 lacks strict full-period single-shoot closure. |
| 3.11 | P1 | proxy_semantics_repaired | pass | partial | source-layer/boundary evidence is tracked by the per-figure audit | The illustrative section contours must be replaced by event-detected crossings. |
| 3.12 | P0 | transparent_topology_boundary | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | Panels (b)-(d) do not preserve the paper torus-hole topology. |
| 3.13 | P0 | endpoint_coverage_boundary | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | The numerical branch ends below the approximately 93000-km paper endpoint. |
| 3.16 | P0 | source_and_renderer_repaired | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | Route H does not cover the full thesis branch/range. |
| 3.17 | P1 | proxy_context_disclosure | pass | partial | source-layer/boundary evidence is tracked by the per-figure audit | Most of the thesis-scale trend remains proxy context. |
| 4.1 | P0 | degenerate_surface_removed | pass | false | max phase width 0.007668351 km; degenerate geometry disclosed | The DG target passes, but finite-amplitude torus geometry does not. |
| 4.2 | P1 | digitized_overlap_and_tail_boundary | pass | false | overlap pass; tail gap 0.049450113 day | The last approximately 0.04945 day of the paper curve is uncovered. |
| 4.3 | P0 | frozen_projection_failure_disclosure | pass | false | frozen projection holdout fail and paper_3d=false retained | Frozen paper-projection holdout fails. |
| 4.4 | P0 | frozen_projection_failure_disclosure | pass | false | frozen projection holdout fail and paper_3d=false retained | Frozen paper-projection holdout fails. |
| 4.5 | P0 | frozen_projection_failure_disclosure | pass | false | frozen projection holdout fail and paper_3d=false retained | Frozen paper-projection holdout fails. |
| 4.6 | P0 | frozen_projection_failure_disclosure | pass | false | frozen projection holdout fail and paper_3d=false retained | Frozen paper-projection holdout fails. |
| 4.7 | P0 | local_baseline_disclosure | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | The dense thesis global reach/topology is not reproduced. |
| 4.8 | P0 | local_baseline_disclosure | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | The dense thesis Earthward reach/topology is not reproduced. |
| 5.1 | P0 | data_source_repaired | pass | false | one common trajectory at 325/1068/2182 days | BCR4BP/ephemeris and pointwise paper comparison remain open. |
| 5.5 | P0 | proxy_scene_removed | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | A corrected ephemeris/BCR4BP return remains open. |
| 5.8 | P1 | project_baseline_disclosure | pass | false | source-layer/boundary evidence is tracked by the per-figure audit | Thesis pointwise geometry and high-fidelity correction remain open. |
| 5.10 | P1 | numerical_vs_paper_acceptance_split | pass | false | BCR4BP numerical 2/2; paper equivalence 0/2 | The paper-specific quasi-NRHO boundary states and geometry are not recovered. |
| 5.12 | P0 | truncated_domain_disclosure | pass | false | accepted branch right edge +11 h | The numerical branch stops at +11 h. |
| 5.13 | P0 | data_source_repaired | pass | false | active two-angle scan 70x16 | High-fidelity correction and pointwise heat-map comparison remain open. |
| 5.14 | P0 | data_source_and_target_repaired | pass | false | 185-km LEO target radius 6563 km | High-fidelity BCR4BP/ephemeris correction remains open. |

## 判定边界

本表解决的是导师指出的明显错误、错误数据源、代理未披露、截断范围未披露和失败门槛被隐藏的问题。
若要把某幅图升级为 McCarthy (2018) 的论文等价复现，仍必须完成该行记录的数值延拓、全局流形、点对点数字化或高保真动力学门槛。

人工视觉复核清单：`reports/adviser_figure_correction_verification/visual_review_manifest.csv`。
