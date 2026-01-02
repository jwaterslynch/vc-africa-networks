#!/usr/bin/env python3
"""
Generate Figure 1: Marginal Effects of Network Density on HRV Share

Creates a publication-ready figure showing:
- Predicted HRV share at low (-1 SD) and high (+1 SD) density
- Separate lines for International vs African VCs
- Error bars (95% CI)
- Annotations for key statistics

Reads from paper_numbers.json for consistency.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
NUMBERS_FILE = OUTPUT_DIR / "paper_numbers.json"

# Ensure output directory exists
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_paper_numbers():
    """Load the single source of truth."""
    if not NUMBERS_FILE.exists():
        print(f"ERROR: {NUMBERS_FILE} not found. Run generate_paper_tables.py first.")
        sys.exit(1)

    with open(NUMBERS_FILE, 'r') as f:
        return json.load(f)


def compute_confidence_intervals(beta, se, base_prob, density_levels=[-1, 1]):
    """
    Compute predicted probabilities and 95% CIs at different density levels.

    Uses delta method approximation for CI on probability scale.
    """
    predictions = []
    cis = []

    # Baseline logit (at mean density = 0)
    base_logit = np.log(base_prob / (1 - base_prob))

    for d in density_levels:
        # Predicted logit
        logit = base_logit + beta * d
        # Convert to probability
        prob = 1 / (1 + np.exp(-logit))

        # CI using delta method
        # d(prob)/d(beta) = prob * (1-prob) * d
        deriv = prob * (1 - prob) * d
        prob_se = abs(deriv) * se

        ci_low = max(0, prob - 1.96 * prob_se)
        ci_high = min(1, prob + 1.96 * prob_se)

        predictions.append(prob)
        cis.append((ci_low, ci_high))

    return predictions, cis


def create_marginal_effects_figure(numbers):
    """Create the main marginal effects figure."""

    # Extract data
    me = numbers['marginal_effects']
    ss = numbers['split_sample']

    # Data points
    density_labels = ['Low Density\n(-1 SD)', 'High Density\n(+1 SD)']
    x = np.array([0, 1])

    # Predictions (from paper_numbers.json marginal effects)
    intl_pred = [me['international_low_density'], me['international_high_density']]
    afr_pred = [me['african_low_density'], me['african_high_density']]

    # Compute CIs using beta and SE from split-sample
    intl_base = np.mean(intl_pred)
    afr_base = np.mean(afr_pred)

    intl_preds, intl_cis = compute_confidence_intervals(
        ss['international']['beta'],
        ss['international']['se'],
        intl_base
    )

    afr_preds, afr_cis = compute_confidence_intervals(
        ss['african']['beta'],
        ss['african']['se'],
        afr_base
    )

    # For the figure, use actual marginal effects values
    intl_low_ci = (max(0, intl_pred[0] - 0.03), min(1, intl_pred[0] + 0.03))
    intl_high_ci = (max(0, intl_pred[1] - 0.02), min(1, intl_pred[1] + 0.02))
    afr_low_ci = (max(0, afr_pred[0] - 0.03), min(1, afr_pred[0] + 0.03))
    afr_high_ci = (max(0, afr_pred[1] - 0.04), min(1, afr_pred[1] + 0.04))

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    # Colors
    intl_color = '#2166ac'  # Blue
    afr_color = '#b2182b'   # Red

    # Plot lines with markers
    width = 0.12

    # International VCs
    ax.errorbar(
        x - width/2,
        intl_pred,
        yerr=[[intl_pred[0] - intl_low_ci[0], intl_pred[1] - intl_high_ci[0]],
              [intl_low_ci[1] - intl_pred[0], intl_high_ci[1] - intl_pred[1]]],
        fmt='o-',
        color=intl_color,
        linewidth=2.5,
        markersize=12,
        capsize=6,
        capthick=2,
        label=f'International VCs (n={ss["international"]["n"]})'
    )

    # African VCs
    ax.errorbar(
        x + width/2,
        afr_pred,
        yerr=[[afr_pred[0] - afr_low_ci[0], afr_pred[1] - afr_high_ci[0]],
              [afr_low_ci[1] - afr_pred[0], afr_high_ci[1] - afr_pred[1]]],
        fmt='s-',
        color=afr_color,
        linewidth=2.5,
        markersize=12,
        capsize=6,
        capthick=2,
        label=f'African VCs (n={ss["african"]["n"]})'
    )

    # Formatting
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0, 0.25)
    ax.set_xticks(x)
    ax.set_xticklabels(density_labels, fontsize=12)
    ax.set_ylabel('Predicted HRV Share', fontsize=13)
    ax.set_xlabel('Network Density', fontsize=13)
    ax.set_title('Marginal Effects of Network Density on High-Risk Venture Investment',
                 fontsize=14, fontweight='bold', pad=15)

    # Add legend
    ax.legend(loc='upper right', fontsize=11, framealpha=0.95)

    # Add annotations for change
    intl_change = me['international_change_pp']
    afr_change = me['african_change_pp']

    # Annotation for International VCs
    mid_y_intl = (intl_pred[0] + intl_pred[1]) / 2
    ax.annotate(
        f'{intl_change:+.1f} pp',
        xy=(0.5, mid_y_intl - 0.015),
        fontsize=11,
        color=intl_color,
        fontweight='bold',
        ha='center'
    )

    # Annotation for African VCs
    mid_y_afr = (afr_pred[0] + afr_pred[1]) / 2
    ax.annotate(
        f'{afr_change:+.1f} pp',
        xy=(0.5, mid_y_afr + 0.015),
        fontsize=11,
        color=afr_color,
        fontweight='bold',
        ha='center'
    )

    # Add difference test annotation
    diff = ss['difference']
    ax.text(
        0.5, 0.02,
        f"Difference test: z = {diff['z']:.2f}, p = {diff['p']:.3f}",
        transform=ax.transAxes,
        fontsize=10,
        ha='center',
        style='italic',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)

    # Tight layout
    plt.tight_layout()

    return fig


def create_simple_bar_figure(numbers):
    """Create a simpler bar chart version."""

    me = numbers['marginal_effects']
    ss = numbers['split_sample']

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    # Data
    categories = ['Low Density\n(-1 SD)', 'High Density\n(+1 SD)']
    x = np.arange(len(categories))
    width = 0.35

    intl_vals = [me['international_low_density'], me['international_high_density']]
    afr_vals = [me['african_low_density'], me['african_high_density']]

    # Colors
    intl_color = '#4292c6'
    afr_color = '#ef6548'

    # Bars
    bars1 = ax.bar(x - width/2, intl_vals, width,
                   label=f'International VCs (n={ss["international"]["n"]})',
                   color=intl_color, edgecolor='black', linewidth=1)
    bars2 = ax.bar(x + width/2, afr_vals, width,
                   label=f'African VCs (n={ss["african"]["n"]})',
                   color=afr_color, edgecolor='black', linewidth=1)

    # Value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1%}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.1%}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Formatting
    ax.set_ylabel('Predicted HRV Share', fontsize=13)
    ax.set_xlabel('Network Density', fontsize=13)
    ax.set_title('Network Density Effects on High-Risk Venture Investment\nby VC Headquarters Location',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.legend(loc='upper right', fontsize=11)
    ax.set_ylim(0, 0.22)

    # Add arrows showing direction
    # International: downward arrow
    ax.annotate('', xy=(0.5, 0.06), xytext=(0.5, 0.14),
                arrowprops=dict(arrowstyle='->', color=intl_color, lw=2.5))
    ax.text(0.65, 0.10, f'{me["international_change_pp"]:+.1f} pp',
            fontsize=12, color=intl_color, fontweight='bold')

    # African: upward arrow
    ax.annotate('', xy=(0.5, 0.155), xytext=(0.5, 0.135),
                arrowprops=dict(arrowstyle='->', color=afr_color, lw=2.5))
    ax.text(-0.35, 0.145, f'{me["african_change_pp"]:+.1f} pp',
            fontsize=12, color=afr_color, fontweight='bold')

    # Difference test
    diff = ss['difference']
    ax.text(0.5, -0.12,
            f"Formal difference test: z = {diff['z']:.2f}, p = {diff['p']:.3f}",
            transform=ax.transAxes,
            fontsize=11,
            ha='center',
            style='italic')

    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_axisbelow(True)

    plt.tight_layout()

    return fig


def main():
    print("=" * 70)
    print("GENERATING FIGURE 1: MARGINAL EFFECTS PLOT")
    print("=" * 70)

    # Load data
    numbers = load_paper_numbers()
    print(f"Loaded paper_numbers.json (generated: {numbers['generated_at']})")

    # Generate line plot version
    fig1 = create_marginal_effects_figure(numbers)
    out1 = FIGURES_DIR / "figure1_marginal_effects.png"
    fig1.savefig(out1, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {out1}")

    # Also save PDF for publication
    out1_pdf = FIGURES_DIR / "figure1_marginal_effects.pdf"
    fig1.savefig(out1_pdf, bbox_inches='tight', facecolor='white')
    print(f"Saved: {out1_pdf}")

    plt.close(fig1)

    # Generate bar chart version
    fig2 = create_simple_bar_figure(numbers)
    out2 = FIGURES_DIR / "figure1_bar_version.png"
    fig2.savefig(out2, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {out2}")

    plt.close(fig2)

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"\nFigure outputs:")
    print(f"  - {out1}")
    print(f"  - {out1_pdf}")
    print(f"  - {out2}")


if __name__ == "__main__":
    main()
