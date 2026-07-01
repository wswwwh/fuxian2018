# Route B quasi-DRO formulation replacement note

本文档启动 Route B，但只定义下一阶段 formulation replacement 的数学和工程路线。本轮不编写新的 continuation 算法，不修改现有数值 CSV，不修改 figure scripts，不重新运行 54 图批处理。本文档中的候选方案都必须以后续代码和 audit 结果为准，不能被解释为 quasi-DRO bottleneck 已经解决。

## 1. 问题定义

当前要解决的问题是：McCarthy 2018 Fig. 3.16 / Fig. 3.17 的 constant-mapping-time quasi-DRO branch 尚未完成 full numerical reproduction。现有工程已经完成低振幅到局部中等振幅的 physical-consistency baseline，但完整 thesis-scale branch 仍未被 accepted numerical branch 覆盖。

当前 accepted quasi-DRO branch 的最高点只到：

- `max_abs_z = 10164.02309965055 km`;
- accepted branch 没有成员超过 `10,500 km` 或 `11,000 km`;
- Fig. 3.16 / Fig. 3.17 仍应标记为 partial physical-consistency baseline。

Route B 的直接目标不是立刻追到 thesis reference trend 的约 `31,000 km` 高振幅端，而是先找到一个能稳定通过 `10,500 km` / `11,000 km` audit gate 的 continuation formulation。只有通过该局部门槛后，才有资格讨论更高振幅、figure 升级和 Chapter 5 quasi-DRO application scene 的后续替换。

## 2. 当前 fixed-mapping invariant curve formulation 总结

当前实现以 stroboscopic invariant curve 为核心。曲线由均匀相位点

```text
X_i = X(theta_i),  theta_i = 2*pi*i/N,  X_i in R^6
```

表示，其中状态为 CR3BP rotating-frame state。曲线样本通常来自线性 seed、低阶 corrected branch、spectral lift 或相邻 branch member 的插值预测。

当前 fixed-mapping-time quasi-DRO formulation 的主要元素如下。

- **Invariant curve states**：未知量主要是 `N` 个六维状态 `X_i`。free-rotation formulation 还把 rotation angle `rho` 作为未知量；PALC formulation 在此基础上加入 pseudo-arclength plane。
- **Stroboscopic map**：对每个 `X_i` 积分固定映射时间 `T`，得到 `Phi_T(X_i)`。映射 Jacobian 使用 propagated STM block 构造。
- **Fixed mapping time**：quasi-DRO branch 保持 `T` 固定，当前 accepted branch 的 `mapping_time_days = 14.74932760227518`。这与 Fig. 3.16 / Fig. 3.17 的 constant-mapping-time 目标一致，但也是当前 bottleneck 的主要嫌疑参数化。
- **Rotation angle rho**：不变曲线要求一次 stroboscopic map 后曲线相位推进 `rho`。目标点通过 trigonometric interpolation 计算：

```text
I_rho[X](theta_i) = X(theta_i + rho)
```

- **Amplitude constraint**：当前 amplitude-stepping 使用 vertical component 的 phase-invariant RMS amplitude 选择 branch member，即约束 `A_z(X) - A_target = 0`。这比单点最大值更平滑，但仍把 continuation 强绑定到固定映射时间下的 vertical amplitude parameterization。
- **Phase constraint**：使用当前曲线相对 reference tangent / phase direction 的正交条件，压掉曲线参数化漂移，例如 `<X - X_ref, tau_ref> = 0`。
- **Residual definition**：核心 map residual 为

```text
R_i(X, rho) = Phi_T(X_i) - I_rho[X](theta_i)
```

全局 residual norm 取 pointwise residual 的最大值或展开向量范数。accepted / rejected 判定还必须包含 amplitude residual、phase residual、Jacobi span 和 phase-return audit。

- **Newton / least-squares correction**：线性化使用 STM block、trigonometric interpolation matrix，以及必要时对 `rho` 的 interpolation derivative。由于系统通常带约束或近奇异，校正使用 least-squares / damped Newton，并限制单步 state correction、rotation step 等。
- **PALC extension**：fixed-mapping pseudo-arclength continuation 使用相邻 accepted members 的 secant predictor，并加入 arclength plane：

```text
<u - u_pred, tangent> = 0
```

其中 `u` 包含曲线状态和 `rho`。该扩展避免只按 amplitude 自然参数推进，但仍保持 fixed mapping time。

- **Audit metrics**：当前验收不是只看 Newton convergence，而是综合检查 `map_residual_norm`、amplitude residual、phase residual、curve Jacobi span、one-map Jacobi drift、one-map phase return error、ten-return Jacobi span、monotone amplitude/rho/Jacobi 趋势，以及 rejected candidate 是否混入 figure branch。

该 formulation 在低振幅局部分支和 10,000 km 附近是有效的：accepted local/extended/PALC branch 可以保持小 residual、低 Jacobi drift 和良好的 ten-return Jacobi span。它失败的位置集中在 `rho about 1.44388`、`max_abs_z about 10.16e3 km` 之后。失败表现不是单纯的 Fourier tail 变大，而是 Newton candidate 出现 residual / Jacobi span 快速恶化、fixed-rotation 高振幅候选通过不了 audit、free-time/free-rho 试验仍不能给出 accepted member。

## 3. Bottleneck 证据复盘

当前证据来自 `docs/chapter3_quasi_dro_validation.md`、`docs/reproduction_report/numerical_audit_appendix.md`、`data/computed/chapter3_quasi_dro_palc_validation.csv`、`data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv` 和 `data/computed/chapter3_quasi_dro_bottleneck_experiments.csv`。

accepted 10,000 km member 的局部 audit 很强：

- pointwise map residual `4.147166287852223e-14`;
- Jacobi span `1.615654277031808e-10`;
- state Fourier tail ratio `2.501018355914203e-12`;
- one-map 和 ten-return 检查仍支持它作为 low-to-10,000 km physical-consistency baseline。

accepted PALC `N=61` endpoint 是当前最高 accepted member：

- `max_abs_z = 10164.02309965055 km`;
- `rho = 1.443877875293695 rad`;
- pointwise map residual `7.890714644108212e-10`;
- Jacobi span `1.794120407794253e-11`;
- state Fourier tail ratio `1.80077333522803e-17`;
- one-map phase return error 仍在 `1e-8` audit gate 内。

这说明 `N=61` spectral lift 能降低 Fourier tail 和保持 Jacobi consistency，但 accepted branch 没有因此越过 10,500 km 或 11,000 km。

rejected 11,000 / 12,000 / 14,000 km amplitude-stepping candidates 的失败是全局性的：

- 11,000 km target: map residual `4.227040797634044e-04`, Jacobi span `1.95390551757324e-04`;
- 12,000 km target: map residual `1.025722315499319e-02`, Jacobi span `8.085234362318339e-04`;
- 14,000 km target: map residual `2.368746795354498e-02`, Jacobi span `1.547418108960308e-03`。

rejected fixed-rotation candidates 可以人为推进到更高振幅，但不能作为 numerical branch 使用。rho `1.4465` 附近的 candidate 到达约 `11188.08244697768 km`，但 residual 为 `7.841846983001098e-02`，Jacobi span 为 `1.814140488309413e-03`。这类 candidate 只能说明固定 `rho` target 能制造高振幅形状，不能说明不变曲线已经被校正。

fixed-mean-Jacobi/free-rho/free-time local experiment 也没有通过 audit。它的最好结果只到约 `10210.30431232785 km`，仍有 residual `7.300106125062243e-05` 和 Jacobi span `1.957537848262803e-06`，距离 accepted threshold 仍有明显差距。

Route A 的 Fig. 3.17 digitized comparison 显示 thesis reference trend 继续向高振幅延伸：在 accepted endpoint 附近，digitized amplitude 约 `13204.1 km`，比 corrected endpoint 高约 `3040.1 km`；更右侧 digitized points 延伸到约 `30,714 km`。但这些点只是 lower-authority reference trend，不能替代 raw branch data，也不能用于 extrapolate accepted branch。Fig. 3.16 也不能从静态 3D 图中精确 digitize。

克制结论：当前证据更像 local parameterization / Newton basin failure，而不是纯 spectral-resolution problem。更高 `N` 仍可能在新 formulation 中有价值，但单独提高 spectral order 已经不是最优先的 Route B 动作。

## 4. 候选 formulation A：fixed-Jacobi / free-mapping-time / free-rho invariant curve correction

候选 A 是最小替换路线：保留当前 invariant-curve shooting 框架和 CR3BP map audit，但放松 fixed mapping time，并用 Jacobi constraint 重新定义 branch member。

### Unknown variables

建议第一版 unknown vector 为：

```text
u = [X_0, X_1, ..., X_{N-1}, T, rho]
```

其中 `X_i in R^6`，`T` 为 mapping time，`rho` 为 rotation angle。Jacobi target `C*` 在 correction step 中固定；在 continuation 中可作为 natural parameter 或 PALC vector 的一部分。

### Residual equations

核心 residual 仍是 map invariance：

```text
R_i = Phi_T(X_i) - I_rho[X](theta_i)
```

额外加入 fixed-Jacobi residual：

```text
R_C = mean_i C(X_i) - C*
```

如果后续发现 mean Jacobi 不能充分约束曲线能量一致性，可升级为 pointwise weighted Jacobi residual 或在 audit 中强制 curve Jacobi span，但第一版不应过度增加约束数量。

### Constraints

最小 square correction 可使用：

- `6N` 个 map residual；
- `1` 个 mean Jacobi residual；
- `1` 个 phase condition。

总方程数为 `6N + 2`，匹配 unknown `6N + 2`。这里不再把 amplitude 作为硬约束；amplitude 只作为 continuation progress 和 audit gate。这样做的目的，是避免继续把 branch 锁死在 fixed-time vertical-amplitude parameterization 上。

### Phase conditions

至少保留一个 phase condition：

```text
<X - X_ref, dX_ref/dtheta> = 0
```

如果 `T` 和 `rho` 同时 free 后出现 time/angle gauge drift，可考虑加入第二个 phase condition，并把 continuation 参数改为 free `C` + PALC square system。但最小原型应先保持单 phase condition，以便分辨失败来自 formulation 还是过约束。

### Continuation parameter

推荐从 accepted 10,164 km member 出发，先做 local reparameterization，再做小步 continuation：

- correction-only test：固定 `C* = mean Jacobi(endpoint)`，free `T` 和 `rho`，验证能否复现同一 accepted member；
- small-step test：沿 `C*` 单调下降方向或沿 `[X,T,rho,C]` PALC 方向推进；
- amplitude 只作为输出监控，目标是出现 accepted `max_abs_z > 10,500 km`，然后再尝试 `> 11,000 km`。

### Expected advantages

- 直接缓解 fixed-mapping-time bottleneck：如果真实 branch 在 10,000-11,000 km 区间需要轻微改变 mapping time，当前 formulation 会把可接受曲线推到错误 Newton basin。
- 保留当前 code architecture：仍可复用 stroboscopic map、STM、trigonometric interpolation、phase audit 和 CSV audit 思路。
- 不依赖 digitized trend 或 rejected fixed-rotation candidates：branch progress 仍由 accepted residual / Jacobi / phase gates 决定。
- 可在较小 quasi-halo / quasi-vertical family 上做 formulation sanity check，再回到 quasi-DRO。

### Risks

- fixed-Jacobi / free-time / free-rho 可能仍近奇异，特别是在 fold 或 remote branch 附近。
- mean Jacobi constraint 不等价于 pointwise Jacobi consistency；必须继续用 curve Jacobi span audit 兜底。
- 释放 `T` 可能偏离 Fig. 3.16 / Fig. 3.17 的 constant-mapping-time caption，需要明确区分“诊断 formulation”与“最终 constant-time reproduction”。如果 free-time branch 通过 11,000 km，还要判断它是否能回到 constant-time target 或解释 thesis formulation 差异。
- 若 phase condition 不稳，可能出现 curve parameterization drift 而非物理解。

### Audit gates

候选 A 的 accepted member 必须同时满足：

- `map_residual_norm <= 1e-8`;
- `curve Jacobi span <= 1e-8`;
- `one-map phase return error <= 1e-8`;
- ten-return Jacobi span remains near integration precision；
- no rejected fixed-rotation candidate imported as branch member；
- no extrapolation from digitized Fig. 3.17 trend。

## 5. 候选 formulation B：Fourier / collocation torus BVP

候选 B 是更完整但成本更高的路线，参考 Tor / COCO / Schilder / Olikara 一类 torus continuation 思路。本轮只定义方向，不实现。

### State representation

状态可表示为 Fourier coefficients：

```text
X(theta_1, theta_2) = sum_{k,l} a_{k,l} exp(i(k theta_1 + l theta_2))
```

也可表示为 tensor-product collocation grid。对当前 stroboscopic invariant curve 来说，可以先采用 map-based one-angle curve BVP；若需要完整 torus，则进入 two-angle continuous-time torus BVP。

### Torus invariance equation

continuous-time torus BVP 的核心方程是：

```text
omega_1 * dX/dtheta_1 + omega_2 * dX/dtheta_2 - f(X) = 0
```

map-based torus / invariant-curve version 可写为：

```text
Phi_T(X(theta)) - X(theta + rho) = 0
```

前者更接近完整 torus collocation，后者更容易与现有 shooting result 对接。

### Frequency / rotation variables

unknown variables 可包含：

- Fourier coefficients 或 collocation states；
- `omega_1`, `omega_2` 或等价的 `T`, `rho`;
- Jacobi target `C` 或 energy parameter；
- PALC continuation scalar。

### Phase constraints

必须加入相位锚定，避免 torus shift nullspace。典型做法包括：

- 固定一个 Fourier coefficient 的 imaginary / real projection；
- 对 reference torus tangent 施加 orthogonality；
- 固定一个 physical section point 的 coordinate；
- 对两个 angle direction 各给一个 phase condition。

### Energy or Jacobi constraint

可以固定 mean Jacobi，也可以使用 pointwise Jacobi consistency penalty / residual。出于工程风险控制，建议第一版仍采用 fixed mean Jacobi + strict audit span，而不是直接把每个 collocation point 的 Jacobi 都作为硬方程。

### Pseudo-arclength continuation

BVP route 应默认使用 pseudo-arclength continuation，而不是 amplitude stepping。continuation vector 应包括 coefficients/states、frequency variables、Jacobi 或 energy parameter。这样可以处理 folds，但需要更严格的 scaling 和 conditioning diagnostics。

### Residual norm

residual 应分层记录：

- normalized BVP residual；
- physical state residual in nondimensional units；
- curve / torus Jacobi span；
- phase constraint residual；
- PALC residual；
- Fourier tail or collocation defect；
- singular values / condition estimate。

### Comparison against current invariant-curve shooting result

候选 B 不能直接声称优于当前 branch。它必须先复现 current accepted endpoint：

1. 从 accepted 10,164 km member 构造 Fourier/collocation initial guess；
2. 在相同 CR3BP system 下重建 one-map phase return；
3. 对比 `rho`、`T`、mean Jacobi、max abs z、map residual、Jacobi span；
4. 只有通过相同 audit gates 后，才能尝试 10,500 / 11,000 km continuation。

### Implementation cost

该路线成本显著高于候选 A：

- 需要设计 coefficient/grid unknown vector 和 residual assembly；
- 需要高质量 scaling、preconditioner 或 sparse linear algebra；
- 需要 phase conditions 和 PALC 的 robust implementation；
- 若引入 COCO/Tor，会带来 MATLAB/Python workflow split；
- 若 Python 原生实现，需要新增大量测试和小系统验证。

因此候选 B 应作为 fallback，而不是下一轮第一实现。

## 6. 候选 formulation C：hybrid route

保守混合路线如下。

1. 冻结当前 accepted branch，尤其是 accepted 10,000 km member 和 accepted `N=61` 10,164 km endpoint，作为 seed 和 baseline comparison target。
2. 先做 local reparameterization：在当前 endpoint 上测试 fixed-Jacobi/free-time/free-rho correction，确认它能在不改变物理解的情况下通过原 audit gates。
3. 如果 local formulation 稳定，做小步 continuation，并以 `10,500 km` / `11,000 km` 为唯一短期 success gate。
4. 如果局部 formulation 通过 10,500 / 11,000 km，再考虑 higher `N`，例如 `N=81` 或更高，但只作为 accepted formulation 的 spectral refinement。
5. 如果仍失败，再进入 full Fourier/collocation BVP route。此时候选 B 的第一阶段也只做 residual assembly 和 current endpoint reproduction，不直接追高振幅。

这条路线的原则是：先换最可能解除 bottleneck 的约束，再增加 spectral order；先通过局部 audit gate，再更新 figures；先证明 formulation 能工作，再考虑 Chapter 5。

## 7. 最小原型实验设计

本节定义下一轮编码的最小可执行实验。本轮不实现。

### 实验 1：fixed-Jacobi/free-time/free-rho correction on accepted 10,164 km member

- **Input data**：`data/computed/chapter3_quasi_dro_palc_family.csv` 中 accepted `N=61` endpoint；对应 validation row；Earth-Moon CR3BP constants；当前 endpoint 的 states、phases、mean Jacobi、rho、mapping time。
- **Output files**：建议新建独立实验 CSV，例如 `data/computed/chapter3_route_b_free_time_local_experiment.csv` 和 log CSV；不得覆盖 accepted branch CSV。
- **Success criteria**：correction-only 复现 endpoint，`map_residual_norm <= 1e-8`，curve Jacobi span `<= 1e-8`，one-map phase return error `<= 1e-8`，ten-return Jacobi span near integration precision；若做小步 continuation，则至少一个 accepted member 超过 `10,500 km`。
- **Failure criteria**：free `T/rho` 后 residual、Jacobi span 或 phase return error 不能回到 audit gate；`T` 漂移导致 branch 与 Fig. 3.16 / Fig. 3.17 constant-time 目标不可解释；candidate 只能靠 rejected fixed-rotation shape 达到高振幅。
- **Stop condition**：连续小步 trust-region / continuation 尝试仍不能产生 accepted `>10,500 km` member，或 condition estimate / singular value 证据显示局部 formulation 退化。

### 实验 2：same formulation on smaller known quasi-halo or quasi-vertical family

- **Input data**：已有 accepted quasi-halo 或 quasi-vertical invariant-curve family，例如 Chapter 3 fixed-energy quasi-halo / quasi-vertical corrected members；选择 residual 和 Jacobi audit 已经稳定的一段。
- **Output files**：独立 method-validation CSV 和 log，例如 `data/computed/chapter3_route_b_free_time_sanity_check.csv`；不改现有 family CSV 和 figure inputs。
- **Success criteria**：fixed-Jacobi/free-time/free-rho formulation 能复现较小 family 的 accepted member，并能做至少 2-3 个小 continuation steps，保持 residual/Jacobi/phase gates。
- **Failure criteria**：在已知较小 family 上也无法复现 accepted solution，说明 formulation / phase condition / scaling 本身有问题，不能直接用于 quasi-DRO bottleneck。
- **Stop condition**：小 family sanity check 失败时停止 quasi-DRO high-amplitude coding，先修正 unknown scaling、phase condition 或 Jacobian assembly。

### 实验 3：Fourier/collocation BVP paper prototype

- **Input data**：accepted 10,164 km member；现有 stroboscopic map residual assembly；参考 Tor / COCO / Schilder / Olikara formulation notes。
- **Output files**：只允许 method prototype 文档或 residual-design stub；如果写代码，应限定在非 production prototype，输出 `data/computed/chapter3_route_b_bvp_residual_design.csv` 或 equivalent diagnostic，不接入 figures。
- **Success criteria**：明确 unknown vector layout、index map、residual blocks、phase constraints、Jacobi constraint、PALC equation、normalization/scaling；能够在 current accepted endpoint 上 assemble residual 并报告接近当前 audit 的 residual level。
- **Failure criteria**：unknown vector 或 residual block 定义不闭合；无法解释 phase nullspace；无法把 current accepted endpoint 映射到 BVP representation。
- **Stop condition**：完成 residual assembly 和 endpoint reproduction design 后停止，不做 full continuation，除非候选 A 已确认失败且用户明确启动 BVP implementation。

## 8. 验收标准

下一轮如果真的编码，成功必须由 accepted branch audit 判定，而不是视觉趋势或 Newton convergence message 判定。

最低成功标准：

- 至少一个 accepted member exceeds `10,500 km`;
- `residual <= 1e-8`;
- curve Jacobi span `<= 1e-8`;
- one-map phase return error `<= 1e-8`;
- ten-return Jacobi span remains near integration precision。

更强成功标准：

- 至少一个 accepted member exceeds `11,000 km`;
- 该 member 与前后 accepted members 在 `rho`、mean Jacobi、amplitude 上趋势一致；
- residual/Jacobi/phase metrics 与当前 accepted branch 同量级；
- 有清楚 log 说明它不是 rejected fixed-rotation candidate。

强制限制：

- no use of rejected fixed-rotation candidates as accepted branch members；
- no extrapolation from digitized Fig. 3.17 trend；
- Fig. 3.16 / Fig. 3.17 不升级为 full numerical reproduction，除非 accepted branch 真实通过 audit；
- teacher package 和 current report package 保持冻结，只在新结果通过 audit 后更新。

## 9. 文件与代码影响范围

后续若编码，可能涉及以下文件或文件族，但本轮不修改它们：

- `src/qp_orbits/quasi_torus.py`
- `src/qp_orbits/corrected_dro_family.py`
- `scripts/run_chapter3_palc_diagnostic.py`
- `data/computed/chapter3_*`
- `docs/chapter3_quasi_dro_validation.md`

后续编码时应新增 Route B-specific experiment outputs，而不是覆盖当前 accepted branch、PALC family、validation CSV 或 figure input CSV。任何 figure script 更新必须等 accepted branch 通过 10,500 / 11,000 km audit gate 后再讨论。

## 10. 决策建议

建议如下。

- 不继续 fixed-mapping-time blind parameter search。现有证据已经显示 amplitude stepping、fixed-mapping PALC 和 fixed-rotation fallback 都卡在同一局部区域。
- 不直接进入 Chapter 5。Chapter 5 quasi-DRO application scenes 依赖 Chapter 3 quasi-DRO branch 的可信度，当前 branch 还没有通过 10,500 / 11,000 km audit gate。
- 下一轮先做 fixed-Jacobi/free-time/free-rho minimal prototype。它最大化复用现有 invariant-curve shooting/audit 架构，同时直接测试 fixed-mapping-time bottleneck 假设。
- 若 minimal prototype 在 accepted endpoint 和较小 known family 上失败，再考虑 Fourier/collocation BVP route。
- teacher package 和 current report package 保持冻结；只有当新 formulation 产生 accepted high-amplitude member 并通过 residual/Jacobi/phase/ten-return audit 后，才更新报告、展示材料和 Fig. 3.16 / Fig. 3.17 状态。
