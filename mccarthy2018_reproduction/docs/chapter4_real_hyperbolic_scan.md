# Chapter 4 Real-Hyperbolic Route H Scan

## Summary

- Strict Route H members scanned: `31`
- Real-hyperbolic passes: `1`
- Failures: `30`
- Relative-imaginary tolerance: `1e-06`
- Passing member indices: `[68]`
- Passing max-abs-z range: `13404.12772869574..13404.12772869574 km`

## Decision Rule

A member passes only when both stable and unstable hyperbolic eigenvalues have
relative imaginary part at or below the stated tolerance, the DG determinant
error is below `1e-9`, and the selected complex pair has reciprocity error below
`1e-8`. A magnitude-only reciprocal pair is insufficient.

This scan selects candidates for a subsequent manifold audit. It does not itself
promote Chapter 4 or replace original Fig. 4.1-4.8.
