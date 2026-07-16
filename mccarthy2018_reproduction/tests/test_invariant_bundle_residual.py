"""Tests for the cocycle invariant-bundle equation."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import bundle_invariance_metrics


def rotation(angle: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


class InvariantBundleResidualTests(unittest.TestCase):
    def test_exact_one_dimensional_bundle_has_machine_residual(self) -> None:
        sample_count = 9
        phases = np.linspace(0.0, 2.0 * np.pi, sample_count, endpoint=False)
        rho = 0.41

        def frame(theta: float) -> np.ndarray:
            matrix = np.eye(3)
            matrix[:2, :2] = rotation(theta)
            return matrix

        cocycle = np.asarray(
            [
                frame(theta + rho)
                @ np.diag([2.0, 0.5, 0.8])
                @ frame(theta).T
                for theta in phases
            ]
        )
        bundle = np.asarray([frame(theta)[:, [0]] for theta in phases])

        reduced, residuals = bundle_invariance_metrics(
            cocycle, phases, rho, bundle
        )

        self.assertEqual(reduced.shape, (sample_count, 1, 1))
        self.assertLess(float(np.max(residuals)), 1.0e-12)
        np.testing.assert_allclose(reduced[:, 0, 0], 2.0, atol=1.0e-12)

    def test_wrong_bundle_is_rejected_by_residual(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.31
        cocycle = np.repeat(np.diag([2.0, 0.5, 0.8])[None, :, :], 9, axis=0)
        wrong = np.zeros((9, 3, 1))
        wrong[:, 0, 0] = np.cos(phases)
        wrong[:, 1, 0] = np.sin(phases)

        _, residuals = bundle_invariance_metrics(cocycle, phases, rho, wrong)

        self.assertGreater(float(np.max(residuals)), 0.1)


if __name__ == "__main__":
    unittest.main()
