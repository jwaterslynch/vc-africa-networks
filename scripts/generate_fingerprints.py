#!/usr/bin/env python3
"""
Generate Data and Output Fingerprints for Reproducibility

Creates:
1. data/DATA_FINGERPRINTS.json - Raw data file hashes for verification
2. outputs/OUTPUT_FINGERPRINTS.json - Output file hashes for verification

These allow:
- Replicators with licensed data to verify they have the same version
- Anyone to verify outputs match what the code produced
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def get_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_git_status() -> str:
    """Check if working directory is clean."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            return "clean" if not result.stdout.strip() else "modified"
        return "unknown"
    except Exception:
        return "unknown"


def get_package_versions() -> dict:
    """Get versions of key packages."""
    versions = {"python": platform.python_version()}

    packages = [
        'pandas', 'numpy', 'statsmodels', 'networkx',
        'scipy', 'matplotlib', 'seaborn'
    ]

    for pkg in packages:
        try:
            module = __import__(pkg)
            versions[pkg] = getattr(module, '__version__', 'unknown')
        except ImportError:
            versions[pkg] = 'not installed'

    return versions


def find_raw_data_file():
    """Find the ATBD raw data file."""
    if not RAW_DIR.exists():
        return None

    patterns = [
        "*Africa*Big*Deal*.xlsx",
        "*ATBD*.xlsx",
        "atbd_*.xlsx"
    ]

    for pattern in patterns:
        files = list(RAW_DIR.glob(pattern))
        if files:
            return files[0]

    # Check for any xlsx
    xlsx_files = list(RAW_DIR.glob("*.xlsx"))
    if xlsx_files:
        return xlsx_files[0]

    return None


def generate_data_fingerprints() -> dict:
    """Generate fingerprints for raw data files."""
    print("\n--- Generating Data Fingerprints ---")

    fingerprints = {
        "generated_at": datetime.now().isoformat(),
        "git_commit": get_git_commit(),
        "git_status": get_git_status(),
        "environment": get_package_versions(),
        "raw_data": None,
        "processed_data": []
    }

    # Raw data file
    raw_file = find_raw_data_file()
    if raw_file:
        print(f"  Found raw data: {raw_file.name}")
        fingerprints["raw_data"] = {
            "filename": raw_file.name,
            "expected_pattern": "*Africa*Big*Deal*.xlsx",
            "size_bytes": raw_file.stat().st_size,
            "sha256": get_file_hash(raw_file),
            "modified": datetime.fromtimestamp(raw_file.stat().st_mtime).isoformat(),
            "source": "Africa: The Big Deal (https://thebigdeal.com/database)",
            "license": "Individual License - redistribution prohibited"
        }
    else:
        print("  No raw data file found (expected in data/raw/)")
        fingerprints["raw_data"] = {
            "filename": None,
            "expected_pattern": "*Africa*Big*Deal*.xlsx",
            "note": "Raw data not present - obtain from https://thebigdeal.com/database"
        }

    # Processed data files (for verification, not redistribution)
    processed_dir = DATA_DIR / "processed"
    if processed_dir.exists():
        for pfile in sorted(processed_dir.glob("*.parquet")):
            fingerprints["processed_data"].append({
                "filename": pfile.name,
                "size_bytes": pfile.stat().st_size,
                "sha256": get_file_hash(pfile)
            })
            print(f"  Processed: {pfile.name}")

    # Save
    output_path = DATA_DIR / "DATA_FINGERPRINTS.json"
    with open(output_path, 'w') as f:
        json.dump(fingerprints, f, indent=2)

    print(f"\n  Saved: {output_path}")
    return fingerprints


def generate_output_fingerprints() -> dict:
    """Generate fingerprints for all publication outputs."""
    print("\n--- Generating Output Fingerprints ---")

    fingerprints = {
        "generated_at": datetime.now().isoformat(),
        "git_commit": get_git_commit(),
        "tables": [],
        "figures": [],
        "paper_numbers": None
    }

    # Tables
    tables_dir = OUTPUTS_DIR / "tables"
    if tables_dir.exists():
        for tfile in sorted(tables_dir.glob("*.tex")) + sorted(tables_dir.glob("*.csv")):
            fingerprints["tables"].append({
                "filename": tfile.name,
                "size_bytes": tfile.stat().st_size,
                "sha256": get_file_hash(tfile)
            })
            print(f"  Table: {tfile.name}")

    # Figures
    figures_dir = OUTPUTS_DIR / "figures"
    if figures_dir.exists():
        for ffile in sorted(figures_dir.glob("*.png")) + sorted(figures_dir.glob("*.pdf")):
            fingerprints["figures"].append({
                "filename": ffile.name,
                "size_bytes": ffile.stat().st_size,
                "sha256": get_file_hash(ffile)
            })
            print(f"  Figure: {ffile.name}")

    # Paper numbers (single source of truth)
    paper_numbers = OUTPUTS_DIR / "paper_numbers.json"
    if paper_numbers.exists():
        fingerprints["paper_numbers"] = {
            "filename": "paper_numbers.json",
            "size_bytes": paper_numbers.stat().st_size,
            "sha256": get_file_hash(paper_numbers)
        }
        print(f"  Paper numbers: paper_numbers.json")

    # Save
    output_path = OUTPUTS_DIR / "OUTPUT_FINGERPRINTS.json"
    with open(output_path, 'w') as f:
        json.dump(fingerprints, f, indent=2)

    print(f"\n  Saved: {output_path}")
    return fingerprints


def verify_outputs() -> bool:
    """Verify current outputs match stored fingerprints."""
    print("\n--- Verifying Output Fingerprints ---")

    fingerprint_path = OUTPUTS_DIR / "OUTPUT_FINGERPRINTS.json"
    if not fingerprint_path.exists():
        print("  ❌ No OUTPUT_FINGERPRINTS.json found. Run --generate first.")
        return False

    with open(fingerprint_path) as f:
        stored = json.load(f)

    all_match = True
    checked = 0

    # Check tables
    tables_dir = OUTPUTS_DIR / "tables"
    for item in stored.get("tables", []):
        fpath = tables_dir / item["filename"]
        if fpath.exists():
            current_hash = get_file_hash(fpath)
            if current_hash == item["sha256"]:
                print(f"  ✓ {item['filename']}")
            else:
                print(f"  ✗ {item['filename']} - HASH MISMATCH")
                all_match = False
            checked += 1
        else:
            print(f"  ✗ {item['filename']} - FILE MISSING")
            all_match = False

    # Check figures
    figures_dir = OUTPUTS_DIR / "figures"
    for item in stored.get("figures", []):
        fpath = figures_dir / item["filename"]
        if fpath.exists():
            current_hash = get_file_hash(fpath)
            if current_hash == item["sha256"]:
                print(f"  ✓ {item['filename']}")
            else:
                print(f"  ✗ {item['filename']} - HASH MISMATCH")
                all_match = False
            checked += 1
        else:
            print(f"  ✗ {item['filename']} - FILE MISSING")
            all_match = False

    # Check paper numbers
    if stored.get("paper_numbers"):
        pn_path = OUTPUTS_DIR / "paper_numbers.json"
        if pn_path.exists():
            current_hash = get_file_hash(pn_path)
            if current_hash == stored["paper_numbers"]["sha256"]:
                print(f"  ✓ paper_numbers.json")
            else:
                print(f"  ✗ paper_numbers.json - HASH MISMATCH")
                all_match = False
            checked += 1

    print(f"\n  Checked {checked} files")
    if all_match:
        print("  ✅ All outputs match stored fingerprints")
    else:
        print("  ❌ Some outputs have changed or are missing")

    return all_match


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate or verify reproducibility fingerprints"
    )
    parser.add_argument(
        '--generate', '-g', action='store_true',
        help='Generate new fingerprints for data and outputs'
    )
    parser.add_argument(
        '--verify', '-v', action='store_true',
        help='Verify current outputs match stored fingerprints'
    )
    parser.add_argument(
        '--data-only', action='store_true',
        help='Only generate/check data fingerprints'
    )
    parser.add_argument(
        '--outputs-only', action='store_true',
        help='Only generate/check output fingerprints'
    )

    args = parser.parse_args()

    # Default to generate if no args
    if not args.generate and not args.verify:
        args.generate = True

    print("=" * 70)
    print(" REPRODUCIBILITY FINGERPRINT GENERATOR")
    print("=" * 70)

    if args.verify:
        success = verify_outputs()
        sys.exit(0 if success else 1)

    if args.generate:
        if not args.outputs_only:
            generate_data_fingerprints()
        if not args.data_only:
            generate_output_fingerprints()

        print("\n" + "=" * 70)
        print(" FINGERPRINTS GENERATED SUCCESSFULLY")
        print("=" * 70)


if __name__ == "__main__":
    main()
