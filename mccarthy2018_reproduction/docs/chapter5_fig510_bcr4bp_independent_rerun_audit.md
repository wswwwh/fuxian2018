# Chapter 5 Figure 5.10 BCR4BP independent rerun audit

Date: 2026-07-14

## Decision

Two fresh Python processes regenerated the dedicated Fig. 5.10 numerical audit
and its diagnostic figure. The audit CSV, saved trajectories, Markdown report,
PNG, and PDF have identical SHA256 hashes before and after the rerun. The two
BCR4BP cases therefore pass the deterministic-rerun gate.

This audit confirms reproducibility of the project extension only. It does not
change `paper_equivalence=false`: the epoch is project-selected, the endpoints
remain CR3BP NRHO states, and the paper impulse/pointwise-geometry gates are not
satisfied.

## Commands

```powershell
$env:PYTHONPATH='src'
D:\miniconda3\envs\cislunar\python.exe scripts\run_chapter5_fig510_bcr4bp_transfer_audit.py
D:\miniconda3\envs\cislunar\python.exe figures\diagnostics\plot_fig_5_10_bcr4bp_extension.py
```

The numerical audit and plot were each launched as a separate process. Hashes
were computed before and after both commands. PDF creation/modification dates
are intentionally omitted from plot metadata so that the rendered PDF is a
deterministic artifact rather than a timestamp-dependent file.

## Frozen inputs and implementations

| artifact | SHA256 |
|---|---|
| `data/raw/ephemeris/de421.bsp` | `A20A7139DA04CBC462454634918E9A9CA69127044E2CC9D4F9C16E238D2DEEDC` |
| `data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv` | `36FFA4FCD7D88E9EAB792D98A9B0FDB1E20662418B55BF9EA8F92F56D98A12B1` |
| `src/qp_orbits/bcr4bp.py` | `885D1A0FC4038CDE93A003C332510D158D543ECD0F5CC3B380A0ADC3CCB4EE4C` |
| `src/qp_orbits/ephemeris.py` | `17AD032EFE76B9CA8C5FFEEB3417AAE200AB9FCCA3048E0286FEB418ACA8596B` |
| `scripts/run_chapter5_fig510_bcr4bp_transfer_audit.py` | `901FCB8B62D4679439600E96059F2AC336C33FA746FF16952B0D445D8E8D0DB1` |
| `figures/diagnostics/plot_fig_5_10_bcr4bp_extension.py` | `12A6D601F94223755531EE0AE9F6D298E127FE4D09B5301972FC5E053D0C26F3` |

## Rerun hash equality

| regenerated artifact | SHA256 before | SHA256 after | equal |
|---|---|---|---|
| `data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv` | `A0C492238C79E294EC02FF985914F55A1508519378933BC605403674D530E15B` | `A0C492238C79E294EC02FF985914F55A1508519378933BC605403674D530E15B` | true |
| `data/computed/chapter5_fig510_bcr4bp_transfer_trajectories.csv` | `86327BE732749DD78F764459767EB325D61A56C8C70978BED10F633E95526DA7` | `86327BE732749DD78F764459767EB325D61A56C8C70978BED10F633E95526DA7` | true |
| `docs/chapter5_fig510_bcr4bp_transfer_audit.md` | `1A37F8F201DFBEA56CF06A133D16F82A3DBD981F806B51B37785BBFC6DF6CF2F` | `1A37F8F201DFBEA56CF06A133D16F82A3DBD981F806B51B37785BBFC6DF6CF2F` | true |
| `outputs/diagnostics/fig_5_10_bcr4bp_extension.png` | `7C06A44B83654E10ADC9035EDCA2F98669E2B352E55757DE06FE6AF6FEFAF493` | `7C06A44B83654E10ADC9035EDCA2F98669E2B352E55757DE06FE6AF6FEFAF493` | true |
| `outputs/diagnostics/fig_5_10_bcr4bp_extension.pdf` | `FA5E97C214C490C4C4968E1FFD8013B56D3EC73E2A03275EC5B842C40426F27D` | `FA5E97C214C490C4C4968E1FFD8013B56D3EC73E2A03275EC5B842C40426F27D` | true |

## Numerical checkpoint

- Case 1, 23 days: independent endpoint error
  `4.819078391415363e-05 km`, total delta-v `72.62814172854959 m/s`.
- Case 2, 12.4 days: independent endpoint error
  `8.357550997979159e-06 km`, total delta-v `89.04994709685531 m/s`.
- Strict dense-output lunar-clearance minima are `4147.683824658591 km`
  and `4657.413538414054 km` for cases 1 and 2, respectively.
- Numerical acceptance: `2/2`.
- Paper equivalence: `0/2`.
