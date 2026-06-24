# McCarthy 2018 拟周期轨道论文复现计划

目标论文：Brian P. McCarthy, *Characterization of Quasi-Periodic Orbits for Applications in the Sun-Earth and Earth-Moon Systems*, Purdue University, 2018.

本计划的目标不是把 PDF 里的图截图重排，而是建立一套可以复算、可修改、可批量出图的代码管线，最后用统一风格仿照论文中的全部 54 张图。

## 1. 论文核心内容

这篇论文的主线是：

1. 在 CR3BP 中建立基础动力学、Jacobi 常数、线性变分、STM、微分校正、延拓、周期轨道稳定性和流形。
2. 用 Howell 和 Olikara 风格的 stroboscopic mapping 技术计算二维不变环面，即拟周期轨道族。
3. 对三类拟周期轨道族做延拓：定能量、定频率比、定映射时间。
4. 用离散不变曲线的映射微分矩阵分析拟周期轨道稳定性，并生成稳定/不稳定流形。
5. 把拟周期轨道用于 Sun-Earth 和 Earth-Moon 系统中的长期弧段、月球遮挡规避、NRHO 转移、LEO 到 Sun-Earth L1 Lissajous 的转移初猜。

因此复现顺序必须是“动力学基础 -> 周期轨道 -> 拟周期环面 -> 稳定性/流形 -> 应用图”，不能直接从第 5 章开始画。

## 2. 推荐代码组织

建议建立一个专门项目，例如：

```text
mccarthy2018_reproduction/
  README.md
  environment.yml
  src/qp_orbits/
    constants.py
    cr3bp.py
    frames.py
    libration_points.py
    jacobi.py
    variational.py
    shooting.py
    continuation.py
    periodic_orbits.py
    torus.py
    torus_stability.py
    manifolds.py
    ephemeris.py
    plot_style.py
  scripts/
    build_figure_index.py
    reproduce_all_figures.py
  figures/
    fig_2_01.py
    fig_2_02.py
    ...
    fig_5_14.py
  data/
    raw/
    computed/
    figure_params/
  outputs/
    figures_png/
    figures_pdf/
    comparison_contact_sheets/
```

环境建议：

- 主力开发环境：`D:\miniconda3\envs\cislunar`
- 需要 TudatPy 高保真/星历验证时：`D:\miniconda3\envs\orbit-tudat`
- 需要 PyKEP/Orekit/heyoka 实验时：`D:\miniconda3\envs\orbit-pykep`

这些环境最好保持分开。核心算法尽量写成纯 Python/NumPy/SciPy，这样可以在 `cislunar` 中稳定开发；复杂库只用于验证或补充。

## 3. 图形复现分层

### A 类：示意图，优先快速仿照

这些图主要是几何、流程或概念图，不依赖精确数值轨道。可以先用 Matplotlib 2D/3D、patch、箭头、透明面和注释快速重画。

- 2.1, 2.2, 2.9, 2.10, 2.12
- 3.1, 3.2, 3.3, 3.4
- 5.2, 5.3, 5.4

验收标准：布局、标签、箭头、颜色、视角和论文相似；数据不要求物理精确。

### B 类：CR3BP 基础数值图

这些图需要先实现 CR3BP 基础模块，但难度低于拟周期环面。

- 2.3, 2.4, 2.5, 2.6：平衡点、ZVC/ZVS、Jacobi 常数
- 2.7, 2.8：线性化 Lissajous/模态轨道
- 2.11, 2.13：周期轨道校正与轨道族
- 2.14, 2.15：周期轨道流形与稳定性指标

验收标准：坐标尺度、开口区域、轨道族趋势和论文一致；具体数值允许先近似，后续再收敛到论文参数。

### C 类：拟周期环面核心图

这是论文最关键也最难的部分，需要完成不变曲线离散、stroboscopic map、相位约束、Newton 校正和延拓。

- 3.5-3.9：定能量 quasi-halo / quasi-vertical 环面族和参数曲线
- 3.10-3.11：中心周期轨道、Poincare 映射
- 3.12-3.15：定频率比 quasi-halo / quasi-vertical 环面族
- 3.16-3.17：定映射时间 quasi-DRO 环面族

验收标准：先做到形态和趋势一致，再追求 Jacobi 常数、映射时间、频率比、振幅曲线与论文数值接近。

### D 类：拟周期稳定性和流形图

这些图依赖 C 类结果。要构造离散不变曲线映射微分矩阵 `DG`，求特征值/特征向量，再沿稳定/不稳定方向扰动并传播。

- 4.1：`DG` 特征值结构
- 4.2：稳定性指标随映射时间变化
- 4.3-4.8：quasi-halo / quasi-vertical 不稳定流形及与周期 halo 流形对比

验收标准：特征值环结构、稳定性曲线峰谷、流形管形态与论文一致。

### E 类：应用场景图

这些图最耗时，因为不仅需要动力学，还涉及任务几何、插入历元、NRHO 转移或近地转移假设。

- 5.1：Sun-Earth L1 quasi-vertical 长期传播
- 5.5-5.7：quasi-DRO、eclipse avoidance、不同相位/历元轨道
- 5.8-5.12：quasi-periodic trajectory arc 转移和 NRHO rendezvous
- 5.13-5.14：Sun-Earth L1 Lissajous 稳定流形到 LEO/P2 的应用

验收标准：第一版允许做 CR3BP/近似星历仿图；最终版再用 ephemeris 模型细化时间、历元和几何。

## 4. 阶段路线

### 阶段 0：建立图谱和验收表

已完成部分：

- 已提取全文文本。
- 已渲染 137 页 PDF 页面。
- 已确认论文共有 54 张图。
- 已做每章图页缩略图，便于后续逐图比对。

下一步：

1. 把 54 张图整理为 `figure_index.csv`。
2. 每张图记录：章节、页码、图类型、依赖模块、复现脚本、状态、是否需要精确数值。
3. 为每张图裁剪原图区域，作为视觉对照基准。

### 阶段 1：CR3BP 基础层

实现内容：

- 归一化单位和质量参数 `mu`
- 旋转坐标系下 CR3BP 方程
- Jacobi 常数
- 五个 libration points
- zero velocity curves / surfaces
- variational equations 和 6x6 STM
- 基础积分器、事件截面、坐标转换

优先复现图：

- 2.1-2.8

建议先从 Earth-Moon 系统做起，再扩展到 Sun-Earth、Saturn-Titan、Jupiter-Europa。

### 阶段 2：周期轨道、微分校正和延拓

实现内容：

- 单次打靶和多次打靶框架
- Lyapunov、halo、vertical、DRO 初值生成
- 周期轨道收敛
- natural continuation 和 pseudo-arclength continuation
- monodromy matrix、稳定性指标、周期轨道流形

优先复现图：

- 2.9-2.15

这一阶段完成后，后面拟周期环面的初始猜测和对照轨道才有来源。

### 阶段 3：拟周期轨道核心算法

实现内容：

- 用 `N` 个离散点表示不变曲线
- 对每个点积分一个映射时间 `T0`
- 旋转角 `rho` 下的相位重排/插值
- 不变性残差 `R(-rho) u(T0) - u(0)`
- 相位约束和参数约束
- Newton / least-squares 校正
- constant energy continuation
- constant frequency-ratio continuation
- constant mapping-time continuation

优先复现图：

- 3.1-3.17

建议顺序：

1. 先画 3.1-3.4 的概念示意。
2. 用小 `N` 验证单个 quasi-halo 环面。
3. 再做定能量族 3.5-3.9。
4. 最后做定频率比和定映射时间族 3.12-3.17。

### 阶段 4：拟周期轨道稳定性和流形

实现内容：

- 构造离散不变曲线的全局映射微分矩阵 `DG`
- 提取特征值环和实稳定/不稳定方向
- 稳定性指标 `nu`
- 沿特征向量扰动每个离散点
- 正向/反向传播稳定与不稳定流形

优先复现图：

- 4.1-4.8

这一阶段必须严格保存每次环面计算的状态、STM 和插值参数，否则后面无法稳定复现。

### 阶段 5：应用章节

实现内容：

- Sun-Earth L1 quasi-vertical 长期传播
- Earth-Moon quasi-DRO eclipse / LOS 几何
- quasi-periodic arc 用作转移初猜
- NRHO 到 NRHO 转移示意和收敛轨道
- Sun-Earth L1 Lissajous 稳定流形到 LEO/P2 的近似访问图

优先复现图：

- 5.1-5.14

注意：第 5 章很可能不能只靠论文正文完全复现全部精确数值，因为部分初始条件、历元、约束细节可能没有完全表格化。计划上应先完成“可解释的仿图”，再逐步用数值搜索把轨迹和论文靠近。

## 5. 54 张图的复现清单

| 图号 | 类型 | 第一版方法 | 依赖阶段 |
|---|---|---|---|
| 2.1 | 几何示意 | 2D/3D 箭头与旋转坐标示意 | 0 |
| 2.2 | 几何示意 | collinear points 几何关系 | 0 |
| 2.3 | 数值图 | Earth-Moon libration points | 1 |
| 2.4 | 数值图 | Jacobi ZVC 对比 | 1 |
| 2.5 | 数值图 | Earth-Moon ZVS/ZVC | 1 |
| 2.6 | 数值图 | 多系统 ZVC 对比 | 1 |
| 2.7 | 数值图 | L1 线性模态 | 1 |
| 2.8 | 数值图 | 线性 Lissajous 3D/projections | 1 |
| 2.9 | 流程示意 | single shooting 流程图 | 2 |
| 2.10 | 流程示意 | multiple shooting patch arcs | 2 |
| 2.11 | 数值图 | L2 Lyapunov 初值与收敛解 | 2 |
| 2.12 | 方法示意 | natural / pseudo-arclength continuation | 2 |
| 2.13 | 数值图 | Lyapunov/Halo/Vertical orbit families | 2 |
| 2.14 | 数值图 | L1 Lyapunov stable/unstable manifolds | 2 |
| 2.15 | 数值曲线 | Earth-Moon L2 halo stability index | 2 |
| 3.1 | 概念示意 | torus as product of two circles | 3 |
| 3.2 | 概念示意 | invariant curve and rotation angle | 3 |
| 3.3 | 概念示意 | 7-point invariant curve mapping | 3 |
| 3.4 | 概念示意 | multiple shooting patch curves | 3 |
| 3.5 | 核心数值 | constant-energy quasi-halo tori | 3 |
| 3.6 | 参数曲线 | quasi-halo amplitude curves | 3 |
| 3.7 | 核心数值 | constant-energy quasi-vertical tori | 3 |
| 3.8 | 参数曲线 | quasi-vertical amplitude curves | 3 |
| 3.9 | 参数曲线 | frequency ratio vs mapping time | 3 |
| 3.10 | 数值图 | period-2/3/8 halo examples | 3 |
| 3.11 | 数值图 | Poincare map and central periodic orbits | 3 |
| 3.12 | 核心数值 | constant-frequency quasi-halo tori | 3 |
| 3.13 | 参数曲线 | quasi-halo amplitude and Jacobi curves | 3 |
| 3.14 | 核心数值 | constant-frequency quasi-vertical tori | 3 |
| 3.15 | 参数曲线 | quasi-vertical Jacobi/time curves | 3 |
| 3.16 | 核心数值 | constant-time quasi-DRO tori | 3 |
| 3.17 | 参数曲线 | quasi-DRO amplitude and Jacobi curves | 3 |
| 4.1 | 稳定性 | `DG` eigenstructure | 4 |
| 4.2 | 稳定性曲线 | stability index vs mapping time | 4 |
| 4.3 | 流形 | quasi-halo unstable manifold +x | 4 |
| 4.4 | 流形 | quasi-halo unstable manifold -x | 4 |
| 4.5 | 流形 | quasi-vertical unstable manifold +x | 4 |
| 4.6 | 流形 | quasi-vertical unstable manifold -x | 4 |
| 4.7 | 流形对比 | quasi-halo vs periodic halo manifolds | 4 |
| 4.8 | 流形对比 | quasi-vertical vs periodic halo manifolds | 4 |
| 5.1 | 应用轨道 | Sun-Earth L1 quasi-vertical propagation | 5 |
| 5.2 | 几何示意 | Sun-Moon eclipse geometry | 5 |
| 5.3 | 几何示意 | Earth-Moon-spacecraft LOS geometry | 5 |
| 5.4 | 几何示意 | Sun-Earth-Moon synodic geometry | 5 |
| 5.5 | 应用轨道 | quasi-DRO and planar DRO returns | 5 |
| 5.6 | 应用轨道 | quasi-DRO ephemeris by phase | 5 |
| 5.7 | 应用轨道 | quasi-DRO ephemeris by epoch | 5 |
| 5.8 | 转移 | halo-to-Lyapunov transfer initial guess | 5 |
| 5.9 | 转移 | NRHO intersections with torus | 5 |
| 5.10 | 转移 | converged transfer trajectories 1/2 | 5 |
| 5.11 | 转移 | converged NRHO-to-NRHO transfer | 5 |
| 5.12 | 参数曲线 | rendezvous maneuver vs arrival time | 5 |
| 5.13 | 热力图 | periapsis heat map from stable manifolds | 5 |
| 5.14 | 转移 | LEO to Sun-Earth L1 Lissajous transfer | 5 |

## 6. 绘图风格规范

为了让全套图看起来像同一篇论文，先建立统一 `plot_style.py`：

- 字体：优先 Computer Modern / serif；数学标签使用 LaTeX 风格。
- 输出：PNG 300 dpi 和 PDF 矢量版各一份。
- 3D 图：统一视角、透明面、轨道线宽、主轨道颜色、辅助轨道颜色。
- 坐标轴：尽量保留论文中的轴标签、单位、投影方向。
- 图例：先仿论文布局，不强行现代化。
- 色彩：保留论文中的蓝、红、灰、黑、浅透明面风格。

每张图脚本开头记录：

```python
FIGURE_ID = "3.5"
SOURCE_PAGE = 68
REPRO_LEVEL = "shape-match"  # shape-match / numerical-match / final
SYSTEM = "Earth-Moon CR3BP"
NOTES = "First version uses recovered torus family from continuation."
```

## 7. 复现验收标准

每张图分三级验收：

1. V0：视觉仿照。布局、颜色、标签、视角接近论文。
2. V1：物理一致。轨道类型、动力学系统、Jacobi 常数/映射时间/频率比趋势一致。
3. V2：数值接近。关键参数尽量接近论文标注值，图形可以用于复现实验说明。

每个图脚本都要能独立运行，并且 `scripts/reproduce_all_figures.py` 可以一键重建全部图。

## 8. 最小可行启动顺序

建议从下面 8 个任务开始：

1. 建立项目目录和 `figure_index.csv`。
2. 裁剪 PDF 中的 54 张原图，生成对照图库。
3. 实现 CR3BP 方程、Jacobi 常数、libration points。
4. 复现 2.3、2.4、2.6，确认基础模型正确。
5. 实现 STM 和 single shooting，复现 2.11。
6. 实现 halo/Lyapunov continuation，复现 2.13、2.15。
7. 先用示意数据复现 3.1-3.4，固定环面图风格。
8. 开始 quasi-halo constant-energy torus，目标先复现 3.5 和 3.6。

完成这 8 步后，整篇论文复现的技术风险会大幅降低；剩下主要是扩展轨道族、补应用场景和批量绘图。

## 9. 主要风险

1. 论文不一定给出每张图的完整初值和所有约束参数，需要用延拓重新搜索。
2. 拟周期环面的 Newton 校正对初始猜测和相位约束很敏感，不能只靠普通轨道积分。
3. 第 5 章中的 ephemeris/历元图可能需要额外星历文件和假设，第一版应先做 CR3BP 仿图。
4. 3D 图的“像不像”很依赖视角、透明度、线宽和投影范围，必须逐图保存绘图参数。

## 10. 我建议的第一周目标

第一周不要直接冲第 3 章拟周期环面。更稳的目标是：

- 完成项目骨架。
- 完成 54 张图的裁剪和索引。
- 完成 CR3BP 基础模块。
- 复现 2.3、2.4、2.6、2.11 四类基础图。
- 建立统一绘图风格。

这样后面每新增一个数值模块，都能立即产出一组论文风格图片，而不是最后再补绘图。
