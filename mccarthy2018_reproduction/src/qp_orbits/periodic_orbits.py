"""Periodic-orbit initial guesses and differential correction."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from scipy.integrate import solve_ivp

from .constants import CR3BPSystem
from .cr3bp import cr3bp_rhs, integrate_cr3bp, jacobi_constant
from .linear_modes import center_modes
from .libration_points import compute_libration_points
from .linearization import eigensystem_at
from .variational import integrate_state_and_stm, unpack_augmented


@dataclass(frozen=True)
class PlanarLyapunovGuess:
    """Linearized planar Lyapunov half-period guess."""

    libration_point: str
    equilibrium_state: np.ndarray
    initial_state: np.ndarray
    half_period: float
    eigenvalue: complex
    amplitude_x: float


@dataclass(frozen=True)
class CorrectionIteration:
    iteration: int
    x0: float
    ydot0: float
    half_period: float
    residual_norm: float


@dataclass(frozen=True)
class PlanarLyapunovOrbit:
    """Corrected symmetric planar Lyapunov orbit."""

    mu: float
    initial_guess: PlanarLyapunovGuess
    initial_state: np.ndarray
    half_period: float
    iterations: tuple[CorrectionIteration, ...] = field(default_factory=tuple)

    @property
    def period(self) -> float:
        return 2.0 * self.half_period

    @property
    def jacobi(self) -> float:
        return float(jacobi_constant(self.initial_state, self.mu))


@dataclass(frozen=True)
class PlanarDROOrbit:
    """Corrected planar distant retrograde orbit with a fixed x-axis crossing."""

    mu: float
    fixed_x0: float
    initial_state: np.ndarray
    half_period: float
    iterations: tuple[CorrectionIteration, ...] = field(default_factory=tuple)

    @property
    def period(self) -> float:
        return 2.0 * self.half_period

    @property
    def jacobi(self) -> float:
        return float(jacobi_constant(self.initial_state, self.mu))


@dataclass(frozen=True)
class SpatialSymmetricOrbit:
    """Corrected 3D symmetric periodic orbit with fixed initial z displacement."""

    mu: float
    point: str
    family_label: str
    initial_state: np.ndarray
    half_period: float
    fixed_z0: float
    seed_x_amplitude: float
    iterations: tuple[CorrectionIteration, ...] = field(default_factory=tuple)

    @property
    def period(self) -> float:
        return 2.0 * self.half_period

    @property
    def jacobi(self) -> float:
        return float(jacobi_constant(self.initial_state, self.mu))


@dataclass(frozen=True)
class JacobiTargetedSpatialOrbit:
    """Spatial periodic orbit refined to a target Jacobi constant."""

    orbit: SpatialSymmetricOrbit
    target_jacobi: float
    z0_history: np.ndarray
    jacobi_history: np.ndarray

    @property
    def jacobi_error(self) -> float:
        return self.orbit.jacobi - self.target_jacobi


@dataclass(frozen=True)
class ConstantEnergyBoundaryFrequency:
    """Periodic boundary and transverse Floquet frequency for a torus family."""

    family_label: str
    targeted: JacobiTargetedSpatialOrbit
    rotation_eigenvalue: complex
    rotation_angle_rad: float
    frequency_ratio: float
    mapping_time_days: float
    periodicity_error: float


@dataclass(frozen=True)
class HaloFloquetResonance:
    """Corrected halo orbit whose transverse Floquet angle is resonant."""

    resonance: int
    orbit: SpatialSymmetricOrbit
    eigenvalue: complex
    eigenvector: np.ndarray
    rotation_angle_rad: float
    frequency_ratio: float
    periodicity_error: float


@dataclass(frozen=True)
class ResonantHaloLinearSeed:
    """CR3BP propagation of a finite Floquet perturbation at a q resonance."""

    resonance: int
    base_orbit: SpatialSymmetricOrbit
    base_eigenvalue: complex
    base_frequency_ratio: float
    initial_state: np.ndarray
    trajectory: np.ndarray
    propagation_time: float
    closure_error: float
    position_amplitude: float


@dataclass(frozen=True)
class SpatialMultipleShootingOrbit:
    """Spatial symmetric periodic orbit corrected with half-period patch points."""

    orbit: SpatialSymmetricOrbit
    patch_states: np.ndarray
    segment_duration: float
    continuity_errors: np.ndarray
    terminal_symmetry_error: np.ndarray


@dataclass(frozen=True)
class ResonantHaloExample:
    """Numerically corrected period-q halo example and its bifurcation anchor."""

    resonance: int
    bifurcation: HaloFloquetResonance
    corrected: SpatialMultipleShootingOrbit
    trajectory: np.ndarray


@dataclass(frozen=True)
class SpatialMultipleShootingClosureAudit:
    """Independent closure diagnostics for a half-period multiple-shooting orbit."""

    patch_to_patch_continuity_vectors: np.ndarray
    patch_to_patch_continuity_errors: np.ndarray
    terminal_symmetry_error: np.ndarray
    per_segment_endpoint_errors: np.ndarray
    multiple_shooting_residual_norm: float
    patch_to_patch_continuity_norm: float
    patch_to_patch_continuity_max: float
    terminal_symmetry_residual_norm: float
    full_period_terminal_state: np.ndarray
    full_period_single_shoot_closure_error: float
    half_period_terminal_state: np.ndarray
    half_period_single_shoot_symmetry_error: float
    trajectory_sampling_closure_error: float
    trajectory_jacobi_drift: float
    full_period_single_shoot_jacobi_drift: float
    monodromy_matrix: np.ndarray
    monodromy_multipliers: np.ndarray
    monodromy_multiplier_magnitudes: np.ndarray
    segment_duration_consistency_error: float


def _planar_center_mode(position: np.ndarray, mu: float) -> tuple[complex, np.ndarray]:
    eigenvalues, eigenvectors = eigensystem_at(position, mu)
    candidates = [
        idx
        for idx, value in enumerate(eigenvalues)
        if value.imag > 1e-8 and abs(value.real) < 1e-7
    ]
    if not candidates:
        raise RuntimeError("No planar center eigenvalue found")
    idx = min(candidates, key=lambda i: abs(eigenvectors[2, i]) + abs(eigenvectors[5, i]))
    return eigenvalues[idx], eigenvectors[:, idx]


def planar_lyapunov_linear_guess(
    mu: float,
    *,
    point: str = "L2",
    x_amplitude: float = -1.15e-3,
) -> PlanarLyapunovGuess:
    """Build a planar Lyapunov initial guess from the linearized center mode.

    ``x_amplitude`` is the initial displacement from the collinear equilibrium.
    For the Earth-Moon L2 example in Figure 2.11, a negative displacement places
    the starting state just inside L2.
    """

    libration = compute_libration_points(mu)[point]
    equilibrium = np.array([libration.x, libration.y, libration.z, 0.0, 0.0, 0.0], dtype=float)
    eigenvalue, eigenvector = _planar_center_mode(equilibrium[:3], mu)
    real_mode = np.real(eigenvector)
    if abs(real_mode[0]) < 1e-14:
        raise RuntimeError("Selected planar mode cannot be scaled by x displacement")
    scale = x_amplitude / real_mode[0]
    initial_state = equilibrium + scale * real_mode
    initial_state[[1, 2, 3, 5]] = 0.0
    half_period = np.pi / abs(eigenvalue.imag)
    return PlanarLyapunovGuess(point, equilibrium, initial_state, float(half_period), eigenvalue, x_amplitude)


def correct_planar_lyapunov(
    mu: float,
    guess: PlanarLyapunovGuess,
    *,
    tolerance: float = 1e-11,
    max_iterations: int = 12,
) -> PlanarLyapunovOrbit:
    """Correct a planar Lyapunov orbit using the perpendicular-crossing scheme."""

    x0 = float(guess.initial_state[0])
    ydot0 = float(guess.initial_state[4])
    half_period = float(guess.half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(state0, (0.0, half_period), mu)
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        residual = np.array([final_state[1], final_state[3]], dtype=float)
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm))
        if residual_norm < tolerance:
            return PlanarLyapunovOrbit(mu, guess, state0, half_period, tuple(iterations))

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.array(
            [
                [phi[1, 0], phi[1, 4], final_state[4]],
                [phi[3, 0], phi[3, 4], final_derivative[3]],
            ],
            dtype=float,
        )
        delta = np.linalg.lstsq(jacobian, -residual, rcond=None)[0]
        x0 += float(delta[0])
        ydot0 += float(delta[1])
        half_period += float(delta[2])

    final_state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
    raise RuntimeError(
        f"Planar Lyapunov correction did not converge after {max_iterations} iterations; "
        f"last residual={iterations[-1].residual_norm:.3e}, state={final_state0}, T={half_period}"
    )


def correct_planar_lyapunov_fixed_x(
    mu: float,
    guess: PlanarLyapunovGuess,
    *,
    tolerance: float = 1e-11,
    max_iterations: int = 40,
    max_ydot_step: float = 2e-3,
    max_time_step: float = 0.15,
    max_step: float = 0.01,
) -> PlanarLyapunovOrbit:
    """Correct a planar Lyapunov orbit while preserving its initial x crossing.

    The initial x coordinate supplied by ``guess`` is held fixed. Newton updates
    only the initial y velocity and half-period to enforce the opposite symmetry
    crossing ``y = xdot = 0``. This gives a well-defined natural parameter for
    manifold-family scans.
    """

    x0 = float(guess.initial_state[0])
    ydot0 = float(guess.initial_state[4])
    half_period = float(guess.half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(
            state0,
            (0.0, half_period),
            mu,
            max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        residual = final_state[[1, 3]]
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm))
        if residual_norm < tolerance:
            return PlanarLyapunovOrbit(mu, guess, state0, half_period, tuple(iterations))

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.array(
            [
                [phi[1, 4], final_derivative[1]],
                [phi[3, 4], final_derivative[3]],
            ],
            dtype=float,
        )
        delta = np.linalg.lstsq(jacobian, -residual, rcond=None)[0]
        scale = min(
            1.0,
            max_ydot_step / max(abs(float(delta[0])), 1e-30),
            max_time_step / max(abs(float(delta[1])), 1e-30),
        )
        ydot0 += scale * float(delta[0])
        half_period += scale * float(delta[1])
        if half_period <= 0.0:
            raise RuntimeError("Fixed-x Lyapunov correction produced a non-positive half-period")

    raise RuntimeError(
        f"Fixed-x planar Lyapunov correction did not converge after {max_iterations} iterations; "
        f"last residual={iterations[-1].residual_norm:.3e}, x0={x0:.12g}, "
        f"ydot0={ydot0:.12g}, T={half_period:.12g}"
    )


def correct_planar_lyapunov_jacobi(
    mu: float,
    seed_orbit: PlanarLyapunovOrbit,
    *,
    target_jacobi: float,
    tolerance: float = 1.0e-11,
    max_iterations: int = 30,
    max_x_step: float = 0.02,
    max_ydot_step: float = 0.05,
    max_time_step: float = 0.15,
) -> PlanarLyapunovOrbit:
    """Correct a planar Lyapunov orbit to a prescribed Jacobi constant."""

    x0 = float(seed_orbit.initial_state[0])
    ydot0 = float(seed_orbit.initial_state[4])
    half_period = float(seed_orbit.half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        if half_period <= 0.0:
            raise RuntimeError("Jacobi-targeted Lyapunov correction produced a non-positive half-period")
        state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
        solution = integrate_state_and_stm(
            state0,
            (0.0, half_period),
            mu,
            t_eval=np.array([half_period]),
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        final_state, phi = unpack_augmented(solution.y[:, -1])
        residual = np.array(
            [
                final_state[1],
                final_state[3],
                float(jacobi_constant(state0, mu)) - target_jacobi,
            ],
            dtype=float,
        )
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(
            CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm)
        )
        if residual_norm < tolerance:
            return PlanarLyapunovOrbit(
                mu=mu,
                initial_guess=seed_orbit.initial_guess,
                initial_state=state0,
                half_period=half_period,
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        initial_derivative = cr3bp_rhs(0.0, state0, mu)
        jacobian = np.array(
            [
                [phi[1, 0], phi[1, 4], final_derivative[1]],
                [phi[3, 0], phi[3, 4], final_derivative[3]],
                [2.0 * (initial_derivative[3] - 2.0 * ydot0), -2.0 * ydot0, 0.0],
            ],
            dtype=float,
        )
        delta = np.linalg.solve(jacobian, -residual)
        scale = max(
            abs(float(delta[0])) / max_x_step,
            abs(float(delta[1])) / max_ydot_step,
            abs(float(delta[2])) / max_time_step,
            1.0,
        )
        x0 += float(delta[0]) / scale
        ydot0 += float(delta[1]) / scale
        half_period += float(delta[2]) / scale

    raise RuntimeError(
        "Jacobi-targeted planar Lyapunov correction did not converge after "
        f"{max_iterations} iterations; residual={iterations[-1].residual_norm:.3e}"
    )


def correct_planar_dro(
    mu: float,
    *,
    x0: float,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    tolerance: float = 1e-11,
    max_iterations: int = 14,
    max_delta_norm: float = 0.25,
) -> PlanarDROOrbit:
    """Correct a planar DRO while holding one x-axis crossing fixed.

    The initial state is ``[x0, 0, 0, 0, ydot0, 0]``. Newton updates the
    initial y velocity and half-period until the opposite symmetry crossing
    satisfies ``y = xdot = 0``. The Jacobian uses the propagated STM and the
    terminal state derivative.
    """

    ydot0 = float(initial_ydot)
    half_period = float(initial_half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(state0, (0.0, half_period), mu, max_step=0.01)
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        residual = np.array([final_state[1], final_state[3]], dtype=float)
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(CorrectionIteration(iteration, float(x0), ydot0, half_period, residual_norm))
        if residual_norm < tolerance:
            return PlanarDROOrbit(
                mu=mu,
                fixed_x0=float(x0),
                initial_state=state0,
                half_period=half_period,
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.array(
            [
                [phi[1, 4], final_state[4]],
                [phi[3, 4], final_derivative[3]],
            ],
            dtype=float,
        )
        delta = np.linalg.solve(jacobian, -residual)
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_norm:
            delta *= max_delta_norm / delta_norm
        ydot0 += float(delta[0])
        half_period += float(delta[1])
        if half_period <= 0.0:
            raise RuntimeError("Planar DRO correction produced a non-positive half-period")

    final_state0 = np.array([x0, 0.0, 0.0, 0.0, ydot0, 0.0], dtype=float)
    raise RuntimeError(
        f"Planar DRO correction did not converge after {max_iterations} iterations; "
        f"last residual={iterations[-1].residual_norm:.3e}, state={final_state0}, T={half_period}"
    )


def correct_spatial_symmetric_orbit(
    mu: float,
    *,
    z0: float,
    point: str = "L2",
    seed_x_amplitude: float = -0.002,
    seed_orbit: SpatialSymmetricOrbit | PlanarLyapunovOrbit | None = None,
    family_label: str = "halo",
    tolerance: float = 1e-11,
    max_iterations: int = 18,
    max_delta_norm: float = 0.10,
) -> SpatialSymmetricOrbit:
    """Correct a 3D symmetric periodic orbit using STM-based Newton steps.

    The corrected initial state has the form ``[x0, 0, z0, 0, ydot0, 0]``.
    Holding ``z0`` fixed supplies the family parameter; ``x0``, ``ydot0``, and
    the half-period are adjusted so the half-period state satisfies
    ``y = xdot = zdot = 0``. This is the standard symmetry condition for a
    north/south halo-like orbit and is a numerical step beyond the earlier
    shape-only halo placeholders.
    """

    if seed_orbit is None:
        guess = planar_lyapunov_linear_guess(mu, point=point, x_amplitude=seed_x_amplitude)
        seed = correct_planar_lyapunov(mu, guess, tolerance=1e-10, max_iterations=30)
    else:
        seed = seed_orbit

    x0 = float(seed.initial_state[0])
    ydot0 = float(seed.initial_state[4])
    half_period = float(seed.half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(state0, (0.0, half_period), mu, max_step=0.02)
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        residual = np.array([final_state[1], final_state[3], final_state[5]], dtype=float)
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm))
        if residual_norm < tolerance:
            return SpatialSymmetricOrbit(
                mu=mu,
                point=point,
                family_label=family_label,
                initial_state=state0,
                half_period=half_period,
                fixed_z0=float(z0),
                seed_x_amplitude=float(seed_x_amplitude),
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.column_stack(
            [
                phi[[1, 3, 5], 0],
                phi[[1, 3, 5], 4],
                final_derivative[[1, 3, 5]],
            ]
        )
        delta = np.linalg.lstsq(jacobian, -residual, rcond=None)[0]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_norm:
            delta *= max_delta_norm / delta_norm
        x0 += float(delta[0])
        ydot0 += float(delta[1])
        half_period += float(delta[2])

    final_state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
    raise RuntimeError(
        f"Spatial symmetric correction did not converge after {max_iterations} iterations; "
        f"last residual={iterations[-1].residual_norm:.3e}, state={final_state0}, T={half_period}"
    )


def correct_spatial_symmetric_orbit_fixed_secondary_radius(
    mu: float,
    *,
    target_radius: float,
    seed_orbit: SpatialSymmetricOrbit,
    tolerance: float = 1.0e-11,
    max_iterations: int = 24,
    max_delta_norm: float = 0.05,
) -> SpatialSymmetricOrbit:
    """Correct a symmetric spatial orbit to a secondary-centered radius.

    The seed must place its initial symmetry crossing at the desired periapsis
    branch. The unknowns ``[x0, z0, ydot0, half_period]`` satisfy the three
    terminal symmetry conditions and the initial secondary-centered radius.
    """

    if target_radius <= 0.0:
        raise ValueError("target_radius must be positive")

    secondary_x = 1.0 - mu
    x0 = float(seed_orbit.initial_state[0])
    z0 = float(seed_orbit.initial_state[2])
    ydot0 = float(seed_orbit.initial_state[4])
    half_period = float(seed_orbit.half_period)
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        if half_period <= 0.0:
            raise RuntimeError("Fixed-radius correction produced a non-positive half-period")
        state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
        solution = integrate_state_and_stm(
            state0,
            (0.0, half_period),
            mu,
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)

        final_state, phi = unpack_augmented(solution.y[:, -1])
        relative = np.array([x0 - secondary_x, z0], dtype=float)
        radius = float(np.linalg.norm(relative))
        residual = np.r_[
            final_state[[1, 3, 5]],
            radius - target_radius,
        ]
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(
            CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm)
        )
        if residual_norm < tolerance:
            return SpatialSymmetricOrbit(
                mu=mu,
                point=seed_orbit.point,
                family_label=seed_orbit.family_label,
                initial_state=state0,
                half_period=half_period,
                fixed_z0=z0,
                seed_x_amplitude=seed_orbit.seed_x_amplitude,
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.empty((4, 4), dtype=float)
        jacobian[:3, :] = np.column_stack(
            [
                phi[[1, 3, 5], 0],
                phi[[1, 3, 5], 2],
                phi[[1, 3, 5], 4],
                final_derivative[[1, 3, 5]],
            ]
        )
        jacobian[3, :] = np.array(
            [relative[0] / radius, relative[1] / radius, 0.0, 0.0],
            dtype=float,
        )
        delta = np.linalg.solve(jacobian, -residual)
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_norm:
            delta *= max_delta_norm / delta_norm
        x0 += float(delta[0])
        z0 += float(delta[1])
        ydot0 += float(delta[2])
        half_period += float(delta[3])

    final_state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
    raise RuntimeError(
        "Fixed-secondary-radius spatial correction did not converge after "
        f"{max_iterations} iterations; residual={iterations[-1].residual_norm:.3e}, "
        f"state={final_state0}, T={half_period}"
    )


def spatial_symmetric_family(
    mu: float,
    z_amplitudes: list[float] | np.ndarray,
    *,
    point: str = "L2",
    seed_x_amplitude: float = -0.002,
    family_label: str = "halo",
    tolerance: float = 1e-11,
    max_iterations: int = 18,
) -> list[SpatialSymmetricOrbit]:
    """Generate a natural-parameter family of corrected 3D symmetric orbits."""

    family: list[SpatialSymmetricOrbit] = []
    seed: SpatialSymmetricOrbit | None = None
    for z_amplitude in z_amplitudes:
        orbit = correct_spatial_symmetric_orbit(
            mu,
            z0=float(z_amplitude),
            point=point,
            seed_x_amplitude=seed_x_amplitude,
            seed_orbit=seed,
            family_label=family_label,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        family.append(orbit)
        seed = orbit
    return family


def _spatial_symmetric_arclength_correction(
    mu: float,
    *,
    predictor: np.ndarray,
    tangent: np.ndarray,
    point: str,
    family_label: str,
    seed_x_amplitude: float,
    tolerance: float,
    max_iterations: int,
    max_delta_norm: float,
) -> SpatialSymmetricOrbit:
    """Correct one spatial symmetric orbit on a pseudo-arclength hyperplane."""

    variables = np.asarray(predictor, dtype=float).copy()
    tangent = np.asarray(tangent, dtype=float)
    if variables.shape != (4,) or tangent.shape != (4,):
        raise ValueError("predictor and tangent must contain [x0, z0, ydot0, half_period]")
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 0.0:
        raise ValueError("tangent must be nonzero")
    tangent = tangent / tangent_norm
    iterations: list[CorrectionIteration] = []

    for iteration in range(max_iterations):
        x0, z0, ydot0, half_period = variables
        if half_period <= 0.0:
            raise RuntimeError("Pseudo-arclength correction produced a non-positive half-period")
        state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(state0, (0.0, half_period), mu, max_step=0.01)
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        symmetry = final_state[[1, 3, 5]]
        arclength = float(np.dot(tangent, variables - predictor))
        residual = np.r_[symmetry, arclength]
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(
            CorrectionIteration(iteration, float(x0), float(ydot0), float(half_period), residual_norm)
        )
        if residual_norm < tolerance:
            return SpatialSymmetricOrbit(
                mu=mu,
                point=point,
                family_label=family_label,
                initial_state=state0,
                half_period=float(half_period),
                fixed_z0=float(z0),
                seed_x_amplitude=float(seed_x_amplitude),
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.empty((4, 4), dtype=float)
        jacobian[:3, :] = np.column_stack(
            [
                phi[[1, 3, 5], 0],
                phi[[1, 3, 5], 2],
                phi[[1, 3, 5], 4],
                final_derivative[[1, 3, 5]],
            ]
        )
        jacobian[3, :] = tangent
        delta = np.linalg.solve(jacobian, -residual)
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_norm:
            delta *= max_delta_norm / delta_norm
        variables += delta

    raise RuntimeError(
        "Pseudo-arclength spatial correction did not converge after "
        f"{max_iterations} iterations; residual={iterations[-1].residual_norm:.3e}, "
        f"variables={variables}"
    )


def spatial_symmetric_pseudo_arclength_family(
    seed_orbits: list[SpatialSymmetricOrbit] | tuple[SpatialSymmetricOrbit, ...],
    *,
    members: int,
    step_size: float,
    tolerance: float = 1.0e-11,
    max_iterations: int = 24,
    max_delta_norm: float = 0.10,
) -> list[SpatialSymmetricOrbit]:
    """Continue a spatial symmetric family through natural-parameter folds."""

    if len(seed_orbits) < 2:
        raise ValueError("At least two seed orbits are required")
    if members < len(seed_orbits):
        raise ValueError("members must include all supplied seed orbits")
    if step_size <= 0.0:
        raise ValueError("step_size must be positive")

    family = list(seed_orbits)
    first = family[0]
    if any(orbit.mu != first.mu for orbit in family):
        raise ValueError("All seed orbits must use the same mass parameter")

    def variables(orbit: SpatialSymmetricOrbit) -> np.ndarray:
        return np.array(
            [
                orbit.initial_state[0],
                orbit.fixed_z0,
                orbit.initial_state[4],
                orbit.half_period,
            ],
            dtype=float,
        )

    while len(family) < members:
        previous = variables(family[-2])
        current = variables(family[-1])
        tangent = current - previous
        tangent /= np.linalg.norm(tangent)
        predictor = current + step_size * tangent
        family.append(
            _spatial_symmetric_arclength_correction(
                first.mu,
                predictor=predictor,
                tangent=tangent,
                point=first.point,
                family_label=first.family_label,
                seed_x_amplitude=first.seed_x_amplitude,
                tolerance=tolerance,
                max_iterations=max_iterations,
                max_delta_norm=max_delta_norm,
            )
        )
    return family


def correct_spatial_symmetric_orbit_multiple_shooting(
    mu: float,
    *,
    z0: float,
    seed_orbit: SpatialSymmetricOrbit,
    segments: int,
    family_label: str,
    patch_state_guesses: np.ndarray | None = None,
    tolerance: float = 1.0e-10,
    max_iterations: int = 24,
    max_delta_component: float = 0.05,
) -> SpatialMultipleShootingOrbit:
    """Correct a long symmetric orbit with equal-duration half-period patches."""

    if segments < 2:
        raise ValueError("segments must be at least two")
    half_period = float(seed_orbit.half_period)
    if patch_state_guesses is None:
        initial_solution = integrate_cr3bp(
            seed_orbit.initial_state,
            (0.0, half_period),
            mu,
            t_eval=np.linspace(0.0, half_period, segments + 1),
            max_step=0.01,
        )
        if not initial_solution.success:
            raise RuntimeError(initial_solution.message)
        patch_state_guesses = initial_solution.y[:, :segments].T
    else:
        patch_state_guesses = np.asarray(patch_state_guesses, dtype=float)
        if patch_state_guesses.shape != (segments, 6):
            raise ValueError("patch_state_guesses must have shape (segments, 6)")
    if abs(patch_state_guesses[0, 2] - z0) > 1.0e-12:
        raise ValueError("The first patch-state z coordinate must equal fixed z0")

    variables = np.r_[
        patch_state_guesses[0, 0],
        patch_state_guesses[0, 4],
        half_period,
        patch_state_guesses[1:].reshape(-1),
    ]
    iterations: list[CorrectionIteration] = []
    terminal_indices = np.array([1, 3, 5], dtype=int)
    identity = np.eye(6)

    for iteration in range(max_iterations):
        x0, ydot0, half_period = variables[:3]
        if half_period <= 0.0:
            raise RuntimeError("Multiple shooting produced a non-positive half-period")
        patch_states = np.empty((segments, 6), dtype=float)
        patch_states[0] = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
        patch_states[1:] = variables[3:].reshape(segments - 1, 6)
        segment_duration = float(half_period / segments)
        residual = np.empty(6 * (segments - 1) + 3, dtype=float)
        jacobian = np.zeros((residual.size, variables.size), dtype=float)
        terminal_states = np.empty((segments, 6), dtype=float)

        for segment, state in enumerate(patch_states):
            solution = integrate_state_and_stm(
                state,
                (0.0, segment_duration),
                mu,
                t_eval=np.array([segment_duration]),
                max_step=0.01,
            )
            if not solution.success:
                raise RuntimeError(solution.message)
            terminal_state, phi = unpack_augmented(solution.y[:, -1])
            terminal_states[segment] = terminal_state
            duration_column = cr3bp_rhs(segment_duration, terminal_state, mu) / segments

            if segment < segments - 1:
                rows = slice(6 * segment, 6 * (segment + 1))
                residual[rows] = terminal_state - patch_states[segment + 1]
                if segment == 0:
                    jacobian[rows, 0] = phi[:, 0]
                    jacobian[rows, 1] = phi[:, 4]
                else:
                    start = 3 + 6 * (segment - 1)
                    jacobian[rows, start : start + 6] = phi
                next_start = 3 + 6 * segment
                jacobian[rows, next_start : next_start + 6] = -identity
                jacobian[rows, 2] = duration_column
            else:
                rows = slice(6 * (segments - 1), residual.size)
                residual[rows] = terminal_state[terminal_indices]
                start = 3 + 6 * (segment - 1)
                jacobian[rows, start : start + 6] = phi[terminal_indices, :]
                jacobian[rows, 2] = duration_column[terminal_indices]

        residual_norm = float(np.linalg.norm(residual))
        iterations.append(
            CorrectionIteration(iteration, float(x0), float(ydot0), float(half_period), residual_norm)
        )
        if residual_norm < tolerance:
            orbit = SpatialSymmetricOrbit(
                mu=mu,
                point=seed_orbit.point,
                family_label=family_label,
                initial_state=patch_states[0],
                half_period=float(half_period),
                fixed_z0=float(z0),
                seed_x_amplitude=seed_orbit.seed_x_amplitude,
                iterations=tuple(iterations),
            )
            continuity = terminal_states[:-1] - patch_states[1:]
            return SpatialMultipleShootingOrbit(
                orbit=orbit,
                patch_states=patch_states,
                segment_duration=segment_duration,
                continuity_errors=np.linalg.norm(continuity, axis=1),
                terminal_symmetry_error=terminal_states[-1, terminal_indices],
            )

        delta = np.linalg.lstsq(jacobian, -residual, rcond=1.0e-12)[0]
        largest = float(np.max(np.abs(delta)))
        if largest > max_delta_component:
            delta *= max_delta_component / largest
        variables += delta

    raise RuntimeError(
        "Spatial multiple shooting did not converge after "
        f"{max_iterations} iterations; initial={iterations[0].residual_norm:.3e}, "
        f"best={min(item.residual_norm for item in iterations):.3e}, "
        f"final={iterations[-1].residual_norm:.3e}"
    )


def sample_spatial_multiple_shooting_orbit(
    corrected: SpatialMultipleShootingOrbit,
    *,
    samples_per_segment: int = 80,
) -> np.ndarray:
    """Sample a corrected half orbit by patches and reflect it to full period."""

    if samples_per_segment < 2:
        raise ValueError("samples_per_segment must be at least two")
    half_segments: list[np.ndarray] = []
    for segment, state in enumerate(corrected.patch_states):
        times = np.linspace(0.0, corrected.segment_duration, samples_per_segment)
        solution = integrate_cr3bp(
            state,
            (0.0, corrected.segment_duration),
            corrected.orbit.mu,
            t_eval=times,
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        values = solution.y.T
        half_segments.append(values if segment == 0 else values[1:])
    first_half = np.concatenate(half_segments, axis=0)
    symmetry = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
    second_half = first_half[-2::-1] * symmetry
    return np.concatenate([first_half, second_half], axis=0)


def audit_spatial_multiple_shooting_orbit(
    corrected: SpatialMultipleShootingOrbit,
    *,
    trajectory: np.ndarray | None = None,
    samples_per_segment: int = 80,
) -> SpatialMultipleShootingClosureAudit:
    """Compute closure diagnostics without reusing stored residual summaries."""

    if trajectory is None:
        trajectory = sample_spatial_multiple_shooting_orbit(
            corrected,
            samples_per_segment=samples_per_segment,
        )
    trajectory = np.asarray(trajectory, dtype=float)
    terminal_indices = np.array([1, 3, 5], dtype=int)
    terminal_states = np.empty_like(corrected.patch_states)
    for segment, state in enumerate(corrected.patch_states):
        solution = integrate_cr3bp(
            state,
            (0.0, corrected.segment_duration),
            corrected.orbit.mu,
            t_eval=np.array([corrected.segment_duration]),
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        terminal_states[segment] = solution.y[:, -1]

    continuity_vectors = terminal_states[:-1] - corrected.patch_states[1:]
    continuity_errors = np.linalg.norm(continuity_vectors, axis=1)
    terminal_symmetry_error = terminal_states[-1, terminal_indices]
    per_segment_endpoint_errors = np.r_[
        continuity_errors,
        np.linalg.norm(terminal_symmetry_error),
    ]
    residual = np.r_[continuity_vectors.reshape(-1), terminal_symmetry_error]

    half_solution = integrate_cr3bp(
        corrected.orbit.initial_state,
        (0.0, corrected.orbit.half_period),
        corrected.orbit.mu,
        t_eval=np.array([corrected.orbit.half_period]),
        max_step=0.01,
    )
    if not half_solution.success:
        raise RuntimeError(half_solution.message)
    half_terminal = half_solution.y[:, -1]

    full_solution = integrate_state_and_stm(
        corrected.orbit.initial_state,
        (0.0, corrected.orbit.period),
        corrected.orbit.mu,
        max_step=0.01,
    )
    if not full_solution.success:
        raise RuntimeError(full_solution.message)
    full_terminal, monodromy_matrix = unpack_augmented(full_solution.y[:, -1])
    monodromy_multipliers = np.linalg.eigvals(monodromy_matrix)

    full_state_solution = integrate_cr3bp(
        corrected.orbit.initial_state,
        (0.0, corrected.orbit.period),
        corrected.orbit.mu,
        t_eval=np.linspace(0.0, corrected.orbit.period, max(200, corrected.patch_states.shape[0] * 20)),
        max_step=0.01,
    )
    if not full_state_solution.success:
        raise RuntimeError(full_state_solution.message)

    trajectory_jacobi = jacobi_constant(trajectory, corrected.orbit.mu)
    full_jacobi = jacobi_constant(full_state_solution.y.T, corrected.orbit.mu)
    return SpatialMultipleShootingClosureAudit(
        patch_to_patch_continuity_vectors=continuity_vectors,
        patch_to_patch_continuity_errors=continuity_errors,
        terminal_symmetry_error=terminal_symmetry_error,
        per_segment_endpoint_errors=per_segment_endpoint_errors,
        multiple_shooting_residual_norm=float(np.linalg.norm(residual)),
        patch_to_patch_continuity_norm=float(np.linalg.norm(continuity_errors)),
        patch_to_patch_continuity_max=float(np.max(continuity_errors)) if continuity_errors.size else 0.0,
        terminal_symmetry_residual_norm=float(np.linalg.norm(terminal_symmetry_error)),
        full_period_terminal_state=full_terminal,
        full_period_single_shoot_closure_error=float(np.linalg.norm(full_terminal - corrected.orbit.initial_state)),
        half_period_terminal_state=half_terminal,
        half_period_single_shoot_symmetry_error=float(np.linalg.norm(half_terminal[terminal_indices])),
        trajectory_sampling_closure_error=float(np.linalg.norm(trajectory[-1] - trajectory[0])),
        trajectory_jacobi_drift=float(np.ptp(trajectory_jacobi)),
        full_period_single_shoot_jacobi_drift=float(np.ptp(full_jacobi)),
        monodromy_matrix=monodromy_matrix,
        monodromy_multipliers=monodromy_multipliers,
        monodromy_multiplier_magnitudes=np.abs(monodromy_multipliers),
        segment_duration_consistency_error=float(
            abs(corrected.segment_duration * corrected.patch_states.shape[0] - corrected.orbit.half_period)
        ),
    )


def continue_spatial_multiple_shooting_fixed_z(
    seed: SpatialMultipleShootingOrbit,
    z_values: list[float] | np.ndarray,
    *,
    tolerance: float = 1.0e-10,
    max_iterations: int = 32,
    max_delta_component: float = 0.05,
) -> list[SpatialMultipleShootingOrbit]:
    """Continue a multiple-shooting branch while fixing successive z crossings."""

    targets = np.asarray(z_values, dtype=float)
    if targets.ndim != 1:
        raise ValueError("z_values must be one-dimensional")
    family = [seed]
    segments = seed.patch_states.shape[0]
    for target_z in targets:
        previous = family[-1]
        patch_guess = previous.patch_states.copy()
        half_period_guess = previous.orbit.half_period
        if len(family) >= 2:
            earlier = family[-2]
            previous_step = previous.orbit.fixed_z0 - earlier.orbit.fixed_z0
            if abs(previous_step) > np.finfo(float).eps:
                ratio = (target_z - previous.orbit.fixed_z0) / previous_step
                patch_guess += ratio * (previous.patch_states - earlier.patch_states)
                half_period_guess += ratio * (
                    previous.orbit.half_period - earlier.orbit.half_period
                )
        patch_guess[0, 2] = float(target_z)
        orbit_guess = replace(
            previous.orbit,
            initial_state=patch_guess[0].copy(),
            half_period=float(half_period_guess),
            fixed_z0=float(target_z),
        )
        family.append(
            correct_spatial_symmetric_orbit_multiple_shooting(
                previous.orbit.mu,
                z0=float(target_z),
                seed_orbit=orbit_guess,
                segments=segments,
                family_label=previous.orbit.family_label,
                patch_state_guesses=patch_guess,
                tolerance=tolerance,
                max_iterations=max_iterations,
                max_delta_component=max_delta_component,
            )
        )
    return family


def correct_vertical_symmetric_orbit(
    mu: float,
    *,
    z0: float,
    point: str = "L2",
    seed_orbit: SpatialSymmetricOrbit | None = None,
    tolerance: float = 1e-11,
    max_iterations: int = 24,
    max_delta_norm: float = 0.015,
) -> SpatialSymmetricOrbit:
    """Correct a vertical-mode-seeded 3D symmetric periodic orbit.

    This uses the same half-period symmetry constraints as
    :func:`correct_spatial_symmetric_orbit`, but the first member starts from
    the collinear point's linear vertical mode instead of a planar Lyapunov
    seed. It is intentionally conservative because larger vertical branches
    require branch-aware continuation to avoid jumping to a nearby halo branch.
    """

    if seed_orbit is None:
        modes = center_modes(mu, point=point)
        x0 = float(modes.equilibrium_state[0])
        ydot0 = 0.0
        half_period = float(np.pi / modes.vertical_frequency)
    else:
        x0 = float(seed_orbit.initial_state[0])
        ydot0 = float(seed_orbit.initial_state[4])
        half_period = float(seed_orbit.half_period)

    iterations: list[CorrectionIteration] = []
    for iteration in range(max_iterations):
        state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
        sol = integrate_state_and_stm(state0, (0.0, half_period), mu, max_step=0.01)
        if not sol.success:
            raise RuntimeError(sol.message)

        final_state, phi = unpack_augmented(sol.y[:, -1])
        residual = np.array([final_state[1], final_state[3], final_state[5]], dtype=float)
        residual_norm = float(np.linalg.norm(residual))
        iterations.append(CorrectionIteration(iteration, x0, ydot0, half_period, residual_norm))
        if residual_norm < tolerance:
            return SpatialSymmetricOrbit(
                mu=mu,
                point=point,
                family_label="vertical",
                initial_state=state0,
                half_period=half_period,
                fixed_z0=float(z0),
                seed_x_amplitude=0.0,
                iterations=tuple(iterations),
            )

        final_derivative = cr3bp_rhs(half_period, final_state, mu)
        jacobian = np.column_stack(
            [
                phi[[1, 3, 5], 0],
                phi[[1, 3, 5], 4],
                final_derivative[[1, 3, 5]],
            ]
        )
        delta = np.linalg.lstsq(jacobian, -residual, rcond=None)[0]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_norm:
            delta *= max_delta_norm / delta_norm
        x0 += float(delta[0])
        ydot0 += float(delta[1])
        half_period += float(delta[2])

    final_state0 = np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float)
    raise RuntimeError(
        f"Vertical symmetric correction did not converge after {max_iterations} iterations; "
        f"last residual={iterations[-1].residual_norm:.3e}, state={final_state0}, T={half_period}"
    )


def vertical_symmetric_family(
    mu: float,
    z_amplitudes: list[float] | np.ndarray,
    *,
    point: str = "L2",
    tolerance: float = 1e-11,
    max_iterations: int = 24,
    secant_predictor: bool = False,
) -> list[SpatialSymmetricOrbit]:
    """Generate a vertical-mode-seeded 3D symmetric periodic family."""

    family: list[SpatialSymmetricOrbit] = []
    amplitudes = np.asarray(z_amplitudes, dtype=float)
    if amplitudes.ndim != 1 or amplitudes.size == 0:
        raise ValueError("z_amplitudes must be a non-empty one-dimensional sequence")
    if np.any(amplitudes <= 0.0) or np.any(np.diff(amplitudes) <= 0.0):
        raise ValueError("z_amplitudes must be positive and strictly increasing")

    for z_amplitude in amplitudes:
        seed = family[-1] if family else None
        if secant_predictor and len(family) >= 2:
            previous_step = family[-1].fixed_z0 - family[-2].fixed_z0
            next_step = float(z_amplitude) - family[-1].fixed_z0
            ratio = next_step / previous_step
            predicted_state = family[-1].initial_state.copy()
            predicted_state[[0, 4]] += ratio * (
                family[-1].initial_state[[0, 4]] - family[-2].initial_state[[0, 4]]
            )
            predicted_half_period = family[-1].half_period + ratio * (
                family[-1].half_period - family[-2].half_period
            )
            seed = replace(
                family[-1],
                initial_state=predicted_state,
                half_period=float(predicted_half_period),
                fixed_z0=float(z_amplitude),
            )
        orbit = correct_vertical_symmetric_orbit(
            mu,
            z0=float(z_amplitude),
            point=point,
            seed_orbit=seed,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        family.append(orbit)
    return family


def target_spatial_orbit_jacobi(
    mu: float,
    *,
    target_jacobi: float,
    z_amplitudes: list[float] | np.ndarray,
    point: str = "L1",
    family_label: str = "halo",
    vertical_mode: bool = False,
    tolerance: float = 1.0e-11,
    max_refinements: int = 10,
    max_iterations: int = 32,
    seed_x_amplitude: float = 0.002,
) -> JacobiTargetedSpatialOrbit:
    """Refine a corrected spatial family member to a target Jacobi constant."""

    amplitudes = np.asarray(z_amplitudes, dtype=float)
    if vertical_mode:
        family = vertical_symmetric_family(
            mu,
            amplitudes,
            point=point,
            max_iterations=max_iterations,
            secant_predictor=True,
        )
    else:
        family = spatial_symmetric_family(
            mu,
            amplitudes,
            point=point,
            seed_x_amplitude=seed_x_amplitude,
            family_label=family_label,
            max_iterations=max_iterations,
        )

    errors = np.asarray([orbit.jacobi - target_jacobi for orbit in family], dtype=float)
    exact = np.flatnonzero(np.abs(errors) <= tolerance)
    history_z = list(amplitudes)
    history_jacobi = [orbit.jacobi for orbit in family]
    if exact.size:
        orbit = family[int(exact[0])]
        return JacobiTargetedSpatialOrbit(
            orbit=orbit,
            target_jacobi=float(target_jacobi),
            z0_history=np.asarray(history_z),
            jacobi_history=np.asarray(history_jacobi),
        )

    bracket_indices = np.flatnonzero(errors[:-1] * errors[1:] < 0.0)
    if bracket_indices.size == 0:
        raise ValueError("z_amplitudes do not bracket the target Jacobi constant")
    lower_index = int(bracket_indices[0])
    orbit_a = family[lower_index]
    orbit_b = family[lower_index + 1]
    error_a = orbit_a.jacobi - target_jacobi
    error_b = orbit_b.jacobi - target_jacobi

    for _ in range(max_refinements):
        z_a = orbit_a.fixed_z0
        z_b = orbit_b.fixed_z0
        if abs(error_b - error_a) > np.finfo(float).eps:
            trial_z = z_a - error_a * (z_b - z_a) / (error_b - error_a)
        else:
            trial_z = 0.5 * (z_a + z_b)
        low_z, high_z = sorted((z_a, z_b))
        if not low_z < trial_z < high_z:
            trial_z = 0.5 * (z_a + z_b)
        seed = orbit_a if abs(trial_z - z_a) <= abs(trial_z - z_b) else orbit_b
        if vertical_mode:
            trial = correct_vertical_symmetric_orbit(
                mu,
                z0=float(trial_z),
                point=point,
                seed_orbit=seed,
                tolerance=tolerance,
                max_iterations=max_iterations,
            )
        else:
            trial = correct_spatial_symmetric_orbit(
                mu,
                z0=float(trial_z),
                point=point,
                seed_x_amplitude=seed_x_amplitude,
                seed_orbit=seed,
                family_label=family_label,
                tolerance=tolerance,
                max_iterations=max_iterations,
            )
        trial_error = trial.jacobi - target_jacobi
        history_z.append(float(trial_z))
        history_jacobi.append(trial.jacobi)
        if abs(trial_error) <= tolerance:
            return JacobiTargetedSpatialOrbit(
                orbit=trial,
                target_jacobi=float(target_jacobi),
                z0_history=np.asarray(history_z),
                jacobi_history=np.asarray(history_jacobi),
            )
        if error_a * trial_error < 0.0:
            orbit_b, error_b = trial, trial_error
        else:
            orbit_a, error_a = trial, trial_error

    best = min((orbit_a, orbit_b), key=lambda orbit: abs(orbit.jacobi - target_jacobi))
    raise RuntimeError(
        "Jacobi-targeted spatial orbit did not converge; "
        f"best error={best.jacobi - target_jacobi:.3e}"
    )


def constant_energy_periodic_boundaries(
    system: CR3BPSystem,
    *,
    target_jacobi: float = 3.1389,
) -> tuple[ConstantEnergyBoundaryFrequency, ConstantEnergyBoundaryFrequency]:
    """Return halo and vertical periodic boundaries for a constant-energy torus family."""

    if system.time_unit_days is None:
        raise ValueError("system time_unit_days is required for dimensional mapping times")
    halo = target_spatial_orbit_jacobi(
        system.mu,
        target_jacobi=target_jacobi,
        z_amplitudes=np.arange(0.005, 0.0601, 0.005),
        point="L1",
        family_label="halo",
        seed_x_amplitude=0.002,
    )
    vertical = target_spatial_orbit_jacobi(
        system.mu,
        target_jacobi=target_jacobi,
        z_amplitudes=np.r_[
            np.arange(0.005, 0.0201, 0.0025),
            np.arange(0.025, 0.1051, 0.005),
        ],
        point="L1",
        family_label="vertical",
        vertical_mode=True,
    )

    from .manifolds import monodromy

    results: list[ConstantEnergyBoundaryFrequency] = []
    for family_name, targeted in (("quasi_halo", halo), ("quasi_vertical", vertical)):
        diagnostic = monodromy(targeted.orbit)
        eigenvalues = diagnostic.eigenvalues
        candidates = [
            value
            for value in eigenvalues
            if value.imag > 1.0e-6
            and abs(abs(value) - 1.0) < 1.0e-3
            and abs(np.angle(value)) > 1.0e-3
        ]
        if not candidates:
            raise RuntimeError(f"no nontrivial elliptic Floquet multiplier found for {family_name}")
        eigenvalue = max(candidates, key=lambda value: abs(np.angle(value)))
        rotation_angle = float(abs(np.angle(eigenvalue)))
        results.append(
            ConstantEnergyBoundaryFrequency(
                family_label=family_name,
                targeted=targeted,
                rotation_eigenvalue=complex(eigenvalue),
                rotation_angle_rad=rotation_angle,
                frequency_ratio=float(2.0 * np.pi / rotation_angle),
                mapping_time_days=float(targeted.orbit.period * system.time_unit_days),
                periodicity_error=float(diagnostic.periodicity_error),
            )
        )
    return results[0], results[1]


def _halo_transverse_floquet_pair(
    orbit: SpatialSymmetricOrbit,
    *,
    target_angle: float,
) -> tuple[complex, np.ndarray, float, float]:
    """Return the unit-circle Floquet pair nearest a requested resonance angle."""

    sol = integrate_state_and_stm(orbit.initial_state, (0.0, orbit.period), orbit.mu, max_step=0.01)
    if not sol.success:
        raise RuntimeError(sol.message)
    terminal_state, matrix = unpack_augmented(sol.y[:, -1])
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    candidates = [
        idx
        for idx, value in enumerate(eigenvalues)
        if value.imag > 1.0e-7
        and abs(abs(value) - 1.0) < 1.0e-4
        and abs(np.angle(value)) > 1.0e-3
    ]
    if not candidates:
        raise RuntimeError("No nontrivial elliptic Floquet multiplier found")
    index = min(candidates, key=lambda idx: abs(abs(np.angle(eigenvalues[idx])) - target_angle))
    eigenvalue = complex(eigenvalues[index])
    angle = float(abs(np.angle(eigenvalue)))
    periodicity_error = float(np.linalg.norm(terminal_state - orbit.initial_state))
    return eigenvalue, eigenvectors[:, index], angle, periodicity_error


def _spatial_symmetric_variables(orbit: SpatialSymmetricOrbit) -> np.ndarray:
    return np.array(
        [
            orbit.initial_state[0],
            orbit.fixed_z0,
            orbit.initial_state[4],
            orbit.half_period,
        ],
        dtype=float,
    )


def _period_doubling_floquet_data(
    orbit: SpatialSymmetricOrbit,
) -> tuple[float, complex, np.ndarray, float, float, float]:
    """Return the Floquet multiplier data nearest the period-doubling crossing."""

    sol = integrate_state_and_stm(orbit.initial_state, (0.0, orbit.period), orbit.mu, max_step=0.01)
    if not sol.success:
        raise RuntimeError(sol.message)
    terminal_state, matrix = unpack_augmented(sol.y[:, -1])
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    candidates = [
        idx
        for idx, value in enumerate(eigenvalues)
        if value.real < 0.0 or abs(abs(np.angle(value)) - np.pi) < 0.5
    ]
    if not candidates:
        candidates = list(range(len(eigenvalues)))
    index = min(candidates, key=lambda idx: abs(eigenvalues[idx] + 1.0))
    eigenvalue = complex(eigenvalues[index])
    indicator = float(np.real(eigenvalue + 1.0 / eigenvalue) + 2.0)
    angle = float(abs(np.angle(eigenvalue)))
    distance_to_minus_one = float(abs(eigenvalue + 1.0))
    periodicity_error = float(np.linalg.norm(terminal_state - orbit.initial_state))
    return (
        indicator,
        eigenvalue,
        eigenvectors[:, index],
        angle,
        distance_to_minus_one,
        periodicity_error,
    )


def _correct_spatial_symmetric_between(
    lower: SpatialSymmetricOrbit,
    upper: SpatialSymmetricOrbit,
    fraction: float,
    *,
    tolerance: float,
) -> SpatialSymmetricOrbit:
    lower_variables = _spatial_symmetric_variables(lower)
    upper_variables = _spatial_symmetric_variables(upper)
    tangent = upper_variables - lower_variables
    tangent /= np.linalg.norm(tangent)
    predictor = (1.0 - fraction) * lower_variables + fraction * upper_variables
    return _spatial_symmetric_arclength_correction(
        lower.mu,
        predictor=predictor,
        tangent=tangent,
        point=lower.point,
        family_label=lower.family_label,
        seed_x_amplitude=lower.seed_x_amplitude,
        tolerance=tolerance,
        max_iterations=64,
        max_delta_norm=0.03,
    )


def _target_halo_period_doubling_resonance(
    mu: float,
    *,
    z_bracket: tuple[float, float],
    point: str,
    seed_x_amplitude: float,
    angle_tolerance: float,
    max_refinements: int,
) -> HaloFloquetResonance:
    lower_z, upper_z = map(float, z_bracket)
    prefix = np.arange(0.005, lower_z, 0.005)
    local_step = min(0.0005, max((upper_z - lower_z) / 10.0, 1.0e-4))
    local = np.arange(lower_z, upper_z + 0.5 * local_step, local_step)
    amplitudes = np.unique(np.r_[prefix, local])
    natural = spatial_symmetric_family(
        mu,
        amplitudes,
        point=point,
        seed_x_amplitude=seed_x_amplitude,
        family_label="halo",
        max_iterations=48,
    )
    folded = spatial_symmetric_pseudo_arclength_family(
        natural[-2:],
        members=max(36, max_refinements + 9),
        step_size=0.003,
        max_iterations=48,
        max_delta_norm=0.05,
    )
    data = [_period_doubling_floquet_data(orbit) for orbit in folded]

    bracket: tuple[SpatialSymmetricOrbit, SpatialSymmetricOrbit] | None = None
    bracket_data: tuple[tuple[float, complex, np.ndarray, float, float, float], tuple[float, complex, np.ndarray, float, float, float]] | None = None
    for left, right, left_data, right_data in zip(folded[:-1], folded[1:], data[:-1], data[1:]):
        if left_data[0] * right_data[0] <= 0.0:
            bracket = (left, right)
            bracket_data = (left_data, right_data)
            break
    if bracket is None or bracket_data is None:
        best_index = min(range(len(folded)), key=lambda idx: data[idx][4])
        best_data = data[best_index]
        raise RuntimeError(
            "q=2 period-doubling targeting did not bracket a -1 Floquet crossing; "
            f"best |lambda+1|={best_data[4]:.3e}"
        )

    lower, upper = bracket
    lower_data, upper_data = bracket_data
    candidates: list[tuple[float, SpatialSymmetricOrbit, tuple[float, complex, np.ndarray, float, float, float]]] = [
        (lower_data[4], lower, lower_data),
        (upper_data[4], upper, upper_data),
    ]
    for _ in range(max_refinements):
        trial = _correct_spatial_symmetric_between(
            lower,
            upper,
            0.5,
            tolerance=min(1.0e-11, angle_tolerance),
        )
        trial_data = _period_doubling_floquet_data(trial)
        candidates.append((trial_data[4], trial, trial_data))
        if trial_data[4] <= max(angle_tolerance, 1.0e-10) and abs(trial_data[1].imag) > 1.0e-10:
            break
        if lower_data[0] * trial_data[0] <= 0.0:
            upper, upper_data = trial, trial_data
        else:
            lower, lower_data = trial, trial_data

    complex_candidates = [
        item
        for item in candidates
        if abs(item[2][1].imag) > 1.0e-10 and abs(item[2][3] - np.pi) <= 1.0e-6
    ]
    _, best_orbit, best_data = min(complex_candidates or candidates, key=lambda item: item[0])
    _, eigenvalue, eigenvector, angle, distance_to_minus_one, periodicity_error = best_data
    if distance_to_minus_one > max(5.0e-6, 10.0 * angle_tolerance):
        raise RuntimeError(
            "q=2 period-doubling targeting did not converge close enough to lambda=-1; "
            f"|lambda+1|={distance_to_minus_one:.3e}"
        )
    return HaloFloquetResonance(
        resonance=2,
        orbit=best_orbit,
        eigenvalue=eigenvalue,
        eigenvector=eigenvector,
        rotation_angle_rad=angle,
        frequency_ratio=float(2.0 * np.pi / angle),
        periodicity_error=periodicity_error,
    )


def target_halo_floquet_resonance(
    mu: float,
    *,
    resonance: int,
    z_bracket: tuple[float, float],
    point: str = "L1",
    seed_x_amplitude: float = 0.002,
    angle_tolerance: float = 1.0e-8,
    max_refinements: int = 24,
) -> HaloFloquetResonance:
    """Target a transverse q:1 Floquet resonance on a corrected halo family."""

    lower_z, upper_z = map(float, z_bracket)
    if not 0.0 < lower_z < upper_z:
        raise ValueError("z_bracket must be positive and increasing")
    if resonance == 2:
        return _target_halo_period_doubling_resonance(
            mu,
            z_bracket=(lower_z, upper_z),
            point=point,
            seed_x_amplitude=seed_x_amplitude,
            angle_tolerance=angle_tolerance,
            max_refinements=max_refinements,
        )
    if resonance < 2:
        raise ValueError("resonance must be at least 2")

    prefix = np.arange(0.005, lower_z, 0.005)
    amplitudes = np.unique(np.r_[prefix, lower_z, upper_z])
    family = spatial_symmetric_family(
        mu,
        amplitudes,
        point=point,
        seed_x_amplitude=seed_x_amplitude,
        family_label="halo",
        max_iterations=48,
    )
    lower = family[-2]
    upper = family[-1]
    target_angle = float(2.0 * np.pi / resonance)

    def evaluate(orbit: SpatialSymmetricOrbit) -> tuple[float, complex, np.ndarray, float, float]:
        eigenvalue, eigenvector, angle, periodicity_error = _halo_transverse_floquet_pair(
            orbit,
            target_angle=target_angle,
        )
        return angle - target_angle, eigenvalue, eigenvector, angle, periodicity_error

    lower_data = evaluate(lower)
    upper_data = evaluate(upper)
    if lower_data[0] * upper_data[0] > 0.0:
        raise ValueError(
            f"z_bracket does not enclose the q={resonance} Floquet resonance: "
            f"angle errors {lower_data[0]:.3e}, {upper_data[0]:.3e}"
        )

    best_orbit = min((lower, upper), key=lambda orbit: abs(evaluate(orbit)[0]))
    best_data = evaluate(best_orbit)
    for _ in range(max_refinements):
        trial_z = 0.5 * (lower.fixed_z0 + upper.fixed_z0)
        seed = lower if abs(trial_z - lower.fixed_z0) <= abs(trial_z - upper.fixed_z0) else upper
        trial = correct_spatial_symmetric_orbit(
            mu,
            z0=trial_z,
            point=point,
            seed_x_amplitude=seed_x_amplitude,
            seed_orbit=seed,
            family_label="halo",
            max_iterations=48,
        )
        trial_data = evaluate(trial)
        if abs(trial_data[0]) < abs(best_data[0]):
            best_orbit, best_data = trial, trial_data
        if abs(trial_data[0]) <= angle_tolerance:
            best_orbit, best_data = trial, trial_data
            break
        if lower_data[0] * trial_data[0] <= 0.0:
            upper, upper_data = trial, trial_data
        else:
            lower, lower_data = trial, trial_data
    else:
        raise RuntimeError(
            f"q={resonance} Floquet targeting did not converge; "
            f"best angle error={best_data[0]:.3e}"
        )

    _, eigenvalue, eigenvector, angle, periodicity_error = best_data
    return HaloFloquetResonance(
        resonance=int(resonance),
        orbit=best_orbit,
        eigenvalue=eigenvalue,
        eigenvector=eigenvector,
        rotation_angle_rad=angle,
        frequency_ratio=float(2.0 * np.pi / angle),
        periodicity_error=periodicity_error,
    )


def _symmetry_compatible_floquet_displacement(
    resonance: HaloFloquetResonance,
    position_amplitude: float,
) -> np.ndarray:
    if position_amplitude <= 0.0:
        raise ValueError("position_amplitude must be positive")
    basis = np.column_stack([np.real(resonance.eigenvector), -np.imag(resonance.eigenvector)])
    forbidden = basis[[1, 3, 5], :]
    _, _, right_vectors = np.linalg.svd(forbidden, full_matrices=False)
    direction = basis @ right_vectors[-1, :]
    direction[[1, 3, 5]] = 0.0
    position_norm = float(np.linalg.norm(direction[:3]))
    if position_norm <= np.finfo(float).eps:
        raise RuntimeError("Floquet eigenspace has no symmetry-compatible position direction")
    direction *= position_amplitude / position_norm
    if direction[2] < 0.0:
        direction *= -1.0
    return direction


def resonant_halo_multiple_shooting_guess(
    resonance: HaloFloquetResonance,
    *,
    position_amplitude: float,
    segments: int,
) -> tuple[SpatialSymmetricOrbit, np.ndarray]:
    """Build patch-local Floquet guesses without unstable multi-period propagation."""

    if segments < 2:
        raise ValueError("segments must be at least two")
    direction = _symmetry_compatible_floquet_displacement(resonance, position_amplitude)
    basis = np.column_stack([np.real(resonance.eigenvector), -np.imag(resonance.eigenvector)])
    coefficients = np.linalg.lstsq(basis, direction, rcond=None)[0]
    complex_coefficient = complex(coefficients[0], coefficients[1])
    half_period = float(resonance.resonance * resonance.orbit.half_period)
    patch_times = np.arange(segments, dtype=float) * half_period / segments
    patch_states = np.empty((segments, 6), dtype=float)

    for index, time in enumerate(patch_times):
        cycles = int(np.floor((time + 1.0e-12) / resonance.orbit.period))
        local_time = float(time - cycles * resonance.orbit.period)
        if local_time < 1.0e-12:
            base_state = resonance.orbit.initial_state
            local_stm = np.eye(6)
        else:
            solution = integrate_state_and_stm(
                resonance.orbit.initial_state,
                (0.0, local_time),
                resonance.orbit.mu,
                t_eval=np.array([local_time]),
                max_step=0.01,
            )
            if not solution.success:
                raise RuntimeError(solution.message)
            base_state, local_stm = unpack_augmented(solution.y[:, -1])
        local_mode = local_stm @ resonance.eigenvector
        multiplier = resonance.eigenvalue**cycles
        displacement = np.real(complex_coefficient * multiplier * local_mode)
        patch_states[index] = base_state + displacement

    patch_states[0, [1, 3, 5]] = 0.0
    seed_orbit = replace(
        resonance.orbit,
        initial_state=patch_states[0].copy(),
        half_period=half_period,
        fixed_z0=float(patch_states[0, 2]),
        family_label=f"period{resonance.resonance}",
    )
    return seed_orbit, patch_states


def resonant_halo_linear_seed(
    resonance: HaloFloquetResonance,
    *,
    position_amplitude: float,
    samples: int = 1200,
) -> ResonantHaloLinearSeed:
    """Propagate a symmetry-compatible Floquet perturbation for q halo periods."""

    if samples < 2:
        raise ValueError("samples must be at least two")
    direction = _symmetry_compatible_floquet_displacement(resonance, position_amplitude)

    initial_state = resonance.orbit.initial_state + direction
    propagation_time = float(resonance.resonance * resonance.orbit.period)
    times = np.linspace(0.0, propagation_time, samples)
    solution = integrate_cr3bp(
        initial_state,
        (0.0, propagation_time),
        resonance.orbit.mu,
        t_eval=times,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    trajectory = solution.y.T
    return ResonantHaloLinearSeed(
        resonance=resonance.resonance,
        base_orbit=resonance.orbit,
        base_eigenvalue=resonance.eigenvalue,
        base_frequency_ratio=resonance.frequency_ratio,
        initial_state=initial_state,
        trajectory=trajectory,
        propagation_time=propagation_time,
        closure_error=float(np.linalg.norm(trajectory[-1] - trajectory[0])),
        position_amplitude=float(position_amplitude),
    )


def period_q_halo_examples(mu: float) -> tuple[ResonantHaloExample, ...]:
    """Compute corrected period-2, period-3, and period-8 Earth-Moon halo examples."""

    period_two_resonance = target_halo_floquet_resonance(
        mu,
        resonance=2,
        z_bracket=(0.0805, 0.0850),
        angle_tolerance=1.0e-8,
        max_refinements=44,
    )
    seed_two, patches_two = resonant_halo_multiple_shooting_guess(
        period_two_resonance,
        position_amplitude=6.0e-3,
        segments=4,
    )
    corrected_two = correct_spatial_symmetric_orbit_multiple_shooting(
        mu,
        z0=seed_two.fixed_z0,
        seed_orbit=seed_two,
        segments=4,
        family_label="period2",
        patch_state_guesses=patches_two,
        max_iterations=80,
        max_delta_component=0.04,
    )

    period_three_resonance = target_halo_floquet_resonance(
        mu,
        resonance=3,
        z_bracket=(0.084, 0.0845),
    )
    seed_three, patches_three = resonant_halo_multiple_shooting_guess(
        period_three_resonance,
        position_amplitude=5.0e-4,
        segments=6,
    )
    first_three = correct_spatial_symmetric_orbit_multiple_shooting(
        mu,
        z0=seed_three.fixed_z0,
        seed_orbit=seed_three,
        segments=6,
        family_label="period3",
        patch_state_guesses=patches_three,
        max_iterations=40,
        max_delta_component=0.01,
    )
    corrected_three = continue_spatial_multiple_shooting_fixed_z(
        first_three,
        np.array([0.0855, 0.0875, 0.0900, 0.0925, 0.0950]),
        max_iterations=42,
        max_delta_component=0.03,
    )[-1]

    period_eight_resonance = target_halo_floquet_resonance(
        mu,
        resonance=8,
        z_bracket=(0.055, 0.060),
    )
    seed_eight, patches_eight = resonant_halo_multiple_shooting_guess(
        period_eight_resonance,
        position_amplitude=1.0e-4,
        segments=16,
    )
    first_eight = correct_spatial_symmetric_orbit_multiple_shooting(
        mu,
        z0=seed_eight.fixed_z0,
        seed_orbit=seed_eight,
        segments=16,
        family_label="period8",
        patch_state_guesses=patches_eight,
        max_iterations=40,
        max_delta_component=0.01,
    )
    corrected_eight = continue_spatial_multiple_shooting_fixed_z(
        first_eight,
        np.array([0.0605, 0.0655, 0.0705, 0.0755, 0.0805]),
        max_iterations=42,
        max_delta_component=0.05,
    )[-1]

    corrected = (corrected_two, corrected_three, corrected_eight)
    resonances = (period_two_resonance, period_three_resonance, period_eight_resonance)
    samples = (160, 90, 45)
    return tuple(
        ResonantHaloExample(
            resonance=resonance.resonance,
            bifurcation=resonance,
            corrected=orbit,
            trajectory=sample_spatial_multiple_shooting_orbit(
                orbit,
                samples_per_segment=sample_count,
            ),
        )
        for resonance, orbit, sample_count in zip(resonances, corrected, samples)
    )


def propagate_half_orbit(state0: np.ndarray, half_period: float, mu: float, samples: int = 400) -> np.ndarray:
    """Return states along a half orbit."""

    t_eval = np.linspace(0.0, half_period, samples)
    sol = integrate_state_and_stm(state0, (0.0, half_period), mu, t_eval=t_eval)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y[:6, :].T


def propagate_periodic_orbit(orbit: PlanarLyapunovOrbit, samples: int = 500) -> np.ndarray:
    """Return states along one full period of a corrected periodic orbit."""

    t_eval = np.linspace(0.0, orbit.period, samples)
    sol = integrate_state_and_stm(orbit.initial_state, (0.0, orbit.period), orbit.mu, t_eval=t_eval)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y[:6, :].T


def planar_lyapunov_family(
    mu: float,
    x_amplitudes: list[float] | np.ndarray,
    *,
    point: str = "L2",
    tolerance: float = 1e-10,
    max_iterations: int = 20,
) -> list[PlanarLyapunovOrbit]:
    """Generate a natural-parameter family of planar Lyapunov orbits."""

    family: list[PlanarLyapunovOrbit] = []
    for amplitude in x_amplitudes:
        guess = planar_lyapunov_linear_guess(mu, point=point, x_amplitude=float(amplitude))
        orbit = correct_planar_lyapunov(
            mu,
            guess,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )
        family.append(orbit)
    return family


def propagate_to_y_crossing(
    state0: np.ndarray,
    mu: float,
    *,
    t_max: float = 4.0,
    samples: int = 400,
    direction: int = -1,
) -> np.ndarray:
    """Propagate until the next nontrivial crossing of the x-z plane."""

    def y_crossing(t: float, state: np.ndarray) -> float:
        if t < 1e-6:
            return 1.0
        return float(state[1])

    y_crossing.terminal = True
    y_crossing.direction = direction

    sol = solve_ivp(
        lambda t, y: cr3bp_rhs(t, y, mu),
        (0.0, t_max),
        np.asarray(state0, dtype=float),
        method="DOP853",
        rtol=1e-11,
        atol=1e-13,
        max_step=0.01,
        dense_output=True,
        events=y_crossing,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    if len(sol.t_events[0]) == 0:
        raise RuntimeError("No y=0 crossing detected")
    crossing_time = float(sol.t_events[0][0])
    times = np.linspace(0.0, crossing_time, samples)
    return sol.sol(times).T
