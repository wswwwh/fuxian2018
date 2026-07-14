"""Unit and normalization checks for the Earth-Moon BCR4BP model."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.bcr4bp import (
    MEAN_SIDEREAL_YEAR_DAYS,
    bcr4bp_rhs,
    earth_moon_bcr4bp_parameters,
    integrate_bcr4bp,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import cr3bp_rhs


class EarthMoonBCR4BPParameterTests(unittest.TestCase):
    def test_solar_angular_rate_uses_radians_per_normalized_time(self) -> None:
        system = SYSTEMS["earth_moon"]
        params = earth_moon_bcr4bp_parameters(system)
        expected = (
            2.0 * np.pi * float(system.time_unit_days) / MEAN_SIDEREAL_YEAR_DAYS
            - 1.0
        )

        self.assertAlmostEqual(params.sun_angular_rate, expected, places=15)
        self.assertGreater(params.sun_angular_rate, -1.0)
        self.assertLess(params.sun_angular_rate, -0.9)

    def test_without_sun_reduces_exactly_to_cr3bp_rhs(self) -> None:
        system = SYSTEMS["earth_moon"]
        params = earth_moon_bcr4bp_parameters(system).without_sun()
        state = np.array([0.81, -0.04, 0.03, 0.01, 0.12, -0.02])

        np.testing.assert_allclose(
            bcr4bp_rhs(0.37, state, params),
            cr3bp_rhs(0.37, state, system.mu),
            rtol=0.0,
            atol=0.0,
        )

    def test_dense_output_is_available_for_continuous_clearance_checks(self) -> None:
        system = SYSTEMS["earth_moon"]
        params = earth_moon_bcr4bp_parameters(system)
        state = np.array([0.99, 0.02, 0.03, 0.01, 0.08, -0.02])

        solution = integrate_bcr4bp(
            state,
            (0.0, 0.02),
            params,
            rtol=1.0e-11,
            atol=1.0e-13,
            max_step=0.002,
            dense_output=True,
        )

        self.assertTrue(solution.success)
        self.assertIsNotNone(solution.sol)
        self.assertTrue(np.all(np.isfinite(solution.sol(0.01))))


if __name__ == "__main__":
    unittest.main()
