"""Checks for DE421 initialization of the planar BCR4BP model."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.ephemeris import de421_bcr4bp_initial_geometry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KERNEL = PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp"


class DE421BCR4BPGeometryTests(unittest.TestCase):
    @unittest.skipUnless(KERNEL.is_file(), "DE421 kernel is not available")
    def test_epoch_geometry_is_finite_and_self_consistent(self) -> None:
        system = SYSTEMS["earth_moon"]
        geometry = de421_bcr4bp_initial_geometry(
            KERNEL,
            epoch_utc="2020-06-15T00:00:00Z",
            system=system,
        )

        self.assertEqual(geometry.epoch_utc, "2020-06-15T00:00:00Z")
        self.assertTrue(np.isfinite(geometry.sun_rotating_vector_km).all())
        self.assertLess(geometry.frame_orthogonality_error, 1.0e-12)
        self.assertGreater(geometry.frame_determinant, 0.0)
        self.assertLess(geometry.earth_moon_barycenter_spk_error_km, 1.0e-3)
        self.assertGreater(geometry.earth_moon_distance_km, 3.4e5)
        self.assertLess(geometry.earth_moon_distance_km, 4.2e5)
        self.assertGreater(geometry.sun_distance_km, 1.4e8)
        self.assertLess(geometry.sun_distance_km, 1.6e8)
        self.assertLess(geometry.sun_planar_distance_km, geometry.sun_distance_km)
        self.assertAlmostEqual(
            np.linalg.norm(geometry.sun_rotating_vector_km),
            geometry.sun_distance_km,
            places=6,
        )
        self.assertAlmostEqual(
            np.arctan2(
                geometry.sun_rotating_vector_km[1],
                geometry.sun_rotating_vector_km[0],
            ),
            geometry.sun_phase_rad,
            places=14,
        )
        self.assertLess(abs(geometry.sun_elevation_rad), np.deg2rad(10.0))


if __name__ == "__main__":
    unittest.main()
