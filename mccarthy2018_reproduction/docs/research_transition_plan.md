# 从复现基线到 invariant-bundle 研究的切换计划

## 当前状态

- 阶段 A：完成。baseline v1、环境锁、架构图和只读生成器已通过完整回归。
- 阶段 B：完成，但结论为 negative/boundary，不代表各数值门通过。权威结论见 `data/computed/chapter4_invariant_bundle_stage_b_conclusion.csv`。
- 阶段 C：完成。已冻结 4 类轨道族、15 个 case，并把 Route H member 68 的 physical corrected-rho 与 frozen legacy-DG 正控制分开登记。
- 阶段 D：完成。traditional pointwise、ordered partial real-Schur 和 shifted QR/SVD 已进入 `src/qp_orbits/invariant_bundles.py`，一维/二维结果分开报告。
- 阶段 E：完成。45 个 case–method 结果中，pointwise 为 0 accepted，Schur 为 7 accepted/4 boundary/4 fail，QR/SVD 为 10 accepted/5 fail。
- 阶段 F：完成。7 个 case、3 类轨道族、3 个扰动尺度、正负两支，共 126 行同条件流形证据；高分辨率三族锚点通过，低分辨率全片距离失败保留。
- 论文材料：已生成 6 组 PNG/PDF 图、方法型初稿、双语摘要、贡献/限制/表格及 claim-evidence matrix；外部文献核验仍明确待办。

本计划服从 **计划与目标/codex_goal_invariant_bundles.md**。它不修改既有审计门槛。

## 阶段 A：复现基线冻结门

### 必需产物

- **docs/reproduction_baseline_v1.md**
- **docs/repository_architecture.md**
- **docs/research_transition_plan.md**
- **docs/reproducible_environment.md**
- **environment-lock.yml**
- **data/computed/reproduction_baseline_v1_lock.json**
- **data/computed/reproduction_baseline_v1_summary.csv**
- **data/computed/reproduction_baseline_v1_manifest.csv**
- **scripts/run_reproduction_baseline_freeze.py**

### 完成判据

1. baseline generator 的默认模式只能写上述派生 summary/manifest/Markdown，不能写 figure validation、staged gate 或 Chapter 4 holdout。
2. **run_reproduction_baseline_freeze.py --check** 通过，证明输入哈希、分类计数和冻结边界未漂移。
3. 单元测试全部通过。
4. target registry **--check** 通过。
5. 54 图 smoke 通过，仍报告 54 PNG、54 PDF、13 V0、41 V2。
6. Chapter 4 fixed-time 状态仍为 numerical pass，冻结 projection holdout 仍为 0/4；Route H real-hyperbolic 仍如实报告 1/31。
7. **git diff --check** 通过。

阶段 A 失败时只修复环境、路径、生成器或真实回归缺陷；不得修改 acceptance threshold、删除失败测试或改写 canonical CSV 来制造通过。

## 阶段 B：仅补齐 invariant-bundle 研究所需 Chapter 4 缺口

### B1 Halo 12.40-day source falsification

固定物理候选：

- JC = 3.1389
- T0 = 12.397983401715157 day
- 初始 N = 21
- Ay 约 41815 km
- Az 约 35783 km

只运行 N21、N33、N45 三个分辨率。成员在读取 red mask 前固定；camera、epsilon、crop、renderer、branch、snapshot time 和 threshold 全部沿用冻结设置。

输出：

- **data/computed/research_halo_12p40_resolution_audit.csv**
- **data/computed/research_halo_12p40_resolution_states.npz**
- **docs/research_halo_12p40_resolution_audit.md**

状态空间门保持：

- |T0-12.40| <= 0.005 day；
- |Ay-41815| <= 50 km，|Az-35783| <= 50 km；
- curve residual <= 1e-9，Jacobi span <= 1e-6；
- determinant error <= 5e-9，相对虚部 <= 1e-10；
- unstable-ring relative dispersion <= 6e-2；
- manifold Jacobi drift <= 1e-10；
- 相邻 N 的相对 multiplier 变化 <= 1e-3；
- phase-aligned principal angle <= 5 deg；
- normalized 3D snapshot HD95 <= 0.01。

开发投影门仍为 Chamfer/D <= 0.02、F1 >= 0.70、HD95/D <= 0.05、area ratio in [0.67, 1.50]；即使通过也不能改写 v1 holdout。

Campaign 上限：3 个 N case；N 最大 45；每个 corrector 最多 64 次迭代、最多 2 次数值重试；总 wall-time 8 小时；每完成一个 N 保存 checkpoint。若 residual 连续两个 resolution 不降或方向不可定义，停止并保存 fail/boundary。

### B2 Quasi-vertical N 收敛

固定当前约 12.6647965-day quasi-vertical member，不从 panel (d) 重新选成员。只比较 N33、N45、N57。

输出：

- **data/computed/research_vertical_12p66_resolution_audit.csv**
- **data/computed/research_vertical_12p66_resolution_states.npz**
- **docs/research_vertical_12p66_resolution_audit.md**

至少记录 curve residual、Jacobi span、selected bundle dimension、multiplier、eigen/subspace residual、phase-aligned principal angle、full-sheet 3D convergence、Jacobi drift 和 runtime。

Campaign 上限：3 个 N case；N 最大 57；每个 corrector 最多 64 次迭代、最多 2 次重试；总 wall-time 8 小时；每个 N 单独 checkpoint。若只能稳定得到二维实子空间，接受二维结果，禁止强投影到一维。

### B3 冻结负对照

按 one-factor-at-a-time 执行：

1. panel/time mapping；
2. red-mask extraction；
3. quad-union rasterizer；
4. plotted-surface renderer；
5. explicit STM transport 对照当前 transport 语义。

输出：

- **data/computed/chapter4_projection_semantics_negative_controls.csv**
- **data/computed/chapter4_projection_semantics_negative_controls.npz**
- **docs/chapter4_projection_semantics_negative_controls.md**

Campaign 上限：上述 5 类语义，每类至多 2 个实现变体；不新增 camera/epsilon/crop/threshold 搜索；总 wall-time 4 小时。负对照可以定位 semantic error，但不能修改 holdout 结论。

### B4 阶段结论与停止

必须从以下类别中给出一个或多个有证据的结论：

- source member；
- spectral resolution；
- pointwise eigenvector selection；
- renderer/projection semantics；
- original 3D state/perturbation unavailable。

即使所有新方法都失败，只要预注册 case 已运行、负结果和限制完整保存，阶段 B 也可判定“完成但结论为负”。禁止无边界调参。

## 阶段 B 完成门

只有同时满足下列条件才允许进入阶段 C：

1. Halo N21/N33/N45 与 vertical N33/N45/N57 的 CSV、NPZ、Markdown 完整。
2. phase alignment、principal angle、DG/bundle residual、3D sheet distance、Jacobi drift 和 runtime 均有数据。
3. 负对照生成器可重跑，且没有修改冻结 camera/fit/holdout 的哈希。
4. 明确的 B4 结论存在，failed/boundary 行没有被删除。
5. baseline freeze **--check** 仍通过。
6. unit tests、target **--check**、54 图 smoke、**git diff --check** 全部通过。

若任一项不满足，research/invariant_bundles 的 benchmark registry 仍保持 blocked。

## 阶段 C–F 顺序

### 阶段 C：benchmark registry

完成至少三类轨道族、六个 case。registry 只引用已有 CSV/NPZ/checkpoint，并记录 source residual、expected bundle type、正/负控制和 Git commit。

当前权威产物：

- **research/invariant_bundles/benchmarks/benchmark_registry.csv**：15 case、4 family；
- **research/invariant_bundles/benchmarks/benchmark_state_extracts.npz**：只含 Route H 和小振幅 Halo 的最小状态提取；
- **research/invariant_bundles/benchmarks/benchmark_provenance.md**：原始 artifact/hash/selection rule；
- **scripts/build_invariant_bundle_registry.py --check**：通过。

### 阶段 D：方法实现

先实现 traditional pointwise eigendecomposition baseline，再实现 real ordered Schur tracking 与 QR/SVD cocycle bundle iteration。原型先在 experiments，稳定且测试通过后才进入 **src/qp_orbits/invariant_bundles.py**。

当前实现与测试：

- **src/qp_orbits/invariant_bundles.py**；
- traditional pointwise eig 明确保留 complex-to-real 失败标签；
- ordered partial real-Schur 对复共轭对返回二维实子空间；
- shifted QR/SVD 在固定 200 次迭代上限内收敛或保留失败；
- residual、Schur 选择、phase/sign、phase permutation、N refinement、complex pair、manifold direction 单元测试均通过。

### 阶段 E：系统对比

统一记录 invariance residual、eigen/Schur residual、relative imaginary part、principal angle、cross-resolution angle、multiplier/Lyapunov estimate、flip、runtime、memory、acceptance 和 failure reason。

权威入口与输出：

- **scripts/run_invariant_bundle_benchmarks.py**；
- **research/invariant_bundles/results/csv/method_comparison.csv**；
- **resolution_convergence.csv**、**phase_continuity.csv**、**runtime_scaling.csv** 及对应 NPZ；
- `--check` 当前通过 15 case、45 method rows。

### 阶段 F：流形验证

至少 halo、vertical、Sun–Earth active geometry 或 Route H member 68 三组；相同 phase samples、perturbation norm、传播时长、积分器、坐标系、事件和停止条件。不得只凭图像判断。

当前权威入口与输出：

- **scripts/run_invariant_bundle_manifold_convergence.py**；
- **research/invariant_bundles/results/csv/manifold_convergence.csv**（126 rows）；
- **research/invariant_bundles/results/npz/manifold_convergence.npz**；
- **research/invariant_bundles/experiments/manifold_convergence/stage_f_audit.md**；
- Jacobi drift 最大值约 `2.22e-15`，未放宽 `1e-10` 门槛；
- Halo N21/N33、Vertical N33/N45 的 cross-N full-sheet distance 仍高于 `0.01`，因此保持失败；
- Route H physical corrected-rho 未得到 accepted 1D bundle，按切换规则使用 Sun–Earth member 468 作为第三族，未强行构造流形。

## 方法 campaign 停止规则

若一种方法在三个代表性 benchmark 上都不能改善 bundle residual、phase continuity、cross-resolution angle 和 manifold geometry convergence，则停止该方法，冻结负结果，转向另一种子空间方法。

一维实 bundle 不存在而二维实 invariant subspace 稳定存在时，结论必须是二维。原始论文数据不可得时，结论必须是 evidence boundary。

## 提交与证据隔离

- reproduction baseline/Stage B 证据与 research 方法实验分开提交和审计。
- 每个实验结果保存 config、source hash、Git commit、环境、runtime 和日志。
- 图是 CSV/NPZ 的派生物，不是 acceptance authority。
- 论文措辞只有在多 benchmark 证据支持时才可使用“提出新方法”；否则表述为“可靠数值框架和系统比较”。
