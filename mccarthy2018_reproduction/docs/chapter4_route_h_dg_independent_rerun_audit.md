# Chapter 4 Route H DG/manifold independent rerun audit

This audit records two fresh-process runs of the strict Route H member-68
manifold command after the real-hyperbolic gate was tightened to relative
imaginary tolerance `1e-6`.

## Exact command

```powershell
$env:PYTHONPATH='src'
& D:\miniconda3\envs\cislunar\python.exe scripts/run_chapter4_route_h_dg_manifold_audit.py `
  --member-index 68 --min-z-km 10500 --max-step 0.02 `
  --duration-periods 0.1 --time-samples 12 --perturbation-scale 1e-7
```

## Stable outputs

| artifact | SHA-256 |
|---|---|
| `data/computed/chapter4_route_h_quasi_dro_dg.csv` | `86CD43A429DE0E064770D213C540104E11156FB642E83676026321E8DB15D721` |
| `data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv` | `013E167B89FB1A8AD6BF4E6F35B6B17419ECE8A493B677BDAA0C23341E106828` |
| `docs/chapter4_route_h_quasi_dro_dg_manifold_audit.md` | `EA843CAA53DE61504A01FA045058D006D929546E8318E4CB41C20C70E4146426` |
| `outputs/figures_png/fig_4_route_h.png` | `A2E46A6BBE8332F760291F17FC3E3AE055E664B2AED4A80DF0122A5415E359CB` |
| `outputs/figures_pdf/fig_4_route_h.pdf` | `86FFBE9040302BDA5E48C59F024CE690083DD7E6AB444339B7B39C5D5A43A001` |

The before/after hashes for the DG CSV, manifold CSV, and audit report were
identical across the second fresh-process rerun.  Member `68` has determinant
error `2.391e-13`, real stable/unstable reciprocity error `3.442e-15`, and
local-probe Jacobi drift `8.882e-16`.  The all-member scan remains the governing
boundary: only `1/31` strict Route H members passes the real-hyperbolic gate.

The independent all-member scan command is
`scripts/run_chapter4_real_hyperbolic_scan.py --max-step 0.02
--relative-imaginary-tolerance 1e-6`.  Its CSV and Markdown hashes were also
identical before and after a fresh-process rerun:

- scan CSV: `91793D4B5AD8425FDF8E58E29E7CB21E5AA2FCB45D0A47D3DB3016B7961D1796`
- scan report: `12EE45376542DBF80B140DF158DEA56F2D12182807649EAE285312920AF728FB`
