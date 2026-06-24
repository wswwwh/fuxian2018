"""Corrected torus-map stability layers and Chapter 4 visual proxies."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import pickle

import numpy as np

from .constants import CR3BPSystem
from .cr3bp import integrate_cr3bp
from .quasi_torus import (
    FreeEnergyCurveCorrection,
    FixedFrequencyPseudoArclengthCorrection,
    FreeMappingTimeCurveCorrection,
    FreeRotationCurveCorrection,
    PseudoArclengthCurveCorrection,
    StroboscopicCurveNewtonCorrection,
    SurfaceFamilyMember,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_matrix,
    corrected_constant_energy_curve_family,
    corrected_l1_constant_energy_halo_high_order_corrections,
    corrected_l1_constant_energy_halo_pseudo_arclength_corrections,
    linear_quasi_halo_member,
    linear_quasi_vertical_member,
    stroboscopic_curve_newton_correction,
    stroboscopic_invariant_curve_seed,
    stroboscopic_spatial_jacobi_seed,
    stroboscopic_vertical_invariant_curve_seed,
)


CurveCorrection = (
    StroboscopicCurveNewtonCorrection
    | FreeRotationCurveCorrection
    | FreeMappingTimeCurveCorrection
    | FreeEnergyCurveCorrection
    | PseudoArclengthCurveCorrection
    | FixedFrequencyPseudoArclengthCorrection
)


_HIGH_ORDER_DG_CACHE_VERSION = 1


def _high_order_dg_cache_path(parameters: dict[str, object]) -> Path:
    payload = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("ascii")).hexdigest()[:16]
    project_root = Path(__file__).resolve().parents[2]
    return (
        project_root
        / "data"
        / "computed"
        / "cache"
        / f"quasi_halo_high_order_dg_v{_HIGH_ORDER_DG_CACHE_VERSION}_{digest}.pkl"
    )


@dataclass(frozen=True)
class ManifoldSheet:
    """A proxy manifold sheet grown from a quasi-periodic torus."""

    surface: np.ndarray
    family: str
    direction: str
    stage_fraction: float


@dataclass(frozen=True)
class DiscreteCurveDG:
    """Differential of a stroboscopic map on a corrected discrete curve."""

    correction: CurveCorrection
    map_jacobian: np.ndarray
    interpolation_to_base: np.ndarray
    stms: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray

    @property
    def determinant(self) -> float:
        return float(np.linalg.det(self.map_jacobian))

    @property
    def max_multiplier(self) -> float:
        return float(np.max(np.abs(self.eigenvalues)))

    @property
    def min_multiplier(self) -> float:
        return float(np.min(np.abs(self.eigenvalues)))

    @property
    def stability_index(self) -> float:
        lambda_max = self.max_multiplier
        return 0.5 * (lambda_max + 1.0 / lambda_max)

    @property
    def unit_multiplier_count(self) -> int:
        magnitudes = np.abs(self.eigenvalues)
        return int(np.count_nonzero(np.isclose(magnitudes, 1.0, rtol=1e-5, atol=1e-5)))

    @property
    def mapping_time(self) -> float:
        return _correction_mapping_time(self.correction)

    @property
    def rotation_angle_rad(self) -> float:
        return _correction_rotation_angle(self.correction)


@dataclass(frozen=True)
class CorrectedCurveManifoldSheet:
    """Local manifold sheet generated from a corrected-curve DG eigenvector."""

    dg: DiscreteCurveDG
    branch: str
    eigenvalue: complex
    perturbation_sign: float
    perturbation_scale: float
    times: np.ndarray
    base_states: np.ndarray
    manifold_states: np.ndarray
    perturbation_directions: np.ndarray

    @property
    def base_surface(self) -> np.ndarray:
        return self.base_states[:, :, :3]

    @property
    def surface(self) -> np.ndarray:
        return self.manifold_states[:, :, :3]

    @property
    def state_separation_norms(self) -> np.ndarray:
        return np.linalg.norm(self.manifold_states - self.base_states, axis=2)

    @property
    def position_separation_norms(self) -> np.ndarray:
        return np.linalg.norm(self.surface - self.base_surface, axis=2)

    @property
    def mean_state_growth(self) -> float:
        initial = float(np.mean(self.state_separation_norms[0]))
        final = float(np.mean(self.state_separation_norms[-1]))
        return final / initial

    @property
    def expected_growth(self) -> float:
        multiplier = abs(self.eigenvalue)
        if self.branch == "stable":
            return 1.0 / multiplier
        return multiplier


def display_scaled_corrected_dg_spectrum(
    dg: DiscreteCurveDG,
    *,
    unstable_radius: float = 2.35,
    unit_radius: float = 1.0,
    stable_radius: float = 0.38,
    unit_tolerance: float = 1.0e-3,
) -> dict[str, np.ndarray]:
    """Project a corrected ``DG`` spectrum to thesis-style display radii.

    The local corrected curve has very large unstable multipliers and reciprocal
    stable multipliers. Figure 4.1 uses compact rings, so this helper preserves
    the computed eigenvalue angles and stability classification while scaling
    each class to a comparable display radius.
    """

    eigenvalues = np.asarray(dg.eigenvalues, dtype=complex)
    magnitudes = np.abs(eigenvalues)
    masks = {
        "unstable": magnitudes > 1.0 + unit_tolerance,
        "unit": np.abs(magnitudes - 1.0) <= unit_tolerance,
        "stable": magnitudes < 1.0 - unit_tolerance,
    }
    radii = {
        "unstable": unstable_radius,
        "unit": unit_radius,
        "stable": stable_radius,
    }
    scaled: dict[str, np.ndarray] = {}
    for name, mask in masks.items():
        values = eigenvalues[mask]
        if values.size == 0:
            scaled[name] = np.empty(0, dtype=complex)
            continue
        value_magnitudes = np.abs(values)
        directions = values / np.where(value_magnitudes > 1.0e-300, value_magnitudes, 1.0)
        projected = float(radii[name]) * directions
        scaled[name] = projected[np.argsort(np.angle(projected))]
    return scaled


def _correction_mapping_time(correction: CurveCorrection) -> float:
    if isinstance(
        correction,
        (
            FreeMappingTimeCurveCorrection,
            FreeEnergyCurveCorrection,
            PseudoArclengthCurveCorrection,
            FixedFrequencyPseudoArclengthCorrection,
        ),
    ):
        return float(correction.mapping_time)
    return float(correction.seed.orbit_period)


def _correction_rotation_angle(correction: CurveCorrection) -> float:
    if isinstance(
        correction,
        (
            FreeRotationCurveCorrection,
            FreeMappingTimeCurveCorrection,
            FreeEnergyCurveCorrection,
            PseudoArclengthCurveCorrection,
            FixedFrequencyPseudoArclengthCorrection,
        ),
    ):
        return float(correction.rotation_angle_rad)
    return float(correction.seed.rotation_angle_rad)


def corrected_curve_dg(
    correction: CurveCorrection,
    *,
    max_step: float = 0.01,
) -> DiscreteCurveDG:
    """Assemble McCarthy's discrete torus-map differential for a correction.

    The map uses the correction's converged mapping time and rotation angle,
    including free-time/free-rotation Chapter 3 family members. The rotation
    interpolation maps terminal perturbations at ``theta + rho`` back to the
    base phase grid before the block-diagonal STMs are eigendecomposed.
    """

    seed = correction.seed
    mapping_time = _correction_mapping_time(correction)
    rotation_angle = _correction_rotation_angle(correction)
    _, stms = _stroboscopic_map_and_stms(
        correction.corrected_states,
        period=mapping_time,
        mu=seed.mu,
        max_step=max_step,
    )
    interpolation_to_base = _trigonometric_interpolation_matrix(
        seed.phases + rotation_angle,
        seed.phases,
    )

    sample_count = correction.corrected_states.shape[0]
    block_diagonal = np.zeros((6 * sample_count, 6 * sample_count), dtype=float)
    for idx in range(sample_count):
        block_diagonal[6 * idx : 6 * idx + 6, 6 * idx : 6 * idx + 6] = stms[idx]
    map_jacobian = np.kron(interpolation_to_base, np.eye(6)) @ block_diagonal
    eigenvalues, eigenvectors = np.linalg.eig(map_jacobian)
    order = np.argsort(np.abs(eigenvalues))[::-1]
    return DiscreteCurveDG(
        correction=correction,
        map_jacobian=map_jacobian,
        interpolation_to_base=interpolation_to_base,
        stms=stms,
        eigenvalues=eigenvalues[order],
        eigenvectors=eigenvectors[:, order],
    )


def _corrected_curve_dg_from_seed(
    seed,
    *,
    max_iterations: int,
    max_step: float,
) -> DiscreteCurveDG:
    """Assemble the corrected discrete-curve map differential for one seed."""

    correction = stroboscopic_curve_newton_correction(
        seed,
        max_iterations=max_iterations,
        max_step=max_step,
    )
    return corrected_curve_dg(correction, max_step=max_step)


def corrected_stroboscopic_curve_dg(
    mu: float,
    *,
    samples: int = 25,
    x_amplitude: float = 0.001,
    vertical_amplitude: float = 1e-5,
    max_iterations: int = 2,
    max_step: float = 0.02,
) -> DiscreteCurveDG:
    """Compute an STM-based ``DG`` matrix for a corrected invariant curve.

    The curve is represented by odd, equally spaced samples. Each sample is
    propagated for the corrected Lyapunov-orbit period; the resulting STM
    blocks are interpolated from the shifted phases ``theta_i + rho`` back to
    the base grid. This is the first physically computed Chapter 4 ``DG``
    layer. It is still local to the small stroboscopic curve seeded in Figure
    3.3, not a full large-amplitude quasi-halo continuation.
    """

    seed = stroboscopic_invariant_curve_seed(
        mu,
        samples=samples,
        x_amplitude=x_amplitude,
        vertical_amplitude=vertical_amplitude,
        curve_samples=max(4 * samples, 120),
    )
    return _corrected_curve_dg_from_seed(
        seed,
        max_iterations=max_iterations,
        max_step=max_step,
    )


def corrected_vertical_stroboscopic_curve_dg(
    mu: float,
    *,
    samples: int = 9,
    vertical_orbit_amplitude: float = 1e-4,
    planar_mode_amplitude: float = 1e-5,
    max_iterations: int = 2,
    max_step: float = 0.01,
) -> DiscreteCurveDG:
    """Compute ``DG`` for a corrected curve around a vertical periodic orbit."""

    seed = stroboscopic_vertical_invariant_curve_seed(
        mu,
        samples=samples,
        vertical_orbit_amplitude=vertical_orbit_amplitude,
        planar_mode_amplitude=planar_mode_amplitude,
        curve_samples=max(4 * samples, 120),
    )
    return _corrected_curve_dg_from_seed(
        seed,
        max_iterations=max_iterations,
        max_step=max_step,
    )


def real_hyperbolic_eigen_index(dg: DiscreteCurveDG, *, branch: str) -> int:
    """Return the nearly real stable or unstable eigenvalue index.

    McCarthy's manifold construction uses the purely real member of the stable
    or unstable eigenvalue circle. Finite curve discretization introduces small
    radius dispersion, so selecting only the largest magnitude can choose a
    complex Fourier-shifted member instead.
    """

    magnitudes = np.abs(dg.eigenvalues)
    if branch == "unstable":
        candidates = np.flatnonzero(magnitudes > 1.0 + 1.0e-3)
    elif branch == "stable":
        candidates = np.flatnonzero(magnitudes < 1.0 - 1.0e-3)
    else:
        raise ValueError("branch must be 'stable' or 'unstable'")
    if candidates.size == 0:
        raise RuntimeError(f"DG has no {branch} hyperbolic eigenvalue")
    relative_imaginary = np.abs(np.imag(dg.eigenvalues[candidates])) / magnitudes[candidates]
    minimum_imaginary = float(np.min(relative_imaginary))
    nearly_real = candidates[
        relative_imaginary <= max(minimum_imaginary + 1.0e-10, 1.0e-8)
    ]
    if branch == "unstable":
        return int(nearly_real[np.argmax(magnitudes[nearly_real])])
    return int(nearly_real[np.argmin(magnitudes[nearly_real])])


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_dg_family(
    mu: float,
    *,
    target_jacobi: float = 3.1389,
    mode_amplitudes: tuple[float, ...] = (2.5e-4, 5.0e-4, 7.5e-4, 1.0e-3),
    samples: int = 9,
    max_iterations: int = 24,
    max_step: float = 0.01,
) -> tuple[DiscreteCurveDG, ...]:
    """Return ``DG`` for the corrected L1 constant-energy quasi-halo family."""

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
    return tuple(corrected_curve_dg(correction, max_step=max_step) for correction in corrections)


def corrected_l1_constant_energy_halo_stability_family(
    mu: float,
    **kwargs,
) -> list[dict[str, float]]:
    """Return finite-amplitude ``JC=3.1389`` quasi-halo stability metrics."""

    rows: list[dict[str, float]] = []
    for dg in corrected_l1_constant_energy_halo_dg_family(mu, **kwargs):
        correction = dg.correction
        if not isinstance(correction, FreeEnergyCurveCorrection):
            raise TypeError("Expected a free-energy curve correction")
        unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
        stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
        rows.append(
            {
                "target_jacobi": float(correction.target_jacobi),
                "mode_amplitude_nd": float(correction.target_amplitude),
                "mapping_time_nd": float(correction.mapping_time),
                "rotation_angle_rad": float(correction.rotation_angle_rad),
                "curve_residual_norm": float(correction.final_residual_norms.max()),
                "determinant": float(dg.determinant),
                "stability_index": float(dg.stability_index),
                "max_multiplier": float(dg.max_multiplier),
                "min_multiplier": float(dg.min_multiplier),
                "real_unstable_multiplier": float(abs(dg.eigenvalues[unstable_index])),
                "real_stable_multiplier": float(abs(dg.eigenvalues[stable_index])),
                "unit_multiplier_count": float(dg.unit_multiplier_count),
            }
        )
    return rows


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_pseudo_arclength_dg_family(
    mu: float,
    *,
    member_indices: tuple[int, ...] = (0, 4, 8, 12, 16, 20, 26),
    max_step: float = 0.01,
) -> tuple[DiscreteCurveDG, ...]:
    """Return representative ``DG`` samples along the pseudo-arclength branch."""

    if max_step == 0.01:
        corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
            mu,
            members=27,
        )
    else:
        corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
            mu,
            members=27,
            max_step=max_step,
        )
    if not member_indices:
        raise ValueError("member_indices must not be empty")
    if any(index < 0 or index >= len(corrections) for index in member_indices):
        raise ValueError("member_indices contains an out-of-range member")
    if any(a >= b for a, b in zip(member_indices, member_indices[1:])):
        raise ValueError("member_indices must be strictly increasing")
    return tuple(
        corrected_curve_dg(corrections[index], max_step=max_step)
        for index in member_indices
    )


def corrected_l1_constant_energy_halo_pseudo_arclength_stability_family(
    mu: float,
    **kwargs,
) -> list[dict[str, float]]:
    """Return stability metrics along the corrected pseudo-arclength branch."""

    rows: list[dict[str, float]] = []
    for dg in corrected_l1_constant_energy_halo_pseudo_arclength_dg_family(mu, **kwargs):
        correction = dg.correction
        component = correction.seed.mode_component
        displacement = (
            correction.corrected_states[:, component]
            - correction.seed.orbit_state[component]
        )
        mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
        stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
        rows.append(
            {
                "target_jacobi": float(correction.target_jacobi),
                "mode_amplitude_nd": mode_amplitude,
                "mapping_time_nd": float(dg.mapping_time),
                "rotation_angle_rad": float(dg.rotation_angle_rad),
                "curve_residual_norm": float(correction.final_residual_norms.max()),
                "determinant": float(dg.determinant),
                "stability_index": float(dg.stability_index),
                "max_multiplier": float(dg.max_multiplier),
                "min_multiplier": float(dg.min_multiplier),
                "real_unstable_multiplier": float(abs(dg.eigenvalues[unstable_index])),
                "real_stable_multiplier": float(abs(dg.eigenvalues[stable_index])),
                "unit_multiplier_count": float(dg.unit_multiplier_count),
            }
        )
    return rows


@lru_cache(maxsize=8)
def corrected_l1_constant_energy_halo_high_order_dg_family(
    mu: float,
    *,
    samples: int,
    members: int,
    member_indices: tuple[int, ...],
    tolerance: float,
    max_iterations: int = 48,
    max_step: float = 0.01,
    persistent_cache: bool = True,
) -> tuple[DiscreteCurveDG, ...]:
    """Return representative ``DG`` samples on a spectrally lifted branch."""

    cache_parameters: dict[str, object] = {
        "version": _HIGH_ORDER_DG_CACHE_VERSION,
        "mu": float(mu),
        "samples": int(samples),
        "members": int(members),
        "member_indices": tuple(int(index) for index in member_indices),
        "tolerance": float(tolerance),
        "max_iterations": int(max_iterations),
        "max_step": float(max_step),
    }
    cache_path = _high_order_dg_cache_path(cache_parameters)
    if persistent_cache and cache_path.exists():
        with cache_path.open("rb") as stream:
            cached = pickle.load(stream)
        if isinstance(cached, tuple) and len(cached) == len(member_indices):
            return cached

    corrections = corrected_l1_constant_energy_halo_high_order_corrections(
        mu,
        members=members,
        samples=samples,
        max_iterations=max_iterations,
        tolerance=tolerance,
        max_step=max_step,
    )
    if not member_indices:
        raise ValueError("member_indices must not be empty")
    if any(index < 0 or index >= len(corrections) for index in member_indices):
        raise ValueError("member_indices contains an out-of-range member")
    if any(a >= b for a, b in zip(member_indices, member_indices[1:])):
        raise ValueError("member_indices must be strictly increasing")
    result = tuple(
        corrected_curve_dg(corrections[index], max_step=max_step)
        for index in member_indices
    )
    if persistent_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(result, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return result


def corrected_l1_constant_energy_halo_high_order_stability_family(
    mu: float,
    **kwargs,
) -> list[dict[str, float]]:
    """Return stability metrics on a spectrally lifted quasi-halo branch."""

    rows: list[dict[str, float]] = []
    for dg in corrected_l1_constant_energy_halo_high_order_dg_family(mu, **kwargs):
        correction = dg.correction
        component = correction.seed.mode_component
        displacement = (
            correction.corrected_states[:, component]
            - correction.seed.orbit_state[component]
        )
        mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
        stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
        rows.append(
            {
                "target_jacobi": float(correction.target_jacobi),
                "curve_samples": float(correction.corrected_states.shape[0]),
                "mode_amplitude_nd": mode_amplitude,
                "mapping_time_nd": float(dg.mapping_time),
                "rotation_angle_rad": float(dg.rotation_angle_rad),
                "curve_residual_norm": float(correction.final_residual_norms.max()),
                "determinant": float(dg.determinant),
                "stability_index": float(dg.stability_index),
                "max_multiplier": float(dg.max_multiplier),
                "min_multiplier": float(dg.min_multiplier),
                "real_unstable_multiplier": float(abs(dg.eigenvalues[unstable_index])),
                "real_stable_multiplier": float(abs(dg.eigenvalues[stable_index])),
                "unit_multiplier_count": float(dg.unit_multiplier_count),
            }
        )
    return rows


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_pseudo_arclength_endpoint_dg(
    mu: float,
    *,
    max_step: float = 0.01,
) -> DiscreteCurveDG:
    """Return ``DG`` for the 12.097-day endpoint of the validated branch."""

    if max_step == 0.01:
        corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
            mu,
            members=27,
        )
    else:
        corrections = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
            mu,
            members=27,
            max_step=max_step,
        )
    return corrected_curve_dg(corrections[-1], max_step=max_step)


def _corrected_curve_manifold_from_dg(
    mu: float,
    *,
    dg: DiscreteCurveDG,
    branch: str = "unstable",
    time_samples: int = 24,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float = 1.0,
    eigen_index: int | None = None,
    duration_periods: float = 1.0,
    max_step: float = 0.02,
    evaluation_times: np.ndarray | None = None,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local stable or unstable manifold sheet from a curve.

    The perturbation direction is taken from a stable or unstable eigenvector
    of the discretized curve-map differential ``DG``. Stable sheets are
    propagated backward for one mapping interval by default; unstable sheets
    are propagated forward. This is a local Chapter 4 manifold layer for the
    small corrected stroboscopic curve.
    """

    sample_count = dg.correction.corrected_states.shape[0]
    if branch not in {"stable", "unstable"}:
        raise ValueError("branch must be 'stable' or 'unstable'")
    if eigen_index is None:
        eigen_index = real_hyperbolic_eigen_index(dg, branch=branch)
    if not 0 <= eigen_index < dg.eigenvectors.shape[1]:
        eigen_index = dg.eigenvectors.shape[1] + eigen_index
    if not 0 <= eigen_index < dg.eigenvectors.shape[1]:
        raise ValueError("eigen_index is out of range")

    eigenvector = dg.eigenvectors[:, eigen_index]
    direction = np.real(eigenvector).reshape(sample_count, 6)
    block_norms = np.linalg.norm(direction, axis=1)
    if np.min(block_norms) < 1e-12:
        direction = np.imag(eigenvector).reshape(sample_count, 6)
        block_norms = np.linalg.norm(direction, axis=1)
    if np.min(block_norms) < 1e-12:
        raise RuntimeError("Selected DG eigenvector has near-zero local blocks")
    direction = direction / block_norms[:, None]

    base_initial = dg.correction.corrected_states
    manifold_initial = base_initial + float(perturbation_sign) * perturbation_scale * direction
    propagation_sign = -1.0 if branch == "stable" else 1.0
    final_time = propagation_sign * duration_periods * dg.mapping_time
    if evaluation_times is None:
        times = np.linspace(0.0, final_time, time_samples)
    else:
        times = np.asarray(evaluation_times, dtype=float)
        if times.ndim != 1 or times.size < 2:
            raise ValueError("evaluation_times must contain at least two values")
        if abs(times[0]) > 1.0e-14:
            raise ValueError("evaluation_times must start at zero")
        if propagation_sign * np.diff(times).min() < -1.0e-14:
            raise ValueError("evaluation_times must follow the propagation direction")
        if abs(times[-1] - final_time) > 1.0e-12:
            raise ValueError("evaluation_times must end at duration_periods * mapping_time")
        time_samples = times.size

    base_states = np.empty((time_samples, sample_count, 6), dtype=float)
    manifold_states = np.empty_like(base_states)
    for idx in range(sample_count):
        base_sol = integrate_cr3bp(
            base_initial[idx],
            (0.0, final_time),
            mu,
            t_eval=times,
            max_step=max_step,
        )
        manifold_sol = integrate_cr3bp(
            manifold_initial[idx],
            (0.0, final_time),
            mu,
            t_eval=times,
            max_step=max_step,
        )
        if not base_sol.success:
            raise RuntimeError(base_sol.message)
        if not manifold_sol.success:
            raise RuntimeError(manifold_sol.message)
        base_states[:, idx, :] = base_sol.y.T
        manifold_states[:, idx, :] = manifold_sol.y.T

    return CorrectedCurveManifoldSheet(
        dg=dg,
        branch=branch,
        eigenvalue=dg.eigenvalues[eigen_index],
        perturbation_sign=float(perturbation_sign),
        perturbation_scale=float(perturbation_scale),
        times=times,
        base_states=base_states,
        manifold_states=manifold_states,
        perturbation_directions=direction,
    )


def corrected_curve_manifold(
    mu: float,
    *,
    branch: str = "unstable",
    samples: int = 9,
    time_samples: int = 24,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float = 1.0,
    eigen_index: int | None = None,
    duration_periods: float = 1.0,
    max_step: float = 0.02,
    evaluation_times: np.ndarray | None = None,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local manifold from the corrected quasi-halo curve."""

    dg = corrected_stroboscopic_curve_dg(mu, samples=samples, max_step=max_step)
    return _corrected_curve_manifold_from_dg(
        mu,
        dg=dg,
        branch=branch,
        time_samples=time_samples,
        perturbation_scale=perturbation_scale,
        perturbation_sign=perturbation_sign,
        eigen_index=eigen_index,
        duration_periods=duration_periods,
        max_step=max_step,
        evaluation_times=evaluation_times,
    )


def corrected_vertical_curve_manifold(
    mu: float,
    *,
    branch: str = "unstable",
    samples: int = 9,
    time_samples: int = 24,
    vertical_orbit_amplitude: float = 1e-4,
    planar_mode_amplitude: float = 1e-5,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float = 1.0,
    eigen_index: int | None = None,
    duration_periods: float = 1.0,
    max_step: float = 0.01,
    evaluation_times: np.ndarray | None = None,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local manifold from the corrected quasi-vertical curve."""

    dg = corrected_vertical_stroboscopic_curve_dg(
        mu,
        samples=samples,
        vertical_orbit_amplitude=vertical_orbit_amplitude,
        planar_mode_amplitude=planar_mode_amplitude,
        max_step=max_step,
    )
    return _corrected_curve_manifold_from_dg(
        mu,
        dg=dg,
        branch=branch,
        time_samples=time_samples,
        perturbation_scale=perturbation_scale,
        perturbation_sign=perturbation_sign,
        eigen_index=eigen_index,
        duration_periods=duration_periods,
        max_step=max_step,
        evaluation_times=evaluation_times,
    )


def corrected_vertical_curve_unstable_manifold(
    mu: float,
    **kwargs,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local unstable sheet from the quasi-vertical curve."""

    return corrected_vertical_curve_manifold(mu, branch="unstable", **kwargs)


def corrected_vertical_curve_stable_manifold(
    mu: float,
    **kwargs,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local stable sheet from the quasi-vertical curve."""

    return corrected_vertical_curve_manifold(mu, branch="stable", **kwargs)


def corrected_vertical_global_unstable_manifold(
    mu: float,
    *,
    samples: int = 9,
    time_samples: int = 240,
    vertical_orbit_amplitude: float = 1e-4,
    planar_mode_amplitude: float = 1e-5,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float | None = None,
    duration_periods: float = 2.5,
    max_step: float = 0.01,
) -> CorrectedCurveManifoldSheet:
    """Propagate the Earthward quasi-vertical unstable sheet globally."""

    dg = corrected_vertical_stroboscopic_curve_dg(
        mu,
        samples=samples,
        vertical_orbit_amplitude=vertical_orbit_amplitude,
        planar_mode_amplitude=planar_mode_amplitude,
        max_step=max_step,
    )
    signs = (-1.0, 1.0) if perturbation_sign is None else (float(perturbation_sign),)
    candidates = tuple(
        _corrected_curve_manifold_from_dg(
            mu,
            dg=dg,
            branch="unstable",
            time_samples=time_samples,
            perturbation_scale=perturbation_scale,
            perturbation_sign=sign,
            duration_periods=duration_periods,
            max_step=max_step,
        )
        for sign in signs
    )
    return min(candidates, key=lambda sheet: float(np.min(sheet.surface[:, :, 0])))


@lru_cache(maxsize=4)
def corrected_l1_constant_energy_halo_unstable_manifolds(
    mu: float,
    *,
    time_unit_days: float,
    snapshot_times_days: tuple[float, ...] = (7.79, 9.75, 11.39, 13.02),
    samples: int = 9,
    time_samples: int = 120,
    perturbation_scale: float = 5.0e-5,
    max_step: float = 0.01,
) -> tuple[CorrectedCurveManifoldSheet, CorrectedCurveManifoldSheet]:
    """Return the +x and -x finite-amplitude quasi-halo unstable sheets.

    The underlying member is the 12.097-day endpoint of the validated
    ``JC=3.1389`` pseudo-arclength quasi-halo branch. Both signs of the purely
    real unstable eigenvector are propagated, then labelled by terminal mean x
    so the result does not depend on NumPy's arbitrary eigenvector sign.
    """

    if time_unit_days <= 0.0:
        raise ValueError("time_unit_days must be positive")
    if not snapshot_times_days or any(value <= 0.0 for value in snapshot_times_days):
        raise ValueError("snapshot_times_days must contain positive values")
    if any(a >= b for a, b in zip(snapshot_times_days, snapshot_times_days[1:])):
        raise ValueError("snapshot_times_days must be strictly increasing")

    if samples != 9:
        raise ValueError("The validated pseudo-arclength endpoint currently uses samples=9")
    dg = corrected_l1_constant_energy_halo_pseudo_arclength_endpoint_dg(
        mu,
        max_step=max_step,
    )
    snapshot_times = np.asarray(snapshot_times_days, dtype=float) / time_unit_days
    final_time = float(snapshot_times[-1])
    evaluation_times = np.unique(
        np.r_[np.linspace(0.0, final_time, time_samples), snapshot_times]
    )
    duration_periods = final_time / dg.mapping_time
    candidates = tuple(
        _corrected_curve_manifold_from_dg(
            mu,
            dg=dg,
            branch="unstable",
            time_samples=evaluation_times.size,
            perturbation_scale=perturbation_scale,
            perturbation_sign=sign,
            duration_periods=duration_periods,
            max_step=max_step,
            evaluation_times=evaluation_times,
        )
        for sign in (-1.0, 1.0)
    )
    ordered = sorted(candidates, key=lambda sheet: float(np.mean(sheet.surface[-1, :, 0])))
    minus_x, plus_x = ordered
    return plus_x, minus_x


def corrected_curve_unstable_manifold(
    mu: float,
    *,
    samples: int = 9,
    time_samples: int = 24,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float = 1.0,
    eigen_index: int | None = None,
    duration_periods: float = 1.0,
    max_step: float = 0.02,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local unstable manifold sheet from the corrected curve."""

    return corrected_curve_manifold(
        mu,
        branch="unstable",
        samples=samples,
        time_samples=time_samples,
        perturbation_scale=perturbation_scale,
        perturbation_sign=perturbation_sign,
        eigen_index=eigen_index,
        duration_periods=duration_periods,
        max_step=max_step,
    )


def corrected_curve_stable_manifold(
    mu: float,
    *,
    samples: int = 9,
    time_samples: int = 24,
    perturbation_scale: float = 1e-7,
    perturbation_sign: float = 1.0,
    eigen_index: int | None = None,
    duration_periods: float = 1.0,
    max_step: float = 0.02,
) -> CorrectedCurveManifoldSheet:
    """Propagate a local stable manifold sheet backward from the curve."""

    return corrected_curve_manifold(
        mu,
        branch="stable",
        samples=samples,
        time_samples=time_samples,
        perturbation_scale=perturbation_scale,
        perturbation_sign=perturbation_sign,
        eigen_index=eigen_index,
        duration_periods=duration_periods,
        max_step=max_step,
    )


def corrected_curve_stability_family(
    mu: float,
    *,
    vertical_amplitudes: tuple[float, ...] = (1e-5, 1.5e-5, 2e-5, 3e-5),
    samples: int = 9,
    max_step: float = 0.02,
) -> list[dict[str, float]]:
    """Return local corrected-curve DG stability metrics over amplitudes."""

    rows: list[dict[str, float]] = []
    for vertical_amplitude in vertical_amplitudes:
        dg = corrected_stroboscopic_curve_dg(
            mu,
            samples=samples,
            vertical_amplitude=vertical_amplitude,
            max_step=max_step,
        )
        seed = dg.correction.seed
        rows.append(
            {
                "vertical_amplitude_nd": float(vertical_amplitude),
                "orbit_period_nd": float(seed.orbit_period),
                "rotation_angle_rad": float(seed.rotation_angle_rad),
                "curve_residual_norm": float(dg.correction.final_residual_norms.max()),
                "stability_index": float(dg.stability_index),
                "max_multiplier": float(dg.max_multiplier),
                "min_multiplier": float(dg.min_multiplier),
                "determinant": float(dg.determinant),
                "unit_multiplier_count": float(dg.unit_multiplier_count),
            }
        )
    return rows


def dg_eigenvalue_loops(samples: int = 28) -> dict[str, np.ndarray]:
    """Return first-pass DG eigenvalue loops for Figure 4.1."""

    theta = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    return {
        "outer": 2.35 * np.exp(1j * theta),
        "middle": 1.00 * np.exp(1j * theta),
        "inner": 0.38 * np.exp(1j * theta),
    }


def quasi_halo_stability_curve(samples: int = 64) -> list[dict[str, float]]:
    """Return the Figure 4.2 stability-index trend."""

    t = np.linspace(12.025, 12.475, samples)
    frac = (t - t[0]) / (t[-1] - t[0])
    nu = 618.0 + 177.0 * frac**1.05
    return [{"mapping_time_days": float(time), "stability_index": float(value)} for time, value in zip(t, nu)]


def chapter4_quasi_halo_orbit(system: CR3BPSystem, n_major: int = 128, n_minor: int = 16) -> SurfaceFamilyMember:
    """Return a small L2 quasi-halo orbit/tube used in Figure 4.1."""

    moon_x = 1.0 - system.mu
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)
    centerline = np.column_stack(
        [
            moon_x + 0.012 * np.cos(theta + 0.15 * np.pi),
            0.052 * np.cos(theta),
            0.088 + 0.088 * np.sin(theta),
        ]
    )
    normal_yz = np.column_stack([np.zeros_like(theta), np.cos(theta), np.sin(theta)])
    normal_x = np.column_stack([np.ones_like(theta), np.zeros_like(theta), np.zeros_like(theta)])
    tube = 0.006
    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = centerline + tube * np.cos(angle) * normal_yz + 0.55 * tube * np.sin(angle) * normal_x
    return SurfaceFamilyMember(surface=surface, invariant_curve=centerline, mapping_time_days=12.03, jacobi=3.1389)


def base_torus(system: CR3BPSystem, family: str, n_major: int = 96, n_minor: int = 22) -> SurfaceFamilyMember:
    """Return the black reference torus for Chapter 4 manifold figures."""

    if family == "halo":
        return linear_quasi_halo_member(
            system,
            y_amplitude_km=3.95e4,
            z_amplitude_km=3.40e4,
            mapping_time_days=12.23,
            point="L1",
            n_major=n_major,
            n_minor=n_minor,
        )
    if family == "vertical":
        return linear_quasi_vertical_member(
            system,
            y_amplitude_km=2.2e4,
            z_amplitude_km=3.9e4,
            mapping_time_days=12.76,
            point="L1",
            n_major=n_major,
            n_minor=n_minor,
        )
    raise ValueError(f"Unknown torus family: {family}")


def manifold_sheet(
    system: CR3BPSystem,
    *,
    family: str = "halo",
    direction: str = "plus",
    stage_fraction: float = 1.0,
    n_curve: int = 74,
    n_steps: int = 38,
) -> ManifoldSheet:
    """Create a deterministic proxy stable/unstable manifold sheet.

    ``direction='plus'`` grows toward the Moon/L2 side; ``direction='minus'``
    grows toward the Earth side. The sheet is a visual continuation proxy, not
    the DG-eigenvector manifold from the thesis.
    """

    member = base_torus(system, family, n_major=n_curve, n_minor=18)
    base = member.invariant_curve
    theta = np.linspace(0.0, 2.0 * np.pi, n_curve)
    stage = float(np.clip(stage_fraction, 0.05, 1.35))

    if direction == "plus":
        reach = (0.18 if family == "halo" else 0.22) * stage
        target = base.copy()
        target[:, 0] = base[:, 0] + reach * (0.75 + 0.25 * np.cos(theta - 0.30))
        target[:, 1] = base[:, 1] + 0.10 * stage * np.sin(theta + 0.85)
        target[:, 2] = 0.82 * base[:, 2] + 0.060 * stage * np.sin(2.0 * theta + 0.20)
    elif direction == "minus":
        reach = (0.62 if family == "halo" else 0.70) * stage
        target = base.copy()
        target[:, 0] = base[:, 0] - reach * (0.86 + 0.14 * np.cos(theta + 0.20))
        target[:, 1] = base[:, 1] + 0.27 * stage * (0.62 + 0.38 * np.sin(theta + 0.55))
        target[:, 2] = 0.95 * base[:, 2] + 0.060 * stage * np.sin(1.5 * theta)
    else:
        raise ValueError(f"Unknown manifold direction: {direction}")

    alphas = np.linspace(0.0, 1.0, n_steps)
    surface = np.empty((n_steps, n_curve, 3), dtype=float)
    for idx, alpha in enumerate(alphas):
        curl = 0.016 * stage * np.sin(np.pi * alpha) * np.column_stack(
            [
                0.15 * np.sin(theta + 2.0 * alpha),
                np.sin(2.0 * theta + 1.5 * alpha),
                np.cos(theta - alpha),
            ]
        )
        surface[idx, :, :] = (1.0 - alpha) * base + alpha * target + curl
    return ManifoldSheet(surface=surface, family=family, direction=direction, stage_fraction=stage)
