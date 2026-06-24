"""Fetch the JPL DE421 SPK kernel used by Figures 5.6-5.7."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import urlopen

from _paths import PROJECT_ROOT


URL = "https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp"
EXPECTED_SIZE = 16_788_480
EXPECTED_SHA256 = "a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> Path:
    destination = PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != EXPECTED_SIZE or file_sha256(destination) != EXPECTED_SHA256:
            raise RuntimeError(f"existing DE421 kernel failed integrity checks: {destination}")
        print(f"Verified {destination}")
        return destination

    temporary = destination.with_suffix(".bsp.part")
    try:
        with urlopen(URL, timeout=60) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if temporary.stat().st_size != EXPECTED_SIZE or file_sha256(temporary) != EXPECTED_SHA256:
            raise RuntimeError("downloaded DE421 kernel failed integrity checks")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"Downloaded and verified {destination}")
    return destination


if __name__ == "__main__":
    main()
