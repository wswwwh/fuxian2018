"""Bicircular restricted four-body problem utilities.

The state ordering and Earth-Moon rotating frame match :mod:`qp_orbits.cr3bp`:
``[x, y, z, xdot, ydot, zdot]`` in normalized Earth-Moon units.  The Sun is a
prescribed circular perturber and enters as a differential acceleration, so the
solar term vanishes at the Earth-Moon barycenter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp

from .constants import CR3BPSystem
from .cr3bp import ArrayLike, cr3bp_rhs


SUN_GM_KM3_S2 = 1.32712440018e11
MEAN_SUN_DISTANCE_KM = 149597870.7
MEAN_SIDEREAL_YEAR_DAYS = 365.256363004
MEAN_LUNAR_SIDEREAL_PERIOD_DAYS = 27.321661


@dataclass(frozen=True)
class BCR4BPParameters:
    """Normalized planar bicircular Sun-Earth-Moon model parameters."""

    mu: float
    sun_mass_parameter: float
    sun_distance: float
    sun_angular_rate: float
    sun_phase: float = 0.0

    def without_sun(self) -> "BCR4BPParameters":
        """Return an equivalent CR3BP parameter set with the solar term removed."""

        return replace(self, sun_mass_parameter=0.0)


@dataclass(frozen=True)
class BCR4BPSegmentCorrection:
    """Velocity-corrected BCR4BP segment matching a target final position."""

    initial_state: np.ndarray
    corrected_initial_state: np.ndarray
    target_position: np.ndarray
    final_state: np.ndarray
    time_of_flight: float
    velocity_delta: np.ndarray
    residual: np.ndarray
    residual_norm: float
    optimizer_success: bool
    integration_success: bool
    nfev: int
    cost: float

    @property
    def accepted(self) -> bool:
        """Whether the optimizer and final propagation both succeeded."""

        return self.optimizer_success and self.integration_success and np.isfinite(self.residual_norm)


def earth_moon_bcr4bp_parameters(system: CR3BPSystem) -> BCR4BPParameters:
    """Return mean Sun-Earth-Moon BCR4BP parameters in this repo's units."""

    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("dimensional Earth-Moon units are required")
    time_unit_s = system.time_unit_days * 86400.0
    sun_mass_parameter = SUN_GM_KM3_S2 * time_unit_s**2 / system.length_unit_km**3
    sun_distance = MEAN_SUN_DISTANCE_KM / system.length_unit_km
    # CR3BP normalized time uses one Earth-Moon radian per time unit, so the
    # inertial solar rate must also be converted from cycles/year to
    # radians/normalized-time before subtracting the rotating-frame rate 1.
    sun_angular_rate = (
        2.0 * np.pi * system.time_unit_days / MEAN_SIDEREAL_YEAR_DAYS - 1.0
    )
    return BCR4BPParameters(
        mu=system.mu,
        sun_mass_parameter=float(sun_mass_parameter),
        sun_distance=float(sun_distance),
        sun_angular_rate=float(sun_angular_rate),
    )


def bicircular_sun_position(t: float, params: BCR4BPParameters) -> np.ndarray:
    """Position of the prescribed Sun in the Earth-Moon rotating frame."""

    angle = params.sun_phase + params.sun_angular_rate * float(t)
    return params.sun_distance * np.array([np.cos(angle), np.sin(angle), 0.0], dtype=float)


def bicircular_solar_acceleration(
    t: float,
    position: ArrayLike,
    params: BCR4BPParameters,
) -> np.ndarray:
    """Differential solar acceleration in normalized Earth-Moon units."""

    if params.sun_mass_parameter == 0.0:
        return np.zeros(3, dtype=float)
    pos = np.asarray(position, dtype=float)
    if pos.shape != (3,):
        raise ValueError("position must have shape (3,)")
    sun = bicircular_sun_position(t, params)
    spacecraft_from_sun = pos - sun
    sun_norm = np.linalg.norm(sun)
    rel_norm = np.linalg.norm(spacecraft_from_sun)
    if sun_norm <= 0.0 or rel_norm <= 0.0:
        raise ValueError("singular Sun-spacecraft geometry")
    return -params.sun_mass_parameter * (
        spacecraft_from_sun / rel_norm**3 + sun / sun_norm**3
    )


def bcr4bp_rhs(t: float, state: ArrayLike, params: BCR4BPParameters) -> np.ndarray:
    """Normalized rotating-frame BCR4BP equations of motion."""

    state_arr = np.asarray(state, dtype=float)
    if state_arr.shape != (6,):
        raise ValueError("state must have shape (6,)")
    derivative = cr3bp_rhs(t, state_arr, params.mu)
    derivative[3:6] += bicircular_solar_acceleration(t, state_arr[:3], params)
    return derivative


def integrate_bcr4bp(
    initial_state: ArrayLike,
    t_span: tuple[float, float],
    params: BCR4BPParameters,
    *,
    t_eval: np.ndarray | None = None,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
    dense_output: bool = False,
):
    """Integrate a BCR4BP trajectory with SciPy's DOP853 solver."""

    return solve_ivp(
        lambda t, y: bcr4bp_rhs(t, y, params),
        t_span,
        np.asarray(initial_state, dtype=float),
        method="DOP853",
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        dense_output=dense_output,
    )


def _solve_3x3_linear_system(matrix: np.ndarray, rhs: np.ndarray) -> np.ndarray | None:
    """Solve a 3x3 linear system with pivoted Gaussian elimination."""

    a = np.asarray(matrix, dtype=float).copy()
    b = np.asarray(rhs, dtype=float).copy()
    if a.shape != (3, 3) or b.shape != (3,):
        raise ValueError("expected a 3x3 matrix and 3-vector")
    for col in range(3):
        pivot = col + int(np.argmax(np.abs(a[col:, col])))
        if abs(a[pivot, col]) < 1.0e-14:
            return None
        if pivot != col:
            a[[col, pivot]] = a[[pivot, col]]
            b[[col, pivot]] = b[[pivot, col]]
        for row in range(col + 1, 3):
            factor = a[row, col] / a[col, col]
            a[row, col:] -= factor * a[col, col:]
            b[row] -= factor * b[col]
    x = np.empty(3, dtype=float)
    for row in range(2, -1, -1):
        diagonal = a[row, row]
        if abs(diagonal) < 1.0e-14:
            return None
        x[row] = (b[row] - float(np.dot(a[row, row + 1 :], x[row + 1 :]))) / diagonal
    return x


def correct_bcr4bp_velocity_to_position_target(
    initial_state: ArrayLike,
    target_position: ArrayLike,
    time_of_flight: float,
    params: BCR4BPParameters,
    *,
    initial_velocity_delta: ArrayLike | None = None,
    residual_scale: float = 1.0,
    rtol: float = 1e-11,
    atol: float = 1e-13,
    max_step: float = np.inf,
    max_nfev: int = 30,
) -> BCR4BPSegmentCorrection:
    """Correct initial velocity so a BCR4BP segment reaches a target position.

    This is a single-segment defect correction.  It is intentionally small, but
    it provides the same core contract later needed by a multi-shooting layer:
    free variables, a propagated defect, and an accepted residual.
    """

    state0 = np.asarray(initial_state, dtype=float)
    target = np.asarray(target_position, dtype=float)
    if state0.shape != (6,):
        raise ValueError("initial_state must have shape (6,)")
    if target.shape != (3,):
        raise ValueError("target_position must have shape (3,)")
    if time_of_flight <= 0.0:
        raise ValueError("time_of_flight must be positive")
    if residual_scale <= 0.0:
        raise ValueError("residual_scale must be positive")

    guess = (
        np.zeros(3, dtype=float)
        if initial_velocity_delta is None
        else np.asarray(initial_velocity_delta, dtype=float)
    )
    if guess.shape != (3,):
        raise ValueError("initial_velocity_delta must have shape (3,)")

    def residual_for_delta(delta: np.ndarray) -> np.ndarray:
        candidate = state0.copy()
        candidate[3:6] += delta
        solution = integrate_bcr4bp(
            candidate,
            (0.0, float(time_of_flight)),
            params,
            t_eval=np.array([float(time_of_flight)]),
            rtol=rtol,
            atol=atol,
            max_step=max_step,
        )
        if not solution.success or solution.y.shape[1] != 1 or not np.all(np.isfinite(solution.y)):
            return np.full(3, 1.0e6, dtype=float)
        return (solution.y[:3, -1] - target) / residual_scale

    delta = guess.copy()
    best_delta = delta.copy()
    best_residual = residual_for_delta(delta)
    best_norm = float(np.linalg.norm(best_residual))
    nfev = 1
    optimizer_success = best_norm * residual_scale <= 1.0e-10
    for _iteration in range(max_nfev):
        if optimizer_success:
            break
        base_residual = residual_for_delta(delta)
        nfev += 1
        base_norm = float(np.linalg.norm(base_residual))
        if base_norm < best_norm:
            best_norm = base_norm
            best_delta = delta.copy()
        jacobian = np.empty((3, 3), dtype=float)
        for column in range(3):
            step = 1.0e-6 * max(1.0, abs(delta[column]))
            trial = delta.copy()
            trial[column] += step
            jacobian[:, column] = (residual_for_delta(trial) - base_residual) / step
            nfev += 1
        newton_step = _solve_3x3_linear_system(jacobian, -base_residual)
        if newton_step is None or not np.all(np.isfinite(newton_step)):
            break
        improved = False
        for scale in (1.0, 0.5, 0.25, 0.125, 0.0625):
            candidate = delta + scale * newton_step
            candidate_residual = residual_for_delta(candidate)
            nfev += 1
            candidate_norm = float(np.linalg.norm(candidate_residual))
            if candidate_norm < best_norm:
                delta = candidate
                best_delta = candidate.copy()
                best_norm = candidate_norm
                best_residual = candidate_residual
                improved = True
                break
        optimizer_success = best_norm * residual_scale <= 1.0e-10
        if not improved:
            break
    corrected_initial = state0.copy()
    corrected_initial[3:6] += best_delta
    final_solution = integrate_bcr4bp(
        corrected_initial,
        (0.0, float(time_of_flight)),
        params,
        t_eval=np.array([float(time_of_flight)]),
        rtol=rtol,
        atol=atol,
        max_step=max_step,
    )
    if final_solution.success and final_solution.y.shape[1] == 1:
        final_state = final_solution.y[:, -1]
        residual = final_state[:3] - target
    else:
        final_state = np.full(6, np.nan, dtype=float)
        residual = np.full(3, np.nan, dtype=float)
    residual_norm = float(np.linalg.norm(residual))
    return BCR4BPSegmentCorrection(
        initial_state=state0,
        corrected_initial_state=corrected_initial,
        target_position=target,
        final_state=final_state,
        time_of_flight=float(time_of_flight),
        velocity_delta=np.asarray(best_delta, dtype=float),
        residual=residual,
        residual_norm=residual_norm,
        optimizer_success=bool(optimizer_success),
        integration_success=bool(final_solution.success and final_solution.y.shape[1] == 1),
        nfev=int(nfev),
        cost=float(0.5 * best_norm**2),
    )
