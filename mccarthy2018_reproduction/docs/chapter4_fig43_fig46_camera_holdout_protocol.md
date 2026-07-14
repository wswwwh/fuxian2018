# Chapter 4 Figures 4.3-4.6 frozen camera/epsilon protocol

Protocol: `chapter4_camera_epsilon_holdout_v1`.

## Evidence boundary

All 16 thesis panels were already visible in the legacy diagnostic. Panel
(d) is therefore only a **programmatic frozen holdout with historical
exposure**, not a genuinely blind test. A pass may upgrade the project to
`paper_projection_holdout_pass`; it can never set `paper_3d_equivalence=true`.

## Frozen split and leakage rule

- Panels (a),(b): camera/epsilon training.
- Panel (c): model-selection validation.
- Panel (d): one programmatic frozen-holdout evaluation after parameters,
  thresholds, rendering, crops, and source hashes are locked.
- The panel-(d) red mask is forbidden in fitting, model selection,
  refinement, and threshold changes. If anything changes after viewing the
  new result, panel (d) is downgraded to development evidence.

## Frozen parameterization

- Camera: `shared_per_figure_orthographic_2x3_affine_from_static_fiducials`; one camera per figure, shared by all panels.
- No panel-specific affine, homography, crop shift, ICP, or non-rigid
  registration is allowed.
- The thesis reports only a small epsilon, not its numeric value or whether
  it is shared. The primary hypothesis H0 uses one global epsilon. H1 uses
  one scalar per source-torus family, shared across +x/-x, and is admitted
  only if panel-(c) validation loss improves by at least 10% globally and
  neither family worsens. Branch/figure/panel-specific epsilon is forbidden.
- Coarse grid: `[1.590990257669732e-07, 2.25e-07, 3.181980515339464e-07, 4.5e-07, 6.363961030678928e-07, 9e-07, 1.2727922061357855e-06]`.
- Refinement: `five_log2_points_inclusive_within_plus_minus_0.25_octave_around_training_selected_coarse_candidate`.
- Projection loss: `chamfer_over_D+0.5*(1-F1_at_0.01D)+0.25*abs(log(area_ratio))+0.25*HD95_over_D`.
- Model selection: `select_each_candidate_on_mean_train_projection_loss_ab_then_compare_H0_H1_once_on_validation_c;choose_H1_only_if_global_relative_improvement_ge_0.10_and_neither_family_validation_loss_worsens`.
- Red mask: `R>=55;R-max(G,B)>=14;R>=1.10*max(G,B)`; morphology: `none`; normalized grid:
  `512x512`.

## Project-defined holdout gates

- Static-anchor RMSE <= `4.0` px and maximum error
  <= `8.0` px.
- Symmetric Chamfer <= `0.020D`.
- F1 at `0.01D` >= `0.70`.
- HD95 <= `0.050D`.
- Area ratio in `[0.67, 1.50]`.
- Every one of the four panel-(d) rows must pass; averages cannot hide a
  failed figure. These are project gates, not thesis-reported tolerances.

## Registered panel rows

| Figure | Panel | Role | Time [day] | Family | Branch |
|---|---:|---|---:|---|---|
| 4.3 | (a) | `train` | 7.79 | halo | plus_x |
| 4.3 | (b) | `train` | 9.75 | halo | plus_x |
| 4.3 | (c) | `validation` | 11.39 | halo | plus_x |
| 4.3 | (d) | `programmatic_frozen_holdout` | 13.02 | halo | plus_x |
| 4.4 | (a) | `train` | 7.79 | halo | minus_x |
| 4.4 | (b) | `train` | 9.75 | halo | minus_x |
| 4.4 | (c) | `validation` | 11.39 | halo | minus_x |
| 4.4 | (d) | `programmatic_frozen_holdout` | 13.02 | halo | minus_x |
| 4.5 | (a) | `train` | 8.05 | vertical | plus_x |
| 4.5 | (b) | `train` | 10.08 | vertical | plus_x |
| 4.5 | (c) | `validation` | 11.77 | vertical | plus_x |
| 4.5 | (d) | `programmatic_frozen_holdout` | 13.46 | vertical | plus_x |
| 4.6 | (a) | `train` | 8.05 | vertical | minus_x |
| 4.6 | (b) | `train` | 10.08 | vertical | minus_x |
| 4.6 | (c) | `validation` | 11.77 | vertical | minus_x |
| 4.6 | (d) | `programmatic_frozen_holdout` | 13.46 | vertical | minus_x |

## Bound sources

- `outputs/reference_pages/fig_4_3_reference.png`: SHA256 `DDD9E4B1EF0B3B8D456BBF1AEBA66AB1E8A672D8907FFF22B3329269536158EE`.
- `outputs/reference_pages/fig_4_4_reference.png`: SHA256 `72F9F9A41FAF5DB2E00F021866086EE5A982AB35EC2EC05EC2C0C7D1D2782256`.
- `outputs/reference_pages/fig_4_5_reference.png`: SHA256 `ED1D3B2F5C9977ABFEA717FAB4F24832B09668B8B0972DABE8338133B19A1746`.
- `outputs/reference_pages/fig_4_6_reference.png`: SHA256 `7E18E60DE4C373BE50A908128565B36FBFBFB93A1FBF6EC81EE1D25F901B2CD3`.
- `data/computed/chapter4_fig43_fig44_global_manifold_audit.npz`: SHA256 `7E077D5557C3392BBE54C7D2CBCB7CF13EF649D2855A0D8B02BF2BB0047ADBB6`.
- `data/computed/chapter4_fig45_fig48_vertical_manifold_audit.npz`: SHA256 `4C494631B23964D9741D08D758D62EDC4F6FF1B97F5C164D48583F9A7BF09CA7`.

The machine-readable protocol is
`data/computed/chapter4_fig43_fig46_camera_holdout_protocol.csv`. At registration time,
`paper_projection_acceptance=not_run` and
`paper_3d_equivalence=false` for every row.
