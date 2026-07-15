# 54 图状态总表

- A-E 等级统计：{'A': 7, 'B': 30, 'C': 5, 'D': 12}
- 权威证据状态：{'accepted': 7, 'boundary': 30, 'diagnostic': 5, 'proxy': 12}
- A 表示当前项目门槛内的定量通过，不自动等于原作者节点逐点等价。

| 图号 | 研究对象 | 等级 | proxy | 当前源层/结果 | 主要边界 |
|---|---|---|---|---|---|
| 2.1 | 三体系统几何与参考坐标系 | D | true | frame definitions and primary geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.2 | 共线平动点求解几何 | D | true | collinear point layout | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.3 | 五个平动点的相对位置 | B | false | CR3BP L1-L5 locations | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.4 | 地月系统零速度曲线 | B | false | Jacobi zero velocity contours | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.5 | 地月系统零速度面 | D | true | rotating-frame axes and primaries | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.6 | 地月、土卫六与日地系统零速度曲线对照 | B | false | Jacobi zero velocity contours | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.7 | 地月 L1 点附近面内与面外线性模态 | B | false | planar and vertical linear modes | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.8 | 地月 L1 点附近线性 Lissajous 运动 | B | false | linear mode amplitudes | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.9 | 单步打靶差分修正示意 | D | true | single-shooting correction geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.10 | 多步打靶轨迹弧段示意 | D | true | multiple-shooting arc geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.11 | L2 Lyapunov 初值与修正解 | B | false | L2 Lyapunov state; period; Jacobi | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.12 | 自然参数与伪弧长延拓示意 | D | true | natural and pseudo-arclength continuation geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 2.13 | 木星—欧罗巴 L2 周期轨道族 | B | false | Jupiter-Europa Lyapunov; halo; vertical families | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.14 | L1 Lyapunov 轨道的稳定与不稳定流形 | B | false | L1 Lyapunov monodromy and stable/unstable manifolds | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 2.15 | 地月 L2 Halo 轨道族稳定指标 | A | false | L2 halo/NRHO stability branch | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.1 | 二维环面作为两个圆的直积 | D | true | two-circle torus geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 3.2 | 不变曲线、旋转角与回归轨迹 | D | true | rotation angle and return map geometry | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 3.3 | 七节点离散不变曲线映射 | C | partial | seven-point invariant curve map residuals | 只可用于局部/诊断性结论，未覆盖部分不得外推。 |
| 3.4 | 多步打靶环面修正的拼接曲线 | D | true | patch curves and multiple-shooting layout | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 3.5 | 定能量拟 Halo 环面族 | A | false | JC 3.1389 quasi-halo tori | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.6 | 定能量拟 Halo 振幅曲线 | A | false | quasi-halo amplitudes versus mapping time | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.7 | 定能量拟垂直环面族 | B | false | JC 3.1389 quasi-vertical tori | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 3.8 | 定能量拟垂直振幅曲线 | B | false | quasi-vertical amplitudes versus mapping time | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 3.9 | 频率比随映射时间变化 | C | partial | frequency ratio versus mapping time | 只可用于局部/诊断性结论，未覆盖部分不得外推。 |
| 3.10 | period-2、period-3 与 period-8 Halo 示例 | C | partial | q=2/q=3/q=8 Earth-Moon CR3BP period-q halo examples; strict single-shoot accepted rows 2; local multiple-shooting accepted rows 3; q8 max multiplier 3.431052642945378e+16 | q=8 必须维持 C 级边界，直至存在新的严格闭合审计。 |
| 3.11 | Poincare 映射与中心周期轨道 | C | partial | Poincare map and central periodic orbits | 只可用于局部/诊断性结论，未覆盖部分不得外推。 |
| 3.12 | 定频率拟 Halo 环面族 | A | false | L2 constant-frequency quasi-halo tori | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.13 | 定频率拟 Halo 振幅与 Jacobi 常数 | A | false | L2 quasi-halo amplitudes and Jacobi trend | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.14 | 定频率拟垂直环面族 | A | false | L2 constant-frequency quasi-vertical tori | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.15 | 定频率拟垂直 Jacobi 常数与映射时间 | A | false | L2 quasi-vertical Jacobi and mapping time | A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。 |
| 3.16 | 定映射时间拟 DRO 环面 | B | false | constant-mapping-time quasi-DRO tori rendered directly from the accepted fixed-mapping-time Route H quasi-DRO source branch; rho 1.445863346020272..1.457169483818128 rad; max abs z 10969.67553863909..14573.10318409037 km; 30 rows >= 10500 km and 29 rows >= 11000 km; mapping time 14.74932760227518 days | 只声明 Route H 图源层有效，不声明整条论文分支逐点等价。 |
| 3.17 | 拟 DRO 振幅与 Jacobi 常数随旋转角变化 | C | partial | rho-amplitude-Jacobi trends with the audited Route H branch plotted as the numerical source layer; accepted fixed-mapping-time Route H quasi-DRO source branch; rho 1.445863346020272..1.457169483818128 rad; max abs z 10969.67553863909..14573.10318409037 km; 30 rows >= 10500 km and 29 rows >= 11000 km; mapping time 14.74932760227518 days | 该图维持 C 级诊断/部分覆盖，不将参考趋势当作原始数据。 |
| 4.1 | 地月 L2 拟 Halo 轨道与 DG 特征结构 | B | false | N=25 corrected L2 quasi-halo DG at paper-reported Jacobi precision | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 4.2 | 拟 Halo 稳定指标随映射时间变化 | B | false | accepted L1 constant-energy quasi-halo DG stability family plus native-PDF digitized reference | 只对公共区间作点对点声明，完整曲线等价仍未通过。 |
| 4.3 | 拟 Halo +x 方向不稳定流形 | B | false | corrected L1 quasi-halo +x fixed-time full-torus unstable-manifold snapshots at four paper times | 不得声明论文视角、物理飞行或三维等价。 |
| 4.4 | 拟 Halo -x 方向不稳定流形 | B | false | corrected L1 quasi-halo -x fixed-time full-torus unstable-manifold snapshots at four paper times | 不得声明论文视角、物理飞行或三维等价。 |
| 4.5 | 拟垂直 +x 方向不稳定流形 | B | false | corrected L1 quasi-vertical +x fixed-time full-torus unstable-manifold snapshots at four paper times | 不得声明论文视角、物理飞行或三维等价。 |
| 4.6 | 拟垂直 -x 方向不稳定流形 | B | false | corrected L1 quasi-vertical -x fixed-time full-torus unstable-manifold snapshots at four paper times | 不得声明论文视角、物理飞行或三维等价。 |
| 4.7 | 拟 Halo 与周期 Halo 流形对照 | B | false | corrected quasi-halo manifold with periodic-halo comparison | 只声明内部动力学源层，不声明投影几何等价。 |
| 4.8 | 拟垂直与周期 Halo 流形对照 | B | false | corrected 33-node JC=3.1389 quasi-vertical global unstable manifold with periodic-halo comparison | 只声明内部动力学源层，不声明投影几何等价。 |
| 5.1 | 日地 L1 拟垂直轨道长时传播 | B | false | corrected Sun-Earth L1 two-frequency Lissajous torus trajectories | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.2 | 日—月食几何示意 | D | true | mission-geometry schematic | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 5.3 | 地—月—航天器视线几何 | D | true | mission-geometry schematic | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 5.4 | 日—地—月会合坐标几何 | D | true | mission-geometry schematic | 只可用于概念说明，不得报告数值误差或严格等价。 |
| 5.5 | 拟 DRO 与对应平面周期 DRO | B | false | corrected DRO and quasi-DRO return CR3BP baseline | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.6 | 不同相位的拟 DRO 星历轨迹 | B | false | Route H quasi-DRO embedded in DE421-oriented Sun-Moon frame | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.7 | 不同插入历元的拟 DRO 星历轨迹 | B | false | Route H quasi-DRO eclipse/occultation scene in DE421-oriented frame | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.8 | Halo 至 Lyapunov 转移初值与收敛解 | B | false | Earth-Moon equal-Jacobi halo-to-Lyapunov multiple-shooting transfer | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.9 | NRHO 与候选离去位置 | B | false | Earth-Moon corrected periodic-NRHO family with transfer departure markers | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.10 | 两处离去位置的收敛转移轨迹 | B | false | Earth-Moon NRHO CR3BP transfers plus DE421-initialized planar BCR4BP correction | 只声明项目 BCR4BP 数值扩展，不替代论文 Fig. 5.10 原始解。 |
| 5.11 | 两条 NRHO 之间的收敛转移 | B | false | Earth-Moon NRHO direct-transfer CR3BP baseline | 结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。 |
| 5.12 | 交会速度增量随到达时间变化 | B | false | Earth-Moon NRHO fixed-departure rendezvous arrival-offset branch | 未覆盖区间不得插值或绘制代理。 |
| 5.13 | 日地 L1 稳定流形近地点热图 | B | false | accepted active-geometry Sun-Earth L1 two-frequency torus DG tight stable-manifold periapsis map | 只声明 CR3BP 活跃几何源层与目标近地点一致。 |
| 5.14 | LEO 至日地 L1 拟周期 Lissajous 轨道转移 | B | false | accepted active-geometry Sun-Earth L1 stable-manifold LEO transfer | 只声明 CR3BP 数值转移，不声明高保真论文等价。 |
