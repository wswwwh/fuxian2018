# Contributions

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`

## Supported contribution statement

> A reliable numerical framework and systematic comparison for real
> invariant-bundle and global-manifold computation on quasi-periodic orbit
> cocycles.

The evidence supports the following contributions.

1. **Cocycle-aware audit equation.** Every method is tested against
   `A(theta) E(theta) ≈ E(theta + rho) R(theta)` with stored local and aggregate
   residuals, phase principal angles, bundle dimension, reciprocal-pair error,
   runtime, and failure reason.
2. **Real one- and two-dimensional outputs.** The partial real-Schur method
   returns a one-dimensional real block only for a nearly real selected root;
   a conjugate pair is retained as a two-dimensional real invariant subspace.
3. **Independent shifted QR/SVD method.** The second improved method transports,
   Fourier-interpolates, orthonormalizes, and phase-aligns real subspaces under
   a fixed 200-iteration cap.  It accepted
   `10/15` cases without hiding its
   `5/15` failures.
4. **Four-family benchmark and controls.** The registry contains 15 cases from
   four families and preserves low-resolution, complex-spectrum, boundary,
   physical corrected-rho, and legacy-DG controls.
5. **Resolution-to-manifold traceability.** Bundle convergence and full-sheet
   geometry are evaluated separately.  Halo N21/N33 and Vertical N33/N45 remain
   above the 0.01 cross-resolution sheet boundary even when their local bundle
   residual is small.
6. **Route-H operator-semantics finding.** The physical corrected-rho member-68
   curve has a recomputed map residual near
   `8.697e-13`,
   but its selected partial real-Schur block is dimension
   `2` with relative
   imaginary part `0.342`.
   The accepted one-dimensional legacy control instead uses a curve-map
   residual near `1.988e-03`.

## Claims deliberately not made

- No new invariant-bundle theorem or convergence proof is claimed.
- No two-dimensional real subspace is called a one-dimensional stable or
  unstable direction.
- No research result is written back into the reproduction validation table.
- No Route-H research figure is called a replacement for original Fig. 4.3–4.8.
- No claim of thesis-wide paper equivalence is made.
- No external citation is included until title, authors, year, and DOI or
  official link are independently verified.
