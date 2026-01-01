"""
Robustness Checks

Priority robustness tests:
R1: Alternative DV — hrv_share_early_only (early-stage regardless of sector)
R2: Alternative DV — hrv_share_hardtech_only (hard-tech regardless of stage)
R5: Weighted density (ego_density_weighted)
R7: Exclude inferred stages (stage_inferred == 0 only)
R15: Stable coverage regime only (deals from 2021+ threshold)
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Dict, List
import logging

from src.analysis.main_models import (
    prepare_analysis_sample,
    run_fractional_logit,
    extract_model_stats,
    print_model_summary
)

logger = logging.getLogger(__name__)


def run_robustness_r1_early_only(sample: pd.DataFrame) -> sm.GEE:
    """
    R1: Alternative DV — early-stage share regardless of sector.

    Tests whether results hold when looking at propensity to invest
    early-stage generally, not just hard-tech.
    """
    logger.info("R1: Early-stage DV (regardless of sector)")

    # DV = proportion of early-stage deals
    controls = ['log_ego_size', 'log_experience']

    return run_fractional_logit(
        sample, 'hrv_share_early_only',
        ['density_std', 'diversity_std', 'density_x_diversity_std'] + controls
    )


def run_robustness_r2_hardtech_only(sample: pd.DataFrame) -> sm.GEE:
    """
    R2: Alternative DV — hard-tech share regardless of stage.

    Tests whether results hold when looking at hard-tech selection
    regardless of stage.
    """
    logger.info("R2: Hard-tech DV (regardless of stage)")

    controls = ['log_ego_size', 'log_experience']

    return run_fractional_logit(
        sample, 'hrv_share_hardtech_only',
        ['density_std', 'diversity_std', 'density_x_diversity_std'] + controls
    )


def run_robustness_r5_weighted_density(sample: pd.DataFrame) -> sm.GEE:
    """
    R5: Weighted density (repeated co-investments).

    Uses ego_density_weighted which counts repeat ties.
    """
    logger.info("R5: Weighted density")

    # Create standardized weighted density
    sample = sample.copy()
    sample['density_weighted_std'] = (
        sample['ego_density_weighted'] - sample['ego_density_weighted'].mean()
    ) / sample['ego_density_weighted'].std()

    # Interaction with diversity
    sample['density_w_x_diversity_std'] = (
        sample['density_weighted_std'] * sample['diversity_std']
    )

    controls = ['log_ego_size', 'log_experience']

    return run_fractional_logit(
        sample, 'hrv_share',
        ['density_weighted_std', 'diversity_std', 'density_w_x_diversity_std'] + controls
    )


def run_robustness_r7_no_inferred(
    panel: pd.DataFrame,
    deals: pd.DataFrame,
    deal_investors: pd.DataFrame
) -> sm.GEE:
    """
    R7: Exclude deals with inferred stages.

    Recalculates HRV share using only deals where stage was explicit,
    not inferred from amount.
    """
    logger.info("R7: Exclude inferred stages")

    # Filter deals to non-inferred only
    deals_explicit = deals[deals['stage_inferred'] == 0].copy()

    # Recalculate HRV share for each VC-year
    sample = panel[panel['n_deals'] > 0].copy()

    for idx, row in sample.iterrows():
        vc_id = row['investor_id']
        year = row['year']

        # Get VC's deals in year with explicit stages only
        vc_deal_ids = deal_investors[
            deal_investors['investor_id'] == vc_id
        ]['deal_id'].unique()

        year_deals = deals_explicit[
            (deals_explicit['deal_id'].isin(vc_deal_ids)) &
            (deals_explicit['deal_year'] == year)
        ]

        if len(year_deals) > 0:
            hrv_count = year_deals['hrv_primary'].sum()
            sample.loc[idx, 'hrv_share_explicit'] = hrv_count / len(year_deals)
            sample.loc[idx, 'n_deals_explicit'] = len(year_deals)
        else:
            sample.loc[idx, 'hrv_share_explicit'] = np.nan
            sample.loc[idx, 'n_deals_explicit'] = 0

    # Filter to obs with valid explicit HRV
    sample = sample[sample['n_deals_explicit'] > 0].copy()

    # Prepare sample
    sample = prepare_analysis_sample(sample)

    controls = ['log_ego_size', 'log_experience']

    return run_fractional_logit(
        sample, 'hrv_share_explicit',
        ['density_std', 'diversity_std', 'density_x_diversity_std'] + controls
    )


def run_robustness_r15_stable_regime(sample: pd.DataFrame) -> sm.GEE:
    """
    R15: Stable coverage regime only.

    Restricts to years where network window uses only 2021+
    deals (stable $100K+ coverage threshold).

    For 2024: window is 2021-2023 (all stable)
    For 2023: window is 2020-2022 (2020 has different threshold)
    For 2022: window is 2019-2021 (2019-2020 have different thresholds)

    So only 2024 has a fully stable window. We relax to include
    2023 and 2024 where majority of window is stable.
    """
    logger.info("R15: Stable coverage regime (2023-2024 only)")

    # Keep only 2023 and 2024
    sample = sample[sample['year'].isin([2023, 2024])].copy()

    if len(sample) == 0:
        logger.warning("No observations in stable regime sample")
        return None

    controls = ['log_ego_size', 'log_experience']

    return run_fractional_logit(
        sample, 'hrv_share',
        ['density_std', 'diversity_std', 'density_x_diversity_std'] + controls
    )


def run_all_robustness(
    sample: pd.DataFrame,
    panel: pd.DataFrame = None,
    deals: pd.DataFrame = None,
    deal_investors: pd.DataFrame = None
) -> Dict[str, sm.GEE]:
    """
    Run all priority robustness checks.

    Parameters
    ----------
    sample : DataFrame
        Prepared analysis sample
    panel : DataFrame
        Full panel (for R7)
    deals : DataFrame
        Deals with HRV flags (for R7)
    deal_investors : DataFrame
        Junction table (for R7)

    Returns
    -------
    Dict of fitted models
    """
    logger.info("Running robustness checks...")

    results = {}

    # R1: Early-stage DV
    try:
        results['R1_early_only'] = run_robustness_r1_early_only(sample)
    except Exception as e:
        logger.warning(f"R1 failed: {e}")

    # R2: Hard-tech DV
    try:
        results['R2_hardtech_only'] = run_robustness_r2_hardtech_only(sample)
    except Exception as e:
        logger.warning(f"R2 failed: {e}")

    # R5: Weighted density
    try:
        results['R5_weighted_density'] = run_robustness_r5_weighted_density(sample)
    except Exception as e:
        logger.warning(f"R5 failed: {e}")

    # R7: No inferred stages
    if panel is not None and deals is not None and deal_investors is not None:
        try:
            results['R7_no_inferred'] = run_robustness_r7_no_inferred(
                panel, deals, deal_investors
            )
        except Exception as e:
            logger.warning(f"R7 failed: {e}")

    # R15: Stable regime
    try:
        results['R15_stable_regime'] = run_robustness_r15_stable_regime(sample)
    except Exception as e:
        logger.warning(f"R15 failed: {e}")

    return results


def format_robustness_summary(
    main_model: sm.GEE,
    robustness_models: Dict[str, sm.GEE]
) -> pd.DataFrame:
    """
    Create summary table comparing interaction term across models.
    """
    rows = []

    # Main model
    if 'density_x_diversity_std' in main_model.params.index:
        coef = main_model.params['density_x_diversity_std']
        se = main_model.bse['density_x_diversity_std']
        pval = main_model.pvalues['density_x_diversity_std']

        rows.append({
            'model': 'Main (M4)',
            'interaction_coef': coef,
            'interaction_se': se,
            'interaction_pval': pval,
            'n_obs': int(main_model.nobs),
            'significant': pval < 0.05,
            'positive': coef > 0
        })

    # Robustness models
    for name, model in robustness_models.items():
        if model is None:
            continue

        # Find interaction term (may have different name)
        int_vars = [v for v in model.params.index if 'x_diversity' in v.lower()]

        if int_vars:
            var = int_vars[0]
            coef = model.params[var]
            se = model.bse[var]
            pval = model.pvalues[var]

            rows.append({
                'model': name,
                'interaction_coef': coef,
                'interaction_se': se,
                'interaction_pval': pval,
                'n_obs': int(model.nobs),
                'significant': pval < 0.05,
                'positive': coef > 0
            })

    return pd.DataFrame(rows)


def print_robustness_summary(
    main_model: sm.GEE,
    robustness_models: Dict[str, sm.GEE]
):
    """Print formatted robustness summary."""
    print("\n" + "="*80)
    print("ROBUSTNESS CHECK SUMMARY: Interaction Term (Density × Diversity)")
    print("="*80)

    df = format_robustness_summary(main_model, robustness_models)

    print(f"\n{'Model':<25} {'Coef':>10} {'SE':>10} {'p-value':>10} {'N':>8} {'Result':>15}")
    print("-" * 80)

    for _, row in df.iterrows():
        if row['significant'] and row['positive']:
            result = "✅ Significant+"
        elif row['positive']:
            result = "⚠️ Positive NS"
        else:
            result = "❌ Negative"

        print(f"{row['model']:<25} {row['interaction_coef']:>10.4f} {row['interaction_se']:>10.4f} "
              f"{row['interaction_pval']:>10.4f} {row['n_obs']:>8} {result:>15}")

    # Overall assessment
    n_significant = df['significant'].sum()
    n_positive = df['positive'].sum()
    n_total = len(df)

    print("\n" + "-" * 80)
    print(f"Significant positive: {n_significant}/{n_total}")
    print(f"Positive (any significance): {n_positive}/{n_total}")

    if n_significant >= n_total * 0.8:
        print("\n✅ ROBUST: Interaction holds across specifications")
    elif n_significant >= n_total * 0.5:
        print("\n⚠️ PARTIALLY ROBUST: Some specifications lose significance")
    else:
        print("\n❌ NOT ROBUST: Interaction fails in most specifications")
