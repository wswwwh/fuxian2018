"""Contracts for committed cross-platform artifact hash manifests."""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "refresh_portable_artifact_hash_manifests.py"


class PortableArtifactHashManifestTests(unittest.TestCase):
    def test_all_committed_artifact_manifests_are_portable_and_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("manifests=9", result.stdout)

    def test_manifest_modes_distinguish_text_and_binary_artifacts(self) -> None:
        manifest = (
            ROOT
            / "research"
            / "invariant_bundles"
            / "ci_validation"
            / "artifact_hashes.csv"
        )
        with manifest.open("r", encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))

        modes = {row["hash_mode"] for row in rows}
        self.assertEqual(modes, {"raw_bytes", "utf8_lf_normalized"})


if __name__ == "__main__":
    unittest.main()
