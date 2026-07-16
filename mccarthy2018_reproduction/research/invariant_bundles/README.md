# Real invariant-bundle research layer

This directory is the research layer that follows the frozen McCarthy 2018
reproduction baseline.  It does not own or modify the 54-figure validation
table, the staged goal gate, or the frozen Chapter-4 camera holdout.

The governing equation is

```text
A(theta) E(theta) = E(theta + rho) R(theta).
```

`E` is always real and orthonormal.  Its stored dimension is either one for a
real direction or two for a real representation of a complex conjugate pair.
A two-dimensional result is never relabelled as a one-dimensional manifold
direction.

## Authority order

1. `benchmarks/benchmark_registry.csv` freezes case selection and source hashes.
2. `configs/` freezes campaign caps and research-only numerical thresholds.
3. `src/qp_orbits/invariant_bundles.py` contains reusable algorithms.
4. `experiments/` documents prototypes and failure modes.
5. `results/` contains generated CSV/NPZ/checkpoints.
6. `paper/` may summarize only claims supported by generated results.

## Boundary rules

- Research status is never promoted into reproduction status automatically.
- Existing failed and boundary cases remain visible.
- The legacy Route-H member-68 positive control and the physical corrected-rho
  case are separate benchmarks because they use different rotations.
- Projection equivalence remains a frozen evidence boundary.

