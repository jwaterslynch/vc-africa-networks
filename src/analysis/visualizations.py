"""
Visualization Module

Creates publication-ready figures for the paper.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['figure.figsize'] = (8, 6)
plt.rcParams['figure.dpi'] = 150


def plot_interaction_effect(
    sample: pd.DataFrame,
    model,
    output_path: str = None,
    n_diversity_levels: int = 3
):
    """
    Plot marginal effect of density at different diversity levels.

    Creates visualization showing how the effect of network density
    on HRV share varies with network diversity.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Get coefficient estimates
    params = model.params

    # Density range for prediction
    density_range = np.linspace(
        sample['density_std'].min(),
        sample['density_std'].max(),
        100
    )

    # Diversity levels (low, medium, high)
    diversity_levels = np.percentile(
        sample['diversity_std'].dropna(),
        [25, 50, 75]
    )

    diversity_labels = ['Low Diversity (25th pctl)', 'Medium Diversity (50th pctl)',
                        'High Diversity (75th pctl)']
    colors = ['#e74c3c', '#95a5a6', '#2ecc71']

    # Get mean values for controls
    mean_ego = sample['log_ego_size'].mean()
    mean_exp = sample['log_experience'].mean()

    # Predict for each diversity level
    for div_level, label, color in zip(diversity_levels, diversity_labels, colors):
        # Linear predictor: const + density*b1 + diversity*b2 + interaction*b3 + controls
        eta = (
            params['const'] +
            params['density_std'] * density_range +
            params['diversity_std'] * div_level +
            params['density_x_diversity_std'] * density_range * div_level +
            params['log_ego_size'] * mean_ego +
            params['log_experience'] * mean_exp
        )

        # Transform to probability (logistic)
        prob = 1 / (1 + np.exp(-eta))

        ax.plot(density_range, prob, label=label, color=color, linewidth=2.5)

    ax.set_xlabel('Network Density (Standardized)')
    ax.set_ylabel('Predicted HRV Share')
    ax.set_title('Interaction Effect: Network Density × Diversity on HRV Investment')
    ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)

    # Add annotation about interaction
    int_coef = params['density_x_diversity_std']
    int_pval = model.pvalues['density_x_diversity_std']

    annotation = f"Interaction: β = {int_coef:.3f}"
    if int_pval < 0.001:
        annotation += "***"
    elif int_pval < 0.01:
        annotation += "**"
    elif int_pval < 0.05:
        annotation += "*"

    ax.annotate(
        annotation,
        xy=(0.05, 0.95), xycoords='axes fraction',
        fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.8)
    )

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Interaction plot saved to {output_path}")

    return fig, ax


def plot_variable_distributions(
    sample: pd.DataFrame,
    output_path: str = None
):
    """
    Plot distributions of key variables.
    """
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))

    # Density distribution
    ax = axes[0, 0]
    ax.hist(sample['ego_density'], bins=30, edgecolor='black', alpha=0.7)
    ax.axvline(sample['ego_density'].mean(), color='red', linestyle='--', label=f'Mean: {sample["ego_density"].mean():.2f}')
    ax.set_xlabel('Ego-Network Density')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Network Density')
    ax.legend()

    # Diversity distribution
    ax = axes[0, 1]
    ax.hist(sample['diversity_combined'], bins=30, edgecolor='black', alpha=0.7, color='green')
    ax.axvline(sample['diversity_combined'].mean(), color='red', linestyle='--', label=f'Mean: {sample["diversity_combined"].mean():.2f}')
    ax.set_xlabel('Network Diversity (Z-scored)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Network Diversity')
    ax.legend()

    # HRV share distribution
    ax = axes[1, 0]
    ax.hist(sample['hrv_share'], bins=20, edgecolor='black', alpha=0.7, color='orange')
    ax.axvline(sample['hrv_share'].mean(), color='red', linestyle='--', label=f'Mean: {sample["hrv_share"].mean():.2f}')
    ax.set_xlabel('HRV Share')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of HRV Share')
    ax.legend()

    # Ego size distribution
    ax = axes[1, 1]
    ax.hist(sample['ego_size'], bins=30, edgecolor='black', alpha=0.7, color='purple')
    ax.axvline(sample['ego_size'].median(), color='red', linestyle='--', label=f'Median: {sample["ego_size"].median():.0f}')
    ax.set_xlabel('Ego-Network Size (# Partners)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Network Size')
    ax.legend()

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Distribution plot saved to {output_path}")

    return fig, axes


def plot_scatter_matrix(
    sample: pd.DataFrame,
    output_path: str = None
):
    """
    Create scatter plot matrix of key variables.
    """
    vars_to_plot = ['ego_density', 'diversity_combined', 'hrv_share']
    var_labels = {
        'ego_density': 'Density',
        'diversity_combined': 'Diversity',
        'hrv_share': 'HRV Share'
    }

    fig, axes = plt.subplots(3, 3, figsize=(10, 10))

    for i, var1 in enumerate(vars_to_plot):
        for j, var2 in enumerate(vars_to_plot):
            ax = axes[i, j]

            if i == j:
                # Diagonal: histogram
                ax.hist(sample[var1].dropna(), bins=20, edgecolor='black', alpha=0.7)
                ax.set_ylabel('Frequency' if j == 0 else '')
            else:
                # Off-diagonal: scatter
                ax.scatter(sample[var2], sample[var1], alpha=0.3, s=10)

                # Add regression line
                valid = sample[[var1, var2]].dropna()
                if len(valid) > 10:
                    z = np.polyfit(valid[var2], valid[var1], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(valid[var2].min(), valid[var2].max(), 100)
                    ax.plot(x_line, p(x_line), 'r--', alpha=0.8, linewidth=2)

            # Labels
            if i == 2:
                ax.set_xlabel(var_labels[var2])
            if j == 0:
                ax.set_ylabel(var_labels[var1])

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Scatter matrix saved to {output_path}")

    return fig, axes


def plot_coefficient_comparison(
    main_model,
    robustness_models: Dict,
    output_path: str = None
):
    """
    Forest plot comparing interaction coefficient across specifications.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Collect results
    results = []

    # Main model
    if 'density_x_diversity_std' in main_model.params.index:
        results.append({
            'model': 'Main Model',
            'coef': main_model.params['density_x_diversity_std'],
            'se': main_model.bse['density_x_diversity_std'],
            'pval': main_model.pvalues['density_x_diversity_std']
        })

    # Robustness models
    for name, model in robustness_models.items():
        if model is None:
            continue
        int_vars = [v for v in model.params.index if 'x_diversity' in v.lower()]
        if int_vars:
            var = int_vars[0]
            results.append({
                'model': name.replace('_', ' '),
                'coef': model.params[var],
                'se': model.bse[var],
                'pval': model.pvalues[var]
            })

    if not results:
        return None, None

    df = pd.DataFrame(results)

    # Sort by coefficient
    df = df.sort_values('coef')

    # Plot
    y_pos = np.arange(len(df))
    colors = ['green' if p < 0.05 else 'orange' if p < 0.10 else 'gray'
              for p in df['pval']]

    ax.errorbar(
        df['coef'], y_pos,
        xerr=1.96 * df['se'],
        fmt='o', capsize=5, capthick=2,
        markersize=8, elinewidth=2,
        color='black'
    )

    # Color code by significance
    for i, (coef, color) in enumerate(zip(df['coef'], colors)):
        ax.scatter([coef], [i], color=color, s=100, zorder=5)

    ax.axvline(0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['model'])
    ax.set_xlabel('Interaction Coefficient (Density × Diversity)')
    ax.set_title('Robustness: Interaction Coefficient Across Specifications')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='p < 0.05'),
        Patch(facecolor='orange', label='p < 0.10'),
        Patch(facecolor='gray', label='p ≥ 0.10')
    ]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Coefficient comparison saved to {output_path}")

    return fig, ax
