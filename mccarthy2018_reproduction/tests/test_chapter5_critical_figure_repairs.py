"""Regression gates for the corrected Chapter 5 figure data chains."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
FIGURES = PROJECT_ROOT / "figures"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class Chapter5CriticalFigureRepairTests(unittest.TestCase):
    def test_figure_51_uses_one_active_geometry_trajectory_at_exact_durations(self) -> None:
        bundle_path = DATA / "chapter5_sun_earth_l1_active_geometry_long_trajectory.npz"
        with np.load(bundle_path) as bundle:
            durations = tuple(float(value) for value in bundle["durations_days"])
            self.assertEqual(durations, (325.0, 1068.0, 2182.0))
            starts = []
            sample_counts = []
            for duration in durations:
                tag = f"{int(duration):04d}_days"
                elapsed = bundle[f"elapsed_{tag}"]
                states = bundle[f"trajectory_{tag}_states"]
                starts.append(states[0])
                sample_counts.append(len(states))
                self.assertAlmostEqual(float(elapsed[0]), 0.0, places=13)
                self.assertAlmostEqual(float(elapsed[-1]), duration, places=11)
                self.assertEqual(len(elapsed), len(states))
            np.testing.assert_allclose(starts, np.repeat(starts[:1], 3, axis=0), rtol=0.0, atol=1.0e-13)
            self.assertEqual(sample_counts, sorted(sample_counts))
            self.assertGreater(bundle["torus_surface_nd"].shape[0], 50)
            self.assertGreater(bundle["torus_surface_nd"].shape[1], 90)

        audit = _rows(DATA / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv")
        self.assertEqual(len(audit), 3)
        self.assertTrue(all(row["acceptance"] == "true" for row in audit))
        self.assertLessEqual(max(float(row["max_seam_residual_nd"]) for row in audit), 1.0e-7)
        self.assertLessEqual(max(float(row["jacobi_span"]) for row in audit), 5.0e-7)
        source = (FIGURES / "fig_5_01.py").read_text(encoding="utf-8")
        self.assertIn("chapter5_sun_earth_l1_active_geometry_long_trajectory.npz", source)
        self.assertNotIn("chapter5_sun_earth_l1_lissajous_torus_surface.csv", source)

    def test_figure_55_reads_the_audited_corrected_torus_not_the_proxy_scene(self) -> None:
        source = (FIGURES / "fig_5_05.py").read_text(encoding="utf-8")
        self.assertIn("chapter5_corrected_dro_quasi_dro_return.csv", source)
        self.assertNotIn("quasi_dro_return_scene", source)
        rows = _rows(DATA / "chapter5_corrected_dro_quasi_dro_return.csv")
        counts = {
            kind: sum(row["kind"] == kind for row in rows)
            for kind in ("periodic_dro", "quasi_dro_10_return", "corrected_local_torus")
        }
        self.assertEqual(counts, {"periodic_dro": 420, "quasi_dro_10_return": 1100, "corrected_local_torus": 540})

    def test_figure_513_uses_the_full_active_two_angle_scan(self) -> None:
        source = (FIGURES / "fig_5_13.py").read_text(encoding="utf-8")
        self.assertIn("chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv", source)
        self.assertNotIn("chapter5_sun_earth_l1_lissajous_stable_manifold_scan.csv", source)
        rows = _rows(DATA / "chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv")
        theta0 = sorted({float(row["theta0_deg"]) for row in rows})
        theta1 = sorted({float(row["theta1_deg"]) for row in rows})
        self.assertEqual((len(theta0), len(theta1), len(rows)), (70, 16, 1120))
        lookup = {
            (float(row["theta0_deg"]), float(row["theta1_deg"])): float(row["periapsis_radius_km"])
            for row in rows
        }
        grid = np.array([[lookup[(x, y)] for x in theta0] for y in theta1])
        self.assertGreater(float(np.median(np.ptp(grid, axis=0))), 1.0e3)
        self.assertGreater(float(np.median(np.ptp(grid, axis=1))), 1.0e3)
        tight = _rows(DATA / "chapter5_active_geometry_stable_manifold_tight_target_scan.csv")
        best = min(tight, key=lambda row: abs(float(row["periapsis_radius_km"]) - 7_033.0))
        self.assertLessEqual(abs(float(best["periapsis_radius_km"]) - 7_033.0), 5.0)

    def test_figure_514_uses_active_geometry_and_the_185_km_leo_target(self) -> None:
        source = (FIGURES / "fig_5_14.py").read_text(encoding="utf-8")
        self.assertIn("chapter5_sun_earth_l1_active_geometry_long_trajectory.npz", source)
        self.assertIn("chapter5_active_geometry_leo_transfer.csv", source)
        self.assertNotIn("chapter5_sun_earth_l1_lissajous_leo_transfer.csv", source)
        audit = _rows(DATA / "chapter5_active_geometry_leo_transfer_audit.csv")
        self.assertEqual(len(audit), 1)
        row = audit[0]
        self.assertEqual(row["acceptance"], "true")
        self.assertAlmostEqual(float(row["target_periapsis_radius_km"]), 6_563.0, places=10)
        self.assertLessEqual(abs(float(row["leo_altitude_km"]) - 185.0), 5.0)
        self.assertLessEqual(float(row["periapsis_target_error_km"]), 5.0)
        self.assertLessEqual(float(row["jacobi_span"]), 1.0e-8)
        self.assertLessEqual(float(row["lissajous_endpoint_distance_km"]), 100.0)


if __name__ == "__main__":
    unittest.main()
