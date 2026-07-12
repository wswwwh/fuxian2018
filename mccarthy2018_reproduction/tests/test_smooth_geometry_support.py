"""Tests for the differentiable geometry-support constraint."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.quasi_torus import (
    _regularized_least_squares_step,
    _smooth_absolute_support,
    _smooth_dual_geometry_constraints,
)


class SmoothAbsoluteSupportTests(unittest.TestCase):
    def test_zero_input_has_zero_support_and_gradient(self) -> None:
        support, gradient = _smooth_absolute_support(np.zeros((3, 4)))

        self.assertEqual(support, 0.0)
        np.testing.assert_array_equal(gradient, np.zeros((3, 4)))

    def test_support_is_sign_and_permutation_invariant(self) -> None:
        values = np.array([-0.3, 0.2, 0.8, -0.1])
        support, _ = _smooth_absolute_support(values, sharpness=25.0)
        reflected, _ = _smooth_absolute_support(-values, sharpness=25.0)
        permuted, _ = _smooth_absolute_support(values[[2, 0, 3, 1]], sharpness=25.0)

        self.assertAlmostEqual(support, reflected, places=14)
        self.assertAlmostEqual(support, permuted, places=14)
        self.assertLessEqual(support, np.max(np.abs(values)))
        self.assertGreaterEqual(
            support,
            np.max(np.abs(values)) - np.log(2.0 * values.size) / 25.0,
        )

    def test_analytic_gradient_matches_centered_difference(self) -> None:
        values = np.array([[-0.35, 0.12], [0.51, -0.27]], dtype=float)
        _, gradient = _smooth_absolute_support(values, sharpness=18.0)
        numerical = np.zeros_like(values)
        step = 1.0e-7
        for index in np.ndindex(values.shape):
            upper = values.copy()
            lower = values.copy()
            upper[index] += step
            lower[index] -= step
            upper_value, _ = _smooth_absolute_support(upper, sharpness=18.0)
            lower_value, _ = _smooth_absolute_support(lower, sharpness=18.0)
            numerical[index] = (upper_value - lower_value) / (2.0 * step)

        np.testing.assert_allclose(gradient, numerical, rtol=2.0e-7, atol=2.0e-9)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _smooth_absolute_support(np.array([]))
        with self.assertRaises(ValueError):
            _smooth_absolute_support(np.array([np.nan]))
        with self.assertRaises(ValueError):
            _smooth_absolute_support(np.array([1.0]), sharpness=0.0)

    def test_dual_geometry_jacobian_uses_only_y_and_z_columns(self) -> None:
        states = np.zeros((3, 6), dtype=float)
        states[:, 1] = (-0.2, 0.4, 0.1)
        states[:, 2] = (0.5, -0.1, 0.25)
        residuals, jacobian = _smooth_dual_geometry_constraints(
            states,
            target_y_support=0.3,
            target_z_support=0.45,
            sharpness=20.0,
        )

        self.assertEqual(residuals.shape, (2,))
        self.assertEqual(jacobian.shape, (2, states.size))
        active_columns = set(np.flatnonzero(np.any(jacobian != 0.0, axis=0)))
        self.assertTrue(active_columns.issubset(set(range(1, states.size, 6)) | set(range(2, states.size, 6))))
        np.testing.assert_array_equal(jacobian[0, 2::6], 0.0)
        np.testing.assert_array_equal(jacobian[1, 1::6], 0.0)

    def test_regularization_stabilizes_a_near_null_direction(self) -> None:
        jacobian = np.diag([1.0, 1.0e-9])
        rhs = np.array([1.0, 1.0])
        unregularized = _regularized_least_squares_step(
            jacobian,
            rhs,
            regularization=0.0,
        )
        regularized = _regularized_least_squares_step(
            jacobian,
            rhs,
            regularization=1.0e-6,
        )

        self.assertGreater(abs(unregularized[1]), 1.0e8)
        self.assertLess(abs(regularized[1]), 1.0e-2)
        self.assertAlmostEqual(regularized[0], 1.0 / 1.000001, places=12)


if __name__ == "__main__":
    unittest.main()
