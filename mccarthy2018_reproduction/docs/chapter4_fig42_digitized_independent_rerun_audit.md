# Chapter 4 Figure 4.2 digitized independent rerun audit

The native-image digitization was executed twice in separate Python processes
with:

```powershell
$env:PYTHONPATH='src'
& 'D:\miniconda3\envs\cislunar\python.exe' `
  'scripts/run_chapter4_fig42_digitized_comparison_audit.py'
```

Both runs reported:

- status: `pointwise_overlap_pass_full_curve_coverage_boundary`
- overlap rows: `13`
- thesis-time coverage: `0.8902665099213599`
- pointwise RMSE: `0.3710034126027414`
- maximum absolute error: `0.5108820184630076`
- uncovered tail: `0.04945011318863024` days

The following SHA256 values were identical before and after the second run:

| artifact | SHA256 |
|---|---|
| `outputs/reference_pages/fig_4_2_reference_native.png` | `BF013B6B97E09436AE5333422E52E53ECBECA62DAABAAEFDC2530FFA4E270B12` |
| `data/digitized/fig_4_2_axis_calibration.csv` | `217290FF1139BD4C86063838BDA851AC01E7BB18FA461D304B868B9C74E93BEB` |
| `data/digitized/fig_4_2_digitized_points.csv` | `279815C7D73300CF3548D83769C3877C035FE73ADF62EE7BEE822B3380DFE309` |
| `data/digitized/fig_4_2_computed_vs_digitized.csv` | `E44AC847E8B9480AF19F218CEE128E938E84C036B9D60CC5804263AE5E97839C` |
| `data/computed/chapter4_fig42_digitized_comparison_audit.csv` | `9F3FDB7F7E9F07F08285B7A9804E8364CEC72B1CC5C2B9AA229601135781F7BD` |
| `docs/chapter4_fig42_digitized_comparison_audit.md` | `FEE509D4883C954DD2A9481159C7D9BE4321BC8CECE1DE63425419558D5F5D8A` |
| `outputs/diagnostics/fig_4_2_digitized_comparison.png` | `4E15A59C48B4CE282FDB3439CAFEB383156D26DC4464E671CC1A9FE304CA2733` |

This proves deterministic extraction, calibration, comparison, reporting, and
PNG rendering for the current inputs. It does not change the explicit
`full_curve_coverage=false` boundary.
