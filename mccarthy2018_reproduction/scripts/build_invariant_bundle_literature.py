#!/usr/bin/env python3
"""Build the verified literature matrix and its auditable stage evidence."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any
from urllib.parse import urlparse

import numpy as np

from qp_orbits.artifact_fingerprints import fingerprint_fields


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "configs"
    / "literature_verification.json"
)
PAPER = ROOT / "research" / "invariant_bundles" / "paper"
DEFAULT_EVIDENCE = ROOT / "research" / "invariant_bundles" / "literature_validation"
MATRIX_FIELDS = [
    "reference_id",
    "authors",
    "title",
    "year",
    "venue",
    "doi",
    "official_url",
    "method",
    "problem",
    "relation_to_this_work",
    "claim_supported",
    "verified",
]
TOPIC_FIELDS = [
    "topic_id",
    "topic_label",
    "reference_count",
    "reference_ids",
    "status",
]
LOG_FIELDS = [
    "reference_id",
    "source_type",
    "verification_date",
    "verification_method",
    "official_domain",
    "doi",
    "doi_status",
    "metadata_status",
]
FORMAL_SOURCE_TYPES = {
    "journal_article",
    "masters_thesis",
    "conference_paper",
    "official_proceedings_article",
    "monograph",
    "book_chapter",
}
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if config.get("study_positioning") != "numerical_framework_and_systematic_comparison":
        errors.append("study_positioning must remain numerical_framework_and_systematic_comparison")
    references = config.get("references", [])
    topics = config.get("required_topics", [])
    if len(references) < 20:
        errors.append(f"formal reference count is {len(references)}; expected at least 20")
    if len(topics) != 9:
        errors.append(f"required topic count is {len(topics)}; expected exactly 9")
    topic_ids = [row.get("topic_id", "") for row in topics]
    if len(topic_ids) != len(set(topic_ids)):
        errors.append("required topic IDs are not unique")
    known_topics = set(topic_ids)
    seen_ids: set[str] = set()
    seen_dois: set[str] = set()
    coverage = {topic_id: [] for topic_id in topic_ids}
    no_doi: list[str] = []
    for row in references:
        missing = [field for field in MATRIX_FIELDS[:-1] if field not in row]
        if missing:
            errors.append(f"{row.get('reference_id', '<unknown>')}: missing fields {missing}")
        reference_id = str(row.get("reference_id", ""))
        if not reference_id or reference_id in seen_ids:
            errors.append(f"duplicate or blank reference_id: {reference_id!r}")
        seen_ids.add(reference_id)
        if row.get("verified") is not True:
            errors.append(f"{reference_id}: metadata is not verified")
        if row.get("source_type") not in FORMAL_SOURCE_TYPES:
            errors.append(f"{reference_id}: unsupported source type {row.get('source_type')!r}")
        official_url = str(row.get("official_url", ""))
        if not official_url.startswith("https://") or not urlparse(official_url).netloc:
            errors.append(f"{reference_id}: official_url is not a valid HTTPS source")
        doi = str(row.get("doi", "")).strip()
        doi_status = row.get("doi_status")
        if doi:
            folded = doi.casefold()
            if not DOI_PATTERN.fullmatch(doi):
                errors.append(f"{reference_id}: malformed DOI {doi!r}")
            if folded in seen_dois:
                errors.append(f"{reference_id}: duplicate DOI {doi!r}")
            seen_dois.add(folded)
            if doi_status != "verified":
                errors.append(f"{reference_id}: DOI exists but doi_status is {doi_status!r}")
        else:
            no_doi.append(reference_id)
            if doi_status != "not_assigned":
                errors.append(f"{reference_id}: blank DOI must be explicitly not_assigned")
        row_topics = row.get("topics", [])
        unknown = sorted(set(row_topics) - known_topics)
        if unknown:
            errors.append(f"{reference_id}: unknown topics {unknown}")
        for topic_id in row_topics:
            coverage[topic_id].append(reference_id)
        flattened = " ".join(str(value) for value in row.values()).casefold()
        if any(marker in flattened for marker in ("tbd", "todo", "doi pending", "doi unknown")):
            errors.append(f"{reference_id}: unresolved placeholder text remains")
    for topic_id, ids in coverage.items():
        if not ids:
            errors.append(f"required topic has no verified source: {topic_id}")
    required_boundaries = "\n".join(config.get("truth_boundaries", []))
    for marker in (
        "0/4",
        "paper_projection=fail",
        "paper_3d=false",
        "Route H",
        "submission readiness",
    ):
        if marker not in required_boundaries:
            errors.append(f"truth boundary marker missing: {marker}")
    if errors:
        raise ValueError("literature configuration failed validation:\n- " + "\n- ".join(errors))
    return {
        "reference_count": len(references),
        "doi_count": len(seen_dois),
        "no_doi_count": len(no_doi),
        "no_doi_reference_ids": no_doi,
        "topic_coverage": coverage,
    }


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def matrix_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            **{field: row.get(field, "") for field in MATRIX_FIELDS},
            "verified": "yes" if row["verified"] else "no",
        }
        for row in config["references"]
    ]


def topic_rows(config: dict[str, Any], coverage: dict[str, list[str]]) -> list[dict[str, Any]]:
    return [
        {
            "topic_id": topic["topic_id"],
            "topic_label": topic["topic_label"],
            "reference_count": len(coverage[topic["topic_id"]]),
            "reference_ids": ";".join(coverage[topic["topic_id"]]),
            "status": "covered" if coverage[topic["topic_id"]] else "missing",
        }
        for topic in config["required_topics"]
    ]


def verification_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "reference_id": row["reference_id"],
            "source_type": row["source_type"],
            "verification_date": config["verification_date"],
            "verification_method": row["verification_method"],
            "official_domain": urlparse(row["official_url"]).netloc,
            "doi": row["doi"],
            "doi_status": row["doi_status"],
            "metadata_status": "verified",
        }
        for row in config["references"]
    ]


def bibtex(config: dict[str, Any]) -> str:
    blocks: list[str] = []
    for row in config["references"]:
        entry_type = row["bibtex_type"]
        venue_field = {
            "article": "journal",
            "inproceedings": "booktitle",
            "mastersthesis": "school",
            "incollection": "booktitle",
            "book": "publisher",
        }[entry_type]
        venue_value = row.get("publisher", row["venue"]) if entry_type == "book" else row["venue"]
        fields = [
            ("author", row["authors"].replace("; ", " and ")),
            ("title", "{" + row["title"] + "}"),
            (venue_field, venue_value),
            ("year", str(row["year"])),
        ]
        for optional in ("volume", "number", "pages"):
            if row.get(optional):
                fields.append((optional, str(row[optional])))
        if row["doi"]:
            fields.append(("doi", row["doi"]))
        fields.append(("url", row["official_url"]))
        rendered = ",\n".join(f"  {key} = {{{value}}}" for key, value in fields)
        blocks.append(f"@{entry_type}{{{row['reference_id']},\n{rendered}\n}}")
    return "\n\n".join(blocks) + "\n"


def positioning_markdown(config: dict[str, Any], stats: dict[str, Any]) -> str:
    return f"""# Literature-grounded paper positioning

## Decision

`{config['study_positioning']}`

The matrix contains {stats['reference_count']} verified formal sources: {stats['doi_count']} with a checked DOI and {stats['no_doi_count']} formal thesis/conference sources explicitly recorded as `not_assigned` rather than supplied with a guessed DOI. All nine required topics are covered.

## Why this is the defensible position

- Parameterization methods for invariant tori and whiskers are established in [@HaroLlave2006Numerical; @HaroLlave2006Rigorous; @HaroEtAl2016].
- Cocycle iteration and phase-dependent bundle computation are established in [@Jorba2001; @WyshamMeiss2006; @HuguetLlaveSire2013].
- Continuous orthonormalization, QR/SVD spectral diagnostics, and covariant Lyapunov vectors are established in [@DieciRussellVanVleck1994; @DieciVanVleck2002; @GinelliEtAl2007; @KuptsovParlitz2012].
- Real and periodic Schur reordering are established numerical linear algebra in [@BaiDemmel1993; @GranatKagstrom2006].
- CR3BP quasi-periodic tori and their manifold applications predate this study [@OlikaraHowell2010; @McCarthy2018; @McCarthyHowell2023].

The present work therefore does **not** claim a new invariant-bundle theorem, the first Schur method, the first shifted QR/SVD method, or the first quasi-periodic CR3BP manifold computation. Its supported contribution is an auditable 15-case comparison framework that binds three numerical routes to frozen acceptance metrics, independent Schur-backend agreement, bounded failure classification, ablation evidence, fresh-process reproducibility, and CI guards.

## Scientific truth boundary

- The frozen McCarthy reproduction level is unchanged.
- Chapter 4 remains a `0/4` projection holdout with `paper_projection=fail` and `paper_3d=false`.
- The physical Route H corrected-rho cases remain two-dimensional real conjugate subspaces and failed one-dimensional acceptance; the legacy seed-rho case is only a positive control.
- A two-dimensional real Schur subspace is not relabelled as a one-dimensional real direction.
- Local bundle convergence and global manifold-sheet convergence are reported separately.
- This positioning is **not_submission_ready**: literature coverage and independent validation do not remove the unresolved scientific limitations.

## Rejected stronger labels

- `methodological_innovation`: rejected because the constituent algorithms and theory are established in the verified literature.
- `failure_mode_and_diagnostic_study`: informative as a secondary emphasis, but too narrow for the full benchmark, independent-backend, manifold, and reproducibility scope.
"""


def write_npz(
    path: Path,
    config: dict[str, Any],
    coverage: dict[str, list[str]],
) -> None:
    references = config["references"]
    topic_ids = [row["topic_id"] for row in config["required_topics"]]
    membership = np.array(
        [[topic_id in row["topics"] for topic_id in topic_ids] for row in references],
        dtype=np.bool_,
    )
    np.savez_compressed(
        path,
        schema_version=np.array(["invariant_bundle_literature_validation_npz_v1"]),
        reference_ids=np.array([row["reference_id"] for row in references]),
        years=np.array([row["year"] for row in references], dtype=np.int64),
        doi_present=np.array([bool(row["doi"]) for row in references], dtype=np.bool_),
        verified=np.ones(len(references), dtype=np.bool_),
        topic_ids=np.array(topic_ids),
        topic_membership=membership,
        topic_reference_counts=np.array(
            [len(coverage[topic_id]) for topic_id in topic_ids], dtype=np.int64
        ),
        positioning=np.array([config["study_positioning"]]),
    )


def write_hash_manifest(
    evidence: Path,
    config_path: Path,
    outputs: list[Path],
) -> None:
    target = evidence / "artifact_hashes.csv"
    inputs = [
        config_path,
        Path(__file__).resolve(),
        ROOT / "tests" / "test_invariant_bundle_literature.py",
    ]
    paths = inputs + [path for path in outputs if path != target]
    rows = [
        {
            "schema_version": "literature_stage_artifact_hash_v2",
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            **fingerprint_fields(path),
        }
        for path in paths
    ]
    write_csv(target, list(rows[0]), rows)


def build(config_path: Path, evidence: Path) -> dict[str, Any]:
    if evidence.exists() and any(evidence.iterdir()):
        raise RuntimeError(f"refusing to overwrite literature evidence: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)
    logs = evidence / "logs"
    logs.mkdir()
    started = datetime.now(timezone.utc)
    config = load_config(config_path)
    stats = validate_config(config)
    matrix = PAPER / "literature_matrix.csv"
    topic_coverage = PAPER / "literature_topic_coverage.csv"
    positioning = PAPER / "literature_positioning.md"
    references_bib = PAPER / "references_verified.bib"
    verification_log = logs / "literature_verification_log.csv"
    write_csv(matrix, MATRIX_FIELDS, matrix_rows(config))
    write_csv(
        topic_coverage,
        TOPIC_FIELDS,
        topic_rows(config, stats["topic_coverage"]),
    )
    positioning.write_text(
        positioning_markdown(config, stats), encoding="utf-8"
    )
    references_bib.write_text(bibtex(config), encoding="utf-8")
    write_csv(verification_log, LOG_FIELDS, verification_rows(config))
    validation_npz = evidence / "literature_validation.npz"
    write_npz(validation_npz, config, stats["topic_coverage"])
    failures = evidence / "failure_evidence.md"
    failures.write_text(
        "# Literature-verification failure and boundary evidence\n\n"
        "## Unresolved metadata failures\n\n"
        "None among the 25 retained formal sources. Sources with conflicting or incomplete "
        "metadata were excluded rather than silently normalized.\n\n"
        "## Intentionally blank DOI fields\n\n"
        + "\n".join(f"- `{reference_id}`: no DOI assigned in the verified formal source." for reference_id in stats["no_doi_reference_ids"])
        + "\n\n## Access limitations encountered\n\n"
        "Some publisher pages reject automated full-text retrieval or are protected by "
        "robots rules. Their bibliographic fields were cross-checked using the publisher "
        "landing page, DOI registry metadata, and/or an official institutional record. "
        "This package records metadata verification, not a claim that every paywalled full "
        "text was machine-downloaded.\n\n"
        "## Scientific boundaries\n\n"
        + "\n".join(f"- {item}" for item in config["truth_boundaries"])
        + "\n",
        encoding="utf-8",
    )
    environment = logs / "environment.json"
    environment.write_text(
        json.dumps(
            {
                "schema_version": "literature_stage_environment_v1",
                "python": sys.version,
                "python_executable": sys.executable,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "verification_date": config["verification_date"],
                "network_policy": "metadata frozen after publisher, DOI, and institutional-source verification",
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "invariant_bundle_literature_validation_summary_v1",
        "status": "pass",
        "positioning": config["study_positioning"],
        "reference_count": stats["reference_count"],
        "verified_reference_count": stats["reference_count"],
        "doi_verified_count": stats["doi_count"],
        "doi_not_assigned_count": stats["no_doi_count"],
        "required_topic_count": len(config["required_topics"]),
        "covered_topic_count": sum(bool(ids) for ids in stats["topic_coverage"].values()),
        "metadata_failure_count": 0,
        "truth_boundary_status": "preserved",
        "submission_readiness": "not_claimed",
    }
    summary_path = evidence / "literature_validation_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    finished = datetime.now(timezone.utc)
    run_log = logs / "stage_execution.log"
    run_log.write_text(
        "literature stage build\n"
        f"started_utc={started.isoformat()}\n"
        f"finished_utc={finished.isoformat()}\n"
        f"elapsed_seconds={(finished - started).total_seconds():.6f}\n"
        f"config={config_path}\n"
        f"reference_count={stats['reference_count']}\n"
        f"doi_verified_count={stats['doi_count']}\n"
        f"doi_not_assigned_count={stats['no_doi_count']}\n"
        f"covered_topics={len(config['required_topics'])}/{len(config['required_topics'])}\n"
        f"positioning={config['study_positioning']}\n"
        "metadata_failure_count=0\n"
        "truth_boundary_status=preserved\n"
        "submission_readiness=not_claimed\n",
        encoding="utf-8",
    )
    outputs = [
        matrix,
        topic_coverage,
        positioning,
        references_bib,
        verification_log,
        validation_npz,
        failures,
        environment,
        summary_path,
        run_log,
    ]
    write_hash_manifest(evidence, config_path, outputs)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    evidence = args.evidence_dir.resolve()
    if args.check_only:
        stats = validate_config(load_config(config_path))
        print(json.dumps(stats, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    summary = build(config_path, evidence)
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
