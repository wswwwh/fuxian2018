"""Artifact gates for the bounded 12.40-day halo post-hoc diagnostic."""

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
CSV_PATH = DATA / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.npz"
PORTABLE_SCRIPT = ROOT / "scripts" / "validate_chapter4_halo_12p40_portable_replay.py"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter4_halo_12p40_posthoc_diagnostic as posthoc
import validate_chapter4_halo_12p40_portable_replay as portable


class Chapter4Halo12p40PosthocDiagnosticTests(unittest.TestCase):
    def test_csv_check_accepts_crlf_but_rejects_content_drift(self) -> None:
        rows = [{"source_variant": "current_n9", "figure_id": "4.3"}]
        rendered = posthoc._csv_bytes(rows).decode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagnostic.csv"
            path.write_bytes(rendered.replace("\n", "\r\n").encode("utf-8"))
            original = posthoc.CSV_PATH
            posthoc.CSV_PATH = path
            try:
                self.assertTrue(posthoc._stored_csv_matches(rows))
                path.write_text(
                    rendered.replace("current_n9", "changed"),
                    encoding="utf-8",
                    newline="",
                )
                self.assertFalse(posthoc._stored_csv_matches(rows))
            finally:
                posthoc.CSV_PATH = original

    def test_candidate_source_and_evidence_boundaries(self) -> None:
        with CSV_PATH.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            {(row["source_variant"], row["figure_id"]) for row in rows},
            {
                ("current_n9", "4.3"),
                ("current_n9", "4.4"),
                ("thesis_12p40_n21", "4.3"),
                ("thesis_12p40_n21", "4.4"),
            },
        )
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in rows)
        )
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))
        self.assertTrue(
            all(row["source_selection_red_mask_read"] == "false" for row in rows)
        )
        self.assertTrue(all(row["projection_red_mask_read"] == "true" for row in rows))
        current = [row for row in rows if row["source_variant"] == "current_n9"]
        self.assertTrue(
            all(row["replay_status"] == "exact_frozen_holdout_replay" for row in current)
        )
        candidate = [
            row for row in rows if row["source_variant"] == "thesis_12p40_n21"
        ]
        for row in candidate:
            self.assertLessEqual(abs(float(row["source_period_days"]) - 12.40), 0.005)
            self.assertLessEqual(abs(float(row["source_ay_km"]) - 41815.0), 50.0)
            self.assertLessEqual(abs(float(row["source_az_km"]) - 35783.0), 50.0)
            self.assertLessEqual(float(row["source_curve_residual"]), 1.0e-9)
            self.assertLessEqual(float(row["dg_determinant_error_from_one"]), 5.0e-9)
            self.assertLessEqual(
                float(row["unstable_eigenvalue_relative_imaginary"]), 1.0e-10
            )
            self.assertLessEqual(float(row["source_jacobi_span"]), 1.0e-6)
            self.assertLessEqual(float(row["manifold_jacobi_drift_max"]), 1.0e-10)

    def test_arrays_and_recomputation_check(self) -> None:
        with np.load(NPZ_PATH, allow_pickle=False) as evidence:
            self.assertEqual(evidence["current_snapshot_states"].shape, (2, 4, 121, 9, 6))
            self.assertEqual(
                evidence["candidate_snapshot_states"].shape,
                (2, 4, 121, 21, 6),
            )
            self.assertTrue(np.all(np.isfinite(evidence["candidate_snapshot_states"])))
            self.assertEqual(int(evidence["selected_family_index"][0]), 3)
        result = subprocess.run(
            [sys.executable, str(PORTABLE_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("chapter4_halo_12p40_portable_replay: PASS", result.stdout)
        self.assertIn("candidate_masks=exact", result.stdout)
        self.assertIn("frozen_holdout=fail, paper_3d=false", result.stdout)

    def test_portable_envelope_accepts_solver_scale_drift(self) -> None:
        recomputed = np.zeros((2, 3, 2), dtype=float)
        refined = np.full_like(recomputed, 1.0e-8)
        stored = np.full_like(recomputed, 2.0e-8)
        comparison = portable.compare_with_refinement_envelope(
            "synthetic_states", stored, recomputed, refined
        )
        self.assertLessEqual(comparison.maximum_ratio, 1.0)

    def test_portable_envelope_rejects_material_drift(self) -> None:
        recomputed = np.zeros((2, 3, 2), dtype=float)
        refined = np.full_like(recomputed, 1.0e-8)
        stored = np.full_like(recomputed, 5.0e-8)
        with self.assertRaisesRegex(RuntimeError, "step-refinement envelope"):
            portable.compare_with_refinement_envelope(
                "synthetic_states", stored, recomputed, refined
            )


if __name__ == "__main__":
    unittest.main()
