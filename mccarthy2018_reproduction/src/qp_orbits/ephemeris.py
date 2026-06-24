"""DE421 geometry used to orient corrected quasi-DRO trajectories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .constants import CR3BPSystem
from .corrected_dro_family import (
    CorrectedDROFamilyMember,
    CorrectedDROTrajectory,
    propagate_corrected_dro_phase,
)


MOON_RADIUS_KM = 1737.4
SUN_RADIUS_KM = 695700.0


@dataclass(frozen=True)
class DE421FrameSeries:
    """Time-varying Earth-Moon and Sun-Moon orthonormal frames from DE421."""

    epoch_utc: str
    times_days: np.ndarray
    earth_moon_frames: np.ndarray
    sun_moon_frames: np.ndarray
    earth_moon_vectors_km: np.ndarray
    earth_moon_distances_km: np.ndarray
    sun_moon_distances_km: np.ndarray
    orthogonality_error: float


@dataclass(frozen=True)
class DE421QuasiDROScene:
    """Corrected CR3BP quasi-DRO embedded in the DE421 Sun-Moon frame."""

    epoch_utc: str
    phase_deg: float
    times_days: np.ndarray
    points_km: np.ndarray
    marker_km: np.ndarray
    shadow_surface_km: np.ndarray
    eclipse_mask: np.ndarray
    earth_occultation_mask: np.ndarray
    earth_moon_distances_km: np.ndarray
    sun_moon_distances_km: np.ndarray
    cr3bp_jacobi_span: float
    frame_orthogonality_error: float
    eclipse_duration_hours: float
    earth_occultation_hours: float
    minimum_shadow_clearance_km: float


def _parse_epoch_utc(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        epoch = value
    else:
        epoch = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=timezone.utc)
    return epoch.astimezone(timezone.utc)


def _normalize_rows(vectors: np.ndarray, *, label: str) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1)
    if np.any(~np.isfinite(norms)) or np.any(norms <= 0.0):
        raise ValueError(f"cannot normalize {label}")
    return vectors / norms[:, None]


def _orbital_frames(position: np.ndarray, velocity: np.ndarray, *, label: str) -> np.ndarray:
    x_axis = _normalize_rows(position, label=f"{label} position")
    z_axis = _normalize_rows(np.cross(position, velocity), label=f"{label} angular momentum")
    y_axis = _normalize_rows(np.cross(z_axis, x_axis), label=f"{label} transverse axis")
    z_axis = _normalize_rows(np.cross(x_axis, y_axis), label=f"{label} corrected normal")
    return np.stack([x_axis, y_axis, z_axis], axis=2)


def de421_frame_series(
    kernel_path: str | Path,
    *,
    epoch_utc: str | datetime,
    times_days: np.ndarray,
) -> DE421FrameSeries:
    """Load DE421 states and construct instantaneous Earth-Moon/Sun-Moon frames."""

    try:
        from skyfield.api import load
    except ImportError as exc:
        raise RuntimeError("skyfield is required for DE421 frame generation") from exc

    kernel = Path(kernel_path)
    if not kernel.is_file():
        raise FileNotFoundError(f"DE421 kernel not found: {kernel}")
    sample_times = np.asarray(times_days, dtype=float)
    if sample_times.ndim != 1 or sample_times.size < 2 or np.any(np.diff(sample_times) <= 0.0):
        raise ValueError("times_days must be a strictly increasing one-dimensional array")

    epoch = _parse_epoch_utc(epoch_utc)
    timescale = load.timescale()
    skyfield_times = timescale.from_datetime(epoch) + sample_times
    ephemeris = load(str(kernel))
    try:
        earth_state = ephemeris["earth"].at(skyfield_times)
        moon_state = ephemeris["moon"].at(skyfield_times)
        sun_state = ephemeris["sun"].at(skyfield_times)
        earth_position = np.asarray(earth_state.position.km, dtype=float).T
        moon_position = np.asarray(moon_state.position.km, dtype=float).T
        sun_position = np.asarray(sun_state.position.km, dtype=float).T
        earth_velocity = np.asarray(earth_state.velocity.km_per_s, dtype=float).T
        moon_velocity = np.asarray(moon_state.velocity.km_per_s, dtype=float).T
        sun_velocity = np.asarray(sun_state.velocity.km_per_s, dtype=float).T
    finally:
        ephemeris.close()

    earth_moon_position = moon_position - earth_position
    earth_moon_velocity = moon_velocity - earth_velocity
    sun_moon_position = sun_position - moon_position
    sun_moon_velocity = sun_velocity - moon_velocity
    earth_moon_frames = _orbital_frames(
        earth_moon_position,
        earth_moon_velocity,
        label="Earth-Moon",
    )
    sun_moon_frames = _orbital_frames(
        sun_moon_position,
        sun_moon_velocity,
        label="Sun-Moon",
    )
    identity = np.eye(3)
    errors = np.concatenate(
        [
            (np.swapaxes(earth_moon_frames, 1, 2) @ earth_moon_frames - identity).reshape(-1, 9),
            (np.swapaxes(sun_moon_frames, 1, 2) @ sun_moon_frames - identity).reshape(-1, 9),
        ],
        axis=0,
    )
    return DE421FrameSeries(
        epoch_utc=epoch.isoformat().replace("+00:00", "Z"),
        times_days=sample_times,
        earth_moon_frames=earth_moon_frames,
        sun_moon_frames=sun_moon_frames,
        earth_moon_vectors_km=earth_moon_position,
        earth_moon_distances_km=np.linalg.norm(earth_moon_position, axis=1),
        sun_moon_distances_km=np.linalg.norm(sun_moon_position, axis=1),
        orthogonality_error=float(np.max(np.abs(errors))),
    )


def lunar_umbra_surface(
    sun_moon_distance_km: float,
    *,
    length_km: float = 1.0e5,
    axial_samples: int = 36,
    angular_samples: int = 28,
) -> np.ndarray:
    """Return a Moon-centered umbra cone whose positive x-axis points to the Sun."""

    axial_distance = np.linspace(0.0, length_km, axial_samples)
    radius = MOON_RADIUS_KM - axial_distance * (
        (SUN_RADIUS_KM - MOON_RADIUS_KM) / sun_moon_distance_km
    )
    radius = np.maximum(radius, 0.0)
    angle = np.linspace(0.0, 2.0 * np.pi, angular_samples)
    return np.stack(
        [
            np.broadcast_to(-axial_distance[:, None], (axial_samples, angular_samples)),
            radius[:, None] * np.cos(angle)[None, :],
            radius[:, None] * np.sin(angle)[None, :],
        ],
        axis=2,
    )


def embed_corrected_dro_in_de421(
    trajectory: CorrectedDROTrajectory,
    frames: DE421FrameSeries,
    system: CR3BPSystem,
) -> DE421QuasiDROScene:
    """Embed a corrected CR3BP propagation in the instantaneous DE421 Sun-Moon frame."""

    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("dimensional Earth-Moon units are required for DE421 embedding")
    times_days = trajectory.normalized_times * system.time_unit_days
    if trajectory.states.shape[0] != frames.times_days.size or not np.allclose(
        times_days,
        frames.times_days,
        rtol=0.0,
        atol=1.0e-9,
    ):
        raise ValueError("trajectory and DE421 frame times do not match")

    moon_x = 1.0 - system.mu
    moon_relative_nd = trajectory.states[:, :3] - np.array([moon_x, 0.0, 0.0])
    moon_relative_em_km = moon_relative_nd * frames.earth_moon_distances_km[:, None]
    moon_relative_inertial_km = np.einsum(
        "nij,nj->ni",
        frames.earth_moon_frames,
        moon_relative_em_km,
    )
    points_km = np.einsum(
        "nij,nj->ni",
        np.swapaxes(frames.sun_moon_frames, 1, 2),
        moon_relative_inertial_km,
    )

    behind_moon = points_km[:, 0] < 0.0
    axial_distance = np.maximum(-points_km[:, 0], 0.0)
    umbra_radius = MOON_RADIUS_KM - axial_distance * (
        (SUN_RADIUS_KM - MOON_RADIUS_KM) / frames.sun_moon_distances_km
    )
    shadow_radial_distance = np.linalg.norm(points_km[:, 1:3], axis=1)
    eclipse_mask = behind_moon & (umbra_radius > 0.0) & (shadow_radial_distance < umbra_radius)

    earth_to_moon = frames.earth_moon_vectors_km
    earth_to_spacecraft = earth_to_moon + moon_relative_inertial_km
    separation_angle = np.arctan2(
        np.linalg.norm(np.cross(earth_to_moon, earth_to_spacecraft), axis=1),
        np.einsum("ij,ij->i", earth_to_moon, earth_to_spacecraft),
    )
    moon_angular_radius = np.arctan2(MOON_RADIUS_KM, frames.earth_moon_distances_km)
    earth_occultation_mask = (
        (separation_angle < moon_angular_radius)
        & (np.linalg.norm(earth_to_spacecraft, axis=1) > frames.earth_moon_distances_km)
    )

    time_steps_hours = np.diff(times_days) * 24.0
    eclipse_hours = float(np.sum(time_steps_hours * eclipse_mask[:-1]))
    earth_occultation_hours = float(np.sum(time_steps_hours * earth_occultation_mask[:-1]))
    behind_clearance = shadow_radial_distance[behind_moon] - umbra_radius[behind_moon]
    minimum_shadow_clearance = float(np.min(behind_clearance)) if behind_clearance.size else float("inf")
    shadow_surface = lunar_umbra_surface(float(np.mean(frames.sun_moon_distances_km)))
    return DE421QuasiDROScene(
        epoch_utc=frames.epoch_utc,
        phase_deg=float(np.degrees(trajectory.phase_rad)),
        times_days=times_days,
        points_km=points_km,
        marker_km=points_km[0].copy(),
        shadow_surface_km=shadow_surface,
        eclipse_mask=eclipse_mask,
        earth_occultation_mask=earth_occultation_mask,
        earth_moon_distances_km=frames.earth_moon_distances_km.copy(),
        sun_moon_distances_km=frames.sun_moon_distances_km.copy(),
        cr3bp_jacobi_span=trajectory.jacobi_span,
        frame_orthogonality_error=frames.orthogonality_error,
        eclipse_duration_hours=eclipse_hours,
        earth_occultation_hours=earth_occultation_hours,
        minimum_shadow_clearance_km=minimum_shadow_clearance,
    )


def de421_quasi_dro_phase_scenes(
    member: CorrectedDROFamilyMember,
    system: CR3BPSystem,
    kernel_path: str | Path,
    *,
    epoch_utc: str | datetime,
    phases_deg: tuple[float, ...],
    returns: int = 10,
    samples: int = 1100,
) -> tuple[DE421QuasiDROScene, ...]:
    """Generate several insertion phases at one common DE421 epoch."""

    if not phases_deg:
        raise ValueError("phases_deg must not be empty")
    trajectories = tuple(
        propagate_corrected_dro_phase(
            member,
            system,
            phase_rad=np.radians(phase_deg),
            returns=returns,
            samples=samples,
        )
        for phase_deg in phases_deg
    )
    times_days = trajectories[0].normalized_times * (system.time_unit_days or 1.0)
    frames = de421_frame_series(kernel_path, epoch_utc=epoch_utc, times_days=times_days)
    return tuple(embed_corrected_dro_in_de421(trajectory, frames, system) for trajectory in trajectories)


def de421_quasi_dro_epoch_scenes(
    member: CorrectedDROFamilyMember,
    system: CR3BPSystem,
    kernel_path: str | Path,
    *,
    epochs_utc: tuple[str | datetime, ...],
    phase_deg: float = 0.0,
    returns: int = 10,
    samples: int = 1100,
) -> tuple[DE421QuasiDROScene, ...]:
    """Embed one corrected insertion phase at several DE421 epochs."""

    if not epochs_utc:
        raise ValueError("epochs_utc must not be empty")
    trajectory = propagate_corrected_dro_phase(
        member,
        system,
        phase_rad=np.radians(phase_deg),
        returns=returns,
        samples=samples,
    )
    times_days = trajectory.normalized_times * (system.time_unit_days or 1.0)
    return tuple(
        embed_corrected_dro_in_de421(
            trajectory,
            de421_frame_series(kernel_path, epoch_utc=epoch, times_days=times_days),
            system,
        )
        for epoch in epochs_utc
    )
