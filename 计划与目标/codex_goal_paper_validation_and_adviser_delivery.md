# Codex 目标模式任务：完成 invariant-bundle 研究的论文级验收、导师交付与投稿准备

## 0. 任务定位

当前仓库已经完成：

- McCarthy（2018）复现基线冻结；
- 54 图逐图对照 Word/PDF 报告；
- invariant-bundle 独立研究层；
- 15 个 benchmark case、4 类轨道族；
- pointwise eigendecomposition、partial real-Schur、shifted QR/SVD 三种方法；
- 96 项测试；
- 126 行流形实验；
- 内部论文初稿、摘要、贡献、图表与局限性材料。

本任务不再扩展大范围新算法，也不再追求 McCarthy 全部图的严格数值等价。

本阶段的总目标是：

> 将当前“内部完成”的研究结果提升为导师可以审阅、审稿人可以快速评价、主要数值结论能够独立复核的论文级材料。

必须完成四条主线：

1. 对 54 图 Word 报告进行最终人工交付前审计；
2. 对 invariant-bundle 结果进行独立数值后端验证；
3. 对失败案例、消融实验和可重复性进行论文级验收；
4. 将内部 methods draft 整理为可提交导师评审的中文论文初稿。

---

# 1. 真实性和范围边界

必须保留以下既有边界，不得修改或弱化：

- McCarthy 54 图是工程覆盖，不是全文严格数值等价；
- Chapter 4 frozen projection holdout 保持 `0/4`、`paper_projection=fail`、`paper_3d=false`；
- Route H physical corrected-rho case 当前不能接受为一维实不变子束；
- 二维实共轭子空间不得写成一维稳定/不稳定方向；
- 当前贡献定位为“可靠数值框架与系统比较”，不是新定理；
- 失败、boundary 和 negative-control 结果必须保留；
- research 层不得自动修改 reproduction validation table；
- 不得通过放宽阈值、改变物理参数或删除失败行制造更高通过率。

遇到无法核实的信息，使用：

```text
【待核实】
```

不得猜测。

---

# 2. 第一阶段：54 图报告交付前审计

目标文件：

```text
reports/mccarthy2018_figure_comparison/
  McCarthy2018_54图逐图复现对照报告.docx
  McCarthy2018_54图逐图复现对照报告.pdf
```

## 2.1 清理剩余占位符

检查并处理：

- 封面姓名；
- 单位；
- 导师；
- 已知的坐标系元数据；
- 文档中全部 `【待核实】`；
- registry 中过时的 `comparison_asset` 占位字段。

规则：

- 用户个人信息无法从仓库确认时，保留封面占位符并生成填写说明；
- 已经生成的 54 张 comparison panel 路径应回写到 registry；
- 坐标系能从脚本和数据明确确定时填写；
- 无法确定时保留 `【待核实】` 并说明具体缺失信息。

输出：

```text
reports/mccarthy2018_figure_comparison/
  final_manual_fields_checklist.md
  final_placeholder_audit.csv
```

## 2.2 最终文档一致性检查

检查：

- 54/54 原图；
- 54/54 复现图；
- 54/54 comparison panel；
- 54 组中英文图题；
- 54 组证据表；
- 图号、表号、公式号；
- 自动目录；
- 页码；
- 图片清晰度；
- 图表引用；
- 章节分页；
- 结论与当前 authoritative CSV 一致。

必须重新运行现有构建和验证脚本。

输出：

```text
stage_g_delivery_review/
  delivery_validation.json
  delivery_validation.md
  final_pages_contact_sheet.png
  selected_pages_review.md
```

## 2.3 导师交付包

生成一个只包含导师需要文件的目录：

```text
reports/adviser_delivery/
  McCarthy2018_54图逐图复现对照报告.docx
  McCarthy2018_54图逐图复现对照报告.pdf
  复现情况一页说明.pdf
  导师审阅重点.md
```

“复现情况一页说明”应包括：

- 已完成的核心工作；
- 复现等级统计；
- 最强数值结果；
- 主要客观限制；
- 不作严格等价声明的原因。

不要在该说明中展开原创论文计划，只提供当前复现事实和审阅重点。

---

# 3. 第二阶段：独立 real-Schur 后端验证

当前 Windows 环境中的 `scipy.linalg.schur` 存在运行异常，因此现有实现属于 partial real-Schur/eigenpair realification 路线。

必须增加至少一种独立后端验证，优先顺序：

1. 在新的 Conda 环境中使用稳定版本 SciPy + LAPACK；
2. MATLAB `schur` / `ordschur`；
3. Julia `LinearAlgebra.schur`；
4. Linux 环境中的 SciPy/OpenBLAS 或 MKL。

不得以同一段 NumPy eig 代码包装成“独立后端”。

## 3.1 验证范围

至少覆盖：

- Halo N21、N33、N45；
- Vertical N33、N45、N57；
- Sun–Earth member 468；
- Route H member 17、32、54、68 physical corrected-rho；
- Route H member 68 legacy seed-rho control。

## 3.2 对比指标

每个 case 比较：

- selected block dimension；
- selected spectrum；
- relative imaginary part；
- invariant-subspace principal angle；
- partial-Schur residual；
- bundle invariance residual；
- multiplier estimate；
- classification；
- accepted/boundary/fail；
- runtime。

输出：

```text
research/invariant_bundles/results/csv/
  independent_schur_backend_comparison.csv

research/invariant_bundles/results/npz/
  independent_schur_backend_bases.npz

research/invariant_bundles/docs/
  independent_schur_backend_validation.md
```

## 3.3 验收标准

- 一维/二维分类必须一致；
- principal angle 应满足预设容差；
- 关键 multiplier 和 residual 不得出现无法解释的数量级差异；
- Route H physical corrected-rho 不得因为后端变化被强行改写成一维；
- 若后端结果不一致，必须保留不一致并定位原因。

---

# 4. 第三阶段：QR/SVD 五个失败案例分类

当前 QR/SVD accepted 为 10/15，失败 5/15。

必须逐个分析失败原因，不得简单增加迭代次数直到通过。

## 4.1 对每个失败案例检查

- 目标是否本来就是二维实子空间；
- spectral gap 是否过小；
- 初始化是否错误；
- Fourier interpolation 是否造成误差；
- 200 次迭代是否达到平台；
- phase alignment 是否引入不连续；
- 稳定/不稳定 branch 选择是否正确；
- source state 是否为 boundary 或 failed source；
- 是否存在近退化或非双曲谱。

## 4.2 有界实验

每个失败案例最多进行：

- 3 种初始化；
- 3 个 iteration cap：200、500、1000；
- 2 个 spectral resolution；
- 1 次高精度重跑。

必须设置 wall-time 和停止条件。

## 4.3 分类标签

最终只能使用以下标签之一：

```text
no_accepted_1d_bundle
accepted_2d_real_subspace
insufficient_spectral_gap
iteration_stagnation
interpolation_resolution_boundary
source_state_boundary
method_initialization_sensitive
implementation_issue
unresolved
```

输出：

```text
research/invariant_bundles/results/csv/
  qr_svd_failure_classification.csv

research/invariant_bundles/docs/
  qr_svd_failure_analysis.md
```

---

# 5. 第四阶段：消融实验

必须证明改进来自哪些步骤，而不是多个处理叠加后的偶然结果。

至少比较以下版本：

1. pointwise eig，无 phase alignment；
2. pointwise eig，仅符号对齐；
3. partial real-Schur，无 phase tracking；
4. partial real-Schur + phase tracking；
5. QR/SVD，无 phase alignment；
6. QR/SVD + phase alignment；
7. QR/SVD + phase alignment + Schur dimension seed。

至少在以下案例运行：

- Halo N45；
- Vertical N57；
- Sun–Earth member 468；
- Route H member 68 physical corrected-rho；
- 一个明显 complex-pair negative control。

指标：

- bundle residual；
- phase principal angle；
- sign/subspace flips；
- cross-resolution angle；
- manifold geometry distance；
- runtime。

输出：

```text
research/invariant_bundles/results/csv/
  ablation_study.csv

research/invariant_bundles/figures/
  ablation_bundle_residual.*
  ablation_phase_continuity.*
  ablation_manifold_geometry.*

research/invariant_bundles/paper/
  ablation_results.md
```

---

# 6. 第五阶段：全新进程独立重跑

执行一次不使用旧结果表的完整重跑。

要求：

- 新 Python 进程；
- 清空 research cache；
- 使用冻结 benchmark registry；
- 使用冻结 config；
- 重新生成 cocycle、bundle 和 manifold 结果；
- 保存新 run_id；
- 与 Stage-F 结果逐字段比较；
- 生成 SHA256；
- 不覆盖原始结果。

输出目录：

```text
research/invariant_bundles/independent_rerun/
  results/
  logs/
  hashes/
  comparison_to_stage_f.csv
  independent_rerun_report.md
```

验收标准：

- 分类结果一致；
- 核心 residual 数量级一致；
- manifold acceptance 一致；
- 浮点差异在预设容差内；
- 不一致必须解释。

---

# 7. 第六阶段：GitHub Actions 持续集成

新增 CI，但不要让完整重计算导致每次提交运行数小时。

## 7.1 PR/Push 快速 CI

运行：

- import checks；
- unit tests；
- benchmark registry integrity；
- small synthetic bundle tests；
- 1 个小型 physical benchmark；
- document registry consistency；
- `git diff --check`。

## 7.2 手动或定时 full validation

支持 `workflow_dispatch`：

- 15-case bundle benchmark；
- selected manifold benchmark；
- result schema checks；
- artifact upload。

新增：

```text
.github/workflows/
  ci.yml
  full_research_validation.yml
```

CI 不得修改 committed authoritative results。

---

# 8. 第七阶段：文献核实与论文定位

当前 paper 材料明确缺少外部文献。

只使用可核实的正式来源：

- 期刊论文；
- 学位论文；
- 专著；
- 官方技术报告；
- DOI 或出版社页面；
- arXiv 仅作为补充。

## 8.1 文献主题

至少覆盖：

- quasi-periodic invariant tori；
- cocycle/reducibility；
- invariant bundles；
- QR/continuous orthogonalization；
- covariant Lyapunov vectors；
- real Schur invariant subspace tracking；
- CR3BP quasi-periodic orbit computation；
- invariant manifold computation；
- McCarthy 2018 及其相关工作。

## 8.2 文献矩阵

输出：

```text
research/invariant_bundles/paper/literature_matrix.csv
```

字段：

```text
reference_id
authors
title
year
venue
doi
official_url
method
problem
relation_to_this_work
claim_supported
verified
```

不得编造 DOI。

## 8.3 论文定位判断

根据文献核实后，选择并记录一种定位：

```text
methodological_innovation
numerical_framework_and_systematic_comparison
failure_mode_and_diagnostic_study
```

当前默认优先：

```text
numerical_framework_and_systematic_comparison
```

除非文献和实验明确支持更强结论。

---

# 9. 第八阶段：中文论文初稿

在现有 `research/invariant_bundles/paper/` 基础上生成一份完整中文稿：

```text
research/invariant_bundles/paper_release/
  manuscript_zh.md
  manuscript_zh.docx
  figures/
  tables/
  references.bib
  claim_evidence_matrix.csv
  limitations.md
  reviewer_quick_assessment.md
```

## 9.1 推荐题目

默认题目：

```text
拟周期轨道实不变子束计算方法的数值比较与可靠性分析
```

可根据最终结果调整，但不得使用“全新理论”“首次提出”等未经证实措辞。

## 9.2 文章结构

1. 引言
2. 问题描述与 cocycle 方程
3. 传统点式特征方向方法及其失效模式
4. Partial real-Schur 方法
5. Shifted QR/SVD cocycle 迭代
6. Benchmark 轨道族与评价指标
7. 子束结果
8. 消融实验
9. 流形传播与几何收敛
10. Route H 算子语义案例
11. 计算成本
12. 局限性与讨论
13. 结论

## 9.3 必须回答的科学问题

- 为什么 pointwise eig 不是 cocycle invariant bundle；
- 为什么复共轭对不能投影成一维实方向；
- Schur 与 QR/SVD 各自解决什么问题；
- 哪些 case 上方法有效；
- 哪些 case 上仍失败；
- 失败是否来自方法、分辨率、源轨道或谱结构；
- Route H corrected-rho 与 legacy seed-rho 的差异说明什么；
- 局部 bundle 收敛与全局 manifold sheet 收敛为什么必须分开评价。

## 9.4 Claim-evidence matrix

每个论文结论必须绑定证据：

```text
claim_id
claim_text
supporting_cases
supporting_csv
supporting_figure
acceptance_threshold
status
limitation
```

---

# 10. 第九阶段：导师快速审阅材料

额外生成一份不超过 4 页的中文研究摘要：

```text
reports/adviser_delivery/
  invariant_bundle研究摘要_4页.docx
  invariant_bundle研究摘要_4页.pdf
```

内容：

1. 复现工作如何引出问题；
2. 点式特征方向的主要缺陷；
3. 三种方法；
4. 15-case 总体结果表；
5. 三个高分辨率案例；
6. Route H 关键发现；
7. 当前论文贡献；
8. 仍需补充的内容。

同时生成：

```text
reports/adviser_delivery/
  给导师的审阅问题.md
```

只列 3–5 个明确问题，例如：

- 论文定位是否合适；
- 是否优先投中文核心；
- Route H 案例是否作为核心贡献；
- 是否需要增加稳定子束案例；
- 是否需要将 Sun–Earth 应用扩展为独立章节。

---

# 11. 测试和验证

至少运行：

```powershell
python -m unittest discover -s tests -v
python scripts/run_invariant_bundle_benchmarks.py
python scripts/validate_reproduction_smoke.py
python scripts/build_reproduction_targets.py --check
git diff --check
```

新增独立后端、失败分类、消融和重跑后，必须增加对应测试。

最终需要记录：

- 测试数量；
- 通过数量；
- 失败数量；
- wall-time；
- Git commit；
- 环境；
- 后端版本；
- BLAS/LAPACK 信息。

---

# 12. 最终验收门槛

只有满足以下条件，任务才可完成。

## 导师交付

- 54 图 Word/PDF 最终检查完成；
- 所有可解决的占位符已处理；
- 导师交付包生成；
- 一页复现说明生成。

## 独立科学验证

- 至少一个独立 Schur 后端完成；
- 关键 case 分类一致；
- QR/SVD 五个失败案例完成分类；
- 消融实验完成；
- 全新进程独立重跑完成。

## 工程可靠性

- GitHub Actions 快速 CI 建立；
- full validation workflow 建立；
- tests 全部通过；
- authoritative 结果未被无审计覆盖。

## 论文材料

- 文献矩阵完成；
- 中文论文初稿完成；
- claim-evidence matrix 完成；
- 4 页导师摘要完成；
- 贡献定位准确；
- limitations 完整。

---

# 13. 最终汇报格式

完成后报告：

1. 54 图报告最终状态；
2. 处理了哪些占位符；
3. 独立 Schur 后端及版本；
4. 后端验证是否一致；
5. QR/SVD 五个失败案例分类；
6. 消融实验结论；
7. 独立重跑结果；
8. CI 状态；
9. 文献数量和主题覆盖；
10. 论文最终定位；
11. 推荐题目；
12. 论文初稿路径；
13. 导师交付材料路径；
14. 尚未解决的科学问题；
15. 下一步建议。

---

# 14. 执行原则

- 先完成导师交付，再扩展论文实验；
- 先独立验证，再强化论文结论；
- 先分类失败，再尝试修复；
- 先核实文献，再写创新性；
- 不以通过率作为唯一目标；
- 不隐藏负结果；
- 不放宽 frozen gates；
- 每个阶段单独提交 Git commit；
- 保留所有日志、配置、哈希和失败证据；
- 不在独立验证完成前声明“可投稿”。
