"""Cross-platform contracts for text, binary, and legacy artifact hashes."""

from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from qp_orbits.artifact_fingerprints import (
    RAW_BYTES,
    UTF8_LF_NORMALIZED,
    artifact_fingerprint,
    fingerprint_matches,
    recorded_fingerprint_matches,
    recorded_sha256_matches,
)


class ArtifactFingerprintTests(unittest.TestCase):
    def test_lf_and_crlf_text_have_one_normalized_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lf = Path(directory) / "lf.csv"
            crlf = Path(directory) / "crlf.csv"
            lf.write_bytes(b"a,b\n1,2\n")
            crlf.write_bytes(b"a,b\r\n1,2\r\n")

            left = artifact_fingerprint(lf)
            right = artifact_fingerprint(crlf)

        self.assertEqual(left.hash_mode, UTF8_LF_NORMALIZED)
        self.assertEqual(left, right)

    def test_real_text_content_change_changes_normalized_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            first.write_bytes(b'{"status":"fail"}\n')
            second.write_bytes(b'{"status":"pass"}\r\n')

            left = artifact_fingerprint(first)
            right = artifact_fingerprint(second)

        self.assertNotEqual(left.sha256, right.sha256)

    def test_utf8_bom_change_is_not_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plain = Path(directory) / "plain.txt"
            bom = Path(directory) / "bom.txt"
            plain.write_bytes("boundary\n".encode("utf-8"))
            bom.write_bytes("\ufeffboundary\r\n".encode("utf-8"))

            left = artifact_fingerprint(plain)
            right = artifact_fingerprint(bom)

        self.assertNotEqual(left.sha256, right.sha256)

    def test_binary_scientific_artifact_uses_exact_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.npz"
            data = b"PK\x03\x04\r\nscientific\x00payload"
            path.write_bytes(data)
            fingerprint = artifact_fingerprint(path)

        self.assertEqual(fingerprint.hash_mode, RAW_BYTES)
        self.assertEqual(fingerprint.bytes, len(data))
        self.assertEqual(
            fingerprint.sha256,
            hashlib.sha256(data).hexdigest().upper(),
        )

    def test_legacy_raw_text_hash_accepts_only_newline_variants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.csv"
            lf = b"gate,status\nholdout,fail\n"
            crlf = lf.replace(b"\n", b"\r\n")
            path.write_bytes(lf)
            expected = hashlib.sha256(crlf).hexdigest().upper()

            self.assertTrue(recorded_sha256_matches(path, expected))
            self.assertTrue(
                recorded_fingerprint_matches(
                    path,
                    expected_bytes=len(crlf),
                    expected_sha256=expected,
                )
            )
            path.write_bytes(b"gate,status\nholdout,pass\n")
            self.assertFalse(recorded_sha256_matches(path, expected))

    def test_declared_manifest_mode_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.md"
            path.write_bytes(b"line one\r\nline two\r\n")
            fingerprint = artifact_fingerprint(path)

            self.assertTrue(
                fingerprint_matches(
                    path,
                    expected_bytes=fingerprint.bytes,
                    expected_sha256=fingerprint.sha256,
                    hash_mode=fingerprint.hash_mode,
                )
            )
            self.assertFalse(
                fingerprint_matches(
                    path,
                    expected_bytes=fingerprint.bytes,
                    expected_sha256="0" * 64,
                    hash_mode=fingerprint.hash_mode,
                )
            )


if __name__ == "__main__":
    unittest.main()
