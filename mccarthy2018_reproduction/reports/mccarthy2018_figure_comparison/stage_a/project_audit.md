# 阶段 A 项目审计

## 审计对象

- McCarthy 主版本：`C:\Users\wwh20\Desktop\复现论文\2018_McCarthy_拟周期轨道.pdf`
- PDF 页数：`137`；SHA-256：`e434aeabb749dc34b2b05d12bfd77d7afe940a0e04eee1a6b20c2e1c4206456a`
- 参考投稿稿：`C:\Users\wwh20\Desktop\复现论文\[20260709]DRO至日地L1 Halo有动力月球借力转移策略_投稿版.docx`；SHA-256：`28fe6836665adfe7e36773c5cecbeb4f1947155e0bcfd78dc6de9c0f5fb669f4`
- 项目根目录：`C:\Users\wwh20\Desktop\复现论文\mccarthy2018_reproduction`
- 当前 Git HEAD：由阶段 A 提交后写入构建日志；本审计不改写权威 CSV。

## 54 图一致性

- `data/figure_index.csv`：54 个唯一图号。
- `data/reproduction_targets.csv`：54 行，集合与索引一致。
- `data/computed/figure_validation_table.csv`：54 行，集合与索引一致。
- `data/computed/figure_evidence_gap_audit.csv`：54 行，集合与索引一致。
- Chapter 2/3/4/5 目标数：15 / 17 / 8 / 14。
- 原论文现有裁图：54/54；复现 PNG：54/54；复现 PDF：54/54。
- 从原 PDF 文本块核对到的图题：54/54；其余均已列入缺失资产清单，不猜测补写。
- 原图重复哈希组：0；复现图重复哈希组：0。

## 当前权威状态

- 证据状态：accepted=7、boundary=30、diagnostic=5、proxy=12。
- proxy 标记：false=37、partial=5、true=12。
- 本报告 A-E 映射初值：A=7、B=30、C=5、D=12。
- staged gate 状态：blocked_by_chapter4=1、chapter3_passed_chapter4_ready=1、fail=4、informational=1、not_run_or_fail=2、pass=16、ready_for_regeneration=1。

## 真实性边界

- Chapter 3 Route H 当前图源层可审计，但 monolithic cold-start 失败仍必须保留；hybrid 冷启动链与具体图源层门槛不得混写。
- Chapter 4 Fig. 4.3-4.6 的状态空间/局部 STM 证据不等于论文投影等价；冻结的 panel-(d) 投影 holdout 为失败边界。
- 代理图、示意图、局部数值分支与应用 baseline 均不得升级为论文逐点等价。
- 参考稿只用于排版和论证形式学习；其研究数据、结论和句子不进入本报告。
- 任何未能从 PDF、CSV、NPZ、脚本或实际构建结果核实的信息统一写作【待核实】。

## 阶段 A 结论

54 图索引和现有资产均已建立一一映射；阶段 A 审计与设计交付齐全。低尺寸原图、未自动识别图题和逐图模型/坐标系/方法字段作为后续阶段的显式队列，不构成隐性假设。阶段 A 状态：`PASS_WITH_TRACKED_GAPS`。
