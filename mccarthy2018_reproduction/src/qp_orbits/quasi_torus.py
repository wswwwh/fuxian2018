"""First-pass quasi-periodic torus approximations for Chapter 3 figures."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import pickle

import numpy as np

from .constants import CR3BPSystem
from .cr3bp import (
    cr3bp_rhs,
    integrate_cr3bp,
    integrate_states_cr3bp,
    jacobi_constant,
    potential_gradient,
)
from .linear_modes import center_modes
from .periodic_orbits import (
    correct_planar_dro,
    correct_planar_lyapunov,
    correct_spatial_symmetric_orbit,
    correct_vertical_symmetric_orbit,
    planar_lyapunov_family,
    planar_lyapunov_linear_guess,
    propagate_periodic_orbit,
    spatial_symmetric_family,
    target_spatial_orbit_jacobi,
    vertical_symmetric_family,
)
from .variational import integrate_state_and_stm, integrate_states_and_stms, unpack_augmented


_HIGH_ORDER_CACHE_VERSION = 1
_VERTICAL_CONTINUATION_CACHE_VERSION = 1
_FIXED_FREQUENCY_CACHE_VERSION = 1
_FIXED_MAPPING_DRO_CACHE_VERSION = 1


def _high_order_cache_path(parameters: dict[str, float | int]) -> Path:
    """Return a versioned cache path for an expensive continuation family."""

    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]
    project_root = Path(__file__).resolve().parents[2]
    return (
        project_root
        / "data"
        / "computed"
        / "cache"
        / f"quasi_halo_high_order_v{_HIGH_ORDER_CACHE_VERSION}_{digest}.pkl"
    )


def _vertical_continuation_cache_path(
    kind: str,
    parameters: dict[str, object],
) -> Path:
    """Return a versioned cache path for a quasi-vertical continuation."""

    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]
    project_root = Path(__file__).resolve().parents[2]
    return (
        project_root
        / "data"
        / "computed"
        / "cache"
        / (
            f"quasi_vertical_{kind}_v{_VERTICAL_CONTINUATION_CACHE_VERSION}_"
            f"{digest}.pkl"
        )
    )


def _fixed_frequency_cache_path(kind: str, parameters: dict[str, object]) -> Path:
    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]
    project_root = Path(__file__).resolve().parents[2]
    return (
        project_root
        / "data"
        / "computed"
        / "cache"
        / f"fixed_frequency_{kind}_v{_FIXED_FREQUENCY_CACHE_VERSION}_{digest}.pkl"
    )


def _fixed_mapping_dro_cache_path(parameters: dict[str, object]) -> Path:
    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]
    project_root = Path(__file__).resolve().parents[2]
    return (
        project_root
        / "data"
        / "computed"
        / "cache"
        / f"fixed_mapping_dro_v{_FIXED_MAPPING_DRO_CACHE_VERSION}_{digest}.pkl"
    )


@dataclass(frozen=True)
class LinearQuasiHaloMember:
    """Shape-match quasi-halo torus member anchored at an L1 center-mode scale."""

    y_amplitude_km: float
    z_amplitude_km: float
    mapping_time_days: float
    surface: np.ndarray
    invariant_curve: np.ndarray


@dataclass(frozen=True)
class LinearQuasiVerticalMember:
    """Shape-match quasi-vertical torus member anchored at an L1 center-mode scale."""

    y_amplitude_km: float
    z_amplitude_km: float
    mapping_time_days: float
    surface: np.ndarray
    invariant_curve: np.ndarray


@dataclass(frozen=True)
class SurfaceFamilyMember:
    """Generic first-pass surface member for Chapter 3 proxy families."""

    surface: np.ndarray
    invariant_curve: np.ndarray
    y_amplitude_km: float = 0.0
    z_amplitude_km: float = 0.0
    mapping_time_days: float = 0.0
    jacobi: float = 0.0
    rotation_angle_rad: float = 0.0


@dataclass(frozen=True)
class CentralPeriodicOrbitScene:
    """CR3BP-corrected central periodic orbits and section-anchored map curves."""

    map_lyapunov: tuple[np.ndarray, ...]
    map_halo_upper: tuple[np.ndarray, ...]
    map_halo_lower: tuple[np.ndarray, ...]
    lyapunov_orbits: tuple[np.ndarray, ...]
    halo_orbit: np.ndarray
    vertical_orbit: np.ndarray
    halo_section_centers: np.ndarray
    vertical_section_center: np.ndarray


@dataclass(frozen=True)
class StroboscopicInvariantCurveSeed:
    """Small-amplitude invariant-curve seed around a corrected periodic orbit."""

    mu: float
    orbit_state: np.ndarray
    orbit_period: float
    orbit_jacobi: float
    monodromy_eigenvalue: complex
    rotation_angle_rad: float
    vertical_amplitude: float
    phases: np.ndarray
    initial_states: np.ndarray
    mapped_states: np.ndarray
    predicted_states: np.ndarray
    residuals: np.ndarray
    map_stms: np.ndarray
    mode_basis: np.ndarray
    curve_points: np.ndarray
    initial_points: np.ndarray
    mapped_points: np.ndarray
    predicted_points: np.ndarray
    base_family: str
    base_orbit_amplitude: float
    mode_component: int
    mode_amplitude: float

    @property
    def residual_norms(self) -> np.ndarray:
        return np.linalg.norm(self.residuals, axis=1)


@dataclass(frozen=True)
class StroboscopicShootingCorrection:
    """Fixed-target STM shooting correction for a stroboscopic curve seed."""

    seed: StroboscopicInvariantCurveSeed
    corrected_initial_states: np.ndarray
    corrected_mapped_states: np.ndarray
    target_states: np.ndarray
    corrected_initial_points: np.ndarray
    corrected_mapped_points: np.ndarray
    residual_history: np.ndarray
    correction_norm_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class StroboscopicCurveNewtonCorrection:
    """Fixed-rotation global Newton correction for a discretized curve."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    residual_history: np.ndarray
    correction_norm_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FreeRotationCurveCorrection:
    """Invariant-curve correction with a solved rotation angle and constraints."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    target_amplitude: float
    amplitude_component: int
    residual_history: np.ndarray
    amplitude_residual_history: np.ndarray
    phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    rotation_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FixedMappingPseudoArclengthCorrection:
    """Fixed-time invariant curve corrected on a pseudo-arclength plane."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    target_amplitude: float
    amplitude_component: int
    predictor_variables: np.ndarray
    continuation_tangent: np.ndarray
    step_size: float
    residual_history: np.ndarray
    phase_residual_history: np.ndarray
    arclength_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    rotation_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FixedRotationCurveCorrection:
    """Fixed-time, fixed-rotation invariant-curve correction."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    target_amplitude: float
    amplitude_component: int
    residual_history: np.ndarray
    phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FreeMappingTimeCurveCorrection:
    """Invariant-curve correction with fixed rotation and solved mapping time."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    target_amplitude: float
    amplitude_component: int
    residual_history: np.ndarray
    amplitude_residual_history: np.ndarray
    phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FreeEnergyCurveCorrection:
    """Invariant-curve correction at fixed mean Jacobi constant with free time and rotation."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    target_jacobi: float
    target_amplitude: float
    amplitude_component: int
    residual_history: np.ndarray
    energy_residual_history: np.ndarray
    amplitude_residual_history: np.ndarray
    phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    rotation_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FixedJacobiFreeTimeRotationCurveCorrection:
    """Experimental Route B curve correction with fixed mean Jacobi and free time/rho."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    target_jacobi: float
    residual_history: np.ndarray
    energy_residual_history: np.ndarray
    phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    rotation_history: np.ndarray
    jacobian_condition_history: np.ndarray
    jacobian_min_singular_history: np.ndarray
    jacobian_max_singular_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class PseudoArclengthCurveCorrection:
    """Fixed-energy invariant curve corrected on a pseudo-arclength plane."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    target_jacobi: float
    predictor_variables: np.ndarray
    continuation_tangent: np.ndarray
    step_size: float
    residual_history: np.ndarray
    energy_residual_history: np.ndarray
    longitudinal_phase_residual_history: np.ndarray
    latitudinal_phase_residual_history: np.ndarray
    arclength_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    rotation_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FixedFrequencyPseudoArclengthCorrection:
    """Fixed-rotation invariant curve corrected on a pseudo-arclength plane."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    predictor_variables: np.ndarray
    continuation_tangent: np.ndarray
    step_size: float
    residual_history: np.ndarray
    longitudinal_phase_residual_history: np.ndarray
    latitudinal_phase_residual_history: np.ndarray
    arclength_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class FixedFrequencyEnergyCurveCorrection:
    """Fixed-rotation invariant curve corrected at one Jacobi constant."""

    seed: StroboscopicInvariantCurveSeed
    corrected_states: np.ndarray
    corrected_mapped_states: np.ndarray
    corrected_target_states: np.ndarray
    corrected_points: np.ndarray
    corrected_mapped_points: np.ndarray
    corrected_target_points: np.ndarray
    interpolation_matrix: np.ndarray
    rotation_angle_rad: float
    mapping_time: float
    target_jacobi: float
    residual_history: np.ndarray
    energy_residual_history: np.ndarray
    longitudinal_phase_residual_history: np.ndarray
    latitudinal_phase_residual_history: np.ndarray
    correction_norm_history: np.ndarray
    mapping_time_history: np.ndarray
    jacobian_condition_history: np.ndarray

    @property
    def initial_residual_norms(self) -> np.ndarray:
        return self.residual_history[0]

    @property
    def final_residual_norms(self) -> np.ndarray:
        return self.residual_history[-1]


@dataclass(frozen=True)
class CorrectedStroboscopicTorus:
    """CR3BP surface swept by propagating a corrected stroboscopic curve."""

    correction: (
        StroboscopicCurveNewtonCorrection
        | FreeRotationCurveCorrection
        | FreeMappingTimeCurveCorrection
        | FreeEnergyCurveCorrection
        | PseudoArclengthCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    )
    normalized_times: np.ndarray
    states: np.ndarray
    surface: np.ndarray
    invariant_curve: np.ndarray
    terminal_curve: np.ndarray
    target_curve: np.ndarray
    closure_residuals: np.ndarray
    jacobi_values: np.ndarray

    @property
    def closure_error_norms(self) -> np.ndarray:
        return np.linalg.norm(self.closure_residuals, axis=1)

    @property
    def jacobi_drift(self) -> float:
        return float(np.ptp(self.jacobi_values))


def _mode_cycle(eigenvector: np.ndarray, phases: np.ndarray) -> np.ndarray:
    return np.real(np.exp(1j * phases[:, None]) * eigenvector[None, :])


def _scale_mode_to_component(eigenvector: np.ndarray, component: int, amplitude: float) -> float:
    phases = np.linspace(0.0, 2.0 * np.pi, 720, endpoint=False)
    unit = _mode_cycle(eigenvector, phases)
    component_amplitude = float(np.max(np.abs(unit[:, component])))
    if component_amplitude <= 0.0:
        raise RuntimeError("Cannot scale center mode with zero requested component")
    return float(amplitude / component_amplitude)


def _project_to_mode_plane(states: np.ndarray, origin: np.ndarray, basis: np.ndarray) -> np.ndarray:
    values = np.atleast_2d(states)
    return np.linalg.lstsq(basis, (values - origin).T, rcond=None)[0].T


def _trigonometric_interpolation_matrix(phases: np.ndarray, evaluation_phases: np.ndarray) -> np.ndarray:
    """Return periodic trigonometric interpolation weights for odd sample counts."""

    sample_count = len(phases)
    if sample_count % 2 == 0:
        raise ValueError("Trigonometric interpolation currently expects an odd sample count")
    harmonic_count = (sample_count - 1) // 2
    matrix = np.empty((len(evaluation_phases), sample_count), dtype=float)
    for idx, phase in enumerate(evaluation_phases):
        delta = phase - phases
        row = np.ones(sample_count, dtype=float)
        for harmonic in range(1, harmonic_count + 1):
            row += 2.0 * np.cos(harmonic * delta)
        matrix[idx, :] = row / sample_count
    return matrix


def _trigonometric_interpolation_derivative_matrix(
    phases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """Return derivatives of periodic interpolation weights by evaluation phase."""

    sample_count = len(phases)
    if sample_count % 2 == 0:
        raise ValueError("Trigonometric interpolation currently expects an odd sample count")
    harmonic_count = (sample_count - 1) // 2
    matrix = np.zeros((len(evaluation_phases), sample_count), dtype=float)
    for idx, phase in enumerate(evaluation_phases):
        delta = phase - phases
        row = np.zeros(sample_count, dtype=float)
        for harmonic in range(1, harmonic_count + 1):
            row -= 2.0 * harmonic * np.sin(harmonic * delta)
        matrix[idx, :] = row / sample_count
    return matrix


def _stroboscopic_map_and_stms(
    states: np.ndarray,
    *,
    period: float,
    mu: float,
    max_step: float,
) -> tuple[np.ndarray, np.ndarray]:
    sol = integrate_states_and_stms(
        states,
        (0.0, period),
        mu,
        t_eval=np.array([period]),
        max_step=max_step,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    terminal = sol.y[:, -1].reshape(states.shape[0], 42)
    return terminal[:, :6].copy(), terminal[:, 6:].reshape(-1, 6, 6).copy()


def _stroboscopic_invariant_curve_seed_from_orbit(
    mu: float,
    *,
    orbit_state: np.ndarray,
    orbit_period: float,
    orbit_jacobi: float,
    base_family: str,
    base_orbit_amplitude: float,
    mode_component: int,
    mode_amplitude: float,
    samples: int,
    curve_samples: int,
    max_step: float = 0.02,
) -> StroboscopicInvariantCurveSeed:
    """Build a local invariant-curve seed from a corrected periodic orbit."""

    sol = integrate_state_and_stm(orbit_state, (0.0, orbit_period), mu, max_step=max_step)
    if not sol.success:
        raise RuntimeError(sol.message)
    _, monodromy = unpack_augmented(sol.y[:, -1])
    eigenvalues, eigenvectors = np.linalg.eig(monodromy)
    candidates = [
        idx
        for idx, value in enumerate(eigenvalues)
        if abs(abs(value) - 1.0) < 1e-6 and np.angle(value) > 1e-3
    ]
    if not candidates:
        raise RuntimeError("No non-trivial unit-circle monodromy eigenvalue found")
    eigen_index = max(
        candidates,
        key=lambda idx: abs(eigenvectors[mode_component, idx])
        + abs(eigenvectors[mode_component + 3, idx]),
    )
    eigenvalue = eigenvalues[eigen_index]
    eigenvector = eigenvectors[:, eigen_index]
    rotation = float(np.angle(eigenvalue) % (2.0 * np.pi))

    scale = _scale_mode_to_component(eigenvector, mode_component, mode_amplitude)
    phases = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    curve_phases = np.linspace(0.0, 2.0 * np.pi, curve_samples, endpoint=False)
    basis = np.column_stack([scale * np.real(eigenvector), -scale * np.imag(eigenvector)])

    displacements = scale * _mode_cycle(eigenvector, phases)
    predicted_displacements = scale * _mode_cycle(eigenvector, phases + rotation)
    initial_states = orbit_state[None, :] + displacements
    predicted_states = orbit_state[None, :] + predicted_displacements

    mapped_states = np.empty_like(initial_states)
    map_stms = np.empty((samples, 6, 6), dtype=float)
    for idx, state in enumerate(initial_states):
        mapped = integrate_state_and_stm(
            state,
            (0.0, orbit_period),
            mu,
            t_eval=np.array([orbit_period]),
            max_step=max_step,
        )
        if not mapped.success:
            raise RuntimeError(mapped.message)
        mapped_state, mapped_stm = unpack_augmented(mapped.y[:, -1])
        mapped_states[idx, :] = mapped_state
        map_stms[idx, :, :] = mapped_stm

    curve_states = orbit_state[None, :] + scale * _mode_cycle(eigenvector, curve_phases)
    return StroboscopicInvariantCurveSeed(
        mu=float(mu),
        orbit_state=orbit_state,
        orbit_period=float(orbit_period),
        orbit_jacobi=float(orbit_jacobi),
        monodromy_eigenvalue=complex(eigenvalue),
        rotation_angle_rad=rotation,
        vertical_amplitude=float(mode_amplitude),
        phases=phases,
        initial_states=initial_states,
        mapped_states=mapped_states,
        predicted_states=predicted_states,
        residuals=mapped_states - predicted_states,
        map_stms=map_stms,
        mode_basis=basis,
        curve_points=_project_to_mode_plane(curve_states, orbit_state, basis),
        initial_points=_project_to_mode_plane(initial_states, orbit_state, basis),
        mapped_points=_project_to_mode_plane(mapped_states, orbit_state, basis),
        predicted_points=_project_to_mode_plane(predicted_states, orbit_state, basis),
        base_family=base_family,
        base_orbit_amplitude=float(base_orbit_amplitude),
        mode_component=int(mode_component),
        mode_amplitude=float(mode_amplitude),
    )


def stroboscopic_invariant_curve_seed(
    mu: float,
    *,
    point: str = "L1",
    x_amplitude: float = 0.001,
    vertical_amplitude: float = 1e-5,
    samples: int = 7,
    curve_samples: int = 240,
) -> StroboscopicInvariantCurveSeed:
    """Return a CR3BP stroboscopic invariant-curve seed and map residuals.

    The seed is built around a corrected planar Lyapunov orbit. Its unit-circle
    monodromy eigenvector gives a small closed curve that is mapped for one
    Lyapunov period and compared with the curve rotated by the eigenangle. This
    is a verified Newton/DG starting layer, not a fully corrected invariant
    curve.
    """

    guess = planar_lyapunov_linear_guess(mu, point=point, x_amplitude=x_amplitude)
    orbit = correct_planar_lyapunov(mu, guess)
    return _stroboscopic_invariant_curve_seed_from_orbit(
        mu,
        orbit_state=orbit.initial_state,
        orbit_period=orbit.period,
        orbit_jacobi=orbit.jacobi,
        base_family="planar_lyapunov",
        base_orbit_amplitude=x_amplitude,
        mode_component=2,
        mode_amplitude=vertical_amplitude,
        samples=samples,
        curve_samples=curve_samples,
    )


def stroboscopic_vertical_invariant_curve_seed(
    mu: float,
    *,
    point: str = "L1",
    vertical_orbit_amplitude: float = 1e-4,
    planar_mode_amplitude: float = 1e-5,
    samples: int = 11,
    curve_samples: int = 240,
) -> StroboscopicInvariantCurveSeed:
    """Return a planar-mode invariant curve around a corrected vertical orbit."""

    orbit = correct_vertical_symmetric_orbit(
        mu,
        point=point,
        z0=vertical_orbit_amplitude,
    )
    return _stroboscopic_invariant_curve_seed_from_orbit(
        mu,
        orbit_state=orbit.initial_state,
        orbit_period=orbit.period,
        orbit_jacobi=orbit.jacobi,
        base_family="vertical",
        base_orbit_amplitude=vertical_orbit_amplitude,
        mode_component=0,
        mode_amplitude=planar_mode_amplitude,
        samples=samples,
        curve_samples=curve_samples,
        max_step=0.01,
    )


def stroboscopic_spatial_frequency_seed(
    mu: float,
    *,
    target_frequency_ratio: float,
    z_bracket: tuple[float, float],
    point: str = "L2",
    vertical_mode: bool = False,
    mode_component: int,
    mode_amplitude: float,
    samples: int = 11,
    curve_samples: int = 240,
    angle_tolerance: float = 1.0e-8,
    max_refinements: int = 24,
) -> StroboscopicInvariantCurveSeed:
    """Target a spatial periodic boundary and seed a fixed-frequency curve."""

    if target_frequency_ratio <= 2.0:
        raise ValueError("target_frequency_ratio must exceed two")
    lower_z, upper_z = map(float, z_bracket)
    if not 0.0 < lower_z < upper_z:
        raise ValueError("z_bracket must be positive and increasing")
    target_angle = float(2.0 * np.pi / target_frequency_ratio)

    if vertical_mode:
        prefix = np.r_[np.arange(0.005, 0.0201, 0.0025), np.arange(0.025, lower_z, 0.005)]
        amplitudes = np.unique(np.r_[prefix, lower_z, upper_z])
        family = vertical_symmetric_family(
            mu,
            amplitudes,
            point=point,
            max_iterations=40,
            secant_predictor=True,
        )
    else:
        amplitudes = np.unique(np.r_[np.arange(0.005, lower_z, 0.005), lower_z, upper_z])
        family = spatial_symmetric_family(
            mu,
            amplitudes,
            point=point,
            seed_x_amplitude=-0.002 if point.upper() == "L2" else 0.002,
            family_label="halo",
            max_iterations=40,
        )

    def evaluate(orbit) -> float:
        solution = integrate_state_and_stm(
            orbit.initial_state,
            (0.0, orbit.period),
            orbit.mu,
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        _, matrix = unpack_augmented(solution.y[:, -1])
        eigenvalues = np.linalg.eigvals(matrix)
        candidates = [
            abs(np.angle(value))
            for value in eigenvalues
            if value.imag > 1.0e-7
            and abs(abs(value) - 1.0) < 1.0e-4
            and abs(np.angle(value)) > 1.0e-3
        ]
        if not candidates:
            raise RuntimeError("No nontrivial elliptic Floquet multiplier found")
        angle = min(candidates, key=lambda value: abs(value - target_angle))
        return float(angle - target_angle)

    lower = family[-2]
    upper = family[-1]
    lower_error = evaluate(lower)
    upper_error = evaluate(upper)
    if lower_error * upper_error > 0.0:
        raise ValueError(
            "z_bracket does not enclose the requested Floquet frequency ratio: "
            f"angle errors {lower_error:.3e}, {upper_error:.3e}"
        )

    targeted = lower if abs(lower_error) <= abs(upper_error) else upper
    best_error = min(abs(lower_error), abs(upper_error))
    for _ in range(max_refinements):
        trial_z = 0.5 * (lower.fixed_z0 + upper.fixed_z0)
        nearby = lower if abs(trial_z - lower.fixed_z0) <= abs(trial_z - upper.fixed_z0) else upper
        if vertical_mode:
            trial = correct_vertical_symmetric_orbit(
                mu,
                z0=trial_z,
                point=point,
                seed_orbit=nearby,
                max_iterations=40,
            )
        else:
            trial = correct_spatial_symmetric_orbit(
                mu,
                z0=trial_z,
                point=point,
                seed_x_amplitude=-0.002 if point.upper() == "L2" else 0.002,
                seed_orbit=nearby,
                family_label="halo",
                max_iterations=40,
            )
        trial_error = evaluate(trial)
        if abs(trial_error) < best_error:
            targeted = trial
            best_error = abs(trial_error)
        if abs(trial_error) <= angle_tolerance:
            targeted = trial
            break
        if lower_error * trial_error <= 0.0:
            upper, upper_error = trial, trial_error
        else:
            lower, lower_error = trial, trial_error
    else:
        raise RuntimeError(
            "Spatial Floquet frequency targeting did not converge; "
            f"best angle error={best_error:.3e}"
        )

    return _stroboscopic_invariant_curve_seed_from_orbit(
        mu,
        orbit_state=targeted.initial_state,
        orbit_period=targeted.period,
        orbit_jacobi=targeted.jacobi,
        base_family="vertical" if vertical_mode else "halo",
        base_orbit_amplitude=targeted.fixed_z0,
        mode_component=mode_component,
        mode_amplitude=mode_amplitude,
        samples=samples,
        curve_samples=curve_samples,
        max_step=0.01,
    )


def stroboscopic_spatial_jacobi_seed(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    family_label: str,
    mode_component: int,
    mode_amplitude: float,
    samples: int = 11,
    curve_samples: int = 240,
) -> StroboscopicInvariantCurveSeed:
    """Target an L1 periodic boundary at fixed Jacobi constant and seed a curve."""

    label = family_label.lower()
    if label not in {"halo", "vertical"}:
        raise ValueError("family_label must be 'halo' or 'vertical'")
    vertical_mode = label == "vertical"
    z_amplitudes = (
        np.r_[np.arange(0.005, 0.0201, 0.0025), np.arange(0.025, 0.1051, 0.005)]
        if vertical_mode
        else np.arange(0.005, 0.0601, 0.005)
    )
    targeted = target_spatial_orbit_jacobi(
        mu,
        target_jacobi=target_jacobi,
        z_amplitudes=z_amplitudes,
        point="L1",
        family_label=label,
        vertical_mode=vertical_mode,
        seed_x_amplitude=0.002,
    )
    orbit = targeted.orbit
    return _stroboscopic_invariant_curve_seed_from_orbit(
        mu,
        orbit_state=orbit.initial_state,
        orbit_period=orbit.period,
        orbit_jacobi=orbit.jacobi,
        base_family=label,
        base_orbit_amplitude=orbit.fixed_z0,
        mode_component=mode_component,
        mode_amplitude=mode_amplitude,
        samples=samples,
        curve_samples=curve_samples,
        max_step=0.01,
    )


def stroboscopic_dro_invariant_curve_seed(
    mu: float,
    *,
    x0: float,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    vertical_amplitude: float = 1e-4,
    samples: int = 11,
    curve_samples: int = 240,
) -> StroboscopicInvariantCurveSeed:
    """Return a vertical-mode invariant curve around a corrected planar DRO."""

    orbit = correct_planar_dro(
        mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
    )
    return _stroboscopic_invariant_curve_seed_from_orbit(
        mu,
        orbit_state=orbit.initial_state,
        orbit_period=orbit.period,
        orbit_jacobi=orbit.jacobi,
        base_family="planar_dro",
        base_orbit_amplitude=abs((1.0 - mu) - x0),
        mode_component=2,
        mode_amplitude=vertical_amplitude,
        samples=samples,
        curve_samples=curve_samples,
        max_step=0.01,
    )


def stroboscopic_fixed_target_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    iterations: int = 3,
    max_step: float = 0.02,
) -> StroboscopicShootingCorrection:
    """Shoot each seed point so one-period propagation hits its rotated target.

    This uses the propagated STM at each point to correct the initial states
    toward the fixed linear-rotation targets stored in ``seed``. It validates
    the local shooting machinery needed for full invariant-curve Newton
    correction, but it does not yet update the curve targets or rotation angle.
    """

    states = seed.initial_states.copy()
    residual_history: list[np.ndarray] = []
    correction_history: list[np.ndarray] = []

    for _ in range(iterations):
        residuals = np.empty_like(states)
        corrections = np.empty(states.shape[0], dtype=float)
        for idx, state in enumerate(states):
            sol = integrate_state_and_stm(
                state,
                (0.0, seed.orbit_period),
                seed.mu,
                t_eval=np.array([seed.orbit_period]),
                max_step=max_step,
            )
            if not sol.success:
                raise RuntimeError(sol.message)
            mapped_state, phi = unpack_augmented(sol.y[:, -1])
            residual = mapped_state - seed.predicted_states[idx]
            delta = np.linalg.solve(phi, -residual)
            residuals[idx, :] = residual
            corrections[idx] = float(np.linalg.norm(delta))
            states[idx, :] += delta
        residual_history.append(np.linalg.norm(residuals, axis=1))
        correction_history.append(corrections)

    final_mapped = np.empty_like(states)
    final_residuals = np.empty(states.shape[0], dtype=float)
    for idx, state in enumerate(states):
        sol = integrate_state_and_stm(
            state,
            (0.0, seed.orbit_period),
            seed.mu,
            t_eval=np.array([seed.orbit_period]),
            max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(sol.message)
        mapped_state, _ = unpack_augmented(sol.y[:, -1])
        final_mapped[idx, :] = mapped_state
        final_residuals[idx] = float(np.linalg.norm(mapped_state - seed.predicted_states[idx]))
    residual_history.append(final_residuals)

    return StroboscopicShootingCorrection(
        seed=seed,
        corrected_initial_states=states,
        corrected_mapped_states=final_mapped,
        target_states=seed.predicted_states,
        corrected_initial_points=_project_to_mode_plane(states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(final_mapped, seed.orbit_state, seed.mode_basis),
        residual_history=np.array(residual_history, dtype=float),
        correction_norm_history=np.array(correction_history, dtype=float),
    )


def stroboscopic_curve_newton_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    max_iterations: int = 3,
    tolerance: float = 1e-10,
    max_step: float = 0.02,
    rcond: float = 1e-12,
) -> StroboscopicCurveNewtonCorrection:
    """Correct all discrete curve points with a fixed rotation-angle Newton step.

    The residual is ``F(x_i) - I_rho(x)_i``, where ``F`` is one-period CR3BP
    propagation and ``I_rho`` is periodic trigonometric interpolation of the
    current curve at ``theta_i + rho``. This is a curve-updating Newton layer
    with fixed mapping time and fixed rotation angle; full continuation must
    still add phase/energy constraints and solve for the continuation
    parameters.
    """

    states = seed.initial_states.copy()
    interpolation = _trigonometric_interpolation_matrix(
        seed.phases,
        seed.phases + seed.rotation_angle_rad,
    )
    residual_history: list[np.ndarray] = []
    correction_history: list[np.ndarray] = []
    condition_history: list[float] = []

    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_norms: np.ndarray | None = None
    best_max_residual = np.inf
    for _ in range(max_iterations):
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=seed.orbit_period,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        residual_history.append(residual_norms)
        if residual_norms.max() < best_max_residual:
            best_max_residual = float(residual_norms.max())
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_norms = residual_norms.copy()
        if residual_norms.max() < tolerance:
            break

        sample_count = states.shape[0]
        jacobian = np.zeros((6 * sample_count, 6 * sample_count), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        condition_history.append(float(np.linalg.cond(jacobian)))
        delta = np.linalg.lstsq(jacobian, -residuals.reshape(-1), rcond=rcond)[0].reshape(sample_count, 6)
        correction_history.append(np.linalg.norm(delta, axis=1))
        states = states + delta

    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=seed.orbit_period,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    final_norms = np.linalg.norm(mapped - targets, axis=1)
    residual_history.append(final_norms)
    if final_norms.max() < best_max_residual:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_norms = final_norms.copy()
    if best_norms is not None and not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)

    return StroboscopicCurveNewtonCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=interpolation,
        residual_history=np.array(residual_history, dtype=float),
        correction_norm_history=np.array(correction_history, dtype=float),
        jacobian_condition_history=np.array(condition_history, dtype=float),
    )


def stroboscopic_curve_free_rotation_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_amplitude: float | None = None,
    amplitude_component: int | None = None,
    initial_states: np.ndarray | None = None,
    initial_rotation_angle_rad: float | None = None,
    phase_reference_states: np.ndarray | None = None,
    max_iterations: int = 6,
    tolerance: float = 1e-10,
    constraint_tolerance: float = 1e-10,
    max_step: float = 0.02,
    max_state_step: float | None = None,
    max_rotation_step: float = 0.15,
    rcond: float = 1e-11,
) -> FreeRotationCurveCorrection:
    """Correct a curve while solving its rotation angle at fixed mapping time.

    A phase condition removes parameterization drift. A phase-invariant RMS
    component-amplitude constraint selects one member of the fixed-mapping-time
    family. The map Jacobian uses propagated STM blocks and the analytic
    derivative of trigonometric interpolation with respect to rotation angle.
    """

    states = seed.initial_states.copy() if initial_states is None else np.array(initial_states, dtype=float, copy=True)
    if states.shape != seed.initial_states.shape:
        raise ValueError("initial_states must match the seed curve shape")
    reference = states.copy() if phase_reference_states is None else np.array(
        phase_reference_states,
        dtype=float,
        copy=True,
    )
    if reference.shape != states.shape:
        raise ValueError("phase_reference_states must match the seed curve shape")

    component = seed.mode_component if amplitude_component is None else int(amplitude_component)
    if not 0 <= component < 6:
        raise ValueError("amplitude_component must be a state component index")
    target = seed.mode_amplitude if target_amplitude is None else float(target_amplitude)
    if target <= 0.0:
        raise ValueError("target_amplitude must be positive")
    rotation = (
        seed.rotation_angle_rad
        if initial_rotation_angle_rad is None
        else float(initial_rotation_angle_rad)
    )

    tangent = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 1e-14:
        raise RuntimeError("Phase reference has a degenerate curve tangent")
    tangent /= tangent_norm

    residual_history: list[np.ndarray] = []
    amplitude_history: list[float] = []
    phase_history: list[float] = []
    correction_history: list[np.ndarray] = []
    rotation_history: list[float] = []
    condition_history: list[float] = []

    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_interpolation = np.empty((states.shape[0], states.shape[0]), dtype=float)
    best_rotation = rotation
    best_norms: np.ndarray | None = None
    best_amplitude_residual = np.inf
    best_phase_residual = np.inf

    def constraints(values: np.ndarray) -> tuple[float, np.ndarray, float]:
        displacement = values[:, component] - seed.orbit_state[component]
        amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        amplitude_gradient = np.zeros_like(values)
        if amplitude > 1e-15:
            amplitude_gradient[:, component] = 2.0 * displacement / (values.shape[0] * amplitude)
        phase_residual = float(np.sum((values - reference) * tangent))
        return amplitude - target, amplitude_gradient, phase_residual

    for _ in range(max_iterations):
        interpolation = _trigonometric_interpolation_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=seed.orbit_period,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        amplitude_residual, amplitude_gradient, phase_residual = constraints(states)
        metric = max(
            float(residual_norms.max()),
            abs(amplitude_residual),
            abs(phase_residual),
        )
        residual_history.append(residual_norms)
        amplitude_history.append(amplitude_residual)
        phase_history.append(phase_residual)
        rotation_history.append(rotation)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_interpolation = interpolation.copy()
            best_rotation = rotation
            best_norms = residual_norms.copy()
            best_amplitude_residual = amplitude_residual
            best_phase_residual = phase_residual
        if residual_norms.max() < tolerance and abs(amplitude_residual) < constraint_tolerance and abs(
            phase_residual
        ) < constraint_tolerance:
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        jacobian[:state_size, -1] = -(interpolation_derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = amplitude_gradient.reshape(-1)
        jacobian[state_size + 1, :state_size] = tangent.reshape(-1)
        condition_history.append(float(np.linalg.cond(jacobian)))

        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                np.array([amplitude_residual, phase_residual]),
            ]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        rotation_delta = float(delta[-1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        state_limit = max(0.35 * target, 1e-5) if max_state_step is None else float(max_state_step)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(rotation_delta) > max_rotation_step:
            scale = min(scale, max_rotation_step / abs(rotation_delta))
        state_delta *= scale
        rotation_delta *= scale
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta
        rotation = float((rotation + rotation_delta) % (2.0 * np.pi))

    interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=seed.orbit_period,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    residual_norms = np.linalg.norm(mapped - targets, axis=1)
    amplitude_residual, _, phase_residual = constraints(states)
    metric = max(float(residual_norms.max()), abs(amplitude_residual), abs(phase_residual))
    residual_history.append(residual_norms)
    amplitude_history.append(amplitude_residual)
    phase_history.append(phase_residual)
    rotation_history.append(rotation)
    if metric < best_metric:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_interpolation = interpolation.copy()
        best_rotation = rotation
        best_norms = residual_norms.copy()
        best_amplitude_residual = amplitude_residual
        best_phase_residual = phase_residual

    if best_norms is None:
        raise RuntimeError("Free-rotation correction did not evaluate a candidate")
    if not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)
        amplitude_history.append(best_amplitude_residual)
        phase_history.append(best_phase_residual)
        rotation_history.append(best_rotation)

    return FreeRotationCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=best_interpolation,
        rotation_angle_rad=float(best_rotation),
        target_amplitude=target,
        amplitude_component=component,
        residual_history=np.array(residual_history, dtype=float),
        amplitude_residual_history=np.array(amplitude_history, dtype=float),
        phase_residual_history=np.array(phase_history, dtype=float),
        correction_norm_history=np.array(correction_history, dtype=float),
        rotation_history=np.array(rotation_history, dtype=float),
        jacobian_condition_history=np.array(condition_history, dtype=float),
    )


def stroboscopic_curve_fixed_rotation_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_rotation_angle_rad: float,
    initial_states: np.ndarray,
    phase_reference_states: np.ndarray | None = None,
    max_iterations: int = 16,
    tolerance: float = 1e-8,
    phase_tolerance: float = 1e-10,
    max_step: float = 0.01,
    max_state_step: float = 2e-3,
    rcond: float = 1e-11,
) -> FixedRotationCurveCorrection:
    """Correct a fixed-time curve while holding the rotation angle fixed."""

    states = np.array(initial_states, dtype=float, copy=True)
    if states.shape != seed.initial_states.shape:
        raise ValueError("initial_states must match the seed curve shape")
    reference = states.copy() if phase_reference_states is None else np.array(
        phase_reference_states,
        dtype=float,
        copy=True,
    )
    if reference.shape != states.shape:
        raise ValueError("phase_reference_states must match the seed curve shape")
    rotation = float(target_rotation_angle_rad % (2.0 * np.pi))
    interpolation = _trigonometric_interpolation_matrix(
        seed.phases,
        seed.phases + rotation,
    )
    phase_direction = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    phase_direction /= np.linalg.norm(phase_direction)

    residual_history: list[np.ndarray] = []
    phase_history: list[float] = []
    correction_history: list[np.ndarray] = []
    condition_history: list[float] = []
    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_norms: np.ndarray | None = None
    best_phase_residual = np.inf

    for _ in range(max_iterations):
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=seed.orbit_period,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        phase_residual = float(np.sum((states - reference) * phase_direction))
        metric = max(float(residual_norms.max()), abs(phase_residual))
        residual_history.append(residual_norms)
        phase_history.append(phase_residual)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_norms = residual_norms.copy()
            best_phase_residual = phase_residual
        if residual_norms.max() < tolerance and abs(phase_residual) < phase_tolerance:
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        jacobian = np.zeros((state_size + 1, state_size), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        jacobian[state_size, :] = phase_direction.reshape(-1)
        condition_history.append(float(np.linalg.cond(jacobian)))
        right_hand_side = -np.r_[residuals.reshape(-1), phase_residual]
        state_delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0].reshape(
            sample_count,
            6,
        )
        block_norms = np.linalg.norm(state_delta, axis=1)
        if block_norms.max() > max_state_step:
            state_delta *= max_state_step / float(block_norms.max())
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta

    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=seed.orbit_period,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    residual_norms = np.linalg.norm(mapped - targets, axis=1)
    phase_residual = float(np.sum((states - reference) * phase_direction))
    residual_history.append(residual_norms)
    phase_history.append(phase_residual)
    if max(float(residual_norms.max()), abs(phase_residual)) < best_metric:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_norms = residual_norms.copy()
        best_phase_residual = phase_residual
    if best_norms is None:
        raise RuntimeError("Fixed-rotation correction did not evaluate a candidate")
    if not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)
        phase_history.append(best_phase_residual)

    component = seed.mode_component
    displacement = best_states[:, component] - seed.orbit_state[component]
    amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return FixedRotationCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=interpolation,
        rotation_angle_rad=rotation,
        target_amplitude=amplitude,
        amplitude_component=component,
        residual_history=np.asarray(residual_history),
        phase_residual_history=np.asarray(phase_history),
        correction_norm_history=np.asarray(correction_history),
        jacobian_condition_history=np.asarray(condition_history),
    )


def stroboscopic_curve_free_mapping_time_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_rotation_angle_rad: float | None = None,
    target_amplitude: float | None = None,
    amplitude_component: int | None = None,
    initial_states: np.ndarray | None = None,
    initial_mapping_time: float | None = None,
    phase_reference_states: np.ndarray | None = None,
    max_iterations: int = 8,
    tolerance: float = 1e-10,
    constraint_tolerance: float = 1e-10,
    max_step: float = 0.02,
    max_state_step: float | None = None,
    max_mapping_time_step: float = 0.15,
    rcond: float = 1e-11,
) -> FreeMappingTimeCurveCorrection:
    """Correct a curve at fixed rotation angle while solving mapping time."""

    states = seed.initial_states.copy() if initial_states is None else np.array(initial_states, dtype=float, copy=True)
    if states.shape != seed.initial_states.shape:
        raise ValueError("initial_states must match the seed curve shape")
    reference = states.copy() if phase_reference_states is None else np.array(
        phase_reference_states,
        dtype=float,
        copy=True,
    )
    if reference.shape != states.shape:
        raise ValueError("phase_reference_states must match the seed curve shape")

    component = seed.mode_component if amplitude_component is None else int(amplitude_component)
    if not 0 <= component < 6:
        raise ValueError("amplitude_component must be a state component index")
    target = seed.mode_amplitude if target_amplitude is None else float(target_amplitude)
    if target <= 0.0:
        raise ValueError("target_amplitude must be positive")
    rotation = seed.rotation_angle_rad if target_rotation_angle_rad is None else float(target_rotation_angle_rad)
    rotation %= 2.0 * np.pi
    mapping_time = seed.orbit_period if initial_mapping_time is None else float(initial_mapping_time)
    if mapping_time <= 0.0:
        raise ValueError("initial_mapping_time must be positive")

    interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
    tangent = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 1e-14:
        raise RuntimeError("Phase reference has a degenerate curve tangent")
    tangent /= tangent_norm

    residual_history: list[np.ndarray] = []
    amplitude_history: list[float] = []
    phase_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    condition_history: list[float] = []

    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_mapping_time = mapping_time
    best_norms: np.ndarray | None = None
    best_amplitude_residual = np.inf
    best_phase_residual = np.inf

    def constraints(values: np.ndarray) -> tuple[float, np.ndarray, float]:
        displacement = values[:, component] - seed.orbit_state[component]
        amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        amplitude_gradient = np.zeros_like(values)
        if amplitude > 1e-15:
            amplitude_gradient[:, component] = 2.0 * displacement / (values.shape[0] * amplitude)
        phase_residual = float(np.sum((values - reference) * tangent))
        return amplitude - target, amplitude_gradient, phase_residual

    for _ in range(max_iterations):
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        amplitude_residual, amplitude_gradient, phase_residual = constraints(states)
        metric = max(float(residual_norms.max()), abs(amplitude_residual), abs(phase_residual))
        residual_history.append(residual_norms)
        amplitude_history.append(amplitude_residual)
        phase_history.append(phase_residual)
        mapping_time_history.append(mapping_time)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_mapping_time = mapping_time
            best_norms = residual_norms.copy()
            best_amplitude_residual = amplitude_residual
            best_phase_residual = phase_residual
        if residual_norms.max() < tolerance and abs(amplitude_residual) < constraint_tolerance and abs(
            phase_residual
        ) < constraint_tolerance:
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, -1] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[state_size, :state_size] = amplitude_gradient.reshape(-1)
        jacobian[state_size + 1, :state_size] = tangent.reshape(-1)
        condition_history.append(float(np.linalg.cond(jacobian)))

        right_hand_side = -np.concatenate(
            [residuals.reshape(-1), np.array([amplitude_residual, phase_residual])]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[-1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        state_limit = max(0.35 * target, 1e-5) if max_state_step is None else float(max_state_step)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        state_delta *= scale
        mapping_time_delta *= scale
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta
        mapping_time += mapping_time_delta
        if mapping_time <= 0.0:
            raise RuntimeError("Free-mapping-time correction produced a non-positive mapping time")

    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    residual_norms = np.linalg.norm(mapped - targets, axis=1)
    amplitude_residual, _, phase_residual = constraints(states)
    metric = max(float(residual_norms.max()), abs(amplitude_residual), abs(phase_residual))
    residual_history.append(residual_norms)
    amplitude_history.append(amplitude_residual)
    phase_history.append(phase_residual)
    mapping_time_history.append(mapping_time)
    if metric < best_metric:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_mapping_time = mapping_time
        best_norms = residual_norms.copy()
        best_amplitude_residual = amplitude_residual
        best_phase_residual = phase_residual

    if best_norms is None:
        raise RuntimeError("Free-mapping-time correction did not evaluate a candidate")
    if not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)
        amplitude_history.append(best_amplitude_residual)
        phase_history.append(best_phase_residual)
        mapping_time_history.append(best_mapping_time)

    return FreeMappingTimeCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=interpolation,
        rotation_angle_rad=rotation,
        mapping_time=float(best_mapping_time),
        target_amplitude=target,
        amplitude_component=component,
        residual_history=np.array(residual_history, dtype=float),
        amplitude_residual_history=np.array(amplitude_history, dtype=float),
        phase_residual_history=np.array(phase_history, dtype=float),
        correction_norm_history=np.array(correction_history, dtype=float),
        mapping_time_history=np.array(mapping_time_history, dtype=float),
        jacobian_condition_history=np.array(condition_history, dtype=float),
    )


def _jacobi_gradient(states: np.ndarray, mu: float) -> np.ndarray:
    """Return row-wise gradients of the CR3BP Jacobi constant."""

    values = np.asarray(states, dtype=float)
    gradients = np.empty_like(values)
    for idx, state in enumerate(values):
        gradients[idx, :3] = 2.0 * potential_gradient(state[:3], mu)
        gradients[idx, 3:] = -2.0 * state[3:]
    return gradients


def stroboscopic_curve_free_energy_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_jacobi: float | None = None,
    target_amplitude: float | None = None,
    amplitude_component: int | None = None,
    initial_states: np.ndarray | None = None,
    initial_mapping_time: float | None = None,
    initial_rotation_angle_rad: float | None = None,
    phase_reference_states: np.ndarray | None = None,
    max_iterations: int = 16,
    tolerance: float = 1e-10,
    constraint_tolerance: float = 1e-10,
    max_step: float = 0.01,
    max_state_step: float | None = None,
    max_mapping_time_step: float = 0.12,
    max_rotation_step: float = 0.12,
    rcond: float = 1e-11,
) -> FreeEnergyCurveCorrection:
    """Correct an invariant curve at fixed mean Jacobi constant.

    The curve states, stroboscopic mapping time, and rotation angle are solved
    simultaneously. The Jacobian follows McCarthy's single-shooting equations:
    STM blocks for the map, analytic time and rotation columns, and the average
    Jacobi gradient. An RMS component-amplitude constraint selects a local
    family member, while a curve-tangent phase condition removes parameter drift.
    """

    states = seed.initial_states.copy() if initial_states is None else np.array(initial_states, dtype=float, copy=True)
    if states.shape != seed.initial_states.shape:
        raise ValueError("initial_states must match the seed curve shape")
    reference = states.copy() if phase_reference_states is None else np.array(
        phase_reference_states,
        dtype=float,
        copy=True,
    )
    if reference.shape != states.shape:
        raise ValueError("phase_reference_states must match the seed curve shape")

    component = seed.mode_component if amplitude_component is None else int(amplitude_component)
    if not 0 <= component < 6:
        raise ValueError("amplitude_component must be a state component index")
    target_amp = seed.mode_amplitude if target_amplitude is None else float(target_amplitude)
    if target_amp <= 0.0:
        raise ValueError("target_amplitude must be positive")
    target_energy = seed.orbit_jacobi if target_jacobi is None else float(target_jacobi)
    mapping_time = seed.orbit_period if initial_mapping_time is None else float(initial_mapping_time)
    if mapping_time <= 0.0:
        raise ValueError("initial_mapping_time must be positive")
    rotation = (
        seed.rotation_angle_rad
        if initial_rotation_angle_rad is None
        else float(initial_rotation_angle_rad)
    ) % (2.0 * np.pi)

    tangent = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 1e-14:
        raise RuntimeError("Phase reference has a degenerate curve tangent")
    tangent /= tangent_norm

    residual_history: list[np.ndarray] = []
    energy_history: list[float] = []
    amplitude_history: list[float] = []
    phase_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    rotation_history: list[float] = []
    condition_history: list[float] = []

    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_interpolation = np.empty((states.shape[0], states.shape[0]), dtype=float)
    best_mapping_time = mapping_time
    best_rotation = rotation
    best_norms: np.ndarray | None = None
    best_energy_residual = np.inf
    best_amplitude_residual = np.inf
    best_phase_residual = np.inf

    def constraints(values: np.ndarray) -> tuple[float, np.ndarray, float, np.ndarray, float]:
        energy_values = jacobi_constant(values, seed.mu)
        energy_residual = float(np.mean(energy_values) - target_energy)
        energy_gradient = _jacobi_gradient(values, seed.mu) / values.shape[0]
        displacement = values[:, component] - seed.orbit_state[component]
        amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        amplitude_gradient = np.zeros_like(values)
        if amplitude > 1e-15:
            amplitude_gradient[:, component] = 2.0 * displacement / (values.shape[0] * amplitude)
        phase_residual = float(np.sum((values - reference) * tangent))
        return energy_residual, energy_gradient, amplitude - target_amp, amplitude_gradient, phase_residual

    for _ in range(max_iterations):
        interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        (
            energy_residual,
            energy_gradient,
            amplitude_residual,
            amplitude_gradient,
            phase_residual,
        ) = constraints(states)
        metric = max(
            float(residual_norms.max()),
            abs(energy_residual),
            abs(amplitude_residual),
            abs(phase_residual),
        )
        residual_history.append(residual_norms)
        energy_history.append(energy_residual)
        amplitude_history.append(amplitude_residual)
        phase_history.append(phase_residual)
        mapping_time_history.append(mapping_time)
        rotation_history.append(rotation)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_interpolation = interpolation.copy()
            best_mapping_time = mapping_time
            best_rotation = rotation
            best_norms = residual_norms.copy()
            best_energy_residual = energy_residual
            best_amplitude_residual = amplitude_residual
            best_phase_residual = phase_residual
        if (
            residual_norms.max() < tolerance
            and abs(energy_residual) < constraint_tolerance
            and abs(amplitude_residual) < constraint_tolerance
            and abs(phase_residual) < constraint_tolerance
        ):
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        jacobian = np.zeros((state_size + 3, state_size + 2), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[:state_size, state_size + 1] = -(interpolation_derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = energy_gradient.reshape(-1)
        jacobian[state_size + 1, :state_size] = amplitude_gradient.reshape(-1)
        jacobian[state_size + 2, :state_size] = tangent.reshape(-1)
        condition_history.append(float(np.linalg.cond(jacobian)))

        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                np.array([energy_residual, amplitude_residual, phase_residual]),
            ]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[state_size])
        rotation_delta = float(delta[state_size + 1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        state_limit = max(0.35 * target_amp, 1e-5) if max_state_step is None else float(max_state_step)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        if abs(rotation_delta) > max_rotation_step:
            scale = min(scale, max_rotation_step / abs(rotation_delta))
        state_delta *= scale
        mapping_time_delta *= scale
        rotation_delta *= scale
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta
        mapping_time += mapping_time_delta
        rotation = float((rotation + rotation_delta) % (2.0 * np.pi))
        if mapping_time <= 0.0:
            raise RuntimeError("Free-energy correction produced a non-positive mapping time")

    interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    residual_norms = np.linalg.norm(mapped - targets, axis=1)
    (
        energy_residual,
        _,
        amplitude_residual,
        _,
        phase_residual,
    ) = constraints(states)
    metric = max(
        float(residual_norms.max()),
        abs(energy_residual),
        abs(amplitude_residual),
        abs(phase_residual),
    )
    residual_history.append(residual_norms)
    energy_history.append(energy_residual)
    amplitude_history.append(amplitude_residual)
    phase_history.append(phase_residual)
    mapping_time_history.append(mapping_time)
    rotation_history.append(rotation)
    if metric < best_metric:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_interpolation = interpolation.copy()
        best_mapping_time = mapping_time
        best_rotation = rotation
        best_norms = residual_norms.copy()
        best_energy_residual = energy_residual
        best_amplitude_residual = amplitude_residual
        best_phase_residual = phase_residual

    if best_norms is None:
        raise RuntimeError("Free-energy correction did not evaluate a candidate")
    if not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)
        energy_history.append(best_energy_residual)
        amplitude_history.append(best_amplitude_residual)
        phase_history.append(best_phase_residual)
        mapping_time_history.append(best_mapping_time)
        rotation_history.append(best_rotation)

    return FreeEnergyCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=best_interpolation,
        rotation_angle_rad=float(best_rotation),
        mapping_time=float(best_mapping_time),
        target_jacobi=target_energy,
        target_amplitude=target_amp,
        amplitude_component=component,
        residual_history=np.array(residual_history, dtype=float),
        energy_residual_history=np.array(energy_history, dtype=float),
        amplitude_residual_history=np.array(amplitude_history, dtype=float),
        phase_residual_history=np.array(phase_history, dtype=float),
        correction_norm_history=np.array(correction_history, dtype=float),
        mapping_time_history=np.array(mapping_time_history, dtype=float),
        rotation_history=np.array(rotation_history, dtype=float),
        jacobian_condition_history=np.array(condition_history, dtype=float),
    )


def stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_jacobi: float,
    initial_states: np.ndarray | None = None,
    initial_mapping_time: float | None = None,
    initial_rotation_angle_rad: float | None = None,
    phase_reference_states: np.ndarray | None = None,
    max_iterations: int = 16,
    tolerance: float = 1e-10,
    jacobi_tolerance: float = 1e-10,
    phase_tolerance: float = 1e-10,
    max_step: float = 0.01,
    max_state_step: float = 2e-3,
    max_mapping_time_step: float = 0.05,
    max_rotation_step: float = 0.01,
    rcond: float = 1e-11,
    state_variable_scale: float = 1.0,
    mapping_time_variable_scale: float = 1.0,
    rotation_variable_scale: float = 1.0,
    map_residual_scale: float = 1.0,
    jacobi_residual_scale: float = 1.0,
    phase_residual_scale: float = 1.0,
    phase_condition: str = "curve_tangent",
) -> FixedJacobiFreeTimeRotationCurveCorrection:
    """Correct a stroboscopic curve at fixed mean Jacobi with free time and rho.

    This is the minimal Route B square system. The unknown vector is the full
    curve state block plus mapping time and rotation angle. The residual blocks
    are map invariance, curve-average Jacobi, and one curve-tangent phase
    condition. Amplitude is intentionally not a hard equation.
    """

    states = seed.initial_states.copy() if initial_states is None else np.array(initial_states, dtype=float, copy=True)
    if states.shape != seed.initial_states.shape:
        raise ValueError("initial_states must match the seed curve shape")
    reference = states.copy() if phase_reference_states is None else np.array(
        phase_reference_states,
        dtype=float,
        copy=True,
    )
    if reference.shape != states.shape:
        raise ValueError("phase_reference_states must match the seed curve shape")

    target_energy = float(target_jacobi)
    mapping_time = seed.orbit_period if initial_mapping_time is None else float(initial_mapping_time)
    if mapping_time <= 0.0:
        raise ValueError("initial_mapping_time must be positive")
    rotation = (
        seed.rotation_angle_rad
        if initial_rotation_angle_rad is None
        else float(initial_rotation_angle_rad)
    ) % (2.0 * np.pi)

    scales = (
        state_variable_scale,
        mapping_time_variable_scale,
        rotation_variable_scale,
        map_residual_scale,
        jacobi_residual_scale,
        phase_residual_scale,
    )
    if any(scale <= 0.0 or not np.isfinite(scale) for scale in scales):
        raise ValueError("Route B variable and residual scales must be positive finite values")

    if phase_condition == "curve_tangent":
        phase_directions = [np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)]
    elif phase_condition == "reference_section_z":
        section = np.zeros_like(reference)
        section[0, 2] = 1.0
        phase_directions = [section]
    elif phase_condition == "two_orthogonality":
        longitudinal, latitudinal = _curve_phase_directions(
            seed,
            reference,
            mapping_time=mapping_time,
            rotation_angle_rad=rotation,
        )
        phase_directions = [longitudinal, latitudinal]
    else:
        raise ValueError(
            "phase_condition must be 'curve_tangent', 'reference_section_z', or 'two_orthogonality'"
        )
    normalized_phase_directions = []
    for direction in phase_directions:
        direction_norm = float(np.linalg.norm(direction))
        if direction_norm <= 1e-14:
            raise RuntimeError("Phase reference has a degenerate phase direction")
        normalized_phase_directions.append(direction / direction_norm)
    phase_directions = normalized_phase_directions

    residual_history: list[np.ndarray] = []
    energy_history: list[float] = []
    phase_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    rotation_history: list[float] = []
    condition_history: list[float] = []
    min_singular_history: list[float] = []
    max_singular_history: list[float] = []

    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_interpolation = np.empty((states.shape[0], states.shape[0]), dtype=float)
    best_mapping_time = mapping_time
    best_rotation = rotation
    best_norms: np.ndarray | None = None
    best_energy_residual = np.inf
    best_phase_residual = np.inf

    def constraints(values: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        energy_values = jacobi_constant(values, seed.mu)
        energy_residual = float(np.mean(energy_values) - target_energy)
        energy_gradient = _jacobi_gradient(values, seed.mu) / values.shape[0]
        phase_residuals = np.asarray(
            [float(np.sum((values - reference) * direction)) for direction in phase_directions],
            dtype=float,
        )
        return energy_residual, energy_gradient, phase_residuals

    for _ in range(max_iterations):
        interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        energy_residual, energy_gradient, phase_residuals = constraints(states)
        phase_residual_norm = float(np.linalg.norm(phase_residuals, ord=np.inf))
        metric = max(float(residual_norms.max()), abs(energy_residual), phase_residual_norm)
        residual_history.append(residual_norms)
        energy_history.append(energy_residual)
        phase_history.append(phase_residual_norm)
        mapping_time_history.append(mapping_time)
        rotation_history.append(rotation)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_interpolation = interpolation.copy()
            best_mapping_time = mapping_time
            best_rotation = rotation
            best_norms = residual_norms.copy()
            best_energy_residual = energy_residual
            best_phase_residual = phase_residual_norm
        if (
            residual_norms.max() < tolerance
            and abs(energy_residual) < jacobi_tolerance
            and phase_residual_norm < phase_tolerance
        ):
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        phase_count = len(phase_directions)
        jacobian = np.zeros((state_size + 1 + phase_count, state_size + 2), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[:state_size, state_size + 1] = -(interpolation_derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = energy_gradient.reshape(-1)
        for phase_idx, direction in enumerate(phase_directions):
            jacobian[state_size + 1 + phase_idx, :state_size] = direction.reshape(-1)

        right_hand_side = -np.concatenate(
            [residuals.reshape(-1), np.array([energy_residual]), phase_residuals]
        )
        row_scales = np.concatenate(
            [
                np.full(state_size, map_residual_scale, dtype=float),
                np.array([jacobi_residual_scale], dtype=float),
                np.full(phase_count, phase_residual_scale, dtype=float),
            ]
        )
        column_scales = np.concatenate(
            [
                np.full(state_size, state_variable_scale, dtype=float),
                np.array([mapping_time_variable_scale, rotation_variable_scale], dtype=float),
            ]
        )
        scaled_jacobian = row_scales[:, None] * jacobian * column_scales[None, :]
        scaled_right_hand_side = row_scales * right_hand_side
        scaled_delta, _, _, singular_values = np.linalg.lstsq(
            scaled_jacobian,
            scaled_right_hand_side,
            rcond=rcond,
        )
        delta = column_scales * scaled_delta
        condition_history.append(
            float(singular_values[0] / singular_values[-1])
            if singular_values.size and singular_values[-1] > 0.0
            else np.inf
        )
        max_singular_history.append(float(singular_values[0]) if singular_values.size else np.nan)
        min_singular_history.append(float(singular_values[-1]) if singular_values.size else np.nan)
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[state_size])
        rotation_delta = float(delta[state_size + 1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > max_state_step:
            scale = min(scale, max_state_step / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        if abs(rotation_delta) > max_rotation_step:
            scale = min(scale, max_rotation_step / abs(rotation_delta))
        state_delta *= scale
        mapping_time_delta *= scale
        rotation_delta *= scale
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta
        mapping_time += mapping_time_delta
        rotation = float((rotation + rotation_delta) % (2.0 * np.pi))
        if mapping_time <= 0.0:
            raise RuntimeError("Fixed-Jacobi free-time correction produced a non-positive mapping time")

    interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=seed.mu,
        max_step=max_step,
    )
    targets = interpolation @ states
    residual_norms = np.linalg.norm(mapped - targets, axis=1)
    energy_residual, _, phase_residuals = constraints(states)
    phase_residual_norm = float(np.linalg.norm(phase_residuals, ord=np.inf))
    metric = max(float(residual_norms.max()), abs(energy_residual), phase_residual_norm)
    residual_history.append(residual_norms)
    energy_history.append(energy_residual)
    phase_history.append(phase_residual_norm)
    mapping_time_history.append(mapping_time)
    rotation_history.append(rotation)
    if metric < best_metric:
        best_states = states.copy()
        best_mapped = mapped.copy()
        best_targets = targets.copy()
        best_interpolation = interpolation.copy()
        best_mapping_time = mapping_time
        best_rotation = rotation
        best_norms = residual_norms.copy()
        best_energy_residual = energy_residual
        best_phase_residual = phase_residual_norm

    if best_norms is None:
        raise RuntimeError("Fixed-Jacobi free-time correction did not evaluate a candidate")
    if not np.array_equal(residual_history[-1], best_norms):
        residual_history.append(best_norms)
        energy_history.append(best_energy_residual)
        phase_history.append(best_phase_residual)
        mapping_time_history.append(best_mapping_time)
        rotation_history.append(best_rotation)

    return FixedJacobiFreeTimeRotationCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=best_interpolation,
        rotation_angle_rad=float(best_rotation),
        mapping_time=float(best_mapping_time),
        target_jacobi=target_energy,
        residual_history=np.asarray(residual_history),
        energy_residual_history=np.asarray(energy_history),
        phase_residual_history=np.asarray(phase_history),
        correction_norm_history=np.asarray(correction_history),
        mapping_time_history=np.asarray(mapping_time_history),
        rotation_history=np.asarray(rotation_history),
        jacobian_condition_history=np.asarray(condition_history),
        jacobian_min_singular_history=np.asarray(min_singular_history),
        jacobian_max_singular_history=np.asarray(max_singular_history),
    )


def _curve_correction_variables(
    correction: FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection,
) -> np.ndarray:
    """Pack curve states, mapping time, and rotation into one continuation vector."""

    return np.r_[
        correction.corrected_states.reshape(-1),
        correction.mapping_time,
        correction.rotation_angle_rad,
    ]


def _curve_phase_directions(
    seed: StroboscopicInvariantCurveSeed,
    reference_states: np.ndarray,
    *,
    mapping_time: float,
    rotation_angle_rad: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return normalized longitudinal and latitudinal phase directions.

    This follows McCarthy Equations (3.34)-(3.41). The longitudinal direction
    combines the CR3BP flow with the invariant-curve rotation, while the
    latitudinal direction is the trigonometric derivative of the curve.
    """

    derivative_matrix = _trigonometric_interpolation_derivative_matrix(
        seed.phases,
        seed.phases,
    )
    latitudinal = derivative_matrix @ reference_states
    flow = np.asarray(
        [cr3bp_rhs(0.0, state, seed.mu) for state in reference_states],
        dtype=float,
    )
    longitudinal = (mapping_time / (2.0 * np.pi)) * (
        flow - (rotation_angle_rad / mapping_time) * latitudinal
    )

    longitudinal /= np.linalg.norm(longitudinal)
    latitudinal -= np.sum(latitudinal * longitudinal) * longitudinal
    latitudinal_norm = float(np.linalg.norm(latitudinal))
    if latitudinal_norm <= 1.0e-14:
        raise RuntimeError("Longitudinal and latitudinal phase directions are degenerate")
    latitudinal /= latitudinal_norm
    return longitudinal, latitudinal


def _fixed_mapping_correction_variables(
    correction: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
) -> np.ndarray:
    return np.r_[correction.corrected_states.reshape(-1), correction.rotation_angle_rad]


def _fixed_mapping_pseudo_arclength_geometry(
    previous: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
    current: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Build a phase-projected secant for fixed-mapping-time continuation."""

    if previous.corrected_states.shape != current.corrected_states.shape:
        raise ValueError("Fixed-mapping corrections must share one curve resolution")
    if (
        abs(previous.seed.mu - current.seed.mu) > 1e-15
        or abs(previous.seed.orbit_period - current.seed.orbit_period) > 1e-12
        or not np.allclose(previous.seed.phases, current.seed.phases, rtol=0.0, atol=1e-13)
    ):
        raise ValueError("Fixed-mapping corrections must share compatible seeds")

    current_variables = _fixed_mapping_correction_variables(current)
    tangent = current_variables - _fixed_mapping_correction_variables(previous)
    phase_direction = np.roll(current.corrected_states, -1, axis=0) - np.roll(
        current.corrected_states,
        1,
        axis=0,
    )
    phase_direction /= np.linalg.norm(phase_direction)
    state_size = current.corrected_states.size
    full_phase = np.zeros_like(tangent)
    full_phase[:state_size] = phase_direction.reshape(-1)
    tangent -= np.dot(tangent, full_phase) * full_phase
    natural_step = float(np.linalg.norm(tangent))
    if natural_step <= 1e-12:
        raise RuntimeError("Fixed-mapping pseudo-arclength secant is degenerate")
    tangent /= natural_step
    if tangent[-1] < 0.0:
        tangent *= -1.0
    return current_variables, tangent, phase_direction, natural_step


def stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
    previous: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
    current: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
    *,
    step_size: float | None = None,
    max_iterations: int = 24,
    tolerance: float = 1e-8,
    constraint_tolerance: float = 1e-10,
    max_step: float = 0.01,
    max_state_step: float | None = None,
    max_rotation_step: float = 0.02,
    max_predictor_distance_factor: float = 4.0,
    rcond: float = 1e-11,
) -> FixedMappingPseudoArclengthCorrection:
    """Correct one fixed-time quasi-DRO on a pseudo-arclength hyperplane."""

    seed = current.seed
    current_variables, tangent, phase_direction, natural_step = (
        _fixed_mapping_pseudo_arclength_geometry(previous, current)
    )
    continuation_step = natural_step if step_size is None else float(step_size)
    if continuation_step <= 0.0:
        raise ValueError("step_size must be positive")
    predictor = current_variables + continuation_step * tangent
    variables = predictor.copy()
    reference_states = current.corrected_states
    sample_count = reference_states.shape[0]
    state_size = reference_states.size
    state_limit = (
        max(0.15 * continuation_step, 1e-4)
        if max_state_step is None
        else float(max_state_step)
    )

    residual_history: list[np.ndarray] = []
    phase_history: list[float] = []
    arclength_history: list[float] = []
    correction_history: list[np.ndarray] = []
    rotation_history: list[float] = []
    condition_history: list[float] = []

    for _ in range(max_iterations):
        states = variables[:state_size].reshape(sample_count, 6)
        rotation = float(variables[-1] % (2.0 * np.pi))
        variables[-1] = rotation
        interpolation = _trigonometric_interpolation_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=seed.orbit_period,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        displacement = states - reference_states
        phase_residual = float(np.sum(displacement * phase_direction))
        arclength_residual = float(np.dot(tangent, variables - predictor))
        residual_history.append(residual_norms)
        phase_history.append(phase_residual)
        arclength_history.append(arclength_residual)
        rotation_history.append(rotation)
        if (
            residual_norms.max() < tolerance
            and abs(phase_residual) < constraint_tolerance
            and abs(arclength_residual) < constraint_tolerance
        ):
            predictor_distance = float(np.linalg.norm(variables - predictor))
            if predictor_distance > max_predictor_distance_factor * continuation_step:
                raise RuntimeError(
                    "Fixed-mapping correction reached a remote branch: "
                    f"predictor distance={predictor_distance:.3e}, "
                    f"step={continuation_step:.3e}"
                )
            component = seed.mode_component
            component_displacement = states[:, component] - seed.orbit_state[component]
            amplitude = float(np.sqrt(2.0 * np.mean(component_displacement**2)))
            return FixedMappingPseudoArclengthCorrection(
                seed=seed,
                corrected_states=states.copy(),
                corrected_mapped_states=mapped.copy(),
                corrected_target_states=targets.copy(),
                corrected_points=_project_to_mode_plane(states, seed.orbit_state, seed.mode_basis),
                corrected_mapped_points=_project_to_mode_plane(mapped, seed.orbit_state, seed.mode_basis),
                corrected_target_points=_project_to_mode_plane(targets, seed.orbit_state, seed.mode_basis),
                interpolation_matrix=interpolation.copy(),
                rotation_angle_rad=rotation,
                target_amplitude=amplitude,
                amplitude_component=component,
                predictor_variables=predictor.copy(),
                continuation_tangent=tangent.copy(),
                step_size=continuation_step,
                residual_history=np.asarray(residual_history),
                phase_residual_history=np.asarray(phase_history),
                arclength_residual_history=np.asarray(arclength_history),
                correction_norm_history=np.asarray(correction_history),
                rotation_history=np.asarray(rotation_history),
                jacobian_condition_history=np.asarray(condition_history),
            )

        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        jacobian[:state_size, -1] = -(interpolation_derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = phase_direction.reshape(-1)
        jacobian[state_size + 1, :] = tangent
        condition_history.append(float(np.linalg.cond(jacobian)))
        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                np.array([phase_residual, arclength_residual]),
            ]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        rotation_delta = float(delta[-1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(rotation_delta) > max_rotation_step:
            scale = min(scale, max_rotation_step / abs(rotation_delta))
        delta *= scale
        correction_history.append(
            np.linalg.norm(delta[:state_size].reshape(sample_count, 6), axis=1)
        )
        variables += delta

    raise RuntimeError(
        "Fixed-mapping pseudo-arclength correction did not converge after "
        f"{max_iterations} iterations; curve={residual_history[-1].max():.3e}, "
        f"phase={phase_history[-1]:.3e}, "
        f"arc={arclength_history[-1]:.3e}"
    )


def _pseudo_arclength_geometry(
    previous: FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection,
    current: FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Build a phase-projected secant, predictor basis, and natural step scale."""

    if previous.seed is not current.seed:
        raise ValueError("Pseudo-arclength seeds must share the same invariant-curve seed")
    seed = current.seed
    previous_variables = _curve_correction_variables(previous)
    current_variables = _curve_correction_variables(current)
    longitudinal, latitudinal = _curve_phase_directions(
        current.seed,
        current.corrected_states,
        mapping_time=current.mapping_time,
        rotation_angle_rad=current.rotation_angle_rad,
    )
    state_size = current.corrected_states.size
    sample_count = current.corrected_states.shape[0]
    tangent = current_variables - previous_variables
    for direction in (longitudinal, latitudinal):
        full_direction = np.zeros_like(tangent)
        full_direction[:state_size] = direction.reshape(-1)
        tangent -= np.dot(tangent, full_direction) * full_direction
    natural_step = float(np.linalg.norm(tangent))
    if natural_step <= 1.0e-12:
        raise RuntimeError("Phase-projected pseudo-arclength secant is degenerate")
    tangent /= natural_step
    component = seed.mode_component
    previous_displacement = (
        previous.corrected_states[:, component] - seed.orbit_state[component]
    )
    current_displacement = (
        current.corrected_states[:, component] - seed.orbit_state[component]
    )
    previous_amplitude = float(np.sqrt(2.0 * np.mean(previous_displacement**2)))
    current_amplitude = float(np.sqrt(2.0 * np.mean(current_displacement**2)))
    amplitude_gradient = np.zeros_like(current.corrected_states)
    if current_amplitude > 1.0e-14:
        amplitude_gradient[:, component] = (
            2.0 * current_displacement / (sample_count * current_amplitude)
        )
    amplitude_direction = float(
        np.dot(amplitude_gradient.reshape(-1), tangent[:state_size])
    )
    if (current_amplitude - previous_amplitude) * amplitude_direction < 0.0:
        tangent *= -1.0
    return current_variables, tangent, longitudinal, latitudinal, natural_step


def stroboscopic_curve_pseudo_arclength_correction(
    previous: FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection,
    current: FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection,
    *,
    step_size: float | None = None,
    target_jacobi: float | None = None,
    max_iterations: int = 24,
    tolerance: float = 2.0e-9,
    constraint_tolerance: float = 1.0e-10,
    max_step: float = 0.01,
    max_state_step: float | None = None,
    max_mapping_time_step: float = 0.01,
    max_rotation_step: float = 0.01,
    max_predictor_distance_factor: float = 4.0,
    rcond: float = 1.0e-11,
) -> PseudoArclengthCurveCorrection:
    """Correct one fixed-energy torus on a pseudo-arclength hyperplane.

    The residual contains curve invariance, mean Jacobi constant, McCarthy's
    longitudinal and latitudinal phase constraints, and one pseudo-arclength
    constraint. STM blocks provide the dense analytic invariance Jacobian.
    """

    seed = current.seed
    if previous.seed is not seed:
        raise ValueError("previous and current corrections must share the same seed")
    current_variables, tangent, longitudinal, latitudinal, natural_step = (
        _pseudo_arclength_geometry(previous, current)
    )
    continuation_step = natural_step if step_size is None else float(step_size)
    if continuation_step <= 0.0:
        raise ValueError("step_size must be positive")
    predictor = current_variables + continuation_step * tangent
    variables = predictor.copy()
    reference_states = current.corrected_states
    target_energy = (
        float(current.target_jacobi)
        if target_jacobi is None
        else float(target_jacobi)
    )
    state_size = reference_states.size
    sample_count = reference_states.shape[0]
    state_limit = (
        max(0.15 * continuation_step, 1.0e-4)
        if max_state_step is None
        else float(max_state_step)
    )
    if max_predictor_distance_factor <= 0.0:
        raise ValueError("max_predictor_distance_factor must be positive")

    residual_history: list[np.ndarray] = []
    energy_history: list[float] = []
    longitudinal_history: list[float] = []
    latitudinal_history: list[float] = []
    arclength_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    rotation_history: list[float] = []
    condition_history: list[float] = []

    for _ in range(max_iterations):
        states = variables[:state_size].reshape(sample_count, 6)
        mapping_time = float(variables[state_size])
        rotation = float(variables[state_size + 1])
        if mapping_time <= 0.0:
            raise RuntimeError("Pseudo-arclength correction produced a non-positive mapping time")

        interpolation = _trigonometric_interpolation_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        energy_residual = float(np.mean(jacobi_constant(states, seed.mu)) - target_energy)
        energy_gradient = _jacobi_gradient(states, seed.mu) / sample_count
        displacement = states - reference_states
        longitudinal_residual = float(np.sum(displacement * longitudinal))
        latitudinal_residual = float(np.sum(displacement * latitudinal))
        arclength_residual = float(np.dot(tangent, variables - predictor))

        residual_history.append(residual_norms)
        energy_history.append(energy_residual)
        longitudinal_history.append(longitudinal_residual)
        latitudinal_history.append(latitudinal_residual)
        arclength_history.append(arclength_residual)
        mapping_time_history.append(mapping_time)
        rotation_history.append(rotation)
        if (
            residual_norms.max() < tolerance
            and abs(energy_residual) < constraint_tolerance
            and abs(longitudinal_residual) < constraint_tolerance
            and abs(latitudinal_residual) < constraint_tolerance
            and abs(arclength_residual) < constraint_tolerance
        ):
            predictor_distance = float(np.linalg.norm(variables - predictor))
            if predictor_distance > max_predictor_distance_factor * continuation_step:
                raise RuntimeError(
                    "Pseudo-arclength correction reached a remote branch: "
                    f"predictor distance={predictor_distance:.3e}, "
                    f"step={continuation_step:.3e}"
                )
            return PseudoArclengthCurveCorrection(
                seed=seed,
                corrected_states=states.copy(),
                corrected_mapped_states=mapped.copy(),
                corrected_target_states=targets.copy(),
                corrected_points=_project_to_mode_plane(states, seed.orbit_state, seed.mode_basis),
                corrected_mapped_points=_project_to_mode_plane(mapped, seed.orbit_state, seed.mode_basis),
                corrected_target_points=_project_to_mode_plane(targets, seed.orbit_state, seed.mode_basis),
                interpolation_matrix=interpolation.copy(),
                rotation_angle_rad=float(rotation % (2.0 * np.pi)),
                mapping_time=mapping_time,
                target_jacobi=target_energy,
                predictor_variables=predictor.copy(),
                continuation_tangent=tangent.copy(),
                step_size=continuation_step,
                residual_history=np.asarray(residual_history),
                energy_residual_history=np.asarray(energy_history),
                longitudinal_phase_residual_history=np.asarray(longitudinal_history),
                latitudinal_phase_residual_history=np.asarray(latitudinal_history),
                arclength_residual_history=np.asarray(arclength_history),
                correction_norm_history=np.asarray(correction_history),
                mapping_time_history=np.asarray(mapping_time_history),
                rotation_history=np.asarray(rotation_history),
                jacobian_condition_history=np.asarray(condition_history),
            )

        jacobian = np.zeros((state_size + 4, state_size + 2), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[:state_size, state_size + 1] = -(
            interpolation_derivative @ states
        ).reshape(-1)
        jacobian[state_size, :state_size] = energy_gradient.reshape(-1)
        jacobian[state_size + 1, :state_size] = longitudinal.reshape(-1)
        jacobian[state_size + 2, :state_size] = latitudinal.reshape(-1)
        jacobian[state_size + 3, :] = tangent
        condition_history.append(float(np.linalg.cond(jacobian)))

        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                np.array(
                    [
                        energy_residual,
                        longitudinal_residual,
                        latitudinal_residual,
                        arclength_residual,
                    ]
                ),
            ]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[state_size])
        rotation_delta = float(delta[state_size + 1])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        if abs(rotation_delta) > max_rotation_step:
            scale = min(scale, max_rotation_step / abs(rotation_delta))
        delta *= scale
        correction_history.append(np.linalg.norm(delta[:state_size].reshape(sample_count, 6), axis=1))
        variables += delta

    raise RuntimeError(
        "Pseudo-arclength curve correction did not converge after "
        f"{max_iterations} iterations; curve={residual_history[-1].max():.3e}, "
        f"energy={energy_history[-1]:.3e}, phase0={longitudinal_history[-1]:.3e}, "
        f"phase1={latitudinal_history[-1]:.3e}, arc={arclength_history[-1]:.3e}"
    )


def corrected_constant_energy_pseudo_arclength_family(
    seed_corrections: tuple[
        FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...
    ]
    | list[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection],
    *,
    members: int,
    step_size: float | None = None,
    minimum_step_size: float = 1.0e-5,
    maximum_step_size: float | None = None,
    max_iterations: int = 24,
    tolerance: float = 2.0e-9,
    constraint_tolerance: float = 1.0e-10,
    max_step: float = 0.01,
) -> list[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection]:
    """Continue a fixed-energy torus family with adaptive pseudo-arclength steps."""

    if len(seed_corrections) < 2:
        raise ValueError("At least two corrected curves are required")
    if members < len(seed_corrections):
        raise ValueError("members must include the supplied seed corrections")
    family = list(seed_corrections)
    _, _, _, _, natural_step = _pseudo_arclength_geometry(family[-2], family[-1])
    current_step = natural_step if step_size is None else float(step_size)
    maximum_step = (
        2.0 * natural_step if maximum_step_size is None else float(maximum_step_size)
    )
    if not 0.0 < minimum_step_size <= current_step:
        raise ValueError("minimum_step_size must be positive and no larger than step_size")

    while len(family) < members:
        trial_step = min(current_step, maximum_step)
        while True:
            try:
                correction = stroboscopic_curve_pseudo_arclength_correction(
                    family[-2],
                    family[-1],
                    step_size=trial_step,
                    max_iterations=max_iterations,
                    tolerance=tolerance,
                    constraint_tolerance=constraint_tolerance,
                    max_step=max_step,
                )
                break
            except RuntimeError as error:
                trial_step *= 0.5
                if trial_step < minimum_step_size:
                    raise RuntimeError(
                        "Pseudo-arclength family stopped after "
                        f"{len(family)} members at step={trial_step:.3e}: {error}"
                    ) from error
        family.append(correction)
        iterations = correction.residual_history.shape[0]
        current_step = min(
            maximum_step,
            trial_step * (1.20 if iterations <= 6 else 1.0),
        )
    return family


def _fixed_frequency_correction_variables(
    correction: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
) -> np.ndarray:
    return np.r_[correction.corrected_states.reshape(-1), correction.mapping_time]


def _fixed_frequency_pseudo_arclength_geometry(
    previous: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    current: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Build a phase-projected secant for fixed-rotation continuation."""

    if previous.seed is not current.seed:
        raise ValueError("Fixed-frequency corrections must share the same seed")
    if abs(previous.rotation_angle_rad - current.rotation_angle_rad) > 1.0e-12:
        raise ValueError("Fixed-frequency corrections must share one rotation angle")
    seed = current.seed
    previous_variables = _fixed_frequency_correction_variables(previous)
    current_variables = _fixed_frequency_correction_variables(current)
    longitudinal, latitudinal = _curve_phase_directions(
        seed,
        current.corrected_states,
        mapping_time=current.mapping_time,
        rotation_angle_rad=current.rotation_angle_rad,
    )
    state_size = current.corrected_states.size
    tangent = current_variables - previous_variables
    for direction in (longitudinal, latitudinal):
        full_phase = np.zeros_like(tangent)
        full_phase[:state_size] = direction.reshape(-1)
        tangent -= np.dot(tangent, full_phase) * full_phase
    natural_step = float(np.linalg.norm(tangent))
    if natural_step <= 1.0e-12:
        raise RuntimeError("Fixed-frequency pseudo-arclength secant is degenerate")
    tangent /= natural_step

    component = seed.mode_component
    previous_displacement = (
        previous.corrected_states[:, component] - seed.orbit_state[component]
    )
    current_displacement = (
        current.corrected_states[:, component] - seed.orbit_state[component]
    )
    previous_amplitude = float(np.sqrt(2.0 * np.mean(previous_displacement**2)))
    current_amplitude = float(np.sqrt(2.0 * np.mean(current_displacement**2)))
    sample_count = current.corrected_states.shape[0]
    amplitude_gradient = np.zeros_like(current.corrected_states)
    if current_amplitude > 1.0e-14:
        amplitude_gradient[:, component] = (
            2.0 * current_displacement / (sample_count * current_amplitude)
        )
    amplitude_direction = float(
        np.dot(amplitude_gradient.reshape(-1), tangent[:state_size])
    )
    if (current_amplitude - previous_amplitude) * amplitude_direction < 0.0:
        tangent *= -1.0
    return current_variables, tangent, longitudinal, latitudinal, natural_step


def stroboscopic_curve_fixed_frequency_energy_correction(
    reference: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    *,
    target_jacobi: float,
    previous: FixedFrequencyEnergyCurveCorrection | None = None,
    max_iterations: int = 32,
    tolerance: float = 2.0e-9,
    energy_tolerance: float = 5.0e-9,
    phase_tolerance: float = 1.0e-10,
    max_step: float = 0.01,
    max_state_step: float = 5.0e-4,
    max_mapping_time_step: float = 0.01,
    rcond: float = 1.0e-11,
) -> FixedFrequencyEnergyCurveCorrection:
    """Correct a fixed-frequency curve while enforcing one energy at every node."""

    seed = reference.seed
    states = reference.corrected_states.copy()
    mapping_time = float(reference.mapping_time)
    if previous is not None:
        if previous.seed is not reference.seed:
            raise ValueError("previous and reference corrections must share one seed")
        if previous.corrected_states.shape != states.shape:
            raise ValueError("previous and reference corrections must share one resolution")
        if not isinstance(reference, FixedFrequencyEnergyCurveCorrection):
            raise ValueError("secant prediction requires an energy-corrected reference")
        energy_span = reference.target_jacobi - previous.target_jacobi
        if abs(energy_span) <= 1.0e-14:
            raise ValueError("previous and reference Jacobi targets must differ")
        ratio = (target_jacobi - reference.target_jacobi) / energy_span
        states += ratio * (reference.corrected_states - previous.corrected_states)
        mapping_time += ratio * (reference.mapping_time - previous.mapping_time)
    rotation = float(reference.rotation_angle_rad)
    interpolation = _trigonometric_interpolation_matrix(
        seed.phases,
        seed.phases + rotation,
    )
    longitudinal, latitudinal = _curve_phase_directions(
        seed,
        states,
        mapping_time=mapping_time,
        rotation_angle_rad=rotation,
    )
    reference_states = reference.corrected_states.copy()
    sample_count = states.shape[0]
    state_size = states.size

    residual_history: list[np.ndarray] = []
    energy_history: list[np.ndarray] = []
    longitudinal_history: list[float] = []
    latitudinal_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    condition_history: list[float] = []

    best_metric = np.inf
    best_states = states.copy()
    best_mapped = np.empty_like(states)
    best_targets = np.empty_like(states)
    best_mapping_time = mapping_time
    best_residuals = np.full(sample_count, np.inf)
    best_energy = np.full(sample_count, np.inf)
    best_longitudinal = np.inf
    best_latitudinal = np.inf

    for _ in range(max_iterations):
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        energy_residuals = jacobi_constant(states, seed.mu) - target_jacobi
        displacement = states - reference_states
        longitudinal_residual = float(np.sum(displacement * longitudinal))
        latitudinal_residual = float(np.sum(displacement * latitudinal))
        metric = max(
            float(residual_norms.max()),
            float(np.max(np.abs(energy_residuals))),
            abs(longitudinal_residual),
            abs(latitudinal_residual),
        )
        residual_history.append(residual_norms)
        energy_history.append(energy_residuals)
        longitudinal_history.append(longitudinal_residual)
        latitudinal_history.append(latitudinal_residual)
        mapping_time_history.append(mapping_time)
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_mapped = mapped.copy()
            best_targets = targets.copy()
            best_mapping_time = mapping_time
            best_residuals = residual_norms.copy()
            best_energy = energy_residuals.copy()
            best_longitudinal = longitudinal_residual
            best_latitudinal = latitudinal_residual
        if (
            residual_norms.max() < tolerance
            and np.max(np.abs(energy_residuals)) < energy_tolerance
            and abs(longitudinal_residual) < phase_tolerance
            and abs(latitudinal_residual) < phase_tolerance
        ):
            break

        jacobian = np.zeros(
            (state_size + sample_count + 2, state_size + 1),
            dtype=float,
        )
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        energy_gradients = _jacobi_gradient(states, seed.mu)
        for row in range(sample_count):
            jacobian[state_size + row, 6 * row : 6 * row + 6] = energy_gradients[row]
        jacobian[state_size + sample_count, :state_size] = longitudinal.reshape(-1)
        jacobian[state_size + sample_count + 1, :state_size] = latitudinal.reshape(-1)
        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                energy_residuals,
                np.array([longitudinal_residual, latitudinal_residual]),
            ]
        )
        delta, _, _, singular_values = np.linalg.lstsq(
            jacobian,
            right_hand_side,
            rcond=rcond,
        )
        condition_history.append(
            float(singular_values[0] / singular_values[-1])
            if singular_values.size and singular_values[-1] > 0.0
            else np.inf
        )
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[state_size])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > max_state_step:
            scale = min(scale, max_state_step / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        delta *= scale
        correction_history.append(
            np.linalg.norm(delta[:state_size].reshape(sample_count, 6), axis=1)
        )
        states += delta[:state_size].reshape(sample_count, 6)
        mapping_time += float(delta[state_size])
        if mapping_time <= 0.0:
            raise RuntimeError("Fixed-frequency energy correction produced non-positive time")

    if not np.array_equal(residual_history[-1], best_residuals):
        residual_history.append(best_residuals)
        energy_history.append(best_energy)
        longitudinal_history.append(best_longitudinal)
        latitudinal_history.append(best_latitudinal)
        mapping_time_history.append(best_mapping_time)
    return FixedFrequencyEnergyCurveCorrection(
        seed=seed,
        corrected_states=best_states,
        corrected_mapped_states=best_mapped,
        corrected_target_states=best_targets,
        corrected_points=_project_to_mode_plane(best_states, seed.orbit_state, seed.mode_basis),
        corrected_mapped_points=_project_to_mode_plane(best_mapped, seed.orbit_state, seed.mode_basis),
        corrected_target_points=_project_to_mode_plane(best_targets, seed.orbit_state, seed.mode_basis),
        interpolation_matrix=interpolation.copy(),
        rotation_angle_rad=rotation,
        mapping_time=best_mapping_time,
        target_jacobi=float(target_jacobi),
        residual_history=np.asarray(residual_history),
        energy_residual_history=np.asarray(energy_history),
        longitudinal_phase_residual_history=np.asarray(longitudinal_history),
        latitudinal_phase_residual_history=np.asarray(latitudinal_history),
        correction_norm_history=np.asarray(correction_history),
        mapping_time_history=np.asarray(mapping_time_history),
        jacobian_condition_history=np.asarray(condition_history),
    )


def stroboscopic_curve_fixed_frequency_pseudo_arclength_correction(
    previous: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    current: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    *,
    step_size: float | None = None,
    max_iterations: int = 32,
    tolerance: float = 2.0e-9,
    constraint_tolerance: float = 1.0e-10,
    max_step: float = 0.01,
    max_state_step: float | None = None,
    max_mapping_time_step: float = 0.02,
    max_predictor_distance_factor: float = 4.0,
    rcond: float = 1.0e-11,
) -> FixedFrequencyPseudoArclengthCorrection:
    """Correct one fixed-frequency torus on a pseudo-arclength hyperplane."""

    seed = current.seed
    current_variables, tangent, longitudinal, latitudinal, natural_step = (
        _fixed_frequency_pseudo_arclength_geometry(previous, current)
    )
    continuation_step = natural_step if step_size is None else float(step_size)
    if continuation_step <= 0.0:
        raise ValueError("step_size must be positive")
    predictor = current_variables + continuation_step * tangent
    variables = predictor.copy()
    reference_states = current.corrected_states
    state_size = reference_states.size
    sample_count = reference_states.shape[0]
    rotation = float(current.rotation_angle_rad)
    interpolation = _trigonometric_interpolation_matrix(
        seed.phases,
        seed.phases + rotation,
    )
    state_limit = (
        max(0.15 * continuation_step, 1.0e-4)
        if max_state_step is None
        else float(max_state_step)
    )

    residual_history: list[np.ndarray] = []
    longitudinal_history: list[float] = []
    latitudinal_history: list[float] = []
    arclength_history: list[float] = []
    correction_history: list[np.ndarray] = []
    mapping_time_history: list[float] = []
    condition_history: list[float] = []

    for _ in range(max_iterations):
        states = variables[:state_size].reshape(sample_count, 6)
        mapping_time = float(variables[state_size])
        if mapping_time <= 0.0:
            raise RuntimeError("Fixed-frequency correction produced a non-positive mapping time")
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=max_step,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        displacement = states - reference_states
        longitudinal_residual = float(np.sum(displacement * longitudinal))
        latitudinal_residual = float(np.sum(displacement * latitudinal))
        arclength_residual = float(np.dot(tangent, variables - predictor))
        residual_history.append(residual_norms)
        longitudinal_history.append(longitudinal_residual)
        latitudinal_history.append(latitudinal_residual)
        arclength_history.append(arclength_residual)
        mapping_time_history.append(mapping_time)
        if (
            residual_norms.max() < tolerance
            and abs(longitudinal_residual) < constraint_tolerance
            and abs(latitudinal_residual) < constraint_tolerance
            and abs(arclength_residual) < constraint_tolerance
        ):
            predictor_distance = float(np.linalg.norm(variables - predictor))
            if predictor_distance > max_predictor_distance_factor * continuation_step:
                raise RuntimeError(
                    "Fixed-frequency correction reached a remote branch: "
                    f"predictor distance={predictor_distance:.3e}, "
                    f"step={continuation_step:.3e}"
                )
            return FixedFrequencyPseudoArclengthCorrection(
                seed=seed,
                corrected_states=states.copy(),
                corrected_mapped_states=mapped.copy(),
                corrected_target_states=targets.copy(),
                corrected_points=_project_to_mode_plane(states, seed.orbit_state, seed.mode_basis),
                corrected_mapped_points=_project_to_mode_plane(mapped, seed.orbit_state, seed.mode_basis),
                corrected_target_points=_project_to_mode_plane(targets, seed.orbit_state, seed.mode_basis),
                interpolation_matrix=interpolation.copy(),
                rotation_angle_rad=rotation,
                mapping_time=mapping_time,
                predictor_variables=predictor.copy(),
                continuation_tangent=tangent.copy(),
                step_size=continuation_step,
                residual_history=np.asarray(residual_history),
                longitudinal_phase_residual_history=np.asarray(longitudinal_history),
                latitudinal_phase_residual_history=np.asarray(latitudinal_history),
                arclength_residual_history=np.asarray(arclength_history),
                correction_norm_history=np.asarray(correction_history),
                mapping_time_history=np.asarray(mapping_time_history),
                jacobian_condition_history=np.asarray(condition_history),
            )

        jacobian = np.zeros((state_size + 3, state_size + 1), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[state_size, :state_size] = longitudinal.reshape(-1)
        jacobian[state_size + 1, :state_size] = latitudinal.reshape(-1)
        jacobian[state_size + 2, :] = tangent
        condition_history.append(float(np.linalg.cond(jacobian)))
        right_hand_side = -np.concatenate(
            [
                residuals.reshape(-1),
                np.array(
                    [
                        longitudinal_residual,
                        latitudinal_residual,
                        arclength_residual,
                    ]
                ),
            ]
        )
        delta = np.linalg.lstsq(jacobian, right_hand_side, rcond=rcond)[0]
        state_delta = delta[:state_size].reshape(sample_count, 6)
        mapping_time_delta = float(delta[state_size])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > state_limit:
            scale = min(scale, state_limit / float(block_norms.max()))
        if abs(mapping_time_delta) > max_mapping_time_step:
            scale = min(scale, max_mapping_time_step / abs(mapping_time_delta))
        delta *= scale
        correction_history.append(
            np.linalg.norm(delta[:state_size].reshape(sample_count, 6), axis=1)
        )
        variables += delta

    raise RuntimeError(
        "Fixed-frequency pseudo-arclength correction did not converge after "
        f"{max_iterations} iterations; curve={residual_history[-1].max():.3e}, "
        f"phase0={longitudinal_history[-1]:.3e}, "
        f"phase1={latitudinal_history[-1]:.3e}, "
        f"arc={arclength_history[-1]:.3e}"
    )


def corrected_fixed_frequency_pseudo_arclength_family(
    seed_corrections: tuple[
        FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection, ...
    ]
    | list[FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection],
    *,
    members: int,
    step_size: float | None = None,
    minimum_step_size: float = 1.0e-5,
    maximum_step_size: float | None = None,
    max_iterations: int = 32,
    tolerance: float = 2.0e-9,
    constraint_tolerance: float = 1.0e-10,
    max_step: float = 0.01,
) -> list[FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection]:
    """Continue a fixed-frequency family with adaptive pseudo-arclength steps."""

    if len(seed_corrections) < 2:
        raise ValueError("At least two fixed-frequency corrections are required")
    if members < len(seed_corrections):
        raise ValueError("members must include the supplied corrections")
    family = list(seed_corrections)
    _, _, _, _, natural_step = _fixed_frequency_pseudo_arclength_geometry(
        family[-2],
        family[-1],
    )
    current_step = natural_step if step_size is None else float(step_size)
    maximum_step = (
        2.0 * natural_step if maximum_step_size is None else float(maximum_step_size)
    )
    if not 0.0 < minimum_step_size <= current_step:
        raise ValueError("minimum_step_size must be positive and no larger than step_size")

    while len(family) < members:
        trial_step = min(current_step, maximum_step)
        while True:
            try:
                correction = stroboscopic_curve_fixed_frequency_pseudo_arclength_correction(
                    family[-2],
                    family[-1],
                    step_size=trial_step,
                    max_iterations=max_iterations,
                    tolerance=tolerance,
                    constraint_tolerance=constraint_tolerance,
                    max_step=max_step,
                )
                break
            except RuntimeError as error:
                trial_step *= 0.5
                if trial_step < minimum_step_size:
                    raise RuntimeError(
                        "Fixed-frequency family stopped after "
                        f"{len(family)} members at step={trial_step:.3e}: {error}"
                    ) from error
        family.append(correction)
        iterations = correction.residual_history.shape[0]
        current_step = min(
            maximum_step,
            trial_step * (1.20 if iterations <= 6 else 1.0),
        )
    return family


def _corrected_torus_from_seed(
    seed: StroboscopicInvariantCurveSeed,
    *,
    time_samples: int,
    max_iterations: int,
    max_step: float,
) -> CorrectedStroboscopicTorus:
    """Correct and sweep one periodic-orbit invariant-curve seed."""

    samples = seed.phases.size
    if samples % 2 == 0:
        raise ValueError("samples must be odd for trigonometric interpolation")
    if time_samples < 2:
        raise ValueError("time_samples must be at least 2")
    correction = stroboscopic_curve_newton_correction(
        seed,
        max_iterations=max_iterations,
        max_step=max_step,
    )

    return _sweep_corrected_curve_correction(
        correction,
        time_samples=time_samples,
        max_step=max_step,
    )


def _sweep_corrected_curve_correction(
    correction: (
        StroboscopicCurveNewtonCorrection
        | FreeRotationCurveCorrection
        | FreeMappingTimeCurveCorrection
        | FreeEnergyCurveCorrection
        | PseudoArclengthCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    *,
    time_samples: int,
    max_step: float,
) -> CorrectedStroboscopicTorus:
    """Sweep an already corrected invariant curve through one mapping interval."""

    seed = correction.seed
    samples = seed.phases.size
    if time_samples < 2:
        raise ValueError("time_samples must be at least 2")

    mapping_time = (
        correction.mapping_time
        if isinstance(
            correction,
            (
                FreeMappingTimeCurveCorrection,
                FreeEnergyCurveCorrection,
                PseudoArclengthCurveCorrection,
                FixedFrequencyPseudoArclengthCorrection,
                FixedFrequencyEnergyCurveCorrection,
            ),
        )
        else seed.orbit_period
    )
    times = np.linspace(0.0, mapping_time, time_samples)
    sol = integrate_states_cr3bp(
        correction.corrected_states,
        (0.0, mapping_time),
        seed.mu,
        t_eval=times,
        max_step=max_step,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    states = sol.y.T.reshape(time_samples, samples, 6)

    terminal_curve = states[-1, :, :]
    target_curve = correction.corrected_target_states
    return CorrectedStroboscopicTorus(
        correction=correction,
        normalized_times=times,
        states=states,
        surface=states[:, :, :3],
        invariant_curve=correction.corrected_states[:, :3],
        terminal_curve=terminal_curve[:, :3],
        target_curve=target_curve[:, :3],
        closure_residuals=terminal_curve - target_curve,
        jacobi_values=jacobi_constant(states.reshape(-1, 6), seed.mu).reshape(time_samples, samples),
    )


def sweep_corrected_curve_correction(
    correction: (
        StroboscopicCurveNewtonCorrection
        | FreeRotationCurveCorrection
        | FreeMappingTimeCurveCorrection
        | FreeEnergyCurveCorrection
        | PseudoArclengthCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    *,
    time_samples: int = 24,
    max_step: float = 0.01,
) -> CorrectedStroboscopicTorus:
    """Sweep one already-corrected invariant curve through its map interval."""

    return _sweep_corrected_curve_correction(
        correction,
        time_samples=time_samples,
        max_step=max_step,
    )


def resample_corrected_torus_surface(
    member: CorrectedStroboscopicTorus,
    *,
    phase_samples: int = 96,
) -> tuple[np.ndarray, np.ndarray]:
    """Densify a corrected torus in curve phase for smooth plotting."""

    if phase_samples < 3:
        raise ValueError("phase_samples must be at least 3")
    phases = np.linspace(0.0, 2.0 * np.pi, phase_samples, endpoint=True)
    surface = np.empty((member.surface.shape[0], phase_samples, 3), dtype=float)
    normalized_time = member.normalized_times / member.correction.mapping_time
    for time_index, fraction in enumerate(normalized_time):
        interpolation = _trigonometric_interpolation_matrix(
            member.correction.seed.phases,
            phases - fraction * member.correction.rotation_angle_rad,
        )
        surface[time_index] = interpolation @ member.surface[time_index]
    curve_interpolation = _trigonometric_interpolation_matrix(
        member.correction.seed.phases,
        phases,
    )
    invariant_curve = curve_interpolation @ member.invariant_curve
    return surface, invariant_curve


def corrected_stroboscopic_torus(
    mu: float,
    *,
    point: str = "L1",
    samples: int = 15,
    time_samples: int = 48,
    x_amplitude: float = 0.001,
    vertical_amplitude: float = 1e-5,
    max_iterations: int = 2,
    max_step: float = 0.02,
) -> CorrectedStroboscopicTorus:
    """Sweep a corrected stroboscopic invariant curve through CR3BP flow.

    This constructs a physically propagated small-amplitude torus surface from
    the same fixed-rotation curve correction used in Figure 3.3. It is a local
    invariant-curve surface, not the final large-amplitude continuation family
    in Chapter 3.
    """

    if samples % 2 == 0:
        raise ValueError("samples must be odd for trigonometric interpolation")
    seed = stroboscopic_invariant_curve_seed(
        mu,
        point=point,
        samples=samples,
        x_amplitude=x_amplitude,
        vertical_amplitude=vertical_amplitude,
        curve_samples=max(4 * samples, 120),
    )
    return _corrected_torus_from_seed(
        seed,
        time_samples=time_samples,
        max_iterations=max_iterations,
        max_step=max_step,
    )


def corrected_stroboscopic_torus_family(
    mu: float,
    *,
    point: str = "L1",
    vertical_amplitudes: tuple[float, ...] = (1e-5, 1.5e-5, 2e-5, 3e-5),
    samples: int = 11,
    time_samples: int = 24,
    x_amplitude: float = 0.001,
    max_iterations: int = 2,
    max_step: float = 0.02,
) -> list[CorrectedStroboscopicTorus]:
    """Return a small physically propagated stroboscopic torus family."""

    return [
        corrected_stroboscopic_torus(
            mu,
            point=point,
            samples=samples,
            time_samples=time_samples,
            x_amplitude=x_amplitude,
            vertical_amplitude=vertical_amplitude,
            max_iterations=max_iterations,
            max_step=max_step,
        )
        for vertical_amplitude in vertical_amplitudes
    ]


def corrected_vertical_stroboscopic_torus(
    mu: float,
    *,
    point: str = "L1",
    samples: int = 11,
    time_samples: int = 24,
    vertical_orbit_amplitude: float = 1e-4,
    planar_mode_amplitude: float = 1e-5,
    max_iterations: int = 2,
    max_step: float = 0.01,
) -> CorrectedStroboscopicTorus:
    """Sweep a corrected planar-mode curve around a vertical periodic orbit."""

    if samples % 2 == 0:
        raise ValueError("samples must be odd for trigonometric interpolation")
    seed = stroboscopic_vertical_invariant_curve_seed(
        mu,
        point=point,
        vertical_orbit_amplitude=vertical_orbit_amplitude,
        planar_mode_amplitude=planar_mode_amplitude,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    return _corrected_torus_from_seed(
        seed,
        time_samples=time_samples,
        max_iterations=max_iterations,
        max_step=max_step,
    )


def corrected_vertical_stroboscopic_torus_family(
    mu: float,
    *,
    point: str = "L1",
    vertical_orbit_amplitudes: tuple[float, ...] = (1e-4, 1.5e-4, 2e-4, 3e-4),
    planar_mode_amplitude: float = 1e-5,
    samples: int = 11,
    time_samples: int = 24,
    max_iterations: int = 2,
    max_step: float = 0.01,
) -> list[CorrectedStroboscopicTorus]:
    """Return a local corrected quasi-vertical stroboscopic torus family."""

    return [
        corrected_vertical_stroboscopic_torus(
            mu,
            point=point,
            samples=samples,
            time_samples=time_samples,
            vertical_orbit_amplitude=amplitude,
            planar_mode_amplitude=planar_mode_amplitude,
            max_iterations=max_iterations,
            max_step=max_step,
        )
        for amplitude in vertical_orbit_amplitudes
    ]


def corrected_fixed_frequency_curve_family(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_frequency_ratio: float,
    mode_amplitudes: tuple[float, ...],
    max_iterations: int = 16,
    max_step: float = 0.01,
) -> list[FreeMappingTimeCurveCorrection]:
    """Continue a local invariant-curve family at fixed frequency ratio."""

    amplitudes = tuple(float(value) for value in mode_amplitudes)
    if not amplitudes or any(value <= 0.0 for value in amplitudes):
        raise ValueError("mode_amplitudes must contain positive values")
    if any(a >= b for a, b in zip(amplitudes, amplitudes[1:])):
        raise ValueError("mode_amplitudes must be strictly increasing")
    if target_frequency_ratio <= 2.0:
        raise ValueError("target_frequency_ratio must exceed two")
    target_rotation = float(2.0 * np.pi / target_frequency_ratio)

    family: list[FreeMappingTimeCurveCorrection] = []
    previous_amplitude = seed.mode_amplitude
    for amplitude in amplitudes:
        if family:
            previous = family[-1]
            scale = amplitude / previous_amplitude
            initial_states = seed.orbit_state + scale * (
                previous.corrected_states - seed.orbit_state
            )
            initial_mapping_time = previous.mapping_time
        else:
            scale = amplitude / seed.mode_amplitude
            initial_states = seed.orbit_state + scale * (
                seed.initial_states - seed.orbit_state
            )
            initial_mapping_time = seed.orbit_period

        correction = stroboscopic_curve_free_mapping_time_correction(
            seed,
            target_rotation_angle_rad=target_rotation,
            target_amplitude=amplitude,
            amplitude_component=seed.mode_component,
            initial_states=initial_states,
            initial_mapping_time=initial_mapping_time,
            phase_reference_states=initial_states,
            max_iterations=max_iterations,
            max_step=max_step,
        )
        family.append(correction)
        previous_amplitude = amplitude
    return family


def corrected_l2_constant_frequency_halo_family(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    mode_amplitudes: tuple[float, ...] = (1.0e-4, 2.0e-4, 3.0e-4, 5.0e-4),
    samples: int = 9,
    time_samples: int = 24,
    max_iterations: int = 16,
    max_step: float = 0.01,
) -> list[CorrectedStroboscopicTorus]:
    """Return a local corrected L2 quasi-halo family at fixed frequency ratio."""

    seed = stroboscopic_spatial_frequency_seed(
        mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.055, 0.060),
        point="L2",
        vertical_mode=False,
        mode_component=2,
        mode_amplitude=mode_amplitudes[0],
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    corrections = corrected_fixed_frequency_curve_family(
        seed,
        target_frequency_ratio=target_frequency_ratio,
        mode_amplitudes=mode_amplitudes,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


def corrected_l2_constant_frequency_vertical_family(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    mode_amplitudes: tuple[float, ...] = (1.0e-5, 2.0e-5, 3.0e-5, 5.0e-5),
    samples: int = 9,
    time_samples: int = 24,
    max_iterations: int = 16,
    max_step: float = 0.01,
) -> list[CorrectedStroboscopicTorus]:
    """Return a local corrected L2 quasi-vertical family at fixed frequency ratio."""

    seed = stroboscopic_spatial_frequency_seed(
        mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.195, 0.200),
        point="L2",
        vertical_mode=True,
        mode_component=0,
        mode_amplitude=mode_amplitudes[0],
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    corrections = corrected_fixed_frequency_curve_family(
        seed,
        target_frequency_ratio=target_frequency_ratio,
        mode_amplitudes=mode_amplitudes,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


@lru_cache(maxsize=4)
def corrected_l2_constant_frequency_halo_pseudo_arclength_corrections(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    members: int = 78,
    samples: int = 9,
    maximum_step_size: float = 0.04,
    max_iterations: int = 64,
    tolerance: float = 3.0e-9,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection, ...]:
    """Continue the L2 fixed-frequency quasi-halo branch with ``N=9``."""

    if samples != 9:
        raise ValueError("The base fixed-frequency quasi-halo branch uses samples=9")
    parameters: dict[str, object] = {
        "version": _FIXED_FREQUENCY_CACHE_VERSION,
        "mu": float(mu),
        "target_frequency_ratio": float(target_frequency_ratio),
        "members": int(members),
        "samples": int(samples),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _fixed_frequency_cache_path("halo_n9", parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if isinstance(cached, tuple) and len(cached) == members:
            return cached

    seed = stroboscopic_spatial_frequency_seed(
        mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.055, 0.060),
        point="L2",
        vertical_mode=False,
        mode_component=2,
        mode_amplitude=1.0e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    natural = corrected_fixed_frequency_curve_family(
        seed,
        target_frequency_ratio=target_frequency_ratio,
        mode_amplitudes=(1.0e-4, 2.0e-4, 4.0e-4, 8.0e-4),
        max_iterations=max_iterations,
        max_step=max_step,
    )
    anchors = natural[-2:]
    if max(anchor.final_residual_norms.max() for anchor in anchors) >= 1.0e-9:
        raise RuntimeError("Fixed-frequency quasi-halo anchors did not converge")
    family = tuple(
        corrected_fixed_frequency_pseudo_arclength_family(
            anchors,
            members=members,
            maximum_step_size=maximum_step_size,
            max_iterations=max_iterations,
            tolerance=tolerance,
            max_step=max_step,
        )
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(family, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return family


@lru_cache(maxsize=4)
def corrected_l2_constant_frequency_halo_high_order_anchors(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    samples: int = 15,
    source_indices: tuple[int, int] = (49, 69),
    max_iterations: int = 96,
    max_step: float = 0.01,
) -> tuple[FreeMappingTimeCurveCorrection, FreeMappingTimeCurveCorrection]:
    """Spectrally lift two separated fixed-frequency quasi-halo members.

    ``N=15`` is lifted from the base ``N=9`` branch. Higher resolutions use
    the validated ``N=15`` continuation before its spectral truncation floor.
    """

    if samples < 15 or samples % 2 == 0:
        raise ValueError("samples must be odd and at least 15")
    if samples >= 21:
        source = corrected_l2_constant_frequency_halo_high_order_corrections(
            mu,
            target_frequency_ratio=target_frequency_ratio,
            members=20,
            samples=15,
            source_indices=(49, 69),
            maximum_step_size=0.10,
            max_iterations=96,
            tolerance=5.0e-10,
            max_step=max_step,
        )
    else:
        source = corrected_l2_constant_frequency_halo_pseudo_arclength_corrections(
            mu,
            target_frequency_ratio=target_frequency_ratio,
            members=78,
            max_step=max_step,
        )
    if not 0 <= source_indices[0] < source_indices[1] < len(source):
        raise ValueError("source_indices must select two ordered source members")
    seed = stroboscopic_spatial_frequency_seed(
        mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.055, 0.060),
        point="L2",
        vertical_mode=False,
        mode_component=2,
        mode_amplitude=1.0e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    target_rotation = float(2.0 * np.pi / target_frequency_ratio)
    anchors: list[FreeMappingTimeCurveCorrection] = []
    for source_index in source_indices:
        correction = source[source_index]
        interpolation = _trigonometric_interpolation_matrix(
            correction.seed.phases,
            seed.phases,
        )
        initial_states = interpolation @ correction.corrected_states
        component = seed.mode_component
        displacement = initial_states[:, component] - seed.orbit_state[component]
        target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        anchors.append(
            stroboscopic_curve_free_mapping_time_correction(
                seed,
                target_rotation_angle_rad=target_rotation,
                target_amplitude=target_amplitude,
                amplitude_component=component,
                initial_states=initial_states,
                initial_mapping_time=correction.mapping_time,
                phase_reference_states=initial_states,
                max_iterations=max_iterations,
                max_state_step=5.0e-4,
                max_mapping_time_step=0.05,
                max_step=max_step,
            )
        )
    return anchors[0], anchors[1]


@lru_cache(maxsize=4)
def corrected_l2_constant_frequency_halo_high_order_corrections(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    members: int = 20,
    samples: int = 15,
    source_indices: tuple[int, int] = (49, 69),
    maximum_step_size: float = 0.10,
    max_iterations: int = 96,
    tolerance: float = 5.0e-10,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection, ...]:
    """Continue a spectrally lifted fixed-frequency quasi-halo branch."""

    parameters: dict[str, object] = {
        "version": _FIXED_FREQUENCY_CACHE_VERSION,
        "mu": float(mu),
        "target_frequency_ratio": float(target_frequency_ratio),
        "members": int(members),
        "samples": int(samples),
        "source_indices": tuple(int(index) for index in source_indices),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _fixed_frequency_cache_path("halo_high_order", parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if (
            isinstance(cached, tuple)
            and len(cached) == members
            and all(correction.corrected_states.shape == (samples, 6) for correction in cached)
        ):
            return cached

    resume_family: tuple[
        FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection, ...
    ] | None = None
    if persistent_cache and cache_path.parent.exists():
        for candidate in cache_path.parent.glob(
            f"fixed_frequency_halo_high_order_v{_FIXED_FREQUENCY_CACHE_VERSION}_*.pkl"
        ):
            try:
                with candidate.open("rb") as stream:
                    cached = pickle.load(stream)
            except (OSError, pickle.PickleError, EOFError):
                continue
            if not isinstance(cached, tuple) or not 2 <= len(cached) < members:
                continue
            if not all(
                correction.corrected_states.shape == (samples, 6)
                and abs(correction.seed.mu - mu) < 1.0e-15
                and abs(2.0 * np.pi / correction.rotation_angle_rad - target_frequency_ratio)
                < 1.0e-10
                for correction in cached
            ):
                continue
            if resume_family is None or len(cached) > len(resume_family):
                resume_family = cached

    anchors = (
        resume_family
        if resume_family is not None
        else corrected_l2_constant_frequency_halo_high_order_anchors(
            mu,
            target_frequency_ratio=target_frequency_ratio,
            samples=samples,
            source_indices=source_indices,
            max_iterations=max_iterations,
            max_step=max_step,
        )
    )
    family = tuple(
        corrected_fixed_frequency_pseudo_arclength_family(
            anchors,
            members=members,
            maximum_step_size=maximum_step_size,
            max_iterations=max_iterations,
            tolerance=tolerance,
            max_step=max_step,
        )
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(family, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return family


def _lift_l2_constant_frequency_halo_correction(
    correction: (
        FreeMappingTimeCurveCorrection
        | FixedFrequencyPseudoArclengthCorrection
        | FixedFrequencyEnergyCurveCorrection
    ),
    *,
    samples: int,
    target_frequency_ratio: float,
    max_iterations: int,
    max_step: float,
) -> FreeMappingTimeCurveCorrection:
    """Spectrally lift one fixed-frequency L2 quasi-halo curve."""

    source_samples = correction.corrected_states.shape[0]
    if samples <= source_samples or samples % 2 == 0:
        raise ValueError("samples must be an odd value above the source resolution")
    seed = stroboscopic_spatial_frequency_seed(
        correction.seed.mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.055, 0.060),
        point="L2",
        vertical_mode=False,
        mode_component=2,
        mode_amplitude=1.0e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    interpolation = _trigonometric_interpolation_matrix(
        correction.seed.phases,
        seed.phases,
    )
    initial_states = interpolation @ correction.corrected_states
    component = seed.mode_component
    displacement = initial_states[:, component] - seed.orbit_state[component]
    target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return stroboscopic_curve_free_mapping_time_correction(
        seed,
        target_rotation_angle_rad=2.0 * np.pi / target_frequency_ratio,
        target_amplitude=target_amplitude,
        amplitude_component=component,
        initial_states=initial_states,
        initial_mapping_time=correction.mapping_time,
        phase_reference_states=initial_states,
        max_iterations=max_iterations,
        tolerance=5.0e-10,
        max_state_step=5.0e-4,
        max_mapping_time_step=0.05,
        max_step=max_step,
    )


@lru_cache(maxsize=4)
def corrected_l2_constant_frequency_halo_energy_corrections(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    target_jacobi_values: tuple[float, ...] = (
        3.1182,
        3.1140,
        3.1098,
        3.1056,
        3.1014,
        3.0972,
        3.0930,
        3.0876,
        3.0846,
        3.0804,
        3.0762,
        3.0720,
        3.0678,
        3.0636,
        3.0594,
        3.0552,
        3.0510,
        3.0468,
        3.0426,
        3.0384,
        3.0364,
        3.0342,
        3.0300,
        3.0258,
        3.0216,
        3.0174,
        3.0132,
        3.0090,
        3.0048,
        3.0011,
    ),
    initial_samples: int = 15,
    maximum_samples: int = 213,
    maximum_jacobi_step: float = 1.05e-3,
    max_iterations: int = 32,
    map_tolerance: float = 1.0e-7,
    energy_tolerance: float = 5.0e-8,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FixedFrequencyEnergyCurveCorrection, ...]:
    """Return the thesis-scale fixed-frequency quasi-halo branch.

    Target Jacobi values are reached through small energy steps. The curve is
    spectrally lifted by six nodes whenever the current collocation resolution
    cannot satisfy both mapping and pointwise-energy residual thresholds.
    """

    targets = tuple(float(value) for value in target_jacobi_values)
    if not targets or not np.all(np.diff(targets) < 0.0):
        raise ValueError("target_jacobi_values must be strictly decreasing")
    if initial_samples < 15 or initial_samples % 2 == 0:
        raise ValueError("initial_samples must be odd and at least 15")
    if maximum_samples < initial_samples or maximum_samples % 2 == 0:
        raise ValueError("maximum_samples must be odd and no smaller than initial_samples")
    if maximum_jacobi_step <= 0.0:
        raise ValueError("maximum_jacobi_step must be positive")

    parameters: dict[str, object] = {
        "version": _FIXED_FREQUENCY_CACHE_VERSION,
        "mu": float(mu),
        "target_frequency_ratio": float(target_frequency_ratio),
        "target_jacobi_values": targets,
        "initial_samples": int(initial_samples),
        "maximum_samples": int(maximum_samples),
        "maximum_jacobi_step": float(maximum_jacobi_step),
        "max_iterations": int(max_iterations),
        "map_tolerance": float(map_tolerance),
        "energy_tolerance": float(energy_tolerance),
        "max_step": float(max_step),
    }
    cache_path = _fixed_frequency_cache_path("halo_energy", parameters)
    family: list[FixedFrequencyEnergyCurveCorrection] = []
    if persistent_cache and cache_path.exists():
        try:
            with cache_path.open("rb") as stream:
                cached = pickle.load(stream)
        except (OSError, pickle.PickleError, EOFError):
            cached = ()
        if (
            isinstance(cached, tuple)
            and len(cached) <= len(targets)
            and all(
                isinstance(correction, FixedFrequencyEnergyCurveCorrection)
                and abs(correction.target_jacobi - targets[index]) < 1.0e-12
                and correction.final_residual_norms.max() < map_tolerance
                and np.max(np.abs(correction.energy_residual_history[-1]))
                < energy_tolerance
                for index, correction in enumerate(cached)
            )
        ):
            family.extend(cached)
    if persistent_cache and cache_path.parent.exists() and len(family) < len(targets):
        for candidate_path in cache_path.parent.glob(
            f"fixed_frequency_halo_energy_v{_FIXED_FREQUENCY_CACHE_VERSION}_*.pkl"
        ):
            if candidate_path == cache_path:
                continue
            try:
                with candidate_path.open("rb") as stream:
                    candidate = pickle.load(stream)
            except (OSError, pickle.PickleError, EOFError):
                continue
            if not isinstance(candidate, tuple) or len(candidate) <= len(family):
                continue
            if len(candidate) > len(targets):
                continue
            if not all(
                isinstance(correction, FixedFrequencyEnergyCurveCorrection)
                and abs(correction.seed.mu - mu) < 1.0e-15
                and abs(
                    2.0 * np.pi / correction.rotation_angle_rad
                    - target_frequency_ratio
                )
                < 1.0e-10
                and abs(correction.target_jacobi - targets[index]) < 1.0e-12
                and correction.final_residual_norms.max() < map_tolerance
                and np.max(np.abs(correction.energy_residual_history[-1]))
                < energy_tolerance
                for index, correction in enumerate(candidate)
            ):
                continue
            family = list(candidate)
    if len(family) == len(targets):
        return tuple(family)

    if family:
        reference: (
            FreeMappingTimeCurveCorrection
            | FixedFrequencyPseudoArclengthCorrection
            | FixedFrequencyEnergyCurveCorrection
        ) = family[-1]
        start_index = len(family)
    else:
        base = corrected_l2_constant_frequency_halo_pseudo_arclength_corrections(
            mu,
            target_frequency_ratio=target_frequency_ratio,
            max_step=max_step,
        )
        base_jacobi = np.array(
            [float(np.mean(jacobi_constant(item.corrected_states, mu))) for item in base]
        )
        reference = base[int(np.argmin(np.abs(base_jacobi - targets[0])))]
        if initial_samples > reference.corrected_states.shape[0]:
            reference = _lift_l2_constant_frequency_halo_correction(
                reference,
                samples=initial_samples,
                target_frequency_ratio=target_frequency_ratio,
                max_iterations=max_iterations,
                max_step=max_step,
            )
        start_index = 0

    def converged(correction: FixedFrequencyEnergyCurveCorrection) -> bool:
        return bool(
            correction.final_residual_norms.max() < map_tolerance
            and np.max(np.abs(correction.energy_residual_history[-1])) < energy_tolerance
            and abs(correction.longitudinal_phase_residual_history[-1]) < 1.0e-10
            and abs(correction.latitudinal_phase_residual_history[-1]) < 1.0e-10
        )

    for target_index in range(start_index, len(targets)):
        target = targets[target_index]
        while True:
            current_jacobi = float(np.mean(jacobi_constant(reference.corrected_states, mu)))
            remaining = current_jacobi - target
            if remaining <= 1.0e-12:
                break
            proposed_step = min(maximum_jacobi_step, remaining)
            while True:
                internal_target = current_jacobi - proposed_step
                candidate = stroboscopic_curve_fixed_frequency_energy_correction(
                    reference,
                    target_jacobi=float(internal_target),
                    max_iterations=max_iterations,
                    tolerance=map_tolerance,
                    energy_tolerance=energy_tolerance,
                    max_step=max_step,
                )
                if converged(candidate):
                    reference = candidate
                    break
                candidate_energy = float(
                    np.max(np.abs(candidate.energy_residual_history[-1]))
                )
                if candidate_energy >= 10.0 * energy_tolerance:
                    proposed_step *= 0.5
                    if proposed_step < 1.0e-5:
                        raise RuntimeError(
                            "Fixed-frequency quasi-halo energy step collapsed at "
                            f"JC={internal_target:.7f}; "
                            f"map={candidate.final_residual_norms.max():.3e}, "
                            f"energy={candidate_energy:.3e}"
                        )
                    continue
                current_samples = reference.corrected_states.shape[0]
                next_samples = current_samples + 6
                if next_samples > maximum_samples:
                    raise RuntimeError(
                        "Fixed-frequency quasi-halo energy continuation exceeded "
                        f"N={maximum_samples} at JC={internal_target:.7f}; "
                        f"map={candidate.final_residual_norms.max():.3e}, "
                        "energy="
                        f"{np.max(np.abs(candidate.energy_residual_history[-1])):.3e}"
                    )
                reference = _lift_l2_constant_frequency_halo_correction(
                    reference,
                    samples=next_samples,
                    target_frequency_ratio=target_frequency_ratio,
                    max_iterations=max_iterations,
                    max_step=max_step,
                )
        if not isinstance(reference, FixedFrequencyEnergyCurveCorrection):
            raise RuntimeError("Energy continuation did not produce a corrected target")
        family.append(reference)
        if persistent_cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".tmp")
            with temporary.open("wb") as stream:
                pickle.dump(tuple(family), stream, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.replace(cache_path)
    return tuple(family)


@lru_cache(maxsize=4)
def corrected_l2_constant_frequency_vertical_pseudo_arclength_corrections(
    mu: float,
    *,
    target_frequency_ratio: float = 9.441,
    members: int = 25,
    samples: int = 9,
    maximum_step_size: float = 0.04,
    max_iterations: int = 80,
    tolerance: float = 3.0e-9,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeMappingTimeCurveCorrection | FixedFrequencyPseudoArclengthCorrection, ...]:
    """Continue the physical L2 fixed-frequency quasi-vertical branch."""

    if samples != 9:
        raise ValueError("The base fixed-frequency quasi-vertical branch uses samples=9")
    parameters: dict[str, object] = {
        "version": _FIXED_FREQUENCY_CACHE_VERSION,
        "mu": float(mu),
        "target_frequency_ratio": float(target_frequency_ratio),
        "members": int(members),
        "samples": int(samples),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _fixed_frequency_cache_path("vertical_n9", parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if isinstance(cached, tuple) and len(cached) == members:
            return cached

    seed = stroboscopic_spatial_frequency_seed(
        mu,
        target_frequency_ratio=target_frequency_ratio,
        z_bracket=(0.195, 0.200),
        point="L2",
        vertical_mode=True,
        mode_component=0,
        mode_amplitude=1.0e-5,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    natural = corrected_fixed_frequency_curve_family(
        seed,
        target_frequency_ratio=target_frequency_ratio,
        mode_amplitudes=(1.0e-5, 2.0e-5, 4.0e-5, 8.0e-5),
        max_iterations=max_iterations,
        max_step=max_step,
    )
    anchors = natural[-2:]
    if max(anchor.final_residual_norms.max() for anchor in anchors) >= 1.0e-9:
        raise RuntimeError("Fixed-frequency quasi-vertical anchors did not converge")
    family = tuple(
        corrected_fixed_frequency_pseudo_arclength_family(
            anchors,
            members=members,
            maximum_step_size=maximum_step_size,
            max_iterations=max_iterations,
            tolerance=tolerance,
            max_step=max_step,
        )
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(family, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return family


def corrected_constant_energy_curve_family(
    seed: StroboscopicInvariantCurveSeed,
    *,
    target_jacobi: float,
    mode_amplitudes: tuple[float, ...],
    max_iterations: int = 18,
    max_step: float = 0.01,
) -> list[FreeEnergyCurveCorrection]:
    """Continue a local invariant-curve family at fixed mean Jacobi constant."""

    amplitudes = tuple(float(value) for value in mode_amplitudes)
    if not amplitudes or any(value <= 0.0 for value in amplitudes):
        raise ValueError("mode_amplitudes must contain positive values")
    if any(a >= b for a, b in zip(amplitudes, amplitudes[1:])):
        raise ValueError("mode_amplitudes must be strictly increasing")

    family: list[FreeEnergyCurveCorrection] = []
    previous_amplitude = seed.mode_amplitude
    for amplitude in amplitudes:
        if family:
            previous = family[-1]
            scale = amplitude / previous_amplitude
            initial_states = seed.orbit_state + scale * (
                previous.corrected_states - seed.orbit_state
            )
            initial_mapping_time = previous.mapping_time
            initial_rotation = previous.rotation_angle_rad
        else:
            scale = amplitude / seed.mode_amplitude
            initial_states = seed.orbit_state + scale * (
                seed.initial_states - seed.orbit_state
            )
            initial_mapping_time = seed.orbit_period
            initial_rotation = seed.rotation_angle_rad

        correction = stroboscopic_curve_free_energy_correction(
            seed,
            target_jacobi=target_jacobi,
            target_amplitude=amplitude,
            amplitude_component=seed.mode_component,
            initial_states=initial_states,
            initial_mapping_time=initial_mapping_time,
            initial_rotation_angle_rad=initial_rotation,
            phase_reference_states=initial_states,
            max_iterations=max_iterations,
            max_step=max_step,
        )
        family.append(correction)
        previous_amplitude = amplitude
    return family


def corrected_l1_constant_energy_halo_family(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    mode_amplitudes: tuple[float, ...] = (2.5e-4, 5.0e-4, 7.5e-4, 1.0e-3),
    samples: int = 9,
    time_samples: int = 24,
    max_iterations: int = 24,
    max_step: float = 0.01,
) -> list[CorrectedStroboscopicTorus]:
    """Return a local corrected L1 quasi-halo family at fixed Jacobi constant."""

    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="halo",
        mode_component=2,
        mode_amplitude=mode_amplitudes[0],
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    corrections = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=target_jacobi,
        mode_amplitudes=mode_amplitudes,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    members: int = 27,
    samples: int = 9,
    maximum_step_size: float = 0.012,
    max_iterations: int = 36,
    tolerance: float = 2.0e-9,
    max_step: float = 0.01,
) -> tuple[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...]:
    """Continue the L1 constant-energy quasi-halo family by pseudo-arclength.

    Four naturally continued members establish the branch and the final two
    seed the phase-projected pseudo-arclength continuation. The default range
    reaches the first two thesis-scale mapping-time examples while retaining a
    strict single-shooting invariance tolerance.
    """

    natural_amplitudes = (2.5e-4, 5.0e-4, 7.5e-4, 1.0e-3)
    if members < len(natural_amplitudes):
        raise ValueError("members must be at least four")
    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="halo",
        mode_component=2,
        mode_amplitude=natural_amplitudes[0],
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    natural = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=target_jacobi,
        mode_amplitudes=natural_amplitudes,
        max_iterations=24,
        max_step=max_step,
    )
    continued = corrected_constant_energy_pseudo_arclength_family(
        natural[-2:],
        members=members - len(natural) + 2,
        maximum_step_size=maximum_step_size,
        max_iterations=max_iterations,
        tolerance=tolerance,
        max_step=max_step,
    )
    return tuple(natural[:-2] + continued)


def corrected_l1_constant_energy_halo_pseudo_arclength_family(
    mu: float,
    *,
    time_samples: int = 16,
    **kwargs,
) -> list[CorrectedStroboscopicTorus]:
    """Sweep the corrected pseudo-arclength quasi-halo branch into torus surfaces."""

    corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
        mu,
        **kwargs,
    )
    max_step = float(kwargs.get("max_step", 0.01))
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_high_order_anchors(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    samples: int = 15,
    max_iterations: int = 48,
    max_step: float = 0.01,
) -> tuple[FreeEnergyCurveCorrection, FreeEnergyCurveCorrection]:
    """Spectrally lift two validated members to the requested odd resolution.

    ``N=15`` is lifted from the final two ``N=9`` members.  Resolutions of
    ``N>=21`` use the last two well-resolved ``N=15`` members, before that
    branch reaches its spectral truncation floor near 12.35 days.
    """

    if samples < 15 or samples % 2 == 0:
        raise ValueError("samples must be odd and at least 15")
    if samples >= 21:
        source_corrections = corrected_l1_constant_energy_halo_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=27,
            samples=15,
            maximum_step_size=0.02,
            max_iterations=max_iterations,
            tolerance=5.0e-10,
            max_step=max_step,
        )[-2:]
    else:
        source_corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
            mu,
            members=27,
        )[-2:]
    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="halo",
        mode_component=2,
        mode_amplitude=1.0e-3,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )

    anchors: list[FreeEnergyCurveCorrection] = []
    for low_order_correction in source_corrections:
        interpolation = _trigonometric_interpolation_matrix(
            low_order_correction.seed.phases,
            seed.phases,
        )
        initial_states = interpolation @ low_order_correction.corrected_states
        component = seed.mode_component
        displacement = initial_states[:, component] - seed.orbit_state[component]
        target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        anchors.append(
            stroboscopic_curve_free_energy_correction(
                seed,
                target_jacobi=target_jacobi,
                target_amplitude=target_amplitude,
                amplitude_component=component,
                initial_states=initial_states,
                initial_mapping_time=low_order_correction.mapping_time,
                initial_rotation_angle_rad=low_order_correction.rotation_angle_rad,
                phase_reference_states=initial_states,
                max_iterations=max_iterations,
                max_state_step=5.0e-4,
                max_mapping_time_step=0.02,
                max_rotation_step=0.02,
                max_step=max_step,
            )
        )
    return anchors[0], anchors[1]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_high_order_corrections(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    members: int = 20,
    samples: int = 15,
    maximum_step_size: float = 0.02,
    max_iterations: int = 40,
    tolerance: float = 1.0e-9,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...]:
    """Continue a spectrally lifted fixed-energy quasi-halo branch."""

    cache_parameters: dict[str, float | int] = {
        "version": _HIGH_ORDER_CACHE_VERSION,
        "mu": float(mu),
        "target_jacobi": float(target_jacobi),
        "members": int(members),
        "samples": int(samples),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _high_order_cache_path(cache_parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if (
            isinstance(cached, tuple)
            and len(cached) == members
            and all(
                correction.corrected_states.shape == (samples, 6)
                for correction in cached
            )
        ):
            return cached

    anchors = corrected_l1_constant_energy_halo_high_order_anchors(
        mu,
        target_jacobi=target_jacobi,
        samples=samples,
        max_step=max_step,
    )
    family = corrected_constant_energy_pseudo_arclength_family(
        anchors,
        members=members,
        maximum_step_size=maximum_step_size,
        max_iterations=max_iterations,
        tolerance=tolerance,
        max_step=max_step,
    )
    result = tuple(family)
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(result, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return result


def corrected_l1_constant_energy_halo_high_order_family(
    mu: float,
    *,
    time_samples: int = 20,
    **kwargs,
) -> list[CorrectedStroboscopicTorus]:
    """Sweep the high-order pseudo-arclength branch into torus surfaces."""

    corrections = corrected_l1_constant_energy_halo_high_order_corrections(
        mu,
        **kwargs,
    )
    max_step = float(kwargs.get("max_step", 0.01))
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


def corrected_l1_constant_energy_vertical_family(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    mode_amplitudes: tuple[float, ...] = (2.5e-5, 5.0e-5, 7.5e-5, 1.0e-4),
    samples: int = 9,
    time_samples: int = 24,
    max_iterations: int = 24,
    max_step: float = 0.01,
) -> list[CorrectedStroboscopicTorus]:
    """Return a local corrected L1 quasi-vertical family at fixed Jacobi constant."""

    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="vertical",
        mode_component=0,
        mode_amplitude=mode_amplitudes[0],
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    corrections = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=target_jacobi,
        mode_amplitudes=mode_amplitudes,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_vertical_pseudo_arclength_corrections(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    members: int = 26,
    samples: int = 9,
    maximum_step_size: float = 0.02,
    max_iterations: int = 48,
    tolerance: float = 3.0e-9,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...]:
    """Continue the fixed-energy L1 quasi-vertical branch with ``N=9``."""

    if samples != 9:
        raise ValueError("The base quasi-vertical continuation uses samples=9")
    parameters: dict[str, object] = {
        "version": _VERTICAL_CONTINUATION_CACHE_VERSION,
        "mu": float(mu),
        "target_jacobi": float(target_jacobi),
        "members": int(members),
        "samples": int(samples),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _vertical_continuation_cache_path("n9", parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if isinstance(cached, tuple) and len(cached) == members:
            return cached

    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="vertical",
        mode_component=0,
        mode_amplitude=1.0e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    anchors = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=target_jacobi,
        mode_amplitudes=(1.0e-4, 2.0e-4),
        max_iterations=max_iterations,
        max_step=max_step,
    )
    if max(anchor.final_residual_norms.max() for anchor in anchors) >= 1.0e-9:
        raise RuntimeError("Quasi-vertical natural-parameter anchors did not converge")
    family = tuple(
        corrected_constant_energy_pseudo_arclength_family(
            anchors,
            members=members,
            maximum_step_size=maximum_step_size,
            max_iterations=max_iterations,
            tolerance=tolerance,
            max_step=max_step,
        )
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(family, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return family


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_vertical_high_order_anchors(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    samples: int = 15,
    source_indices: tuple[int, int] = (20, 25),
    max_iterations: int = 64,
    max_step: float = 0.01,
) -> tuple[FreeEnergyCurveCorrection, FreeEnergyCurveCorrection]:
    """Spectrally lift two separated quasi-vertical continuation members.

    ``N=15`` anchors are lifted from the base ``N=9`` branch. Resolutions of
    ``N>=21`` are lifted from the validated 20-member ``N=15`` branch.
    """

    if samples < 15 or samples % 2 == 0:
        raise ValueError("samples must be odd and at least 15")
    if samples >= 33:
        source = corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=32,
            samples=27,
            source_indices=(5, 15),
            maximum_step_size=0.12,
            max_iterations=80,
            tolerance=2.0e-9,
            max_step=max_step,
        )
    elif samples >= 27:
        source = corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=16,
            samples=21,
            source_indices=(14, 19),
            maximum_step_size=0.06,
            max_iterations=72,
            tolerance=5.0e-10,
            max_step=max_step,
        )
    elif samples >= 21:
        source = corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=20,
            samples=15,
            source_indices=(20, 25),
            maximum_step_size=0.04,
            max_iterations=72,
            tolerance=2.0e-9,
            max_step=max_step,
        )
    else:
        source = corrected_l1_constant_energy_vertical_pseudo_arclength_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=26,
            max_step=max_step,
        )
    if not 0 <= source_indices[0] < source_indices[1] < len(source):
        raise ValueError("source_indices must select two ordered source members")
    seed = stroboscopic_spatial_jacobi_seed(
        mu,
        target_jacobi=target_jacobi,
        family_label="vertical",
        mode_component=0,
        mode_amplitude=1.0e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    anchors: list[FreeEnergyCurveCorrection] = []
    for source_index in source_indices:
        correction = source[source_index]
        interpolation = _trigonometric_interpolation_matrix(
            correction.seed.phases,
            seed.phases,
        )
        initial_states = interpolation @ correction.corrected_states
        component = seed.mode_component
        displacement = initial_states[:, component] - seed.orbit_state[component]
        target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        anchors.append(
            stroboscopic_curve_free_energy_correction(
                seed,
                target_jacobi=target_jacobi,
                target_amplitude=target_amplitude,
                amplitude_component=component,
                initial_states=initial_states,
                initial_mapping_time=correction.mapping_time,
                initial_rotation_angle_rad=correction.rotation_angle_rad,
                phase_reference_states=initial_states,
                max_iterations=max_iterations,
                max_state_step=5.0e-4,
                max_mapping_time_step=0.02,
                max_rotation_step=0.02,
                max_step=max_step,
            )
        )
    return anchors[0], anchors[1]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_vertical_high_order_corrections(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    members: int = 24,
    samples: int = 15,
    source_indices: tuple[int, int] = (20, 25),
    maximum_step_size: float = 0.04,
    max_iterations: int = 64,
    tolerance: float = 5.0e-10,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...]:
    """Continue the spectrally lifted fixed-energy quasi-vertical branch."""

    parameters: dict[str, object] = {
        "version": _VERTICAL_CONTINUATION_CACHE_VERSION,
        "mu": float(mu),
        "target_jacobi": float(target_jacobi),
        "members": int(members),
        "samples": int(samples),
        "source_indices": tuple(int(index) for index in source_indices),
        "maximum_step_size": float(maximum_step_size),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "max_step": float(max_step),
    }
    cache_path = _vertical_continuation_cache_path("high_order", parameters)
    resume_family: tuple[
        FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...
    ] | None = None
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if (
            isinstance(cached, tuple)
            and len(cached) == members
            and all(correction.corrected_states.shape == (samples, 6) for correction in cached)
        ):
            return cached
    if persistent_cache:
        cache_directory = cache_path.parent
        if cache_directory.exists():
            for candidate in cache_directory.glob(
                f"quasi_vertical_high_order_v{_VERTICAL_CONTINUATION_CACHE_VERSION}_*.pkl"
            ):
                try:
                    with candidate.open("rb") as stream:
                        cached = pickle.load(stream)
                except (OSError, pickle.PickleError, EOFError):
                    continue
                if not isinstance(cached, tuple) or not 2 <= len(cached) < members:
                    continue
                if not all(
                    correction.corrected_states.shape == (samples, 6)
                    and abs(correction.seed.mu - mu) < 1.0e-15
                    and abs(correction.target_jacobi - target_jacobi) < 1.0e-13
                    for correction in cached
                ):
                    continue
                if resume_family is None or len(cached) > len(resume_family):
                    resume_family = cached

    anchors = (
        resume_family
        if resume_family is not None
        else corrected_l1_constant_energy_vertical_high_order_anchors(
            mu,
            target_jacobi=target_jacobi,
            samples=samples,
            source_indices=source_indices,
            max_iterations=max_iterations,
            max_step=max_step,
        )
    )
    family = tuple(
        corrected_constant_energy_pseudo_arclength_family(
            anchors,
            members=members,
            maximum_step_size=maximum_step_size,
            max_iterations=max_iterations,
            tolerance=tolerance,
            max_step=max_step,
        )
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(family, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return family


def corrected_l1_constant_energy_vertical_high_order_family(
    mu: float,
    *,
    time_samples: int = 24,
    **kwargs,
) -> list[CorrectedStroboscopicTorus]:
    """Sweep the high-order quasi-vertical branch into torus surfaces."""

    corrections = corrected_l1_constant_energy_vertical_high_order_corrections(
        mu,
        **kwargs,
    )
    max_step = float(kwargs.get("max_step", 0.01))
    return [
        _sweep_corrected_curve_correction(
            correction,
            time_samples=time_samples,
            max_step=max_step,
        )
        for correction in corrections
    ]


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_vertical_staged_corrections(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
) -> tuple[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection, ...]:
    """Return the validated staged quasi-vertical branch through 12.66 days."""

    branches = (
        corrected_l1_constant_energy_vertical_pseudo_arclength_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=26,
            samples=9,
            maximum_step_size=0.02,
            max_iterations=48,
            tolerance=3.0e-9,
        ),
        corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=20,
            samples=15,
            source_indices=(20, 25),
            maximum_step_size=0.04,
            max_iterations=72,
            tolerance=2.0e-9,
        ),
        corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=16,
            samples=21,
            source_indices=(14, 19),
            maximum_step_size=0.06,
            max_iterations=72,
            tolerance=5.0e-10,
        ),
        corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=32,
            samples=27,
            source_indices=(5, 15),
            maximum_step_size=0.12,
            max_iterations=80,
            tolerance=2.0e-9,
        ),
        corrected_l1_constant_energy_vertical_high_order_corrections(
            mu,
            target_jacobi=target_jacobi,
            members=20,
            samples=33,
            source_indices=(15, 31),
            maximum_step_size=0.15,
            max_iterations=96,
            tolerance=5.0e-10,
        ),
    )
    n9, n15, n21, n27, n33 = branches
    candidates = [
        *(correction for correction in n9 if correction.mapping_time > n15[0].mapping_time),
        *n15,
        *(correction for correction in n21 if correction.mapping_time < n15[-1].mapping_time),
        *(correction for correction in n27 if correction.mapping_time < n21[-1].mapping_time),
        *(
            correction
            for correction in n33
            if correction.mapping_time < n27[-1].mapping_time
        ),
    ]
    staged: list[FreeEnergyCurveCorrection | PseudoArclengthCurveCorrection] = []
    for correction in candidates:
        if correction.final_residual_norms.max() >= 3.1e-9:
            continue
        if staged and correction.mapping_time >= staged[-1].mapping_time - 1.0e-10:
            continue
        staged.append(correction)
    return tuple(staged)


def corrected_dro_stroboscopic_torus(
    mu: float,
    *,
    x0: float,
    samples: int = 11,
    time_samples: int = 36,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    vertical_amplitude: float = 1e-4,
    max_iterations: int = 2,
    max_step: float = 0.01,
) -> CorrectedStroboscopicTorus:
    """Sweep a corrected vertical-mode invariant curve around a planar DRO."""

    if samples % 2 == 0:
        raise ValueError("samples must be odd for trigonometric interpolation")
    seed = stroboscopic_dro_invariant_curve_seed(
        mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=vertical_amplitude,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    return _corrected_torus_from_seed(
        seed,
        time_samples=time_samples,
        max_iterations=max_iterations,
        max_step=max_step,
    )


def corrected_dro_fixed_mapping_family(
    mu: float,
    *,
    x0: float,
    vertical_amplitudes: tuple[float, ...] = (1e-3, 5e-3, 1e-2, 1.25e-2, 1.5e-2, 1.75e-2, 2e-2),
    samples: int = 11,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    max_iterations: int = 8,
    max_step: float = 0.01,
) -> list[FreeRotationCurveCorrection]:
    """Continue a fixed-mapping-time quasi-DRO family in vertical amplitude."""

    if samples % 2 == 0:
        raise ValueError("samples must be odd for trigonometric interpolation")
    amplitudes = tuple(float(value) for value in vertical_amplitudes)
    if not amplitudes or any(value <= 0.0 for value in amplitudes):
        raise ValueError("vertical_amplitudes must contain positive values")
    if any(a >= b for a, b in zip(amplitudes, amplitudes[1:])):
        raise ValueError("vertical_amplitudes must be strictly increasing")

    family: list[FreeRotationCurveCorrection] = []
    previous_amplitude: float | None = None
    for amplitude in amplitudes:
        seed = stroboscopic_dro_invariant_curve_seed(
            mu,
            x0=x0,
            initial_ydot=initial_ydot,
            initial_half_period=initial_half_period,
            vertical_amplitude=amplitude,
            samples=samples,
            curve_samples=max(4 * samples, 120),
        )
        initial_states = None
        initial_rotation = None
        if family and previous_amplitude is not None:
            initial_states = family[-1].corrected_states.copy()
            scale = amplitude / previous_amplitude
            for component in (seed.mode_component, seed.mode_component + 3):
                initial_states[:, component] = seed.orbit_state[component] + scale * (
                    initial_states[:, component] - seed.orbit_state[component]
                )
            initial_rotation = family[-1].rotation_angle_rad

        correction = stroboscopic_curve_free_rotation_correction(
            seed,
            target_amplitude=amplitude,
            amplitude_component=seed.mode_component,
            initial_states=initial_states,
            initial_rotation_angle_rad=initial_rotation,
            phase_reference_states=initial_states,
            max_iterations=max_iterations,
            max_step=max_step,
        )
        family.append(correction)
        previous_amplitude = amplitude
    return family


def _lift_dro_fixed_mapping_correction(
    correction: FreeRotationCurveCorrection | FixedMappingPseudoArclengthCorrection,
    *,
    x0: float,
    samples: int,
    initial_ydot: float,
    initial_half_period: float,
    max_iterations: int,
    map_tolerance: float,
    max_step: float,
) -> FreeRotationCurveCorrection:
    """Spectrally lift one fixed-mapping-time quasi-DRO invariant curve."""

    source_samples = correction.corrected_states.shape[0]
    if samples <= source_samples or samples % 2 == 0:
        raise ValueError("samples must be an odd value above the source resolution")
    seed = stroboscopic_dro_invariant_curve_seed(
        correction.seed.mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=1e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    interpolation = _trigonometric_interpolation_matrix(
        correction.seed.phases,
        seed.phases,
    )
    initial_states = interpolation @ correction.corrected_states
    displacement = initial_states[:, seed.mode_component] - seed.orbit_state[seed.mode_component]
    target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return stroboscopic_curve_free_rotation_correction(
        seed,
        target_amplitude=target_amplitude,
        initial_states=initial_states,
        initial_rotation_angle_rad=correction.rotation_angle_rad,
        phase_reference_states=initial_states,
        max_iterations=max_iterations,
        tolerance=map_tolerance,
        max_step=max_step,
        max_state_step=1e-3,
    )


def _lift_dro_fixed_rotation_correction(
    correction: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
    *,
    x0: float,
    samples: int,
    initial_ydot: float,
    initial_half_period: float,
    max_iterations: int,
    map_tolerance: float,
    max_step: float,
) -> FixedRotationCurveCorrection:
    """Spectrally lift a fixed-rotation quasi-DRO curve."""

    if samples <= correction.corrected_states.shape[0] or samples % 2 == 0:
        raise ValueError("samples must be an odd value above the source resolution")
    seed = stroboscopic_dro_invariant_curve_seed(
        correction.seed.mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=1e-4,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    interpolation = _trigonometric_interpolation_matrix(
        correction.seed.phases,
        seed.phases,
    )
    initial_states = interpolation @ correction.corrected_states
    return stroboscopic_curve_fixed_rotation_correction(
        seed,
        target_rotation_angle_rad=correction.rotation_angle_rad,
        initial_states=initial_states,
        phase_reference_states=initial_states,
        max_iterations=max_iterations,
        tolerance=map_tolerance,
        max_step=max_step,
        max_state_step=1e-3,
    )


@lru_cache(maxsize=4)
def corrected_dro_fixed_mapping_full_corrections(
    mu: float,
    *,
    x0: float,
    thesis_jacobi_targets: tuple[float, ...] = (2.9221, 2.9215, 2.9212),
    initial_samples: int = 21,
    maximum_samples: int = 141,
    initial_amplitude: float = 1e-3,
    amplitude_step: float = 2.5e-3,
    minimum_amplitude_step: float = 1.25e-4,
    jacobi_target_tolerance: float = 5e-7,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    max_iterations: int = 16,
    map_tolerance: float = 1e-8,
    jacobi_span_tolerance: float = 2e-8,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[
    FreeRotationCurveCorrection | FixedRotationCurveCorrection,
    ...,
]:
    """Return the thesis-scale constant-mapping-time quasi-DRO family.

    Vertical-amplitude continuation is adaptively shortened when Newton fails
    and spectrally lifted when map closure or pointwise Jacobi consistency hits
    a collocation floor. When the branch crosses a thesis Jacobi value, a local
    secant in amplitude inserts a corrected member at that target.
    """

    targets = tuple(float(value) for value in thesis_jacobi_targets)
    if not targets or not np.all(np.diff(targets) < 0.0):
        raise ValueError("thesis_jacobi_targets must be strictly decreasing")
    if initial_samples < 9 or initial_samples % 2 == 0:
        raise ValueError("initial_samples must be odd and at least 9")
    if maximum_samples < initial_samples or maximum_samples % 2 == 0:
        raise ValueError("maximum_samples must be odd and no smaller than initial_samples")
    if not 0.0 < minimum_amplitude_step <= amplitude_step:
        raise ValueError("amplitude step bounds must be positive and ordered")

    parameters: dict[str, object] = {
        "version": _FIXED_MAPPING_DRO_CACHE_VERSION,
        "mu": float(mu),
        "x0": float(x0),
        "thesis_jacobi_targets": targets,
        "initial_samples": int(initial_samples),
        "maximum_samples": int(maximum_samples),
        "initial_amplitude": float(initial_amplitude),
        "amplitude_step": float(amplitude_step),
        "minimum_amplitude_step": float(minimum_amplitude_step),
        "jacobi_target_tolerance": float(jacobi_target_tolerance),
        "initial_ydot": float(initial_ydot),
        "initial_half_period": float(initial_half_period),
        "max_iterations": int(max_iterations),
        "map_tolerance": float(map_tolerance),
        "jacobi_span_tolerance": float(jacobi_span_tolerance),
        "max_step": float(max_step),
    }
    cache_path = _fixed_mapping_dro_cache_path(parameters)
    family: list[FreeRotationCurveCorrection | FixedRotationCurveCorrection] = []

    def mean_jacobi(
        correction: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
    ) -> float:
        return float(np.mean(jacobi_constant(correction.corrected_states, mu)))

    def converged(
        correction: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
    ) -> bool:
        jacobi_span = float(np.ptp(jacobi_constant(correction.corrected_states, mu)))
        if isinstance(correction, FreeRotationCurveCorrection):
            constraints_ok = bool(
                abs(correction.amplitude_residual_history[-1]) < 1e-10
                and abs(correction.phase_residual_history[-1]) < 1e-10
            )
        else:
            constraints_ok = bool(
                abs(correction.phase_residual_history[-1]) < 1e-10
            )
        return bool(
            correction.final_residual_norms.max() < map_tolerance
            and constraints_ok
            and jacobi_span < jacobi_span_tolerance
        )

    if persistent_cache and cache_path.exists():
        try:
            with cache_path.open("rb") as stream:
                cached = pickle.load(stream)
        except (OSError, pickle.PickleError, EOFError):
            cached = ()
        if (
            isinstance(cached, tuple)
            and all(
                isinstance(
                    correction,
                    (FreeRotationCurveCorrection, FixedRotationCurveCorrection),
                )
                and converged(correction)
                for correction in cached
            )
            and all(mean_jacobi(a) > mean_jacobi(b) for a, b in zip(cached, cached[1:]))
            and all(
                a.rotation_angle_rad < b.rotation_angle_rad
                for a, b in zip(cached, cached[1:])
            )
        ):
            family.extend(cached)
    if family and mean_jacobi(family[-1]) <= targets[-1] + jacobi_target_tolerance:
        return tuple(family)

    if family:
        reference = family[-1]
    else:
        seed = stroboscopic_dro_invariant_curve_seed(
            mu,
            x0=x0,
            initial_ydot=initial_ydot,
            initial_half_period=initial_half_period,
            vertical_amplitude=initial_amplitude,
            samples=initial_samples,
            curve_samples=max(4 * initial_samples, 120),
        )
        reference = stroboscopic_curve_free_rotation_correction(
            seed,
            target_amplitude=initial_amplitude,
            max_iterations=max_iterations,
            tolerance=map_tolerance,
            max_step=max_step,
        )
        family.append(reference)

    def corrected_at_amplitude(
        source: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
        target_amplitude: float,
    ) -> FreeRotationCurveCorrection:
        seed = stroboscopic_dro_invariant_curve_seed(
            mu,
            x0=x0,
            initial_ydot=initial_ydot,
            initial_half_period=initial_half_period,
            vertical_amplitude=target_amplitude,
            samples=source.corrected_states.shape[0],
            curve_samples=max(4 * source.corrected_states.shape[0], 120),
        )
        predecessor = family[-2] if len(family) >= 2 and family[-1] is source else None
        if predecessor is not None and predecessor.target_amplitude < source.target_amplitude:
            interpolation = _trigonometric_interpolation_matrix(
                predecessor.seed.phases,
                source.seed.phases,
            )
            predecessor_states = interpolation @ predecessor.corrected_states
            ratio = (target_amplitude - source.target_amplitude) / (
                source.target_amplitude - predecessor.target_amplitude
            )
            initial_states = source.corrected_states + ratio * (
                source.corrected_states - predecessor_states
            )
        else:
            initial_states = source.corrected_states.copy()
            scale = target_amplitude / source.target_amplitude
            for component in (seed.mode_component, seed.mode_component + 3):
                initial_states[:, component] = seed.orbit_state[component] + scale * (
                    initial_states[:, component] - seed.orbit_state[component]
                )
        return stroboscopic_curve_free_rotation_correction(
            seed,
            target_amplitude=target_amplitude,
            initial_states=initial_states,
            initial_rotation_angle_rad=source.rotation_angle_rad,
            phase_reference_states=initial_states,
            max_iterations=max_iterations,
            tolerance=map_tolerance,
            max_step=max_step,
        )

    def corrected_at_rotation(
        lower: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
        upper: FreeRotationCurveCorrection | FixedRotationCurveCorrection,
        target_rotation: float,
    ) -> FixedRotationCurveCorrection:
        seed = stroboscopic_dro_invariant_curve_seed(
            mu,
            x0=x0,
            initial_ydot=initial_ydot,
            initial_half_period=initial_half_period,
            vertical_amplitude=1e-4,
            samples=upper.corrected_states.shape[0],
            curve_samples=max(4 * upper.corrected_states.shape[0], 120),
        )
        interpolation = _trigonometric_interpolation_matrix(
            lower.seed.phases,
            upper.seed.phases,
        )
        lower_states = interpolation @ lower.corrected_states
        fraction = (target_rotation - lower.rotation_angle_rad) / (
            upper.rotation_angle_rad - lower.rotation_angle_rad
        )
        initial_states = lower_states + fraction * (upper.corrected_states - lower_states)
        return stroboscopic_curve_fixed_rotation_correction(
            seed,
            target_rotation_angle_rad=target_rotation,
            initial_states=initial_states,
            phase_reference_states=initial_states,
            max_iterations=max_iterations,
            tolerance=map_tolerance,
            max_step=max_step,
        )

    remaining_targets = [target for target in targets if target < mean_jacobi(reference)]
    rotation_mode = isinstance(reference, FixedRotationCurveCorrection)
    rotation_maximum_step: float | None = None
    if rotation_mode:
        if len(family) < 2:
            raise RuntimeError("Fixed-rotation cache requires two fixed-mapping anchors")
        step = max(
            0.25 * (family[-1].rotation_angle_rad - family[-2].rotation_angle_rad),
            2e-8,
        )
        rotation_maximum_step = 5e-4
    else:
        step = amplitude_step
    while remaining_targets:
        previous = reference
        if rotation_mode:
            candidate = corrected_at_rotation(
                family[-2],
                family[-1],
                previous.rotation_angle_rad + step,
            )
        else:
            candidate = corrected_at_amplitude(previous, previous.target_amplitude + step)
        candidate_jacobi = mean_jacobi(candidate)
        branch_ok = (
            converged(candidate)
            and candidate.rotation_angle_rad > previous.rotation_angle_rad
            and candidate_jacobi < mean_jacobi(previous)
        )
        if not branch_ok:
            if rotation_mode:
                candidate_span = float(
                    np.ptp(jacobi_constant(candidate.corrected_states, mu))
                )
                rotation_spectral_floor = bool(
                    abs(candidate.phase_residual_history[-1]) < 1e-10
                    and candidate.final_residual_norms.max() < map_tolerance
                    and candidate_span >= jacobi_span_tolerance
                )
                if rotation_spectral_floor:
                    next_samples = previous.corrected_states.shape[0] + 12
                    if next_samples > maximum_samples:
                        raise RuntimeError(
                            "Fixed-rotation quasi-DRO continuation exceeded "
                            f"N={maximum_samples} at rho={candidate.rotation_angle_rad:.7f}"
                        )
                    lifted_previous = _lift_dro_fixed_rotation_correction(
                        family[-2],
                        x0=x0,
                        samples=next_samples,
                        initial_ydot=initial_ydot,
                        initial_half_period=initial_half_period,
                        max_iterations=max_iterations,
                        map_tolerance=map_tolerance,
                        max_step=max_step,
                    )
                    lifted_current = _lift_dro_fixed_rotation_correction(
                        family[-1],
                        x0=x0,
                        samples=next_samples,
                        initial_ydot=initial_ydot,
                        initial_half_period=initial_half_period,
                        max_iterations=max_iterations,
                        map_tolerance=map_tolerance,
                        max_step=max_step,
                    )
                    if not converged(lifted_previous) or not converged(lifted_current):
                        raise RuntimeError(
                            f"Fixed-rotation spectral anchors failed at N={next_samples}"
                        )
                    family[-2:] = [lifted_previous, lifted_current]
                    reference = lifted_current
                    continue
                step *= 0.5
                if step < 2e-8:
                    raise RuntimeError(
                        "Fixed-mapping rotation continuation lost monotonic direction at "
                        f"JC={candidate_jacobi:.7f}"
                    )
                continue
            numerical_constraints_ok = bool(
                abs(candidate.amplitude_residual_history[-1]) < 1e-10
                and abs(candidate.phase_residual_history[-1]) < 1e-10
            )
            candidate_span = float(np.ptp(jacobi_constant(candidate.corrected_states, mu)))
            spectral_floor = bool(
                numerical_constraints_ok
                and candidate.final_residual_norms.max() < map_tolerance
                and candidate_span >= jacobi_span_tolerance
            )
            if spectral_floor:
                next_samples = previous.corrected_states.shape[0] + 12
                if next_samples > maximum_samples:
                    raise RuntimeError(
                        "Fixed-mapping quasi-DRO continuation exceeded "
                        f"N={maximum_samples} at amplitude={candidate.target_amplitude:.6f}"
                    )
                reference = _lift_dro_fixed_mapping_correction(
                    previous,
                    x0=x0,
                    samples=next_samples,
                    initial_ydot=initial_ydot,
                    initial_half_period=initial_half_period,
                    max_iterations=max_iterations,
                    map_tolerance=map_tolerance,
                    max_step=max_step,
                )
                if not converged(reference):
                    raise RuntimeError(
                        f"Spectral lift did not recover the quasi-DRO curve at N={next_samples}"
                    )
                family[-1] = reference
                continue
            step *= 0.5
            if step < minimum_amplitude_step:
                if (
                    len(family) < 2
                    or family[-2].corrected_states.shape != family[-1].corrected_states.shape
                ):
                    next_samples = previous.corrected_states.shape[0] + 12
                    if next_samples > maximum_samples:
                        raise RuntimeError(
                            "Fixed-mapping quasi-DRO has no compatible rotation anchors "
                            f"at N={maximum_samples}"
                        )
                    reference = _lift_dro_fixed_mapping_correction(
                        previous,
                        x0=x0,
                        samples=next_samples,
                        initial_ydot=initial_ydot,
                        initial_half_period=initial_half_period,
                        max_iterations=max_iterations,
                        map_tolerance=map_tolerance,
                        max_step=max_step,
                    )
                    if not converged(reference):
                        raise RuntimeError(
                            "Spectral lift did not recover a fixed-rotation anchor at "
                            f"N={next_samples}"
                        )
                    family[-1] = reference
                    step = minimum_amplitude_step
                    continue
                rotation_step = max(
                    0.25
                    * (
                        family[-1].rotation_angle_rad
                        - family[-2].rotation_angle_rad
                    ),
                    2e-8,
                )
                if rotation_step <= 0.0:
                    raise RuntimeError(
                        "Fixed-mapping quasi-DRO rotation anchor is degenerate"
                    )
                rotation_mode = True
                step = rotation_step
                rotation_maximum_step = 5e-4
            continue

        crossed = [
            target
            for target in remaining_targets
            if mean_jacobi(previous) > target >= candidate_jacobi
        ]
        for target in crossed:
            lower = previous
            upper = candidate
            targeted = candidate
            for _ in range(5):
                lower_jacobi = mean_jacobi(lower)
                upper_jacobi = mean_jacobi(upper)
                fraction = (lower_jacobi - target) / (lower_jacobi - upper_jacobi)
                if rotation_mode:
                    target_rotation = lower.rotation_angle_rad + fraction * (
                        upper.rotation_angle_rad - lower.rotation_angle_rad
                    )
                    targeted = corrected_at_rotation(lower, upper, target_rotation)
                else:
                    target_amplitude = lower.target_amplitude + fraction * (
                        upper.target_amplitude - lower.target_amplitude
                    )
                    targeted = corrected_at_amplitude(lower, target_amplitude)
                targeted_jacobi = mean_jacobi(targeted)
                if not converged(targeted):
                    break
                if abs(targeted_jacobi - target) < jacobi_target_tolerance:
                    break
                if targeted_jacobi > target:
                    lower = targeted
                else:
                    upper = targeted
            if not converged(targeted) or abs(mean_jacobi(targeted) - target) >= jacobi_target_tolerance:
                raise RuntimeError(f"Failed to target thesis quasi-DRO JC={target:.7f}")
            family.append(targeted)
            remaining_targets.remove(target)
        family.append(candidate)
        reference = candidate
        if rotation_mode:
            step = min(rotation_maximum_step or step, step * 1.20)
        else:
            step = min(amplitude_step, step * 1.25)
        if persistent_cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".tmp")
            with temporary.open("wb") as stream:
                pickle.dump(tuple(family), stream, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.replace(cache_path)
    return tuple(family)


def corrected_dro_free_rotation_torus(
    mu: float,
    *,
    x0: float,
    samples: int = 15,
    time_samples: int = 36,
    initial_ydot: float = 0.53,
    initial_half_period: float = 1.70,
    vertical_amplitude: float = 1e-2,
    max_iterations: int = 8,
    max_step: float = 0.01,
) -> CorrectedStroboscopicTorus:
    """Return a finite-amplitude fixed-time quasi-DRO with solved rotation."""

    seed = stroboscopic_dro_invariant_curve_seed(
        mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=vertical_amplitude,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    correction = stroboscopic_curve_free_rotation_correction(
        seed,
        target_amplitude=vertical_amplitude,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return _sweep_corrected_curve_correction(
        correction,
        time_samples=time_samples,
        max_step=max_step,
    )


def _ellipse_2d(
    center: np.ndarray,
    radius_x: float,
    radius_y: float,
    *,
    samples: int = 180,
    tilt_rad: float = 0.0,
) -> np.ndarray:
    angle = np.linspace(0.0, 2.0 * np.pi, samples)
    local = np.column_stack([radius_x * np.cos(angle), radius_y * np.sin(angle)])
    rotation = np.array(
        [
            [np.cos(tilt_rad), -np.sin(tilt_rad)],
            [np.sin(tilt_rad), np.cos(tilt_rad)],
        ]
    )
    return center[:2] + local @ rotation.T


def _z_zero_crossings(states: np.ndarray) -> list[np.ndarray]:
    crossings: list[np.ndarray] = []
    z = states[:, 2]
    for idx in range(len(z) - 1):
        if z[idx] == 0.0:
            crossings.append(states[idx, :3])
        elif z[idx] * z[idx + 1] < 0.0:
            weight = abs(z[idx]) / (abs(z[idx]) + abs(z[idx + 1]))
            crossings.append((1.0 - weight) * states[idx, :3] + weight * states[idx + 1, :3])
    return crossings


def central_periodic_orbit_scene(
    mu: float,
    *,
    lyapunov_amplitudes: list[float] | np.ndarray | None = None,
    halo_z_amplitudes: list[float] | np.ndarray | None = None,
    vertical_z_amplitudes: list[float] | np.ndarray | None = None,
    orbit_samples: int = 420,
    map_samples: int = 180,
) -> CentralPeriodicOrbitScene:
    """Return corrected central-orbit content for the Figure 3.11 scene.

    The Lyapunov, halo-like, and vertical-seed orbits are corrected CR3BP
    periodic orbits. The red Poincare island contours are local visual contours
    anchored at the corrected halo family's ``z=0`` section crossings; the full
    invariant-curve map correction is a later reproduction layer.
    """

    if lyapunov_amplitudes is None:
        lyapunov_amplitudes = [0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.020, 0.024, 0.028]
    if halo_z_amplitudes is None:
        halo_z_amplitudes = [0.005, 0.010, 0.020, 0.030, 0.040, 0.050, 0.060, 0.070]
    if vertical_z_amplitudes is None:
        vertical_z_amplitudes = [0.005, 0.010, 0.020, 0.040, 0.070, 0.100]

    lyapunov_family = planar_lyapunov_family(mu, lyapunov_amplitudes, point="L1")
    halo_family = spatial_symmetric_family(
        mu,
        halo_z_amplitudes,
        point="L1",
        seed_x_amplitude=0.002,
        family_label="halo",
    )
    vertical_family = vertical_symmetric_family(mu, vertical_z_amplitudes, point="L1")

    lyapunov_orbits = tuple(propagate_periodic_orbit(orbit, samples=orbit_samples)[:, :3] for orbit in lyapunov_family)
    map_lyapunov = tuple(curve[:, :2] for curve in lyapunov_orbits)

    halo_orbit = propagate_periodic_orbit(halo_family[-1], samples=orbit_samples)[:, :3]
    vertical_orbit = propagate_periodic_orbit(vertical_family[-1], samples=orbit_samples)[:, :3]

    upper: list[np.ndarray] = []
    lower: list[np.ndarray] = []
    centers: list[np.ndarray] = []
    for idx, orbit in enumerate(halo_family):
        states = propagate_periodic_orbit(orbit, samples=orbit_samples)
        crossings = _z_zero_crossings(states)
        if len(crossings) < 2:
            continue
        positive = max(crossings, key=lambda point: point[1])
        negative = min(crossings, key=lambda point: point[1])
        centers.extend([positive, negative])
        frac = idx / max(1, len(halo_family) - 1)
        radius_x = 0.0025 + 0.0075 * frac
        radius_y = 0.0030 + 0.0125 * frac
        upper.append(_ellipse_2d(positive, radius_x, radius_y, samples=map_samples, tilt_rad=0.18))
        lower.append(_ellipse_2d(negative, radius_x, radius_y, samples=map_samples, tilt_rad=-0.18))

    vertical_crossings = _z_zero_crossings(propagate_periodic_orbit(vertical_family[2], samples=orbit_samples))
    vertical_center = vertical_crossings[0] if vertical_crossings else vertical_family[2].initial_state[:3]

    return CentralPeriodicOrbitScene(
        map_lyapunov=map_lyapunov,
        map_halo_upper=tuple(upper),
        map_halo_lower=tuple(lower),
        lyapunov_orbits=lyapunov_orbits,
        halo_orbit=halo_orbit,
        vertical_orbit=vertical_orbit,
        halo_section_centers=np.array(centers, dtype=float),
        vertical_section_center=np.asarray(vertical_center, dtype=float),
    )


def quasi_halo_parameter_curve(system: CR3BPSystem, samples: int = 50) -> list[dict[str, float]]:
    """Return a thesis-shaped constant-energy quasi-halo parameter curve.

    The values are a first-pass reconstruction of the trends in McCarthy Fig.
    3.6, not a converged invariant-curve continuation. They are kept explicit
    so that the numerical torus solver can replace this source later without
    changing the figure scripts.
    """

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    times = np.linspace(12.04, 12.48, samples)
    frac = (times - times[0]) / (times[-1] - times[0])
    y_amp = 3.22e4 + 9.8e3 * (1.0 - np.exp(-4.0 * frac)) / (1.0 - np.exp(-4.0))
    z_amp = 2.60e4 + (y_amp - y_amp[0]) * (1.00e4 / (y_amp[-1] - y_amp[0]))

    return [
        {
            "mapping_time_days": float(t),
            "y_amplitude_km": float(y),
            "z_amplitude_km": float(z),
            "y_amplitude_nd": float(y / system.length_unit_km),
            "z_amplitude_nd": float(z / system.length_unit_km),
        }
        for t, y, z in zip(times, y_amp, z_amp)
    ]


def quasi_vertical_parameter_curve(system: CR3BPSystem, samples: int = 50) -> list[dict[str, float]]:
    """Return a thesis-shaped constant-energy quasi-vertical parameter curve."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    times = np.linspace(12.64, 12.875, samples)
    frac = (times - times[0]) / (times[-1] - times[0])
    y_amp = 2.0e3 + 4.0e4 * (1.0 - frac**1.85)
    z_amp = 3.58e4 + 3.7e3 * np.sin(0.74 * np.pi * frac) ** 0.95

    return [
        {
            "mapping_time_days": float(t),
            "y_amplitude_km": float(y),
            "z_amplitude_km": float(z),
            "y_amplitude_nd": float(y / system.length_unit_km),
            "z_amplitude_nd": float(z / system.length_unit_km),
        }
        for t, y, z in zip(times, y_amp, z_amp)
    ]


def frequency_ratio_curves(samples: int = 80) -> dict[str, list[dict[str, float]]]:
    """Return first-pass frequency-ratio trends for Fig. 3.9."""

    frac = np.linspace(0.0, 1.0, samples)
    halo_time = 12.04 + 0.44 * frac
    vertical_time = 12.65 + 0.225 * frac
    halo_ratio = 9.6 + 33.8 * (np.exp(3.7 * frac) - 1.0) / (np.exp(3.7) - 1.0)
    vertical_ratio = 14.8 + 33.0 * np.exp(-2.35 * frac)
    return {
        "quasi_halo": [
            {"mapping_time_days": float(t), "frequency_ratio": float(r)}
            for t, r in zip(halo_time, halo_ratio)
        ],
        "quasi_vertical": [
            {"mapping_time_days": float(t), "frequency_ratio": float(r)}
            for t, r in zip(vertical_time, vertical_ratio)
        ],
    }


def constant_frequency_halo_curve(system: CR3BPSystem, samples: int = 50) -> list[dict[str, float]]:
    """Return a first-pass constant-frequency quasi-halo parameter curve."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    times = np.linspace(14.55, 17.75, samples)
    frac = (times - times[0]) / (times[-1] - times[0])
    y_amp = 4.30e4 + 6.95e4 * np.sqrt(frac)
    z_amp = 3.45e4 + 5.85e4 * np.sqrt(frac)
    jacobi = 3.12 - 0.119 * frac**0.62
    return [
        {
            "mapping_time_days": float(t),
            "y_amplitude_km": float(y),
            "z_amplitude_km": float(z),
            "y_amplitude_nd": float(y / system.length_unit_km),
            "z_amplitude_nd": float(z / system.length_unit_km),
            "jacobi": float(j),
        }
        for t, y, z, j in zip(times, y_amp, z_amp, jacobi)
    ]


def constant_frequency_vertical_curve(system: CR3BPSystem, samples: int = 80) -> list[dict[str, float]]:
    """Return a first-pass constant-frequency quasi-vertical parameter curve."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    index = np.linspace(0.0, 700.0, samples)
    frac = index / index[-1]
    smooth = 1.0 / (1.0 + np.exp(-11.0 * (frac - 0.46)))
    jacobi = 3.044 - 0.0155 * smooth - 0.0003 * frac
    mapping_time = 16.90 + 0.36 * smooth
    return [
        {
            "orbit_index": float(i),
            "jacobi": float(j),
            "mapping_time_days": float(t),
        }
        for i, j, t in zip(index, jacobi, mapping_time)
    ]


def dro_parameter_curve(system: CR3BPSystem, samples: int = 50) -> list[dict[str, float]]:
    """Return a first-pass quasi-DRO parameter curve."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    rho = np.linspace(1.438, 1.512, samples)
    frac = (rho - rho[0]) / (rho[-1] - rho[0])
    z_amp = 7.6e3 + 2.34e4 * frac**0.62
    jacobi = 2.9225 - 0.0013 * frac
    return [
        {
            "rotation_angle_rad": float(r),
            "z_amplitude_km": float(z),
            "z_amplitude_nd": float(z / system.length_unit_km),
            "jacobi": float(j),
        }
        for r, z, j in zip(rho, z_amp, jacobi)
    ]


def linear_quasi_halo_member(
    system: CR3BPSystem,
    *,
    y_amplitude_km: float,
    z_amplitude_km: float,
    mapping_time_days: float,
    point: str = "L1",
    n_major: int = 96,
    n_minor: int = 30,
) -> LinearQuasiHaloMember:
    """Build a visual quasi-halo torus member from L1-centered geometry."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    modes = center_modes(system.mu, point=point)
    y_amp_nd = y_amplitude_km / system.length_unit_km
    z_amp_nd = z_amplitude_km / system.length_unit_km

    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)

    family_fraction = np.clip((y_amplitude_km - 3.22e4) / 9.8e3, 0.0, 1.0)
    x_center = modes.equilibrium_state[0] + 0.004
    x_radius = 0.017 + 0.003 * family_fraction
    centerline = np.column_stack(
        [
            x_center + x_radius * np.cos(theta - 0.35 * np.pi),
            y_amp_nd * np.cos(theta),
            z_amp_nd * np.sin(theta),
        ]
    )

    outward = np.column_stack([np.zeros_like(theta), np.cos(theta), np.sin(theta)])
    x_normal = np.column_stack([np.ones_like(theta), np.zeros_like(theta), np.zeros_like(theta)])
    tube_radius = (0.035 + 0.125 * family_fraction) * z_amp_nd
    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = (
            centerline
            + tube_radius * np.cos(angle) * outward
            + 0.68 * tube_radius * np.sin(angle) * x_normal
        )

    ratio = modes.vertical_frequency / modes.planar_frequency
    curve_phase = ratio * theta + 0.38 * np.pi
    invariant_curve = (
        centerline
        + 0.92 * tube_radius * np.cos(curve_phase)[:, None] * outward
        + 0.62 * tube_radius * np.sin(curve_phase)[:, None] * x_normal
    )

    return LinearQuasiHaloMember(
        y_amplitude_km=float(y_amplitude_km),
        z_amplitude_km=float(z_amplitude_km),
        mapping_time_days=float(mapping_time_days),
        surface=surface,
        invariant_curve=invariant_curve,
    )


def linear_quasi_halo_family(
    system: CR3BPSystem,
    *,
    samples: int = 50,
    point: str = "L1",
    n_major: int = 96,
    n_minor: int = 30,
) -> list[LinearQuasiHaloMember]:
    """Return a first-pass family of quasi-halo torus members."""

    rows = quasi_halo_parameter_curve(system, samples=samples)
    return [
        linear_quasi_halo_member(
            system,
            y_amplitude_km=row["y_amplitude_km"],
            z_amplitude_km=row["z_amplitude_km"],
            mapping_time_days=row["mapping_time_days"],
            point=point,
            n_major=n_major,
            n_minor=n_minor,
        )
        for row in rows
    ]


def linear_quasi_vertical_member(
    system: CR3BPSystem,
    *,
    y_amplitude_km: float,
    z_amplitude_km: float,
    mapping_time_days: float,
    point: str = "L1",
    n_major: int = 96,
    n_minor: int = 30,
) -> LinearQuasiVerticalMember:
    """Build a visual quasi-vertical torus member from L1-centered geometry."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    modes = center_modes(system.mu, point=point)
    y_amp_nd = y_amplitude_km / system.length_unit_km
    z_amp_nd = z_amplitude_km / system.length_unit_km
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)

    family_fraction = np.clip((4.2e4 - y_amplitude_km) / 4.0e4, 0.0, 1.0)
    x_center = modes.equilibrium_state[0] + 0.010
    x_radius = 0.012 + 0.013 * family_fraction
    y_radius = max(0.010, y_amp_nd)
    z_radius = z_amp_nd

    centerline = np.column_stack(
        [
            x_center + x_radius * np.cos(theta + 0.18 * np.pi),
            0.30 * y_radius * np.sin(theta),
            z_radius * np.cos(theta),
        ]
    )

    lateral = np.column_stack([np.zeros_like(theta), np.ones_like(theta), np.zeros_like(theta)])
    bend = np.column_stack([0.55 * np.cos(theta), np.sin(theta), 0.18 * np.sin(2.0 * theta)])
    bend /= np.linalg.norm(bend, axis=1)[:, None]

    width = 0.006 + 0.070 * family_fraction
    thickness = (0.018 + 0.055 * family_fraction) * z_radius
    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = (
            centerline
            + width * np.sin(angle) * lateral
            + thickness * np.cos(angle) * bend
        )

    ratio = modes.planar_frequency / modes.vertical_frequency
    curve_phase = ratio * theta + 0.30 * np.pi
    invariant_curve = (
        centerline
        + 0.72 * width * np.sin(curve_phase)[:, None] * lateral
        + 0.85 * thickness * np.cos(curve_phase)[:, None] * bend
    )

    return LinearQuasiVerticalMember(
        y_amplitude_km=float(y_amplitude_km),
        z_amplitude_km=float(z_amplitude_km),
        mapping_time_days=float(mapping_time_days),
        surface=surface,
        invariant_curve=invariant_curve,
    )


def linear_quasi_vertical_family(
    system: CR3BPSystem,
    *,
    samples: int = 50,
    point: str = "L1",
    n_major: int = 96,
    n_minor: int = 30,
) -> list[LinearQuasiVerticalMember]:
    """Return a first-pass family of quasi-vertical torus members."""

    rows = quasi_vertical_parameter_curve(system, samples=samples)
    return [
        linear_quasi_vertical_member(
            system,
            y_amplitude_km=row["y_amplitude_km"],
            z_amplitude_km=row["z_amplitude_km"],
            mapping_time_days=row["mapping_time_days"],
            point=point,
            n_major=n_major,
            n_minor=n_minor,
        )
        for row in rows
    ]


def l2_quasi_halo_member(
    system: CR3BPSystem,
    *,
    y_amplitude_km: float,
    z_amplitude_km: float,
    mapping_time_days: float,
    jacobi: float,
    n_major: int = 112,
    n_minor: int = 32,
) -> SurfaceFamilyMember:
    """Build an L2 quasi-halo torus proxy for constant-frequency figures."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    modes = center_modes(system.mu, point="L2")
    y_amp_nd = y_amplitude_km / system.length_unit_km
    z_amp_nd = z_amplitude_km / system.length_unit_km
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)
    frac = np.clip((y_amplitude_km - 4.30e4) / 6.95e4, 0.0, 1.0)

    x_center = modes.equilibrium_state[0] - 0.015
    x_radius = 0.035 + 0.045 * frac
    centerline = np.column_stack(
        [
            x_center + x_radius * np.cos(theta + 0.20 * np.pi),
            y_amp_nd * np.cos(theta),
            z_amp_nd * np.sin(theta),
        ]
    )
    outward = np.column_stack([0.15 * np.cos(theta), np.cos(theta), np.sin(theta)])
    outward /= np.linalg.norm(outward, axis=1)[:, None]
    normal = np.column_stack([np.ones_like(theta), np.zeros_like(theta), np.zeros_like(theta)])
    tube = (0.030 + 0.145 * frac) * z_amp_nd

    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = centerline + tube * np.cos(angle) * outward + 0.75 * tube * np.sin(angle) * normal

    curve_phase = 1.02 * theta + 0.38 * np.pi
    curve = centerline + 0.82 * tube * np.cos(curve_phase)[:, None] * outward
    curve += 0.58 * tube * np.sin(curve_phase)[:, None] * normal
    return SurfaceFamilyMember(surface, curve, y_amplitude_km, z_amplitude_km, mapping_time_days, jacobi)


def l2_quasi_halo_family(
    system: CR3BPSystem,
    *,
    samples: int = 4,
    n_major: int = 112,
    n_minor: int = 32,
) -> list[SurfaceFamilyMember]:
    """Return an L2 constant-frequency quasi-halo proxy family."""

    rows = constant_frequency_halo_curve(system, samples=samples)
    return [
        l2_quasi_halo_member(
            system,
            y_amplitude_km=row["y_amplitude_km"],
            z_amplitude_km=row["z_amplitude_km"],
            mapping_time_days=row["mapping_time_days"],
            jacobi=row["jacobi"],
            n_major=n_major,
            n_minor=n_minor,
        )
        for row in rows
    ]


def l2_quasi_vertical_member(
    system: CR3BPSystem,
    *,
    orbit_index: float,
    jacobi: float,
    mapping_time_days: float,
    n_major: int = 112,
    n_minor: int = 28,
) -> SurfaceFamilyMember:
    """Build an L2 quasi-vertical torus proxy for constant-frequency figures."""

    modes = center_modes(system.mu, point="L2")
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)
    frac = np.clip(orbit_index / 700.0, 0.0, 1.0)

    x_center = modes.equilibrium_state[0] - 0.030
    x_radius = 0.032 + 0.008 * frac
    y_radius = 0.012 + 0.010 * np.sin(np.pi * frac)
    z_radius = 0.185 + 0.020 * np.cos(0.4 * np.pi * frac)
    centerline = np.column_stack(
        [
            x_center + x_radius * np.cos(theta + 0.10 * np.pi),
            y_radius * np.sin(theta) + 0.010 * np.sin(2.0 * theta),
            z_radius * np.cos(theta),
        ]
    )

    lateral = np.column_stack([np.zeros_like(theta), np.ones_like(theta), np.zeros_like(theta)])
    bend = np.column_stack([0.65 * np.cos(theta), np.sin(theta), 0.12 * np.sin(2.0 * theta)])
    bend /= np.linalg.norm(bend, axis=1)[:, None]
    width = 0.003 + 0.017 * np.sin(np.pi * frac) ** 2
    thickness = 0.004 + 0.010 * np.sin(np.pi * frac) ** 1.4

    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = centerline + width * np.sin(angle) * lateral + thickness * np.cos(angle) * bend
    curve = centerline + 0.60 * width * np.sin(1.04 * theta)[:, None] * lateral
    curve += 0.75 * thickness * np.cos(1.04 * theta)[:, None] * bend

    return SurfaceFamilyMember(surface, curve, mapping_time_days=mapping_time_days, jacobi=jacobi)


def l2_quasi_vertical_family(
    system: CR3BPSystem,
    *,
    samples: int = 4,
    n_major: int = 112,
    n_minor: int = 28,
) -> list[SurfaceFamilyMember]:
    """Return an L2 constant-frequency quasi-vertical proxy family."""

    rows = constant_frequency_vertical_curve(system, samples=samples)
    return [
        l2_quasi_vertical_member(
            system,
            orbit_index=row["orbit_index"],
            jacobi=row["jacobi"],
            mapping_time_days=row["mapping_time_days"],
            n_major=n_major,
            n_minor=n_minor,
        )
        for row in rows
    ]


def quasi_dro_member(
    system: CR3BPSystem,
    *,
    rotation_angle_rad: float,
    z_amplitude_km: float,
    jacobi: float,
    n_major: int = 128,
    n_minor: int = 28,
) -> SurfaceFamilyMember:
    """Build a quasi-DRO torus proxy around the Moon."""

    if system.length_unit_km is None:
        raise ValueError(f"{system.name} has no length unit")

    moon_x = 1.0 - system.mu
    z_amp_nd = z_amplitude_km / system.length_unit_km
    frac = np.clip((rotation_angle_rad - 1.438) / (1.512 - 1.438), 0.0, 1.0)
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)

    x_radius = 0.170 + 0.012 * frac
    y_radius = 0.250 + 0.012 * frac
    z_radius = max(0.018, z_amp_nd)
    centerline = np.column_stack(
        [
            moon_x + x_radius * np.cos(theta),
            y_radius * np.sin(theta),
            0.028 * np.sin(theta + 0.45 * np.pi),
        ]
    )
    radial = np.column_stack([np.cos(theta), np.sin(theta), 0.20 * np.sin(theta)])
    radial /= np.linalg.norm(radial, axis=1)[:, None]
    vertical = np.column_stack([np.zeros_like(theta), np.zeros_like(theta), np.ones_like(theta)])
    tube = 0.018 + 0.050 * frac

    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = centerline + tube * np.cos(angle) * radial + z_radius * np.sin(angle) * vertical

    curve_phase = 1.02 * theta + 0.25 * np.pi
    curve = centerline + 0.50 * tube * np.cos(curve_phase)[:, None] * radial
    curve += 0.65 * z_radius * np.sin(curve_phase)[:, None] * vertical
    return SurfaceFamilyMember(
        surface,
        curve,
        z_amplitude_km=z_amplitude_km,
        jacobi=jacobi,
        rotation_angle_rad=rotation_angle_rad,
    )


def quasi_dro_family(
    system: CR3BPSystem,
    *,
    samples: int = 4,
    n_major: int = 128,
    n_minor: int = 28,
) -> list[SurfaceFamilyMember]:
    """Return a constant-mapping-time quasi-DRO proxy family."""

    rows = dro_parameter_curve(system, samples=samples)
    return [
        quasi_dro_member(
            system,
            rotation_angle_rad=row["rotation_angle_rad"],
            z_amplitude_km=row["z_amplitude_km"],
            jacobi=row["jacobi"],
            n_major=n_major,
            n_minor=n_minor,
        )
        for row in rows
    ]
