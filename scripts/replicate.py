#!/usr/bin/env python3
"""
One-Shot Replication Script for VC Africa Networks Paper

This script provides full replication of the paper's analysis.

MODES:
1. FULL REPLICATION (if raw data available):
   - Runs complete pipeline from data ingestion to final outputs
   - Requires: data/raw/2019-2025 Africa The Big Deal_Database_*.xlsx

2. DEMONSTRATION (if no raw data):
   - Loads pre-computed outputs/paper_numbers.json
   - Displays all key statistics and generates figures
   - Demonstrates the analysis without proprietary data

Usage:
    python scripts/replicate.py [--full | --demo | --check]

Options:
    --full   Force full pipeline (fails if no raw data)
    --demo   Force demonstration mode (uses pre-computed outputs)
    --check  Just check what mode would run

Data Access:
    Raw data from Africa: The Big Deal (ATBD) is proprietary.
    Purchase access at: https://thebiganddeal.com/database
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS = PROJECT_ROOT / "outputs"
SCRIPTS = PROJECT_ROOT / "scripts"
PAPER_NUMBERS = OUTPUTS / "paper_numbers.json"


def print_header(title: str):
    """Print formatted header."""
    width = 70
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def print_section(title: str):
    """Print section header."""
    print(f"\n--- {title} ---\n")


def check_raw_data() -> bool:
    """Check if raw ATBD data is available."""
    if not DATA_RAW.exists():
        return False

    xlsx_files = list(DATA_RAW.glob("*Africa The Big Deal*.xlsx"))
    return len(xlsx_files) > 0


def check_processed_data() -> bool:
    """Check if processed panel exists."""
    panel_file = DATA_PROCESSED / "vc_year_panel.parquet"
    return panel_file.exists()


def check_paper_numbers() -> bool:
    """Check if pre-computed outputs exist."""
    return PAPER_NUMBERS.exists()


def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    script_path = SCRIPTS / script_name
    print(f"  Running {script_name}... ", end="", flush=True)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print("✗")
            print(f"    Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ (timeout)")
        return False
    except Exception as e:
        print(f"✗ ({e})")
        return False


def run_full_pipeline():
    """Run complete analysis pipeline from raw data."""
    print_header("FULL REPLICATION MODE")
    print("Running complete pipeline from raw ATBD data...")

    steps = [
        ("01_ingest_atbd.py", "Ingest raw data"),
        ("03_build_panel.py", "Build VC-year panel"),
        ("06_run_analysis.py", "Run main analysis"),
        ("generate_paper_tables.py", "Generate tables and paper_numbers.json"),
        ("generate_figure1.py", "Generate figures"),
    ]

    print_section("Pipeline Steps")

    for script, description in steps:
        if not run_script(script, description):
            print(f"\n❌ Pipeline failed at: {script}")
            return False

    print("\n✅ Full pipeline completed successfully!")
    return True


def load_paper_numbers() -> dict:
    """Load pre-computed statistics."""
    with open(PAPER_NUMBERS, 'r') as f:
        return json.load(f)


def display_key_results(numbers: dict):
    """Display key results from paper_numbers.json."""

    print_section("Sample Description")
    sample = numbers['sample']
    print(f"  Total VC-year observations: {sample['n_vc_years']}")
    print(f"  Unique investors: {sample['n_investors']}")
    print(f"  International VCs: {sample['n_international']}")
    print(f"  African VCs: {sample['n_african']}")
    print(f"  Years: {sample['years']}")

    print_section("Descriptive Statistics")
    desc = numbers['descriptives']
    print(f"  HRV Share:     mean = {desc['hrv_share']['mean']:.3f}, SD = {desc['hrv_share']['sd']:.3f}")
    print(f"  Ego Density:   mean = {desc['ego_density']['mean']:.3f}, SD = {desc['ego_density']['sd']:.3f}")
    print(f"    - International: {desc['ego_density_intl']['mean']:.2f} (SD = {desc['ego_density_intl']['sd']:.2f})")
    print(f"    - African:       {desc['ego_density_african']['mean']:.2f} (SD = {desc['ego_density_african']['sd']:.2f})")

    print_section("Main Finding: Split-Sample Analysis")
    ss = numbers['split_sample']
    print("  Effect of network density on high-risk venture investment:")
    print()
    print(f"  International VCs (N={ss['international']['n']}):")
    print(f"    β = {ss['international']['beta']:.3f}, SE = {ss['international']['se']:.3f}, p = {ss['international']['p']:.4f}")
    print(f"    → Dense networks REDUCE HRV investment")
    print()
    print(f"  African VCs (N={ss['african']['n']}):")
    print(f"    β = {ss['african']['beta']:.3f}, SE = {ss['african']['se']:.3f}, p = {ss['african']['p']:.3f}")
    print(f"    → No significant effect")
    print()
    print(f"  Formal Difference Test:")
    print(f"    Δβ = {ss['difference']['beta']:.3f}, z = {ss['difference']['z']:.2f}, p = {ss['difference']['p']:.4f}")
    print(f"    → Statistically significant difference between groups")

    print_section("Marginal Effects (Probability Scale)")
    me = numbers['marginal_effects']
    print("  Moving from low (-1 SD) to high (+1 SD) network density:")
    print()
    print(f"  International VCs: {me['international_low_density']:.1%} → {me['international_high_density']:.1%}")
    print(f"                     ({me['international_change_pp']:+.1f} percentage points)")
    print()
    print(f"  African VCs:       {me['african_low_density']:.1%} → {me['african_high_density']:.1%}")
    print(f"                     ({me['african_change_pp']:+.1f} percentage points)")

    print_section("Robustness Checks")
    rob = numbers['robustness']
    print("  All robustness checks confirm the main finding:")
    print()
    print(f"  Common Support:  z = {rob['common_support']['z']:.2f}, p = {rob['common_support']['p']:.4f}")
    print(f"  Trim 10%:        z = {rob['trim_10pct']['z']:.2f}, p = {rob['trim_10pct']['p']:.4f}")
    print(f"  Weighted by N:   z = {rob['weighted']['z']:.2f}, p = {rob['weighted']['p']:.4f}")


def display_theoretical_interpretation():
    """Display theoretical interpretation of findings."""

    print_section("Theoretical Interpretation")
    print("""
  FINDING: Network density constrains high-risk venture investment,
           but ONLY for international VCs.

  MECHANISM: "Liability of Embeddedness for Outsiders"

  International VCs in dense networks:
    • Lack local knowledge for independent evaluation
    • Face amplified conformity pressure from interconnected partners
    • Result: Follow "safe" consensus bets, avoid HRVs

  African VCs are protected because:
    • Local knowledge enables independent deal assessment
    • Can leverage network trust WITHOUT information disadvantage
    • Result: No density penalty for HRV investment

  IMPLICATION: Network structure effects are contingent on
               investor positioning relative to the market.
    """)


def run_demonstration():
    """Run demonstration mode using pre-computed outputs."""
    print_header("DEMONSTRATION MODE")
    print("Loading pre-computed results from paper_numbers.json...")
    print("(Raw data not available - using archived outputs)")

    if not check_paper_numbers():
        print("\n❌ Error: outputs/paper_numbers.json not found!")
        print("   This file should be included in the repository.")
        return False

    numbers = load_paper_numbers()
    print(f"\nLoaded results generated: {numbers['generated_at']}")

    display_key_results(numbers)
    display_theoretical_interpretation()

    # Check for figures
    print_section("Available Outputs")

    figures = list((OUTPUTS / "figures").glob("*.png")) + list((OUTPUTS / "figures").glob("*.pdf"))
    tables = list((OUTPUTS / "tables").glob("*.tex"))

    print(f"  Figures: {len(figures)} files")
    for f in sorted(figures)[:5]:
        print(f"    - {f.name}")
    if len(figures) > 5:
        print(f"    ... and {len(figures) - 5} more")

    print(f"\n  Tables: {len(tables)} files")
    for t in sorted(tables):
        print(f"    - {t.name}")

    print("\n✅ Demonstration complete!")
    print("\n  To run full replication, obtain raw data from:")
    print("  https://thebigdeal.com/database")
    print("  and place the Excel file in data/raw/")

    return True


def check_mode():
    """Check and report what mode would run."""
    print_header("REPLICATION CHECK")

    has_raw = check_raw_data()
    has_processed = check_processed_data()
    has_outputs = check_paper_numbers()

    print("\nData availability:")
    print(f"  Raw ATBD data:      {'✓ Available' if has_raw else '✗ Not found'}")
    print(f"  Processed panel:    {'✓ Available' if has_processed else '✗ Not found'}")
    print(f"  Pre-computed outputs: {'✓ Available' if has_outputs else '✗ Not found'}")

    print("\nDefault mode:")
    if has_raw:
        print("  → FULL REPLICATION (raw data detected)")
    elif has_outputs:
        print("  → DEMONSTRATION (using pre-computed outputs)")
    else:
        print("  → ERROR (no data or outputs available)")

    return has_raw or has_outputs


def main():
    parser = argparse.ArgumentParser(
        description="One-shot replication script for VC Africa Networks paper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/replicate.py          # Auto-detect mode
  python scripts/replicate.py --full   # Force full pipeline
  python scripts/replicate.py --demo   # Force demonstration
  python scripts/replicate.py --check  # Check what would run
        """
    )
    parser.add_argument('--full', action='store_true', help='Force full replication mode')
    parser.add_argument('--demo', action='store_true', help='Force demonstration mode')
    parser.add_argument('--check', action='store_true', help='Check mode without running')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" VC SYNDICATION NETWORKS AND HIGH-RISK VENTURE INVESTMENT IN AFRICA")
    print(" Replication Script")
    print("=" * 70)
    print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Project:   {PROJECT_ROOT}")

    # Check mode only
    if args.check:
        success = check_mode()
        return 0 if success else 1

    # Determine mode
    if args.full:
        if not check_raw_data():
            print("\n❌ Error: --full specified but no raw data found!")
            print("   Place ATBD Excel file in data/raw/")
            return 1
        success = run_full_pipeline()
    elif args.demo:
        success = run_demonstration()
    else:
        # Auto-detect
        if check_raw_data():
            success = run_full_pipeline()
        elif check_paper_numbers():
            success = run_demonstration()
        else:
            print("\n❌ Error: No data or pre-computed outputs found!")
            print("   Either:")
            print("   1. Place ATBD data in data/raw/, or")
            print("   2. Ensure outputs/paper_numbers.json exists")
            return 1

    print("\n" + "=" * 70)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
