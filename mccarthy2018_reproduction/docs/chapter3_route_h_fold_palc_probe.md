# Chapter 3 Route H Fold PALC Probe

## Result

- Status: `pass`
- Accepted PALC steps: `9/9`
- Accepted negative-delta-rho steps: `9`
- Mean Jacobi start / end: `2.922282866714092` / `2.922281560541282`
- Net Jacobi change: `-1.306173e-06`
- Final rotation angle: `1.444073386595544`
- Final amplitude: `0.02639331229182024`
- Failure: `N/A`

## Interpretation

The fixed-rotation continuation stopped because it required monotonically increasing
rotation number. This probe keeps the ordered pseudo-arclength secant orientation.
A passing negative-`delta_rotation` row demonstrates that the branch crosses a
rotation-number fold while Jacobi continues to decrease and the invariant-curve,
phase, arclength, and pointwise-Jacobi audits remain within tolerance.

This is a bounded fold-crossing proof, not yet the full thesis-target cold start.
The next acceptance step is integrating this PALC fallback into the persistent
Route H generator and reaching all requested Jacobi targets from an empty cache.
