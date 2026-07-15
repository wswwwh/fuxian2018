# 阶段 F 第 1 轮：内容、结构与可追溯性检查

## 结果

- 自动报告门槛：`FAIL`，36 项中 33 项通过、3 项需修订。
- 阶段 B 资产复验：`PASS`；54 张原图、54 张复现图、唯一哈希与映射仍完整。
- 科学结论未发现新增失败：54/54 图号、54/54 嵌入 panel、54/54 双语逐图图题、54/54 证据表、28 张核心数值图、6 个公式、关键数值与失败边界均通过。

## 发现

1. **标题间距**：19 个两位数二级标题在 Word PDF 中显示为 `4.10McCarthy` 等，自动编号与标题之间缺少可见空格。
2. **指标标签**：54 张图都有验证记录，但只有 28 张是 `priority_core=true`。初稿把其余 26 张的验证/边界记录也标为 “Core quantitative metrics”，标签过强。
3. **参考文献标点**：文末为 `McCarthy B. P.`，与本报告采用的作者格式 `McCarthy, B. P.` 不一致。

## 修订动作

- 在多级标题和参考文献编号中显式设置 `LevelSuffix.SPACE`。
- 仅对 28 张 `priority_core=true` 图使用“核心定量指标 / Core quantitative metrics”；其余 26 张改为“验证/边界指标 / Validation and boundary metrics”。
- 参考文献作者改为 `McCarthy, B. P.`。
- 封面 3 个 `【待核实】` 占位同步改为红色加粗，以与表内待核实项一致。

本轮失败文件 `stage_f_round_1_validation.json/md` 保留，不覆盖，以形成修订前证据。
