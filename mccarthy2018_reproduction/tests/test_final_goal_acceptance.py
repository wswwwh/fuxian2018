from __future__ import annotations

import csv
from pathlib import Path
import tempfile
from typing import Callable
import unittest

from scripts import run_final_goal_acceptance as acceptance


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def method_rows() -> list[dict[str, str]]:
    return [
        {
            "run_id": "reference-run",
            "case_id": f"case_{case_index:02d}",
            "method": f"method_{method_index}",
            "bundle_dimension": "2",
            "max_invariance_residual": "1e-8",
            "manifold_jacobi_drift": "1e-15",
            "manifold_status": "pass",
            "runtime_seconds": "1.0",
            "peak_memory_mb_estimate": "2.0",
            "registry_sha256": "A" * 64,
            "cocycle_cache_sha256": "B" * 64,
            "source_git_commit": "reference-commit",
        }
        for case_index in range(15)
        for method_index in range(3)
    ]


class FinalGoalAcceptanceComparisonTests(unittest.TestCase):
    def compare(
        self, mutate: Callable[[list[dict[str, str]]], None] | None = None
    ) -> tuple[list[dict[str, str]], dict[str, int]]:
        reference = method_rows()
        candidate = [dict(row) for row in reference]
        for row in candidate:
            row["run_id"] = "isolated-run"
            row["runtime_seconds"] = "9.0"
            row["peak_memory_mb_estimate"] = "8.0"
            row["source_git_commit"] = "isolated-commit"
            row["manifold_jacobi_drift"] = "nan"
            row["manifold_status"] = "not_run_stage_f"
        if mutate is not None:
            mutate(candidate)
        with tempfile.TemporaryDirectory(prefix="final_acceptance_test_") as tmp:
            reference_path = Path(tmp) / "reference.csv"
            candidate_path = Path(tmp) / "candidate.csv"
            write_rows(reference_path, reference)
            write_rows(candidate_path, candidate)
            comparisons = acceptance.compare_method_tables(
                reference_path, candidate_path
            )
        return comparisons, acceptance.summarize_isolated_comparisons(comparisons)

    def test_expected_stage_f_reset_is_exposed_but_accepted(self) -> None:
        comparisons, summary = self.compare()
        acceptance.require_isolated_comparison_pass(summary)
        self.assertEqual(summary["total_contract_failures"], 0)
        self.assertEqual(summary["downstream_stage_f_reset_checks"], 90)
        self.assertEqual(
            summary["downstream_stage_f_reset_equality_differences"], 90
        )
        downstream = [
            row
            for row in comparisons
            if row["field_scope"] == "downstream_stage_f_reset"
        ]
        self.assertTrue(all(row["difference_expected"] == "true" for row in downstream))
        self.assertTrue(all(row["comparison_status"] == "pass" for row in downstream))

    def test_benchmark_owned_mismatch_is_a_hard_failure(self) -> None:
        _, summary = self.compare(
            lambda rows: rows[0].__setitem__("bundle_dimension", "1")
        )
        self.assertEqual(summary["benchmark_owned_failures"], 1)
        with self.assertRaisesRegex(RuntimeError, "comparison contract failed"):
            acceptance.require_isolated_comparison_pass(summary)

    def test_provenance_mismatch_is_a_hard_failure(self) -> None:
        _, summary = self.compare(
            lambda rows: rows[0].__setitem__("registry_sha256", "C" * 64)
        )
        self.assertEqual(summary["provenance_failures"], 1)
        with self.assertRaisesRegex(RuntimeError, "comparison contract failed"):
            acceptance.require_isolated_comparison_pass(summary)


if __name__ == "__main__":
    unittest.main()
