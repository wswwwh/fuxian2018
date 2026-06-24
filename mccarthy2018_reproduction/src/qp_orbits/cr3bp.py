"""Circular restricted three-body problem utilities.

State ordering is ``[x, y, z, xdot, ydot, zdot]`` in the normalized rotating
frame. The primaries are fixed at ``(-mu, 0, 0)`` and ``(1 - mu, 0, 0)``.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


ArrayLike = np.ndarray | list[float] | tuple[float, ...]


def distances(state: ArrayLike, mu: float) -> tuple[np.ndarray, np.ndarray]:
    """Return distances to the larger and smaller primaries."""

    state_arr = np.asarray(state, dtype=float)
    x = state_arr[..., 0]
    y = state_arr[..., 1]
    z = state_arr[..., 2]
    r1 = np.sqrt((x + mu) ** 2 + y**2 + z**2)
    r2 = np.sqrt((x - 1.0 + mu) ** 2 + y**2 + z**2)
    return r1, r2


def pseudo_potential(x: ArrayLike, y: ArrayLike, z: ArrayLike, mu: float) -> np.ndarray:
    """Return the CR3BP pseudo-potential U*."""

    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    z_arr = np.asarray(z, dtype=float)
    r1 = np.sqrt((x_arr + mu) ** 2 + y_arr**2 + z_arr**2)
    r2 = np.sqrt((x_arr - 1.0 + mu) ** 2 + y_arr**2 + z_arr**2)
    return 0.5 * (x_arr**2 + y_arr**2) + (1.0 - mu) / r1 + mu / r2


def potential_gradient(position: ArrayLike, mu: float) -> np.ndarray:
    """Gradient of the pseudo-potential."""

    x, y, z = np.asarray(position, dtype=float)
    r1, r2 = distances([x, y, z, 0.0, 0.0, 0.0], mu)
    ux = x - (1.0 - mu) * (x + mu) / r1**3 - mu * (x - 1.0 + mu) / r2**3
    uy = y - (1.0 - mu) * y / r1**3 - mu * y / r2**3
    uz = -(1.0 - mu) * z / r1**3 - mu * z / r2**3
    return np.array([ux, uy, uz], dtype=float)


def cr3bp_rhs(_t: float, state: ArrayLike, mu: float) -> np.ndarray:
    """Normalized rotating-frame CR3BP equations of motion."""

    x, y, z, xdot, ydot, zdot = np.asarray(state, dtype=float)
    ux, uy, uz = potential_gradient([x, y, z], mu)
    return np.array(
        [
            xdot,
            ydot,
            zdot,
            2.0 * ydot + ux,
            -2.0 * xdot + uy,
            uz,
        ],
        dtype=float,
    )


def jacobi_constant(state: ArrayLike, mu: float) -> np.ndarray:
    """Evaluate the Jacobi constant for one state or an array of states."""

    state_arr = np.asarray(state, dtype=float)
    x = state_arr[..., 0]
    y = state_arr[..., 1]
    z = state_arr[..., 2]
    velocities = state_arr[..., 3:6]
    speed_sq = np.sum(velocities**2, axis=-1)
    return 2.0 * pseudo_potential(x, y, z, mu) - speed_sq


def zero_velocity_grid(
    mu: float,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    n: int = 500,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``X, Y, C`` where ``C = 2 U*(x, y, 0)``."""

    x = np.linspace(xlim[0], xlim[1], n)
    y = np.linspace(ylim[0], ylim[1], n)
    x_grid, y_grid = np.meshgrid(x, y)
    c_grid = 2.0 * pseudo_potential(x_grid, y_grid, 0.0, mu)
    return x_grid, y_grid, c_grid


def integrate_cr3bp(
    initial_state: ArrayLike,
    t_span: tuple[float, float],
    mu: float,
    *,
    t_eval: np.ndarray | None = None,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
):
    """Integrate a CR3BP trajectory with SciPy's high-order DOP853 solver."""

    return solve_ivp(
        lambda t, y: cr3bp_rhs(t, y, mu),
        t_span,
        np.asarray(initial_state, dtype=float),
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )


def _batched_cr3bp_rhs(_t: float, flattened_states: np.ndarray, mu: float) -> np.ndarray:
    states = np.asarray(flattened_states, dtype=float).reshape(-1, 6)
    x = states[:, 0]
    y = states[:, 1]
    z = states[:, 2]
    dx1 = x + mu
    dx2 = x - 1.0 + mu
    r1 = np.sqrt(dx1**2 + y**2 + z**2)
    r2 = np.sqrt(dx2**2 + y**2 + z**2)
    gradients = np.empty((states.shape[0], 3), dtype=float)
    gradients[:, 0] = x - (1.0 - mu) * dx1 / r1**3 - mu * dx2 / r2**3
    gradients[:, 1] = y - (1.0 - mu) * y / r1**3 - mu * y / r2**3
    gradients[:, 2] = -(1.0 - mu) * z / r1**3 - mu * z / r2**3
    derivatives = np.empty_like(states)
    derivatives[:, :3] = states[:, 3:6]
    derivatives[:, 3] = 2.0 * states[:, 4] + gradients[:, 0]
    derivatives[:, 4] = -2.0 * states[:, 3] + gradients[:, 1]
    derivatives[:, 5] = gradients[:, 2]
    return derivatives.reshape(-1)


def integrate_states_cr3bp(
    initial_states: np.ndarray,
    t_span: tuple[float, float],
    mu: float,
    *,
    t_eval: np.ndarray | None = None,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
):
    """Integrate several CR3BP states on one adaptive time grid."""

    states = np.asarray(initial_states, dtype=float)
    if states.ndim != 2 or states.shape[1] != 6:
        raise ValueError("initial_states must have shape (samples, 6)")
    return solve_ivp(
        lambda t, y: _batched_cr3bp_rhs(t, y, mu),
        t_span,
        states.reshape(-1),
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
