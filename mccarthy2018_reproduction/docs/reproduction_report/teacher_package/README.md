# Teacher Package README

## 汇报目标

本目录用于老师快速判断 McCarthy 2018 复现项目的当前状态、可信成果、主要边界和下一步路线。核心口径是：项目已完成 54 图一版工程化覆盖和 Route C 报告包，但不是 complete McCarthy 2018 numerical reproduction。

## 建议老师先看的 5 个文件

1. `one_page_summary.md` - 一页中文总览，适合先建立全局判断。
2. `key_results_table.md` - 当前关键结果、数量统计和边界。
3. `../main_report.md` - 完整中文主报告。
4. `../numerical_audit_appendix.md` - Fig. 3.10、Chapter 4、Chapter 3 quasi-DRO 的审计证据。
5. `../proxy_usage_appendix.md` - 哪些图仍使用 proxy / baseline / local overlay。

## 适合组会展示的核心结论

- 54 张目标图已有一版工程化覆盖，并建立了逐图 validation table。
- 当前分类为 16 张 numerical reproduction、6 张 physical-consistency baseline、2 张 partial physical-consistency baseline、17 张 shape-match with local numerical overlay、13 张 proxy/schematic only。
- Fig. 3.10 的 q=8 是 highly unstable multiple-shooting local approximation，不是 robust single-shoot periodic orbit。
- Chapter 4 DG manifold 已有 corrected source curve、DG eigenvector propagation 和 Jacobi drift 证据，但不是 thesis-scale global manifold reproduction。
- Fig. 3.16 / Fig. 3.17 的 accepted quasi-DRO branch 只到 `max_abs_z = 10164.02309965055 km`，不能升级为 full numerical reproduction。
- Route A 搜索没有找到 McCarthy original quasi-DRO branch data、initial states、appendix tables 或 official code；Fig. 3.17 digitized trend 只能作为 lower-authority reference。

## 不能过度声明的边界

- 不能说已经完整复现 McCarthy 2018。
- 不能把 Fig. 3.16 / Fig. 3.17 称为 full numerical reproduction。
- 不能把 digitized Fig. 3.17 trend 当作 raw branch data。
- 不能把 Chapter 5 称为完整 BCR4BP / ephemeris optimized transfer reproduction。
- 不能把 proxy background、grey reference 或 local overlay 说成 corrected numerical data。

## 推荐展示顺序

1. 项目目标和当前状态。
2. 54 图覆盖与复现等级统计。
3. Fig. 3.10 period-q audit。
4. Chapter 4 DG manifold audit。
5. Chapter 3 quasi-DRO accepted branch 与 bottleneck。
6. Route A 原始数据搜索和 Fig. 3.17 digitization。
7. Route A / Route B / Route C 下一步计划。
