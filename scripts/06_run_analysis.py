#!/usr/bin/env python3
"""
Main Analysis Script

Runs all regression models and generates outputs:
- Main models (M1-M4)
- Robustness checks (R1, R2, R5, R7, R15)
- Tables (LaTeX)
- Figures
- Summary report
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from src.config import (
    PROCESSED_DATA_DIR, INTERIM_DATA_DIR,
    TABLES_DIR, FIGURES_DIR, REPORTS_DIR, LOGS_DIR
)
from src.analysis.main_models import (
    prepare_analysis_sample,
    run_main_models,
    generate_latex_table,
    print_model_summary,
    format_results_table
)
from src.analysis.robustness import (
    run_all_robustness,
    format_robustness_summary,
    print_robustness_summary
)
from src.analysis.visualizations import (
    plot_interaction_effect,
    plot_variable_distributions,
    plot_coefficient_comparison
)

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def generate_analysis_report(
    sample: pd.DataFrame,
    main_models: dict,
    robustness_models: dict,
    output_path: Path
):
    """Generate markdown analysis summary report."""

    # Get key statistics
    m4 = main_models['M4_interaction']
    int_coef = m4.params['density_x_diversity_std']
    int_se = m4.bse['density_x_diversity_std']
    int_pval = m4.pvalues['density_x_diversity_std']

    # Determine significance
    if int_pval < 0.001:
        sig_level = "p < 0.001"
        sig_stars = "***"
    elif int_pval < 0.01:
        sig_level = "p < 0.01"
        sig_stars = "**"
    elif int_pval < 0.05:
        sig_level = "p < 0.05"
        sig_stars = "*"
    elif int_pval < 0.10:
        sig_level = "p < 0.10"
        sig_stars = "†"
    else:
        sig_level = f"p = {int_pval:.3f}"
        sig_stars = ""

    # Robustness summary
    rob_df = format_robustness_summary(m4, robustness_models)
    n_sig = rob_df['significant'].sum()
    n_pos = rob_df['positive'].sum()
    n_total = len(rob_df)

    report = f"""# VC Networks Analysis: Summary Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Sample

| Metric | Value |
|--------|-------|
| VC-year observations | {len(sample)} |
| Unique VCs | {sample['investor_id'].nunique()} |
| Years | {sorted(sample['year'].unique())} |
| Mean HRV share | {sample['hrv_share'].mean()*100:.1f}% |

## Key Result: Density × Diversity Interaction

**Coefficient: {int_coef:.4f}{sig_stars} ({sig_level})**

Standard Error: {int_se:.4f}

### Interpretation

"""

    if int_coef > 0 and int_pval < 0.05:
        report += """The interaction between network density and diversity is **positive and statistically significant**.

This supports our core hypothesis: **dense, diverse networks provide both trust infrastructure AND heterogeneous information**, enabling VCs to take on higher-risk ventures.

- In high-diversity networks, greater density amplifies information flow from diverse partners
- In low-diversity networks, density may reinforce echo chambers and herding behavior
"""
    elif int_coef > 0 and int_pval < 0.10:
        report += """The interaction is **positive but only marginally significant** (p < 0.10).

Directionally consistent with the hypothesis, but requires caution in interpretation.
"""
    elif int_coef > 0:
        report += """The interaction is **positive but not statistically significant**.

While directionally consistent with the hypothesis, we cannot rule out that this pattern occurred by chance.
"""
    else:
        report += """The interaction is **negative**, contrary to our hypothesis.

This suggests that dense networks may NOT amplify the benefits of diversity, or that other mechanisms dominate.
"""

    report += f"""

## Robustness Summary

| Check | Significant (p<0.05) | Positive |
|-------|---------------------|----------|
"""

    for _, row in rob_df.iterrows():
        sig_mark = "✅" if row['significant'] else "❌"
        pos_mark = "✅" if row['positive'] else "❌"
        report += f"| {row['model']} | {sig_mark} | {pos_mark} |\n"

    report += f"""
**Overall: {n_sig}/{n_total} specifications significant, {n_pos}/{n_total} positive**

"""

    if n_sig >= n_total * 0.8:
        report += "✅ **ROBUST**: Interaction holds across specifications\n"
    elif n_sig >= n_total * 0.5:
        report += "⚠️ **PARTIALLY ROBUST**: Some specifications lose significance\n"
    else:
        report += "❌ **NOT ROBUST**: Interaction fails in most specifications\n"

    report += """

## Model Specifications

### Main Models

1. **Model 1**: HRV ~ density + controls
2. **Model 2**: HRV ~ diversity + controls
3. **Model 3**: HRV ~ density + diversity + controls
4. **Model 4**: HRV ~ density + diversity + density×diversity + controls

Controls: log(ego size), log(experience), year FE

Standard errors clustered by VC.

### Robustness Checks

- **R1**: Alternative DV — early-stage share (regardless of sector)
- **R2**: Alternative DV — hard-tech share (regardless of stage)
- **R5**: Weighted density (repeated co-investments)
- **R7**: Exclude deals with inferred stages
- **R15**: Stable coverage regime only (2023-2024)

## Output Files

- `outputs/tables/main_results.tex` - LaTeX regression table
- `outputs/tables/robustness_summary.csv` - Robustness comparison
- `outputs/figures/interaction_plot.png` - Marginal effects visualization
- `outputs/figures/distributions.png` - Variable distributions
- `outputs/figures/robustness_forest.png` - Coefficient comparison

"""

    with open(output_path, 'w') as f:
        f.write(report)

    logger.info(f"Report saved to {output_path}")


def main():
    """Main analysis pipeline."""
    logger.info("="*60)
    logger.info("MAIN ANALYSIS PIPELINE")
    logger.info("="*60)

    # Create output directories
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading data...")
    panel = pd.read_parquet(PROCESSED_DATA_DIR / 'vc_year_panel.parquet')
    deals = pd.read_parquet(PROCESSED_DATA_DIR / 'deals_with_hrv.parquet')
    deal_investors = pd.read_parquet(INTERIM_DATA_DIR / 'deal_investors.parquet')

    # Prepare analysis sample
    logger.info("Preparing analysis sample...")
    sample = prepare_analysis_sample(panel)
    logger.info(f"Analysis sample: {len(sample)} observations")

    # Run main models
    logger.info("\n--- MAIN MODELS ---")
    main_models = run_main_models(sample)
    print_model_summary(main_models)

    # Generate LaTeX table
    generate_latex_table(main_models, TABLES_DIR / 'main_results.tex')

    # Save results table
    results_df = format_results_table(main_models)
    results_df.to_csv(TABLES_DIR / 'main_results.csv', index=False)

    # Run robustness checks
    logger.info("\n--- ROBUSTNESS CHECKS ---")
    robustness_models = run_all_robustness(
        sample, panel, deals, deal_investors
    )
    print_robustness_summary(main_models['M4_interaction'], robustness_models)

    # Save robustness summary
    rob_summary = format_robustness_summary(
        main_models['M4_interaction'], robustness_models
    )
    rob_summary.to_csv(TABLES_DIR / 'robustness_summary.csv', index=False)

    # Generate figures
    logger.info("\n--- GENERATING FIGURES ---")

    try:
        plot_interaction_effect(
            sample,
            main_models['M4_interaction'],
            FIGURES_DIR / 'interaction_plot.png'
        )
    except Exception as e:
        logger.warning(f"Failed to generate interaction plot: {e}")

    try:
        plot_variable_distributions(
            sample,
            FIGURES_DIR / 'distributions.png'
        )
    except Exception as e:
        logger.warning(f"Failed to generate distribution plot: {e}")

    try:
        plot_coefficient_comparison(
            main_models['M4_interaction'],
            robustness_models,
            FIGURES_DIR / 'robustness_forest.png'
        )
    except Exception as e:
        logger.warning(f"Failed to generate forest plot: {e}")

    # Generate report
    logger.info("\n--- GENERATING REPORT ---")
    generate_analysis_report(
        sample,
        main_models,
        robustness_models,
        REPORTS_DIR / 'analysis_summary.md'
    )

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*60)

    # Print key result
    m4 = main_models['M4_interaction']
    int_coef = m4.params['density_x_diversity_std']
    int_pval = m4.pvalues['density_x_diversity_std']

    print("\n" + "="*60)
    print("KEY RESULT: Density × Diversity Interaction")
    print("="*60)
    print(f"Coefficient: {int_coef:.4f}")
    print(f"P-value: {int_pval:.4f}")

    if int_coef > 0 and int_pval < 0.05:
        print("\n✅ HYPOTHESIS SUPPORTED")
        print("Dense, diverse networks enable high-risk venture investment.")
    elif int_coef > 0 and int_pval < 0.10:
        print("\n⚠️ MARGINAL SUPPORT")
        print("Positive interaction, but only marginally significant.")
    else:
        print("\n❌ HYPOTHESIS NOT SUPPORTED")

    print("\n" + "="*60)

    return main_models, robustness_models


if __name__ == '__main__':
    main()
