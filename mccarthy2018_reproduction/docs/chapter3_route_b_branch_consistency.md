# Chapter 3 Route B Branch Consistency Audit

## Purpose

This audit checks the Route B `E_amplitude_monitor_large_step` diagnostic
free-time branch. It does not update Figure 3.16, Figure 3.17, fixed-mapping
accepted branch CSV files, `figure_validation_table.csv`, Chapter 5, or the
teacher package.

## Branch Consistency

- Diagnostic free-time branch continuous: `True`
- Amplitude monotone: `True`
- Mapping-time drift monotone: `True`
- Highest diagnostic free-time member: `11107.54149221647` km
- Highest mapping time: `14.80556377691894` days

The continuity classification uses phase-aligned row-to-row distance before raw
state distance. The branch remains a diagnostic free-time branch, not a
constant-mapping-time McCarthy reproduction.

## Phase-Gauge Robustness

- Phase-gauge robustness passed all tests: `True`
- Small perturbation recovery passed: `True`
- Robust rows: `49` / `49`

The phase-shift rows record requested shift, actual integer shift index, actual
phase shift in radians, and shift method. Because `N=61` is odd, requested
quarter/half shifts are not treated as exact unless the recorded index and
radian shift show it.

## Fixed-Time Projection

- Accepted fixed-time projections: `0`
- Accepted projected candidate beyond 10,500 km: `False`
- Accepted projected candidate beyond 11,000 km: `False`
- Best accepted projection: `N/A` km

A projection failure means the diagnostic free-time branch cannot directly serve
as a constant-mapping-time reproduction. A projection that falls back near the
endpoint indicates that the high-amplitude gain mainly came from mapping-time
drift. A projection above 10,500 or 11,000 km is only a candidate fixed-time
projection result requiring multi-member continuation confirmation.

## Category Separation

- Diagnostic free-time branch: audit-passing Route B members with free mapping
  time.
- Fixed-time projected candidate: one-member projection to the original mapping
  time that still needs multi-member fixed-time continuation confirmation.
- Confirmed fixed-time continuation branch: not produced by this audit.

Only a confirmed fixed-time continuation branch can support a later discussion
of replacing Figure 3.16 or Figure 3.17 data sources.

## Next Action

Keep the free-time branch as a diagnostic result and prioritize Fourier/collocation BVP or a smaller-family sanity check before figure-source work.
