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

    def run_target_builder(
        self, output: Path | None = None, *, check: bool
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(TARGET_BUILDER),
            "--project-root",
            str(PROJECT_ROOT),
        ]
        if output is not None:
            command.extend(("--output", str(output)))
        if check:
            command.append("--check")
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

    def generate_target_registry(self, output: Path) -> None:
        result = self.run_target_builder(output, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def read_target_registry(
        self, path: Path
    ) -> tuple[list[str], list[dict[str, str]]]:
        with path.open("r", newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
        self.assertIsNotNone(reader.fieldnames)
        return list(reader.fieldnames or []), rows

    def write_target_registry(
        self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]
    ) -> None:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                lineterminator="\n",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)

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
        self.assertIn("projection_holdout=0/4 paper_projection=fail", result.stdout)
        self.assertIn(
            "chapter4_halo_12p40_source_gate=2/2 "
            "posthoc_projection=0/2 frozen_holdout=fail",
            result.stdout,
        )
        self.assertIn(
            "fig510_bcr4bp_numerical=2/2 paper_equivalence=0/2",
            result.stdout,
        )
        self.assertIn("png=54 pdf=54", result.stdout)

    def test_target_registry_matches_its_generator(self) -> None:
        result = self.run_target_builder(check=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("target registry is up to date", result.stdout)

    def test_generated_lf_target_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            self.assertNotIn(b"\r\n", output.read_bytes())
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_equivalent_crlf_target_registry_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            output.write_bytes(output.read_bytes().replace(b"\n", b"\r\n"))
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_target_registry_content_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            fieldnames, rows = self.read_target_registry(output)
            rows[0]["title"] += " changed"
            self.write_target_registry(output, fieldnames, rows)
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("field 'title' differs", result.stderr)

    def test_target_registry_field_order_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            fieldnames, rows = self.read_target_registry(output)
            fieldnames[0], fieldnames[1] = fieldnames[1], fieldnames[0]
            self.write_target_registry(output, fieldnames, rows)
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("field order differs", result.stderr)

    def test_target_registry_row_order_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            fieldnames, rows = self.read_target_registry(output)
            rows[0], rows[1] = rows[1], rows[0]
            self.write_target_registry(output, fieldnames, rows)
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("row 1 field 'figure_id' differs", result.stderr)

    def test_target_registry_missing_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "targets.csv"
            self.generate_target_registry(output)
            fieldnames, rows = self.read_target_registry(output)
            fieldnames.remove("next_action")
            self.write_target_registry(output, fieldnames, rows)
            result = self.run_target_builder(output, check=True)

        self.assertEqual(result.returncode, 1)
        self.assertIn("field order differs", result.stderr)

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
