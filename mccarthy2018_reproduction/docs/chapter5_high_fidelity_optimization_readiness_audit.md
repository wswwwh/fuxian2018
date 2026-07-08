# Chapter 5 High-Fidelity / Optimization Readiness Audit

## Purpose

This audit records the remaining implementation boundary after the Route H
quasi-DRO branch became available to Chapter 5. It is intentionally stricter
than the DE421 geometry baseline: a plotted DE421 embedding is not a
BCR4BP/ephemeris-corrected or optimized trajectory.

## Gate Rows

- `C5-HF-ROUTE-H-BASELINE`: status `pass`, metric `fig_5_6_png_bytes` = `746932`, decision `use_route_h_de421_baseline_as_initial_guess`
- `C5-HF-BCR4BP-DYNAMICS`: status `pass`, metric `accepted_bcr4bp_audit_rows` = `4`, decision `use_bcr4bp_kernel_for_next_correction_layer`
- `C5-HF-DYNAMICS-CORRECTION`: status `pass`, metric `accepted_dynamics_correction_rows` = `3`, decision `use_bcr4bp_segment_correction_as_first_high_fidelity_correction_layer`
- `C5-HF-TRANSFER-OPTIMIZATION`: status `pass`, metric `accepted_optimized_transfer_rows` = `25`, decision `route_h_bcr4bp_optimized_transfer_source_layer_ready`
- `C5-HF-INTERFACE-CONTRACT`: status `interface_required`, metric `required_interface_fields` = `5`, decision `implement_bcr4bp_ephemeris_optimization_interface`
- `C5-HF-READINESS-STATUS`: status `pass`, metric `missing_high_fidelity_capabilities` = `0`, decision `chapter5_high_fidelity_optimization_source_layer_ready`

## Interface Required Next

The next implementation should introduce a small, auditable Chapter 5 interface
before regenerating application figures:

1. Dynamics model: BCR4BP or ephemeris-corrected Earth-Moon-Sun propagation.
2. Free variables: initial state, segment times, insertion phase, and optional
   impulse/control variables.
3. Constraints: segment continuity, endpoint/event targets, Jacobi or energy
   diagnostics where meaningful, eclipse/line-of-sight constraints when used.
4. Objective: transfer cost, defect norm, eclipse exposure, or a documented
   multi-objective scalarization.
5. Acceptance thresholds: residual, endpoint error, frame consistency,
   optimizer convergence, and figure-source provenance.

## Decision

Readiness status is `pass` with
`missing_high_fidelity_capabilities` = `0`. Chapter 5 can use the
Route H / DE421 baseline as an initial guess layer. The BCR4BP short-segment
defect-correction and transfer-optimization source layers now provide accepted
audit rows and rendered figure artifacts, but they remain source-layer evidence
rather than a full replacement of every original thesis application figure.
