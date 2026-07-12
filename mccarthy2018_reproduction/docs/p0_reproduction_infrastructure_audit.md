# P0 Reproduction Infrastructure Audit

更新时间：2026-07-11

## Purpose

本审计记录 McCarthy 2018 后续复现计划 P0 阶段的第一批基础设施。目标是把“论文图已生成”升级为“每张图有明确论文目标，并能通过无副作用命令快速检查当前证据完整性”。

## Added Artifacts

- `data/reproduction_targets.csv`
  - 54 个唯一图号；
  - 13 张纯示意图标为 `V0`；
  - 41 张数值/应用图标为 `V2`；
  - 54 行均为 `explicit` 论文目标，没有遗留 `needs_parameter_extraction`；
  - 同时保留当前复现等级、proxy 状态、证据路径和下一动作。
- `scripts/build_reproduction_targets.py`
  - 从 `data/figure_index.csv` 与 `data/computed/figure_validation_table.csv` 生成注册表；
  - `--check` 模式只比较、不写文件，可检测手工漂移。
- `scripts/validate_reproduction_smoke.py`
  - 默认只读；
  - 检查 54 图集合、13/41 目标分层、Route H 非退化门槛、staged gate、54 对非空 PNG/PDF；
  - 失败返回非零并输出首个明确原因。
- `tests/test_validate_reproduction_smoke.py`
  - 覆盖缺少注册表、重复图号、目标提取不完整、生成器漂移和健康仓库五条公开 CLI 行为。
- `tests/test_torus_stability_eigen_selection.py`
  - 验证明显复数的双曲候选会被拒绝；
  - 验证存在近实候选时不会被模更大的复候选覆盖。
- `tests/test_staged_goal_gate_audit.py`
  - 验证 Chapter 4 复特征值会阻止 C4 gate 和 staged goal 的完成声明。

## Paper Target Completion

目标注册表补充了论文中明确给出的关键值，包括：

- Fig. 3.16 的 `T0=14.74 day` 和四个 Jacobi anchor；
- Fig. 4.1 的 `JC=3.044`、`N=25`、`nu=1.3837`；
- Fig. 4.3-4.6 的全部快照时刻；
- Fig. 5.1 的 325/1068/2182 day；
- Fig. 5.8 的 `143.4 m/s`、186.9 day；
- Fig. 5.10 的两组分燃烧和 TOF；
- Fig. 5.12 的 `-24..24 h` 与约 `-6.5 h` 极小值；
- Fig. 5.13/5.14 的两频环面尺度、采样量和 LEO 半径目标。

基础图 2.3、2.7、2.8、2.11、2.15 也已回到论文公式与方法定义，不再只保留 caption：平动点解析几何、L1 线性模态、Lissajous 线性解、L2 Lyapunov 垂直穿越校正和稳定指标公式均有明确登记。

## Verification

在 `D:\miniconda3\envs\cislunar\python.exe`、`PYTHONDONTWRITEBYTECODE=1` 下运行：

```powershell
python -m unittest discover -s tests -v
python scripts/build_reproduction_targets.py --check
python scripts/validate_reproduction_smoke.py
```

当前结果：

- 行为测试：`13/13 PASS`；
- target registry：`54 rows, up to date`；
- smoke：`PASS`；
- 目标分层：`V0=13, V2=41`；
- 当前完成度：`numerical reproduction=16, open=25`；
- Route H：`30 rows`，最大 `|z|=14573.1031841 km`，最大 map residual `6.469e-10`；
- staged goal：`chapter3_passed_chapter4_ready`；monolithic cold-start 仍为 fail，但 hybrid cold-start reconstruction chain 已通过；
- 图件：`54 PNG + 54 PDF`，均存在且非空。

## Corrected Chapter 4 Gate

旧 C4 aggregate gate 只检查 determinant、模长互易性和 Jacobi drift，没有验证用于流形传播的特征值是否真正近实。当前三个 Route H manifold probe 的 selected eigenvalue 为：

- member 17：`-0.8332203811+0.6658222758j`；
- member 32：`-0.9529250821+0.3471814378j`；
- member 68：`1.0073295185+0j`。

前两项明显不是论文流形构造所需的纯实双曲方向。现已完成：

1. `real_hyperbolic_eigen_index()` 增加默认 `1e-6` relative-imaginary 硬门槛，无合格候选时明确失败；
2. Chapter 4 DG audit 增加稳定/不稳定特征值实部、虚部、相对虚部和复数互易误差字段；
3. staged gate 将 selected-eigenvalue relative imaginary 纳入 C4 判定；
4. staged goal 完成条件修复为 Chapter 3、Chapter 4、Chapter 5 和逐图审计同时通过，不能再由 Chapter 5 单独覆盖 Chapter 4 失败；
5. 重新生成 `mccarthy2018_staged_goal_gate_status.csv/.md` 后，C4 状态为 `ready_for_regeneration`，总状态为 `chapter3_passed_chapter4_ready`。

真实 cache 的只读复核也已通过预期行为：

- member 68：选中 `1.0073295185+0j` / `0.9927238125+0j` 实稳定/不稳定对，复数互易误差 `3.44e-15`；
- member 17：最小 relative imaginary 为 `0.624264`，高于 `1e-6`，因此被明确拒绝。

## Route H Cold-Start Evidence

`corrected_dro_fixed_mapping_full_corrections()` 现支持显式隔离 cache directory，参数哈希不因目录改变。新增 `run_chapter3_fixed_mapping_cold_start_audit.py` 后得到：

- smoke cold-start：从零生成 4 个成员，22.371 s，`JC=2.92249` 目标误差 `4.714e-7`，status `pass`；
- full cold-start 第一次：从零运行 560.501 s，生成 19 个单调成员后在 `JC=2.9222828` 失去单调方向；
- full checkpoint resume：从 19 个成员恢复，39.389 s 后在同一位置重复失败，成员数和 cache SHA-256 均未变化；
- cold-start checkpoint SHA-256：`4B8209C045A7929482EA65227AB603A4627BD83E58D5E4B1FC7AF67939CBA5DA`；
- historical canonical cache SHA-256：`6B1BF209340BB27CA2C489689FFAAEFAA50170D4834A676EDA877FAEEA3363B0`。

因此 historical Route H artifact 仍仅是可审计数值证据，旧 monolithic 路线不得表述为成功。后续新增的 hybrid chain 从零缓存生成的 19-member checkpoint 出发，经 fixed-Jacobi free-time bridge、逐点能量固定时间同伦与谱提升重建 Fig. 3.16 四个锚点；`C3-ROUTE-H-HYBRID-COLD-START` 与论文精度目标覆盖 gate 已通过，权威 staged goal 状态更新为 `chapter3_passed_chapter4_ready`。

## Full Real-Hyperbolic Coverage Scan

`run_chapter4_real_hyperbolic_scan.py` 已扫描全部 31 个 strict Route H 成员：

- 通过：`1/31`，仅 member 68；
- member 68 的最大 `|z|=13404.1277 km`；
- 其余 30 个成员缺少满足 `1e-6` relative-imaginary 门槛的稳定/不稳定实双曲对；
- 最大振幅 member 54 的最小 relative imaginary 约 `0.34052`。

Chapter 4 gate 现要求至少 3 个有效成员并跨越 2,000 km 振幅范围，防止用唯一容易通过的 member 68 冒充完整 branch coverage。

## Boundary And Remaining P0 Work

本审计不证明整篇论文复现完成，也不替代长时间数值回归。P0 仍需完成：

1. 修复 fixed-mapping continuation 在 `JC=2.9222828` 的 cold-start 单调方向丢失，完成三个论文 Jacobi 目标并使 checkpoint SHA/数值证据可由当前代码重建；
2. 重新生成具有真实双曲方向覆盖的 Chapter 4 source family，并补完 eigenpair residual 和 growth-direction gate；当前 strict Route H family 只有 1/31 可用；
3. 补齐 `skyfield` 等依赖声明与可重复环境锁；
4. 统一仍可能漂移的 README、project index、stage report 和 roadmap；
5. 将重型 `validate_basics.py` 拆分为可选择输出目录的逐章/full 验证层，再执行最新全量回归。

在以上条目完成前，P0 状态应记录为 `in_progress`，目标模式不得标记 complete。
