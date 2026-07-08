# Chapter 5 Upstream Application Gate Audit

## Purpose

This file records whether Chapter 5 can use the upgraded upstream quasi-DRO
evidence without overstating the result as high-fidelity or optimized.

## Current Route H Input

- Source member id: `54`
- Max abs z: `14573.10318409037` km
- Rotation angle rho: `1.457169483818128` rad
- Mapping time: `14.74932760227518` days

## Gate Rows

- `C5-UPSTREAM-ROUTE-H-INPUT`: status `pass`, metric `route_h_member_max_abs_z_km` = `14573.10318409037`, decision `use_route_h_member_for_chapter5_baseline`
- `C5-UPSTREAM-CHAPTER4-SOURCE`: status `pass`, metric `fig_4_route_h_png_bytes` = `539093`, decision `route_h_chapter4_source_available`
- `C5-ROUTE-H-DE421-BASELINE`: status `pass`, metric `fig_5_6_png_bytes` = `746932`, decision `route_h_de421_baseline_available`
- `C5-HIGH-FIDELITY-OPTIMIZATION`: status `pass`, metric `missing_high_fidelity_capabilities` = `0`, decision `use_readiness_audit_source_layer_result`
- `C5-STAGED-APPLICATION-STATUS`: status `route_h_bcr4bp_optimization_source_layer_passed`, metric `route_h_de421_baseline_pass` = `true`, decision `chapter5_source_layer_optimization_available`

## Decision

Figures 5.6 and 5.7 now have a regenerated Route H / DE421-oriented baseline
from the accepted high-amplitude quasi-DRO branch. The stricter high-fidelity
readiness decision is generated separately by
`scripts/run_chapter5_high_fidelity_optimization_readiness_audit.py`; when that
audit passes, the Chapter 5 source-layer optimization result supersedes this
baseline-only gate.
