from __future__ import annotations

import csv
import json
from pathlib import Path
import unittest

import numpy as np

from qp_orbits.artifact_fingerprints import fingerprint_matches


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "ablation_study.json"
CSV_PATH = RESEARCH / "results" / "csv" / "ablation_study.csv"
NPZ_PATH = RESEARCH / "results" / "npz" / "ablation_study.npz"
HASH_PATH = RESEARCH / "results" / "logs" / "ablation_artifact_hashes.csv"
PAPER_PATH = RESEARCH / "paper" / "ablation_results.md"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class InvariantBundleAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.rows = rows(CSV_PATH)

    def test_exact_case_variant_grid(self) -> None:
        self.assertEqual(len(self.rows), 5 * 7)
        self.assertEqual({row["case_id"] for row in self.rows}, set(self.config["cases"]))
        for case in self.config["cases"]:
            self.assertEqual(
                [row["variant"] for row in self.rows if row["case_id"] == case],
                self.config["variants"],
            )

    def test_metrics_or_explicit_method_exception_are_preserved(self) -> None:
        for row in self.rows:
            if row["classification"] == "method_exception":
                self.assertEqual(row["research_status"], "fail")
                self.assertTrue(row["failure_reason"])
            else:
                for field in (
                    "bundle_residual_max", "phase_principal_angle_max_deg",
                    "cross_resolution_angle_max_deg", "manifold_geometry_distance", "runtime_seconds",
                ):
                    self.assertTrue(np.isfinite(float(row[field])), (row["case_id"], row["variant"], field))

    def test_route_h_dimension_seed_never_promotes_physical_failure(self) -> None:
        for case in ("route_h_member_68", "route_h_member_32"):
            subset = {row["variant"]: row for row in self.rows if row["case_id"] == case}
            self.assertEqual(subset[self.config["variants"][5]]["bundle_dimension"], "1")
            self.assertEqual(
                subset[self.config["variants"][5]]["classification"],
                "invalid_1d_complex_pair_ablation_control",
            )
            seeded = subset["qr_svd_phase_alignment_schur_dimension_seed"]
            self.assertEqual(seeded["bundle_dimension"], "2")
            self.assertEqual(seeded["research_status"], "fail")

    def test_npz_and_six_publication_figure_files_exist(self) -> None:
        with np.load(NPZ_PATH, allow_pickle=False) as archive:
            for case in self.config["cases"]:
                self.assertIn(
                    f"{case}__qr_svd_phase_alignment_schur_dimension_seed__basis",
                    archive.files,
                )
        for stem in (
            "ablation_bundle_residual", "ablation_phase_continuity", "ablation_manifold_geometry"
        ):
            for suffix in ("png", "pdf"):
                path = RESEARCH / "figures" / f"{stem}.{suffix}"
                self.assertGreater(path.stat().st_size, 1000)

    def test_hash_manifest_and_truth_boundary(self) -> None:
        for row in rows(HASH_PATH):
            path = ROOT / row["artifact"]
            self.assertTrue(
                fingerprint_matches(
                    path,
                    expected_bytes=int(row["bytes"]),
                    expected_sha256=row["sha256"],
                    hash_mode=row["hash_mode"],
                ),
                row["artifact"],
            )
        paper = PAPER_PATH.read_text(encoding="utf-8")
        self.assertIn("paper_projection=fail", paper)
        self.assertIn("不是Stage-F", paper)


if __name__ == "__main__":
    unittest.main()
