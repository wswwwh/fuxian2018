"""Behavior tests for the read-only reproduction smoke validator."""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = PROJECT_ROOT / "scripts" / "validate_reproduction_smoke.py"
TARGET_BUILDER = PROJECT_ROOT / "scripts" / "build_reproduction_targets.py"


class ReproductionSmokeCliTests(unittest.TestCase):
    def write_targets(self, project_root: Path, figure_ids: list[str]) -> None:
        path = project_root / "data" / "reproduction_targets.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=["figure_id", "acceptance_tier", "source_type"],
            )
            writer.writeheader()
            for figure_id in figure_ids:
                writer.writerow(
                    {
                        "figure_id": figure_id,
                        "acceptance_tier": "V2",
                        "source_type": "explicit",
                    }
                )

    def run_validator(self, project_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--project-root",
                str(project_root),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_missing_target_registry_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_validator(Path(directory))

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "missing required file: data/reproduction_targets.csv",
            result.stderr,
        )

    def test_duplicate_target_figure_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            self.write_targets(project_root, ["2.1", "2.1"])
            result = self.run_validator(project_root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate figure_id in target registry: 2.1", result.stderr)

    def test_current_repository_passes_with_auditable_summary(self) -> None:
        result = self.run_validator(PROJECT_ROOT)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SMOKE PASS", result.stdout)
        self.assertIn("figures=54", result.stdout)
        self.assertIn("targets_v0=13 targets_v2=41", result.stdout)
        self.assertIn("route_h_rows=", result.stdout)
        self.assertIn("route_h_cold_start_status=fail", result.stdout)
        self.assertIn("route_h_hybrid_cold_start_status=pass", result.stdout)
        self.assertIn("staged_goal_status=", result.stdout)
        self.assertIn("fig42_digitized_status=", result.stdout)
        self.assertIn(
            "chapter4_fixed_time=16/16 projection_diagnostic_rows=16",
            result.stdout,
        )
        self.assertIn("projection_alerts=", result.stdout)
        self.assertIn("paper_projection=not_run", result.stdout)
        self.assertIn(
            "fig510_bcr4bp_numerical=2/2 paper_equivalence=0/2",
            result.stdout,
        )
        self.assertIn("png=54 pdf=54", result.stdout)

    def test_target_registry_matches_its_generator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TARGET_BUILDER), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("target registry is up to date", result.stdout)

    def test_incomplete_parameter_extraction_returns_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            target_path = project_root / "data" / "reproduction_targets.csv"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                PROJECT_ROOT / "data" / "reproduction_targets.csv",
                target_path,
            )
            with target_path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
                fieldnames = list(rows[0])
            rows[2]["target_status"] = "caption_target_needs_parameter_extraction"
            with target_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result = self.run_validator(project_root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("incomplete target extraction for figure: 2.3", result.stderr)


if __name__ == "__main__":
    unittest.main()
