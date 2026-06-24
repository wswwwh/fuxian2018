"""Linearized center-mode trajectories near collinear libration points."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .libration_points import compute_libration_points
from .linearization import eigensystem_at


@dataclass(frozen=True)
class CenterModes:
    """Planar and vertical center modes at a collinear libration point."""

    point: str
    equilibrium_state: np.ndarray
    planar_eigenvalue: complex
    planar_eigenvector: np.ndarray
    vertical_eigenvalue: complex
    vertical_eigenvector: np.ndarray

    @property
    def planar_frequency(self) -> float:
        return abs(float(self.planar_eigenvalue.imag))

    @property
    def vertical_frequency(self) -> float:
        return abs(float(self.vertical_eigenvalue.imag))


def center_modes(mu: float, point: str = "L1") -> CenterModes:
    """Return planar and vertical center modes for a collinear point."""

    libration = compute_libration_points(mu)[point]
    equilibrium = np.array([libration.x, libration.y, libration.z, 0.0, 0.0, 0.0], dtype=float)
    eigenvalues, eigenvectors = eigensystem_at(equilibrium[:3], mu)

    center_indices = [
        idx
        for idx, value in enumerate(eigenvalues)
        if value.imag > 1e-8 and abs(value.real) < 1e-7
    ]
    if len(center_indices) < 2:
        raise RuntimeError(f"Expected two center modes at {point}")

    planar_idx = min(
        center_indices,
        key=lambda idx: abs(eigenvectors[2, idx]) + abs(eigenvectors[5, idx]),
    )
    vertical_idx = min(
        center_indices,
        key=lambda idx: (
            abs(eigenvectors[0, idx])
            + abs(eigenvectors[1, idx])
            + abs(eigenvectors[3, idx])
            + abs(eigenvectors[4, idx])
        ),
    )
    return CenterModes(
        point=point,
        equilibrium_state=equilibrium,
        planar_eigenvalue=eigenvalues[planar_idx],
        planar_eigenvector=eigenvectors[:, planar_idx],
        vertical_eigenvalue=eigenvalues[vertical_idx],
        vertical_eigenvector=eigenvectors[:, vertical_idx],
    )


def mode_solution(eigenvalue: complex, eigenvector: np.ndarray, times: np.ndarray, phase: float = 0.0) -> np.ndarray:
    """Real-valued modal solution ``Re(v exp(i omega t + i phase))``."""

    omega = abs(float(eigenvalue.imag))
    angle = omega * times + phase
    return np.real(np.exp(1j * angle[:, None]) * eigenvector[None, :])


def scaled_planar_mode(
    modes: CenterModes,
    y_amplitude: float,
    times: np.ndarray,
) -> np.ndarray:
    """Planar center-mode displacement scaled to a requested y amplitude."""

    unit = mode_solution(modes.planar_eigenvalue, modes.planar_eigenvector, times)
    amplitude = float(np.max(np.abs(unit[:, 1])))
    if amplitude <= 0.0:
        raise RuntimeError("Planar mode has zero y-amplitude")
    return unit * (y_amplitude / amplitude)


def scaled_vertical_mode(
    modes: CenterModes,
    z_amplitude: float,
    times: np.ndarray,
) -> np.ndarray:
    """Vertical center-mode displacement scaled to a requested z amplitude."""

    unit = mode_solution(modes.vertical_eigenvalue, modes.vertical_eigenvector, times, phase=np.pi / 2.0)
    amplitude = float(np.max(np.abs(unit[:, 2])))
    if amplitude <= 0.0:
        raise RuntimeError("Vertical mode has zero z-amplitude")
    return unit * (z_amplitude / amplitude)


def linear_lissajous(
    modes: CenterModes,
    y_amplitude: float,
    z_amplitude: float,
    times: np.ndarray,
    *,
    vertical_phase: float = np.pi / 2.0,
) -> np.ndarray:
    """Combine planar and vertical center modes into a linear Lissajous path."""

    planar_unit = mode_solution(modes.planar_eigenvalue, modes.planar_eigenvector, times)
    planar_scale = y_amplitude / float(np.max(np.abs(planar_unit[:, 1])))
    vertical_unit = mode_solution(modes.vertical_eigenvalue, modes.vertical_eigenvector, times, phase=vertical_phase)
    vertical_scale = z_amplitude / float(np.max(np.abs(vertical_unit[:, 2])))
    return planar_scale * planar_unit + vertical_scale * vertical_unit
