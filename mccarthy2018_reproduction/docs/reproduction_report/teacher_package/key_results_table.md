# Key Results Table

| topic | current result | interpretation | boundary / next step |
|---|---|---|---|
| 54 图覆盖 | Figures 2.1-2.15, 3.1-3.17, 4.1-4.8, 5.1-5.14 已有一版工程化输出。 | 项目已从单图试验进入全图谱管理。 | 覆盖不等于完整数值复现。 |
| numerical reproduction 数量 | 16 张。 | 当前最强证据层，主要为 CR3BP 基础、周期轨道和若干 corrected numerical families。 | 以 `data/computed/figure_validation_table.csv` 为准。 |
| physical-consistency baseline 数量 | 6 张 regular baseline + 2 张 partial baseline。 | 物理链条可信，但不保证等同 McCarthy 原始数值。 | Fig. 3.16 / Fig. 3.17 必须保持 partial。 |
| Fig. 3.10 q=8 结论 | q=8 multiple-shooting patch residual 接近 roundoff，但 full-period single integration closure error 为 `3.906984451743337`。 | 可作为 unstable multiple-shooting local approximation。 | 不能称为 robust single-shoot periodic orbit。 |
| Chapter 4 DG audit 结论 | Fig. 4.3-4.8 有 source residual、DG eigenvector propagation、growth ratio 和 Jacobi drift 证据。 | 支持 physical-consistency baseline。 | thesis-scale continued torus global manifold sheets 仍未完成。 |
| Fig. 3.16 / Fig. 3.17 accepted branch endpoint | accepted quasi-DRO branch reaches rho `1.443877875293695 rad` and `max_abs_z = 10164.02309965055 km`。 | 支持 partial physical-consistency baseline。 | 没有 accepted member 超过 10,500 km 或 11,000 km。 |
| Fig. 3.17 digitized comparison | digitized z-amplitude trend reaches about `30714.3 km`; at accepted endpoint, digitized trend is about `13204.1 km`, about `3040.1 km` above corrected branch。 | digitization documents the gap to the thesis trend。 | digitized trend 是 lower-authority reference，不是 raw branch data。 |
| Chapter 5 当前状态 | CR3BP baseline、DE421-oriented baseline、local direct-shooting baseline 和 geometric / proxy corridor 混合。 | 可展示应用方向和当前实现能力。 | 不能称为完整 BCR4BP / ephemeris optimized transfer reproduction。 |
| 下一步 Route A | 继续有限原始数据搜索，记录 negative evidence，必要时扩展可追溯 digitization。 | 低成本、低风险，适合先做。 | 找不到原始数据时不要假设存在。 |
| 下一步 Route B | quasi-DRO formulation replacement：从 fixed-mapping-time 局部修正转向更适合 fold / parameterization failure 的 formulation。 | 可能突破 10,500 / 11,000 km bottleneck。 | 编码前先定义 residual equations、variables、phase constraints、acceptance thresholds。 |
