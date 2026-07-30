"""PyInstaller build helper for ExcelIntel.

Usage:
    python scripts/build.py
    python scripts/build.py --onefile
    python scripts/build.py --debug
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(onefile: bool = False, debug: bool = False) -> int:
    entry = ROOT / "run.py"
    dist = ROOT / "dist"
    build_dir = ROOT / "build"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "ExcelIntel",
        "--windowed",
        "--distpath", str(dist),
        "--workpath", str(build_dir),
        "--specpath", str(build_dir),
    ]
    if onefile:
        args.append("--onefile")
    if debug:
        args += ["--debug", "all"]
    # Hidden imports for optional Excel engines
    for h in ("pyxlsb", "xlrd", "openpyxl", "polars", "duckdb", "rapidfuzz"):
        args += ["--hidden-import", h]
    args.append(str(entry))
    print(">>", " ".join(args))
    return subprocess.call(args, cwd=ROOT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--onefile", action="store_true")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    sys.exit(build(a.onefile, a.debug))
