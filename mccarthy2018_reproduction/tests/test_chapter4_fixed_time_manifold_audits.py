"""Artifact-level gates for the Chapter 4 fixed-time manifold audits."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class FixedTimeManifoldAuditTests(unittest.TestCase):
    def test_halo_audit_passes_numerical_and_configuration_gates(self) -> None:
        rows = read_rows("chapter4_fig43_fig44_global_manifold_audit.csv")

        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["acceptance"] == "pass" for row in rows))
        self.assertTrue(all(int(row["phase_samples"]) >= 121 for row in rows))
        self.assertTrue(all(int(row["curve_samples"]) == 9 for row in rows))
        self.assertTrue(all(row["paper_projection_acceptance"] == "not_run" for row in rows))
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))
        self.assertTrue(all(row["numerical_acceptance"] == "pass" for row in rows))
        self.assertTrue(
            all(row["configuration_reach_acceptance"] == "pass" for row in rows)
        )
        self.assertEqual({row["artifact_fingerprint_version"] for row in rows}, {"1"})
        self.assertEqual(
            {row["npz_schema_version"] for row in rows},
            {"chapter4_fig43_fig44_fixed_time_audit_v2"},
        )
        self.assertTrue(all(row["local_linearization_gate"] == "pass" for row in rows))
        self.assertTrue(
            all(row["far_field_linearization_status"] == "diagnostic_only" for row in rows)
        )
        self.assertTrue(
            all(row["linear_reference_method"] == "base_trajectory_STM_first_order" for row in rows)
        )
        self.assertTrue(
            all(
                row["epsilon_selection_status"]
                == "project_visualization_parameter_uncalibrated"
                for row in rows
            )
        )
        self.assertEqual({float(row["perturbation_scale"]) for row in rows}, {4.5e-7})
        plus = [row for row in rows if row["figure_id"] == "4.3"]
        minus = [row for row in rows if row["figure_id"] == "4.4"]
        self.assertGreaterEqual(float(plus[-1]["surface_x_max"]), 1.02)
        self.assertLessEqual(float(minus[-1]["surface_x_min"]), 0.72)
        self.assertLessEqual(
            max(float(row["combined_history_snapshot_jacobi_drift_max"]) for row in rows),
            1.0e-10,
        )
        self.assertLessEqual(
            max(float(row["batched_vs_independent_max_abs_error"]) for row in rows),
            1.0e-9,
        )

        with np.load(
            DATA / "chapter4_fig43_fig44_global_manifold_audit.npz",
            allow_pickle=False,
        ) as evidence:
            self.assertEqual(evidence["plus_x_snapshot_states"].shape, (4, 121, 9, 6))
            self.assertEqual(evidence["minus_x_snapshot_states"].shape, (4, 121, 9, 6))
            self.assertEqual(
                evidence["plus_x_linear_snapshot_state_separation_norms"].shape,
                (4, 121, 9),
            )

    def test_vertical_audit_passes_numerical_and_configuration_gates(self) -> None:
        rows = read_rows("chapter4_fig45_fig48_vertical_manifold_audit.csv")

        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["acceptance"] == "pass" for row in rows))
        self.assertTrue(all(int(row["phase_samples"]) >= 121 for row in rows))
        self.assertTrue(all(int(row["curve_samples"]) == 33 for row in rows))
        self.assertTrue(all(row["paper_projection_acceptance"] == "not_run" for row in rows))
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))
        self.assertTrue(all(row["numerical_acceptance"] == "pass" for row in rows))
        self.assertTrue(
            all(row["configuration_reach_acceptance"] == "pass" for row in rows)
        )
        self.assertEqual({row["artifact_fingerprint_version"] for row in rows}, {"1"})
        self.assertEqual(
            {row["npz_schema_version"] for row in rows},
            {"fixed_time_vertical_manifold_audit_v2"},
        )
        self.assertTrue(all(row["local_linearization_gate"] == "pass" for row in rows))
        self.assertTrue(
            all(row["far_field_linearization_status"] == "diagnostic_only" for row in rows)
        )
        self.assertTrue(
            all(row["linear_reference_method"] == "base_trajectory_STM_first_order" for row in rows)
        )
        self.assertTrue(
            all(
                row["epsilon_selection_status"]
                == "project_visualization_parameter_uncalibrated"
                for row in rows
            )
        )
        self.assertEqual({float(row["perturbation_scale"]) for row in rows}, {4.5e-7})
        plus = [row for row in rows if row["figure_id"] == "4.5"]
        minus = [row for row in rows if row["figure_id"] == "4.6"]
        self.assertGreaterEqual(float(plus[-1]["snapshot_x_max"]), 1.15)
        self.assertLessEqual(float(minus[-1]["snapshot_x_min"]), 0.30)
        self.assertLessEqual(max(float(row["jacobi_drift_max"]) for row in rows), 1.0e-10)
        self.assertLessEqual(
            max(
                float(row["batched_vs_independent_state_max_abs_error"])
                for row in rows
            ),
            1.0e-9,
        )

        with np.load(
            DATA / "chapter4_fig45_fig48_vertical_manifold_audit.npz",
            allow_pickle=False,
        ) as evidence:
            self.assertEqual(evidence["plus_x_snapshot_states"].shape, (4, 121, 33, 6))
            self.assertEqual(evidence["minus_x_snapshot_states"].shape, (4, 121, 33, 6))
            self.assertEqual(
                evidence["plus_x_linear_snapshot_state_separation_norms"].shape,
                (4, 121, 33),
            )


if __name__ == "__main__":
    unittest.main()
