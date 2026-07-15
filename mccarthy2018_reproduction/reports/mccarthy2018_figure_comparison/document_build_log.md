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
