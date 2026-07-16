"""Cross-platform artifact fingerprints with explicit text/binary semantics.

Text files use UTF-8 content with LF-normalized newlines.  Binary and scientific
array artifacts retain exact raw-byte fingerprints.  The compatibility helpers
accept historical raw text hashes recorded from either LF or CRLF worktrees,
while still rejecting every non-newline content change.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


TEXT_SUFFIXES = frozenset(
    {
        ".bib",
        ".csv",
        ".js",
        ".json",
        ".log",
        ".md",
        ".py",
        ".tex",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)

RAW_BYTES = "raw_bytes"
UTF8_LF_NORMALIZED = "utf8_lf_normalized"


@dataclass(frozen=True)
class ArtifactFingerprint:
    """A byte count and SHA-256 digest under a declared hashing mode."""

    hash_mode: str
    bytes: int
    sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def is_utf8_text_path(path: Path) -> bool:
    """Return whether *path* is a repository text type with valid UTF-8 bytes."""

    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def lf_normalized_bytes(data: bytes) -> bytes:
    """Normalize CRLF and lone CR newlines to LF without changing other bytes."""

    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def bytes_for_hash_mode(path: Path, hash_mode: str) -> bytes:
    """Read *path* using an explicit portable fingerprint representation."""

    data = path.read_bytes()
    if hash_mode == RAW_BYTES:
        return data
    if hash_mode == UTF8_LF_NORMALIZED:
        data.decode("utf-8")
        return lf_normalized_bytes(data)
    raise ValueError(f"unknown artifact hash mode: {hash_mode}")


def artifact_fingerprint(path: Path) -> ArtifactFingerprint:
    """Fingerprint text semantically by newlines and binary artifacts exactly."""

    path = Path(path)
    mode = UTF8_LF_NORMALIZED if is_utf8_text_path(path) else RAW_BYTES
    data = bytes_for_hash_mode(path, mode)
    return ArtifactFingerprint(mode, len(data), _sha256(data))


def fingerprint_fields(path: Path) -> dict[str, str | int]:
    """Return manifest-ready fields for a portable artifact fingerprint."""

    fingerprint = artifact_fingerprint(path)
    return {
        "hash_mode": fingerprint.hash_mode,
        "bytes": fingerprint.bytes,
        "sha256": fingerprint.sha256,
    }


def fingerprint_matches(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
    hash_mode: str,
) -> bool:
    """Check a manifest row under its declared fingerprint mode."""

    data = bytes_for_hash_mode(Path(path), hash_mode)
    return len(data) == int(expected_bytes) and _sha256(data) == expected_sha256.upper()


def historical_text_representations(path: Path) -> tuple[bytes, ...]:
    """Return exact, LF, and CRLF forms for a historical UTF-8 text artifact."""

    path = Path(path)
    raw = path.read_bytes()
    if not is_utf8_text_path(path):
        return (raw,)
    lf = lf_normalized_bytes(raw)
    crlf = lf.replace(b"\n", b"\r\n")
    return tuple(dict.fromkeys((raw, lf, crlf)))


def recorded_sha256_matches(path: Path, expected_sha256: str) -> bool:
    """Match a legacy raw hash while ignoring only LF-versus-CRLF differences."""

    expected = expected_sha256.upper()
    return any(_sha256(data) == expected for data in historical_text_representations(path))


def recorded_fingerprint_matches(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
) -> bool:
    """Match a legacy raw size/hash pair across LF and CRLF text worktrees."""

    expected = expected_sha256.upper()
    return any(
        len(data) == int(expected_bytes) and _sha256(data) == expected
        for data in historical_text_representations(path)
    )
