# Presentation Outline

## 1. Objective

Explain that the project is an auditable engineering reproduction of McCarthy
2018 figures, not a claim of complete thesis numerical equivalence.

## 2. Current Coverage

Show the 54-figure status table from
`docs/reproduction_report/figure_status_appendix.md`.

## 3. Core Upgrade: Chapter 3 Route H

Suggested figure/table: Fig. 3.16, Fig. 3.17, and
`data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`.

Speaker notes:

- Route H accepted validation rows: `30`.
- Best fixed-time quasi-DRO max abs z: `14573.10318409037` km.
- Rows above 10,500 km: `30`.
- Rows above 11,000 km: `29`.
- Max map residual: `6.469474407020314e-10`.
- Max one-map Jacobi drift: `7.760059261840979e-11`.

Message: Fig. 3.16 / Fig. 3.17 now have an accepted fixed-time source layer.
Do not call this original McCarthy raw branch data.

## 4. Remaining Boundaries

- Fig. 3.10 q=8 is local multiple shooting, not a robust single-shoot periodic
  orbit.
- Chapter 4 Fig. 4.3-4.6 now use corrected fixed-time full-torus surfaces and
  pass 16/16 numerical plus 16/16 epsilon-dependent configuration-reach rows; Fig. 4.7-4.8 remain legacy
  comparisons.
- Fig. 4.2 passes the native-image pointwise gate over 89% of the thesis curve,
  but the final fold tail is still uncovered.
- Fig. 4.3-4.6 projection evidence is diagnostic only (14/16 alerts), with
  `paper_projection=not_run`, `paper_3d=false`, and epsilon uncalibrated.
- Route H remains at 1/31 real-hyperbolic members; its DG/manifold gate fails and
  the staged goal is unchanged.
- Chapter 5 source-layer BCR4BP/optimization audits do not replace every thesis
  application figure.

## 5. Next Work

Choose one of three focused tracks: original branch-data search, Chapter 4
thesis-scale manifold replacement, or Chapter 5 per-figure high-fidelity
equivalence audits.
