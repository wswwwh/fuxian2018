# McCarthy 2018 复现阶段汇报 PPT 大纲

用途：组会 / 开题阶段汇报。建议采用 15 页，风格以“证据优先的实验室报告”为主，不做完整数值复现的过度声明。核心措辞应保持为：当前项目已形成论文级复现报告包和 54 图一版覆盖，但不是 complete McCarthy 2018 numerical reproduction。

## Slide 1. McCarthy 2018 拟周期轨道论文复现阶段汇报

- slide title：McCarthy 2018 拟周期轨道论文复现阶段汇报
- key message：本轮汇报的是 Route C 报告包与审计链条，不是宣布完成完整数值复现。
- suggested figure/table：标题页可放 Fig. 3.16/3.17 对照缩略图、54 图 contact sheet 或当前报告包文件列表。
- speaker notes：先明确边界：项目已经覆盖论文 54 张目标图，并形成主报告、逐图状态、数值审计、proxy 使用和 future work 附录；但 Fig. 3.16/3.17 仍为 partial physical-consistency baseline，Chapter 5 仍是 baseline/proxy 层。

## Slide 2. 研究背景：CR3BP、QPO、quasi-DRO 的意义

- slide title：为什么关注拟周期轨道与 quasi-DRO
- key message：McCarthy 2018 的核心价值在于把 CR3BP 中的二维不变环面、稳定性与任务应用连接起来。
- suggested figure/table：Fig. 2.1/2.2 概念图、Fig. 3.1 torus schematic、Fig. 5 应用场景缩略图。
- speaker notes：解释 CR3BP 是复现的基础模型，QPO 是周期轨道之外的重要任务设计对象；quasi-DRO 连接 Earth-Moon 系统中的共振 DRO、长期相位结构和后续应用场景。这里不需要讲完整公式，重点说明为什么仅画出相似图像不足以支持复现结论。

## Slide 3. 复现目标：不是只画图，而是建立数值审计链条

- slide title：复现目标从“画图”升级到“可审计”
- key message：每张图都应能说明数据来源、残差、Jacobi 一致性、周期性或稳定性证据，以及是否使用 proxy。
- suggested figure/table：审计指标表：residual evidence、Jacobi evidence、periodicity evidence、stability evidence、proxy evidence。
- speaker notes：强调当前报告包采用逐图分级，不用视觉相似度代替数值复现。可信结论来自可追溯 CSV、校正残差、Jacobi drift、DG eigenstructure 和明确 proxy 边界。

## Slide 4. 项目结构与 54 图覆盖

- slide title：工程化复现结构与 54 图一版覆盖
- key message：项目已经形成从动力学模块、数据表、图脚本到报告附录的完整工程框架。
- suggested figure/table：仓库结构图；`figure_status_appendix.md` 的 status summary 表；54 图 contact sheet。
- speaker notes：说明 `src/qp_orbits/` 支撑动力学、周期轨道、拟周期轨道、稳定性和应用场景；`data/computed/` 存放当前数值证据；`outputs/figures_png/` 和 `outputs/comparison_contact_sheets/` 存放图像结果。本轮不重新生成 figures，不修改 CSV。

## Slide 5. 复现等级体系

- slide title：复现等级：从 numerical reproduction 到 proxy
- key message：当前 54 图分类为 16 张 numerical reproduction、6 张 physical-consistency baseline、2 张 partial baseline、17 张 local overlay、13 张 proxy/schematic only。
- suggested figure/table：`figure_status_appendix.md` 的五类统计表。
- speaker notes：解释五类标签的含义。numerical reproduction 是当前最强证据；physical-consistency baseline 表示物理链条可信但不等同 thesis 原始数值；shape-match with local numerical overlay 不能当成完整复现；proxy/schematic only 只承担概念或视觉参考。

## Slide 6. Chapter 2 基础层结果

- slide title：Chapter 2：CR3BP 与周期轨道基础层
- key message：基础动力学、平衡点、零速度曲线和部分周期轨道基线较成熟，可作为后续 QPO 审计的支撑层。
- suggested figure/table：Fig. 2.3、2.4、2.6、2.11、2.14、2.15；或 Chapter 2 逐图状态摘表。
- speaker notes：可强调 Chapter 2 中多张图已归为 numerical reproduction，例如 libration point、zero-velocity contours、Lyapunov/halo/NRHO baseline 等。也要指出部分图是 schematic，不需要被包装成数值复现。

## Slide 7. Fig. 3.10 period-q halo 审计

- slide title：Fig. 3.10：period-q halo 局部复现与 q=8 风险
- key message：q=2、q=3 有较强局部数值证据；q=8 只能作为 unstable multiple-shooting local approximation，不能称为 robust periodic orbit。
- suggested figure/table：Fig. 3.10；q=2/q=3/q=8 审计表，包含 closure、Jacobi drift、resonance angle error。
- speaker notes：q=8 的 patch residual 和 terminal symmetry 可到 roundoff，但 full-period single integration closure error 为 `3.906984451743337`，max monodromy multiplier magnitude 为 `3.431052642945378e+16`。汇报时要把“局部多段打靶一致”与“单弧稳健周期轨道”区分开。

## Slide 8. Chapter 4 DG manifold 审计

- slide title：Chapter 4：DG manifold 的物理一致性基线
- key message：Chapter 4 已有 corrected source curves、DG eigenvector propagation 和 Jacobi drift 证据，但仍不是 thesis-scale global manifold reproduction。
- suggested figure/table：Fig. 4.3-4.8；Chapter 4 manifold audit table。
- speaker notes：重点讲 source residual 约 `9.32e-10` 或 `2.03e-10`，Jacobi drift 约 `1e-15` 到 `1e-14`，局部增长率和 DG 预测基本吻合。但图中 proxy backgrounds / grey references 仍存在，dense global manifold sheet 尚未完成。

## Slide 9. Chapter 3 quasi-DRO 审计与 extension

- slide title：Chapter 3 quasi-DRO：已完成的审计链条
- key message：当前 quasi-DRO 已完成 local validation、fixed-mapping extension、PALC diagnostic、`N=61` lift 和 rejected candidate 诊断。
- suggested figure/table：Fig. 3.16/3.17；quasi-DRO accepted range 表。
- speaker notes：说明已接受分支的核心证据：displayed corrected branch 约 rho `1.4312..1.4438 rad`，PALC accepted member 到 rho `1.443877875293695 rad`，最大 `max_abs_z = 10164.02309965055 km`。这些证据支持 partial physical-consistency baseline，但不足以升级为完整复现。

## Slide 10. quasi-DRO 10,000-11,000 km bottleneck

- slide title：10,000-11,000 km 瓶颈：不是简单提高谱阶
- key message：没有 accepted member 超过 10,500 km 或 11,000 km；`N=61` 降低 Fourier tail，但没有突破 branch。
- suggested figure/table：accepted vs rejected diagnostics 表；11,000/12,000/14,000 km target residual 表。
- speaker notes：报告关键负面证据：11,000 km target residual `4.227e-04`、12,000 km residual `1.026e-02`、14,000 km residual `2.369e-02`；fixed-rotation rho 1.4465 candidate 可到 `11188.08244697768 km`，但 residual `7.841846983001098e-02`、Jacobi span `1.814140488309413e-03`，因此不能接受。

## Slide 11. 为什么 Chapter 5 暂不升级

- slide title：Chapter 5 应用层仍保持 baseline/proxy
- key message：Chapter 5 依赖可靠的 high-amplitude quasi-DRO branch；当前若升级会把 rejected candidate 或 proxy trend 传递到应用结论中。
- suggested figure/table：Chapter 5 图分类表；Fig. 5.5-5.14 状态摘表。
- speaker notes：说明 Chapter 5 中有 CR3BP baseline、DE421-oriented baseline、local direct-shooting baseline 和 proxy corridor，但还不是 BCR4BP / ephemeris optimized transfer reproduction。当前应展示应用方向，而不是把应用层作为完整数值复现成果。

## Slide 12. 外部资源与原始数据缺口

- slide title：原始数据缺口：没有公开 branch data
- key message：目前尚未找到 McCarthy 2018 的公开 branch data、initial states、appendix tables、official code 或 thesis-specific supplement。
- suggested figure/table：外部资源优先级表：Hammer thesis、Howell page、AAS papers、Olikara/Howell 2010、JPL API、digitization fallback。
- speaker notes：强调 JPL periodic orbits API 只能验证周期轨道 baseline，不提供 McCarthy quasi-periodic torus branch。Route A 应继续有限搜索和记录负面证据，找不到原始数据时再进入可追溯 digitization。

## Slide 13. 下一步路线 A/B/C

- slide title：下一阶段路线：A 找数据，B 改 formulation，C 完善报告
- key message：Route A 解决原始数据对照，Route B 解决 quasi-DRO formulation bottleneck，Route C 服务组会/开题/论文准备。
- suggested figure/table：A/B/C 对比表，列 objective、inputs、success criteria、stop condition。
- speaker notes：建议把 Route A 作为短周期、低风险的有限搜索；Route B 作为高成本算法研究，不应在未定义 residual equations、continuation variables、phase constraints 和 thresholds 前开写；Route C 已基本形成可展示材料。

## Slide 14. 硕士研究可切入问题

- slide title：硕士研究切入点：从复现包到可发表问题
- key message：当前最有研究价值的问题是“拟周期轨道复现的审计体系”和“quasi-DRO continuation bottleneck 的 formulation replacement”。
- suggested figure/table：研究问题矩阵：问题、现有基础、风险、最小成果、可能投稿方向。
- speaker notes：可提出三个方向：一是 McCarthy 2018 复现审计框架与数据缺口报告；二是 quasi-DRO fixed-mapping failure 的诊断和替代 formulation；三是 Chapter 4/5 在可靠 branch 之后的任务设计扩展。所有方向都要避免声称已完整复现 McCarthy 2018。

## Slide 15. 结论

- slide title：结论：可汇报、可审计，但尚未 complete reproduction
- key message：当前成果是论文级复现报告包和 54 图一版覆盖；最大未完成缺口是原始数据、quasi-DRO 10,500/11,000 km 审计、Chapter 4 global sheets 和 Chapter 5 高保真应用层。
- suggested figure/table：最终状态 summary：16 / 6 / 2 / 17 / 13 分类统计 + 三个 next actions。
- speaker notes：用克制结论收束：本项目已经从“能生成图”推进到“能说明每张图的证据等级”。下一步建议先完成 Route A 有边界搜索日志和关键图 digitization 决策，再决定是否立项 Route B formulation replacement。
