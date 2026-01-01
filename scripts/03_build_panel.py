#!/usr/bin/env python3
"""
Panel Construction Script

Builds the VC-year panel with:
- Network measures (density, clustering)
- Diversity measures (type, geography, combined z-score)
- HRV outcomes (share of high-risk ventures)
- Control variables

Outputs to data/processed/vc_year_panel.parquet
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from src.config import (
    INTERIM_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR,
    ANALYSIS_PARAMS
)
from src.features.network_construction import (
    build_network_panel,
    build_global_coinvestment_graph,
    get_partner_list
)
from src.features.diversity_measures import (
    compute_all_diversity_measures,
    compute_diversity_composite
)
from src.features.hrv_classification import (
    apply_hrv_classifications,
    compute_all_hrv_measures
)

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'panel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def add_control_variables(
    panel: pd.DataFrame,
    deals: pd.DataFrame,
    deal_investors: pd.DataFrame,
    investors: pd.DataFrame,
    window: int = 3
) -> pd.DataFrame:
    """
    Add control variables to the panel.

    Controls:
    - experience_cumulative: total deals up to t-1
    - experience_window: deals in [t-window, t-1]
    - portfolio_concentration: sector HHI in window
    - fund_age: years since first observed deal
    - investor_hq_in_africa: focal VC HQ in Africa
    """
    logger.info("Adding control variables...")

    panel = panel.copy()

    # Merge investor attributes
    panel = panel.merge(
        investors[['investor_id', 'hq_country', 'hq_in_africa', 'hq_region']],
        on='investor_id',
        how='left'
    )

    # Compute deal-based controls
    for idx, row in panel.iterrows():
        vc_id = row['investor_id']
        year = row['year']

        # Get focal VC's deals
        vc_deal_ids = deal_investors[
            deal_investors['investor_id'] == vc_id
        ]['deal_id'].unique()

        vc_deals = deals[deals['deal_id'].isin(vc_deal_ids)]

        # Experience: cumulative deals up to t-1
        cum_deals = len(vc_deals[vc_deals['deal_year'] < year])
        panel.loc[idx, 'experience_cumulative'] = cum_deals

        # Experience: deals in window
        window_start = year - window
        window_end = year - 1
        window_deals = vc_deals[
            (vc_deals['deal_year'] >= window_start) &
            (vc_deals['deal_year'] <= window_end)
        ]
        panel.loc[idx, 'experience_window'] = len(window_deals)

        # Portfolio concentration (sector HHI in window)
        if len(window_deals) > 0:
            sector_counts = window_deals['sector_raw'].value_counts(normalize=True)
            hhi = (sector_counts ** 2).sum()
            panel.loc[idx, 'sector_concentration_hhi'] = hhi
        else:
            panel.loc[idx, 'sector_concentration_hhi'] = np.nan

        # Fund age: years since first deal
        if len(vc_deals) > 0:
            first_year = vc_deals['deal_year'].min()
            panel.loc[idx, 'fund_age'] = year - first_year
        else:
            panel.loc[idx, 'fund_age'] = 0

    return panel


def run_stop_go_checks(panel: pd.DataFrame) -> dict:
    """
    Run stop/go criteria checks.

    Returns dict of check results.
    """
    logger.info("="*60)
    logger.info("STOP/GO CRITERIA CHECKS")
    logger.info("="*60)

    checks = {}

    # 1. Sample size
    n_obs = len(panel)
    checks['n_observations'] = n_obs
    checks['n_observations_pass'] = n_obs >= 100
    logger.info(f"N (VC-years): {n_obs} {'✅' if n_obs >= 100 else '❌'} (need ≥100)")

    # 2. Unique VCs
    n_vcs = panel['investor_id'].nunique()
    checks['n_unique_vcs'] = n_vcs
    logger.info(f"Unique VCs: {n_vcs}")

    # 3. Years covered
    years = sorted(panel['year'].unique())
    n_years = len(years)
    checks['years_covered'] = years
    checks['n_years'] = n_years
    checks['years_pass'] = n_years >= 3
    logger.info(f"Years: {years} {'✅' if n_years >= 3 else '❌'} (need ≥3)")

    # 4. Density variance
    density_valid = panel['ego_density'].dropna()
    density_var = density_valid.var()
    checks['density_variance'] = density_var
    checks['density_pass'] = density_var > 0.01
    logger.info(f"Density variance: {density_var:.4f} {'✅' if density_var > 0.01 else '❌'} (need >0.01)")
    logger.info(f"  Density range: [{density_valid.min():.3f}, {density_valid.max():.3f}]")
    logger.info(f"  Density mean: {density_valid.mean():.3f}")

    # 5. Diversity variance
    div_valid = panel['diversity_combined'].dropna()
    div_var = div_valid.var()
    checks['diversity_variance'] = div_var
    checks['diversity_pass'] = div_var > 0.01
    logger.info(f"Diversity variance: {div_var:.4f} {'✅' if div_var > 0.01 else '❌'} (need >0.01)")
    logger.info(f"  Diversity range: [{div_valid.min():.3f}, {div_valid.max():.3f}]")

    # 6. HRV variance
    hrv_valid = panel['hrv_share'].dropna()
    hrv_var = hrv_valid.var()
    checks['hrv_variance'] = hrv_var
    checks['hrv_pass'] = hrv_var > 0.01
    logger.info(f"HRV share variance: {hrv_var:.4f} {'✅' if hrv_var > 0.01 else '❌'} (need >0.01)")
    logger.info(f"  HRV share range: [{hrv_valid.min():.3f}, {hrv_valid.max():.3f}]")
    logger.info(f"  HRV share mean: {hrv_valid.mean():.3f}")

    # 7. Median ego size
    median_ego = panel['ego_size'].median()
    checks['median_ego_size'] = median_ego
    checks['ego_size_pass'] = median_ego >= 3
    logger.info(f"Median ego size: {median_ego:.1f} {'✅' if median_ego >= 3 else '⚠️'} (want ≥3)")

    # 8. Missing data
    for col in ['ego_density', 'diversity_combined', 'hrv_share']:
        pct_missing = panel[col].isna().mean() * 100
        logger.info(f"  {col} missing: {pct_missing:.1f}%")

    # Overall verdict
    all_pass = all([
        checks['n_observations_pass'],
        checks['years_pass'],
        checks['density_pass'],
        checks['diversity_pass'],
        checks['hrv_pass']
    ])

    checks['all_pass'] = all_pass

    logger.info("="*60)
    if all_pass:
        logger.info("✅ ALL STOP/GO CHECKS PASSED - PROCEED TO ANALYSIS")
    else:
        logger.warning("❌ SOME CHECKS FAILED - REVIEW BEFORE PROCEEDING")
    logger.info("="*60)

    return checks


def main():
    """Main panel construction pipeline."""
    logger.info("="*60)
    logger.info("PANEL CONSTRUCTION PIPELINE")
    logger.info("="*60)

    # Load interim data
    logger.info("Loading interim data...")
    deals = pd.read_parquet(INTERIM_DATA_DIR / 'deals.parquet')
    investors = pd.read_parquet(INTERIM_DATA_DIR / 'investors.parquet')
    deal_investors = pd.read_parquet(INTERIM_DATA_DIR / 'deal_investors.parquet')

    logger.info(f"  Deals: {len(deals)}")
    logger.info(f"  Investors: {len(investors)}")
    logger.info(f"  Deal-investor links: {len(deal_investors)}")

    # Apply HRV classifications to deals
    logger.info("Applying HRV classifications...")
    deals = apply_hrv_classifications(deals)

    # Analysis parameters
    analysis_years = ANALYSIS_PARAMS['analysis_years']
    window = ANALYSIS_PARAMS['network_window']
    min_ego_size = ANALYSIS_PARAMS['min_ego_size']

    logger.info(f"Analysis years: {analysis_years}")
    logger.info(f"Network window: {window} years")
    logger.info(f"Min ego size: {min_ego_size}")

    # Step 1: Build network panel
    logger.info("\n--- Step 1: Building network panel ---")
    network_panel, graphs = build_network_panel(
        deal_investors, deals,
        years=analysis_years,
        window=window,
        min_ego_size=min_ego_size
    )

    if len(network_panel) == 0:
        logger.error("No VC-years in network panel. Check data.")
        return None

    # Step 2: Add diversity measures
    logger.info("\n--- Step 2: Computing diversity measures ---")
    panel = compute_all_diversity_measures(
        deal_investors, deals, investors,
        network_panel,
        window=window
    )

    # Step 3: Add HRV measures
    logger.info("\n--- Step 3: Computing HRV measures ---")
    panel = compute_all_hrv_measures(deals, deal_investors, panel)

    # Step 4: Add control variables
    logger.info("\n--- Step 4: Adding control variables ---")
    panel = add_control_variables(
        panel, deals, deal_investors, investors,
        window=window
    )

    # Step 5: Create interaction term
    logger.info("\n--- Step 5: Creating interaction term ---")
    # Z-score density for interaction
    panel['density_z'] = (
        panel['ego_density'] - panel['ego_density'].mean()
    ) / panel['ego_density'].std()

    # Interaction = density_z * diversity_combined
    panel['density_x_diversity'] = panel['density_z'] * panel['diversity_combined']

    # Step 6: Stop/go checks
    logger.info("\n--- Step 6: Running stop/go checks ---")
    checks = run_stop_go_checks(panel)

    # Save outputs
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("\nSaving outputs...")
    panel.to_parquet(PROCESSED_DATA_DIR / 'vc_year_panel.parquet', index=False)
    panel.to_csv(PROCESSED_DATA_DIR / 'vc_year_panel.csv', index=False)

    # Save deals with HRV classifications
    deals.to_parquet(PROCESSED_DATA_DIR / 'deals_with_hrv.parquet', index=False)

    # Save stop/go report
    import json
    with open(PROCESSED_DATA_DIR / 'stop_go_checks.json', 'w') as f:
        json.dump(checks, f, indent=2, default=str)

    logger.info(f"  Saved vc_year_panel.parquet: {len(panel)} rows")
    logger.info(f"  Saved stop_go_checks.json")

    # Print summary
    print("\n" + "="*60)
    print("PANEL SUMMARY")
    print("="*60)
    print(f"Observations: {len(panel)}")
    print(f"Unique VCs: {panel['investor_id'].nunique()}")
    print(f"Years: {sorted(panel['year'].unique())}")
    print("\nVariable distributions:")
    print(panel[['ego_density', 'diversity_combined', 'hrv_share']].describe())

    return panel, checks


if __name__ == '__main__':
    main()
