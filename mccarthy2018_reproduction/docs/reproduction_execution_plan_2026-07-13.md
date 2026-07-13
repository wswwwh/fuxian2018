# McCarthy 2018 后续复现执行计划（2026-07-13）

## 1. 总目标与当前判断

项目的最终目标是把 54 张图从“可生成/物理一致性”推进到“逐图可审计的论文级数值复现”。
本计划采用最严格的目标模式：只有存在可重运行脚本、显式参数、CSV/NPZ 数值证据、独立复核和图件审计时，结果才标记为 `accepted`；`diagnostic`、`boundary`、`proxy` 不得升级为论文结果。

当前事实基线（以仓库 CSV/Markdown 为准）：

- Chapter 3 Route H 已有超过 10,500 km 的图源层证据；混合 cold-start 可复核，但单体 cold-start 仍保留失败证据，不能声称所有路径完全可重建。
- Chapter 4 的原图级 DG/manifold 重建仍需从 Route H 高振幅源重新生成；近实双曲方向门控尚未全部通过。
- Chapter 5 已有 DE421/BCR4BP、转移和 stable-manifold 的 source-layer 基线，但 Fig. 5.13/5.14 所需的高振幅 Sun–Earth L1 两频环面仍未达到论文目标。

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

当前检查点（成员 244）为：全曲面 `max|y|=1,022,862.444 km`、`max|z|=945,560.790 km`，Jacobi span `5.917e-9`，闭合残差 `4.138e-9`，网格 `129 x 256`。因此数值残差已在门限内，但几何目标尚未完成。

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

### P3：重建 Chapter 4 原图级 DG/manifold

- 以 Chapter 3 Route H 接受成员为上游，重新计算 DG、特征值/特征向量、正负流形和快照。
- 逐成员要求近实双曲方向、eigenpair residual、determinant/reciprocity、Jacobi 漂移和传播方向一致；至少覆盖 3 个跨 2,000 km 的成员后，才允许升级 Chapter 4 状态。

### P4：逐图收尾与最终验收

- 按 `data/reproduction_targets.csv` 对 54 张图逐行更新 `figure_validation_table.csv`，区分 `accepted / boundary / diagnostic / proxy`。
- 重新生成 PNG/PDF、报告附录、教师版摘要和 artifact manifest；检查每一行是否能追溯到脚本、参数、数值文件和独立复核。
- 做一次从干净缓存/新进程的全量 smoke + 关键章节 full audit。只有总门槛全部通过才把项目标为完成；否则输出带边界的阶段性报告。

## 4. 停止与切换规则

- 若连续多个批次无法保持 full-torus 正进度，先保存失败证据并调节步长、Jacobi 偏置和 z 修正；不放宽残差或网格门限。
- 若有界尝试后仍无法达到 `660,000/940,000 km`，将当前结果正式标为 `boundary`，再启动 Route B（Fourier/collocation torus BVP）或 Route A（原始数据/高分辨率图源检索），而不是把局部结果写成原图复现。
- Chapter 5 应用图在上游环面和 Chapter 4 DG 门控未通过前，只能作为 source-layer/baseline；不得宣称已经完成论文级应用复现。

## 5. 交付清单

每个阶段都必须留下：可重运行脚本、参数快照、CSV/NPZ、Markdown 审计、PNG/PDF、独立复核结果、Git 提交和失败/边界说明。最终报告必须同时给出“已严格复现的图”“边界图”“仍为代理的图”和下一步切换依据。
