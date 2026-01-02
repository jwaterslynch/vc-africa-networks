#!/usr/bin/env python3
"""
Check Manuscript Consistency

Compares numbers in the manuscript against paper_numbers.json.
Generates an audit report flagging any discrepancies.

Usage:
    python check_manuscript_consistency.py <manuscript_path>
    python check_manuscript_consistency.py  # uses default path

Output:
    outputs/final_checks/consistency_audit.md
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
NUMBERS_FILE = OUTPUT_DIR / "paper_numbers.json"
AUDIT_DIR = OUTPUT_DIR / "final_checks"

# Default manuscript path
DEFAULT_MANUSCRIPT = PROJECT_ROOT / "paper" / "manuscript.md"

# Ensure output directory exists
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def load_paper_numbers() -> dict:
    """Load the single source of truth."""
    if not NUMBERS_FILE.exists():
        print(f"ERROR: {NUMBERS_FILE} not found. Run generate_paper_tables.py first.")
        sys.exit(1)

    with open(NUMBERS_FILE, 'r') as f:
        return json.load(f)


def load_manuscript(path: Path) -> str:
    """Load manuscript text."""
    if not path.exists():
        print(f"WARNING: Manuscript not found at {path}")
        return ""

    with open(path, 'r') as f:
        return f.read()


def extract_numbers_from_text(text: str) -> List[Tuple[str, str, int]]:
    """
    Extract all numbers from text with context.

    Returns list of (context, number_str, line_number)
    """
    results = []
    lines = text.split('\n')

    for i, line in enumerate(lines, 1):
        # Skip code blocks and tables
        if line.strip().startswith('```') or line.strip().startswith('|'):
            continue

        # Find numbers in various formats
        patterns = [
            # Integers: N=901, n=606
            r'[Nn]\s*=\s*(\d+)',
            # Percentages: 12.2%, 0.122
            r'(\d+\.?\d*)\s*%',
            r'(\d+\.\d{2,3})\s*(?:percent|pp)',
            # Coefficients: β=-0.55, β = -0.549
            r'[βb]\s*=?\s*(-?\d+\.?\d*)',
            # P-values: p=0.002, p < 0.001
            r'[Pp]\s*[=<>]\s*(\d+\.?\d*)',
            # Z-scores: z=2.88, z = 2.88
            r'[Zz]\s*=\s*(-?\d+\.?\d*)',
            # Standard errors: SE=0.17, (0.17)
            r'SE\s*=\s*(\d+\.?\d*)',
            r'\((\d+\.\d{2,3})\)',  # (0.17) format
            # Generic decimals with context
            r'(\d+\.\d{1,4})',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                context = line[max(0, match.start()-30):min(len(line), match.end()+30)]
                results.append((context.strip(), match.group(1), i))

    return results


def check_specific_values(text: str, numbers: dict) -> List[dict]:
    """
    Check specific key values that should appear in manuscript.

    Returns list of check results.
    """
    checks = []

    # Sample sizes
    sample_checks = [
        ('n_vc_years', r'(?:N|n|sample)\s*(?:=|of)?\s*(\d+).*(?:VC|investor|observation)',
         numbers['sample']['n_vc_years'], 'Total sample size'),
        ('n_international', r'(?:international|non-?African)\s*(?:VCs?|investors?).*?(\d+)',
         numbers['sample']['n_international'], 'International VC count'),
        ('n_african', r'(?:African|local)\s*(?:VCs?|investors?).*?(\d+)',
         numbers['sample']['n_african'], 'African VC count'),
    ]

    for key, pattern, expected, desc in sample_checks:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found = None
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            try:
                val = int(m)
                if val == expected:
                    found = val
                    break
            except:
                continue

        checks.append({
            'category': 'Sample Size',
            'key': key,
            'description': desc,
            'expected': expected,
            'found': found,
            'status': 'OK' if found == expected else ('MISSING' if found is None else 'MISMATCH')
        })

    # Key coefficients - split sample
    ss = numbers['split_sample']
    coef_checks = [
        ('intl_beta', ss['international']['beta'], 'International density β'),
        ('intl_p', ss['international']['p'], 'International density p-value'),
        ('african_beta', ss['african']['beta'], 'African density β'),
        ('african_p', ss['african']['p'], 'African density p-value'),
        ('diff_z', ss['difference']['z'], 'Difference test z-score'),
        ('diff_p', ss['difference']['p'], 'Difference test p-value'),
    ]

    for key, expected, desc in coef_checks:
        # Look for the value with some tolerance
        found = None
        tolerance = 0.01 if abs(expected) < 1 else 0.1

        # Search for exact or close matches
        pattern = r'-?\d+\.\d{1,4}'
        matches = re.findall(pattern, text)
        for m in matches:
            try:
                val = float(m)
                if abs(val - expected) < tolerance:
                    found = val
                    break
            except:
                continue

        checks.append({
            'category': 'Coefficient',
            'key': key,
            'description': desc,
            'expected': expected,
            'found': found,
            'status': 'OK' if found is not None else 'MISSING'
        })

    # Marginal effects
    me = numbers['marginal_effects']
    me_checks = [
        ('intl_change_pp', me['international_change_pp'], 'International density effect (pp)'),
        ('african_change_pp', me['african_change_pp'], 'African density effect (pp)'),
    ]

    for key, expected, desc in me_checks:
        found = None
        # Look for percentage point changes
        patterns = [
            rf'{abs(expected):.1f}\s*(?:percentage\s*points|pp)',
            rf'(?:decrease|increase|change).*?{abs(expected):.1f}',
        ]
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found = expected
                break

        checks.append({
            'category': 'Marginal Effect',
            'key': key,
            'description': desc,
            'expected': expected,
            'found': found,
            'status': 'OK' if found is not None else 'MISSING'
        })

    return checks


def check_table_consistency(text: str, numbers: dict) -> List[dict]:
    """Check if any tables in the text match expected values."""
    checks = []

    # Look for table-like structures
    table_pattern = r'\|[^\n]+\|'
    tables = re.findall(table_pattern, text)

    if tables:
        checks.append({
            'category': 'Tables',
            'key': 'tables_found',
            'description': 'Tables found in manuscript',
            'expected': 'Present',
            'found': f'{len(tables)} table rows',
            'status': 'INFO'
        })

    return checks


def generate_audit_report(checks: List[dict], manuscript_path: Path, numbers: dict) -> str:
    """Generate markdown audit report."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count results
    ok_count = sum(1 for c in checks if c['status'] == 'OK')
    missing_count = sum(1 for c in checks if c['status'] == 'MISSING')
    mismatch_count = sum(1 for c in checks if c['status'] == 'MISMATCH')
    info_count = sum(1 for c in checks if c['status'] == 'INFO')

    report = f"""# Manuscript Consistency Audit Report

**Generated:** {timestamp}
**Manuscript:** {manuscript_path}
**Source of Truth:** paper_numbers.json (generated {numbers['generated_at']})

---

## Summary

| Status | Count |
|--------|-------|
| ✅ OK | {ok_count} |
| ⚠️ MISSING | {missing_count} |
| ❌ MISMATCH | {mismatch_count} |
| ℹ️ INFO | {info_count} |
| **Total** | **{len(checks)}** |

---

## Detailed Results

"""

    # Group by category
    categories = {}
    for check in checks:
        cat = check['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(check)

    for category, cat_checks in categories.items():
        report += f"### {category}\n\n"
        report += "| Description | Expected | Found | Status |\n"
        report += "|-------------|----------|-------|--------|\n"

        for check in cat_checks:
            status_icon = {
                'OK': '✅',
                'MISSING': '⚠️',
                'MISMATCH': '❌',
                'INFO': 'ℹ️'
            }.get(check['status'], '?')

            expected = check['expected']
            if isinstance(expected, float):
                expected = f"{expected:.3f}" if abs(expected) < 10 else f"{expected:.1f}"

            found = check['found']
            if found is None:
                found = "Not found"
            elif isinstance(found, float):
                found = f"{found:.3f}" if abs(found) < 10 else f"{found:.1f}"

            report += f"| {check['description']} | {expected} | {found} | {status_icon} {check['status']} |\n"

        report += "\n"

    # Add key numbers reference
    report += """---

## Key Numbers Reference

These are the authoritative values from `paper_numbers.json`:

### Sample
"""
    for key, val in numbers['sample'].items():
        if key != 'years':
            report += f"- **{key}**: {val}\n"
    report += f"- **years**: {numbers['sample']['years']}\n"

    report += """
### Split-Sample Results
"""
    ss = numbers['split_sample']
    report += f"- **International VCs**: β = {ss['international']['beta']:.3f}, SE = {ss['international']['se']:.3f}, p = {ss['international']['p']:.4f}\n"
    report += f"- **African VCs**: β = {ss['african']['beta']:.3f}, SE = {ss['african']['se']:.3f}, p = {ss['african']['p']:.3f}\n"
    report += f"- **Difference**: z = {ss['difference']['z']:.2f}, p = {ss['difference']['p']:.4f}\n"

    report += """
### Marginal Effects
"""
    me = numbers['marginal_effects']
    report += f"- **International**: {me['international_low_density']:.1%} → {me['international_high_density']:.1%} ({me['international_change_pp']:+.1f} pp)\n"
    report += f"- **African**: {me['african_low_density']:.1%} → {me['african_high_density']:.1%} ({me['african_change_pp']:+.1f} pp)\n"

    report += """
---

## Recommendations

"""
    if missing_count > 0:
        report += f"⚠️ **{missing_count} values not found** - Consider adding these to the manuscript or verify they are correctly formatted.\n\n"

    if mismatch_count > 0:
        report += f"❌ **{mismatch_count} mismatches detected** - Update these values in the manuscript to match paper_numbers.json.\n\n"

    if ok_count == len(checks) - info_count:
        report += "✅ **All checked values are consistent!**\n"

    return report


def main():
    print("=" * 70)
    print("MANUSCRIPT CONSISTENCY CHECKER")
    print("=" * 70)

    # Get manuscript path
    if len(sys.argv) > 1:
        manuscript_path = Path(sys.argv[1])
    else:
        manuscript_path = DEFAULT_MANUSCRIPT

    print(f"Manuscript: {manuscript_path}")

    # Load data
    numbers = load_paper_numbers()
    print(f"Loaded paper_numbers.json (generated: {numbers['generated_at']})")

    # Load manuscript
    manuscript_text = load_manuscript(manuscript_path)

    if not manuscript_text:
        print("\nNo manuscript found. Creating template audit report...")
        # Create a report showing what values SHOULD be in the manuscript
        checks = []
        # Add all expected values as "not found" since no manuscript exists
        ss = numbers['split_sample']
        me = numbers['marginal_effects']

        template_checks = [
            ('Sample Size', 'n_total', 'Total sample size', numbers['sample']['n_vc_years']),
            ('Sample Size', 'n_intl', 'International VCs', numbers['sample']['n_international']),
            ('Sample Size', 'n_african', 'African VCs', numbers['sample']['n_african']),
            ('Coefficient', 'intl_beta', 'International density β', ss['international']['beta']),
            ('Coefficient', 'intl_p', 'International density p', ss['international']['p']),
            ('Coefficient', 'african_beta', 'African density β', ss['african']['beta']),
            ('Coefficient', 'african_p', 'African density p', ss['african']['p']),
            ('Coefficient', 'diff_z', 'Difference z-score', ss['difference']['z']),
            ('Coefficient', 'diff_p', 'Difference p-value', ss['difference']['p']),
            ('Marginal Effect', 'intl_change', 'International change (pp)', me['international_change_pp']),
            ('Marginal Effect', 'african_change', 'African change (pp)', me['african_change_pp']),
        ]

        for cat, key, desc, expected in template_checks:
            checks.append({
                'category': cat,
                'key': key,
                'description': desc,
                'expected': expected,
                'found': None,
                'status': 'MISSING'
            })
    else:
        print(f"Manuscript loaded: {len(manuscript_text)} characters")

        # Run checks
        checks = check_specific_values(manuscript_text, numbers)
        checks.extend(check_table_consistency(manuscript_text, numbers))

    # Generate report
    report = generate_audit_report(checks, manuscript_path, numbers)

    # Save report
    audit_file = AUDIT_DIR / "consistency_audit.md"
    with open(audit_file, 'w') as f:
        f.write(report)

    print(f"\nAudit report saved: {audit_file}")

    # Print summary
    ok_count = sum(1 for c in checks if c['status'] == 'OK')
    missing_count = sum(1 for c in checks if c['status'] == 'MISSING')
    mismatch_count = sum(1 for c in checks if c['status'] == 'MISMATCH')

    print(f"\nSummary:")
    print(f"  ✅ OK: {ok_count}")
    print(f"  ⚠️ MISSING: {missing_count}")
    print(f"  ❌ MISMATCH: {mismatch_count}")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)

    # Return exit code based on findings
    if mismatch_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
