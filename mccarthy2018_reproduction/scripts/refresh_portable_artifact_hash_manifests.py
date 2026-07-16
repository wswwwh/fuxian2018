"""Refresh or verify committed artifact manifests with portable hash semantics."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import io
from pathlib import Path
import subprocess
import sys

from _paths import PROJECT_ROOT
from qp_orbits.artifact_fingerprints import artifact_fingerprint


REPOSITORY_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=PROJECT_ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
).resolve()


@dataclass(frozen=True)
class ManifestSpec:
    path: Path
    artifact_root: Path
    path_field: str
    schema_version: str | None = None


MANIFESTS = (
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/results/logs/independent_schur_backend_artifact_hashes.csv",
        PROJECT_ROOT,
        "artifact",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/results/logs/ablation_artifact_hashes.csv",
        PROJECT_ROOT,
        "artifact",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/independent_rerun/hashes/artifact_hashes.csv",
        PROJECT_ROOT,
        "artifact",
    ),
    ManifestSpec(
        PROJECT_ROOT / "research/invariant_bundles/literature_validation/artifact_hashes.csv",
        PROJECT_ROOT,
        "path",
        "literature_stage_artifact_hash_v2",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/paper_release_validation/artifact_hashes.csv",
        PROJECT_ROOT,
        "path",
        "paper_release_stage_artifact_hash_v2",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/results/logs/qr_svd_failure_artifact_hashes.csv",
        PROJECT_ROOT,
        "artifact",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/adviser_summary_validation/final_acceptance/artifact_hashes.csv",
        REPOSITORY_ROOT,
        "path",
        "final_goal_acceptance_artifact_hash_v3",
    ),
    ManifestSpec(
        PROJECT_ROOT
        / "research/invariant_bundles/adviser_summary_validation/artifact_hashes.csv",
        PROJECT_ROOT,
        "path",
        "adviser_summary_stage_artifact_hash_v2",
    ),
    ManifestSpec(
        PROJECT_ROOT / "research/invariant_bundles/ci_validation/artifact_hashes.csv",
        REPOSITORY_ROOT,
        "path",
        "ci_stage_artifact_hash_v3",
    ),
)


def read_manifest(spec: ManifestSpec) -> tuple[list[str], list[dict[str, str]]]:
    with spec.path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    required = {spec.path_field, "bytes", "sha256"}
    missing = sorted(required - set(fieldnames))
    if missing:
        raise RuntimeError(f"{spec.path}: missing manifest field {missing[0]}")
    if "hash_mode" not in fieldnames:
        fieldnames.insert(fieldnames.index("bytes"), "hash_mode")
    return fieldnames, rows


def artifact_path(spec: ManifestSpec, row: dict[str, str]) -> Path:
    path = (spec.artifact_root / row[spec.path_field]).resolve()
    try:
        path.relative_to(spec.artifact_root)
    except ValueError as error:
        raise RuntimeError(
            f"artifact escapes declared root: {row[spec.path_field]}"
        ) from error
    if not path.is_file():
        raise FileNotFoundError(f"missing manifest artifact: {path}")
    return path


def refreshed_rows(
    spec: ManifestSpec, rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    refreshed: list[dict[str, str]] = []
    for row in rows:
        fingerprint = artifact_fingerprint(artifact_path(spec, row))
        current = dict(row)
        if spec.schema_version is not None:
            current["schema_version"] = spec.schema_version
        current.update(
            {
                "hash_mode": fingerprint.hash_mode,
                "bytes": str(fingerprint.bytes),
                "sha256": fingerprint.sha256,
            }
        )
        refreshed.append(current)
    return refreshed


def render(fieldnames: list[str], rows: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def refresh(*, check: bool) -> tuple[int, int]:
    manifest_count = 0
    artifact_count = 0
    stale: list[str] = []
    for spec in MANIFESTS:
        fieldnames, rows = read_manifest(spec)
        expected = render(fieldnames, refreshed_rows(spec, rows))
        current = spec.path.read_text(encoding="utf-8-sig")
        if current != expected:
            if check:
                stale.append(spec.path.relative_to(PROJECT_ROOT).as_posix())
            else:
                with spec.path.open("w", encoding="utf-8", newline="") as stream:
                    stream.write(expected)
        manifest_count += 1
        artifact_count += len(rows)
    if stale:
        raise RuntimeError("stale portable artifact manifest: " + stale[0])
    return manifest_count, artifact_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify manifests without writing files.",
    )
    args = parser.parse_args()
    try:
        manifests, artifacts = refresh(check=args.check)
    except (FileNotFoundError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"portable artifact manifests FAIL: {error}", file=sys.stderr)
        return 1
    action = "CHECK PASS" if args.check else "WRITE PASS"
    print(
        f"portable artifact manifests {action}: "
        f"manifests={manifests} artifacts={artifacts}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
