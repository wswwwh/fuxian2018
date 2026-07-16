# 54 图报告最终人工字段检查清单

状态：**PASS_IDENTITY_CONFIRMED**

## 已由用户确认的封面字段

- [x] `author_name`：`兀文昊`。已写入受控配置并完成重建验证。
- [x] `affiliation`：`中国科学院大学`。已写入受控配置并完成重建验证。
- [x] `adviser`：`张晨`。已写入受控配置并完成重建验证。

变更方法：先编辑 `delivery_fields.json`，再完整重跑 Stage-G 构建；不得只在 Word 中手工替换。

## 已由仓库证据补全的坐标元数据

| 图号 | 状态 | 当前值 | 证据 |
|---|---:|---|---|
| Fig. 5.2 | resolved | 无物理状态坐标系；局部二维示意绘图坐标（Sun=(0,0)、Moon=(5.6,0)），原点、轴向和历元不作为数值元数据 | `figures/fig_5_02.py` |
| Fig. 5.3 | resolved | 无物理状态坐标系；局部二维示意绘图坐标（Earth=(0,0)、Moon=(4.0,0)），原点、轴向和历元不作为数值元数据 | `figures/fig_5_03.py` |
| Fig. 5.4 | resolved | 无物理状态坐标系；局部二维日—地—月会合示意坐标（Sun=(0,0)），历元不适用 | `figures/fig_5_04.py` |
| Fig. 5.6 | resolved | 月心瞬时 Sun–Moon 正交旋转坐标，X 指向 Sun、Z 为 Sun–Moon 轨道角动量方向，单位 km；共同历元 2020-06-15T00:00:00Z | `figures/fig_5_06.py;src/qp_orbits/ephemeris.py;data/computed/chapter5_de421_quasi_dro_scenes.csv` |
| Fig. 5.7 | resolved | 月心瞬时 Sun–Moon 正交旋转坐标，X 指向 Sun、Z 为 Sun–Moon 轨道角动量方向，单位 km；历元为 2020-06-01/04/10/15T00:00:00Z | `figures/fig_5_07.py;src/qp_orbits/ephemeris.py;data/computed/chapter5_de421_quasi_dro_scenes.csv` |
| Fig. 5.10 | resolved | Earth–Moon 质心旋转坐标，状态顺序 [x,y,z,xdot,ydot,zdot]，Earth–Moon LU/TU 归一化；项目 BCR4BP 扩展由 DE421 于 2020-06-15T00:00:00Z 初始化，论文自主 CR3BP 工况历元不适用 | `src/qp_orbits/bcr4bp.py;scripts/run_chapter5_fig510_bcr4bp_transfer_audit.py;data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv` |

## comparison panel

- 54/54 `comparison_asset` 已回写 registry，存在性与 SHA256 均通过。
- registry 中 `【待核实】`：0 项。
- DOCX/PDF 中 `【待核实】` 出现次数：0/0。

## 真实性边界复核

- [x] 54 图仅声明工程覆盖，不声明全文严格数值等价。
- [x] Chapter 4 frozen projection holdout 保持 `0/4`、`paper_projection=fail`、`paper_3d=false`。
- [x] Route H physical corrected-rho 不得写成接受的一维实不变子束。
- [x] 失败、boundary、diagnostic 与 proxy 行均保留。
