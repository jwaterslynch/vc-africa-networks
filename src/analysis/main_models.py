"""
Main Regression Models

Fractional logit models for HRV share analysis.

Model specifications:
- Model 1: HRV ~ density + controls
- Model 2: HRV ~ diversity + controls
- Model 3: HRV ~ density + diversity + controls
- Model 4: HRV ~ density + diversity + density×diversity + controls

Controls: ego_size, experience_cumulative, year FE
Standard errors clustered by investor_id
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import Logit
import warnings
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def prepare_analysis_sample(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare analysis sample: filter to VCs with deals in focal year,
    standardize variables, create dummies.
    """
    # Filter to observations with outcome
    sample = panel[panel['n_deals'] > 0].copy()

    # Standardize continuous IVs for interpretation
    sample['density_std'] = (
        sample['ego_density'] - sample['ego_density'].mean()
    ) / sample['ego_density'].std()

    sample['diversity_std'] = sample['diversity_combined']  # Already z-scored

    # Interaction term (standardized)
    sample['density_x_diversity_std'] = sample['density_std'] * sample['diversity_std']

    # Log transform experience (add 1 to handle zeros)
    sample['log_experience'] = np.log1p(sample['experience_cumulative'])

    # Log ego size
    sample['log_ego_size'] = np.log1p(sample['ego_size'])

    # Year dummies (reference = first year)
    years = sorted(sample['year'].unique())
    for year in years[1:]:  # Skip first year (reference)
        sample[f'year_{year}'] = (sample['year'] == year).astype(int)

    return sample


def run_fractional_logit(
    sample: pd.DataFrame,
    y_var: str,
    x_vars: List[str],
    cluster_var: str = 'investor_id',
    year_fe: bool = True
) -> sm.GEE:
    """
    Run fractional logit (GLM with binomial family, logit link).

    Parameters
    ----------
    sample : DataFrame
    y_var : str
        Dependent variable (should be [0, 1])
    x_vars : list
        Independent variables
    cluster_var : str
        Variable for clustering SEs
    year_fe : bool
        Include year fixed effects

    Returns
    -------
    Fitted model results
    """
    # Build formula
    all_vars = x_vars.copy()

    if year_fe:
        years = sorted(sample['year'].unique())
        year_dummies = [f'year_{y}' for y in years[1:]]
        all_vars.extend(year_dummies)

    # Prepare data
    y = sample[y_var].values
    X = sample[all_vars].copy()
    X = sm.add_constant(X)

    # Handle any remaining NaN
    valid_mask = ~(X.isna().any(axis=1) | np.isnan(y))
    y = y[valid_mask]
    X = X[valid_mask]
    groups = sample.loc[valid_mask, cluster_var].values

    # Fit GEE for clustered SEs (exchangeable correlation)
    model = sm.GEE(
        y, X,
        groups=groups,
        family=Binomial(link=Logit()),
        cov_struct=sm.cov_struct.Exchangeable()
    )

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit()

    return result


def run_main_models(
    sample: pd.DataFrame,
    y_var: str = 'hrv_share'
) -> Dict[str, sm.GEE]:
    """
    Run all four main model specifications.

    Returns dict of fitted models.
    """
    logger.info(f"Running main models with DV = {y_var}")

    # Control variables
    controls = ['log_ego_size', 'log_experience']

    models = {}

    # Model 1: Density only
    logger.info("  Model 1: Density + controls")
    models['M1_density'] = run_fractional_logit(
        sample, y_var,
        ['density_std'] + controls
    )

    # Model 2: Diversity only
    logger.info("  Model 2: Diversity + controls")
    models['M2_diversity'] = run_fractional_logit(
        sample, y_var,
        ['diversity_std'] + controls
    )

    # Model 3: Both main effects
    logger.info("  Model 3: Density + Diversity + controls")
    models['M3_both'] = run_fractional_logit(
        sample, y_var,
        ['density_std', 'diversity_std'] + controls
    )

    # Model 4: Full model with interaction
    logger.info("  Model 4: Full model with interaction")
    models['M4_interaction'] = run_fractional_logit(
        sample, y_var,
        ['density_std', 'diversity_std', 'density_x_diversity_std'] + controls
    )

    return models


def extract_model_stats(model, model_name: str) -> Dict:
    """Extract key statistics from fitted model."""
    params = model.params
    bse = model.bse
    pvalues = model.pvalues

    stats = {
        'model': model_name,
        'n_obs': int(model.nobs),
        'n_clusters': len(np.unique(model.model.groups))
    }

    # Extract coefficients
    for var in params.index:
        if var == 'const':
            continue
        stats[f'{var}_coef'] = params[var]
        stats[f'{var}_se'] = bse[var]
        stats[f'{var}_pval'] = pvalues[var]

        # Significance stars
        p = pvalues[var]
        if p < 0.001:
            stars = '***'
        elif p < 0.01:
            stars = '**'
        elif p < 0.05:
            stars = '*'
        elif p < 0.10:
            stars = '†'
        else:
            stars = ''
        stats[f'{var}_stars'] = stars

    return stats


def format_results_table(models: Dict[str, sm.GEE]) -> pd.DataFrame:
    """
    Format model results as a table.
    """
    rows = []
    for name, model in models.items():
        stats = extract_model_stats(model, name)
        rows.append(stats)

    return pd.DataFrame(rows)


def generate_latex_table(
    models: Dict[str, sm.GEE],
    output_path: str = None
) -> str:
    """
    Generate publication-ready LaTeX table.
    """
    # Variables in display order
    var_labels = {
        'density_std': 'Network Density',
        'diversity_std': 'Network Diversity',
        'density_x_diversity_std': 'Density × Diversity',
        'log_ego_size': 'Log(Ego Size)',
        'log_experience': 'Log(Experience)',
        'year_2023': 'Year 2023',
        'year_2024': 'Year 2024',
    }

    model_names = list(models.keys())

    # Build table
    lines = []
    lines.append(r'\begin{table}[htbp]')
    lines.append(r'\centering')
    lines.append(r'\caption{Fractional Logit Models: Network Structure and High-Risk Venture Investment}')
    lines.append(r'\label{tab:main_results}')
    lines.append(r'\begin{tabular}{l' + 'c' * len(models) + '}')
    lines.append(r'\hline\hline')

    # Header
    header = ' & '.join([''] + [f'({i+1})' for i in range(len(models))]) + r' \\'
    lines.append(header)

    model_labels = ' & '.join([''] + ['HRV Share'] * len(models)) + r' \\'
    lines.append(model_labels)
    lines.append(r'\hline')

    # Coefficients
    for var, label in var_labels.items():
        coef_row = [label]
        se_row = ['']

        for name, model in models.items():
            if var in model.params.index:
                coef = model.params[var]
                se = model.bse[var]
                pval = model.pvalues[var]

                # Stars
                if pval < 0.001:
                    stars = '***'
                elif pval < 0.01:
                    stars = '**'
                elif pval < 0.05:
                    stars = '*'
                elif pval < 0.10:
                    stars = '$^\\dagger$'
                else:
                    stars = ''

                coef_row.append(f'{coef:.3f}{stars}')
                se_row.append(f'({se:.3f})')
            else:
                coef_row.append('')
                se_row.append('')

        lines.append(' & '.join(coef_row) + r' \\')
        lines.append(' & '.join(se_row) + r' \\[0.5ex]')

    lines.append(r'\hline')

    # Footer stats
    n_row = ['Observations']
    cluster_row = ['VC Clusters']

    for name, model in models.items():
        n_row.append(str(int(model.nobs)))
        cluster_row.append(str(len(np.unique(model.model.groups))))

    lines.append(' & '.join(n_row) + r' \\')
    lines.append(' & '.join(cluster_row) + r' \\')
    lines.append(r'Year FE & ' + ' & '.join(['Yes'] * len(models)) + r' \\')

    lines.append(r'\hline\hline')
    lines.append(r'\multicolumn{' + str(len(models) + 1) + r'}{l}{\footnotesize $^{***}p<0.001$, $^{**}p<0.01$, $^{*}p<0.05$, $^\dagger p<0.10$} \\')
    lines.append(r'\multicolumn{' + str(len(models) + 1) + r'}{l}{\footnotesize Robust standard errors clustered by VC in parentheses.} \\')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')

    latex = '\n'.join(lines)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(latex)
        logger.info(f"LaTeX table saved to {output_path}")

    return latex


def print_model_summary(models: Dict[str, sm.GEE]):
    """Print formatted summary of all models."""
    print("\n" + "="*80)
    print("MAIN MODEL RESULTS")
    print("="*80)

    for name, model in models.items():
        print(f"\n--- {name} ---")
        print(f"N = {int(model.nobs)}, Clusters = {len(np.unique(model.model.groups))}")
        print("\nCoefficients:")

        for var in model.params.index:
            if var == 'const':
                continue
            coef = model.params[var]
            se = model.bse[var]
            pval = model.pvalues[var]

            if pval < 0.001:
                stars = '***'
            elif pval < 0.01:
                stars = '**'
            elif pval < 0.05:
                stars = '*'
            elif pval < 0.10:
                stars = '†'
            else:
                stars = ''

            print(f"  {var:30s}: {coef:8.4f} ({se:.4f}) {stars}")

    # Highlight key result
    if 'M4_interaction' in models:
        m4 = models['M4_interaction']
        if 'density_x_diversity_std' in m4.params.index:
            coef = m4.params['density_x_diversity_std']
            pval = m4.pvalues['density_x_diversity_std']

            print("\n" + "="*80)
            print("KEY RESULT: Density × Diversity Interaction")
            print("="*80)
            print(f"Coefficient: {coef:.4f}")
            print(f"P-value: {pval:.4f}")

            if coef > 0 and pval < 0.05:
                print("✅ HYPOTHESIS SUPPORTED: Positive and significant interaction")
            elif coef > 0 and pval < 0.10:
                print("⚠️ MARGINAL SUPPORT: Positive interaction, marginally significant")
            elif coef > 0:
                print("❌ NOT SIGNIFICANT: Positive but not statistically significant")
            else:
                print("❌ HYPOTHESIS NOT SUPPORTED: Negative interaction")
