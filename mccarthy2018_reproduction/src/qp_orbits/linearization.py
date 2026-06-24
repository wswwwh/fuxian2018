"""Linearized CR3BP utilities."""

from __future__ import annotations

import numpy as np


def second_derivatives(position: np.ndarray, mu: float) -> np.ndarray:
    """Return the 3x3 Hessian of the CR3BP pseudo-potential."""

    x, y, z = np.asarray(position, dtype=float)
    dx1 = x + mu
    dx2 = x - 1.0 + mu
    r1_sq = dx1**2 + y**2 + z**2
    r2_sq = dx2**2 + y**2 + z**2
    r1 = np.sqrt(r1_sq)
    r2 = np.sqrt(r2_sq)

    m1 = 1.0 - mu
    m2 = mu
    common = m1 / r1**3 + m2 / r2**3

    uxx = 1.0 - common + 3.0 * m1 * dx1**2 / r1**5 + 3.0 * m2 * dx2**2 / r2**5
    uyy = 1.0 - common + 3.0 * m1 * y**2 / r1**5 + 3.0 * m2 * y**2 / r2**5
    uzz = -common + 3.0 * m1 * z**2 / r1**5 + 3.0 * m2 * z**2 / r2**5
    uxy = 3.0 * m1 * dx1 * y / r1**5 + 3.0 * m2 * dx2 * y / r2**5
    uxz = 3.0 * m1 * dx1 * z / r1**5 + 3.0 * m2 * dx2 * z / r2**5
    uyz = 3.0 * m1 * y * z / r1**5 + 3.0 * m2 * y * z / r2**5

    return np.array(
        [
            [uxx, uxy, uxz],
            [uxy, uyy, uyz],
            [uxz, uyz, uzz],
        ],
        dtype=float,
    )


def state_jacobian(position: np.ndarray, mu: float) -> np.ndarray:
    """Return the 6x6 first-order CR3BP state matrix at a position."""

    hessian = second_derivatives(position, mu)
    matrix = np.zeros((6, 6), dtype=float)
    matrix[0, 3] = 1.0
    matrix[1, 4] = 1.0
    matrix[2, 5] = 1.0
    matrix[3:6, 0:3] = hessian
    matrix[3, 4] = 2.0
    matrix[4, 3] = -2.0
    return matrix


def eigensystem_at(position: np.ndarray, mu: float) -> tuple[np.ndarray, np.ndarray]:
    """Eigenvalues and eigenvectors of the CR3BP linearized state matrix."""

    matrix = state_jacobian(position, mu)
    return np.linalg.eig(matrix)
