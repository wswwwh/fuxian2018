"""Tests for cross-resolution invariant-subspace comparison."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import cross_resolution_principal_angles_deg


def analytic_bundle(phases: np.ndarray) -> np.ndarray:
    values = np.zeros((phases.size, 3, 1))
    values[:, 0, 0] = np.cos(phases)
    values[:, 1, 0] = np.sin(phases)
    return values


class BundleResolutionConvergenceTests(unittest.TestCase):
    def test_fourier_resampling_recovers_same_bundle_across_odd_resolutions(self) -> None:
        coarse_phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        fine_phases = np.linspace(0.0, 2.0 * np.pi, 17, endpoint=False)

        angles = cross_resolution_principal_angles_deg(
            coarse_phases,
            analytic_bundle(coarse_phases),
            fine_phases,
            analytic_bundle(fine_phases),
        )

        self.assertLess(float(np.max(angles)), 2.0e-6)

    def test_cross_resolution_metric_detects_nonconverged_direction(self) -> None:
        coarse_phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        fine_phases = np.linspace(0.0, 2.0 * np.pi, 17, endpoint=False)
        fine = analytic_bundle(fine_phases)
        fine[:, 2, 0] = 0.2
        fine /= np.linalg.norm(fine, axis=1, keepdims=True)

        angles = cross_resolution_principal_angles_deg(
            coarse_phases,
            analytic_bundle(coarse_phases),
            fine_phases,
            fine,
        )

        self.assertGreater(float(np.mean(angles)), 10.0)


if __name__ == "__main__":
    unittest.main()
