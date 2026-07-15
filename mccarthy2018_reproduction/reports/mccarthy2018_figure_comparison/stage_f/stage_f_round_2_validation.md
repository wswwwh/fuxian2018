# stage_f_round_2 报告自动审计

- 状态：**PASS**
- 生成时间：`2026-07-15T15:31:39.751665+00:00`
- DOCX：`C:\Users\wwh20\Desktop\复现论文\mccarthy2018_reproduction\reports\mccarthy2018_figure_comparison\McCarthy2018_54图逐图复现对照报告.docx`
- PDF：`C:\Users\wwh20\Desktop\复现论文\mccarthy2018_reproduction\reports\mccarthy2018_figure_comparison\McCarthy2018_54图逐图复现对照报告.pdf`
- PDF 页数：122
- 图号覆盖：DOCX 54/54；PDF 54/54

## 门槛检查

| 检查项 | 结果 | 细节 |
|---|---:|---|
| DOCX ZIP 可读 | PASS | `null` |
| registry 54 行且图号唯一 | PASS | `{"rows": 54, "unique": 54}` |
| 三份资产 manifest 均为 54 行 | PASS | `{"source": 54, "reproduced": 54, "comparison": 54}` |
| registry 必填字段完整 | PASS | `[]` |
| registry 三类资产路径有效 | PASS | `[]` |
| DOCX 54 图号覆盖 | PASS | `{"count": 54, "missing": []}` |
| PDF 54 图号覆盖 | PASS | `{"count": 54, "missing": []}` |
| DOCX 54 张嵌入图 | PASS | `{"media": 54, "drawing": 54, "blip": 54}` |
| DOCX 嵌入图分辨率与纵横比 | PASS | `[[1444, 843]]` |
| DOCX 54 个中文逐图图题 | PASS | `54` |
| DOCX 54 个英文逐图图题 | PASS | `54` |
| PDF 54 个中文逐图图题 | PASS | `54` |
| PDF 54 个英文逐图图题 | PASS | `54` |
| 54 个逐图证据表进入 DOCX/PDF | PASS | `{"docx": 54, "pdf": 54}` |
| 28 个核心量化表进入 DOCX/PDF | PASS | `{"docx": 28, "pdf": 28}` |
| 26 个非核心验证边界表标签准确 | PASS | `{"docx": 26, "pdf": 26}` |
| 54 个逐图等级与证据状态叙述 | PASS | `{"grade_narratives": 54, "status_mentions": 55}` |
| 核心数值图 28 张且指标完整 | PASS | `{"core_ids": 28, "failures": []}` |
| 自动目录字段存在 | PASS | `"TOC \\h \\o \"1-3\"  HYPERLINK \\l _Toc21099   PAGEREF _Toc21099 \\h   HYPERLINK \\l _Toc3784   PAGEREF _Toc3784 \\h   HYPERLINK \\l _Toc14774   PAGEREF _Toc14774 \\h   HYPERLINK \\l _Toc7818   PAGEREF _Toc7818 \\h   HYPERLINK \\l _Toc28195   PAGEREF _Toc2...` |
| 页码字段存在 | PASS | `true` |
| 标题自动编号存在 | PASS | `70` |
| 公式对象与式号完整 | PASS | `{"math": 6, "math_paragraphs": 6}` |
| 表格与双语编号符合构建记录 | PASS | `{"table_objects": 121, "labelled_tables": 116}` |
| 无 Word 域错误或 MERGEFORMAT 泄漏 | PASS | `{"docx": [], "pdf": []}` |
| 核心数值与失败边界进入正文 | PASS | `[]` |
| 总论结论未夸大论文等价 | PASS | `[]` |
| 封面未知信息使用待核实标记 | PASS | `{"present": ["【待核实】姓名", "【待核实】单位", "【待核实】导师"], "legacy_waiting": 0}` |
| 参考文献与正文引用存在 | PASS | `{"citation_1": 1}` |
| 关键单位进入报告 | PASS | `{"km": 152, "day": 141, "m/s": 32}` |
| 可重复构建命令进入附录 | PASS | `true` |
| 多级标题编号后保留空格 | PASS | `{"joined_heading_count": 0, "examples": []}` |
| PDF 无真正空白页 | PASS | `[]` |
| PDF 无近空白孤页 | PASS | `[]` |
| PDF 页数与 Word 导出状态一致 | PASS | `{"pdf": 122, "export_status": 122}` |
| 待核实字段集中且未被消隐 | PASS | `{"registry_fields": 6, "docx": 21, "pdf": 21}` |
| 等级统计符合审计 | PASS | `{"D": 12, "B": 30, "A": 7, "C": 5}` |
| 证据状态统计符合审计 | PASS | `{"proxy": 12, "boundary": 30, "accepted": 7, "diagnostic": 5}` |

## 版面提示

- 空白页：无
- 低文本且无位图页（需结合矢量内容人工复核）：无
- `【待核实】`：registry 字段 6 项；DOCX 文本 21 处；PDF 文本 21 处。

说明：自动审计验证结构、覆盖、字段、错误字符串和空白页；分页美观与图片可读性仍须结合渲染总览人工复核。
