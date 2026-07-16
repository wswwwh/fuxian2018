# Literature-grounded paper positioning

## Decision

`numerical_framework_and_systematic_comparison`

The matrix contains 25 verified formal sources: 21 with a checked DOI and 4 formal thesis/conference sources explicitly recorded as `not_assigned` rather than supplied with a guessed DOI. All nine required topics are covered.

## Why this is the defensible position

- Parameterization methods for invariant tori and whiskers are established in [@HaroLlave2006Numerical; @HaroLlave2006Rigorous; @HaroEtAl2016].
- Cocycle iteration and phase-dependent bundle computation are established in [@Jorba2001; @WyshamMeiss2006; @HuguetLlaveSire2013].
- Continuous orthonormalization, QR/SVD spectral diagnostics, and covariant Lyapunov vectors are established in [@DieciRussellVanVleck1994; @DieciVanVleck2002; @GinelliEtAl2007; @KuptsovParlitz2012].
- Real and periodic Schur reordering are established numerical linear algebra in [@BaiDemmel1993; @GranatKagstrom2006].
- CR3BP quasi-periodic tori and their manifold applications predate this study [@OlikaraHowell2010; @McCarthy2018; @McCarthyHowell2023].

The present work therefore does **not** claim a new invariant-bundle theorem, the first Schur method, the first shifted QR/SVD method, or the first quasi-periodic CR3BP manifold computation. Its supported contribution is an auditable 15-case comparison framework that binds three numerical routes to frozen acceptance metrics, independent Schur-backend agreement, bounded failure classification, ablation evidence, fresh-process reproducibility, and CI guards.

## Scientific truth boundary

- The frozen McCarthy reproduction level is unchanged.
- Chapter 4 remains a `0/4` projection holdout with `paper_projection=fail` and `paper_3d=false`.
- The physical Route H corrected-rho cases remain two-dimensional real conjugate subspaces and failed one-dimensional acceptance; the legacy seed-rho case is only a positive control.
- A two-dimensional real Schur subspace is not relabelled as a one-dimensional real direction.
- Local bundle convergence and global manifold-sheet convergence are reported separately.
- This positioning is **not_submission_ready**: literature coverage and independent validation do not remove the unresolved scientific limitations.

## Rejected stronger labels

- `methodological_innovation`: rejected because the constituent algorithms and theory are established in the verified literature.
- `failure_mode_and_diagnostic_study`: informative as a secondary emphasis, but too narrow for the full benchmark, independent-backend, manifold, and reproducibility scope.
