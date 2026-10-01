"""Compare the outputs of two runs of the correction.

    python scripts/compare_implementations.py outputs/matlab outputs/python
    python scripts/compare_implementations.py outputs/matlab results

Compares ``metrics.csv`` (every metric of every station), every column of the
six ``profiles/*.csv`` files (including the positions of missing values) and
``summary.txt``, and prints the largest difference per quantity. Exits with
status 1 if any difference exceeds the tolerances.

Requires only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


def read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def as_float(s: str) -> float:
    return float("nan") if s.strip().lower() in ("", "nan") else float(s)


def max_diff(a, b):
    """Largest |a - b|; inf if missing values are not in the same places."""
    worst = 0.0
    for x, y in zip(a, b):
        if math.isnan(x) or math.isnan(y):
            if math.isnan(x) != math.isnan(y):
                return math.inf
            continue
        worst = max(worst, abs(x - y))
    return worst


def compare_table(path_a: Path, path_b: Path, key_cols: int):
    head_a, rows_a = read_csv(path_a)
    head_b, rows_b = read_csv(path_b)
    if head_a != head_b:
        raise SystemExit(f"Different columns in {path_a.name}:\n  {head_a}\n  {head_b}")
    if len(rows_a) != len(rows_b):
        raise SystemExit(f"Different number of rows in {path_a.name}")
    if [r[:key_cols] for r in rows_a] != [r[:key_cols] for r in rows_b]:
        raise SystemExit(f"Different row labels in {path_a.name}")
    return {col: max_diff([as_float(r[j]) for r in rows_a],
                          [as_float(r[j]) for r in rows_b])
            for j, col in enumerate(head_a) if j >= key_cols}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("a", type=Path, help="first output folder")
    ap.add_argument("b", type=Path, help="second output folder")
    ap.add_argument("--atol-metrics", type=float, default=1e-6)
    ap.add_argument("--atol-profiles", type=float, default=2e-6,
                    help="profiles are written with 6 decimals")
    args = ap.parse_args(argv)

    failed = False
    print(f"A: {args.a}\nB: {args.b}\n")

    diffs = compare_table(args.a / "metrics.csv", args.b / "metrics.csv", key_cols=1)
    worst = max(diffs.values())
    ok = worst <= args.atol_metrics
    failed |= not ok
    print(f"{'PASS' if ok else 'FAIL'}  metrics.csv            max |A - B| = {worst:.3e}")
    for col, d in diffs.items():
        if d > args.atol_metrics:
            print(f"        {col}: {d:.3e}")

    files = sorted(p.name for p in (args.a / "profiles").glob("*.csv"))
    if files != sorted(p.name for p in (args.b / "profiles").glob("*.csv")):
        raise SystemExit("The two folders contain different profile files")
    per_col: dict[str, float] = {}
    for name in files:
        for col, d in compare_table(args.a / "profiles" / name,
                                    args.b / "profiles" / name, key_cols=0).items():
            per_col[col] = max(per_col.get(col, 0.0), d)
    worst = max(per_col.values())
    ok = worst <= args.atol_profiles
    failed |= not ok
    print(f"{'PASS' if ok else 'FAIL'}  profiles/ ({len(files)} files)  max |A - B| = {worst:.3e}")
    for col, d in per_col.items():
        flag = "  <-- exceeds tolerance" if d > args.atol_profiles else ""
        print(f"        {col:26s} {d:.3e}{flag}")

    same = ((args.a / "summary.txt").read_text(encoding="utf-8")
            == (args.b / "summary.txt").read_text(encoding="utf-8"))
    print(f"{'PASS' if same else 'DIFF'}  summary.txt            "
          f"{'identical' if same else 'differs (rounding of the last digit?)'}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
