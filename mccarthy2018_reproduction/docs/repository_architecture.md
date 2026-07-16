# 仓库架构与状态权威图

## 目的

本文件规定复现层、共享数值库和原创研究层的职责边界。它是架构和治理说明，不产生新的科学结论；逐图状态仍必须从 CSV gate 读取。

当前仓库保持原有目录和脚本路径。阶段 A/B 不大规模移动文件，也不把历史产物重新命名为研究结果。

## 三层职责

| 层 | 主要路径 | 职责 | 允许依赖 | 禁止事项 |
|---|---|---|---|---|
| reproduction layer | **figures/**、**scripts/** 中现有复现入口、**data/computed/**、**outputs/figures_png/**、**outputs/figures_pdf/**、**docs/reproduction_report/** | 重建 McCarthy 图、生成 canonical CSV/NPZ、运行原有审计和报告渲染 | shared numerical library；冻结的论文源和配置 | 直接消费 research 结果后自动升级原图状态；手改 canonical CSV；按 holdout 调参 |
| shared numerical library | **src/qp_orbits/** | CR3BP/BCR4BP、校正、延拓、STM、DG、投影及将来的通用 invariant-bundle 实现 | NumPy/SciPy 等显式依赖；无图号特定硬编码 | 把论文图 panel、mask 或 camera 逻辑混入通用算法；在模块导入时写产物 |
| research layer | 规划路径 **research/invariant_bundles/** 和 **scripts/run_invariant_bundle_benchmarks.py** | benchmark registry、方法原型、对比实验、收敛证据、研究图表和论文草稿 | 只读引用 reproduction/shared artifacts；稳定算法可经测试后提升到 shared library | 在阶段 A/B 未过门时发布研究结论；复制大型数据；写回 figure_validation_table；隐藏失败行 |

依赖方向固定为：

    research layer -> shared numerical library
    research layer -> read-only reproduction benchmark artifacts
    reproduction layer -> shared numerical library

reproduction layer 不得依赖 research layer。若研究方法将来用于复现图，必须通过单独 promotion audit，明确更新生成脚本、证据表、边界和回归测试。

## 当前文件地图

### 复现入口

- **figures/fig_x_xx.py**：54 图现有生成接口；阶段 A/B 保持路径不变。
- **scripts/build_reproduction_targets.py**：目标表生成/一致性检查。
- **scripts/validate_reproduction_smoke.py**：54 图、关键 gate 和边界 smoke。
- **scripts/run_reproduction_baseline_freeze.py**：只读汇总 canonical 状态并生成 baseline v1 派生物；不得修改 canonical CSV。
- **scripts/run_mccarthy2018_staged_goal_gate_audit.py**：现有分阶段 gate 生成入口。

### 共享数值实现

- **src/qp_orbits/cr3bp.py**、**variational.py**、**linearization.py**：动力学和 STM。
- **src/qp_orbits/quasi_torus.py**、**torus_stability.py**：拟周期曲线、DG 和当前点式特征结构。
- **src/qp_orbits/chapter4_projection.py**、**chapter4_camera.py**、**chapter4_reproduction_lock.py**：冻结投影语义、相机和保护锁。
- **src/qp_orbits/invariant_bundles.py**：阶段 D 已新增；只含经过正/负控制和单元测试的通用实子束算法。

### 研究层（已建立）

阶段 A/B 已完成，**research/invariant_bundles/** 已按阶段 C–F 建立：

- **configs/** 只保存显式、可版本化参数；
- **benchmarks/benchmark_registry.csv** 只引用已有 authoritative CSV/NPZ/checkpoint；
- **experiments/** 保存方法原型，不供 reproduction layer 导入；
- **results/csv/**、**results/npz/**、**results/logs/** 保存带 case、参数、方法、Git commit 和失败原因的产物；
- **paper/** 只从研究结果表生成结论，不从图片外观推断数值优势。
- **figures/research_figure_manifest.csv** 记录 6 组 PNG/PDF 图的 source hash；图仍不是 acceptance authority。

## 状态权威优先级

状态判断必须按下列顺序读取；低层级不得覆盖高层级：

1. **data/computed/mccarthy2018_staged_goal_gate_status.csv**：跨章 gate。
2. **data/computed/figure_validation_table.csv**：54 图 canonical 当前状态。
3. **data/computed/figure_evidence_gap_audit.csv**：保守 accepted/boundary/diagnostic/proxy 分类。
4. Chapter 4/5 per-figure、holdout、独立重跑等专用 CSV/NPZ。
5. **data/computed/reproduction_baseline_v1_summary.csv** 与 **reproduction_baseline_v1_manifest.csv**：阶段 A 冻结快照和哈希。
6. 由上述数据生成的 Markdown。
7. README、项目索引、教师包和旧阶段报告：导航、汇报或历史背景，不是数值真值。

上述 1–7 是 reproduction 权威链。独立 research 权威链为：

1. **research/invariant_bundles/benchmarks/benchmark_registry.csv**；
2. **research/invariant_bundles/results/csv/method_comparison.csv**；
3. **research/invariant_bundles/results/csv/manifold_convergence.csv**；
4. 对应 NPZ、run summary 和 checkpoint；
5. 由这些表生成的 figure manifest、paper 与 claim-evidence matrix。

research accepted 不得覆盖 reproduction fail/boundary。

任何新状态文字必须同时给出上游 CSV/NPZ 路径。若 Markdown 与 CSV 冲突，以 CSV 和生成器为准，并把 Markdown 标为 stale 后修复。

## 当前 authoritative data

| 主题 | 权威文件 | 解释边界 |
|---|---|---|
| 54 图目标 | **data/reproduction_targets.csv** | V0/V2 目标和参数提取；不是科学 acceptance |
| 逐图数值状态 | **data/computed/figure_validation_table.csv** | canonical 逐图状态；只能经生成/审计更新 |
| 保守缺口分类 | **data/computed/figure_evidence_gap_audit.csv** | 派生分类；不新增科学主张 |
| 跨章进度 | **data/computed/mccarthy2018_staged_goal_gate_status.csv** | 允许/阻断下一复现阶段 |
| Chapter 4 原图 | **data/computed/chapter4_per_figure_source_layer_audit.csv** 及专用 fixed-time CSV/NPZ | source layer 与 paper equivalence 分开 |
| Chapter 4 投影 | camera protocol、fit lock、projection holdout CSV | v1 holdout 失败不可回调 |
| Chapter 5 | per-figure CSV 与 active-geometry/独立重跑审计 | CR3BP/扩展数值通过不等于论文模型等价 |
| 基线 v1 | **reproduction_baseline_v1_summary.csv**、**reproduction_baseline_v1_manifest.csv** | 当前冻结快照；未来研究不得覆盖 |
| Invariant-bundle registry | **research/invariant_bundles/benchmarks/benchmark_registry.csv**、**benchmark_provenance.md** | research case/来源/hash；不改变原图状态 |
| Bundle 方法 | **research/invariant_bundles/results/csv/method_comparison.csv** 及对应 NPZ | 15 case × 3 method 的 research-only 门 |
| 流形收敛 | **research/invariant_bundles/results/csv/manifold_convergence.csv** 及对应 NPZ | 7 case、3 扰动尺度、两分支；低 N 失败保留 |

## Legacy / deprecated status 索引

以下文件保留以追溯历史，但不得直接推断当前状态：

| 文件或区域 | 状态 | 使用规则 |
|---|---|---|
| **docs/stage_report_reproduction_status.md** | historical snapshot | 仅追溯旧阶段叙述 |
| **docs/next_reproduction_roadmap.md** | historical pre-Route-H snapshot | 不作为当前路线或数值来源 |
| **docs/next_reproduction_execution_plan_2026-07-11.md** | superseded plan | 当前计划以 2026-07-13 execution plan 和本目标文件为准 |
| **docs/chapter3_quasi_dro_validation.md** 的 older continuation sections | mixed historical content | Route H 当前值以 accepted validation/gate CSV 为准 |
| **docs/project_index.md** 的旧数值 guardrails | navigation-only and partially stale | 只使用其目录导航；数值转到 baseline/CSV |
| **README.md** 的长篇历史进度段 | mixed summary | 顶部状态提示和运行入口可用；任何数字必须回查 CSV |
| **docs/reproduction_report/future_work_plan.md** | historical Route A/B/C planning context | 不得覆盖 invariant-bundle 阶段 A–F |

“legacy”不等于删除。所有历史正结果、负结果和失败原因继续保留，但必须带时间和权威层级。

## Promotion 与写入规则

1. 原型只写入 **research/invariant_bundles/experiments/**。
2. 方法通过正/负控制、残差和 N 收敛测试后，才可进入 **src/qp_orbits/invariant_bundles.py**。
3. 研究 benchmark 只引用状态/数组，不复制大型 checkpoint。
4. 研究结果永远先写 **research/invariant_bundles/results/**。
5. 若要改变 reproduction 状态，必须另开 promotion audit：预声明门槛、独立重跑、更新 canonical 生成器、同步 per-figure audit、回归 54 图 smoke。
6. 未经 promotion audit，research 的 accepted 只表示“研究方法门通过”，绝不表示“McCarthy 原图 accepted”。

## 保护矩阵

- 不删除现有 reproduction artifacts。
- 不手改 authoritative accepted CSV。
- 不改变冻结 Chapter 4 v1 holdout、camera、epsilon、crop、renderer 或 threshold。
- 不把 post-hoc panel 比较包装为 blind holdout。
- 不把二维实不变子空间称为一维实 stable/unstable direction。
- 不把 Route H derived figure 称为原 Fig. 4.3–4.8 replacement。
- 不依据视觉相似升级结论。
- 不把研究实现继续堆入 figure scripts。
- 所有 failed/boundary 行与停止原因必须保留。

## Provenance 最低字段

研究 registry 和结果表至少记录：case_id、family、member_id、system、mu、energy/Jacobi、mapping time、rho、spectral samples、source artifact、source residual、method、method options、Git commit、运行环境、runtime、acceptance、failure reason。

NPZ 必须有 schema/version 元数据或配套 CSV；Markdown 只能解释 CSV/NPZ，不得成为唯一数值证据。
