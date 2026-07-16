"""Real invariant-subspace tools for discrete quasi-periodic cocycles.

The local matrices ``A[i]`` map perturbations from ``theta[i]`` to
``theta[i] + rho``.  This module keeps that cocycle equation distinct from a
pointwise eigenproblem and reports the normalized residual of

``A(theta) E(theta) = E(theta + rho) R(theta)``.

One-dimensional real bundles and two-dimensional real representations of a
complex conjugate pair are both first-class results.  A complex pair is never
silently projected to a one-dimensional result except in the explicitly named
traditional baseline routine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .quasi_torus import _trigonometric_interpolation_matrix


Branch = Literal["stable", "unstable"]


@dataclass(frozen=True)
class InvariantBundleResult:
    """Auditable result for a real one- or two-dimensional bundle."""

    method: str
    branch: Branch
    bundle_dimension: int
    bases: np.ndarray
    local_reduced_maps: np.ndarray
    invariance_residuals: np.ndarray
    phase_principal_angles_deg: np.ndarray
    selected_spectrum: np.ndarray
    relative_imaginary: float
    selection_residual: float
    iterations: int
    converged: bool
    convergence_history: np.ndarray
    classification: str
    sign_or_orientation_flips: int

    @property
    def max_invariance_residual(self) -> float:
        return float(np.max(self.invariance_residuals))

    @property
    def mean_invariance_residual(self) -> float:
        return float(np.mean(self.invariance_residuals))

    @property
    def max_phase_principal_angle_deg(self) -> float:
        return float(np.max(self.phase_principal_angles_deg, initial=0.0))

    @property
    def mean_phase_principal_angle_deg(self) -> float:
        return float(np.mean(self.phase_principal_angles_deg))


def _validate_inputs(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    matrices = np.asarray(cocycle, dtype=float)
    nodes = np.asarray(phases, dtype=float)
    rotation = float(rho)
    if matrices.ndim != 3 or matrices.shape[1] != matrices.shape[2]:
        raise ValueError("cocycle must have shape (samples, dimension, dimension)")
    if nodes.shape != (matrices.shape[0],):
        raise ValueError("phases must match the cocycle sample count")
    if matrices.shape[0] < 3 or matrices.shape[0] % 2 == 0:
        raise ValueError("an odd cocycle sample count of at least three is required")
    if not np.all(np.isfinite(matrices)) or not np.all(np.isfinite(nodes)):
        raise ValueError("cocycle and phases must be finite")
    if not np.isfinite(rotation):
        raise ValueError("rho must be finite")
    if np.min(np.linalg.svd(matrices, compute_uv=False)) <= np.finfo(float).tiny:
        raise ValueError("cocycle matrices must be nonsingular")
    wrapped = np.mod(nodes, 2.0 * np.pi)
    distances = np.abs(wrapped[:, None] - wrapped[None, :])
    distances += np.eye(nodes.size) * 2.0 * np.pi
    if float(np.min(distances)) < 1.0e-12:
        raise ValueError("phases must be distinct modulo 2*pi")
    return matrices, nodes, rotation


def periodic_interpolation_matrix(
    source_phases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """Return the odd-grid Fourier interpolation matrix used by the cocycle."""

    source = np.asarray(source_phases, dtype=float)
    evaluation = np.asarray(evaluation_phases, dtype=float)
    if source.ndim != 1 or evaluation.ndim != 1:
        raise ValueError("phase arrays must be one-dimensional")
    return _trigonometric_interpolation_matrix(source, evaluation)


def assemble_discrete_cocycle_operator(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
) -> np.ndarray:
    """Assemble the real collocation operator on the base phase grid.

    The block-diagonal cocycle first maps each node to the shifted grid.  The
    Fourier interpolation then maps that shifted field back to the base grid.
    This is the same ordering used by the reproduction ``DG`` construction.
    """

    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    samples, dimension, _ = matrices.shape
    shifted_to_base = periodic_interpolation_matrix(nodes + rotation, nodes)
    block_diagonal = np.zeros(
        (samples * dimension, samples * dimension), dtype=float
    )
    for index, matrix in enumerate(matrices):
        start = index * dimension
        block_diagonal[start : start + dimension, start : start + dimension] = matrix
    return np.kron(shifted_to_base, np.eye(dimension)) @ block_diagonal


def _orthonormalize(values: np.ndarray) -> np.ndarray:
    vectors = np.asarray(values, dtype=float)
    if vectors.ndim != 3:
        raise ValueError("bundle bases must have shape (samples, dimension, rank)")
    result = np.empty_like(vectors)
    for index, basis in enumerate(vectors):
        q, r = np.linalg.qr(basis, mode="reduced")
        if q.shape[1] != vectors.shape[2] or np.min(np.abs(np.diag(r))) < 1.0e-14:
            raise RuntimeError(f"bundle basis lost rank at phase index {index}")
        diagonal = np.sign(np.diag(r))
        diagonal[diagonal == 0.0] = 1.0
        result[index] = q * diagonal
    return result


def _principal_angles_deg(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    singular = np.linalg.svd(left.T @ right, compute_uv=False)
    singular = np.clip(singular, -1.0, 1.0)
    return np.degrees(np.arccos(singular))


def _align_to_reference(
    bases: np.ndarray,
    references: np.ndarray,
) -> tuple[np.ndarray, int]:
    aligned = np.asarray(bases, dtype=float).copy()
    flips = 0
    for index in range(aligned.shape[0]):
        if aligned.shape[2] == 1:
            if float(aligned[index, :, 0] @ references[index, :, 0]) < 0.0:
                aligned[index, :, 0] *= -1.0
                flips += 1
        else:
            u, _, vt = np.linalg.svd(aligned[index].T @ references[index])
            rotation = u @ vt
            if np.linalg.det(rotation) < 0.0:
                flips += 1
            aligned[index] = aligned[index] @ rotation
    return aligned, flips


def align_bundle_phase(
    bases: np.ndarray,
    phases: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Align signs or in-subspace frames along increasing phase."""

    values = _orthonormalize(bases)
    nodes = np.asarray(phases, dtype=float)
    if nodes.shape != (values.shape[0],):
        raise ValueError("phases must match bundle samples")
    order = np.argsort(np.mod(nodes, 2.0 * np.pi))
    aligned = values.copy()
    flips = 0
    for position in range(1, order.size):
        current = order[position]
        previous = order[position - 1]
        updated, count = _align_to_reference(
            aligned[current : current + 1], aligned[previous : previous + 1]
        )
        aligned[current] = updated[0]
        flips += count
    first = order[0]
    last = order[-1]
    if values.shape[2] == 1:
        flips += int(float(aligned[first, :, 0] @ aligned[last, :, 0]) < 0.0)
    else:
        flips += int(np.linalg.det(aligned[last].T @ aligned[first]) < 0.0)
    return aligned, flips


def phase_principal_angles_deg(bases: np.ndarray, phases: np.ndarray) -> np.ndarray:
    """Return maximum adjacent subspace angle on the periodic phase grid."""

    values = _orthonormalize(bases)
    order = np.argsort(np.mod(np.asarray(phases, dtype=float), 2.0 * np.pi))
    angles = np.empty(order.size, dtype=float)
    for position, current in enumerate(order):
        following = order[(position + 1) % order.size]
        angles[position] = float(
            np.max(_principal_angles_deg(values[current], values[following]))
        )
    return angles


def bundle_invariance_metrics(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    bases: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return local reduced maps and normalized cocycle residuals."""

    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    values = _orthonormalize(bases)
    if values.shape[:2] != matrices.shape[:2]:
        raise ValueError("bundle bases do not match cocycle shape")
    forward = periodic_interpolation_matrix(nodes, nodes + rotation)
    shifted = np.einsum("ij,jdk->idk", forward, values)
    shifted = _orthonormalize(shifted)
    rank = values.shape[2]
    reduced = np.empty((matrices.shape[0], rank, rank), dtype=float)
    residuals = np.empty(matrices.shape[0], dtype=float)
    for index, matrix in enumerate(matrices):
        transported = matrix @ values[index]
        reduced[index] = shifted[index].T @ transported
        defect = transported - shifted[index] @ reduced[index]
        residuals[index] = float(
            np.linalg.norm(defect, ord="fro")
            / max(np.linalg.norm(transported, ord="fro"), np.finfo(float).tiny)
        )
    return reduced, residuals


def _branch_candidates(
    eigenvalues: np.ndarray,
    branch: Branch,
    hyperbolic_tolerance: float,
) -> np.ndarray:
    magnitudes = np.abs(eigenvalues)
    if branch == "unstable":
        candidates = np.flatnonzero(magnitudes > 1.0 + hyperbolic_tolerance)
    elif branch == "stable":
        candidates = np.flatnonzero(magnitudes < 1.0 - hyperbolic_tolerance)
    else:
        raise ValueError("branch must be 'stable' or 'unstable'")
    if candidates.size == 0:
        raise RuntimeError(f"cocycle operator has no {branch} hyperbolic spectrum")
    return candidates


def traditional_pointwise_eigen_bundle(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    hyperbolic_tolerance: float = 1.0e-3,
) -> InvariantBundleResult:
    """Traditional pointwise eigenvector baseline.

    This routine intentionally reproduces the conventional failure mode: it
    selects an eigenvector of each local matrix by multiplier magnitude and
    projects a selected complex vector to its real part.  The classification
    and relative-imaginary metric make that misuse explicit.
    """

    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    samples, dimension, _ = matrices.shape
    bases = np.empty((samples, dimension, 1), dtype=float)
    spectrum = np.empty(samples, dtype=complex)
    eigenpair_residuals = np.empty(samples, dtype=float)
    relative_imaginary = np.empty(samples, dtype=float)
    for index, matrix in enumerate(matrices):
        values, vectors = np.linalg.eig(matrix)
        candidates = _branch_candidates(values, branch, hyperbolic_tolerance)
        if branch == "unstable":
            selected = int(candidates[np.argmax(np.abs(values[candidates]))])
        else:
            selected = int(candidates[np.argmin(np.abs(values[candidates]))])
        value = complex(values[selected])
        vector = vectors[:, selected]
        direction = np.real(vector)
        if np.linalg.norm(direction) < 1.0e-13:
            direction = np.imag(vector)
        if np.linalg.norm(direction) < 1.0e-13:
            raise RuntimeError(f"selected pointwise eigenvector vanished at {index}")
        bases[index, :, 0] = direction / np.linalg.norm(direction)
        spectrum[index] = value
        relative_imaginary[index] = abs(value.imag) / max(abs(value), np.finfo(float).tiny)
        eigenpair_residuals[index] = float(
            np.linalg.norm(matrix @ vector - value * vector)
            / max(np.linalg.norm(matrix @ vector), np.finfo(float).tiny)
        )
    bases, flips = align_bundle_phase(bases, nodes)
    reduced, residuals = bundle_invariance_metrics(matrices, nodes, rotation, bases)
    complex_misuse = bool(np.max(relative_imaginary) > 1.0e-10)
    return InvariantBundleResult(
        method="traditional_pointwise_eigendecomposition",
        branch=branch,
        bundle_dimension=1,
        bases=bases,
        local_reduced_maps=reduced,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(bases, nodes),
        selected_spectrum=spectrum,
        relative_imaginary=float(np.max(relative_imaginary)),
        selection_residual=float(np.max(eigenpair_residuals)),
        iterations=0,
        converged=not complex_misuse,
        convergence_history=np.empty(0, dtype=float),
        classification=(
            "complex_vector_projected_to_real_1d_failure"
            if complex_misuse
            else "real_1d_pointwise_candidate"
        ),
        sign_or_orientation_flips=flips,
    )


def _target_operator_eigenvalue(
    eigenvalues: np.ndarray,
    *,
    branch: Branch,
    hyperbolic_tolerance: float,
) -> complex:
    candidates = _branch_candidates(eigenvalues, branch, hyperbolic_tolerance)
    values = eigenvalues[candidates]
    relative_imaginary = np.abs(np.imag(values)) / np.maximum(
        np.abs(values), np.finfo(float).tiny
    )
    minimum = float(np.min(relative_imaginary))
    near_axis = np.flatnonzero(relative_imaginary <= minimum + 1.0e-12)
    if branch == "unstable":
        chosen = near_axis[np.argmax(np.abs(values[near_axis]))]
    else:
        chosen = near_axis[np.argmin(np.abs(values[near_axis]))]
    return complex(values[chosen])


def real_schur_bundle_tracking(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    hyperbolic_tolerance: float = 1.0e-3,
    real_relative_imaginary_tolerance: float = 1.0e-10,
    refinement_iterations: int = 0,
) -> InvariantBundleResult:
    """Select and track an ordered partial real-Schur invariant subspace.

    The spectral ordering targets the hyperbolic operator eigenvalue closest
    to the real axis.  Its selected invariant block is converted to a real
    orthonormal partial Schur form ``operator @ Q = Q @ T``.  A genuinely real
    block yields a one-dimensional result; a conjugate pair is realified with
    the real and imaginary parts of its eigenvector and therefore yields its
    two-dimensional real invariant subspace.
    """

    if real_relative_imaginary_tolerance <= 0.0:
        raise ValueError("real_relative_imaginary_tolerance must be positive")
    if refinement_iterations < 0:
        raise ValueError("refinement_iterations must be nonnegative")
    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    operator = assemble_discrete_cocycle_operator(matrices, nodes, rotation)
    eigenvalues, eigenvectors = np.linalg.eig(operator)
    target = _target_operator_eigenvalue(
        eigenvalues,
        branch=branch,
        hyperbolic_tolerance=hyperbolic_tolerance,
    )
    relative_imaginary = abs(target.imag) / max(abs(target), np.finfo(float).tiny)
    target_is_real = relative_imaginary <= real_relative_imaginary_tolerance
    selected_index = int(np.argmin(np.abs(eigenvalues - target)))
    selected_vector = eigenvectors[:, selected_index]
    if target_is_real:
        candidate = np.real(selected_vector)[:, None]
        if np.linalg.norm(candidate) < 1.0e-13:
            candidate = np.imag(selected_vector)[:, None]
        selected_dimension = 1
    else:
        candidate = np.column_stack(
            (np.real(selected_vector), np.imag(selected_vector))
        )
        selected_dimension = 2
    selected_vectors, factor = np.linalg.qr(candidate, mode="reduced")
    if selected_vectors.shape[1] != selected_dimension or np.min(
        np.abs(np.diag(factor))
    ) < 1.0e-13:
        raise RuntimeError(
            f"selected real Schur block lost rank for target {target}"
        )
    reduced_operator = selected_vectors.T @ operator @ selected_vectors
    schur_defect = operator @ selected_vectors - selected_vectors @ reduced_operator
    schur_residual = float(
        np.linalg.norm(schur_defect, ord="fro")
        / max(np.linalg.norm(operator @ selected_vectors, ord="fro"), np.finfo(float).tiny)
    )
    samples, dimension, _ = matrices.shape
    bases = selected_vectors.reshape(samples, dimension, selected_dimension)
    bases = _orthonormalize(bases)
    bases, flips = align_bundle_phase(bases, nodes)
    history: list[float] = []
    if refinement_iterations:
        bases, history, extra_flips = _graph_transform(
            matrices,
            nodes,
            rotation,
            bases,
            branch=branch,
            max_iterations=refinement_iterations,
            tolerance=0.0,
        )
        flips += extra_flips
    local_maps, residuals = bundle_invariance_metrics(
        matrices, nodes, rotation, bases
    )
    selected_spectrum = np.linalg.eigvals(reduced_operator)
    return InvariantBundleResult(
        method="ordered_real_schur_tracking",
        branch=branch,
        bundle_dimension=selected_dimension,
        bases=bases,
        local_reduced_maps=local_maps,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(bases, nodes),
        selected_spectrum=selected_spectrum,
        relative_imaginary=float(relative_imaginary),
        selection_residual=schur_residual,
        iterations=refinement_iterations,
        converged=bool(schur_residual < 1.0e-8),
        convergence_history=np.asarray(history, dtype=float),
        classification=(
            "real_1d_hyperbolic_bundle"
            if selected_dimension == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        sign_or_orientation_flips=flips,
    )


def _initial_svd_bases(
    matrices: np.ndarray,
    rank: int,
    branch: Branch,
) -> np.ndarray:
    samples, dimension, _ = matrices.shape
    bases = np.empty((samples, dimension, rank), dtype=float)
    for index, matrix in enumerate(matrices):
        _, _, vt = np.linalg.svd(matrix)
        if branch == "unstable":
            bases[index] = vt[:rank].T
        else:
            bases[index] = vt[-rank:].T
    return _orthonormalize(bases)


def _graph_transform(
    matrices: np.ndarray,
    nodes: np.ndarray,
    rotation: float,
    initial_bases: np.ndarray,
    *,
    branch: Branch,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, list[float], int]:
    bases = _orthonormalize(initial_bases)
    shifted_to_base = periodic_interpolation_matrix(nodes + rotation, nodes)
    base_to_shifted = periodic_interpolation_matrix(nodes, nodes + rotation)
    history: list[float] = []
    flips = 0
    for _ in range(max_iterations):
        if branch == "unstable":
            transported = np.einsum("nij,njk->nik", matrices, bases)
            transported = _orthonormalize(transported)
            transported, transport_flips = align_bundle_phase(
                transported, nodes + rotation
            )
            flips += transport_flips
            candidate = np.einsum("ij,jdk->idk", shifted_to_base, transported)
        else:
            shifted = np.einsum("ij,jdk->idk", base_to_shifted, bases)
            shifted = _orthonormalize(shifted)
            shifted, transport_flips = align_bundle_phase(
                shifted, nodes + rotation
            )
            flips += transport_flips
            candidate = np.empty_like(shifted)
            for index, matrix in enumerate(matrices):
                candidate[index] = np.linalg.solve(matrix, shifted[index])
        candidate = _orthonormalize(candidate)
        candidate, iteration_flips = _align_to_reference(candidate, bases)
        candidate, phase_flips = align_bundle_phase(candidate, nodes)
        flips += iteration_flips + phase_flips
        max_angle = max(
            float(np.max(_principal_angles_deg(bases[index], candidate[index])))
            for index in range(bases.shape[0])
        )
        history.append(max_angle)
        bases = candidate
        if tolerance > 0.0 and max_angle <= tolerance:
            break
    return bases, history, flips


def qr_svd_cocycle_bundle_iteration(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    bundle_dimension: int | None = None,
    max_iterations: int = 200,
    angle_tolerance_deg: float = 2.0e-6,
    initial_bases: np.ndarray | None = None,
    hyperbolic_tolerance: float = 1.0e-3,
    real_relative_imaginary_tolerance: float = 1.0e-10,
) -> InvariantBundleResult:
    """Compute a real invariant bundle by shifted QR/SVD graph iteration."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if angle_tolerance_deg <= 0.0:
        raise ValueError("angle_tolerance_deg must be positive")
    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    schur_seed: InvariantBundleResult | None = None
    if bundle_dimension is None:
        schur_seed = real_schur_bundle_tracking(
            matrices,
            nodes,
            rotation,
            branch=branch,
            hyperbolic_tolerance=hyperbolic_tolerance,
            real_relative_imaginary_tolerance=real_relative_imaginary_tolerance,
        )
        bundle_dimension = schur_seed.bundle_dimension
    if bundle_dimension not in (1, 2):
        raise ValueError("bundle_dimension must be one or two")
    if bundle_dimension > matrices.shape[1]:
        raise ValueError("bundle_dimension exceeds state dimension")
    if initial_bases is None:
        bases = _initial_svd_bases(matrices, bundle_dimension, branch)
    else:
        bases = np.asarray(initial_bases, dtype=float)
        if bases.shape != (matrices.shape[0], matrices.shape[1], bundle_dimension):
            raise ValueError("initial_bases has the wrong shape")
        bases = _orthonormalize(bases)
    bases, history, flips = _graph_transform(
        matrices,
        nodes,
        rotation,
        bases,
        branch=branch,
        max_iterations=max_iterations,
        tolerance=angle_tolerance_deg,
    )
    local_maps, residuals = bundle_invariance_metrics(
        matrices, nodes, rotation, bases
    )
    if schur_seed is None:
        operator_eigenvalues = np.linalg.eigvals(
            assemble_discrete_cocycle_operator(matrices, nodes, rotation)
        )
        target = _target_operator_eigenvalue(
            operator_eigenvalues,
            branch=branch,
            hyperbolic_tolerance=hyperbolic_tolerance,
        )
        relative_imaginary = abs(target.imag) / max(abs(target), np.finfo(float).tiny)
        selected_spectrum = np.asarray([target, np.conj(target)])[:bundle_dimension]
    else:
        relative_imaginary = schur_seed.relative_imaginary
        selected_spectrum = schur_seed.selected_spectrum
    converged = bool(history and history[-1] <= angle_tolerance_deg)
    return InvariantBundleResult(
        method="qr_svd_shifted_cocycle_iteration",
        branch=branch,
        bundle_dimension=bundle_dimension,
        bases=bases,
        local_reduced_maps=local_maps,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(bases, nodes),
        selected_spectrum=np.asarray(selected_spectrum),
        relative_imaginary=float(relative_imaginary),
        selection_residual=float(history[-1] if history else np.nan),
        iterations=len(history),
        converged=converged,
        convergence_history=np.asarray(history, dtype=float),
        classification=(
            "real_1d_hyperbolic_bundle"
            if bundle_dimension == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        sign_or_orientation_flips=flips,
    )


def resample_bundle(
    source_phases: np.ndarray,
    source_bases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """Fourier-resample and orthonormalize a real bundle."""

    source = np.asarray(source_phases, dtype=float)
    bases = _orthonormalize(source_bases)
    evaluation = np.asarray(evaluation_phases, dtype=float)
    if source.shape != (bases.shape[0],):
        raise ValueError("source phases do not match bundle bases")
    interpolation = periodic_interpolation_matrix(source, evaluation)
    values = np.einsum("ij,jdk->idk", interpolation, bases)
    return _orthonormalize(values)


def cross_resolution_principal_angles_deg(
    coarse_phases: np.ndarray,
    coarse_bases: np.ndarray,
    fine_phases: np.ndarray,
    fine_bases: np.ndarray,
) -> np.ndarray:
    """Compare two bundle resolutions on the fine phase grid."""

    fine = _orthonormalize(fine_bases)
    lifted = resample_bundle(coarse_phases, coarse_bases, fine_phases)
    if lifted.shape != fine.shape:
        raise ValueError("coarse and fine bundles must have the same state and bundle dimensions")
    return np.asarray(
        [
            float(np.max(_principal_angles_deg(lifted[index], fine[index])))
            for index in range(fine.shape[0])
        ]
    )
