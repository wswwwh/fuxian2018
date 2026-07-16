# 消融实验结果

## 设计

在Halo N45、Vertical N57、Sun–Earth member 468、Route H member 68 physical corrected-rho以及complex-pair negative control（Route H member 32）上比较V1–V7七个预先声明版本。研究阈值未改变。

- V1：pointwise eig，无相位对齐；V2：pointwise eig，仅符号对齐。
- V3：partial real-Schur，无phase tracking；V4：partial real-Schur + phase tracking。
- V5：QR/SVD，无phase alignment、固定一维；V6：QR/SVD + phase alignment、固定一维。
- V7：QR/SVD + phase alignment + Schur dimension seed。

共35行；状态统计：`{"accepted": 15, "fail": 20}`；method exception：4行，均保留。

## 主要结论

- 符号对齐使三个一维锚点的pointwise跨分辨率角V1/V2改善倍数达到5.819e+01–2.189e+05；但V2残差仍全部fail，其一次映射几何距离仍为3.030e-02–4.159e-02。
- 三个一维锚点上，Schur phase tracking的残差比值V3/V4仅为1.000e+00–1.000e+00，说明这里的全局选定基已经足够连续；而两个Route H二维案例的V3/V4残差改善倍数为1.528e+00–4.925e+00，但V4仍fail。
- 三个一维锚点上，QR phase alignment的残差比值V5/V6为1.000e+00–1.000e+00，未显示额外残差收益；其主要作用是显式规范相位帧，而不是在这些已平滑的一维案例上制造通过。
- Route H的V5/V6一维版本是故意保留的无效complex-pair消融对照，不能被解释为物理一维子束；V7恢复二维语义，但physical corrected-rho案例仍保持fail。
- `manifold_geometry_distance`是一次映射的线性化位置位移点云对V7的对称HD95距离，用于隔离局部方向处理；它不是Stage-F非线性全局manifold sheet验收的替代品。
- cross-resolution对Halo/Vertical使用现有冻结分辨率源，对Sun–Earth/Route H使用明确标记的Fourier诊断降采样。

## 失败与边界

pointwise eig在Route H局部矩阵上找不到不稳定双曲实方向，相关method-exception行及图中×标记均保留。所有complex-pair一维对照均强制判fail；未通过删除行、改变rho或放宽阈值提高通过率。

## 图

- `ablation_bundle_residual.pdf`：最大bundle residual及固定pass/boundary线。
- `ablation_phase_continuity.pdf`：相邻相位主角与检测到的相位修正数。
- `ablation_manifold_geometry.pdf`：一次映射线性化几何距离。

## 真实性边界

本消融仅支撑数值框架与系统比较定位，不构成新理论声明。Chapter 4 projection holdout仍为`0/4`、`paper_projection=fail`、`paper_3d=false`。
