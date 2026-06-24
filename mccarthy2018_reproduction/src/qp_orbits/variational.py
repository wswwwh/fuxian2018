"""State transition matrix propagation for CR3BP trajectories."""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .cr3bp import ArrayLike, cr3bp_rhs
from .linearization import state_jacobian


def augmented_state(initial_state: ArrayLike, phi0: np.ndarray | None = None) -> np.ndarray:
    """Pack a 6-state and 6x6 STM into a 42-element augmented state."""

    state = np.asarray(initial_state, dtype=float)
    if state.shape != (6,):
        raise ValueError("initial_state must be a 6-element vector")
    phi = np.eye(6) if phi0 is None else np.asarray(phi0, dtype=float)
    if phi.shape != (6, 6):
        raise ValueError("phi0 must be a 6x6 matrix")
    return np.concatenate([state, phi.ravel()])


def unpack_augmented(augmented: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    """Unpack a 42-element augmented state into state and STM."""

    values = np.asarray(augmented, dtype=float)
    if values.shape != (42,):
        raise ValueError("augmented state must have 42 elements")
    return values[:6], values[6:].reshape(6, 6)


def variational_rhs(_t: float, augmented: ArrayLike, mu: float) -> np.ndarray:
    """RHS for simultaneous CR3BP state and STM propagation."""

    state, phi = unpack_augmented(augmented)
    a_matrix = state_jacobian(state[:3], mu)
    phi_dot = a_matrix @ phi
    return np.concatenate([cr3bp_rhs(0.0, state, mu), phi_dot.ravel()])


def integrate_state_and_stm(
    initial_state: ArrayLike,
    t_span: tuple[float, float],
    mu: float,
    *,
    t_eval: np.ndarray | None = None,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
):
    """Integrate CR3BP state and STM using DOP853."""

    return solve_ivp(
        lambda t, y: variational_rhs(t, y, mu),
        t_span,
        augmented_state(initial_state),
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )


def _batched_variational_rhs(
    _t: float,
    augmented: np.ndarray,
    mu: float,
    sample_count: int,
) -> np.ndarray:
    """Vectorized CR3BP state and STM equations for several trajectories."""

    values = np.asarray(augmented, dtype=float).reshape(sample_count, 42)
    states = values[:, :6]
    phis = values[:, 6:].reshape(sample_count, 6, 6)
    x = states[:, 0]
    y = states[:, 1]
    z = states[:, 2]
    dx1 = x + mu
    dx2 = x - 1.0 + mu
    r1_sq = dx1**2 + y**2 + z**2
    r2_sq = dx2**2 + y**2 + z**2
    r1 = np.sqrt(r1_sq)
    r2 = np.sqrt(r2_sq)
    m1 = 1.0 - mu
    m2 = mu
    common = m1 / r1**3 + m2 / r2**3

    gradients = np.empty((sample_count, 3), dtype=float)
    gradients[:, 0] = x - m1 * dx1 / r1**3 - m2 * dx2 / r2**3
    gradients[:, 1] = y - m1 * y / r1**3 - m2 * y / r2**3
    gradients[:, 2] = -m1 * z / r1**3 - m2 * z / r2**3

    hessians = np.empty((sample_count, 3, 3), dtype=float)
    hessians[:, 0, 0] = (
        1.0 - common + 3.0 * m1 * dx1**2 / r1**5 + 3.0 * m2 * dx2**2 / r2**5
    )
    hessians[:, 1, 1] = (
        1.0 - common + 3.0 * m1 * y**2 / r1**5 + 3.0 * m2 * y**2 / r2**5
    )
    hessians[:, 2, 2] = -common + 3.0 * m1 * z**2 / r1**5 + 3.0 * m2 * z**2 / r2**5
    hessians[:, 0, 1] = hessians[:, 1, 0] = (
        3.0 * m1 * dx1 * y / r1**5 + 3.0 * m2 * dx2 * y / r2**5
    )
    hessians[:, 0, 2] = hessians[:, 2, 0] = (
        3.0 * m1 * dx1 * z / r1**5 + 3.0 * m2 * dx2 * z / r2**5
    )
    hessians[:, 1, 2] = hessians[:, 2, 1] = (
        3.0 * m1 * y * z / r1**5 + 3.0 * m2 * y * z / r2**5
    )

    matrices = np.zeros((sample_count, 6, 6), dtype=float)
    matrices[:, 0, 3] = 1.0
    matrices[:, 1, 4] = 1.0
    matrices[:, 2, 5] = 1.0
    matrices[:, 3:6, 0:3] = hessians
    matrices[:, 3, 4] = 2.0
    matrices[:, 4, 3] = -2.0

    state_derivatives = np.empty_like(states)
    state_derivatives[:, :3] = states[:, 3:6]
    state_derivatives[:, 3] = 2.0 * states[:, 4] + gradients[:, 0]
    state_derivatives[:, 4] = -2.0 * states[:, 3] + gradients[:, 1]
    state_derivatives[:, 5] = gradients[:, 2]
    phi_derivatives = np.einsum("nij,njk->nik", matrices, phis, optimize=True)
    derivatives = np.concatenate(
        [state_derivatives, phi_derivatives.reshape(sample_count, 36)],
        axis=1,
    )
    return derivatives.reshape(-1)


def integrate_states_and_stms(
    initial_states: np.ndarray,
    t_span: tuple[float, float],
    mu: float,
    *,
    t_eval: np.ndarray | None = None,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
):
    """Integrate several CR3BP states and STMs on one adaptive time grid."""

    states = np.asarray(initial_states, dtype=float)
    if states.ndim != 2 or states.shape[1] != 6:
        raise ValueError("initial_states must have shape (samples, 6)")
    sample_count = states.shape[0]
    initial = np.empty((sample_count, 42), dtype=float)
    initial[:, :6] = states
    initial[:, 6:] = np.eye(6).reshape(1, 36)
    return solve_ivp(
        lambda t, y: _batched_variational_rhs(t, y, mu, sample_count),
        t_span,
        initial.reshape(-1),
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
