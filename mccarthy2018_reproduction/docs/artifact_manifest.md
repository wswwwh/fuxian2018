# Artifact Manifest

本表用于区分核心复现资产、报告资产和展示资产。`source_of_truth` 表示该项是否是对应结论的权威来源；`can_modify_directly` 表示是否适合手工直接修改。

| path | artifact_type | purpose | source_of_truth | for_reproduction | for_presentation | can_modify_directly | notes |
|---|---|---|---|---|---|---|---|
| `src/qp_orbits/` | core code | CR3BP dynamics, correction, continuation, stability, manifold and application helpers. | Yes, for implementation behavior | Yes | Limited | No in this organization-only round | Do not edit algorithms in this pass. |
| `figures/` | figure scripts | Per-figure plotting scripts for the 54 target figures. | Yes, for generated figure logic | Yes | Limited | No | Do not modify figure scripts or rerun 54-figure batch in this pass. |
| `data/computed/` | computed data | Numerical outputs, validation CSVs, audit tables, branch data. | Yes | Yes | Yes, with labels | No | Core CSVs must not be hand edited. |
| `data/digitized/` | digitized reference data | Lower-authority Route A reference trends and calibration metadata. | Yes, for digitized reference only | Limited | Yes | Only with documented calibration | Do not merge digitized values into computed validation tables. |
| `outputs/figures_png/` | generated figures | PNG output of the 54 reproduced figures. | No, derived from scripts/data | Yes | Yes | No | Safe to copy selected PNGs to `outputs/presentation/`. |
| `outputs/comparison_contact_sheets/` | diagnostic comparison images | Side-by-side comparison contact sheets for individual figures. | No, diagnostic derivative | Yes | Yes | No | Use as visual QA, not numerical evidence. |
| `outputs/diagnostics/` | diagnostic outputs | Special diagnostic plots such as Fig. 3.17 corrected-vs-digitized comparison. | No, derived from data and diagnostic scripts | Yes | Yes | No | Current key file: `fig_3_17_digitized_comparison.png`. |
| `docs/reproduction_report/` | report package | Main Route C report package and appendices. | Yes, for report wording | Yes | Yes | Yes, documentation only | Must preserve conservative conclusions. |
| `docs/reproduction_report/main_report.md` | main report | Chinese narrative report of current reproduction status. | Yes, for report narrative | Yes | Yes | Yes, documentation only | Do not state complete reproduction. |
| `docs/reproduction_report/figure_status_appendix.md` | appendix | Markdown rendering of all 54 validation rows. | Yes, readable rendering | Yes | Yes | Regenerate/update from CSV, not ad hoc | CSV remains canonical for rows. |
| `docs/reproduction_report/numerical_audit_appendix.md` | appendix | Focused audit for Fig. 3.10, Chapter 4, Chapter 3 quasi-DRO, Route A digitization. | Yes | Yes | Yes | Yes, documentation only | Important source for teacher-facing claims. |
| `docs/reproduction_report/proxy_usage_appendix.md` | appendix | Lists proxy, schematic, local overlay, grey reference and baseline figures. | Yes | Yes | Yes | Yes, documentation only | Main overclaim-prevention document. |
| `docs/reproduction_report/future_work_plan.md` | future work | Route A / Route B / Route C plan, criteria and risks. | Yes, for planning | No | Yes | Yes | Future work, not completed result. |
| `docs/reproduction_report/presentation_outline.md` | presentation material | 15-slide Chinese outline for group meeting / proposal review. | Yes, for slide flow | No | Yes | Yes | Keep aligned with report package. |
| `docs/reproduction_report/qa_for_group_meeting.md` | presentation material | Adviser/group-meeting Q&A script with conservative wording. | Yes, for oral defense | No | Yes | Yes | Use to avoid overclaiming. |
| `docs/reproduction_report/original_data_search_log.md` | Route A record | Search records and negative evidence for public raw data / code. | Yes, for Route A search | Yes | Yes | Yes, documentation only | Current search found no public McCarthy quasi-DRO raw branch data. |
| `docs/reproduction_report/digitization_method.md` | Route A method | Digitization scope, calibration, uncertainty and reporting rules. | Yes, for digitization method | Limited | Yes | Yes, documentation only | Digitized trend is lower authority than raw branch data. |
| `docs/reproduction_report/fig_3_16_digitization_feasibility.md` | Route A feasibility | Explains why Fig. 3.16 cannot be precisely digitized from a static 3D image. | Yes | Limited | Yes | Yes, documentation only | Supports not overusing Fig. 3.16 annotations. |
| `docs/project_index.md` | navigation | Project-level reading path, file classes and source-of-truth map. | Yes, for organization | No | Yes | Yes | This is an index, not new numerical evidence. |
| `docs/artifact_manifest.md` | manifest | Table of major artifacts and modification rules. | Yes, for asset governance | No | Yes | Yes | Helps keep presentation materials separate from core data. |
| `docs/reproduction_report/teacher_package/` | teacher package | Teacher-facing summary, key table and asset index. | Yes, for teacher-facing summary | No | Yes | Yes | Should remain conservative. |
| `outputs/presentation/` | presentation outputs | Selected copied images and a README for PPT insertion. | No, convenience copies | No | Yes | Yes, for copied assets only | Do not move original outputs into this folder. |
