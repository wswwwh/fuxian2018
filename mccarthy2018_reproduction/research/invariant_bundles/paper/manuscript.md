# Auditable Real Invariant-Bundle Computation for Quasi-Periodic CR3BP Tori

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

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

## 11. Discussion

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

## 12. Limitations

This draft has no external literature comparison, theoretical convergence
proof, stable-bundle manifold campaign, two-dimensional manifold object, or
long-event global propagation.  The Schur backend is a verified partial block,
not an independent LAPACK Schur run.  Route H remains a failed physical bundle
family under the tested methods.  Lower-resolution manifold geometry remains
outside the 0.01 boundary.  The Chapter-4 projection holdout remains failed and
is untouched.

## 13. Conclusion

The frozen evidence supports an auditable real invariant-bundle framework and
systematic comparison.  Across multiple Earth–Moon and Sun–Earth families,
partial real-Schur and shifted QR/SVD methods repeatedly reduce cocycle
residuals by many orders of magnitude relative to pointwise eigenselection and
produce consistent high-resolution displacement sheets.  The same workflow
also exposes genuine negative results: Route-H physical corrected-rho cases do
not yield an accepted one-dimensional bundle, and low-resolution sheets do not
clear the retained convergence boundary.  These failures define the current
scope of the contribution and prevent overclaiming.

## Evidence map

- Registry and provenance: `research/invariant_bundles/benchmarks/benchmark_registry.csv`
- Method comparison: `research/invariant_bundles/results/csv/method_comparison.csv`
- Resolution comparison: `research/invariant_bundles/results/csv/resolution_convergence.csv`
- Manifold comparison: `research/invariant_bundles/results/csv/manifold_convergence.csv`
- Figures and hashes: `research/invariant_bundles/figures/research_figure_manifest.csv`
- Reproduction baseline: `data/computed/reproduction_baseline_v1_summary.csv`
- Detailed tables: `tables.md`
- Claim-by-claim traceability: `claim_evidence_matrix.csv`
