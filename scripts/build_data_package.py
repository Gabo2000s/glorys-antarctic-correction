"""Assemble the data package for the Zenodo dataset record.

    python scripts/build_data_package.py [--out dist/zenodo-data]

The package contains:

* ``ctd/``        the six Sea-Bird .cnv files, byte for byte as in data/raw
* ``glorys/``     the six GLORYS12V1 station extracts, byte for byte
* ``corrected/``  the corrected profiles, byte for byte as in results/profiles
* ``stations.csv`` station metadata (dates, positions, cast and water depths)
* ``README.md``   dataset description (copied from data/DATASET_README.md)
* ``MD5SUMS.txt`` and ``SHA256SUMS.txt``

and a zip of the same folder. Files are copied, never rewritten. The script
refuses to build if any raw file differs from data/SHA256SUMS.txt.

Requires only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW_CHECKSUMS = ROOT / "data" / "SHA256SUMS.txt"
PROFILES = ROOT / "results" / "profiles"


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def version() -> str:
    """Version from CITATION.cff."""
    m = re.search(r"^version:\s*(\S+)", (ROOT / "CITATION.cff").read_text(encoding="utf-8"),
                  re.MULTILINE)
    return m.group(1).strip("'\"") if m else "unknown"


def verify_raw() -> None:
    """Check data/raw against data/SHA256SUMS.txt before packaging."""
    bad = []
    for line in RAW_CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel = line.split(maxsplit=1)
        if digest(ROOT / "data" / rel.strip(), "sha256") != expected:
            bad.append(rel)
    if bad:
        sys.exit("Raw files differ from data/SHA256SUMS.txt (line endings "
                 "changed by git?):\n  " + "\n  ".join(bad))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=ROOT / "dist" / "zenodo-data")
    args = ap.parse_args(argv)

    verify_raw()
    profiles = sorted(PROFILES.glob("*_corrected_profile.csv"))
    if len(profiles) != 6:
        sys.exit(f"Expected 6 corrected profiles in {PROFILES}, found {len(profiles)}")

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    for sub in ("ctd", "glorys", "corrected"):
        (out / sub).mkdir(parents=True)

    for src in sorted((RAW / "ctd").glob("*.cnv")):
        shutil.copy2(src, out / "ctd" / src.name)
    for src in sorted((RAW / "glorys").glob("*.csv")):
        shutil.copy2(src, out / "glorys" / src.name)
    for src in profiles:
        shutil.copy2(src, out / "corrected" / src.name)
    shutil.copy2(ROOT / "data" / "stations.csv", out / "stations.csv")
    shutil.copy2(ROOT / "data" / "DATASET_README.md", out / "README.md")

    files = sorted(p for p in out.rglob("*") if p.is_file())
    for algo, name in (("md5", "MD5SUMS.txt"), ("sha256", "SHA256SUMS.txt")):
        lines = [f"{digest(p, algo)}  {p.relative_to(out).as_posix()}" for p in files]
        (out / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    zip_base = out.parent / f"marguerite-bay-ctd-glorys-v{version()}"
    archive = shutil.make_archive(str(zip_base), "zip", root_dir=out)
    print(f"Data package: {out}")
    print(f"Zip archive : {archive}  (md5 {digest(Path(archive), 'md5')})")
    print(f"{len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
