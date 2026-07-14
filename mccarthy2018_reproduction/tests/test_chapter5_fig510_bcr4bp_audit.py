"""Regression tests for the dedicated Fig. 5.10 BCR4BP extension audit."""

from __future__ import annotations

import csv
import sys
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter5_fig510_bcr4bp_transfer_audit as fig510_audit


class Chapter5Figure510BCR4BPAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with fig510_audit.AUDIT_OUTPUT.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))
        with fig510_audit.TRAJECTORY_OUTPUT.open(
            newline="",
            encoding="utf-8",
        ) as stream:
            cls.trajectory_rows = list(csv.DictReader(stream))
        cls.by_case = {row["case_id"]: row for row in cls.rows}

    def test_two_de421_initialized_cases_are_locked(self) -> None:
        self.assertEqual(set(self.by_case), {"1", "2"})
        self.assertEqual(float(self.by_case["1"]["time_of_flight_days"]), 23.0)
        self.assertEqual(float(self.by_case["2"]["time_of_flight_days"]), 12.4)
        for row in self.rows:
            self.assertEqual(row["figure_id"], "5.10")
            self.assertEqual(row["epoch_utc"], fig510_audit.EPOCH_UTC)
            self.assertEqual(
                row["source_model"],
                "DE421-initialized planar Earth-Moon BCR4BP",
            )
            self.assertAlmostEqual(
                float(row["sun_phase_rad"]),
                1.2408947569934152,
                places=12,
            )
            self.assertAlmostEqual(
                float(row["sun_angular_rate_nd"]),
                -0.9253083768906855,
                places=12,
            )
            self.assertLess(float(row["initial_sun_xy_closure_nd"]), 1.0e-12)
            self.assertLess(float(row["frame_orthogonality_error"]), 1.0e-12)
            self.assertLess(
                float(row["earth_moon_barycenter_spk_error_km"]),
                1.0e-3,
            )
            self.assertEqual(
                row["minimum_moon_radius_method"],
                "strict_DOP853_dense_output_all_sampled_local_minima",
            )
            self.assertGreaterEqual(float(row["minimum_moon_radius_time_nd"]), 0.0)
            self.assertLessEqual(
                float(row["minimum_moon_radius_time_nd"]),
                float(row["time_of_flight_nd"]),
            )
            self.assertGreater(float(row["minimum_moon_radius_km"]), 4000.0)

    def test_numerical_gate_passes_but_paper_equivalence_does_not(self) -> None:
        for row in self.rows:
            self.assertEqual(row["numerical_acceptance"], "true")
            self.assertEqual(row["paper_equivalence"], "false")
            self.assertEqual(row["paper_tof_agreement"], "true")
            self.assertEqual(row["paper_delta_v_agreement"], "false")
            self.assertEqual(row["paper_model_geometry_match"], "false")
            self.assertTrue(fig510_audit.numerical_acceptance(row))
            self.assertFalse(fig510_audit.paper_equivalence(row))

        changed = dict(self.rows[0])
        changed["segment_time_origin"] = "reset"
        self.assertFalse(fig510_audit.numerical_acceptance(changed))
        changed = dict(self.rows[0])
        changed["independent_endpoint_error_km"] = "0.0011"
        self.assertFalse(fig510_audit.numerical_acceptance(changed))

        all_paper_gates = dict(self.rows[0])
        all_paper_gates["paper_delta_v_agreement"] = "true"
        all_paper_gates["paper_model_geometry_match"] = "true"
        self.assertTrue(fig510_audit.paper_equivalence(all_paper_gates))

    def test_absolute_time_segments_close_and_reset_time_is_a_negative_control(self) -> None:
        for row in self.rows:
            absolute_defect = float(row["segment_max_position_defect_km"])
            reset_defect = float(
                row["reset_time_negative_control_position_defect_km"]
            )
            self.assertEqual(row["segment_time_origin"], "absolute")
            self.assertLessEqual(absolute_defect, 1.0e-3)
            self.assertGreater(reset_defect, 1.0)
            self.assertGreater(reset_defect, 1.0e6 * absolute_defect)

    def test_delta_v_is_vector_based_and_sums_consistently(self) -> None:
        expected_totals = {"1": 72.62814172854959, "2": 89.04994709685531}
        for case_id, row in self.by_case.items():
            departure = float(row["departure_delta_v_m_s"])
            arrival = float(row["arrival_delta_v_m_s"])
            total = float(row["total_delta_v_m_s"])
            self.assertAlmostEqual(departure + arrival, total, places=10)
            self.assertAlmostEqual(total, expected_totals[case_id], places=6)
            self.assertGreater(
                abs(float(row["total_delta_v_relative_error"])),
                fig510_audit.PAPER_TOTAL_RELATIVE_ERROR_THRESHOLD,
            )

    def test_saved_trajectories_cover_both_models_and_cases(self) -> None:
        counts = Counter(
            (row["case_id"], row["model"]) for row in self.trajectory_rows
        )
        self.assertEqual(counts[("1", "bcr4bp_strict")], 1201)
        self.assertEqual(counts[("2", "bcr4bp_strict")], 1201)
        self.assertGreaterEqual(counts[("1", "cr3bp_seed")], 500)
        self.assertGreaterEqual(counts[("2", "cr3bp_seed")], 500)


if __name__ == "__main__":
    unittest.main()
