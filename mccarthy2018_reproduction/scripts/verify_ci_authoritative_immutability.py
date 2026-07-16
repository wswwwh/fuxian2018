#!/usr/bin/env python3
"""Snapshot and compare committed authoritative files around CI work."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def current_rows() -> list[dict[str, Any]]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for relative in config["authoritative_files_protected"]:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"protected authoritative file missing: {relative}")
        rows.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def snapshot(manifest: Path) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "ci_authoritative_snapshot_v1",
        "config_sha256": sha256(CONFIG),
        "files": current_rows(),
    }
    manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"authoritative snapshot PASS files={len(payload['files'])}")


def compare(manifest: Path, report: Path) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    before = {row["path"]: row for row in payload["files"]}
    after = {row["path"]: row for row in current_rows()}
    if before.keys() != after.keys():
        raise RuntimeError("protected authoritative path set changed")
    rows: list[dict[str, Any]] = []
    for path in before:
        left = before[path]
        right = after[path]
        unchanged = (
            int(left["bytes"]) == int(right["bytes"])
            and left["sha256"] == right["sha256"]
        )
        rows.append(
            {
                "schema_version": "ci_authoritative_before_after_v1",
                "path": path,
                "before_bytes": left["bytes"],
                "after_bytes": right["bytes"],
                "before_sha256": left["sha256"],
                "after_sha256": right["sha256"],
                "unchanged": str(unchanged).lower(),
            }
        )
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    changed = [row for row in rows if row["unchanged"] != "true"]
    if changed:
        raise RuntimeError(f"authoritative files changed: {[row['path'] for row in changed]}")
    print(f"authoritative immutability PASS files={len(rows)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("--manifest", type=Path, required=True)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--manifest", type=Path, required=True)
    compare_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        snapshot(args.manifest)
    else:
        compare(args.manifest, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
