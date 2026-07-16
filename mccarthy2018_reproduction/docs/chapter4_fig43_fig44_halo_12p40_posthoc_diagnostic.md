# Chapter 4 halo 12.40-day post-hoc source diagnostic

## Evidence boundary

This generator replays the frozen N9 panel-(d) result and evaluates one
predeclared N21 candidate selected only by proximity to the thesis-reported
12.40-day source member. Panel (d) was already exposed. The candidate rows
are post-hoc development diagnostics and cannot replace the frozen v1
holdout, whose status remains `paper_projection=fail`, `paper_3d=false`.

## Machine-readable result

| Source | Figure | T0 [day] | N | Ay [km] | Az [km] | Loss | F1 | Chamfer/D | HD95/D | Area | Post-hoc gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `current_n9` | 4.3 | 12.097007 | 9 | 37765.60 | 31824.70 | 0.5534 | 0.362 | 0.0294 | 0.0987 | 0.486 | fail |
| `current_n9` | 4.4 | 12.097007 | 9 | 37765.60 | 31824.70 | 0.7060 | 0.235 | 0.0476 | 0.1508 | 0.386 | fail |
| `thesis_12p40_n21` | 4.3 | 12.397983 | 21 | 41820.70 | 35772.49 | 0.2311 | 0.668 | 0.0152 | 0.0971 | 1.107 | fail |
| `thesis_12p40_n21` | 4.4 | 12.397983 | 21 | 41820.70 | 35772.49 | 0.3851 | 0.402 | 0.0329 | 0.1192 | 0.911 | fail |

## Candidate source gates

- Curve residual: `7.4898195619619e-11`.
- Determinant error: `3.66648311711515e-09`.
- Unstable multiplier: `1532.08486311907`; relative imaginary part `0`.
- Source Jacobi span: `6.57205840415287e-07`; manifold Jacobi drift `2.58708610090252e-11`.
- The source satisfies the predeclared period/Ay/Az gates. Fig. 4.3 improves
  materially but still misses F1 and HD95; Fig. 4.4 remains below the
  projection gates. No 4/4 outcome is claimed.

## Traceability

- Frozen fit SHA256: `D2767E61A3EBF428ED8242CA00EDE441FF2C0666189E062397AA928277E43374`.
- Frozen holdout run ID: `B18B82934AE43D3F3F451ACA000BCBA5BD3095AF91AF8F20A57B5133E009C27B`.
- Frozen holdout CSV SHA256: `6C5390F938E6E0D882152E59BBDD05BAA4EA04EAC2FA092052DF9AB624688FB1`.
- Camera config SHA256: `7FE3D12CF319A3CBD60B540FFDAD005B5C7B51C8B5F3A2D924B7CFECBC26DFA0`.
- Generator SHA256: `4F45F1D677E4E335ED1D867A36B23B91C1B1B453C4CA56957F3464B087AD34EE`.
- Torus core SHA256: `C235868458715F1BD7690B5EC92A5BE93399E3A46A8E3AAEEF59429B4CFCFE25`.
- Projection core SHA256: `07FF9AEF6D48FDBCC3FEA9D242AF0BE73FAF4D278259D22D3FB1F9D24BA44A82`.
- CSV: `data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv`.
- NPZ: `data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.npz` (SHA256 `E4044290D49C31C25F8323219B560A91C9843F1375C4C5FCE047A075FED46A5A`).
