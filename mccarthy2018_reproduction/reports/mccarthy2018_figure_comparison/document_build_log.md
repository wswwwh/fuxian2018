# McCarthy 2018 逐图对照报告构建日志

## 2026-07-15 — 阶段 A：审计与设计

- 状态：`PASS_WITH_TRACKED_GAPS`。
- 输入：McCarthy 2018 本地论文 PDF、用户提供的参考投稿版 DOCX、当前 54 图权威 CSV/NPZ/Markdown/图形资产。
- 输出：参考稿 OOXML/视觉样式审计、54 图目录与初始 registry、原图/复现图 manifest、项目审计、文档提纲、Word/绘图规范、缺失资产清单和阶段门槛。
- 完整性：54 个唯一图号；54/54 现有原图；54/54 复现 PNG；54/54 复现 PDF；54/54 PDF 图题块；原图和复现图重复哈希组均为 0。
- 跟踪问题：9 张现有原图裁图尺寸偏低，阶段 B 必须从原 PDF 高分辨率重提取；逐图模型、坐标系、方法和差异原因由阶段 C 从权威证据绑定。
- 参考稿页数差异：OOXML 扩展属性为 13 页；Microsoft Word 12.0 只读导出为 14 页；LibreOffice 26.2.4 导出为 15 页。
- 参考稿渲染失败记录：LibreOffice 把部分 Word 公式域显示为 `MERGEFORMAT` 文本，故不得作为唯一公式验收器。Microsoft Word PDF 导出成功后，COM 清理阶段报告 `0x800706BE`，检查未发现残留 `WINWORD` 进程，输出 PDF 完整存在。
- 真实性边界：Route H monolithic cold-start=`fail`；hybrid chain=`pass`；Chapter 4 冻结投影 holdout=`0/4 fail`；Fig. 5.10 数值接受=`2/2`、论文等价=`0/2`。这些负面/边界证据必须进入最终报告。

### 构建命令

```powershell
C:\Users\wwh20\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\analyze_reference_docx.py `
  ..\[20260709]DRO至日地L1 Halo有动力月球借力转移策略_投稿版.docx `
  --json reports\mccarthy2018_figure_comparison\stage_a\reference_style_analysis.json `
  --markdown reports\mccarthy2018_figure_comparison\stage_a\reference_style_analysis.md

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\build_stage_a_audit.py

D:\miniconda3\envs\cislunar\python.exe scripts\build_reproduction_targets.py --check
D:\miniconda3\envs\cislunar\python.exe scripts\validate_reproduction_smoke.py
```

### 验证结果

- `build_reproduction_targets.py --check`：`54 rows, up to date`。
- `validate_reproduction_smoke.py`：`SMOKE PASS`；`png=54`；`pdf=54`。
- 报告脚本 `py_compile`：通过。
- `git diff --check`：通过。
- 阶段 A 结束时最终 `.docx/.pdf` 数量：0，符合“先审计、后生成最终 Word”的门槛。

### 【待核实】

- 【待核实】作者、单位、导师、基金和投稿信息。
- 【待核实】原文未公开的完整初始状态、连续分支节点、相位、流形分支和优化约束。
- 【待核实】阶段 C 尚未逐条绑定的模型、坐标系、数值方法和差异原因。

## 2026-07-15 — 阶段 B：原图与复现图资产整理

- 状态：`PASS`。
- 原论文图：54/54；从 137 页主 PDF 以 `zoom=4.2` 重新渲染/裁切，名义分辨率 302.4 dpi；54 个唯一 SHA-256。
- 复现图：54/54；从当前脚本生成的非空 PNG/PDF 权威输出做哈希保持复制，54 个唯一 SHA-256。
- 真实性说明：阶段 B 的 `reexported_in_report_build=False`；没有重新计算 54 个数值任务，也没有覆盖 `outputs/figures_*`。
- 质量：原图 54/54 通过 `>=800×300 px`；复现图 54/54 通过 `>=1000×600 px`；缺失、空图、重复哈希和命名错误均为 0。
- 体量：原图 16,293,245 bytes；复现图 16,954,537 bytes。
- 人工接触表复核：54 对标签与图号一致；未发现错章、错号、正文误裁或漏掉整组子图。明显视觉差异保留为阶段 C-D 科学差异，不作为映射错误消除。

### 构建命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\extract_mccarthy_figures.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\collect_reproduction_figures.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\validate_report_assets.py
```

### 验证结果

- `original_figures=54 unique_hashes=54 quality={'pass': 54}`。
- `reproduction_figures=54 unique_hashes=54 quality={'pass': 54} reexported=0`。
- `stage_b=PASS figures=54 original_unique=54 reproduction_unique=54 review=0`。

## 2026-07-15 — 阶段 C：定量证据整理

- 状态：`PASS_WITH_TRACKED_PENDING`。
- 54/54 图均绑定研究对象、模型、坐标系、主要参数、数值方法、脚本、数据源、证据状态、A-E 等级、差异、原因和限制。
- 等级统计：A=7、B=30、C=5、D=12、E=0。A 级只代表当前项目门槛内定量通过，不等于论文原作者节点逐点等价。
- 权威证据状态：accepted=7、boundary=30、diagnostic=5、proxy=12。
- 定量注册表：238 行；28 张优先核心数值图均至少 2 条记录，并至少包含 1 条当前项目数值。
- CSV 直接范围使用当前文件 min/max，不外推；原论文未报告的残差、Jacobi 漂移、闭合误差等明确标记为“原论文未报告（本项目验证指标）”。
- 边界复核：q=8 单步闭合误差 3.906984451743337；Route H monolithic cold-start=fail；Chapter 4 frozen holdout=0/4；Fig. 5.10 paper_equivalence=0/2；Fig. 5.12 只覆盖 -24..+11 h。
- 【待核实】字段：60 条，其中 54 条为阶段 D 尚未生成的 comparison asset，6 条为任务几何/星历图的统一坐标元数据。

### 构建命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\build_stage_c_evidence.py
```

### 验证结果

- `stage_c=PASS_WITH_TRACKED_PENDING figures=54 metrics=238 core=28 core_missing=0 pending=60`。
- 所有可解析证据路径存在；核心图数值覆盖缺失为 0；必填字段空值为 0。
- `scientific_boundary_review.md` 明确保留失败、局部和高保真边界。

## 2026-07-15 — 阶段 D：统一 panel 与图形审查

- 状态：`PASS`。
- 生成 54/54 对照 panel；固定 2400×1400 px；54 个唯一 SHA-256；缺失和重复均为 0。
- 统一内容：白色画布、左右边框、(a)/(b) 标签、原图号、A-E 等级、中英文状态和页码；两侧均等比缩放。
- 保护规则：cropped=False、stretched=False、underlying_scientific_figure_redrawn=False；没有修改坐标、相机、颜色、数值参数或底层科学图。
- 通栏/双栏预览均已生成。人工复核决定 54 个逐图对照全部通栏；双栏只用于摘要、方法和文本密集段落。
- 人工 montage 复核覆盖 Chapter 2/3/4/5 的 15/17/8/14 个 panel，未发现左右颠倒、图号错位、空图或漏子图。
- registry 的 comparison asset 已从 54 条【待核实】补齐为 54/54；剩余【待核实】为 6 条统一坐标元数据。

### 构建命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\build_comparison_panels.py
```

### 验证结果

- `stage_d=PASS panels=54 unique=54 pending=6 redrawn=0`。
- `graphics_review.csv`：54 行全部 pass。
- `visual_panel_review.md`：人工复核 PASS。

## 2026-07-15 — 阶段 E：完整 Word 初稿与 PDF

- 状态：`PASS`。
- 通过 `build_word_report.py` 生成完整 DOCX：54 个逐图 panel、54 个中文逐图图题、54 个英文逐图图题、116 组双语表题、121 个实际表对象、6 个 OMML 公式对象和 28 张核心数值图量化表。
- 文档结构：中英文摘要/关键词；双栏引言、动力学和评价方法；Chapter 2—5 的 54 组通栏逐图论证；综合讨论、限制、结论、参考文献与附录 A—D。
- Word 12.0 COM 更新自动目录并导出主 PDF；最终为 122 页。初次导出的目录后近空白页已通过节设置修正，自动审计的空白/近空白页均为 0。
- 最终 DOCX：12,260,624 bytes；SHA-256 `f1f19f5ca51e9552b3b6d19d4005be3d015c374943737100947cc856576edbab`。
- 最终 PDF：12,968,768 bytes；SHA-256 `04d519277488a3f4c174c8169979e932f860f61bdc822d92e7fb2ffabf049cdf`。
- LibreOffice 交叉导出为 127 页，分页差 -5；54/54 图号和 54/54 双语图题仍完整，`MERGEFORMAT` 与域错误为 0。最终 PDF 以 Word 导出为准。
- Word COM 退出阶段仍可能报告远程过程调用清理警告，但导出状态为 PASS，且检查后无残留 `WINWORD` 进程。

### 构建命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\build_word_report.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\export_report_pdf.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\validate_final_report.py `
  --output-dir reports\mccarthy2018_figure_comparison\stage_e `
  --label stage_e_precheck

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\render_report_review.py `
  --output-dir reports\mccarthy2018_figure_comparison\stage_e\visual_review
```

### 验证结果

- `word_build=PASS figures=54 metrics=238 media=55`；其中 ZIP 目录项 1 个、实际媒体 54 个。
- `pdf_export=PASS engine=Microsoft Word COM pages=122 fallback=False`。
- `final_report_validation=PASS checks=25 pages=122 docx_figures=54 pdf_figures=54`。
- 全页 contact sheet 覆盖 122/122 页；16 张重点样张覆盖封面、目录、方法、四章代表图、讨论、附录和待核实清单。

### 【待核实】

- 封面：`【待核实】姓名`、`【待核实】单位`、`【待核实】导师`。
- registry：Fig. 5.2、5.3、5.4、5.6、5.7、5.10 的统一坐标元数据仍为 `【待核实】`。

## 2026-07-15 — 阶段 F：两轮期刊式质量检查与最终验收

- 状态：`PASS`。
- 第 1 轮执行内容、结构、可追溯性和资产复验：资产 `PASS`；最终报告 36 项中 33 项通过。发现标题编号间距、26 张非核心图指标标签过强、参考文献作者标点三项问题。
- 第 1 轮修订：多级编号和参考文献列表显式使用空格后缀；仅 28 张 `priority_core=true` 图标“核心定量指标”，其余 26 张改为“验证/边界指标”；作者格式统一为 `McCarthy, B. P.`；封面待核实项改为红色加粗。
- 第 2 轮执行同一报告的强化自动验收与全页渲染：37/37 项通过；122/122 页总览和 22 张重点页通过人工复核。
- 最终 DOCX：12,261,055 bytes；SHA-256 `41a62e98470a226fb97485ad8eb482e71f311a3156cf854c4055ef302ec8c047`。
- 最终 PDF：12,966,265 bytes；122 页；SHA-256 `0e3537b4c2e41bdcfd95e621432a9e03984a3cc19f9377b0a6ec45d449b13976`。
- 最终 Word 内嵌图：54 张，Word 保存后均为 1444×843 px；纵横比保持，人工放大可读。
- LibreOffice 交叉 PDF：127 页；SHA-256 `9294911f0141a4b079953f04a056506825f922a5f69e3e340ef66e9cf336df8e`；54 图完整，域错误 0。5 页分页差来自跨引擎布局算法，最终 PDF 以 Word 导出为准。
- 阶段 E 基线提交：`0cb5531`；阶段 F 验收文件与最终二进制在本阶段最终 Git 提交中记录，具体提交哈希以 `git log` 为准。

### 第 1 轮命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\validate_report_assets.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\validate_final_report.py `
  --output-dir reports\mccarthy2018_figure_comparison\stage_f `
  --label stage_f_round_1
```

### 第 2 轮命令

```powershell
D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\build_word_report.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\export_report_pdf.py

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\validate_final_report.py `
  --output-dir reports\mccarthy2018_figure_comparison\stage_f `
  --label stage_f_round_2

D:\miniconda3\envs\cislunar\python.exe `
  reports\mccarthy2018_figure_comparison\scripts\render_report_review.py `
  --output-dir reports\mccarthy2018_figure_comparison\stage_f\round_2_visual
```

### 最终结果

- `stage_f_round_1_validation.json/md`：`FAIL_REVISED`，修订前证据保留。
- `stage_f_round_2_validation.json/md`：`PASS`，37/37。
- `review_checklist.md`：内容完整性、文档质量、科学可信度和可重复性全部勾选通过。
- `stage_f/final_acceptance.json/md`：最终验收 `PASS`。
