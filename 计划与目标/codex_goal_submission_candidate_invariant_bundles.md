# Codex 目标模式：将 invariant-bundle 研究推进到投稿候选级

## 1. 目标

在不改变 McCarthy 2018 冻结复现事实的前提下，把当前“可交导师评审、但不声明投稿就绪”的中文研究初稿，推进为可由导师决定目标期刊和投稿路线的 `submission-candidate` 证据包。

完成时必须同时具备：

1. 至少 3 个预注册稳定子束 benchmark；
2. 至少 2 个 Route H 二维实不变子空间及二维流形案例；
3. 至少 3 个预注册长事件传播案例；
4. 至少 3 个新增且相互独立的 Sun–Earth benchmark；
5. 每条科学主线对应的 CSV、NPZ、Markdown、配置、运行环境、源哈希、失败证据和回归测试；
6. 更新后的中文稿、英文稿、claim-evidence matrix、导师摘要和最终 acceptance audit；
7. 全量单元测试、baseline `--check`、target `--check`、54 图 smoke、所有新增生成器 `--check` 和 `git diff --check` 全部通过。

目标期刊选择、向导师或期刊发送材料、外部投稿不在本目标授权范围内。

## 2. 2026-07-21 起始基线

- 工作区：`C:\Users\wwh20\Desktop\复现论文`
- 活跃项目：`mccarthy2018_reproduction`
- Git：`main`，启动时工作树干净；本地 HEAD 为 `e39f479`
- 冻结复现：54/54 图，V0=13，V2=41；accepted=7，boundary=30，diagnostic=5，proxy=12
- Chapter 4：fixed-time 16/16；frozen projection holdout 0/4，`paper_projection=fail`，`paper_3d=false`
- Chapter 5 Fig. 5.10：BCR4BP 数值门 2/2；论文等价门 0/2
- 研究层：15 cases、4 families、3 methods；旧研究目标和导师交付目标均已完成
- 当前论文定位：`numerical_framework_and_systematic_comparison`；`not_submission_ready`
- 启动验证：baseline check、target check、smoke、`git diff --check` 全通过；全量 `195/195` tests 通过

上述状态是新目标的只读起点，不得被新研究结果自动升级或覆盖。

## 3. 不可修改的真实性边界

- 不把 54 图工程覆盖写成全文严格数值等价。
- 不修改 Chapter 4 v1 frozen holdout 的相机、裁剪、阈值、渲染器或结论。
- 不把 Route H 的二维实共轭子空间写成一维稳定/不稳定方向。
- 不以放宽阈值、删除失败行或选择性重跑提高通过率。
- 新结果进入独立 Stage H 权威链；不得覆盖 Stage A–G 的 CSV/NPZ、验收报告或哈希清单。
- 原作者未公开的数据继续标为 evidence boundary，不得用视觉拟合补造。

## 4. 阶段计划

### H0：基线复核与目标锁定

状态：已完成。

验收：工作树干净；baseline、target、smoke、全量测试和格式检查通过；Codex 目标已建立。

### H1：Stage H 预注册与隔离架构

建立独立目录和权威读取顺序，建议使用：

```text
research/invariant_bundles/submission_candidate/
  configs/
  benchmarks/
  results/csv/
  results/npz/
  audits/
  failure_evidence/
```

先审计当前 benchmark loader、cocycle 表示、Schur/QR 方法、流形传播器和 Stage F 生成器，再冻结：case ID、来源哈希、方向类型、子空间维数、相位样本、扰动尺度、传播时间、事件、积分器、阈值、最大迭代、重试数和 wall-time。H1 只登记配置和可重跑检查，不运行无边界搜索。

### H2：稳定子束基准

优先审计并预注册 3 个来源可靠的高分辨率案例：Earth–Moon halo、Earth–Moon vertical、Sun–Earth active geometry。实现稳定方向/子空间的明确传播语义，与现有不稳定方向分开登记。

每个 case 至少记录：source residual、bundle dimension、multiplier/Lyapunov estimate、cocycle residual、phase continuity、cross-resolution principal angle、稳定流形 Jacobi drift、几何收敛、runtime 和 failure reason。

投稿候选门：至少 2/3 个 case 达到预注册 stable-bundle 与短程稳定流形 acceptance；否则完成有界失败审计并停止该主线扩展。

### H3：Route H 二维实子空间与二维流形

选择 2 个预注册 physical corrected-rho case，至少包含 member 68 和一个明显复方向对照。保持 `bundle_dim=2`，研究二维实子空间的 transport、phase alignment 和二维扰动片传播；禁止投影为一维。

每个 case 至少记录：二维 Schur block residual、subspace principal angle、orientation/phase continuity、二维 sheet 初始线性误差、Jacobi drift、独立重积分、几何扩张/收缩和 failure reason。

投稿候选门：至少 1/2 个 physical case 在预注册阈值下形成可重复二维流形证据；若两者均失败，保存 bounded negative result 并请求是否转向算子语义论文。

### H4：长事件传播

从 H2/H3 中选定 3 个已完成子束案例，固定事件和时间窗，比较短程门与长事件门。禁止在看到结果后改变事件定义。

至少记录：event hit、传播时间、Jacobi drift、离开线性邻域时间、sheet self-intersection/degeneracy 指标、cross-resolution distance、独立重积分误差和 runtime。

投稿候选门：至少 2/3 个案例产生可解释、可重复的长事件证据；失败必须区分积分失败、事件未命中、bundle 失败和几何不收敛。

### H5：新增 Sun–Earth 独立案例

从已冻结的 Sun–Earth family/checkpoint 中按预注册规则选取至少 3 个不与 member 468 重复的案例。不得按方法结果挑选成员。对三种方法重复 bundle、分辨率、流形和独立重跑审计。

投稿候选门：3/3 完整运行，至少 2 个案例给出 accepted 或有物理解释的 boundary；保留所有 fail 行。

### H6：论文与导师材料升级

仅从 Stage H 权威 CSV/NPZ 生成新图表和文字：

- 更新中文稿并生成英文稿；
- 更新 claim-evidence matrix、limitations、失败分类和可重复性说明；
- 增加稳定子束、二维 Route H、长事件传播和 Sun–Earth 扩展章节；
- 更新 4 页导师摘要和 3–5 个明确审阅问题；
- 明确区分 `submission_candidate_ready` 与 `bounded_extension_complete_not_submission_ready`。

### H7：最终独立验收

在全新进程或隔离工作树中运行 Stage H 全链路，比较 authoritative 与 fresh outputs，生成最终 acceptance CSV/NPZ/Markdown、哈希清单、环境记录、命令结果和失败证据。

只有 H2–H5 的数量门、最低科学门和 H6–H7 的工程门全部满足，才可标记 `submission_candidate_ready`。否则保留为 `bounded_extension_complete_not_submission_ready`，不把目标缩小为文档完成。

## 5. 执行顺序与停止规则

执行顺序固定为 `H0 -> H1 -> H2 -> H3 -> H4 -> H5 -> H6 -> H7`。后续阶段可读取前序 accepted/boundary 结果，但不得覆盖前序事实。

每个 campaign 必须预先给出最大 case 数、最大分辨率、最大迭代次数、最大重试数、wall-time 和 checkpoint。若同一方向在 3 个代表案例的有界预算内均不能改善 residual、phase continuity、cross-resolution angle 或 manifold geometry，则停止，保存负结果，并请求用户决定是否转向。

## 6. 每阶段验证

至少运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
D:\miniconda3\envs\cislunar\python.exe -m unittest discover -s tests -v
D:\miniconda3\envs\cislunar\python.exe scripts\run_reproduction_baseline_freeze.py --check
D:\miniconda3\envs\cislunar\python.exe scripts\build_reproduction_targets.py --check
D:\miniconda3\envs\cislunar\python.exe scripts\validate_reproduction_smoke.py
git diff --check
```

新增 Stage H 生成器必须同时支持生成模式和只读 `--check` 模式，并有针对内容漂移、换行可移植性、失败行保留和冻结边界不变的测试。
