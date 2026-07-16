# Limitations

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`

1. **No thesis-wide numerical equivalence.** The frozen reproduction layer has
   54 engineering targets, but its evidence split
   remains 7 accepted,
   30 boundary,
   5 diagnostic, and
   12 proxy.  Research success cannot promote
   those rows.
2. **No new theory claim.** The evaluated real-Schur and QR/SVD ideas are
   numerical subspace techniques assembled into an auditable workflow.  This
   draft contains no proof of existence, uniqueness, reducibility, or
   convergence for the underlying cocycle.
3. **Partial real-Schur backend.** The locked Windows SciPy 1.17.1 runtime raises
   `0xc06d007f` on `scipy.linalg.schur`.  The implementation therefore orders a
   selected operator eigenpair, realifies a conjugate pair when necessary, and
   verifies the real partial-Schur residual directly.  A repaired LAPACK Schur
   runtime remains an independent backend-validation task.
4. **Finite iteration and resolution.** Shifted QR/SVD stops at 200 iterations.
   Five registry cases fail at this cap.  The largest spectral resolution is
   N57, not an asymptotic limit.
5. **Route-H boundary.** The physical corrected-rho Route-H cases do not yield an
   accepted one-dimensional bundle.  The legacy member-68 one-dimensional
   positive control uses a curve-map residual near
   1.988e-03
   and is not a physical source validation.
6. **Manifold scope.** Stage F evaluates unstable, one-dimensional bundles on
   seven cases, one fixed propagation interval, three perturbation norms, two
   signs, no event termination, and the CR3BP synodic frame.  Stable bundles,
   longer global events, and two-dimensional manifold objects are not yet
   validated.
7. **Geometry boundary.** Lower-resolution Halo and Vertical sheets remain above
   the 0.01 cross-resolution distance.  Visual similarity is not used to
   override that failure.
8. **Projection boundary.** No research result changes the frozen Chapter-4
   camera/epsilon/crop/threshold holdout, whose paper-projection status remains
   failed.
9. **Literature boundary.** External references are intentionally absent from
   this draft until complete bibliographic fields and DOI or official links are
   independently verified.
