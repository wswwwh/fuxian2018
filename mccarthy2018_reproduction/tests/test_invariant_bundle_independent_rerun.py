from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RERUN = ROOT / "research" / "invariant_bundles" / "independent_rerun"
COMPARISON = RERUN / "comparison_to_stage_f.csv"
REPORT = RERUN / "independent_rerun_report.md"
PROCESS = RERUN / "logs" / "process_manifest.json"
AUTHORITATIVE = RERUN / "hashes" / "authoritative_before_after.csv"
ARTIFACTS = RERUN / "hashes" / "artifact_hashes.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class IndependentRerunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.comparison = rows(COMPARISON)

    def test_fresh_processes_and_unique_run_id(self) -> None:
        manifest = json.loads(PROCESS.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["processes"]), 2)
        pids = {record["pid"] for record in manifest["processes"]}
        self.assertEqual(len(pids), 2)
        self.assertNotIn(manifest["controller_pid"], pids)
        self.assertTrue(manifest["independent_run_id"].startswith("FRESH-"))
        self.assertTrue(all(record["return_code"] == 0 for record in manifest["processes"]))

    def test_full_fresh_outputs_and_cocycle_count(self) -> None:
        self.assertEqual(len(rows(RERUN / "results" / "csv" / "method_comparison.csv")), 45)
        self.assertEqual(len(rows(RERUN / "results" / "csv" / "manifold_convergence.csv")), 126)
        self.assertEqual(len(list((RERUN / "results" / "npz" / "cocycles").glob("*.npz"))), 15)
        self.assertTrue((RERUN / "results" / "npz" / "method_comparison.npz").is_file())
        self.assertTrue((RERUN / "results" / "npz" / "manifold_convergence.npz").is_file())

    def test_all_scientific_field_comparisons_pass(self) -> None:
        failures = [row for row in self.comparison if row["comparison_status"] == "fail"]
        self.assertEqual(failures, [])
        exact_fields = {"classification", "research_status", "bundle_dimension", "manifold_status", "status"}
        checked = [row for row in self.comparison if row["field"] in exact_fields]
        self.assertTrue(checked)
        self.assertTrue(all(row["match"] == "true" for row in checked))

    def test_authoritative_results_were_not_overwritten(self) -> None:
        protected = rows(AUTHORITATIVE)
        self.assertGreaterEqual(len(protected), 6)
        self.assertTrue(all(row["unchanged"] == "true" for row in protected))

    def test_artifact_hashes_and_truth_boundary(self) -> None:
        for row in rows(ARTIFACTS):
            path = ROOT / row["artifact"]
            self.assertEqual(int(row["bytes"]), path.stat().st_size)
            self.assertEqual(row["sha256"], sha256(path))
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("Overall acceptance: `PASS`", report)
        self.assertIn("0/4", report)


if __name__ == "__main__":
    unittest.main()
