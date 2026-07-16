# Stage-G 身份回填重建失败与恢复记录

- 时间：2026-07-16。
- 触发命令：`D:\miniconda3\envs\cislunar\python.exe reports/mccarthy2018_figure_comparison/scripts/run_stage_g_delivery_pipeline.py`。
- 首次结果：`delivery_validation` 返回 1；37 项检查中 36 项通过。
- 已通过事实：`兀文昊`、`中国科学院大学`、`张晨` 均已进入 DOCX/PDF；54/54 图、121 个表、122 页、等级统计和冻结边界均通过。
- 失败原因：报告仍有 2 处仅用于解释真实性规则的字面量 `【待核实】`，不是未填写字段；新验收门槛要求确认个人信息后交付版本中的该字面量归零。
- 恢复措施：将摘要身份说明改为配置驱动文本，将 E 级规则改写为“不足时标记为未核实并进入独立清单”，随后完整重跑 Stage-G。
- 第二次结果：`word_build` 曾因 Microsoft Word COM 前一轮导出后的瞬时文件占用返回 Node `UNKNOWN: unknown error, open ...docx`；权限、只读属性和独占打开探针均正常，待占用释放后同一构建命令无代码变更即通过。该事件分类为外部文件锁瞬态，不是报告内容或科学计算失败。
- 恢复加固：Stage-G 编排器仅对 `word_build` 增加最多 3 次、每次间隔 2 秒的有界重试；每次失败的返回码与 stderr 均写入最终执行日志，不掩盖瞬态失败。
- 验收哈希失败：报告重建通过后，101 项单元测试中的哈希测试发现旧 `artifact_hashes.csv` 包含正在被验收脚本截断重写的 `stage_g_acceptance_log.txt`，因此出现 `0 != 21026`。分类为验收基础设施的自引用哈希问题。
- 哈希恢复：稳定交付物继续进入 `artifact_hashes.csv`；执行日志、状态、运行配置和稳定清单在验收完成后进入 `stage_g_acceptance_hashes.json`。单元测试不再循环依赖尚未完成的验收状态。
- 真实性影响：无。失败发生在交付包复制与哈希重写之前；冻结状态文件未被修改，失败原因和恢复过程保留在本文件及最终执行日志中。
