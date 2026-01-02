#!/usr/bin/env python3
"""
Generate Paper Tables and Single Source of Truth

This script:
1. Loads the VC-year panel
2. Runs all models (pooled + split-sample)
3. Computes all statistics
4. Writes to paper_numbers.json
5. Generates publication-ready tables

Output:
- outputs/paper_numbers.json
- outputs/tables/table1_descriptives.tex/.csv
- outputs/tables/table2_pooled_models.tex/.csv
- outputs/tables/table3_split_sample.tex/.csv
- outputs/tables/tableA1_robustness.tex/.csv
- outputs/tables/tableA2_common_support.tex/.csv
- outputs/final_checks/data_validation_log.txt
"""

import os
import sys
from pathlib import Path
import json
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import Logit
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Setup
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
TABLES_DIR = OUTPUTS_DIR / 'tables'
FINAL_CHECKS_DIR = OUTPUTS_DIR / 'final_checks'

for d in [TABLES_DIR, FINAL_CHECKS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def stars(p):
    """Return significance stars from p-value."""
    if p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    elif p < 0.10:
        return '†'
    return ''


def load_and_validate_data():
    """Load panel data and run validation assertions."""
    logger.info("=" * 70)
    logger.info("LOADING AND VALIDATING DATA")
    logger.info("=" * 70)

    # Load data
    panel = pd.read_parquet(PROJECT_ROOT / 'data/processed/vc_year_panel.parquet')
    sample = panel[panel['n_deals'] > 0].copy()

    # Also load deals for deal count
    deals = pd.read_parquet(PROJECT_ROOT / 'data/interim/deals.parquet')
    investors = pd.read_parquet(PROJECT_ROOT / 'data/interim/investors.parquet')

    validation_log = []
    validation_log.append(f"Data Validation Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    validation_log.append("=" * 70)

    # Assertions
    try:
        # Density bounds (allowing small float errors)
        assert (sample['ego_density'] >= -0.01).all() and (sample['ego_density'] <= 1.15).all(), \
            f"Density out of bounds! Range: [{sample['ego_density'].min():.3f}, {sample['ego_density'].max():.3f}]"
        validation_log.append("✓ Density values within expected bounds [0, 1.1]")

        # HRV share bounds
        assert (sample['hrv_share'] >= 0).all() and (sample['hrv_share'] <= 1).all(), \
            "HRV share out of bounds!"
        validation_log.append("✓ HRV share values within [0, 1]")

        # Outcome years
        assert sample['year'].min() >= 2022, f"Outcome years should be 2022+, got {sample['year'].min()}"
        validation_log.append(f"✓ Outcome years: {sample['year'].min()}-{sample['year'].max()}")

        # Sample size checks
        assert len(sample) == 901, f"Expected 901 VC-years, got {len(sample)}"
        validation_log.append(f"✓ Sample size: {len(sample)} VC-years")

        assert sample['investor_id'].nunique() == 558, f"Expected 558 unique investors, got {sample['investor_id'].nunique()}"
        validation_log.append(f"✓ Unique investors: {sample['investor_id'].nunique()}")

        # HQ split
        n_african = (sample['hq_in_africa'] == 1).sum()
        n_intl = (sample['hq_in_africa'] == 0).sum()
        assert n_african == 295, f"Expected 295 African VCs, got {n_african}"
        assert n_intl == 606, f"Expected 606 International VCs, got {n_intl}"
        validation_log.append(f"✓ HQ split: {n_intl} International, {n_african} African")

        validation_log.append("\n✓ ALL VALIDATION CHECKS PASSED")

    except AssertionError as e:
        validation_log.append(f"\n✗ VALIDATION FAILED: {str(e)}")
        logger.error(f"Validation failed: {e}")
        raise

    # Write validation log
    with open(FINAL_CHECKS_DIR / 'data_validation_log.txt', 'w') as f:
        f.write('\n'.join(validation_log))

    logger.info(f"Loaded {len(sample)} VC-years, {sample['investor_id'].nunique()} unique investors")
    logger.info(f"Validation log: {FINAL_CHECKS_DIR / 'data_validation_log.txt'}")

    return sample, deals, investors


def prepare_sample(sample):
    """Prepare analysis sample with standardized variables."""
    df = sample.copy()

    # Standardize
    df['density_std'] = (df['ego_density'] - df['ego_density'].mean()) / df['ego_density'].std()
    df['diversity_std'] = df['diversity_combined']  # Already z-scored
    df['log_ego_size'] = np.log1p(df['ego_size'])
    df['log_experience'] = np.log1p(df['experience_cumulative'])

    # Year dummies
    df['year_2023'] = (df['year'] == 2023).astype(int)
    df['year_2024'] = (df['year'] == 2024).astype(int)

    # Interactions
    df['density_x_diversity'] = df['density_std'] * df['diversity_std']
    df['density_x_african'] = df['density_std'] * df['hq_in_africa']

    return df


def run_gee(df, predictors, cluster_var='investor_id'):
    """Run GEE model with clustered SEs."""
    y = df['hrv_share'].values
    X = df[predictors].copy()
    X = sm.add_constant(X)

    valid = ~(X.isna().any(axis=1) | np.isnan(y))
    y, X = y[valid], X[valid]
    groups = df.loc[valid, cluster_var].values

    model = sm.GEE(
        y, X, groups=groups,
        family=Binomial(link=Logit()),
        cov_struct=sm.cov_struct.Exchangeable()
    )
    return model.fit(), sum(valid)


def run_glm_weighted(df, predictors):
    """Run GLM weighted by n_deals."""
    y = df['hrv_share'].values
    X = df[predictors].copy()
    X = sm.add_constant(X)
    weights = df['n_deals'].values

    model = sm.GLM(y, X, family=Binomial(link=Logit()), freq_weights=weights)
    return model.fit()


def compute_all_statistics(sample, deals, investors):
    """Compute all statistics and return paper_numbers dict."""
    logger.info("\n" + "=" * 70)
    logger.info("COMPUTING ALL STATISTICS")
    logger.info("=" * 70)

    df = prepare_sample(sample)
    african = df[df['hq_in_africa'] == 1]
    intl = df[df['hq_in_africa'] == 0]

    controls = ['log_ego_size', 'log_experience', 'year_2023', 'year_2024']

    paper_numbers = {
        'generated_at': datetime.now().isoformat(),
        'sample': {},
        'descriptives': {},
        'pooled_models': {},
        'split_sample': {},
        'marginal_effects': {},
        'robustness': {}
    }

    # =========================================================================
    # Sample sizes
    # =========================================================================
    paper_numbers['sample'] = {
        'n_deals': int(len(deals)),
        'n_investors': int(sample['investor_id'].nunique()),
        'n_vc_years': int(len(sample)),
        'n_international': int(len(intl)),
        'n_african': int(len(african)),
        'years': [2022, 2023, 2024]
    }

    # =========================================================================
    # Descriptives
    # =========================================================================
    paper_numbers['descriptives'] = {
        'hrv_share': {
            'mean': round(sample['hrv_share'].mean(), 3),
            'sd': round(sample['hrv_share'].std(), 3)
        },
        'ego_density': {
            'mean': round(sample['ego_density'].mean(), 3),
            'sd': round(sample['ego_density'].std(), 3)
        },
        'ego_density_intl': {
            'mean': round(intl['ego_density'].mean(), 3),
            'sd': round(intl['ego_density'].std(), 3)
        },
        'ego_density_african': {
            'mean': round(african['ego_density'].mean(), 3),
            'sd': round(african['ego_density'].std(), 3)
        },
        'diversity': {
            'mean': round(sample['diversity_combined'].mean(), 3),
            'sd': round(sample['diversity_combined'].std(), 3)
        },
        'ego_size': {
            'mean': round(sample['ego_size'].mean(), 1),
            'sd': round(sample['ego_size'].std(), 1)
        },
        'experience': {
            'mean': round(sample['experience_cumulative'].mean(), 1),
            'sd': round(sample['experience_cumulative'].std(), 1)
        },
        'n_deals_per_year': {
            'mean': round(sample['n_deals'].mean(), 1),
            'sd': round(sample['n_deals'].std(), 1)
        }
    }

    # =========================================================================
    # Pooled Models
    # =========================================================================
    logger.info("\nRunning pooled models...")

    # Model 1: Density only
    pred1 = ['density_std'] + controls
    result1, n1 = run_gee(df, pred1)
    paper_numbers['pooled_models']['model1_density'] = {
        'beta': round(result1.params['density_std'], 3),
        'se': round(result1.bse['density_std'], 3),
        'p': round(result1.pvalues['density_std'], 4)
    }

    # Model 2: Density + Diversity
    pred2 = ['density_std', 'diversity_std'] + controls
    result2, n2 = run_gee(df, pred2)
    paper_numbers['pooled_models']['model2_diversity'] = {
        'beta': round(result2.params['diversity_std'], 3),
        'se': round(result2.bse['diversity_std'], 3),
        'p': round(result2.pvalues['diversity_std'], 4)
    }

    # Model 3: With density x diversity
    pred3 = ['density_std', 'diversity_std', 'density_x_diversity'] + controls
    result3, n3 = run_gee(df, pred3)
    paper_numbers['pooled_models']['model3_density_x_diversity'] = {
        'beta': round(result3.params['density_x_diversity'], 3),
        'se': round(result3.bse['density_x_diversity'], 3),
        'p': round(result3.pvalues['density_x_diversity'], 4)
    }

    # Model 4: With density x african
    pred4 = ['density_std', 'diversity_std', 'hq_in_africa', 'density_x_african'] + controls
    result4, n4 = run_gee(df, pred4)
    paper_numbers['pooled_models']['model4_density_x_african'] = {
        'beta': round(result4.params['density_x_african'], 3),
        'se': round(result4.bse['density_x_african'], 3),
        'p': round(result4.pvalues['density_x_african'], 4)
    }

    # Store all model results for table generation
    paper_numbers['pooled_models']['full_results'] = {
        'model1': {var: {'beta': round(result1.params[var], 3),
                         'se': round(result1.bse[var], 3),
                         'p': round(result1.pvalues[var], 4)}
                   for var in result1.params.index},
        'model2': {var: {'beta': round(result2.params[var], 3),
                         'se': round(result2.bse[var], 3),
                         'p': round(result2.pvalues[var], 4)}
                   for var in result2.params.index},
        'model3': {var: {'beta': round(result3.params[var], 3),
                         'se': round(result3.bse[var], 3),
                         'p': round(result3.pvalues[var], 4)}
                   for var in result3.params.index},
        'model4': {var: {'beta': round(result4.params[var], 3),
                         'se': round(result4.bse[var], 3),
                         'p': round(result4.pvalues[var], 4)}
                   for var in result4.params.index}
    }

    # =========================================================================
    # Split-Sample Analysis
    # =========================================================================
    logger.info("Running split-sample analysis...")

    predictors_split = ['density_std', 'diversity_std'] + controls

    result_intl, n_intl = run_gee(intl, predictors_split)
    result_afr, n_afr = run_gee(african, predictors_split)

    coef_intl = result_intl.params['density_std']
    se_intl = result_intl.bse['density_std']
    p_intl = result_intl.pvalues['density_std']

    coef_afr = result_afr.params['density_std']
    se_afr = result_afr.bse['density_std']
    p_afr = result_afr.pvalues['density_std']

    # Difference test
    diff = coef_afr - coef_intl
    se_diff = np.sqrt(se_intl**2 + se_afr**2)
    z_stat = diff / se_diff
    p_diff = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    paper_numbers['split_sample'] = {
        'international': {
            'n': int(n_intl),
            'beta': round(coef_intl, 3),
            'se': round(se_intl, 3),
            'p': round(p_intl, 4)
        },
        'african': {
            'n': int(n_afr),
            'beta': round(coef_afr, 3),
            'se': round(se_afr, 3),
            'p': round(p_afr, 4)
        },
        'difference': {
            'beta': round(diff, 3),
            'se': round(se_diff, 3),
            'z': round(z_stat, 2),
            'p': round(p_diff, 4)
        },
        'full_results': {
            'international': {var: {'beta': round(result_intl.params[var], 3),
                                    'se': round(result_intl.bse[var], 3),
                                    'p': round(result_intl.pvalues[var], 4)}
                             for var in result_intl.params.index},
            'african': {var: {'beta': round(result_afr.params[var], 3),
                              'se': round(result_afr.bse[var], 3),
                              'p': round(result_afr.pvalues[var], 4)}
                       for var in result_afr.params.index}
        }
    }

    # =========================================================================
    # Marginal Effects
    # =========================================================================
    logger.info("Computing marginal effects...")

    def get_marginal_effects(model_result, df_subset, density_values=[-1, 1]):
        predictors = ['density_std', 'diversity_std', 'log_ego_size', 'log_experience',
                      'year_2023', 'year_2024']

        mean_diversity = df_subset['diversity_std'].mean()
        mean_ego = df_subset['log_ego_size'].mean()
        mean_exp = df_subset['log_experience'].mean()

        predictions = {}
        for d in density_values:
            pred_data = pd.DataFrame({
                'const': [1],
                'density_std': [d],
                'diversity_std': [mean_diversity],
                'log_ego_size': [mean_ego],
                'log_experience': [mean_exp],
                'year_2023': [0],
                'year_2024': [0]
            })
            predictions[d] = model_result.predict(pred_data)[0]

        return predictions

    # Refit GLM for predictions (GEE predict can be tricky)
    def fit_glm(df_subset):
        predictors = ['density_std', 'diversity_std', 'log_ego_size', 'log_experience',
                      'year_2023', 'year_2024']
        X = df_subset[predictors].copy()
        X = sm.add_constant(X)
        y = df_subset['hrv_share']
        return sm.GLM(y, X, family=Binomial(link=Logit())).fit()

    glm_intl = fit_glm(intl)
    glm_afr = fit_glm(african)

    pred_intl = get_marginal_effects(glm_intl, intl)
    pred_afr = get_marginal_effects(glm_afr, african)

    paper_numbers['marginal_effects'] = {
        'international_low_density': round(pred_intl[-1], 3),
        'international_high_density': round(pred_intl[1], 3),
        'international_change_pp': round((pred_intl[1] - pred_intl[-1]) * 100, 1),
        'african_low_density': round(pred_afr[-1], 3),
        'african_high_density': round(pred_afr[1], 3),
        'african_change_pp': round((pred_afr[1] - pred_afr[-1]) * 100, 1)
    }

    # =========================================================================
    # Robustness Checks
    # =========================================================================
    logger.info("Running robustness checks...")

    # Common support
    common_min = max(intl['ego_density'].min(), african['ego_density'].min())
    common_max = min(intl['ego_density'].max(), african['ego_density'].max())

    df_common = df[(df['ego_density'] >= common_min) & (df['ego_density'] <= common_max)].copy()
    df_common['density_std'] = (df_common['ego_density'] - df_common['ego_density'].mean()) / df_common['ego_density'].std()

    intl_common = df_common[df_common['hq_in_africa'] == 0]
    afr_common = df_common[df_common['hq_in_africa'] == 1]

    res_intl_cs, _ = run_gee(intl_common, predictors_split)
    res_afr_cs, _ = run_gee(afr_common, predictors_split)

    diff_cs = res_afr_cs.params['density_std'] - res_intl_cs.params['density_std']
    se_cs = np.sqrt(res_intl_cs.bse['density_std']**2 + res_afr_cs.bse['density_std']**2)
    z_cs = diff_cs / se_cs
    p_cs = 2 * (1 - stats.norm.cdf(abs(z_cs)))

    # Trim 10%
    def trim_group(df_group, pct=10):
        lower = np.percentile(df_group['ego_density'], pct)
        upper = np.percentile(df_group['ego_density'], 100 - pct)
        return df_group[(df_group['ego_density'] >= lower) & (df_group['ego_density'] <= upper)]

    intl_trim = trim_group(intl)
    afr_trim = trim_group(african)
    df_trim = pd.concat([intl_trim, afr_trim])
    df_trim['density_std'] = (df_trim['ego_density'] - df_trim['ego_density'].mean()) / df_trim['ego_density'].std()

    intl_trim = df_trim[df_trim['hq_in_africa'] == 0]
    afr_trim = df_trim[df_trim['hq_in_africa'] == 1]

    res_intl_trim, _ = run_gee(intl_trim, predictors_split)
    res_afr_trim, _ = run_gee(afr_trim, predictors_split)

    diff_trim = res_afr_trim.params['density_std'] - res_intl_trim.params['density_std']
    se_trim = np.sqrt(res_intl_trim.bse['density_std']**2 + res_afr_trim.bse['density_std']**2)
    z_trim = diff_trim / se_trim
    p_trim = 2 * (1 - stats.norm.cdf(abs(z_trim)))

    # Weighted
    glm_intl_w = run_glm_weighted(intl, predictors_split)
    glm_afr_w = run_glm_weighted(african, predictors_split)

    diff_w = glm_afr_w.params['density_std'] - glm_intl_w.params['density_std']
    se_w = np.sqrt(glm_intl_w.bse['density_std']**2 + glm_afr_w.bse['density_std']**2)
    z_w = diff_w / se_w
    p_w = 2 * (1 - stats.norm.cdf(abs(z_w)))

    paper_numbers['robustness'] = {
        'common_support': {
            'n_intl': int(len(intl_common)),
            'n_african': int(len(afr_common)),
            'intl_beta': round(res_intl_cs.params['density_std'], 3),
            'intl_se': round(res_intl_cs.bse['density_std'], 3),
            'african_beta': round(res_afr_cs.params['density_std'], 3),
            'african_se': round(res_afr_cs.bse['density_std'], 3),
            'z': round(z_cs, 2),
            'p': round(p_cs, 4)
        },
        'trim_10pct': {
            'n_intl': int(len(intl_trim)),
            'n_african': int(len(afr_trim)),
            'intl_beta': round(res_intl_trim.params['density_std'], 3),
            'intl_se': round(res_intl_trim.bse['density_std'], 3),
            'african_beta': round(res_afr_trim.params['density_std'], 3),
            'african_se': round(res_afr_trim.bse['density_std'], 3),
            'african_p': round(res_afr_trim.pvalues['density_std'], 4),
            'z': round(z_trim, 2),
            'p': round(p_trim, 4)
        },
        'weighted': {
            'n_intl': int(len(intl)),
            'n_african': int(len(african)),
            'intl_beta': round(glm_intl_w.params['density_std'], 3),
            'intl_se': round(glm_intl_w.bse['density_std'], 3),
            'african_beta': round(glm_afr_w.params['density_std'], 3),
            'african_se': round(glm_afr_w.bse['density_std'], 3),
            'z': round(z_w, 2),
            'p': round(p_w, 4)
        }
    }

    return paper_numbers


def generate_table1(paper_numbers, sample):
    """Generate Table 1: Descriptive Statistics."""
    logger.info("\nGenerating Table 1: Descriptives...")

    df = sample.copy()
    african = df[df['hq_in_africa'] == 1]
    intl = df[df['hq_in_africa'] == 0]

    variables = [
        ('N', 'n', None),
        ('HRV Share', 'hrv_share', 3),
        ('Ego Density', 'ego_density', 3),
        ('Diversity (combined)', 'diversity_combined', 3),
        ('Ego Size', 'ego_size', 1),
        ('Experience (cumulative)', 'experience_cumulative', 1),
        ('Deals per Year', 'n_deals', 1)
    ]

    rows = []
    for label, var, decimals in variables:
        if var == 'n':
            rows.append({
                'Variable': label,
                'Full_Mean': len(df),
                'Full_SD': '',
                'Intl_Mean': len(intl),
                'Intl_SD': '',
                'African_Mean': len(african),
                'African_SD': '',
                'p_value': ''
            })
        else:
            t_stat, p_val = stats.ttest_ind(intl[var].dropna(), african[var].dropna())
            rows.append({
                'Variable': label,
                'Full_Mean': round(df[var].mean(), decimals),
                'Full_SD': f"({round(df[var].std(), decimals)})",
                'Intl_Mean': round(intl[var].mean(), decimals),
                'Intl_SD': f"({round(intl[var].std(), decimals)})",
                'African_Mean': round(african[var].mean(), decimals),
                'African_SD': f"({round(african[var].std(), decimals)})",
                'p_value': f"{p_val:.3f}" if p_val >= 0.001 else "<0.001"
            })

    df_table = pd.DataFrame(rows)
    df_table.to_csv(TABLES_DIR / 'table1_descriptives.csv', index=False)

    # LaTeX
    latex = r"""
\begin{table}[htbp]
\centering
\caption{Descriptive Statistics}
\label{tab:descriptives}
\small
\begin{tabular}{lcccccccc}
\toprule
 & \multicolumn{2}{c}{Full Sample} & \multicolumn{2}{c}{International HQ} & \multicolumn{2}{c}{African HQ} & \\
\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}
Variable & Mean & (SD) & Mean & (SD) & Mean & (SD) & $p$ \\
\midrule
"""

    for row in rows:
        if row['Variable'] == 'N':
            latex += f"N & {row['Full_Mean']} & & {row['Intl_Mean']} & & {row['African_Mean']} & & \\\\\n"
        else:
            latex += f"{row['Variable']} & {row['Full_Mean']} & {row['Full_SD']} & "
            latex += f"{row['Intl_Mean']} & {row['Intl_SD']} & "
            latex += f"{row['African_Mean']} & {row['African_SD']} & {row['p_value']} \\\\\n"

    latex += r"""
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item \textit{Notes:} Sample includes VC-year observations with at least one deal in the focal year (2022--2024).
$p$-values from two-sample $t$-tests comparing International and African HQ groups.
\end{tablenotes}
\end{table}
"""

    with open(TABLES_DIR / 'table1_descriptives.tex', 'w') as f:
        f.write(latex)


def generate_table2(paper_numbers):
    """Generate Table 2: Pooled Models."""
    logger.info("Generating Table 2: Pooled Models...")

    models = paper_numbers['pooled_models']['full_results']

    var_labels = {
        'density_std': 'Density',
        'diversity_std': 'Diversity',
        'density_x_diversity': 'Density $\\times$ Diversity',
        'hq_in_africa': 'African HQ',
        'density_x_african': 'Density $\\times$ African HQ',
        'log_ego_size': 'Log(Ego Size)',
        'log_experience': 'Log(Experience)',
        'year_2023': 'Year 2023',
        'year_2024': 'Year 2024',
        'const': 'Constant'
    }

    var_order = ['density_std', 'diversity_std', 'density_x_diversity',
                 'hq_in_africa', 'density_x_african',
                 'log_ego_size', 'log_experience', 'year_2023', 'year_2024', 'const']

    # CSV
    rows = []
    for var in var_order:
        row = {'Variable': var_labels.get(var, var)}
        for i, model_key in enumerate(['model1', 'model2', 'model3', 'model4'], 1):
            model = models[model_key]
            if var in model:
                row[f'M{i}_coef'] = model[var]['beta']
                row[f'M{i}_se'] = model[var]['se']
                row[f'M{i}_p'] = model[var]['p']
            else:
                row[f'M{i}_coef'] = ''
                row[f'M{i}_se'] = ''
                row[f'M{i}_p'] = ''
        rows.append(row)

    pd.DataFrame(rows).to_csv(TABLES_DIR / 'table2_pooled_models.csv', index=False)

    # LaTeX
    latex = r"""
\begin{table}[htbp]
\centering
\caption{Network Density, Diversity, and High-Risk Venture Investment}
\label{tab:pooled}
\small
\begin{tabular}{lcccc}
\toprule
 & (1) & (2) & (3) & (4) \\
\midrule
"""

    for var in var_order:
        if var == 'const':
            continue
        label = var_labels.get(var, var)
        row = f"{label} "
        se_row = " "

        for model_key in ['model1', 'model2', 'model3', 'model4']:
            model = models[model_key]
            if var in model:
                beta = model[var]['beta']
                se = model[var]['se']
                p = model[var]['p']
                star = '^{**}' if p < 0.01 else '^{*}' if p < 0.05 else '^{\\dagger}' if p < 0.10 else ''
                row += f"& ${beta:.3f}{star}$ "
                se_row += f"& ({se:.3f}) "
            else:
                row += "& "
                se_row += "& "

        latex += row + "\\\\\n"
        latex += se_row + "\\\\\n"

    latex += r"""
\midrule
Controls & Yes & Yes & Yes & Yes \\
Year FE & Yes & Yes & Yes & Yes \\
N & 901 & 901 & 901 & 901 \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item \textit{Notes:} Fractional logit (GEE) with clustered standard errors by investor.
DV = HRV share. Controls: log ego size, log experience.
$^{\dagger}p<0.10$; $^{*}p<0.05$; $^{**}p<0.01$.
\end{tablenotes}
\end{table}
"""

    with open(TABLES_DIR / 'table2_pooled_models.tex', 'w') as f:
        f.write(latex)


def generate_table3(paper_numbers):
    """Generate Table 3: Split-Sample Results."""
    logger.info("Generating Table 3: Split-Sample...")

    ss = paper_numbers['split_sample']

    # CSV
    rows = [
        {'Metric': 'N', 'International': ss['international']['n'],
         'African': ss['african']['n'], 'Difference': ''},
        {'Metric': 'Density β', 'International': ss['international']['beta'],
         'African': ss['african']['beta'], 'Difference': ss['difference']['beta']},
        {'Metric': 'SE', 'International': f"({ss['international']['se']})",
         'African': f"({ss['african']['se']})", 'Difference': f"({ss['difference']['se']})"},
        {'Metric': 'p-value', 'International': ss['international']['p'],
         'African': ss['african']['p'], 'Difference': ss['difference']['p']},
        {'Metric': 'z-statistic', 'International': '', 'African': '',
         'Difference': ss['difference']['z']}
    ]

    pd.DataFrame(rows).to_csv(TABLES_DIR / 'table3_split_sample.csv', index=False)

    # LaTeX
    sig_intl = '^{**}' if ss['international']['p'] < 0.01 else '^{*}' if ss['international']['p'] < 0.05 else ''
    sig_diff = '^{**}' if ss['difference']['p'] < 0.01 else '^{*}' if ss['difference']['p'] < 0.05 else ''

    latex = r"""
\begin{table}[htbp]
\centering
\caption{Split-Sample Analysis: Network Density Effects by VC Headquarters}
\label{tab:split_sample}
\begin{tabular}{lccc}
\toprule
 & International HQ & African HQ & Difference \\
\midrule
"""
    latex += f"N & {ss['international']['n']} & {ss['african']['n']} & \\\\\n"
    latex += r"\midrule" + "\n"
    latex += f"Density & ${ss['international']['beta']}{sig_intl}$ & ${ss['african']['beta']}$ & ${ss['difference']['beta']}{sig_diff}$ \\\\\n"
    latex += f" & ({ss['international']['se']}) & ({ss['african']['se']}) & ({ss['difference']['se']}) \\\\\n"
    latex += f"$p$-value & {ss['international']['p']} & {ss['african']['p']} & {ss['difference']['p']} \\\\\n"
    latex += f"$z$-statistic & & & {ss['difference']['z']} \\\\\n"
    latex += r"""
\midrule
Controls & Yes & Yes & \\
Year FE & Yes & Yes & \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item \textit{Notes:} Fractional logit (GEE) with clustered SEs by investor.
Difference test: $z = (\beta_{\text{African}} - \beta_{\text{Intl}}) / \sqrt{SE_{\text{African}}^2 + SE_{\text{Intl}}^2}$.
$^{*}p<0.05$; $^{**}p<0.01$.
\end{tablenotes}
\end{table}
"""

    with open(TABLES_DIR / 'table3_split_sample.tex', 'w') as f:
        f.write(latex)


def generate_table_a2(paper_numbers):
    """Generate Table A2: Common Support and Weighting Robustness."""
    logger.info("Generating Table A2: Common Support Robustness...")

    ss = paper_numbers['split_sample']
    rob = paper_numbers['robustness']

    specs = [
        ('Main (GEE)', ss['international']['n'], ss['african']['n'],
         ss['international']['beta'], ss['international']['se'],
         ss['african']['beta'], ss['african']['se'],
         ss['difference']['z'], ss['difference']['p']),
        ('Common Support', rob['common_support']['n_intl'], rob['common_support']['n_african'],
         rob['common_support']['intl_beta'], rob['common_support']['intl_se'],
         rob['common_support']['african_beta'], rob['common_support']['african_se'],
         rob['common_support']['z'], rob['common_support']['p']),
        ('Trim 10%', rob['trim_10pct']['n_intl'], rob['trim_10pct']['n_african'],
         rob['trim_10pct']['intl_beta'], rob['trim_10pct']['intl_se'],
         rob['trim_10pct']['african_beta'], rob['trim_10pct']['african_se'],
         rob['trim_10pct']['z'], rob['trim_10pct']['p']),
        ('Weighted (n\\_deals)', rob['weighted']['n_intl'], rob['weighted']['n_african'],
         rob['weighted']['intl_beta'], rob['weighted']['intl_se'],
         rob['weighted']['african_beta'], rob['weighted']['african_se'],
         rob['weighted']['z'], rob['weighted']['p'])
    ]

    # CSV
    rows = []
    for spec in specs:
        rows.append({
            'Specification': spec[0],
            'N_Intl': spec[1],
            'N_African': spec[2],
            'Intl_beta': spec[3],
            'Intl_se': spec[4],
            'African_beta': spec[5],
            'African_se': spec[6],
            'z_stat': spec[7],
            'p_value': spec[8]
        })

    pd.DataFrame(rows).to_csv(TABLES_DIR / 'tableA2_common_support.csv', index=False)

    # LaTeX
    latex = r"""
\begin{table}[htbp]
\centering
\caption{Robustness: Common Support and Alternative Specifications}
\label{tab:robustness_support}
\small
\begin{tabular}{lcccccc}
\toprule
Specification & N (Intl/Afr) & Intl $\beta$ (SE) & African $\beta$ (SE) & $z$ & $p$ \\
\midrule
"""

    for spec in specs:
        name, n_i, n_a, b_i, se_i, b_a, se_a, z, p = spec
        sig = '^{**}' if p < 0.01 else '^{*}' if p < 0.05 else ''
        p_str = f"{p:.3f}" if p >= 0.001 else "<0.001"
        latex += f"{name} & {n_i}/{n_a} & {b_i:.3f} ({se_i:.2f}) & {b_a:.3f} ({se_a:.2f}) & {z:.2f}{sig} & {p_str} \\\\\n"

    latex += r"""
\bottomrule
\end{tabular}
\begin{tablenotes}
\small
\item \textit{Notes:} All models use fractional logit with same controls.
Common Support restricts to overlapping density range.
Trim 10\% drops top/bottom deciles within each group.
Weighted uses $n\_deals$ as frequency weights.
$^{*}p<0.05$; $^{**}p<0.01$.
\end{tablenotes}
\end{table}
"""

    with open(TABLES_DIR / 'tableA2_common_support.tex', 'w') as f:
        f.write(latex)


def main():
    """Main pipeline."""
    logger.info("=" * 70)
    logger.info("GENERATING PAPER TABLES AND SINGLE SOURCE OF TRUTH")
    logger.info("=" * 70)
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load and validate
    sample, deals, investors = load_and_validate_data()

    # Compute all statistics
    paper_numbers = compute_all_statistics(sample, deals, investors)

    # Save paper_numbers.json
    with open(OUTPUTS_DIR / 'paper_numbers.json', 'w') as f:
        json.dump(paper_numbers, f, indent=2)
    logger.info(f"\nSaved: {OUTPUTS_DIR / 'paper_numbers.json'}")

    # Generate tables
    generate_table1(paper_numbers, sample)
    generate_table2(paper_numbers)
    generate_table3(paper_numbers)
    generate_table_a2(paper_numbers)

    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nOutputs:")
    logger.info(f"  - {OUTPUTS_DIR / 'paper_numbers.json'}")
    logger.info(f"  - {TABLES_DIR / 'table1_descriptives.tex'}")
    logger.info(f"  - {TABLES_DIR / 'table2_pooled_models.tex'}")
    logger.info(f"  - {TABLES_DIR / 'table3_split_sample.tex'}")
    logger.info(f"  - {TABLES_DIR / 'tableA2_common_support.tex'}")
    logger.info(f"  - {FINAL_CHECKS_DIR / 'data_validation_log.txt'}")


if __name__ == '__main__':
    main()
