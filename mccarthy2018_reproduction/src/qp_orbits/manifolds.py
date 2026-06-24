"""Periodic-orbit stability and invariant manifold utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cr3bp import integrate_cr3bp
from .periodic_orbits import (
    PlanarLyapunovOrbit,
    SpatialSymmetricOrbit,
    correct_spatial_symmetric_orbit_fixed_secondary_radius,
    planar_lyapunov_family,
    propagate_periodic_orbit,
    spatial_symmetric_family,
    spatial_symmetric_pseudo_arclength_family,
)
from .variational import integrate_state_and_stm, unpack_augmented


@dataclass(frozen=True)
class MonodromyData:
    """Monodromy matrix and eigensystem for a periodic orbit."""

    matrix: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    terminal_state: np.ndarray
    periodicity_error: float

    @property
    def stability_index(self) -> float:
        lambda_max = float(np.max(np.abs(self.eigenvalues)))
        return 0.5 * (lambda_max + 1.0 / lambda_max)


@dataclass(frozen=True)
class ManifoldSeed:
    """A local stable or unstable manifold seed at a periodic-orbit point."""

    orbit_state: np.ndarray
    perturbed_state: np.ndarray
    time_on_orbit: float
    branch_sign: int
    kind: str


@dataclass(frozen=True)
class PeriodicManifoldSample:
    """Corrected periodic orbit plus propagated local invariant manifolds."""

    orbit: SpatialSymmetricOrbit
    orbit_curve: np.ndarray
    stable: tuple[np.ndarray, ...]
    unstable: tuple[np.ndarray, ...]
    monodromy: MonodromyData


def monodromy(orbit: PlanarLyapunovOrbit) -> MonodromyData:
    """Compute the monodromy matrix for a corrected periodic orbit."""

    sol = integrate_state_and_stm(orbit.initial_state, (0.0, orbit.period), orbit.mu)
    if not sol.success:
        raise RuntimeError(sol.message)
    terminal_state, matrix = unpack_augmented(sol.y[:, -1])
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    return MonodromyData(
        matrix=matrix,
        eigenvalues=eigenvalues,
        eigenvectors=eigenvectors,
        terminal_state=terminal_state,
        periodicity_error=float(np.linalg.norm(terminal_state - orbit.initial_state)),
    )


def hyperbolic_eigenvectors(data: MonodromyData) -> tuple[np.ndarray, np.ndarray, complex, complex]:
    """Return real unstable/stable eigenvectors and eigenvalues."""

    magnitudes = np.abs(data.eigenvalues)
    unstable_idx = int(np.argmax(magnitudes))
    stable_idx = int(np.argmin(magnitudes))
    unstable = np.real(data.eigenvectors[:, unstable_idx])
    stable = np.real(data.eigenvectors[:, stable_idx])
    return unstable, stable, data.eigenvalues[unstable_idx], data.eigenvalues[stable_idx]


def orbit_states_and_stms(
    orbit: PlanarLyapunovOrbit,
    samples: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample states and STMs along one period of an orbit."""

    times = np.linspace(0.0, orbit.period, samples, endpoint=False)
    sol = integrate_state_and_stm(orbit.initial_state, (0.0, orbit.period), orbit.mu, t_eval=times)
    if not sol.success:
        raise RuntimeError(sol.message)
    states = sol.y[:6, :].T
    stms = sol.y[6:, :].T.reshape(samples, 6, 6)
    return times, states, stms


def manifold_seeds(
    orbit: PlanarLyapunovOrbit,
    *,
    samples: int = 18,
    epsilon: float = 1e-5,
) -> tuple[list[ManifoldSeed], list[ManifoldSeed], MonodromyData]:
    """Generate stable and unstable seeds around a periodic orbit."""

    data = monodromy(orbit)
    unstable0, stable0, _, _ = hyperbolic_eigenvectors(data)
    times, states, stms = orbit_states_and_stms(orbit, samples)

    stable_seeds: list[ManifoldSeed] = []
    unstable_seeds: list[ManifoldSeed] = []
    for time_on_orbit, state, phi in zip(times, states, stms):
        unstable = np.real(phi @ unstable0)
        stable = np.real(phi @ stable0)
        for sign in (-1, 1):
            unstable_step = sign * epsilon * unstable / np.linalg.norm(unstable[:3])
            stable_step = sign * epsilon * stable / np.linalg.norm(stable[:3])
            unstable_seeds.append(
                ManifoldSeed(state, state + unstable_step, float(time_on_orbit), sign, "unstable")
            )
            stable_seeds.append(
                ManifoldSeed(state, state + stable_step, float(time_on_orbit), sign, "stable")
            )
    return stable_seeds, unstable_seeds, data


def propagate_seed(
    seed: ManifoldSeed,
    mu: float,
    *,
    duration: float,
    samples: int = 260,
) -> np.ndarray:
    """Propagate a stable seed backward or unstable seed forward."""

    if seed.kind == "stable":
        t_span = (0.0, -abs(duration))
        t_eval = np.linspace(t_span[0], t_span[1], samples)
    elif seed.kind == "unstable":
        t_span = (0.0, abs(duration))
        t_eval = np.linspace(t_span[0], t_span[1], samples)
    else:
        raise ValueError(f"Unknown manifold kind: {seed.kind}")

    sol = integrate_cr3bp(seed.perturbed_state, t_span, mu, t_eval=t_eval, max_step=0.025)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.T


def manifold_trajectories(
    orbit: PlanarLyapunovOrbit,
    *,
    samples_on_orbit: int = 18,
    epsilon: float = 1e-5,
    duration: float = 3.0,
    trajectory_samples: int = 260,
) -> tuple[list[np.ndarray], list[np.ndarray], MonodromyData]:
    """Return stable and unstable manifold trajectories."""

    stable_seeds, unstable_seeds, data = manifold_seeds(
        orbit,
        samples=samples_on_orbit,
        epsilon=epsilon,
    )
    stable = [
        propagate_seed(seed, orbit.mu, duration=duration, samples=trajectory_samples)
        for seed in stable_seeds
    ]
    unstable = [
        propagate_seed(seed, orbit.mu, duration=duration, samples=trajectory_samples)
        for seed in unstable_seeds
    ]
    return stable, unstable, data


def periodic_halo_manifold_sample(
    mu: float,
    *,
    point: str = "L1",
    z_amplitudes: list[float] | np.ndarray | None = None,
    seed_x_amplitude: float | None = None,
    samples_on_orbit: int = 8,
    epsilon: float = 2e-5,
    duration: float = 4.0,
    trajectory_samples: int = 180,
    include_stable: bool = True,
    include_unstable: bool = True,
) -> PeriodicManifoldSample:
    """Build a corrected 3D halo-like orbit and propagate local manifolds.

    This is the periodic-orbit counterpart used to replace Chapter 4's purely
    geometric periodic-halo manifold placeholder. The quasi-periodic torus
    manifold still requires a separate torus-map eigenvector implementation.
    """

    branch = point.upper()
    if z_amplitudes is None:
        z_amplitudes = [0.001, 0.004, 0.008, 0.014, 0.024, 0.040]
    if seed_x_amplitude is None:
        seed_x_amplitude = 0.002 if branch == "L1" else -0.002

    family = spatial_symmetric_family(
        mu,
        z_amplitudes,
        point=branch,
        seed_x_amplitude=seed_x_amplitude,
        family_label="halo",
    )
    orbit = family[-1]
    stable_seeds, unstable_seeds, data = manifold_seeds(
        orbit,
        samples=samples_on_orbit,
        epsilon=epsilon,
    )

    stable = (
        tuple(
            propagate_seed(seed, orbit.mu, duration=duration, samples=trajectory_samples)
            for seed in stable_seeds
        )
        if include_stable
        else tuple()
    )
    unstable = (
        tuple(
            propagate_seed(seed, orbit.mu, duration=duration, samples=trajectory_samples)
            for seed in unstable_seeds
        )
        if include_unstable
        else tuple()
    )
    orbit_curve = propagate_periodic_orbit(orbit, samples=240)
    return PeriodicManifoldSample(
        orbit=orbit,
        orbit_curve=orbit_curve,
        stable=stable,
        unstable=unstable,
        monodromy=data,
    )


def lyapunov_family_stability(
    mu: float,
    length_unit_km: float,
    x_amplitudes: list[float] | np.ndarray,
    *,
    point: str = "L2",
) -> list[dict[str, float]]:
    """Compute stability index data for a planar Lyapunov family."""

    moon_x = 1.0 - mu
    rows: list[dict[str, float]] = []
    for orbit in planar_lyapunov_family(mu, x_amplitudes, point=point, tolerance=1e-10, max_iterations=20):
        states = propagate_periodic_orbit(orbit, samples=260)
        r_moon = np.sqrt((states[:, 0] - moon_x) ** 2 + states[:, 1] ** 2 + states[:, 2] ** 2)
        data = monodromy(orbit)
        rows.append(
            {
                "x_amplitude_input": float(orbit.initial_guess.amplitude_x),
                "x0": float(orbit.initial_state[0]),
                "ydot0": float(orbit.initial_state[4]),
                "period": float(orbit.period),
                "jacobi": float(orbit.jacobi),
                "perilune_radius_km": float(np.min(r_moon) * length_unit_km),
                "stability_index": float(data.stability_index),
                "periodicity_error": float(data.periodicity_error),
                "final_residual_norm": float(orbit.iterations[-1].residual_norm),
            }
        )
    return rows


def spatial_symmetric_family_stability(
    mu: float,
    length_unit_km: float,
    z_amplitudes: list[float] | np.ndarray,
    *,
    point: str = "L2",
    seed_x_amplitude: float = -0.002,
    family_label: str = "halo",
) -> list[dict[str, float]]:
    """Compute stability data for a corrected 3D symmetric periodic family."""

    moon_x = 1.0 - mu
    rows: list[dict[str, float]] = []
    family = spatial_symmetric_family(
        mu,
        z_amplitudes,
        point=point,
        seed_x_amplitude=seed_x_amplitude,
        family_label=family_label,
    )
    for orbit in family:
        states = propagate_periodic_orbit(orbit, samples=360)
        r_moon = np.sqrt((states[:, 0] - moon_x) ** 2 + states[:, 1] ** 2 + states[:, 2] ** 2)
        data = monodromy(orbit)
        rows.append(
            {
                "z0": float(orbit.fixed_z0),
                "x0": float(orbit.initial_state[0]),
                "ydot0": float(orbit.initial_state[4]),
                "period": float(orbit.period),
                "jacobi": float(orbit.jacobi),
                "perilune_radius_km": float(np.min(r_moon) * length_unit_km),
                "z_amplitude_km": float(np.max(np.abs(states[:, 2])) * length_unit_km),
                "stability_index": float(data.stability_index),
                "periodicity_error": float(data.periodicity_error),
                "final_residual_norm": float(orbit.iterations[-1].residual_norm),
            }
        )
    return rows


def spatial_symmetric_folded_family_stability(
    mu: float,
    length_unit_km: float,
    *,
    point: str = "L2",
    seed_x_amplitude: float = -0.002,
    natural_z_values: np.ndarray | None = None,
    continuation_members: int = 230,
    continuation_step: float = 0.01,
    continuation_stride: int = 4,
    minimum_radius_km: float = 1_737.4,
    targeted_radii_km: tuple[float, ...] = (4_800.0, 12_610.0),
) -> list[dict[str, float | str]]:
    """Continue a folded spatial family and return sampled stability data.

    Natural ``z0`` continuation supplies the two seeds immediately before the
    fold. Pseudo-arclength continuation then follows the same halo/NRHO branch
    toward the secondary. Stability is evaluated on a sparse subset because
    continuation itself is much cheaper than a monodromy integration.
    """

    if length_unit_km <= 0.0:
        raise ValueError("length_unit_km must be positive")
    if continuation_members < 3:
        raise ValueError("continuation_members must be at least three")
    if continuation_step <= 0.0:
        raise ValueError("continuation_step must be positive")
    if continuation_stride < 1:
        raise ValueError("continuation_stride must be positive")
    if minimum_radius_km <= 0.0:
        raise ValueError("minimum_radius_km must be positive")

    if natural_z_values is None:
        natural_z_values = np.array(
            [0.001, 0.004, 0.008, 0.014, 0.024, 0.040, 0.060, 0.070, 0.075],
            dtype=float,
        )
    else:
        natural_z_values = np.asarray(natural_z_values, dtype=float)
    if natural_z_values.ndim != 1 or natural_z_values.size < 2:
        raise ValueError("natural_z_values must contain at least two values")

    natural = spatial_symmetric_family(
        mu,
        natural_z_values,
        point=point,
        seed_x_amplitude=seed_x_amplitude,
        family_label="halo",
        max_iterations=40,
    )
    folded = spatial_symmetric_pseudo_arclength_family(
        natural[-2:],
        members=continuation_members,
        step_size=continuation_step,
        max_iterations=60,
        max_delta_norm=0.10,
    )
    secondary = np.array([1.0 - mu, 0.0, 0.0], dtype=float)

    def crossing_radius_km(orbit: SpatialSymmetricOrbit) -> float:
        return float(
            np.linalg.norm(orbit.initial_state[:3] - secondary) * length_unit_km
        )

    retained_folded: list[SpatialSymmetricOrbit] = []
    for orbit in folded:
        if crossing_radius_km(orbit) < minimum_radius_km:
            break
        retained_folded.append(orbit)
    if len(retained_folded) < 2:
        raise RuntimeError("Folded continuation did not reach the requested radius interval")

    selected: list[tuple[SpatialSymmetricOrbit, str, int]] = [
        (orbit, "natural-z0", index)
        for index, orbit in enumerate(natural[:-1])
    ]
    selected.extend(
        (retained_folded[index], "pseudo-arclength", index)
        for index in range(0, len(retained_folded), continuation_stride)
    )
    last_index = len(retained_folded) - 1
    if last_index % continuation_stride:
        selected.append((retained_folded[-1], "pseudo-arclength", last_index))

    folded_radii = np.array([crossing_radius_km(orbit) for orbit in retained_folded])
    for target_radius_km in targeted_radii_km:
        if not minimum_radius_km <= target_radius_km <= folded_radii.max():
            raise ValueError("targeted_radii_km must lie on the retained folded branch")
        nearest_index = int(np.argmin(np.abs(folded_radii - target_radius_km)))
        targeted = correct_spatial_symmetric_orbit_fixed_secondary_radius(
            mu,
            target_radius=target_radius_km / length_unit_km,
            seed_orbit=retained_folded[nearest_index],
            max_iterations=30,
        )
        selected.append((targeted, "fixed-secondary-radius", nearest_index))

    rows: list[dict[str, float | str]] = []
    for orbit, method, continuation_index in selected:
        states = propagate_periodic_orbit(orbit, samples=240)
        radii = np.linalg.norm(states[:, :3] - secondary, axis=1)
        data = monodromy(orbit)
        rows.append(
            {
                "branch_method": method,
                "continuation_index": float(continuation_index),
                "z0": float(orbit.fixed_z0),
                "x0": float(orbit.initial_state[0]),
                "ydot0": float(orbit.initial_state[4]),
                "period": float(orbit.period),
                "jacobi": float(orbit.jacobi),
                "perilune_radius_km": float(np.min(radii) * length_unit_km),
                "z_amplitude_km": float(np.max(np.abs(states[:, 2])) * length_unit_km),
                "stability_index": float(data.stability_index),
                "periodicity_error": float(data.periodicity_error),
                "final_residual_norm": float(orbit.iterations[-1].residual_norm),
            }
        )
    rows.sort(key=lambda row: float(row["perilune_radius_km"]))
    return rows
