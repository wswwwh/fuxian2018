# Stage-G 最终哈希复核命令恢复记录

## 失败

- 在工作区根目录 `C:\Users\wwh20\Desktop\复现论文` 运行最终哈希/聚焦测试组合命令时，错误地使用了项目内相对路径。
- `build_stage_g_delivery_package.py` 因缺少 `mccarthy2018_reproduction/` 前缀返回 `Errno 2`；`tests.test_stage_g_delivery_artifacts` 也因同一工作目录错误未能导入。
- 该失败发生在最终哈希重写之前，没有修改报告、导师包、验证 JSON 或冻结真值文件。

## 恢复

- 将工作目录切换为 `C:\Users\wwh20\Desktop\复现论文\mccarthy2018_reproduction`。
- 重新运行 `build_stage_g_delivery_package.py --hash-only`。
- 重新运行 `python -m unittest tests.test_stage_g_delivery_artifacts -v` 和 `git diff --check`。
- 恢复后的返回码与结果记录在当前提交前的最终验证输出；本文件随最终 `artifact_hashes.csv` 一并哈希。
