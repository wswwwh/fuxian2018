"""First-pass application-scene geometry for Chapter 5 figures."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

from .constants import SYSTEMS, CR3BPSystem
from .cr3bp import cr3bp_rhs, integrate_cr3bp, jacobi_constant
from .linear_modes import center_modes, mode_solution
from .libration_points import compute_libration_points
from .manifolds import hyperbolic_eigenvectors, monodromy
from .periodic_orbits import (
    PlanarLyapunovOrbit,
    SpatialSymmetricOrbit,
    correct_planar_lyapunov,
    correct_planar_lyapunov_fixed_x,
    correct_planar_lyapunov_jacobi,
    correct_spatial_symmetric_orbit,
    correct_spatial_symmetric_orbit_fixed_secondary_radius,
    planar_lyapunov_linear_guess,
    propagate_periodic_orbit,
)
from .quasi_torus import SurfaceFamilyMember, corrected_dro_free_rotation_torus, quasi_dro_member
from .variational import integrate_state_and_stm, unpack_augmented


@dataclass(frozen=True)
class TorusTrajectoryScene:
    """A surface plus one or more trajectory curves."""

    surface: np.ndarray
    curves: tuple[np.ndarray, ...]
    marker: np.ndarray | None = None


@dataclass(frozen=True)
class CR3BPLongPropagationScene:
    """CR3BP-propagated trajectory curves and diagnostics for an application scene."""

    surface: np.ndarray
    curves: tuple[np.ndarray, ...]
    states: tuple[np.ndarray, ...]
    times: np.ndarray
    jacobi_spans: np.ndarray
    duration_days: float


@dataclass(frozen=True)
class CR3BPDROScene:
    """Corrected resonant DRO and a local quasi-DRO ten-return trajectory."""

    torus_surface: np.ndarray
    torus_states: np.ndarray
    torus_times: np.ndarray
    torus_phases: np.ndarray
    invariant_curve: np.ndarray
    periodic_states: np.ndarray
    quasi_states: np.ndarray
    periodic_times: np.ndarray
    quasi_times: np.ndarray
    marker: np.ndarray
    period_days: float
    duration_days: float
    periselene_radius_km: float
    periodicity_error: float
    periodic_jacobi_span: float
    quasi_jacobi_span: float
    torus_closure_error: float
    rotation_angle_rad: float
    target_vertical_amplitude: float


@dataclass(frozen=True)
class NRHOTransferScene:
    """NRHO departure/destination curves and transfer arcs."""

    departure: np.ndarray
    destination: np.ndarray
    transfer_arcs: tuple[np.ndarray, ...]
    surface: np.ndarray | None = None
    departure_location: np.ndarray | None = None
    arrival_location: np.ndarray | None = None


@dataclass(frozen=True)
class TwoImpulseTransfer:
    """A position-matched CR3BP transfer between two periodic-orbit states."""

    departure_phase: float
    arrival_phase: float
    time_of_flight_days: float
    departure_state: np.ndarray
    arrival_state: np.ndarray
    transfer_states: np.ndarray
    transfer_times_days: np.ndarray
    departure_delta_v_m_s: float
    arrival_delta_v_m_s: float
    endpoint_position_error_km: float
    minimum_moon_radius_km: float
    jacobi_span: float

    @property
    def total_delta_v_m_s(self) -> float:
        return self.departure_delta_v_m_s + self.arrival_delta_v_m_s


@dataclass(frozen=True)
class EarthMoonNRHOTransferBaseline:
    """Corrected NRHO boundaries and direct-shooting transfer baselines."""

    departure_orbit: SpatialSymmetricOrbit
    destination_orbit: SpatialSymmetricOrbit
    departure_states: np.ndarray
    destination_states: np.ndarray
    corridor_surface: np.ndarray
    departure_perilune_radius_km: float
    destination_perilune_radius_km: float
    departure_stability_index: float
    destination_stability_index: float
    departure_periodicity_error: float
    destination_periodicity_error: float
    forward_transfers: tuple[TwoImpulseTransfer, ...]
    reverse_transfers: tuple[TwoImpulseTransfer, ...]
    rendezvous_offsets_hours: np.ndarray
    rendezvous_delta_v_difference_m_s: np.ndarray


@dataclass(frozen=True)
class EarthMoonHaloLyapunovTransferBaseline:
    """Corrected equal-Jacobi boundaries and a fixed-time transfer baseline."""

    halo_orbit: SpatialSymmetricOrbit
    lyapunov_orbit: PlanarLyapunovOrbit
    halo_states: np.ndarray
    lyapunov_states: np.ndarray
    corridor_surface: np.ndarray
    transfer_states: np.ndarray
    transfer_times_days: np.ndarray
    patch_states: np.ndarray
    departure_phase: float
    arrival_phase: float
    time_of_flight_days: float
    departure_state: np.ndarray
    arrival_state: np.ndarray
    departure_delta_v_m_s: float
    arrival_delta_v_m_s: float
    endpoint_position_error_km: float
    maximum_continuity_error: float
    minimum_moon_radius_km: float
    jacobi_span: float
    boundary_jacobi_difference: float
    halo_stability_index: float
    halo_periodicity_error: float
    lyapunov_periodicity_error: float

    @property
    def total_delta_v_m_s(self) -> float:
        return self.departure_delta_v_m_s + self.arrival_delta_v_m_s


@dataclass(frozen=True)
class SunEarthStableManifoldBaseline:
    """Sun-Earth L1 periodic-orbit stable-manifold scan and LEO-targeted arc."""

    orbit: PlanarLyapunovOrbit
    orbit_states: np.ndarray
    scan_phase_deg: np.ndarray
    scan_periapsis_radius_km: np.ndarray
    target_periapsis_radius_km: float
    selected_phase_deg: float
    selected_periapsis_radius_km: float
    selected_states: np.ndarray
    selected_times_days: np.ndarray
    parking_orbit_km: np.ndarray
    transfer_time_days: float
    jacobi_span: float
    periodicity_error: float
    stable_eigenvalue_magnitude: float


def _ellipse_curve(
    center: np.ndarray,
    radii: tuple[float, float, float],
    *,
    phase: float = 0.0,
    samples: int = 360,
    tilt_y: float = 0.0,
) -> np.ndarray:
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    x = center[0] + radii[0] * np.cos(theta + phase)
    y = center[1] + radii[1] * np.sin(theta + phase)
    z = center[2] + radii[2] * np.sin(theta + phase + tilt_y * np.sin(theta))
    return np.column_stack([x, y, z])


def _tube_around_curve(curve: np.ndarray, *, radius: float, samples: int = 22) -> np.ndarray:
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    tangent = np.gradient(curve, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    radial = curve - np.array([curve[:, 0].mean(), curve[:, 1].mean(), curve[:, 2].mean()])
    radial_norm = np.linalg.norm(radial, axis=1)
    valid = radial_norm > 0.0
    radial[valid] = radial[valid] / radial_norm[valid, None]
    vertical = np.tile(np.array([0.0, 0.0, 1.0]), (curve.shape[0], 1))
    normal = np.cross(tangent, vertical)
    normal_norm = np.linalg.norm(normal, axis=1)
    fallback = normal_norm < 1.0e-8
    normal[fallback] = radial[fallback]
    normal_norm = np.linalg.norm(normal, axis=1)
    normal /= normal_norm[:, None]
    binormal = np.cross(tangent, normal)
    binormal /= np.linalg.norm(binormal, axis=1)[:, None]

    surface = np.empty((curve.shape[0], samples, 3), dtype=float)
    for idx, angle in enumerate(theta):
        surface[:, idx, :] = curve + radius * np.cos(angle) * normal + radius * np.sin(angle) * binormal
    return surface


def _sun_earth_l1_proxy_surface(system: CR3BPSystem, *, n_major: int = 120, n_minor: int = 24) -> np.ndarray:
    l1_x = compute_libration_points(system.mu)["L1"].x
    theta = np.linspace(0.0, 2.0 * np.pi, n_major)
    phi = np.linspace(0.0, 2.0 * np.pi, n_minor)

    centerline = np.column_stack(
        [
            l1_x + 0.0018 * np.cos(theta + 0.18 * np.pi),
            0.0048 * np.sin(theta),
            0.0057 * np.cos(theta),
        ]
    )
    lateral = np.column_stack([0.12 * np.cos(theta), np.sin(theta), 0.25 * np.sin(theta)])
    lateral /= np.linalg.norm(lateral, axis=1)[:, None]
    normal = np.column_stack([np.ones_like(theta), np.zeros_like(theta), np.zeros_like(theta)])
    surface = np.empty((n_major, n_minor, 3), dtype=float)
    for j, angle in enumerate(phi):
        surface[:, j, :] = centerline + 0.0010 * np.cos(angle) * lateral + 0.00065 * np.sin(angle) * normal
    return surface


def sun_earth_l1_long_propagation(curve_count: int, *, n_major: int = 120, n_minor: int = 24) -> TorusTrajectoryScene:
    """Return a Sun-Earth L1 quasi-vertical torus proxy and propagated traces."""

    system = SYSTEMS["sun_earth"]
    l1_x = compute_libration_points(system.mu)["L1"].x
    surface = _sun_earth_l1_proxy_surface(system, n_major=n_major, n_minor=n_minor)
    curves: list[np.ndarray] = []
    steps = np.linspace(0.0, 1.0, max(1, curve_count))
    fine = np.linspace(0.0, 2.0 * np.pi, 360)
    for idx, frac in enumerate(steps):
        phase = 0.35 * np.pi * frac
        loops = 1.0 + 0.10 * idx
        curve = np.column_stack(
            [
                l1_x + 0.0018 * np.cos(loops * fine + phase) + 0.00035 * np.sin(2.0 * fine + phase),
                0.0047 * np.sin(fine + phase) + 0.00055 * np.sin(2.7 * fine + 0.4 * phase),
                0.0055 * np.cos(fine + 0.65 * phase),
            ]
        )
        curves.append(curve)
    return TorusTrajectoryScene(surface=surface, curves=tuple(curves))


def sun_earth_l1_cr3bp_long_propagation(
    curve_count: int,
    *,
    n_major: int = 120,
    n_minor: int = 24,
    samples: int = 360,
    duration_periods: float = 0.4,
    y_amplitude: float = 0.00025,
    z_amplitude: float = 0.0028,
    vertical_phase: float = 0.45 * np.pi,
    max_step: float = 0.04,
) -> CR3BPLongPropagationScene:
    """Propagate Sun-Earth L1 Lissajous-like seeds with the CR3BP equations.

    The seeds are linear center-mode Lissajous states near Sun-Earth L1. They
    are not BCR4BP/ephemeris-corrected thesis initial conditions, but the local
    red arcs are integrated CR3BP trajectories with Jacobi conservation checked
    by validation.
    """

    if samples < 2:
        raise ValueError("samples must be at least 2")
    system = SYSTEMS["sun_earth"]
    modes = center_modes(system.mu, point="L1")
    vertical_period = 2.0 * np.pi / modes.vertical_frequency
    duration = float(duration_periods) * vertical_period
    times = np.linspace(0.0, duration, samples)
    phase_fractions = np.linspace(0.0, 1.0, max(1, curve_count), endpoint=False)
    reference_times = np.linspace(0.0, vertical_period, 720, endpoint=False)
    planar_reference = mode_solution(modes.planar_eigenvalue, modes.planar_eigenvector, reference_times)
    vertical_reference = mode_solution(
        modes.vertical_eigenvalue,
        modes.vertical_eigenvector,
        reference_times,
        phase=vertical_phase,
    )
    planar_scale = y_amplitude / float(np.max(np.abs(planar_reference[:, 1])))
    vertical_scale = z_amplitude / float(np.max(np.abs(vertical_reference[:, 2])))

    curves: list[np.ndarray] = []
    states: list[np.ndarray] = []
    jacobi_spans: list[float] = []
    for fraction in phase_fractions:
        phase_time = fraction * vertical_period
        planar_displacement = planar_scale * mode_solution(
            modes.planar_eigenvalue,
            modes.planar_eigenvector,
            np.array([phase_time]),
        )[0]
        vertical_displacement = vertical_scale * mode_solution(
            modes.vertical_eigenvalue,
            modes.vertical_eigenvector,
            np.array([phase_time]),
            phase=vertical_phase,
        )[0]
        displacement = planar_displacement + vertical_displacement
        initial_state = modes.equilibrium_state + displacement
        solution = integrate_cr3bp(
            initial_state,
            (0.0, duration),
            system.mu,
            t_eval=times,
            max_step=max_step,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        curve_states = solution.y.T
        jacobi_values = jacobi_constant(curve_states, system.mu)
        states.append(curve_states)
        curves.append(curve_states[:, :3])
        jacobi_spans.append(float(np.max(jacobi_values) - np.min(jacobi_values)))

    surface = _sun_earth_l1_proxy_surface(system, n_major=n_major, n_minor=n_minor)
    return CR3BPLongPropagationScene(
        surface=surface,
        curves=tuple(curves),
        states=tuple(states),
        times=times,
        jacobi_spans=np.array(jacobi_spans, dtype=float),
        duration_days=duration * (system.time_unit_days or 1.0),
    )


def quasi_dro_return_scene(system: CR3BPSystem | None = None) -> TorusTrajectoryScene:
    """Return a quasi-DRO proxy with a planar DRO and long return trace."""

    system = system or SYSTEMS["earth_moon"]
    member = quasi_dro_member(system, rotation_angle_rad=1.49, z_amplitude_km=2.55e4, jacobi=2.921)
    moon_x = 1.0 - system.mu
    theta = np.linspace(0.0, 10.0 * np.pi, 1100)
    quasi = np.column_stack(
        [
            moon_x + 0.175 * np.cos(theta) + 0.015 * np.cos(0.42 * theta + 0.4),
            0.255 * np.sin(theta) + 0.026 * np.sin(1.22 * theta),
            0.070 * np.sin(0.52 * theta + 0.8) + 0.018 * np.sin(theta),
        ]
    )
    planar = np.column_stack(
        [
            moon_x + 0.170 * np.cos(np.linspace(0.0, 2.0 * np.pi, 420)),
            0.240 * np.sin(np.linspace(0.0, 2.0 * np.pi, 420)),
            np.zeros(420),
        ]
    )
    marker = quasi[75]
    return TorusTrajectoryScene(surface=member.surface, curves=(quasi, planar), marker=marker)


def quasi_dro_cr3bp_return_scene(
    system: CR3BPSystem | None = None,
    *,
    periselene_radius_km: float = 73800.0,
    mapping_time_days: float = 14.75,
    returns: int = 10,
    vertical_amplitude: float = 1e-2,
    periodic_samples: int = 420,
    trajectory_samples: int = 1100,
) -> CR3BPDROScene:
    """Return the thesis-scale resonant DRO and a local corrected quasi-DRO arc."""

    system = system or SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("The resonant DRO scene requires dimensional system units")
    if returns < 1:
        raise ValueError("returns must be positive")

    moon_x = 1.0 - system.mu
    x0 = moon_x - periselene_radius_km / system.length_unit_km
    initial_half_period = mapping_time_days / (2.0 * system.time_unit_days)
    torus = corrected_dro_free_rotation_torus(
        system.mu,
        x0=x0,
        samples=15,
        time_samples=36,
        initial_half_period=initial_half_period,
        vertical_amplitude=vertical_amplitude,
        max_iterations=8,
    )
    seed = torus.correction.seed

    periodic_times = np.linspace(0.0, seed.orbit_period, periodic_samples)
    periodic_sol = integrate_cr3bp(
        seed.orbit_state,
        (0.0, seed.orbit_period),
        system.mu,
        t_eval=periodic_times,
        max_step=0.01,
    )
    if not periodic_sol.success:
        raise RuntimeError(periodic_sol.message)
    periodic_states = periodic_sol.y.T

    quasi_times = np.linspace(0.0, returns * seed.orbit_period, trajectory_samples)
    quasi_sol = integrate_cr3bp(
        torus.correction.corrected_states[0],
        (0.0, returns * seed.orbit_period),
        system.mu,
        t_eval=quasi_times,
        max_step=0.01,
    )
    if not quasi_sol.success:
        raise RuntimeError(quasi_sol.message)
    quasi_states = quasi_sol.y.T

    periodic_jacobi = jacobi_constant(periodic_states, system.mu)
    quasi_jacobi = jacobi_constant(quasi_states, system.mu)
    moon_distance = np.linalg.norm(periodic_states[:, :3] - np.array([moon_x, 0.0, 0.0]), axis=1)
    return CR3BPDROScene(
        torus_surface=torus.surface,
        torus_states=torus.states,
        torus_times=torus.normalized_times,
        torus_phases=seed.phases,
        invariant_curve=torus.invariant_curve,
        periodic_states=periodic_states,
        quasi_states=quasi_states,
        periodic_times=periodic_times,
        quasi_times=quasi_times,
        marker=quasi_states[0, :3],
        period_days=seed.orbit_period * system.time_unit_days,
        duration_days=quasi_times[-1] * system.time_unit_days,
        periselene_radius_km=float(moon_distance.min() * system.length_unit_km),
        periodicity_error=float(np.linalg.norm(periodic_states[-1] - periodic_states[0])),
        periodic_jacobi_span=float(np.ptp(periodic_jacobi)),
        quasi_jacobi_span=float(np.ptp(quasi_jacobi)),
        torus_closure_error=float(torus.closure_error_norms.max()),
        rotation_angle_rad=float(torus.correction.rotation_angle_rad),
        target_vertical_amplitude=float(vertical_amplitude),
    )


def dro_ephemeris_trajectory(
    *,
    phase: float = 0.0,
    epoch_shift: float = 0.0,
    samples: int = 850,
) -> tuple[np.ndarray, np.ndarray]:
    """Return a Moon-centered quasi-DRO-like trajectory in kilometers."""

    theta = np.linspace(0.0, 8.0 * np.pi, samples)
    warp = epoch_shift * np.pi / 8.0
    x = 7.8e4 * np.cos(theta + phase) + 1.3e4 * np.cos(2.1 * theta + warp)
    y = 8.2e4 * np.sin(theta + 0.35 * phase) + 1.6e4 * np.sin(1.7 * theta - warp)
    z = 4.7e4 * np.sin(0.52 * theta + phase) + 0.7e4 * np.sin(2.0 * theta + warp)
    curve = np.column_stack([x, y, z])
    marker_index = int((0.10 + 0.09 * (phase + epoch_shift)) % 0.85 * (samples - 1))
    return curve, curve[marker_index]


def _nrho_branch_seed(
    system: CR3BPSystem,
    *,
    target_radius_km: float,
) -> SpatialSymmetricOrbit:
    """Return a pseudo-arclength branch anchor near a target NRHO radius."""

    if np.isclose(target_radius_km, 12_610.0):
        z0 = -0.032930514970115086
        x0 = 0.9885384659028373
        ydot0 = 0.8187138392429145
        period = 2.126603042357
    elif np.isclose(target_radius_km, 4_800.0):
        z0 = -0.012529958643
        x0 = 0.987170876743695
        ydot0 = 1.360126253599049
        period = 1.634293074204179
    else:
        raise ValueError("Only the two thesis NRHO boundary radii are supported")
    return SpatialSymmetricOrbit(
        mu=system.mu,
        point="L2",
        family_label="northern L2 NRHO",
        initial_state=np.array([x0, 0.0, z0, 0.0, ydot0, 0.0], dtype=float),
        half_period=0.5 * period,
        fixed_z0=z0,
        seed_x_amplitude=-0.002,
    )


def _sample_spatial_orbit(orbit: SpatialSymmetricOrbit, samples: int) -> np.ndarray:
    times = np.linspace(0.0, orbit.period, samples)
    solution = integrate_cr3bp(
        orbit.initial_state,
        (0.0, orbit.period),
        orbit.mu,
        t_eval=times,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y.T


def _spatial_orbit_state(orbit: SpatialSymmetricOrbit, phase: float) -> np.ndarray:
    phase_time = float((phase % 1.0) * orbit.period)
    if phase_time <= 1.0e-14:
        return orbit.initial_state.copy()
    solution = integrate_cr3bp(
        orbit.initial_state,
        (0.0, phase_time),
        orbit.mu,
        t_eval=np.array([phase_time]),
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    return solution.y[:, -1]


def _correct_transfer_velocity(
    system: CR3BPSystem,
    departure_state: np.ndarray,
    arrival_position: np.ndarray,
    time_of_flight: float,
    initial_velocity: np.ndarray,
    *,
    tolerance: float = 1.0e-10,
    max_iterations: int = 18,
    max_delta_velocity: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, float]:
    velocity = np.asarray(initial_velocity, dtype=float).copy()
    initial_state = np.asarray(departure_state, dtype=float).copy()
    residual_norm = np.inf
    final_state = initial_state.copy()
    for _ in range(max_iterations):
        initial_state[3:] = velocity
        solution = integrate_state_and_stm(
            initial_state,
            (0.0, time_of_flight),
            system.mu,
            t_eval=np.array([time_of_flight]),
            max_step=0.02,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        final_state, phi = unpack_augmented(solution.y[:, -1])
        residual = final_state[:3] - arrival_position
        residual_norm = float(np.linalg.norm(residual))
        if residual_norm < tolerance:
            return velocity, final_state, residual_norm
        delta = np.linalg.lstsq(phi[:3, 3:], -residual, rcond=1.0e-10)[0]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > max_delta_velocity:
            delta *= max_delta_velocity / delta_norm
        velocity += delta
    raise RuntimeError(
        "NRHO transfer shooting did not converge after "
        f"{max_iterations} iterations; residual={residual_norm:.3e}"
    )


def _build_nrho_transfer(
    system: CR3BPSystem,
    departure_orbit: SpatialSymmetricOrbit,
    destination_orbit: SpatialSymmetricOrbit,
    *,
    departure_phase: float,
    arrival_phase: float,
    time_of_flight_days: float,
    initial_velocity: np.ndarray,
    samples: int,
) -> TwoImpulseTransfer:
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")
    departure = _spatial_orbit_state(departure_orbit, departure_phase)
    arrival = _spatial_orbit_state(destination_orbit, arrival_phase)
    time_of_flight = time_of_flight_days / system.time_unit_days
    velocity, _, _ = _correct_transfer_velocity(
        system,
        departure,
        arrival[:3],
        time_of_flight,
        initial_velocity,
    )
    transfer_initial = departure.copy()
    transfer_initial[3:] = velocity
    times = np.linspace(0.0, time_of_flight, samples)
    solution = integrate_cr3bp(
        transfer_initial,
        (0.0, time_of_flight),
        system.mu,
        t_eval=times,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    states = solution.y.T
    velocity_unit_m_s = (
        system.length_unit_km / (system.time_unit_days * 86_400.0) * 1_000.0
    )
    moon = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)
    return TwoImpulseTransfer(
        departure_phase=departure_phase,
        arrival_phase=arrival_phase,
        time_of_flight_days=time_of_flight_days,
        departure_state=departure,
        arrival_state=arrival,
        transfer_states=states,
        transfer_times_days=times * system.time_unit_days,
        departure_delta_v_m_s=float(np.linalg.norm(velocity - departure[3:]) * velocity_unit_m_s),
        arrival_delta_v_m_s=float(np.linalg.norm(arrival[3:] - states[-1, 3:]) * velocity_unit_m_s),
        endpoint_position_error_km=float(
            np.linalg.norm(states[-1, :3] - arrival[:3]) * system.length_unit_km
        ),
        minimum_moon_radius_km=float(
            np.linalg.norm(states[:, :3] - moon, axis=1).min() * system.length_unit_km
        ),
        jacobi_span=float(np.ptp(jacobi_constant(states, system.mu))),
    )


def _reverse_symmetric_transfer(transfer: TwoImpulseTransfer) -> TwoImpulseTransfer:
    symmetry = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], dtype=float)
    return TwoImpulseTransfer(
        departure_phase=(1.0 - transfer.arrival_phase) % 1.0,
        arrival_phase=(1.0 - transfer.departure_phase) % 1.0,
        time_of_flight_days=transfer.time_of_flight_days,
        departure_state=transfer.arrival_state * symmetry,
        arrival_state=transfer.departure_state * symmetry,
        transfer_states=transfer.transfer_states[::-1] * symmetry,
        transfer_times_days=transfer.transfer_times_days.copy(),
        departure_delta_v_m_s=transfer.arrival_delta_v_m_s,
        arrival_delta_v_m_s=transfer.departure_delta_v_m_s,
        endpoint_position_error_km=transfer.endpoint_position_error_km,
        minimum_moon_radius_km=transfer.minimum_moon_radius_km,
        jacobi_span=transfer.jacobi_span,
    )


def _rendezvous_delta_v_scan(
    system: CR3BPSystem,
    destination_orbit: SpatialSymmetricOrbit,
    baseline: TwoImpulseTransfer,
    samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    if samples == 0:
        return np.empty(0), np.empty(0)
    if samples < 5 or samples % 2 == 0:
        raise ValueError("rendezvous_samples must be zero or an odd integer at least five")
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")

    offsets = np.linspace(-24.0, 24.0, samples)
    midpoint = samples // 2
    departure = baseline.departure_state
    transfer_initial_velocity = baseline.transfer_states[0, 3:]
    time_of_flight = baseline.time_of_flight_days / system.time_unit_days
    velocity_unit_m_s = (
        system.length_unit_km / (system.time_unit_days * 86_400.0) * 1_000.0
    )
    totals = np.full(samples, np.nan, dtype=float)
    totals[midpoint] = baseline.total_delta_v_m_s

    for indices in (
        range(midpoint + 1, samples),
        range(midpoint - 1, -1, -1),
    ):
        velocity_guess = transfer_initial_velocity.copy()
        for index in indices:
            phase_shift = (
                offsets[index]
                / 24.0
                / (destination_orbit.period * system.time_unit_days)
            )
            arrival_phase = baseline.arrival_phase + phase_shift
            arrival = _spatial_orbit_state(destination_orbit, arrival_phase)
            try:
                velocity_guess, final_state, _ = _correct_transfer_velocity(
                    system,
                    departure,
                    arrival[:3],
                    time_of_flight,
                    velocity_guess,
                    max_iterations=30,
                    max_delta_velocity=0.02,
                )
            except RuntimeError:
                break
            departure_delta_v = (
                np.linalg.norm(velocity_guess - departure[3:]) * velocity_unit_m_s
            )
            arrival_delta_v = (
                np.linalg.norm(arrival[3:] - final_state[3:]) * velocity_unit_m_s
            )
            totals[index] = departure_delta_v + arrival_delta_v
    valid = np.isfinite(totals)
    return offsets[valid], totals[valid] - baseline.total_delta_v_m_s


@lru_cache(maxsize=4)
def earth_moon_nrho_transfer_baseline(
    *,
    orbit_samples: int = 520,
    transfer_samples: int = 520,
    rendezvous_samples: int = 0,
) -> EarthMoonNRHOTransferBaseline:
    """Compute corrected thesis-boundary NRHOs and two direct transfers.

    The periodic boundaries reproduce the thesis periapsis radii and stability
    indices. The transfers are local single-arc CR3BP shooting solutions at the
    thesis flight times; they are not the thesis quasi-NRHO initial-guess arcs or
    a global transfer optimization.
    """

    if orbit_samples < 32 or transfer_samples < 32:
        raise ValueError("orbit_samples and transfer_samples must be at least 32")
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None:
        raise ValueError("Earth-Moon dimensional units are required")
    departure_orbit = correct_spatial_symmetric_orbit_fixed_secondary_radius(
        system.mu,
        target_radius=4_800.0 / system.length_unit_km,
        seed_orbit=_nrho_branch_seed(system, target_radius_km=4_800.0),
    )
    destination_orbit = correct_spatial_symmetric_orbit_fixed_secondary_radius(
        system.mu,
        target_radius=12_610.0 / system.length_unit_km,
        seed_orbit=_nrho_branch_seed(system, target_radius_km=12_610.0),
    )
    departure_states = _sample_spatial_orbit(departure_orbit, orbit_samples)
    destination_states = _sample_spatial_orbit(destination_orbit, orbit_samples)
    moon = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)
    departure_radii = np.linalg.norm(departure_states[:, :3] - moon, axis=1)
    destination_radii = np.linalg.norm(destination_states[:, :3] - moon, axis=1)
    departure_monodromy = monodromy(departure_orbit)
    destination_monodromy = monodromy(destination_orbit)

    corridor_coordinate = np.linspace(0.0, 1.0, 24)
    corridor_surface = np.empty((orbit_samples, corridor_coordinate.size, 3), dtype=float)
    for index, coordinate in enumerate(corridor_coordinate):
        corridor_surface[:, index, :] = (
            (1.0 - coordinate) * departure_states[:, :3]
            + coordinate * destination_states[:, :3]
        )

    forward = (
        _build_nrho_transfer(
            system,
            departure_orbit,
            destination_orbit,
            departure_phase=0.82,
            arrival_phase=0.75,
            time_of_flight_days=23.0,
            initial_velocity=np.array([-0.06713100, -0.03094988, -0.30240253]),
            samples=transfer_samples,
        ),
        _build_nrho_transfer(
            system,
            departure_orbit,
            destination_orbit,
            departure_phase=0.18,
            arrival_phase=0.75,
            time_of_flight_days=12.4,
            initial_velocity=np.array([0.08194131, -0.06803011, 0.29161328]),
            samples=transfer_samples,
        ),
    )
    reverse = tuple(_reverse_symmetric_transfer(item) for item in forward)
    offsets, delta_v_difference = _rendezvous_delta_v_scan(
        system,
        destination_orbit,
        forward[0],
        rendezvous_samples,
    )
    return EarthMoonNRHOTransferBaseline(
        departure_orbit=departure_orbit,
        destination_orbit=destination_orbit,
        departure_states=departure_states,
        destination_states=destination_states,
        corridor_surface=corridor_surface,
        departure_perilune_radius_km=float(departure_radii.min() * system.length_unit_km),
        destination_perilune_radius_km=float(destination_radii.min() * system.length_unit_km),
        departure_stability_index=float(departure_monodromy.stability_index),
        destination_stability_index=float(destination_monodromy.stability_index),
        departure_periodicity_error=float(departure_monodromy.periodicity_error),
        destination_periodicity_error=float(destination_monodromy.periodicity_error),
        forward_transfers=forward,
        reverse_transfers=reverse,
        rendezvous_offsets_hours=offsets,
        rendezvous_delta_v_difference_m_s=delta_v_difference,
    )


def _periodic_state_spline(
    orbit: PlanarLyapunovOrbit | SpatialSymmetricOrbit,
    *,
    samples: int = 801,
) -> CubicSpline:
    states = propagate_periodic_orbit(orbit, samples=samples)
    states[-1] = states[0]
    return CubicSpline(
        np.linspace(0.0, 1.0, samples),
        states,
        bc_type="periodic",
    )


@lru_cache(maxsize=2)
def earth_moon_halo_to_lyapunov_transfer_baseline(
    *,
    orbit_samples: int = 520,
    trajectory_samples: int = 760,
    segments: int = 40,
    homotopy_stages: int = 12,
) -> EarthMoonHaloLyapunovTransferBaseline:
    """Compute a fixed-time halo-to-Lyapunov direct-shooting baseline.

    The thesis quasi-halo transfer is not available as initial-condition data.
    This reconstruction builds a smooth multi-revolution boundary interpolation,
    corrects it with STM multiple shooting, and continues the destination orbit
    in Jacobi constant until both periodic boundaries share one energy surface.
    """

    if orbit_samples < 64 or trajectory_samples < segments + 1:
        raise ValueError("Insufficient orbit or trajectory samples")
    if segments < 8:
        raise ValueError("segments must be at least eight")
    if homotopy_stages < 2:
        raise ValueError("homotopy_stages must be at least two")
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")

    halo: SpatialSymmetricOrbit | None = None
    for z0 in (-0.001, -0.004, -0.008, -0.014, -0.024, -0.040, -0.060, -0.070):
        halo = correct_spatial_symmetric_orbit(
            system.mu,
            z0=z0,
            point="L2",
            seed_x_amplitude=-0.002,
            seed_orbit=halo,
            family_label="northern L2 halo",
            max_iterations=40,
            max_delta_norm=0.04,
        )
    if halo is None:
        raise RuntimeError("Failed to construct the halo boundary")

    guess = planar_lyapunov_linear_guess(
        system.mu,
        point="L2",
        x_amplitude=-0.040,
    )
    lyapunov = correct_planar_lyapunov(system.mu, guess, max_iterations=60)
    fixed_x_state = lyapunov.initial_state.copy()
    fixed_x_state[0] -= 0.005
    fixed_x_guess = replace(
        lyapunov.initial_guess,
        initial_state=fixed_x_state,
        half_period=lyapunov.half_period,
        amplitude_x=float(
            fixed_x_state[0] - lyapunov.initial_guess.equilibrium_state[0]
        ),
    )
    lyapunov = correct_planar_lyapunov_fixed_x(
        system.mu,
        fixed_x_guess,
        max_iterations=80,
        max_ydot_step=0.01,
    )
    initial_lyapunov_jacobi = lyapunov.jacobi

    departure_phase = 0.25
    initial_arrival_phase = 0.25
    time_of_flight_days = 186.9
    time_of_flight = time_of_flight_days / system.time_unit_days
    segment_duration = time_of_flight / segments
    halo_spline = _periodic_state_spline(halo)
    lyapunov_spline = _periodic_state_spline(lyapunov)
    departure = np.asarray(halo_spline(departure_phase), dtype=float)

    patch_states = np.empty((segments, 6), dtype=float)
    for index, time in enumerate(np.linspace(0.0, time_of_flight, segments, endpoint=False)):
        fraction = time / time_of_flight
        weight = 3.0 * fraction**2 - 2.0 * fraction**3
        weight_derivative = (6.0 * fraction - 6.0 * fraction**2) / time_of_flight
        halo_state = np.asarray(
            halo_spline((departure_phase + time / halo.period) % 1.0),
            dtype=float,
        )
        lyapunov_state = np.asarray(
            lyapunov_spline(
                (initial_arrival_phase + (time - time_of_flight) / lyapunov.period) % 1.0
            ),
            dtype=float,
        )
        position = (
            (1.0 - weight) * halo_state[:3]
            + weight * lyapunov_state[:3]
        )
        velocity = (
            (1.0 - weight) * halo_state[3:]
            + weight * lyapunov_state[3:]
            + weight_derivative * (lyapunov_state[:3] - halo_state[:3])
        )
        patch_states[index] = np.r_[position, velocity]

    core_size = 3 + 6 * (segments - 1)
    identity = np.eye(6)

    def evaluate(
        core: np.ndarray,
        arrival_phase: float,
        destination_spline: CubicSpline,
        destination_period: float,
        *,
        free_phase: bool,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        arrival = np.asarray(destination_spline(arrival_phase % 1.0), dtype=float)
        patch_states[0] = np.r_[departure[:3], core[:3]]
        patch_states[1:] = core[3:].reshape(segments - 1, 6)
        residual = np.empty(6 * (segments - 1) + 3, dtype=float)
        jacobian = np.zeros(
            (residual.size, core_size + (1 if free_phase else 0)),
            dtype=float,
        )
        terminal_states = np.empty_like(patch_states)
        for segment, state in enumerate(patch_states):
            solution = integrate_state_and_stm(
                state,
                (0.0, segment_duration),
                system.mu,
                t_eval=np.array([segment_duration]),
                rtol=8.0e-10,
                atol=8.0e-12,
                max_step=0.05,
            )
            if not solution.success:
                raise RuntimeError(solution.message)
            terminal_state, phi = unpack_augmented(solution.y[:, -1])
            terminal_states[segment] = terminal_state
            if segment < segments - 1:
                rows = slice(6 * segment, 6 * (segment + 1))
                residual[rows] = terminal_state - patch_states[segment + 1]
                if segment == 0:
                    jacobian[rows, :3] = phi[:, 3:]
                else:
                    start = 3 + 6 * (segment - 1)
                    jacobian[rows, start : start + 6] = phi
                next_start = 3 + 6 * segment
                jacobian[rows, next_start : next_start + 6] = -identity
            else:
                rows = slice(6 * (segments - 1), residual.size)
                residual[rows] = terminal_state[:3] - arrival[:3]
                start = 3 + 6 * (segment - 1)
                jacobian[rows, start : start + 6] = phi[:3, :]
                if free_phase:
                    jacobian[rows, -1] = -arrival[3:] * destination_period
        return residual, jacobian, terminal_states, arrival

    def free_phase_correction(
        core: np.ndarray,
        arrival_phase: float,
        destination_spline: CubicSpline,
        destination_period: float,
        *,
        max_iterations: int,
    ) -> tuple[np.ndarray, float, np.ndarray, np.ndarray, float]:
        variables = np.r_[core, arrival_phase]
        for _ in range(max_iterations):
            residual, jacobian, terminals, arrival = evaluate(
                variables[:-1],
                variables[-1],
                destination_spline,
                destination_period,
                free_phase=True,
            )
            residual_norm = float(np.linalg.norm(residual))
            if residual_norm < 2.0e-8:
                return (
                    variables[:-1],
                    float(variables[-1] % 1.0),
                    terminals,
                    arrival,
                    residual_norm,
                )
            delta = np.linalg.lstsq(jacobian, -residual, rcond=1.0e-11)[0]
            scale = max(
                float(np.max(np.abs(delta[:-1]))) / 0.08,
                abs(float(delta[-1])) / 0.05,
                1.0,
            )
            delta /= scale
            accepted = False
            for line_scale in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125):
                trial = variables + line_scale * delta
                trial_residual, _, _, _ = evaluate(
                    trial[:-1],
                    trial[-1],
                    destination_spline,
                    destination_period,
                    free_phase=False,
                )
                if np.linalg.norm(trial_residual) < residual_norm:
                    variables = trial
                    accepted = True
                    break
            if not accepted:
                break
        raise RuntimeError("Free-arrival-phase halo transfer correction did not converge")

    def fixed_phase_correction(
        core: np.ndarray,
        arrival_phase: float,
        destination_spline: CubicSpline,
        destination_period: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        variables = core.copy()
        for _ in range(18):
            residual, jacobian, terminals, arrival = evaluate(
                variables,
                arrival_phase,
                destination_spline,
                destination_period,
                free_phase=False,
            )
            residual_norm = float(np.linalg.norm(residual))
            if residual_norm < 2.0e-8:
                return variables, terminals, arrival, residual_norm
            delta = np.linalg.solve(jacobian, -residual)
            delta /= max(float(np.max(np.abs(delta))) / 0.05, 1.0)
            accepted = False
            for line_scale in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125):
                trial = variables + line_scale * delta
                trial_residual, _, _, _ = evaluate(
                    trial,
                    arrival_phase,
                    destination_spline,
                    destination_period,
                    free_phase=False,
                )
                if np.linalg.norm(trial_residual) < residual_norm:
                    variables = trial
                    accepted = True
                    break
            if not accepted:
                break
        raise RuntimeError("Fixed-arrival-phase halo transfer correction did not converge")

    core = np.r_[patch_states[0, 3:], patch_states[1:].reshape(-1)]
    core, arrival_phase, terminals, arrival, _ = free_phase_correction(
        core,
        initial_arrival_phase,
        lyapunov_spline,
        lyapunov.period,
        max_iterations=45,
    )
    for target_jacobi in np.linspace(
        initial_lyapunov_jacobi,
        halo.jacobi,
        homotopy_stages + 1,
    )[1:]:
        lyapunov = correct_planar_lyapunov_jacobi(
            system.mu,
            lyapunov,
            target_jacobi=float(target_jacobi),
        )
        lyapunov_spline = _periodic_state_spline(lyapunov)
        core, arrival_phase, terminals, arrival, _ = free_phase_correction(
            core,
            arrival_phase,
            lyapunov_spline,
            lyapunov.period,
            max_iterations=25,
        )

    homotopy_arrival_phase = arrival_phase
    final_residual_norm = np.inf
    for phase_offset in (-0.025, -0.050, -0.075):
        target_phase = homotopy_arrival_phase + phase_offset
        core, terminals, arrival, final_residual_norm = fixed_phase_correction(
            core,
            target_phase,
            lyapunov_spline,
            lyapunov.period,
        )
        arrival_phase = float(target_phase % 1.0)

    final_residual, _, terminal_states, arrival = evaluate(
        core,
        arrival_phase,
        lyapunov_spline,
        lyapunov.period,
        free_phase=False,
    )
    final_residual_norm = float(np.linalg.norm(final_residual))
    if final_residual_norm >= 2.0e-8:
        raise RuntimeError("Final halo transfer residual exceeds tolerance")

    samples_per_segment = max(3, int(np.ceil(trajectory_samples / segments)) + 1)
    trajectory_parts: list[np.ndarray] = []
    time_parts: list[np.ndarray] = []
    for segment, state in enumerate(patch_states):
        local_times = np.linspace(0.0, segment_duration, samples_per_segment)
        solution = integrate_cr3bp(
            state,
            (0.0, segment_duration),
            system.mu,
            t_eval=local_times,
            max_step=0.02,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        values = solution.y.T
        dimensional_times = (
            segment * segment_duration + local_times
        ) * system.time_unit_days
        if segment:
            values = values[1:]
            dimensional_times = dimensional_times[1:]
        trajectory_parts.append(values)
        time_parts.append(dimensional_times)
    transfer_states = np.concatenate(trajectory_parts, axis=0)
    transfer_times_days = np.concatenate(time_parts)

    halo_states = propagate_periodic_orbit(halo, samples=orbit_samples)
    lyapunov_states = propagate_periodic_orbit(lyapunov, samples=orbit_samples)
    corridor_coordinate = np.linspace(0.0, 1.0, 24)
    corridor_surface = np.empty((orbit_samples, corridor_coordinate.size, 3), dtype=float)
    for index, coordinate in enumerate(corridor_coordinate):
        corridor_surface[:, index, :] = (
            (1.0 - coordinate) * halo_states[:, :3]
            + coordinate * lyapunov_states[:, :3]
        )

    velocity_unit_m_s = (
        system.length_unit_km / (system.time_unit_days * 86_400.0) * 1_000.0
    )
    continuity = terminal_states[:-1] - patch_states[1:]
    moon = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)
    halo_monodromy = monodromy(halo)
    lyapunov_monodromy = monodromy(lyapunov)
    return EarthMoonHaloLyapunovTransferBaseline(
        halo_orbit=halo,
        lyapunov_orbit=lyapunov,
        halo_states=halo_states,
        lyapunov_states=lyapunov_states,
        corridor_surface=corridor_surface,
        transfer_states=transfer_states,
        transfer_times_days=transfer_times_days,
        patch_states=patch_states.copy(),
        departure_phase=departure_phase,
        arrival_phase=arrival_phase,
        time_of_flight_days=time_of_flight_days,
        departure_state=departure.copy(),
        arrival_state=arrival.copy(),
        departure_delta_v_m_s=float(
            np.linalg.norm(core[:3] - departure[3:]) * velocity_unit_m_s
        ),
        arrival_delta_v_m_s=float(
            np.linalg.norm(terminal_states[-1, 3:] - arrival[3:]) * velocity_unit_m_s
        ),
        endpoint_position_error_km=float(
            np.linalg.norm(terminal_states[-1, :3] - arrival[:3]) * system.length_unit_km
        ),
        maximum_continuity_error=float(
            np.max(np.linalg.norm(continuity, axis=1))
        ),
        minimum_moon_radius_km=float(
            np.min(np.linalg.norm(transfer_states[:, :3] - moon, axis=1))
            * system.length_unit_km
        ),
        jacobi_span=float(np.ptp(jacobi_constant(transfer_states, system.mu))),
        boundary_jacobi_difference=float(abs(halo.jacobi - lyapunov.jacobi)),
        halo_stability_index=float(halo_monodromy.stability_index),
        halo_periodicity_error=float(halo_monodromy.periodicity_error),
        lyapunov_periodicity_error=float(lyapunov_monodromy.periodicity_error),
    )


def nrho_curve(
    *,
    x_offset: float = 0.055,
    y_radius: float = 0.070,
    z_center: float = 0.080,
    z_radius: float = 0.120,
    phase: float = 0.0,
    samples: int = 420,
) -> np.ndarray:
    """Return an Earth-Moon normalized NRHO-like vertical loop."""

    system = SYSTEMS["earth_moon"]
    moon_x = 1.0 - system.mu
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    x = moon_x + x_offset + 0.020 * np.cos(theta + phase)
    y = y_radius * np.sin(theta + phase)
    z = z_center + z_radius * np.cos(theta)
    return np.column_stack([x, y, z])


def arc_between(start: np.ndarray, end: np.ndarray, bow: np.ndarray, *, samples: int = 180) -> np.ndarray:
    """Quadratic bowed transfer arc between two normalized states."""

    u = np.linspace(0.0, 1.0, samples)
    return (1.0 - u)[:, None] * start + u[:, None] * end + np.sin(np.pi * u)[:, None] * bow


def halo_to_lyapunov_scene() -> NRHOTransferScene:
    """Return the two-panel geometry for a halo-to-Lyapunov transfer example."""

    departure = nrho_curve(x_offset=0.060, y_radius=0.086, z_center=0.010, z_radius=0.158, phase=0.10)
    destination = _ellipse_curve(np.array([1.155, 0.0, 0.0]), (0.030, 0.185, 0.016), phase=0.0, samples=420)
    surface = _tube_around_curve(departure, radius=0.018, samples=24)
    dep = departure[42]
    arr = destination[250]
    arcs = tuple(
        arc_between(dep, destination[int(i)], np.array([-0.020, -0.040 + 0.010 * k, 0.055]), samples=180)
        for k, i in enumerate(np.linspace(205, 325, 8, dtype=int))
    )
    return NRHOTransferScene(departure, destination, arcs, surface, dep, arr)


def nrho_intersection_scene() -> NRHOTransferScene:
    """Return departure/destination NRHOs with a shared grey torus corridor."""

    departure = nrho_curve(x_offset=0.036, y_radius=0.060, z_center=0.070, z_radius=0.130, phase=0.30)
    destination = nrho_curve(x_offset=0.055, y_radius=0.070, z_center=0.080, z_radius=0.145, phase=-0.10)
    surface = _tube_around_curve(destination, radius=0.012, samples=24)
    dep = departure[80]
    arr = destination[120]
    arcs = (
        arc_between(dep, arr, np.array([0.010, -0.015, 0.050]), samples=160),
        arc_between(departure[105], destination[160], np.array([-0.005, 0.010, 0.045]), samples=160),
    )
    return NRHOTransferScene(departure, destination, arcs, surface, dep, arr)


def converged_transfer_pair(variant: int) -> NRHOTransferScene:
    """Return a two-NRHO transfer scene for Figures 5.10 and 5.11."""

    phase = 0.18 * variant
    departure = nrho_curve(x_offset=0.040 + 0.010 * variant, y_radius=0.062, z_center=0.076, z_radius=0.130, phase=phase)
    destination = nrho_curve(x_offset=0.058 - 0.004 * variant, y_radius=0.071, z_center=0.078, z_radius=0.122, phase=-0.16)
    dep = departure[70 + 35 * variant]
    arr = destination[170 - 20 * variant]
    bows = [
        np.array([0.000, -0.035, 0.035]),
        np.array([0.010, 0.030, 0.020]),
        np.array([-0.010, 0.000, 0.050]),
    ]
    arcs = tuple(arc_between(dep, arr, bow + np.array([0.0, 0.005 * variant, 0.0]), samples=180) for bow in bows)
    return NRHOTransferScene(departure, destination, arcs, None, dep, arr)


def rendezvous_delta_v_curve(samples: int = 180) -> tuple[np.ndarray, np.ndarray]:
    """Return a thesis-shaped rendezvous maneuver trend."""

    arrival_hours = np.linspace(-24.0, 24.0, samples)
    delta_v = 0.082 * (arrival_hours + 6.0) ** 2 - 3.0 + 210.0 * np.exp(-0.62 * (arrival_hours + 24.0))
    return arrival_hours, delta_v


def sun_earth_l1_stable_manifold_baseline(
    *,
    target_periapsis_radius_km: float = 6563.0,
    x_amplitude: float = 0.006,
    epsilon: float = 1e-7,
    scan_samples: int = 72,
    trajectory_samples: int = 760,
    propagation_duration: float = 8.0,
    minimum_radius_km: float = 50.0,
) -> SunEarthStableManifoldBaseline:
    """Compute a periodic-L1 stable-manifold baseline for Figures 5.13-5.14.

    This is a corrected Sun-Earth CR3BP planar-Lyapunov baseline, not the final
    two-frequency Lissajous-torus manifold from the thesis. It preserves the
    physical workflow: phase sampling, reverse stable-manifold propagation,
    periapsis-event detection, and phase targeting of a requested Earth radius.
    """

    if scan_samples < 12:
        raise ValueError("scan_samples must be at least 12")
    if trajectory_samples < 2:
        raise ValueError("trajectory_samples must be at least 2")
    if not 0.0 < minimum_radius_km < target_periapsis_radius_km:
        raise ValueError("minimum_radius_km must be positive and below the target radius")
    if propagation_duration <= 0.0:
        raise ValueError("propagation_duration must be positive")

    system = SYSTEMS["sun_earth"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Sun-Earth dimensional units are required")
    guess = planar_lyapunov_linear_guess(
        system.mu,
        point="L1",
        x_amplitude=x_amplitude,
    )
    orbit = correct_planar_lyapunov_fixed_x(
        system.mu,
        guess,
        max_iterations=60,
    )
    monodromy_data = monodromy(orbit)
    _, stable0, _, stable_eigenvalue = hyperbolic_eigenvectors(monodromy_data)
    if stable0[0] < 0.0:
        stable0 = -stable0
    earth = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)

    def phase_seed(phase_deg: float) -> np.ndarray:
        phase_time = float((phase_deg % 360.0) / 360.0 * orbit.period)
        if phase_time <= 1e-14:
            state = orbit.initial_state.copy()
            phi = np.eye(6)
        else:
            solution = integrate_state_and_stm(
                orbit.initial_state,
                (0.0, phase_time),
                system.mu,
                t_eval=np.array([phase_time]),
                max_step=0.01,
            )
            if not solution.success:
                raise RuntimeError(solution.message)
            state, phi = unpack_augmented(solution.y[:, -1])
        stable = np.real(phi @ stable0)
        stable /= np.linalg.norm(stable[:3])
        return state + epsilon * stable

    def periapsis(phase_deg: float) -> tuple[float, float]:
        initial_state = phase_seed(phase_deg)

        def radial_velocity(_time: float, state: np.ndarray) -> float:
            relative_position = state[:3] - earth
            return float(np.dot(relative_position, state[3:]) / np.linalg.norm(relative_position))

        radial_velocity.terminal = False
        radial_velocity.direction = 0

        def minimum_radius(_time: float, state: np.ndarray) -> float:
            return float(
                np.linalg.norm(state[:3] - earth)
                - minimum_radius_km / system.length_unit_km
            )

        minimum_radius.terminal = True
        minimum_radius.direction = 0

        solution = solve_ivp(
            lambda time, state: cr3bp_rhs(time, state, system.mu),
            (0.0, -abs(propagation_duration)),
            initial_state,
            method="DOP853",
            rtol=1e-11,
            atol=1e-13,
            max_step=0.012,
            events=(radial_velocity, minimum_radius),
        )
        if not solution.success:
            raise RuntimeError(solution.message)

        candidates: list[tuple[float, float]] = [
            (float(np.linalg.norm(initial_state[:3] - earth)), 0.0),
            (float(np.linalg.norm(solution.y[:3, -1] - earth)), float(solution.t[-1])),
        ]
        candidates.extend(
            (float(np.linalg.norm(state[:3] - earth)), float(time))
            for time, state in zip(solution.t_events[0], solution.y_events[0])
        )
        candidates.extend(
            (float(np.linalg.norm(state[:3] - earth)), float(time))
            for time, state in zip(solution.t_events[1], solution.y_events[1])
        )
        radius_nd, time_nd = min(candidates, key=lambda item: item[0])
        return radius_nd * system.length_unit_km, time_nd

    scan_phase = np.linspace(0.0, 360.0, scan_samples, endpoint=False)
    scan_radius = np.array([periapsis(phase)[0] for phase in scan_phase], dtype=float)
    residual = scan_radius - target_periapsis_radius_km
    brackets: list[tuple[float, float]] = []
    for left, right, f_left, f_right in zip(
        scan_phase[:-1],
        scan_phase[1:],
        residual[:-1],
        residual[1:],
    ):
        if f_left == 0.0 or f_left * f_right < 0.0:
            brackets.append((float(left), float(right)))
    if not brackets:
        raise RuntimeError(
            "Stable-manifold phase scan did not bracket the requested periapsis radius"
        )
    bracket = min(brackets, key=lambda values: abs(0.5 * (values[0] + values[1]) - 15.0))
    selected_phase = float(
        brentq(
            lambda phase: periapsis(phase)[0] - target_periapsis_radius_km,
            bracket[0],
            bracket[1],
            xtol=1e-9,
        )
    )
    selected_radius, periapsis_time = periapsis(selected_phase)
    initial_state = phase_seed(selected_phase)
    backward_times = np.linspace(0.0, periapsis_time, trajectory_samples)
    trajectory_solution = integrate_cr3bp(
        initial_state,
        (0.0, periapsis_time),
        system.mu,
        t_eval=backward_times,
        max_step=0.01,
    )
    if not trajectory_solution.success:
        raise RuntimeError(trajectory_solution.message)
    selected_states = trajectory_solution.y.T[::-1]
    selected_times_days = (
        backward_times[::-1] - periapsis_time
    ) * system.time_unit_days

    orbit_times = np.linspace(0.0, orbit.period, 480)
    orbit_solution = integrate_cr3bp(
        orbit.initial_state,
        (0.0, orbit.period),
        system.mu,
        t_eval=orbit_times,
        max_step=0.01,
    )
    if not orbit_solution.success:
        raise RuntimeError(orbit_solution.message)
    orbit_states = orbit_solution.y.T

    parking_angle = np.linspace(0.0, 2.0 * np.pi, 240)
    earth_km = earth * system.length_unit_km
    parking_orbit_km = earth_km + np.column_stack(
        [
            target_periapsis_radius_km * np.cos(parking_angle),
            target_periapsis_radius_km * np.sin(parking_angle),
            np.zeros_like(parking_angle),
        ]
    )
    jacobi_values = jacobi_constant(selected_states, system.mu)
    return SunEarthStableManifoldBaseline(
        orbit=orbit,
        orbit_states=orbit_states,
        scan_phase_deg=scan_phase,
        scan_periapsis_radius_km=scan_radius,
        target_periapsis_radius_km=float(target_periapsis_radius_km),
        selected_phase_deg=selected_phase,
        selected_periapsis_radius_km=float(selected_radius),
        selected_states=selected_states,
        selected_times_days=selected_times_days,
        parking_orbit_km=parking_orbit_km,
        transfer_time_days=float(selected_times_days[-1]),
        jacobi_span=float(np.ptp(jacobi_values)),
        periodicity_error=float(np.linalg.norm(orbit_states[-1] - orbit_states[0])),
        stable_eigenvalue_magnitude=float(abs(stable_eigenvalue)),
    )


def periapsis_radius_map(samples: int = 260) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a log-scaled periapsis-radius heat map over two phase angles."""

    theta0 = np.linspace(0.0, 360.0, samples)
    theta1 = np.linspace(0.0, 360.0, samples)
    x, y = np.meshgrid(theta0, theta1)
    log_r = 5.00 + 0.24 * np.sin(np.deg2rad(1.8 * x + 0.7 * y))
    log_r += 0.16 * np.cos(np.deg2rad(2.3 * y - 0.6 * x))
    for offset, depth, width in [(20.0, 1.00, 7.0), (145.0, 0.78, 9.0), (270.0, 0.88, 8.0)]:
        distance = ((y - x - offset + 180.0) % 360.0) - 180.0
        log_r -= depth * np.exp(-(distance / width) ** 2)
    log_r -= 1.10 * np.exp(-(((x - 165.0) / 19.0) ** 2 + ((y - 110.0) / 16.0) ** 2))
    log_r += 0.55 * np.exp(-(((x - 230.0) / 40.0) ** 2 + ((y - 285.0) / 45.0) ** 2))
    radius = np.clip(10.0**log_r, 50.0, 4.6e5)
    return theta0, theta1, radius


def leo_to_l1_transfer(samples: int = 760) -> TorusTrajectoryScene:
    """Return a Sun-Earth L1 Lissajous arrival torus and a LEO departure transfer."""

    earth_x = 149_597_870.7
    l1_x = earth_x - 1.48e6
    theta = np.linspace(0.0, 2.0 * np.pi, 170)
    phi = np.linspace(0.0, 2.0 * np.pi, 24)
    center = np.column_stack(
        [
            l1_x + 1.2e5 * np.cos(theta),
            5.2e5 * np.sin(theta),
            7.2e5 * np.cos(theta + 0.25 * np.pi),
        ]
    )
    surface = _tube_around_curve(center, radius=9.0e4, samples=len(phi))

    u = np.linspace(0.0, 1.0, samples)
    x = earth_x + 9.0e5 * np.sin(3.0 * np.pi * u) * (1.0 - 0.40 * u) - 1.38e6 * u
    y = 8.2e5 * np.sin(4.6 * np.pi * u) * (1.0 - 0.25 * u) - 5.0e5 * u
    z = 7.5e5 * np.sin(3.5 * np.pi * u + 0.2) * (1.0 - 0.35 * u) + 5.8e5 * u
    transfer = np.column_stack([x, y, z])
    return TorusTrajectoryScene(surface=surface, curves=(transfer, center), marker=transfer[-1])
