"""Behavior tests for ordered real-Schur bundle selection."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import real_schur_bundle_tracking


def rotation(angle: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


class RealSchurSelectionTests(unittest.TestCase):
    def test_selects_real_one_dimensional_block(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.41

        def frame(theta: float) -> np.ndarray:
            value = np.eye(3)
            value[:2, :2] = rotation(theta)
            return value

        cocycle = np.asarray(
            [
                frame(theta + rho)
                @ np.diag([2.0, 0.5, 0.8])
                @ frame(theta).T
                for theta in phases
            ]
        )

        result = real_schur_bundle_tracking(cocycle, phases, rho)

        self.assertEqual(result.bundle_dimension, 1)
        self.assertEqual(result.classification, "real_1d_hyperbolic_bundle")
        self.assertLess(result.selection_residual, 1.0e-12)
        self.assertLess(result.max_invariance_residual, 1.0e-12)

    def test_preserves_complex_pair_as_real_two_dimensional_subspace(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.37
        internal_rotation = 0.23

        def frame(theta: float) -> np.ndarray:
            value = np.eye(4)
            cosine = np.cos(theta)
            sine = np.sin(theta)
            value[0, 0] = value[2, 2] = cosine
            value[0, 2] = -sine
            value[2, 0] = sine
            value[1, 1] = value[3, 3] = cosine
            value[1, 3] = -sine
            value[3, 1] = sine
            return value

        normal = np.zeros((4, 4))
        normal[:2, :2] = 1.7 * rotation(internal_rotation)
        normal[2:, 2:] = 0.55 * rotation(0.11)
        cocycle = np.asarray(
            [frame(theta + rho) @ normal @ frame(theta).T for theta in phases]
        )

        result = real_schur_bundle_tracking(cocycle, phases, rho)

        self.assertEqual(result.bundle_dimension, 2)
        self.assertEqual(
            result.classification,
            "real_2d_complex_pair_invariant_subspace",
        )
        self.assertGreater(result.relative_imaginary, 1.0e-3)
        self.assertLess(result.selection_residual, 1.0e-12)
        self.assertLess(result.max_invariance_residual, 1.0e-12)


if __name__ == "__main__":
    unittest.main()
