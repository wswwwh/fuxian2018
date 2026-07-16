# Abstract / 摘要

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`

## English

Reliable stable and unstable manifold construction around quasi-periodic
orbits requires a real invariant bundle of a phase-shifted cocycle, not an
eigenvector selected independently at each phase.  We present an auditable
numerical framework that separates a traditional pointwise-eigendecomposition
baseline from two real-subspace methods: ordered partial real-Schur tracking
and shifted QR/SVD cocycle iteration.  A frozen registry contains 15 cases from
four Earth–Moon and Sun–Earth benchmark families, including positive, negative,
boundary, low-resolution, and legacy-operator controls.  Across 45
case–method runs, pointwise eigenselection produced 0/15
accepted results, partial real Schur produced 7/15,
and QR/SVD produced 10/15.  On the high-resolution
Halo N45, Vertical N57, and Sun–Earth member-468 cases, QR/SVD reduced the
maximum bundle residual relative to the pointwise baseline by factors of
2.82e+10,
4.11e+07, and
1.51e+07, respectively.  A 126-row manifold
campaign retained a Jacobi-drift ceiling of 2.220e-15 and
accepted both improved methods at the three high-resolution family anchors,
while lower-resolution full-sheet distances remained above the frozen 0.01
boundary.  A Route-H control audit further shows that the previously near-real
member-68 result belongs to a legacy seed-rotation operator whose curve-map
residual is about 1.99e-3; the physical corrected-rotation curve closes near
8.5e-13 but does not yield an accepted one-dimensional bundle.  The supported
contribution is therefore a reliable numerical framework and systematic
comparison, not a claim of new invariant-bundle theory or thesis-wide numerical
equivalence.

## 中文

拟周期轨道附近的稳定/不稳定流形必须来自满足相位平移 cocycle 方程的实不变子束，
不能把各相位独立选出的复特征向量直接投影成实方向。本文建立了一个可审计数值框架，
系统比较传统点式特征分解、ordered partial real-Schur 子空间跟踪和 shifted QR/SVD
cocycle 迭代。冻结 benchmark registry 含 4 类轨道族、15 个 case；45 个 case–method
结果中，点式基线 accepted 为 0/15，partial real-Schur
为 7/15，QR/SVD 为 10/15。
在 Halo N45、Vertical N57 和 Sun–Earth member 468 上，两种实子空间方法均通过，
而点式方法失败。126 行流形实验严格保持 Jacobi 漂移门槛，并保留低分辨率全片几何
不收敛及 Route H corrected-ρ 失败结果。当前证据支持“可靠数值框架与系统比较”，
不支持“新理论”或 McCarthy 2018 全文严格数值等价复现。
