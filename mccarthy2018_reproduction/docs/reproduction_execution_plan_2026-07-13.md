# McCarthy 2018 后续复现执行计划（2026-07-13）

## 1. 总目标与当前判断

项目的最终目标是把 54 张图从“可生成/物理一致性”推进到“逐图可审计的论文级数值复现”。
本计划采用最严格的目标模式：只有存在可重运行脚本、显式参数、CSV/NPZ 数值证据、独立复核和图件审计时，结果才标记为 `accepted`；`diagnostic`、`boundary`、`proxy` 不得升级为论文结果。

当前事实基线（以仓库 CSV/Markdown 为准）：

- Chapter 3 Route H 已有超过 10,500 km 的图源层证据；混合 cold-start 可复核，但单体 cold-start 仍保留失败证据，不能声称所有路径完全可重建。
- Chapter 4 的 Fig. 4.2 已完成 PDF 原生图二维数字化并在共同区间通过逐点误差门，但计算分支仍缺论文末端约 0.04945 天。Fig. 4.3–4.6 已修正把历史前缀误作快照面的语义错误，改用 `tau + [0,T0]` 固定时刻全环面；16/16 数值与局部 STM 行通过，16/16 构型到达范围检查也通过，但后者依赖未校准的 `epsilon=4.5e-7`，不是论文级物理验收。当前无配准投影诊断仍有 14/16 面板告警，`paper_projection=not_run`、`paper_3d=false`。Fig. 4.7–4.8 仍保留旧比较语义。Route H 严格扫描的 31 个高振幅成员中只有成员 68 通过近实双曲门控，因此三成员跨振幅升级仍是 boundary。
- Chapter 5 Fig. 5.13/5.14 的 active-geometry Sun–Earth L1 两频环面、约 7,033 km 近地点和 185 km LEO 端点已通过 CR3BP 目标门；BCR4BP/DE421 按图校正和论文图逐点对照仍未完成。

## 2. 目标模式的硬目标（当前主线）

当前主线是 Fig. 5.13/5.14 的 Sun–Earth L1 两频 Lissajous 环面与稳定流形应用。论文目标注册表给出的目标对为：

| 项目 | 严格目标 |
| --- | --- |
| 全环面 `max\|y\|` | `<= 660,000 km` |
| 全环面 `max\|z\|` | `<= 940,000 km` |
| 高分辨率网格 | 至少 `129 x 256`（33,024 个点，超过论文要求的 3,500 点） |
| 主要应用指标 | 稳定流形候选近地点约 `7,033 km`；Fig. 5.14 的 185 km LEO 端点可审计 |

严格 `accepted` 还必须同时满足：

1. 全曲面（不是只在事件网格）通过双重进度门控，事件面与全曲面的最大值差异进入审计记录；
2. Jacobi span `<= 1e-8`、闭合残差 `<= 1e-8`，map/phase/geometry 残差均有数值证据；
3. 从保存的 checkpoint 独立重跑，得到同一目标对和同一状态哈希；
4. 生成环面 NPZ/CSV、稳定流形扫描、近地点热图、LEO 转移 CSV/PNG/PDF，并回写逐图验证表。

若只达到论文目标附近但未满足全部门控，标记为 `boundary`；若仅为局部或代理曲线，标记为 `diagnostic`/`proxy`，不得当作论文复现。

当前检查点（成员 468）为：全曲面 `max|y|=659,439.431 km`、`max|z|=939,944.305 km`，y 目标误差 `-560.569 km`，z 目标误差 `-55.695 km`，Jacobi span `1.028e-10`，闭合残差 `3.254e-09`，网格 `129 x 256`。目标对已满足 `target_pair_accepted=True`；两次零增量独立审计重跑已得到相同 CSV/checkpoint/报告 SHA-256 与状态哈希，Chapter 5 几何目标门控通过。

## 3. 分阶段执行顺序

### P0：冻结证据与可复现入口

- 保留当前 checkpoint、失败候选和每批审计 CSV；每个可接受批次单独提交。
- 用 `D:\miniconda3\envs\cislunar\python.exe` 和 `PYTHONPATH=src` 运行，保存环境、Git 提交和关键输入哈希。
- 每次延拓后运行单元测试、导入 smoke test、`git diff --check`，禁止以控制台输出替代文件证据。

### P1：完成高分辨率目标环面

- 继续 `run_chapter5_active_geometry_family.py` 的 active-event continuation，保持 `129 x 256` 全曲面验证。
- 使用自适应 y 步长和逐成员 z 修正；每 5 个成员或每次参数策略改变就固化 checkpoint/报告。
- 只有 full-torus y/z 进度均为正、Jacobi/闭合门控通过的候选才能接受；目标对达到后立即独立重跑确认，不再盲目扩大振幅。

### P2：从已接受环面重建 Fig. 5.13/5.14

- 在至少 3,500 个环面初值上扫描 stable manifold，统一事件检测、积分时长、坐标系和单位。
- 复核约 7,033 km 近地点候选，并构造 185 km LEO 端点；记录端点误差、Jacobi 漂移、积分步长和失败样本。
- 输出 stable-manifold/LEO 的 CSV、NPZ、PNG、PDF 与独立复核 Markdown；未通过的点保留为 boundary/diagnostic。

P2 当前证据：accepted=468 环面上的粗扫和 1° 细化均已保存；9×9、0.25° tight scan 的 best periapsis 为 `7034.029835 km`、最大 Jacobi 漂移 `1.508e-10`，LEO 转移为 `7034.028971 km`、Jacobi span `5.498e-13`，两者均 `acceptance=true`。tight scan 与 LEO 均在独立进程重跑后得到一致哈希；PNG/PDF/NPZ 已生成。外部 DE421/BCR4BP 修正仍明确标为 high-fidelity boundary。

### P3：重建 Chapter 4 原图级 DG/manifold

- 先运行 `scripts/run_chapter4_real_hyperbolic_scan.py`，用相对虚部 `1e-6`、determinant 误差 `<1e-9`、复数互易误差 `<1e-8` 锁定可用于实特征向量流形的 Route H 成员。
- 当前扫描结果为 `1/31` 通过，只有成员 68 可重建 DG 和局部不稳定流形；成员 17、32 等旧 CSV 中的复数双曲对已降级为 boundary，不再冒充 real manifold。
- 原始 Fig. 4.3–4.6 现使用固定时刻全环面快照：quasi-halo 为 `K=4, M=121, N=9`，quasi-vertical 为 `K=4, M=121, N=33`，共享项目可视化参数 `epsilon=4.5e-7`。16/16 行通过快照时间、源残差、DG、Jacobi、局部 STM 一阶一致性和独立重积分门；远场非线性/STM 比值只作诊断。当前构型范围包括 Fig. 4.3 `xmax=1.060688`、Fig. 4.4 `xmin=0.661348`、Fig. 4.5 `xmax=1.195293`、Fig. 4.6 `xmin=0.242478`。该参数不是论文公布值，不能据此声称物理包络等价，投影校准仍未完成。
- 因此 P3 的阶段结论是“4.3–4.6 数值状态空间与局部 STM 源层已打通，当前构型到达范围通过，但论文投影/物理等价、4.7–4.8 迁移和 Route H 三成员门均未通过”；只有轴刻度/Moon 锁相机后的红面 hold-out 投影门通过，同时 Route H 覆盖至少 3 个跨 2,000 km 且近实双曲门控均通过后，才可升级为完整 Chapter 4 复现。

### P4：逐图收尾与最终验收

- 按 `data/reproduction_targets.csv` 对 54 张图逐行更新 `figure_validation_table.csv`，区分 `accepted / boundary / diagnostic / proxy`。
- 重新生成 PNG/PDF、报告附录、教师版摘要和 artifact manifest；检查每一行是否能追溯到脚本、参数、数值文件和独立复核。
- 做一次从干净缓存/新进程的全量 smoke + 关键章节 full audit。只有总门槛全部通过才把项目标为完成；否则输出带边界的阶段性报告。

P4 初始审计检查点（2026-07-14）：

- `data/reproduction_targets.csv` 与 `data/computed/figure_validation_table.csv` 已重新生成并校验为 `54/54` 对齐；54 个 PNG 和 54 个 PDF 均存在且非空。
- `scripts/validate_reproduction_smoke.py` 通过：`targets_v0=13`、`targets_v2=41`、`current_numerical=16`、`current_open=25`；Route H hybrid cold-start 仍为 pass，单体 cold-start 仍保留 fail。
- Fig. 5.13/5.14 的逐图证据已改为 active-geometry 成员 468、全环面 `129 x 256`、tight stable-manifold `9 x 9` 和 LEO transfer 审计；目标模式的 CR3BP 几何门控通过，但 BCR4BP/DE421 和论文面板逐点对比仍是 boundary。
- `scripts/run_figure_evidence_gap_audit.py` 进一步给出保守证据分类：`accepted=7`、`boundary=30`、`diagnostic=5`、`proxy=12`，54 行的脚本/数据/PNG/PDF 路径均存在；该表只记录证据缺口，不新增科学主张。
- Fig. 4.2 已从 PDF 第 103 页 xref 473 无损提取 `1517 x 682` 原生面板：1054 个蓝线像素列、13 个共同区间计算点，覆盖 `89.026651%`，稳定性指数 RMSE `0.371003`、最大绝对误差 `0.510882`，均低于 `+/-1.953125` 数字化不确定度；`full_curve_coverage=false`，尾段缺口 `0.049450` 天保持为 boundary。
- Fig. 4.3–4.6 的 canonical 行已更新为“固定时刻全环面数值与局部 STM 通过、未校准 epsilon 下构型范围通过、论文投影与物理等价待校准”；16 面板投影诊断保留 14 个告警。Fig. 4.7–4.8 仍是旧比较边界；后续必须先迁移语义，再拟合/锁定论文相机做 projection-space Chamfer/coverage 审计，不能把静态 3D 图称为状态空间逐点数字化。
- Fig. 4.2 数字化脚本在两个独立 Python 进程中复跑，原生图、标定 CSV、数字化点、逐点对比、摘要、Markdown 和诊断 PNG 的 SHA256 均保持一致；加入 Chapter 4 fixed-time、周期接缝、STM 与 Fig. 5.10 BCR4BP 回归门后，`unittest discover` 42/42、54 图 smoke、目标表 `--check`、投影诊断 `--check` 和 `git diff --check` 均通过。
- Fig. 5.10 已新增 DE421 初始化的平面 Earth–Moon BCR4BP 两案例专用审计：项目历元为 `2020-06-15T00:00:00Z`，初始太阳相位 `1.2408947569934152 rad`，并修复太阳角速度归一化中遗漏的 `2*pi`。23 天与 12.4 天案例均通过独立重传播、容差散布、绝对时间分段和月面净空门，最大独立终端误差 `4.819078e-05 km`；错误地把每段时间重置为零会产生至少 `100.774 km` 缺陷，已作为非自治负对照保留。
- Fig. 5.10 的 BCR4BP 总脉冲分别为 `72.628142 m/s` 与 `89.049947 m/s`，相对论文总量误差为 `-9.7787%` 与 `+2.8290%`。因此数值扩展门为 `2/2`，论文等价门明确为 `0/2`；canonical 论文风格主图仍保留 CR3BP，BCR4BP 轨迹与误差只放入独立诊断 PNG/PDF。论文原案例是自主 CR3BP，历元不适用；`2020-06-15` 只属于项目扩展。
- 因为仍有 25 个图行带 boundary/open 条件，当前结论是“54/54 工程覆盖 + 可审计 source-layer”，不是完整论文数值等价复现；下一步优先按 `figure_validation_table.csv` 的 `next_action` 消化高影响 boundary。

## 4. 停止与切换规则

- 若连续多个批次无法保持 full-torus 正进度，先保存失败证据并调节步长、Jacobi 偏置和 z 修正；不放宽残差或网格门限。
- 若有界尝试后仍无法达到 `660,000/940,000 km`，将当前结果正式标为 `boundary`，再启动 Route B（Fourier/collocation torus BVP）或 Route A（原始数据/高分辨率图源检索），而不是把局部结果写成原图复现。
- 若 Route H 近实双曲扫描仍只有少数成员通过，保留复数 Fourier-shifted 模式和失败扫描作为 boundary；不得放宽 `1e-6` 门限或用复特征向量替代论文所需的实流形方向。下一轮优先把 `chapter3_route_h_fixed_time_target_states.csv` 的 N57/N81/N105 三个严格论文锚点接入跨 N 重校正/DG 扫描，并保留 member 68 为阳性控制；若仍失败则转向准周期 cocycle 的实不变子束求解。
- Chapter 5 的 Fig. 5.10 已完成上述 BCR4BP 专用数值扩展；论文原案例是自主 Earth-Moon CR3BP，因此历元不适用，`2020-06-15` 仅属于项目扩展。下一步不再追索不存在的“论文历元”，而是优先恢复 `rp=8065 km`、频率比 `5.0305` 的 constant-frequency quasi-NRHO 成员、交点相位、原始边界状态与优化约束，再校准两次脉冲分配。若无法获得论文边界条件，则永久保留 `paper_equivalence=false`，再把同样的非自治审计框架扩展到 Fig. 5.11 或其他高影响应用图。

## 5. 交付清单

每个阶段都必须留下：可重运行脚本、参数快照、CSV/NPZ、Markdown 审计、PNG/PDF、独立复核结果、Git 提交和失败/边界说明。最终报告必须同时给出“已严格复现的图”“边界图”“仍为代理的图”和下一步切换依据。
