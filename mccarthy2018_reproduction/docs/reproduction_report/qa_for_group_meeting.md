# 组会 / 开题问答稿

本问答稿用于汇报时控制表述边界。默认立场：当前工作是论文级复现报告包和 54 图一版覆盖，不是 complete McCarthy 2018 numerical reproduction。

## Q1. 这个项目现在到底完成了什么？

完成了 McCarthy 2018 论文 54 张目标图的一版覆盖，并把结果整理成可审计报告包：主报告、逐图状态附录、数值审计附录、proxy 使用附录和 future work plan。更重要的是，项目已经为每张图标注了当前复现等级、数据来源和主要限制。

## Q2. 为什么不能说完全复现 McCarthy 2018？

因为完整数值复现需要原始分支数据、初值、表格或等价的高保真数值结果作为对照。当前尚未找到 McCarthy 原始 branch data 或 official code；Fig. 3.16/3.17 的 quasi-DRO accepted branch 也没有通过 10,500 km 或 11,000 km 审计。因此只能说完成了论文级报告包和阶段性复现覆盖。

## Q3. 54 张图中哪些最可信？

最可信的是标为 `numerical reproduction` 的 16 张图，主要集中在 CR3BP 基础、零速度曲线、平衡点、部分周期轨道族和若干 Chapter 3 corrected numerical family。这些图的数据链条相对清楚，且不依赖 proxy。

## Q4. 哪些图还依赖 proxy？

主要包括 schematic 图、Chapter 3 的 Fig. 3.9/3.10/3.11 局部 overlay，Fig. 3.16/3.17 的 grey proxy surfaces/trends，Chapter 4 的 Fig. 4.1-4.8 中 proxy/grey reference，以及 Chapter 5 的多个应用层 proxy corridor 或 local overlay。

## Q5. Fig. 3.10 的 q=8 为什么不算 robust periodic orbit？

q=8 的 multiple-shooting patch residual 和 terminal symmetry residual 很小，但 full-period single integration closure error 为 `3.906984451743337`，说明单弧传播不能闭合。它更适合描述为 highly unstable multiple-shooting local approximation，而不是稳健的 single-shoot periodic orbit。

## Q6. q=2 和 q=3 是否更可靠？

相对更可靠。q=2 和 q=3 的 resonance angle error、multiple-shooting residual、Jacobi drift 和 full-period closure 都支持局部数值近似。但它们仍未与 McCarthy 原始 branch states 或 thesis table data 精确对照，所以仍保持 `shape-match with local numerical overlay`。

## Q7. Chapter 4 为什么只能算 physical-consistency baseline？

Chapter 4 的 source curves、DG eigenvector propagation、growth ratio 和 Jacobi drift 有审计证据，说明物理链条是可信的。但 Fig. 4.3-4.8 仍保留 proxy backgrounds 或 grey references，并未完成 thesis-scale continued torus family 上的 dense global manifold sheets。

## Q8. Chapter 4 最强的证据是什么？

最强证据是 corrected source curve residual、DG mapping 和 Jacobi drift。例如多张图的 source residual 约 `9.32e-10` 或 `2.03e-10`，Jacobi drift 接近 `1e-15` 到 `1e-14`，局部传播趋势与 DG 预测相符。

## Q9. Fig. 3.16/3.17 为什么卡在 10,000-11,000 km？

当前 accepted quasi-DRO branch 最大只到 `max_abs_z = 10164.02309965055 km`。更高幅值目标可以生成 candidate，但 residual、Jacobi span 或 phase consistency 不能通过审计，说明高幅值端不能作为接受分支。

## Q10. 为什么 N=61 没有解决问题？

`N=61` 的 spectral lift 能降低 Fourier tail energy，但 accepted branch 几乎没有向高幅值推进。当前证据更支持 fixed-mapping-time formulation 的局部参数化或 Newton basin failure，而不是单纯谱阶不足。

## Q11. 为什么 fixed-rotation candidate 不能接受？

fixed-rotation candidate 能到 11,000 km 以上，例如 rho 1.4465 附近达到 `11188.08244697768 km`，但 residual 为 `7.841846983001098e-02`，Jacobi span 为 `1.814140488309413e-03`。这些指标远高于当前 accepted branch 的审计水平，因此不能作为 numerical reproduction。

## Q12. 为什么不直接进入 Chapter 5？

Chapter 5 的 quasi-DRO 应用依赖可靠的 Chapter 3 high-amplitude quasi-DRO branch。如果 Chapter 3 分支没有通过 10,500/11,000 km 审计，直接升级 Chapter 5 会把 rejected candidate 或 proxy trend 带入 line-of-sight、eclipse avoidance 和 transfer baseline 结论。

## Q13. 当前 Chapter 5 可以怎么展示？

可以展示为应用方向和 baseline/proxy 层：CR3BP baseline、DE421-oriented baseline、local direct-shooting baseline 和 proxy corridor。不能称为完整 BCR4BP 或 optimized transfer reproduction。

## Q14. 这个工作对硕士研究有什么价值？

价值在于建立了一个从论文图谱、数值代码、逐图审计到报告材料的完整复现框架。它给后续研究留下了明确问题：原始数据缺口、quasi-DRO continuation bottleneck、Chapter 4 global manifold upgrade 和 Chapter 5 高保真应用。

## Q15. 后续能否发小论文？

有可能，但不应以“完整复现 McCarthy 2018”为题。更合理的方向是复现审计框架、拟周期轨道数值复现中的 bottleneck 诊断、或 quasi-DRO continuation formulation replacement 的方法论文。是否能投稿取决于后续能否形成新的可验证算法或系统性负面/正面结果。

## Q16. 下一步是找原始数据还是改算法？

建议先做有限 Route A：查找原始数据、补充搜索日志、记录 negative evidence，并决定是否进行 Fig. 3.16/3.17 digitization。若原始数据仍不可得，再把 Route B 作为独立算法任务启动。

## Q17. Route A/B/C 分别是什么？

Route A 是 McCarthy 原始数据 / digitization 路线；Route B 是 quasi-DRO formulation replacement 路线；Route C 是论文级复现报告和组会/开题材料整理路线。本轮属于 Route C，不新增算法试错。

## Q18. 如果找不到 McCarthy 原始数据怎么办？

应记录有边界的负面搜索证据，然后对关键图进行可追溯 digitization。digitization 只能作为对照曲线或趋势参考，不能替代原始 branch data，也不能自动把 partial baseline 升级为 full numerical reproduction。

## Q19. 如果导师要求继续数值突破，应该怎么做？

先写 formulation note，而不是直接继续试代码。note 应定义 residual equations、continuation variables、phase constraints、acceptance thresholds 和 stop condition。之后应先在较小的已知 torus family 上验证，再回到 quasi-DRO 10,500/11,000 km bottleneck。

## Q20. 如果导师要求先写论文，应该怎么组织？

建议按“复现目标与审计体系、54 图分类结果、核心案例 Fig. 3.10 / Chapter 4 / Fig. 3.16-3.17、proxy 边界、数据缺口、下一步路线”组织。标题和摘要必须避免 complete reproduction 的表述。

## Q21. 当前最适合展示的图和表是什么？

最适合展示的是 54 图 status summary、Fig. 3.10 audit table、Chapter 4 manifold audit table、Fig. 3.16/3.17 accepted vs rejected diagnostics、proxy usage summary，以及 Route A/B/C future work table。

## Q22. 当前最大风险是什么？

最大风险是视觉上看起来相似的图被误解为完整数值复现。尤其是 Fig. 3.16/3.17、Chapter 4 global sheets 和 Chapter 5 应用图必须明确 proxy、local overlay 或 baseline 标签。

## Q23. 下一阶段最小可交付成果是什么？

最小可交付成果是：完成原始数据搜索日志，明确是否存在 public branch data；如果没有，给出 Fig. 3.16/3.17 digitization 方案；同时保持当前报告包和 PPT/问答材料一致。

## Q24. 当前可以怎样一句话总结？

可以说：项目已完成 McCarthy 2018 论文 54 图的一版工程化覆盖，并建立了逐图数值审计和 proxy 边界，但尚不能声称 complete McCarthy 2018 numerical reproduction。
