# 表格资产说明

最终报告中的表格保持为 Word 可编辑表格，不转成栅格图片。本目录用于说明其可重复生成来源：

- 逐图证据表：`figure_comparison_registry.csv`；54 张图各 1 张。
- 量化/边界指标表：`quantitative_metrics_registry.csv`；28 张核心数值图标为“核心定量指标”，其余 26 张标为“验证/边界指标”。
- 原图、复现图与 panel 清单：`source_figure_manifest.csv`、`reproduction_figure_manifest.csv`、`comparison_panel_manifest.csv`。
- 表格生成逻辑：`scripts/build_word_report.js`，由 `scripts/build_word_report.py` 调用。

本目录不保存手工截图，以避免表格内容与权威 CSV 分叉。
