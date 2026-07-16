"""Regression test that complex pairs are kept as real 2-D subspaces."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import (
    real_schur_bundle_tracking,
    traditional_pointwise_eigen_bundle,
)


def rotation(angle: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


class ComplexPairSubspaceHandlingTests(unittest.TestCase):
    def test_pointwise_real_projection_fails_but_real_subspace_succeeds(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.37

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
        normal[:2, :2] = 1.7 * rotation(0.23)
        normal[2:, 2:] = 0.55 * rotation(0.11)
        cocycle = np.asarray(
            [frame(theta + rho) @ normal @ frame(theta).T for theta in phases]
        )

        baseline = traditional_pointwise_eigen_bundle(cocycle, phases, rho)
        improved = real_schur_bundle_tracking(cocycle, phases, rho)

        self.assertEqual(
            baseline.classification,
            "complex_vector_projected_to_real_1d_failure",
        )
        self.assertEqual(baseline.bundle_dimension, 1)
        self.assertGreater(baseline.relative_imaginary, 1.0e-3)
        self.assertEqual(improved.bundle_dimension, 2)
        self.assertEqual(
            improved.classification,
            "real_2d_complex_pair_invariant_subspace",
        )
        self.assertLess(improved.max_invariance_residual, 1.0e-12)
        self.assertLess(
            improved.max_invariance_residual,
            baseline.max_invariance_residual,
        )


if __name__ == "__main__":
    unittest.main()
