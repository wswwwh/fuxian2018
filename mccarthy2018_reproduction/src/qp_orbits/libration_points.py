"""Libration point solvers for the normalized CR3BP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import root_scalar

from .cr3bp import jacobi_constant, potential_gradient


@dataclass(frozen=True)
class LibrationPoint:
    label: str
    x: float
    y: float
    z: float
    jacobi: float

    @property
    def state(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z, 0.0, 0.0, 0.0], dtype=float)


def _collinear_equation(x: float, mu: float) -> float:
    return float(potential_gradient([x, 0.0, 0.0], mu)[0])


def _solve_collinear(label: str, bracket: tuple[float, float], mu: float) -> LibrationPoint:
    result = root_scalar(
        lambda x: _collinear_equation(x, mu),
        bracket=bracket,
        xtol=1e-14,
        rtol=1e-14,
    )
    if not result.converged:
        raise RuntimeError(f"{label} root solve did not converge")
    state = np.array([result.root, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
    return LibrationPoint(label, result.root, 0.0, 0.0, float(jacobi_constant(state, mu)))


def compute_libration_points(mu: float) -> dict[str, LibrationPoint]:
    """Compute all five CR3BP libration points."""

    eps = 1e-10
    l1 = _solve_collinear("L1", (-mu + eps, 1.0 - mu - eps), mu)
    l2 = _solve_collinear("L2", (1.0 - mu + eps, 2.0), mu)
    l3 = _solve_collinear("L3", (-2.0, -mu - eps), mu)

    x_tri = 0.5 - mu
    y_tri = np.sqrt(3.0) / 2.0
    l4_state = np.array([x_tri, y_tri, 0.0, 0.0, 0.0, 0.0], dtype=float)
    l5_state = np.array([x_tri, -y_tri, 0.0, 0.0, 0.0, 0.0], dtype=float)
    l4 = LibrationPoint("L4", x_tri, y_tri, 0.0, float(jacobi_constant(l4_state, mu)))
    l5 = LibrationPoint("L5", x_tri, -y_tri, 0.0, float(jacobi_constant(l5_state, mu)))

    return {"L1": l1, "L2": l2, "L3": l3, "L4": l4, "L5": l5}
