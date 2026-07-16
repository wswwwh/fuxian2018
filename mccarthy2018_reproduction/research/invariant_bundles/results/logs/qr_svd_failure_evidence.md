# QR/SVD negative-result evidence

The baseline failure set is exactly five rows: Route H physical members 17, 32, 54, and 68, plus the member-68 legacy seed-rho control. All 90 bounded experiment rows are preserved in `qr_svd_failure_experiments.csv`, including nonconvergence, large phase angles, and residuals above threshold.

No failed trajectory was removed. No cap above 1000, fourth initialization, third resolution, parameter change, or threshold relaxation was used. The N67 cocycle is explicitly a Fourier lift of the frozen N45 matrices; it is not misrepresented as an independently reintegrated physical source. Windows `numpy.longdouble` is binary64 on this machine, so the high-precision check used mpmath at 80 decimal digits for residual arithmetic and is explicitly scoped as a residual recomputation rather than a full QR trajectory.
