#!/usr/bin/env python3
"""
Exploratory Analysis Script

Decompose and explore the diversity/density effects to understand
where the action actually is.

Analyses:
1. Diversity decomposition (type vs geo vs international)
2. Heterogeneity by focal investor type (African vs International HQ)
3. Nonlinearity in density (quadratic, terciles)
4. Alternative interactions
5. Temporal dynamics
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import Logit
import matplotlib.pyplot as plt
import seaborn as sns

from src.config import (
    PROCESSED_DATA_DIR, INTERIM_DATA_DIR, LOGS_DIR
)
from src.analysis.main_models import prepare_analysis_sample

# Setup
EXPLORATORY_DIR = PROJECT_ROOT / 'outputs' / 'exploratory'
EXPLORATORY_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR = EXPLORATORY_DIR / 'key_plots'
PLOTS_DIR.mkdir(exist_ok=True)

LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'exploratory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_gee_model(sample, y_var, x_vars, cluster_var='investor_id'):
    """Run GEE fractional logit and return results dict."""
    # Add year dummies
    years = sorted(sample['year'].unique())
    year_dummies = [f'year_{y}' for y in years[1:]]
    all_vars = x_vars + year_dummies

    y = sample[y_var].values
    X = sample[all_vars].copy()
    X = sm.add_constant(X)

    valid_mask = ~(X.isna().any(axis=1) | np.isnan(y))
    y = y[valid_mask]
    X = X[valid_mask]
    groups = sample.loc[valid_mask, cluster_var].values

    model = sm.GEE(
        y, X,
        groups=groups,
        family=Binomial(link=Logit()),
        cov_struct=sm.cov_struct.Exchangeable()
    )

    result = model.fit()

    # Extract key stats
    stats = {
        'n_obs': int(result.nobs),
        'n_clusters': len(np.unique(groups))
    }

    for var in result.params.index:
        if var == 'const':
            continue
        stats[f'{var}_coef'] = result.params[var]
        stats[f'{var}_se'] = result.bse[var]
        stats[f'{var}_pval'] = result.pvalues[var]

    return result, stats


def print_model_result(name, result, key_vars):
    """Print formatted model result."""
    print(f"\n{name}")
    print(f"  N = {int(result.nobs)}")
    for var in key_vars:
        if var in result.params.index:
            coef = result.params[var]
            se = result.bse[var]
            pval = result.pvalues[var]
            stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '†' if pval < 0.10 else ''
            flag = " ⬅️ NOTABLE" if pval < 0.10 else ""
            print(f"    {var:30s}: {coef:8.4f} ({se:.4f}) {stars}{flag}")


# =============================================================================
# 1. DIVERSITY DECOMPOSITION
# =============================================================================

def run_diversity_decomposition(sample):
    """Decompose diversity effect into components."""
    logger.info("="*60)
    logger.info("1. DIVERSITY DECOMPOSITION")
    logger.info("="*60)

    results = []
    controls = ['log_ego_size', 'log_experience']

    # Standardize diversity components
    sample = sample.copy()

    # Z-score individual components
    for col in ['diversity_type', 'diversity_geo', 'pct_international', 'pct_local', 'pct_regional']:
        if col in sample.columns:
            valid = sample[col].dropna()
            if len(valid) > 1 and valid.std() > 0:
                sample[f'{col}_std'] = (sample[col] - valid.mean()) / valid.std()
            else:
                sample[f'{col}_std'] = sample[col]

    # Model 5a: Type diversity only
    print("\n--- Model 5a: Type Diversity ---")
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['diversity_type_std', 'density_std'] + controls
        )
        stats['model'] = '5a_type_only'
        results.append(stats)
        print_model_result("5a: Type Diversity + Density", res,
                          ['diversity_type_std', 'density_std'])
    except Exception as e:
        logger.warning(f"5a failed: {e}")

    # Model 5b: Geographic diversity only
    print("\n--- Model 5b: Geographic Diversity ---")
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['diversity_geo_std', 'density_std'] + controls
        )
        stats['model'] = '5b_geo_only'
        results.append(stats)
        print_model_result("5b: Geo Diversity + Density", res,
                          ['diversity_geo_std', 'density_std'])
    except Exception as e:
        logger.warning(f"5b failed: {e}")

    # Model 5c: Both diversity components
    print("\n--- Model 5c: Both Diversity Components ---")
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['diversity_type_std', 'diversity_geo_std', 'density_std'] + controls
        )
        stats['model'] = '5c_both_components'
        results.append(stats)
        print_model_result("5c: Type + Geo Diversity + Density", res,
                          ['diversity_type_std', 'diversity_geo_std', 'density_std'])
    except Exception as e:
        logger.warning(f"5c failed: {e}")

    # Model 5d: International partner share
    print("\n--- Model 5d: International Partner Share ---")
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['pct_international_std', 'density_std'] + controls
        )
        stats['model'] = '5d_pct_international'
        results.append(stats)
        print_model_result("5d: % International + Density", res,
                          ['pct_international_std', 'density_std'])
    except Exception as e:
        logger.warning(f"5d failed: {e}")

    # Model 5e: All geographic components
    print("\n--- Model 5e: All Geographic Components ---")
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['pct_local_std', 'pct_regional_std', 'pct_international_std', 'density_std'] + controls
        )
        stats['model'] = '5e_all_geo_components'
        results.append(stats)
        print_model_result("5e: Local + Regional + Intl + Density", res,
                          ['pct_local_std', 'pct_regional_std', 'pct_international_std', 'density_std'])
    except Exception as e:
        logger.warning(f"5e failed: {e}")

    df = pd.DataFrame(results)
    df.to_csv(EXPLORATORY_DIR / 'decomposition_results.csv', index=False)

    return df, sample


# =============================================================================
# 2. HETEROGENEITY BY FOCAL INVESTOR TYPE
# =============================================================================

def run_heterogeneity_analysis(sample):
    """Test if effects differ by focal investor type."""
    logger.info("="*60)
    logger.info("2. HETEROGENEITY BY FOCAL INVESTOR TYPE")
    logger.info("="*60)

    results = []
    controls = ['log_ego_size', 'log_experience']

    # Create focal investor type indicator
    sample = sample.copy()
    sample['focal_is_african'] = (sample['hq_in_africa'] == 1).astype(int)
    sample['focal_is_international'] = (sample['hq_in_africa'] == 0).astype(int)

    print(f"\nSample split:")
    print(f"  African HQ VCs: {sample['focal_is_african'].sum()} obs")
    print(f"  International HQ VCs: {sample['focal_is_international'].sum()} obs")

    # Model 6a: African HQ VCs only
    print("\n--- Model 6a: African HQ VCs Only ---")
    try:
        african_sample = sample[sample['focal_is_african'] == 1]
        res, stats = run_gee_model(
            african_sample, 'hrv_share',
            ['density_std', 'diversity_std'] + controls
        )
        stats['model'] = '6a_african_only'
        stats['subsample'] = 'African HQ'
        results.append(stats)
        print_model_result("6a: African HQ VCs", res, ['density_std', 'diversity_std'])
    except Exception as e:
        logger.warning(f"6a failed: {e}")

    # Model 6b: International HQ VCs only
    print("\n--- Model 6b: International HQ VCs Only ---")
    try:
        intl_sample = sample[sample['focal_is_international'] == 1]
        res, stats = run_gee_model(
            intl_sample, 'hrv_share',
            ['density_std', 'diversity_std'] + controls
        )
        stats['model'] = '6b_international_only'
        stats['subsample'] = 'International HQ'
        results.append(stats)
        print_model_result("6b: International HQ VCs", res, ['density_std', 'diversity_std'])
    except Exception as e:
        logger.warning(f"6b failed: {e}")

    # Model 6c: Interaction model
    print("\n--- Model 6c: Interaction with Focal Type ---")
    try:
        # Create interactions
        sample['density_x_african'] = sample['density_std'] * sample['focal_is_african']
        sample['diversity_x_african'] = sample['diversity_std'] * sample['focal_is_african']

        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'diversity_std', 'focal_is_african',
             'density_x_african', 'diversity_x_african'] + controls
        )
        stats['model'] = '6c_interaction'
        results.append(stats)
        print_model_result("6c: Focal Type Interactions", res,
                          ['density_std', 'diversity_std', 'focal_is_african',
                           'density_x_african', 'diversity_x_african'])
    except Exception as e:
        logger.warning(f"6c failed: {e}")

    df = pd.DataFrame(results)
    df.to_csv(EXPLORATORY_DIR / 'heterogeneity_results.csv', index=False)

    return df, sample


# =============================================================================
# 3. NONLINEARITY IN DENSITY
# =============================================================================

def run_nonlinearity_analysis(sample):
    """Test for nonlinear density effects."""
    logger.info("="*60)
    logger.info("3. NONLINEARITY IN DENSITY")
    logger.info("="*60)

    results = []
    controls = ['log_ego_size', 'log_experience']

    sample = sample.copy()

    # Model 7a: Quadratic density
    print("\n--- Model 7a: Quadratic Density ---")
    sample['density_std_sq'] = sample['density_std'] ** 2
    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'density_std_sq', 'diversity_std'] + controls
        )
        stats['model'] = '7a_quadratic'
        results.append(stats)
        print_model_result("7a: Density + Density² + Diversity", res,
                          ['density_std', 'density_std_sq', 'diversity_std'])

        # Check for inverted-U
        if 'density_std_coef' in stats and 'density_std_sq_coef' in stats:
            b1 = stats['density_std_coef']
            b2 = stats['density_std_sq_coef']
            if b2 < 0 and b1 > 0:
                turning_point = -b1 / (2 * b2)
                print(f"\n  📊 Inverted-U detected! Turning point at density_std = {turning_point:.2f}")
            elif b2 > 0 and b1 < 0:
                print(f"\n  📊 U-shaped relationship detected")
    except Exception as e:
        logger.warning(f"7a failed: {e}")

    # Model 7b: Density terciles
    print("\n--- Model 7b: Density Terciles ---")
    sample['density_tercile'] = pd.qcut(
        sample['ego_density'],
        q=3,
        labels=['Low', 'Medium', 'High'],
        duplicates='drop'
    )
    sample['density_medium'] = (sample['density_tercile'] == 'Medium').astype(int)
    sample['density_high'] = (sample['density_tercile'] == 'High').astype(int)

    try:
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_medium', 'density_high', 'diversity_std'] + controls
        )
        stats['model'] = '7b_terciles'
        results.append(stats)
        print_model_result("7b: Density Terciles + Diversity", res,
                          ['density_medium', 'density_high', 'diversity_std'])

        # Compare terciles
        print("\n  Tercile interpretation (vs Low density):")
        if 'density_medium_coef' in stats:
            print(f"    Medium density: {stats['density_medium_coef']:.4f}")
        if 'density_high_coef' in stats:
            print(f"    High density: {stats['density_high_coef']:.4f}")
    except Exception as e:
        logger.warning(f"7b failed: {e}")

    # Model 7c: Marginal effects at different density levels
    print("\n--- Model 7c: Marginal Effects Plot ---")
    try:
        # Refit main model for marginal effects
        res, _ = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'diversity_std'] + controls
        )

        # Plot marginal effects
        fig, ax = plt.subplots(figsize=(8, 5))

        density_range = np.linspace(sample['density_std'].min(), sample['density_std'].max(), 100)
        mean_div = sample['diversity_std'].mean()
        mean_ego = sample['log_ego_size'].mean()
        mean_exp = sample['log_experience'].mean()

        eta = (res.params['const'] +
               res.params['density_std'] * density_range +
               res.params['diversity_std'] * mean_div +
               res.params['log_ego_size'] * mean_ego +
               res.params['log_experience'] * mean_exp)

        prob = 1 / (1 + np.exp(-eta))

        ax.plot(density_range, prob, 'b-', linewidth=2)
        ax.fill_between(density_range, prob - 0.02, prob + 0.02, alpha=0.2)
        ax.set_xlabel('Network Density (Standardized)')
        ax.set_ylabel('Predicted HRV Share')
        ax.set_title('Marginal Effect of Density on HRV')
        ax.axhline(y=prob.mean(), color='gray', linestyle='--', alpha=0.5)

        plt.tight_layout()
        plt.savefig(PLOTS_DIR / 'density_marginal_effect.png', dpi=300)
        plt.close()
        logger.info("Saved density marginal effects plot")

    except Exception as e:
        logger.warning(f"7c plot failed: {e}")

    df = pd.DataFrame(results)
    df.to_csv(EXPLORATORY_DIR / 'nonlinearity_results.csv', index=False)

    return df, sample


# =============================================================================
# 4. ALTERNATIVE INTERACTIONS
# =============================================================================

def run_alternative_interactions(sample):
    """Test interactions we didn't hypothesize ex ante."""
    logger.info("="*60)
    logger.info("4. ALTERNATIVE INTERACTIONS")
    logger.info("="*60)

    results = []
    controls = ['log_ego_size', 'log_experience']

    sample = sample.copy()

    # Model 8a: Diversity × International share
    print("\n--- Model 8a: Diversity × International Share ---")
    try:
        sample['diversity_x_intl'] = sample['diversity_std'] * sample['pct_international_std']
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['diversity_std', 'pct_international_std', 'diversity_x_intl', 'density_std'] + controls
        )
        stats['model'] = '8a_diversity_x_intl'
        results.append(stats)
        print_model_result("8a: Diversity × % International", res,
                          ['diversity_std', 'pct_international_std', 'diversity_x_intl', 'density_std'])
    except Exception as e:
        logger.warning(f"8a failed: {e}")

    # Model 8b: Density × Focal African
    print("\n--- Model 8b: Density × Focal African ---")
    try:
        sample['density_x_african'] = sample['density_std'] * sample['focal_is_african']
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'focal_is_african', 'density_x_african', 'diversity_std'] + controls
        )
        stats['model'] = '8b_density_x_african'
        results.append(stats)
        print_model_result("8b: Density × Focal African", res,
                          ['density_std', 'focal_is_african', 'density_x_african', 'diversity_std'])
    except Exception as e:
        logger.warning(f"8b failed: {e}")

    # Model 8c: Density × Ego size
    print("\n--- Model 8c: Density × Ego Size ---")
    try:
        sample['density_x_egosize'] = sample['density_std'] * sample['log_ego_size']
        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'log_ego_size', 'density_x_egosize', 'diversity_std', 'log_experience']
        )
        stats['model'] = '8c_density_x_egosize'
        results.append(stats)
        print_model_result("8c: Density × Ego Size", res,
                          ['density_std', 'log_ego_size', 'density_x_egosize', 'diversity_std'])
    except Exception as e:
        logger.warning(f"8c failed: {e}")

    df = pd.DataFrame(results)
    df.to_csv(EXPLORATORY_DIR / 'alt_interactions_results.csv', index=False)

    return df


# =============================================================================
# 5. TEMPORAL DYNAMICS
# =============================================================================

def run_temporal_analysis(sample):
    """Check if effects differ by year."""
    logger.info("="*60)
    logger.info("5. TEMPORAL DYNAMICS")
    logger.info("="*60)

    results = []
    controls = ['log_ego_size', 'log_experience']

    sample = sample.copy()

    # Model 9a: Year interactions
    print("\n--- Model 9a: Year Interactions ---")
    try:
        # Create year interactions
        sample['density_x_2023'] = sample['density_std'] * (sample['year'] == 2023).astype(int)
        sample['density_x_2024'] = sample['density_std'] * (sample['year'] == 2024).astype(int)
        sample['diversity_x_2023'] = sample['diversity_std'] * (sample['year'] == 2023).astype(int)
        sample['diversity_x_2024'] = sample['diversity_std'] * (sample['year'] == 2024).astype(int)

        res, stats = run_gee_model(
            sample, 'hrv_share',
            ['density_std', 'diversity_std',
             'density_x_2023', 'density_x_2024',
             'diversity_x_2023', 'diversity_x_2024'] + controls
        )
        stats['model'] = '9a_year_interactions'
        results.append(stats)
        print_model_result("9a: Year Interactions", res,
                          ['density_std', 'diversity_std',
                           'density_x_2023', 'density_x_2024',
                           'diversity_x_2023', 'diversity_x_2024'])
    except Exception as e:
        logger.warning(f"9a failed: {e}")

    # Model 9b: Coefficient plot by year
    print("\n--- Model 9b: Effects by Year ---")
    year_effects = []

    for year in sorted(sample['year'].unique()):
        try:
            year_sample = sample[sample['year'] == year]
            if len(year_sample) < 30:
                continue

            res, stats = run_gee_model(
                year_sample, 'hrv_share',
                ['density_std', 'diversity_std'] + controls
            )

            year_effects.append({
                'year': year,
                'n_obs': len(year_sample),
                'density_coef': stats.get('density_std_coef', np.nan),
                'density_se': stats.get('density_std_se', np.nan),
                'density_pval': stats.get('density_std_pval', np.nan),
                'diversity_coef': stats.get('diversity_std_coef', np.nan),
                'diversity_se': stats.get('diversity_std_se', np.nan),
                'diversity_pval': stats.get('diversity_std_pval', np.nan),
            })

            print(f"\n  Year {year} (N={len(year_sample)}):")
            print(f"    Density:   {stats.get('density_std_coef', np.nan):.4f} (p={stats.get('density_std_pval', np.nan):.3f})")
            print(f"    Diversity: {stats.get('diversity_std_coef', np.nan):.4f} (p={stats.get('diversity_std_pval', np.nan):.3f})")

        except Exception as e:
            logger.warning(f"Year {year} failed: {e}")

    # Plot coefficients by year
    if year_effects:
        year_df = pd.DataFrame(year_effects)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Density by year
        ax = axes[0]
        ax.errorbar(year_df['year'], year_df['density_coef'],
                   yerr=1.96*year_df['density_se'],
                   fmt='o-', capsize=5, capthick=2, markersize=10, linewidth=2)
        ax.axhline(0, color='red', linestyle='--', alpha=0.5)
        ax.set_xlabel('Year')
        ax.set_ylabel('Coefficient')
        ax.set_title('Density Effect by Year')
        ax.set_xticks(year_df['year'])

        # Diversity by year
        ax = axes[1]
        ax.errorbar(year_df['year'], year_df['diversity_coef'],
                   yerr=1.96*year_df['diversity_se'],
                   fmt='o-', capsize=5, capthick=2, markersize=10, linewidth=2, color='green')
        ax.axhline(0, color='red', linestyle='--', alpha=0.5)
        ax.set_xlabel('Year')
        ax.set_ylabel('Coefficient')
        ax.set_title('Diversity Effect by Year')
        ax.set_xticks(year_df['year'])

        plt.tight_layout()
        plt.savefig(PLOTS_DIR / 'temporal_effects.png', dpi=300)
        plt.close()
        logger.info("Saved temporal effects plot")

        year_df.to_csv(EXPLORATORY_DIR / 'temporal_by_year.csv', index=False)

    df = pd.DataFrame(results)
    df.to_csv(EXPLORATORY_DIR / 'temporal_results.csv', index=False)

    return df


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def generate_exploratory_report(decomp_df, hetero_df, nonlin_df, altint_df, temporal_df):
    """Generate summary report of exploratory findings."""

    report = f"""# Exploratory Analysis Summary

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Overview

This report explores the diversity/density effects to understand where the action is,
given that the hypothesized Density × Diversity interaction was not significant.

---

## 1. Diversity Decomposition

**Question:** Is the diversity effect driven by investor-type heterogeneity,
geographic reach, or specifically by international partner access?

"""

    # Find notable results from decomposition
    if decomp_df is not None and len(decomp_df) > 0:
        for _, row in decomp_df.iterrows():
            model = row['model']
            for col in row.index:
                if '_pval' in col and pd.notna(row[col]) and row[col] < 0.10:
                    var = col.replace('_pval', '')
                    coef = row.get(f'{var}_coef', np.nan)
                    pval = row[col]
                    stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '†'
                    report += f"- **{model}**: {var} = {coef:.4f}{stars} (p={pval:.3f})\n"

    report += """

---

## 2. Heterogeneity by Focal Investor Type

**Question:** Does density hurt local VCs more? Do international VCs benefit more from diversity?

"""

    if hetero_df is not None and len(hetero_df) > 0:
        for _, row in hetero_df.iterrows():
            model = row['model']
            subsample = row.get('subsample', '')
            report += f"\n### {model} ({subsample})\n"
            for col in row.index:
                if '_pval' in col and pd.notna(row[col]) and row[col] < 0.10:
                    var = col.replace('_pval', '')
                    coef = row.get(f'{var}_coef', np.nan)
                    pval = row[col]
                    stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '†'
                    report += f"- {var} = {coef:.4f}{stars} (p={pval:.3f})\n"

    report += """

---

## 3. Nonlinearity in Density

**Question:** Is moderate density beneficial but high density harmful?

"""

    if nonlin_df is not None and len(nonlin_df) > 0:
        for _, row in nonlin_df.iterrows():
            model = row['model']
            report += f"\n### {model}\n"
            for col in row.index:
                if '_pval' in col and pd.notna(row[col]) and row[col] < 0.10:
                    var = col.replace('_pval', '')
                    coef = row.get(f'{var}_coef', np.nan)
                    pval = row[col]
                    stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '†'
                    report += f"- {var} = {coef:.4f}{stars} (p={pval:.3f})\n"

    report += """

---

## 4. Alternative Interactions

**Question:** Are there conditional effects the main interaction missed?

"""

    if altint_df is not None and len(altint_df) > 0:
        for _, row in altint_df.iterrows():
            model = row['model']
            report += f"\n### {model}\n"
            for col in row.index:
                if '_pval' in col and pd.notna(row[col]) and row[col] < 0.10:
                    var = col.replace('_pval', '')
                    coef = row.get(f'{var}_coef', np.nan)
                    pval = row[col]
                    stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else '†'
                    report += f"- {var} = {coef:.4f}{stars} (p={pval:.3f})\n"

    report += """

---

## 5. Temporal Dynamics

**Question:** Are effects strengthening or weakening as ecosystem matures?

See `temporal_by_year.csv` and `key_plots/temporal_effects.png` for year-by-year coefficients.

---

## Key Takeaways

"""

    # Count notable findings
    n_notable = 0
    notable_findings = []

    for df, name in [(decomp_df, 'Decomposition'), (hetero_df, 'Heterogeneity'),
                      (nonlin_df, 'Nonlinearity'), (altint_df, 'Alt Interactions')]:
        if df is not None:
            for _, row in df.iterrows():
                for col in row.index:
                    if '_pval' in col and pd.notna(row[col]) and row[col] < 0.10:
                        n_notable += 1
                        var = col.replace('_pval', '')
                        notable_findings.append(f"{name}: {var}")

    report += f"**{n_notable} findings with p < 0.10**\n\n"

    for finding in notable_findings[:10]:
        report += f"- {finding}\n"

    report += """

---

## Output Files

- `decomposition_results.csv` - Models 5a-5e
- `heterogeneity_results.csv` - Models 6a-6c
- `nonlinearity_results.csv` - Models 7a-7c
- `alt_interactions_results.csv` - Models 8a-8c
- `temporal_results.csv` - Model 9a
- `temporal_by_year.csv` - Coefficients by year
- `key_plots/` - Visualization files
"""

    with open(EXPLORATORY_DIR / 'exploratory_summary.md', 'w') as f:
        f.write(report)

    logger.info(f"Report saved to {EXPLORATORY_DIR / 'exploratory_summary.md'}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all exploratory analyses."""
    logger.info("="*60)
    logger.info("EXPLORATORY ANALYSIS")
    logger.info("="*60)

    # Load data
    panel = pd.read_parquet(PROCESSED_DATA_DIR / 'vc_year_panel.parquet')
    sample = prepare_analysis_sample(panel)
    logger.info(f"Analysis sample: {len(sample)} observations")

    # Run all analyses
    decomp_df, sample = run_diversity_decomposition(sample)
    hetero_df, sample = run_heterogeneity_analysis(sample)
    nonlin_df, sample = run_nonlinearity_analysis(sample)
    altint_df = run_alternative_interactions(sample)
    temporal_df = run_temporal_analysis(sample)

    # Generate report
    generate_exploratory_report(decomp_df, hetero_df, nonlin_df, altint_df, temporal_df)

    logger.info("\n" + "="*60)
    logger.info("EXPLORATORY ANALYSIS COMPLETE")
    logger.info("="*60)
    logger.info(f"Results saved to {EXPLORATORY_DIR}")


if __name__ == '__main__':
    main()
