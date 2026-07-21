# Invariant-bundle submission-candidate final acceptance audit

- Overall status: `pass_with_explicit_boundaries`
- Passed gates: `19/19`
- Validation commands: `19/19` exit 0
- Full unittest count: `241`
- Validation source commit: `fcb8afc8aa5694bc2cb47b7033a4f1c943d2bb3f`
- Validation log SHA256: `E664669C7F0E53D58635FAC2FA7624D0B44A07B9AEC4CA8052FE3FD7F739D668`
- Decision status: `adviser_submission_decision_candidate`; no target journal selected; no external submission authorized.

| gate | category | requirement | observed | status | boundary |
|---|---|---|---|---|---|
| `R1` | `frozen_reproduction` | 54-figure baseline remains complete and unpromoted | 54 targets; 13 V0; 41 V2 | `pass` | engineering coverage only, not thesis-wide equivalence |
| `R2` | `frozen_reproduction` | Chapter-4 frozen projection holdout remains 0/4 | paper_projection=fail; paper_3d=false on 4/4 rows | `pass` | research and post-hoc evidence cannot overwrite the holdout |
| `F1` | `figure_correctness` | all 54 figures have an adviser-facing visual priority | P0_OBVIOUS_MISMATCH=18; P1_MATERIAL_PARTIAL=7; P2_ACCEPTABLE_BOUNDARY=17; P3_SCHEMATIC_PROXY=12 | `pass` | P0/P1 items remain a correction queue, not hidden by numerical gates |
| `H1` | `preregistration` | Stage-H cases, caps, stop rule, and authority boundary are locked | 3 H2 + 2 H3 + 3 H4 + 3 H5 cases | `pass` | no blind family extension or reproduction promotion |
| `H2A` | `stable_bundle` | at least three representative stable-bundle benchmarks | cases=3; accepted improved rows=6 | `pass` | pointwise failures retained; finite case set |
| `H2B` | `stable_manifold` | stable-manifold propagation is stored and gated | rows=54; accepted improved rows=36 | `pass` | fixed one-period CR3BP propagation |
| `H3A` | `route_h_2d` | two physical Route-H rank-two real objects are never relabelled 1D | cases=2; diagnostics=90; never_1d=True | `pass` | frozen Stage-E rank-one failures remain failed |
| `H3B` | `route_h_2d` | rank-two manifold outcomes and bounded QR failures are both retained | accepted Schur rows=4; QR bounded-failure cases=2 | `pass` | method-specific result, not a universal convergence claim |
| `H4` | `long_propagation` | three representative long-event cases are propagated for three periods | cases=3; result rows=12; accepted=8; physical boundary=4 | `pass` | four physical-radius crossings retained; thresholds are diagnostic |
| `H5A` | `sun_earth_expansion` | three distinct new local Sun–Earth source artifacts are validated | distinct local sources=3; authority-boundary cases=3 | `pass` | not an external independent solver or dataset |
| `H5B` | `sun_earth_expansion` | Sun–Earth boundary and failed rows are not promoted | bundle boundary=6, fail=3; manifold boundary=12, fail=6 | `pass` | all improved rows remain boundary under frozen residual/source rules |
| `D1` | `documents` | updated Chinese and English manuscripts are present | 2 Markdown + 2 DOCX manuscripts; Chinese media=10; English media=4 | `pass` | adviser-facing candidate, not venue-formatted submission |
| `D2` | `documents` | claim-evidence matrix is complete and boundary-aware | 20 claims with evidence, thresholds, status, and authority boundary | `pass` | document completeness is not peer-review acceptance |
| `D3` | `documents` | bilingual adviser decision brief is present | Markdown + DOCX; four explicit adviser decisions requested | `pass` | no target journal selected and no external submission authorized |
| `V1` | `verification` | full unittest suite passes | tests=241 | `pass` | failed and boundary regressions remain asserted |
| `V2` | `verification` | baseline --check, target --check, and 54-figure smoke pass | 3/3 commands exit 0 | `pass` | passes engineering coverage, not paper equivalence |
| `V3` | `verification` | base research and all Stage-H generator --check commands pass | 13/13 research/package checks exit 0 | `pass` | checks reproduce stored evidence within frozen scopes |
| `V4` | `verification` | working-tree and staged git whitespace checks pass | git diff --check and git diff --cached --check exit 0 | `pass` | does not imply repository cleanliness or remote publication |
| `S1` | `decision_status` | package status and authorization boundary are exact | adviser_submission_decision_candidate; target journal=false; external submission=false | `pass` | goal ends at adviser decision package, not external submission |

## Boundaries that remain open

- The 54-figure baseline remains engineering coverage, not thesis-wide strict equivalence.
- Chapter 4 remains `0/4`, `paper_projection=fail`, and `paper_3d=false`.
- The figure-correctness audit retains 18 P0 and 7 P1 items as a separate correction queue.
- H3 QR/SVD rank-two attempts are bounded failures; H5 improved rows remain boundaries.
- The three H5 sources are distinct local artifacts, not an external independent solver or dataset.
- No target journal, new theorem, external submission authorization, or peer-review outcome is claimed.

## Adviser decision requested

Decide whether to begin venue selection and venue-specific revision now, or first require additional theory, an external solver/backend, or completion of the P0/P1 figure-correction queue. No external submission action was taken.
