"""Run all figure scripts that are currently implemented."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _paths import PROJECT_ROOT


IMPLEMENTED = [
    PROJECT_ROOT / "figures" / "fig_2_01.py",
    PROJECT_ROOT / "figures" / "fig_2_02.py",
    PROJECT_ROOT / "figures" / "fig_2_03.py",
    PROJECT_ROOT / "figures" / "fig_2_04.py",
    PROJECT_ROOT / "figures" / "fig_2_05.py",
    PROJECT_ROOT / "figures" / "fig_2_06.py",
    PROJECT_ROOT / "figures" / "fig_2_07.py",
    PROJECT_ROOT / "figures" / "fig_2_08.py",
    PROJECT_ROOT / "figures" / "fig_2_09.py",
    PROJECT_ROOT / "figures" / "fig_2_10.py",
    PROJECT_ROOT / "figures" / "fig_2_11.py",
    PROJECT_ROOT / "figures" / "fig_2_12.py",
    PROJECT_ROOT / "figures" / "fig_2_13.py",
    PROJECT_ROOT / "figures" / "fig_2_14.py",
    PROJECT_ROOT / "figures" / "fig_2_15.py",
    PROJECT_ROOT / "figures" / "fig_3_01.py",
    PROJECT_ROOT / "figures" / "fig_3_02.py",
    PROJECT_ROOT / "figures" / "fig_3_03.py",
    PROJECT_ROOT / "figures" / "fig_3_04.py",
    PROJECT_ROOT / "figures" / "fig_3_05.py",
    PROJECT_ROOT / "figures" / "fig_3_06.py",
    PROJECT_ROOT / "figures" / "fig_3_07.py",
    PROJECT_ROOT / "figures" / "fig_3_08.py",
    PROJECT_ROOT / "figures" / "fig_3_09.py",
    PROJECT_ROOT / "figures" / "fig_3_10.py",
    PROJECT_ROOT / "figures" / "fig_3_11.py",
    PROJECT_ROOT / "figures" / "fig_3_12.py",
    PROJECT_ROOT / "figures" / "fig_3_13.py",
    PROJECT_ROOT / "figures" / "fig_3_14.py",
    PROJECT_ROOT / "figures" / "fig_3_15.py",
    PROJECT_ROOT / "figures" / "fig_3_16.py",
    PROJECT_ROOT / "figures" / "fig_3_17.py",
    PROJECT_ROOT / "figures" / "fig_4_01.py",
    PROJECT_ROOT / "figures" / "fig_4_02.py",
    PROJECT_ROOT / "figures" / "fig_4_03.py",
    PROJECT_ROOT / "figures" / "fig_4_04.py",
    PROJECT_ROOT / "figures" / "fig_4_05.py",
    PROJECT_ROOT / "figures" / "fig_4_06.py",
    PROJECT_ROOT / "figures" / "fig_4_07.py",
    PROJECT_ROOT / "figures" / "fig_4_08.py",
    PROJECT_ROOT / "figures" / "fig_5_01.py",
    PROJECT_ROOT / "figures" / "fig_5_02.py",
    PROJECT_ROOT / "figures" / "fig_5_03.py",
    PROJECT_ROOT / "figures" / "fig_5_04.py",
    PROJECT_ROOT / "figures" / "fig_5_05.py",
    PROJECT_ROOT / "figures" / "fig_5_06.py",
    PROJECT_ROOT / "figures" / "fig_5_07.py",
    PROJECT_ROOT / "figures" / "fig_5_08.py",
    PROJECT_ROOT / "figures" / "fig_5_09.py",
    PROJECT_ROOT / "figures" / "fig_5_10.py",
    PROJECT_ROOT / "figures" / "fig_5_11.py",
    PROJECT_ROOT / "figures" / "fig_5_12.py",
    PROJECT_ROOT / "figures" / "fig_5_13.py",
    PROJECT_ROOT / "figures" / "fig_5_14.py",
]


def main() -> None:
    for script in IMPLEMENTED:
        print(f"Running {script.relative_to(PROJECT_ROOT)}")
        subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT, check=True)
    print(f"Generated {len(IMPLEMENTED)} implemented figures")


if __name__ == "__main__":
    main()
