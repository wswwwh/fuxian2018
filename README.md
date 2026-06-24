# McCarthy 2018 拟周期轨道论文复现工作说明与进度总结

## 1. 项目概述

本项目围绕 Brian P. McCarthy 2018 年博士论文 *Characterization of Quasi-Periodic Orbits for Applications in the Sun-Earth and Earth-Moon Systems* 展开复现。项目目标不是简单截取论文图片或进行静态重绘，而是建立一套可计算、可验证、可批量生成图像的数值复现管线，尽可能复现论文中关于 CR3BP 周期轨道、拟周期轨道、不变环面、稳定性、流形和任务应用场景的主要结果。

当前仓库已经形成一个较完整的 Python 复现工程：以 `mccarthy2018_reproduction/` 为核心目录，包含基础动力学模块、周期轨道与拟周期轨道算法、稳定性与流形计算、应用场景建模、批量出图脚本、参考图裁剪和结果输出目录。项目目前已经实现论文 54 张图的一版复现覆盖，并保留了 PNG、PDF 和对照检查结果，适合作为后续精细化数值复现和论文级图形比对的基础。

## 2. 复现目标

本项目的复现目标可以分为五层：

1. **CR3BP 基础动力学层**：实现归一化三体系统、Jacobi 常数、零速度曲线、平衡点、线性化、STM 和数值积分。
2. **周期轨道层**：实现 Lyapunov、halo、vertical、DRO、NRHO 等周期轨道的初值生成、微分校正、延拓、单值矩阵和稳定性分析。
3. **拟周期轨道层**：实现基于 stroboscopic mapping 的离散不变曲线、映射残差、相位约束、Newton 校正和不同参数约束下的拟周期轨道族延拓。
4. **稳定性与流形层**：构造离散不变曲线的映射微分矩阵 `DG`，计算特征值、稳定性指标，并沿稳定/不稳定方向传播流形面。
5. **任务应用层**：复现论文第五章中的 Sun-Earth L1、Earth-Moon quasi-DRO、NRHO 转移、月球遮挡规避、LEO 到 L1 Lissajous 转移初猜等应用图。

## 3. 仓库结构说明

当前仓库的主要结构如下：

```text
fuxian2018/
├── 2018_McCarthy_拟周期轨道.pdf
├── mccarthy2018_reproduction_plan.md
└── mccarthy2018_reproduction/
    ├── README.md
    ├── config.yaml
    ├── environment.yml
    ├── pyproject.toml
    ├── src/qp_orbits/
    │   ├── constants.py
    │   ├── cr3bp.py
    │   ├── libration_points.py
    │   ├── linear_modes.py
    │   ├── linearization.py
    │   ├── variational.py
    │   ├── periodic_orbits.py
    │   ├── quasi_torus.py
    │   ├── torus_stability.py
    │   ├── manifolds.py
    │   ├── ephemeris.py
    │   ├── corrected_dro_family.py
    │   ├── application_scenarios.py
    │   └── plot_style.py
    ├── scripts/
    │   ├── build_figure_index.py
    │   ├── fetch_de421.py
    │   ├── crop_reference_figures.py
    │   ├── validate_basics.py
    │   ├── reproduce_all_figures.py
    │   └── build_contact_sheets.py
    ├── data/
    │   ├── figure_index.csv
    │   ├── raw/
    │   └── computed/
    └── outputs/
        ├── reference_pages/
        ├── figures_png/
        ├── figures_pdf/
        └── comparison_contact_sheets/
```

其中，`src/qp_orbits/` 是核心算法层，`scripts/` 是批处理和验证脚本，`data/computed/` 保存中间数值结果，`outputs/` 保存最终图像和对照材料。

## 4. 已完成的主要工作

### 4.1 CR3BP 基础模块

已完成 CR3BP 归一化旋转坐标系下的基础动力学工具，包括：

- 主天体距离计算；
- CR3BP 伪势函数与梯度；
- 状态方程 `cr3bp_rhs`；
- Jacobi 常数计算；
- 零速度曲线网格；
- 单轨道与批量轨道积分；
- 高精度 `DOP853` 积分配置。

这一部分为后续所有周期轨道、拟周期轨道、流形传播和应用场景提供了共同动力学基础。

### 4.2 周期轨道与微分校正

已建立周期轨道的初值、数据结构和校正框架，包括：

- 平面 Lyapunov 轨道初值和单次打靶校正；
- 固定 `x` 的 Lyapunov 校正；
- Jacobi 目标约束下的 Lyapunov 校正；
- 平面 DRO 轨道校正；
- 固定 `z0` 的 3D 对称 halo-like / vertical-like 轨道校正；
- Jacobi 目标空间周期轨道；
- 单值矩阵、Floquet 乘子和稳定性指标；
- Jupiter-Europa、Earth-Moon L1/L2、NRHO 等周期轨道族基线。

这部分基本完成了第二章和后续拟周期算法所需的周期轨道基础。

### 4.3 拟周期轨道与不变环面

已实现 stroboscopic mapping 路线下的拟周期轨道核心框架，包括：

- 离散不变曲线种子生成；
- 固定目标 STM shooting；
- 固定旋转角曲线 Newton 校正；
- 自由旋转角 / 自由映射时间 / 固定平均 Jacobi 的曲线校正；
- pseudo-arclength 延拓；
- 定能量 quasi-halo / quasi-vertical 家族；
- 定频率比 Earth-Moon L2 quasi-halo / quasi-vertical 家族；
- 固定映射时间 quasi-DRO 局部轨道族；
- 高阶 Fourier / spectral lifting 的局部延拓尝试。

目前第三章图形已经全部获得一版输出，其中部分图已经从早期代理曲面升级为 CR3BP 修正后的数值结果。

### 4.4 稳定性和流形

已建立 Chapter 4 所需的稳定性分析基础：

- 离散不变曲线的 `DG` 映射微分矩阵；
- 特征值谱和稳定性指标；
- 局部稳定/不稳定特征向量；
- corrected-curve 局部流形面传播；
- quasi-halo 和 quasi-vertical 的局部不稳定流形；
- 部分全局 quasi-vertical 不稳定流形传播。

需要注意的是，第四章目前仍有一部分图保留 thesis-scale proxy 数据，原因是完整高振幅拟周期环面稳定性和全局流形传播尚未完全收敛到最终论文级版本。

### 4.5 第五章应用场景

已完成一版应用场景基线，包括：

- Sun-Earth L1 Lissajous / quasi-vertical 场景的 CR3BP 局部传播；
- Earth-Moon corrected resonant DRO 和 quasi-DRO 十次返回传播；
- JPL DE421 地月日状态读取与相位/历元变换；
- 月球本影和地球视线几何测试；
- Earth-Moon L2 halo 与 Lyapunov 等 Jacobi 边界；
- 40 段、186.9 天固定时间多段打靶转移基线；
- 4,800 km 和 12,610 km 北向 L2 NRHO 的固定 perilune 校正；
- 23 天和 12.4 天 NRHO 转移局部 direct-shooting 基线；
- Sun-Earth L1 到 LEO 半径目标的稳定流形扫描。

第五章目前处于“可解释数值基线 + 部分代理几何”的状态，还不是完整的高保真优化转移复现。

## 5. 复现进度总览

| 模块 | 当前状态 | 说明 |
|---|---:|---|
| PDF 文献整理与图谱 | 已完成 | 已建立 54 张图的复现索引，并生成参考页面与对照材料。 |
| CR3BP 基础动力学 | 基本完成 | 已实现动力学方程、Jacobi 常数、ZVC、平衡点、STM 和积分器。 |
| 周期轨道与延拓 | 基本完成 | Lyapunov、halo、vertical、DRO、NRHO 等主要周期轨道层已经可用于出图和后续拟周期种子。 |
| 第 2 章图形 | 一版完成 | 图 2.1–2.15 已覆盖，部分图已使用修正后的轨道族和稳定性结果。 |
| 第 3 章拟周期轨道 | 一版完成，核心部分已数值化 | 图 3.1–3.17 已覆盖；定能量和定频率部分已有较深入的修正结果，但定映射时间和高振幅尾段仍有代理成分。 |
| 第 4 章稳定性/流形 | 部分完成 | 已有 `DG` 和局部流形传播，但部分图仍依赖 thesis-scale proxy，需要后续替换。 |
| 第 5 章应用图 | 一版完成，非最终高保真 | 已有 CR3BP/DE421 基线和转移初猜，但 BCR4BP、星历多段修正和优化转移仍未最终完成。 |
| 批量出图管线 | 已完成 | `reproduce_all_figures.py` 已列出并运行 54 个图脚本。 |
| 输出结果 | 已完成一版 | 已生成 PNG、PDF 和 comparison contact sheets。 |

从覆盖率看，项目已经达到 **54/54 张论文图的一版复现覆盖**。从数值严格程度看，当前工作应定位为 **“第一层完整复现 + 多处核心数值升级 + 若干代理图待替换”**，而不是最终版完全复现。

## 6. 分章节进度

| 章节 | 图号范围 | 当前完成度 | 主要内容 |
|---|---|---|---|
| 第 2 章 | Fig. 2.1–2.15 | 高 | CR3BP 基础、平衡点、零速度曲线、周期轨道、稳定性和流形。 |
| 第 3 章 | Fig. 3.1–3.17 | 中高 | 不变曲线、stroboscopic map、quasi-halo、quasi-vertical、constant energy、constant frequency、quasi-DRO。 |
| 第 4 章 | Fig. 4.1–4.8 | 中 | `DG` 特征值、稳定性指标、局部稳定/不稳定流形；部分全局图仍需替换代理数据。 |
| 第 5 章 | Fig. 5.1–5.14 | 中 | 应用场景、DE421 坐标转换、quasi-DRO、月球遮挡、NRHO 转移、L1 到 LEO 稳定流形基线。 |

## 7. 已得到的代表性数值结果

当前 README 中记录了若干代表性进展，可作为阶段性成果：

- 第 3 章定能量 quasi-halo 分支已经从 `N=9` 扩展到 `N=15` 和 `N=21`，并覆盖到约 12.408 天映射时间。
- 12.398 天 quasi-halo 成员的曲线映射残差达到 `7.41e-11` 量级，平均 Jacobi 误差低于 `1.3e-14`，时间 Jacobi 漂移低于 `1.4e-15`。
- quasi-vertical staged continuation 已验证 103 个成员，映射时间覆盖约 `12.872136..12.664797` 天。
- Earth-Moon L2 定频率 quasi-halo 分支包含 30 个点式 Jacobi 修正成员，覆盖 `JC=3.1182..3.0011`。
- 第 5 章的 Earth-Moon halo/Lyapunov 转移基线已形成 40 段、186.9 天的固定时间多段打靶解，当前总速度增量为 291.776 m/s。
- 第 5 章 NRHO 转移基线中，4,800 km 和 12,610 km 北向 L2 NRHO 的稳定性指标分别接近论文值。

这些结果说明项目已经从“画图仿照”推进到“可计算轨道族 + 可检查残差 + 可复现实验管线”的阶段。

## 8. 当前不足与后续工作

当前主要不足集中在以下方面：

1. **代理图仍需替换**：部分 Chapter 4 流形图、Chapter 5 应用图仍使用几何代理或 thesis-scale proxy，后续需要用完整修正后的拟周期环面和流形数据替换。
2. **高振幅拟周期族仍需继续延拓**：部分 quasi-halo / quasi-vertical 分支尾段还没有完全达到论文尺度，需要继续推进高阶谱表示和稳健 continuation。
3. **BCR4BP 和星历模型尚未最终化**：第 5 章应用结果目前以 CR3BP 和 DE421 坐标变换基线为主，还不是完整 ephemeris-corrected 多段打靶结果。
4. **转移优化尚未达到论文最优值**：例如第 5.8 图当前局部基线的总速度增量仍高于论文优化结果，说明后续需要加入更强的优化约束和更完整的转移搜索。
5. **视觉一致性仍需调参**：当前项目优先保证数值可复算和物理一致性，部分图的视角、坐标范围、标签位置和论文原图仍需细调。
6. **自动化验证仍可增强**：建议后续增加 residual table、Jacobi drift table、monodromy/stability regression test 和图像差异度检查。

## 9. 推荐后续路线

后续可按以下顺序推进：

1. 固定当前 54 图接口，避免后续替换数值数据时破坏批量出图脚本。
2. 优先替换第 4 章仍使用 proxy 的 `DG` 稳定性和流形数据。
3. 继续推进第 3 章高振幅 quasi-halo / quasi-vertical continuation，使完整分支尽量覆盖论文参数范围。
4. 对第 5 章逐步引入 BCR4BP 或星历修正模型，先验证 quasi-DRO 遮挡与相位图，再处理转移优化。
5. 为每一张图建立“论文目标值—当前计算值—误差/残差—是否代理”的追踪表。
6. 最后统一图形风格、坐标比例、标注位置和论文原图视觉对照。

## 10. 如何运行当前复现

在 `mccarthy2018_reproduction/` 目录下，可以按 README 中的流程运行：

```powershell
conda run -n cislunar python scripts\build_figure_index.py
conda run -n cislunar python scripts\fetch_de421.py
conda run -n cislunar python scripts\crop_reference_figures.py
conda run -n cislunar python scripts\validate_basics.py
conda run -n cislunar python scripts\reproduce_all_figures.py
conda run -n cislunar python scripts\build_contact_sheets.py
```

生成结果主要位于：

```text
data/computed/
outputs/figures_png/
outputs/figures_pdf/
outputs/comparison_contact_sheets/
```

## 11. 阶段性结论

当前项目已经完成从论文阅读、图谱建立、基础动力学实现、周期轨道校正、拟周期轨道局部/家族计算、稳定性分析到应用场景基线的完整工程化框架。它已经能够批量生成论文全部 54 张图的一版复现结果，并在多处核心图中使用真实 CR3BP 校正轨道族、Jacobi 约束、STM、单值矩阵、`DG` 和多段打靶结果。

因此，本项目当前可以总结为：**图形覆盖已经完整，数值复现已经进入中后期；基础层和周期轨道层较成熟，拟周期环面、全局流形和高保真应用层仍是主要待攻关部分。**
