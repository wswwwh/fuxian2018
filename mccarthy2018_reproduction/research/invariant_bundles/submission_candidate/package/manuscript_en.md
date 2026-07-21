# Auditable Real Invariant-Bundle Computation and Manifold Extensions for Quasi-Periodic CR3BP Tori

> Status: `adviser_submission_decision_candidate`. This bilingual package is ready for an adviser’s venue/submission decision; no target journal has been selected and no external submission is authorized.


- Author: Wuwenhao Wu (兀文昊)
- Adviser: Chen Zhang (张晨)
- Institution: University of Chinese Academy of Sciences
- Package date: 2026-07-21

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`

## 1. Introduction

Quasi-periodic orbit manifolds are frequently seeded from eigenvectors of a
large discrete differential or from eigenvectors computed independently at
each phase.  Both shortcuts can obscure the actual object of interest: a real
subbundle transported by a phase-shifted linear cocycle.  A complex selected
eigenvector may be silently projected to its real part, adjacent phases may
jump by sign or subspace, and a direction that looks smooth at one spectral
resolution may not converge as the phase grid is refined.

This study starts only after freezing the McCarthy 2018 reproduction baseline.
The baseline contains 54 engineering outputs
(13 V0 and 41 V2),
but it is explicitly not a thesis-wide strict-equivalence claim.  The research
layer therefore treats reproduction artifacts as immutable benchmark sources
and never promotes research status into the figure-validation table.

The paper evaluates three numerical routes: a deliberately retained pointwise
eigendecomposition baseline, an ordered partial real-Schur subspace method, and
a shifted QR/SVD cocycle iteration.  The contribution is an auditable framework
and systematic comparison across 15 cases and four families.  It is not a claim
of a new invariant-bundle theorem.

## 2. Problem formulation

Let an invariant curve be sampled at odd phases
`theta_i = 2*pi*i/N`.  A local state-transition matrix `A(theta_i)` maps a
perturbation at `theta_i` to `theta_i + rho`.  A real rank-`k` bundle is an
orthonormal matrix field `E(theta) in R^(6 x k)` satisfying

$$
A(\theta)E(\theta) \approx E(\theta+\rho)R(\theta),
$$

where `R(theta)` is scalar for `k=1` and a real `2 x 2` reduced map for `k=2`.
The normalized local residual is

$$
r(\theta_i)=
\frac{\lVert A_i E_i-E_{i+\rho}(E_{i+\rho}^{T}A_iE_i)\rVert_F}
     {\max(\lVert A_iE_i\rVert_F,\epsilon_\mathrm{mach})}.
$$

The audit records maximum and mean residual, adjacent-phase and cross-resolution
principal angles, selected spectrum, relative imaginary part, reciprocal-pair
error, local multiplier estimate, runtime, memory estimate, status, and failure
reason.  A rank-two real subspace is never relabelled as a rank-one direction.

## 3. Quasi-periodic orbit and cocycle model

For each registry case, the stored invariant-curve nodes are propagated for the
frozen mapping time with the CR3BP variational equations.  The terminal state
is compared with Fourier interpolation of the source curve at `theta+rho`.
Only after this map revalidation passes is the cocycle used by a method.

The collocation operator is

$$
G_N=(P_{\theta+\rho\rightarrow\theta}\otimes I_6)
    \operatorname{diag}(A_0,\ldots,A_{N-1}),
$$

where `P` is the odd-grid trigonometric interpolation matrix.  This operator is
useful for ordered spectral-block selection, while the reported scientific
criterion remains the pointwise cocycle equation above.

## 4. Failure modes of pointwise eigenselection

The baseline eigendecomposes each local `A_i`, selects the stable or unstable
candidate by multiplier magnitude, takes a real part, normalizes each node, and
aligns adjacent signs.  It therefore reproduces the conventional failure mode
rather than hiding it.  Across all 15 cases it obtains
0 accepted results; its high-resolution maximum
residuals are 1.240e-01,
1.598e-01, and
1.434e-01 for Halo N45,
Vertical N57, and Sun–Earth member 468.

The Route-H controls expose a second failure mode.  The saved scan classified
member 68 as a near-real positive control under the seed rotation.  Direct
revalidation shows that this legacy operator has a curve-map residual of
1.988e-03.
The physically corrected rotation closes at
8.697e-13,
but its selected block is rank two with relative imaginary part
0.342.
Thus “near-real DG eigenvalue” and “validated physical one-dimensional bundle”
are not interchangeable claims.

## 5. Proposed invariant-bundle method

The term *proposed* here refers to the evaluated numerical framework, not to a
new mathematical theorem.  The first improved route extracts a selected real
partial-Schur block from `G_N`.

```latex
\begin{algorithm}[t]
\caption{Ordered partial real-Schur bundle tracking}
\begin{algorithmic}[1]
\Require Local matrices $A_i$, phases $\theta_i$, rotation $\rho$, branch
\Ensure Real bases $E_i$, rank $k\in\{1,2\}$, residuals $r_i$
\State Assemble $G_N=(P_{\theta+\rho\rightarrow\theta}\otimes I)\operatorname{diag}(A_i)$
\State Order hyperbolic roots by distance to the real axis
\If{the selected root is real within the frozen tolerance}
  \State Set $k\gets1$ and form a normalized real vector
\Else
  \State Set $k\gets2$ and realify the conjugate pair with real/imaginary columns
\EndIf
\State Orthonormalize the selected block and verify $\lVert G_NQ-Q(Q^TG_NQ)\rVert_F$
\State Reshape into nodewise bases, apply local QR, and align adjacent phases
\State Compute $R_i=E_{i+\rho}^TA_iE_i$ and $r_i$
\end{algorithmic}
\end{algorithm}
```

The second route is independent shifted QR/SVD graph iteration.

```latex
\begin{algorithm}[t]
\caption{Shifted QR/SVD cocycle iteration}
\begin{algorithmic}[1]
\Require $A_i$, $\theta_i$, $\rho$, rank $k$, cap $K=200$
\Ensure Real phase-aligned bases $E_i$ and convergence history
\State Initialize each $E_i$ from the leading local right-singular subspace
\For{$j=1,\ldots,K$}
  \State Transport $F_i\gets A_iE_i$ and apply local QR
  \State Align frames on the shifted grid $\theta_i+\rho$
  \State Interpolate $F$ back to the base grid and apply local QR
  \State Align to the previous iterate and along phase
  \State Stop if the maximum subspace angle is at most $2\times10^{-6}$ degrees
\EndFor
\State Compute the cocycle residual; retain nonconvergence as a failed result
\end{algorithmic}
\end{algorithm}
```

## 6. Numerical implementation

All source integrations use DOP853 with `rtol=1e-11`, `atol=1e-13`, and fixed
maximum steps (`0.01` Earth–Moon, `0.005` Sun–Earth).  Campaign caps are 15
cases, N57, 200 QR iterations, and 1800 seconds.  Per-case cocycle checkpoints
are keyed by state-artifact hash, state key, mapping time, rotation, mass ratio,
and integration step.  The research pass threshold is `max residual <= 1e-6`;
`1e-6 < residual <= 1e-3` is a boundary unless another failure applies.  These
are research-only thresholds and do not modify reproduction gates.

The locked Windows SciPy runtime cannot execute `scipy.linalg.schur` and raises
`0xc06d007f`.  The stored implementation therefore constructs and verifies a
selected real *partial* Schur block from the ordered invariant eigenpair.  This
limitation is explicit and motivates later backend cross-validation.

## 7. Benchmark families

The registry contains five Earth–Moon quasi-halo cases, three Earth–Moon
quasi-vertical cases, five Route-H cases when the physical and legacy member-68
operators are counted separately, and two Sun–Earth L1 cases.  Halo includes
N21/N33/N45 lifts, a smaller N15 member, and the old N9 low-resolution negative
control.  Vertical includes N33/N45/N57.  Route H includes physical members 17,
32, 54, and 68 plus the legacy member-68 operator.  Sun–Earth includes accepted
active-geometry member 468 and a saved smaller-amplitude checkpoint.  No branch
is blindly extended during benchmarking.

## 8. Resolution and phase-continuity tests

The partial real-Schur method records 7 accepted,
4 boundary, and
4 failed cases.  QR/SVD records
10 accepted and
5 failed cases.  On Halo N45 their maximum residuals
are 5.999e-11 and
4.403e-12; on Vertical N57 they
are 6.373e-08 and
3.891e-09; on Sun–Earth 468
they are 6.543e-07 and
9.472e-09.

Cross-resolution principal angles become small for both improved methods, but
that fact alone is insufficient.  Full-sheet distances relative to the highest
resolution remain approximately 0.0219 and 0.0150 for Halo N21/N33, and 0.0245
and 0.0195 for Vertical N33/N45.  All exceed the retained 0.01 boundary.

## 9. Global manifold experiments

Stage F uses seven cases, three methods, three full-state perturbation norms
(`5e-8`, `1e-7`, `2e-7`), two signs, and 41 time samples, for 126 stored rows.
Within each case, methods share source states, phases, propagation duration,
integrator, tolerances, coordinates, and stopping rule.  The maximum Jacobi
drift is 2.220e-15; the maximum initial linear-growth-ratio
deviation is 1.127e-06.

At Halo N45, Vertical N57, and Sun–Earth 468, both improved methods pass the
bundle and manifold checks.  The pointwise baseline fails at every Stage-F
case because its bundle residual already fails.  At the three anchors its
direction differs from QR by roughly 7–9 degrees, while partial real Schur is
within approximately `4e-5` degrees.  This difference becomes clearer when
the displacement sheet is normalized by perturbation size: pointwise-to-QR
distance is order `1e-2`, whereas Schur-to-QR distance is `1e-7` or smaller at
the anchors.

## 10. Computational cost

For the three accepted family anchors, partial real Schur required
0.106,
0.170, and
0.043 seconds; QR/SVD required
0.201,
0.267, and
0.080 seconds.  Failed Route-H QR
runs consume several seconds because they reach the 200-iteration cap.  Runtime
is therefore coupled to convergence status, and failed rows must be included in
any accuracy–cost comparison.

## 11. Preregistered Stage-H extensions

The four empirical gaps named in the reviewed Chinese draft were executed under preregistered case, iteration, retry, and wall-time caps. Completion here means that accepted, boundary, and failed outcomes are all preserved with CSV, NPZ, Markdown, configuration, environment, and SHA256 evidence. It does not mean that every numerical row passed, and none of these research results promotes a reproduction authority table.

| Stage | Preregistered scope | Observed result | Gate |
|---|---|---|---|
| H2 stable bundles | 3 cases × 3 methods | 9 rows; improved accepted=6; pointwise fail=3 | `pass` |
| H2 stable manifolds | 3 cases × 3 methods × 3 perturbations × 2 signs | 54 rows; improved accepted=36 | `pass` |
| H3 Route-H rank-two objects | 2 cases and 8 angular seeds | 90 phase diagnostics; 8 manifold rows; Schur accepted=4 | `pass` |
| H4 three-period propagation | 3 cases × 2 methods × 2 signs | 12 result rows: accepted=8 and physical boundary=4; 492 trajectory events | `pass` |
| H5 Sun–Earth expansion | 3 distinct local sources × 3 methods | 9 benchmark rows; improved boundary=6 and pointwise fail=3 | `pass` |

### 11.1 Stable bundles and stable-manifold propagation

The Halo N45, Vertical N57, and Sun–Earth member-468 anchors were reevaluated on the stable branch and propagated backward. Both improved methods produced six accepted one-dimensional stable-bundle rows across the three cases, whereas all three pointwise rows retained order-1e-1 invariance residuals and failed. The subsequent 54-row stable-manifold campaign covered three perturbation norms and both signs: 36 improved-method rows were accepted, while 18 pointwise rows retained their upstream bundle failure. This closes the previously explicit stable-branch evidence gap only for the declared cases, one mapping period, and perturbation range.

### 11.2 Physical Route-H rank-two real objects

The corrected-rho operators for members 68 and 32 remain rank-two real conjugate blocks and are never relabelled as one-dimensional directions. Their maximum raw equation residual is `5.678e-14` and their maximum gauge-consistent subspace residual is `2.152e-12`. Real-Schur realification generated four accepted rank-two manifold cells while retaining the frozen Stage-E normalized-frame residuals and one-dimensional failures. H3 therefore adds a valid rank-two representation and geometric object; it does not rewrite the historical rank-one gate.

QR/SVD was bounded to local-SVD, Schur-seed, and deterministic-random initializations with 500 iterations each. All six retries remained bounded failures, generated no accepted manifold, and were never collapsed to rank one. The supported claim is method-specific: the Schur construction yields the tested rank-two objects, whereas the tested QR/SVD variants do not converge to an accepted object.

### 11.3 Three-period propagation and physical-radius boundaries

H4 propagated each stable anchor for exactly three mapping periods. Local, global, and far-field thresholds record first crossings but never terminate integration. Eight of twelve method/sign rows were accepted and four were retained as physical boundaries; every case has at least one collision-free accepted row. Four close-approach first attempts triggered the single preregistered tighter retry. The maximum selected Jacobi drift is `7.918e-11`. The positive Halo and negative Vertical signs enter the sampled lunar physical radius for both improved methods, so these rows remain boundaries rather than being deleted or described as numerical failures.

### 11.4 Three additional local Sun–Earth sources

H5 uses three different local source artifacts and arrays: active-event-step, sharpness-stage-4, and energy-frontier. None is a frozen Stage-C registry array. Recomputed source-map residuals are 8.264e-09, 9.583e-09, 1.885e-09 and pass their source-specific limits. The six improved Schur/QR benchmark rows have residuals near 4.3e-5 to 4.8e-5 and therefore remain boundaries under the frozen research threshold; all three pointwise rows fail. The associated one-period campaign stores 12 improved-method boundary rows and six diagnostic pointwise failures.

Here, “independent new source” is deliberately narrow: the sources are distinct local artifacts, state arrays, and metadata fingerprints. They are not an external solver, external institution, or independent experimental dataset. Every H5 row carries the preregistered source-authority boundary.

## 12. Discussion

Three conclusions are supported.  First, low pointwise eigenpair residual does
not imply low cocycle residual: the pointwise method solves the wrong local
problem.  Second, real subspace handling matters independently of numerical
accuracy; complex pairs must remain rank two.  Third, a small bundle residual
does not guarantee converged global-sheet geometry.  The N21/N33 and N33/N45
full-sheet failures demonstrate why source, bundle, and manifold gates must be
reported separately.

The Route-H result is especially instructive.  Correcting the curve rotation
improves curve closure by about nine orders of magnitude relative to the legacy
operator, yet removes the accepted one-dimensional Schur control.  This is not
a reason to restore the old rotation; it is evidence that operator semantics
must be part of benchmark provenance.

![Method-level accepted, boundary, and failed outcomes](../../paper_release/figures/fig_bundle_method_summary.png)

![Route-H physical and legacy operator controls](../../paper_release/figures/fig_route_h_rho_control.png)

![Representative manifold displacement sheets](../../paper_release/figures/fig_halo_manifold_displacement_sheets.png)

## 13. Limitations

Stage H adds three stable-bundle campaigns, two rank-two Route-H manifold objects, three fixed three-period propagations, and three distinct local Sun–Earth source benchmarks. The supported scope is still bounded by the preregistered CR3BP cases, finite perturbations, a three-period horizon, and local source artifacts. There is no new convergence theorem, external solver replication, ephemeris-model validation, or target-journal assessment. The lower-resolution 0.01 manifold boundary and the frozen Chapter-4 0/4 projection holdout remain untouched.

## 14. Conclusion

The frozen evidence supports an auditable real invariant-bundle framework and
systematic comparison.  Across multiple Earth–Moon and Sun–Earth families,
partial real-Schur and shifted QR/SVD methods repeatedly reduce cocycle
residuals by many orders of magnitude relative to pointwise eigenselection and
produce consistent high-resolution displacement sheets.  The same workflow
also exposes genuine negative results: Route-H physical corrected-rho cases do
not yield an accepted one-dimensional bundle, and low-resolution sheets do not
clear the retained convergence boundary.  These failures and boundaries define the current scope of the contribution and prevent overclaiming. The completed Stage-H campaign upgrades the deliverable from an internal draft to an adviser submission-decision candidate, not to an externally authorized or venue-formatted submission.

## 15. Evidence map

- Registry and provenance: `research/invariant_bundles/benchmarks/benchmark_registry.csv`
- Method comparison: `research/invariant_bundles/results/csv/method_comparison.csv`
- Resolution comparison: `research/invariant_bundles/results/csv/resolution_convergence.csv`
- Manifold comparison: `research/invariant_bundles/results/csv/manifold_convergence.csv`
- Figures and hashes: `research/invariant_bundles/figures/research_figure_manifest.csv`
- Reproduction baseline: `data/computed/reproduction_baseline_v1_summary.csv`
- Detailed tables: `tables.md`
- Claim-by-claim traceability: `claim_evidence_matrix.csv`
