"""
High-Risk Venture (HRV) Classification

Primary Definition: HRV = (Seed OR Series_A) AND (hard-tech sector)

CORRECTED: Fintech is NOT included in hard-tech sectors.
Hard-tech = high technological/engineering uncertainty, not market uncertainty.

Hard-tech sectors:
- Healthtech / Biotech / Medtech
- Cleantech / Energy / Climate tech
- Agritech (precision ag, not marketplace)
- Deeptech / Hardware / IoT
- AI / ML

NOT hard-tech:
- Fintech (market/regulatory uncertainty, not technological)
- E-commerce / Marketplace
- Edtech (content)
- Media / Entertainment
"""

import pandas as pd
import numpy as np
from typing import Dict, Set, List
import logging

from src.config import HARDTECH_SECTORS, EARLY_STAGES

logger = logging.getLogger(__name__)


# Sector mapping from ATBD sector names to hardtech classification
SECTOR_TO_HARDTECH = {
    # Hard-tech sectors (high technological uncertainty)
    'healthcare': True,
    'healthtech': True,
    'deeptech': True,
    'energy & water': True,
    'agriculture & food': False,  # Default false, check for precision ag
    'waste management': True,  # Often involves tech solutions

    # NOT hard-tech (market/operational uncertainty, not technological)
    'fintech': False,
    'logistics & transport': False,
    'retail': False,
    'services': False,
    'education & jobs': False,
    'telecom, media & entertainment': False,
    'housing': False,
}


def is_hardtech_sector(sector_raw: str, climate_tech: int = 0) -> bool:
    """
    Determine if deal sector is hard-tech.

    Parameters
    ----------
    sector_raw : str
        Raw sector string from ATBD
    climate_tech : int
        1 if deal is flagged as climate tech

    Returns
    -------
    bool
    """
    if pd.isna(sector_raw):
        return False

    sector_lower = str(sector_raw).strip().lower()

    # Climate tech flag overrides - these are typically hard-tech
    if climate_tech == 1:
        return True

    # Direct mapping
    if sector_lower in SECTOR_TO_HARDTECH:
        return SECTOR_TO_HARDTECH[sector_lower]

    # Check for hard-tech keywords
    hardtech_keywords = [
        'health', 'biotech', 'medtech', 'pharma', 'diagnostic',
        'clean', 'energy', 'solar', 'renewable', 'climate', 'green',
        'deeptech', 'deep tech', 'hardware', 'iot', 'robotics',
        'ai', 'machine learning', 'precision', 'agritech_precision'
    ]

    for keyword in hardtech_keywords:
        if keyword in sector_lower:
            return True

    return False


def is_early_stage(stage_std: str) -> bool:
    """Check if deal is early-stage (Seed or Series A)."""
    return stage_std in EARLY_STAGES


def classify_hrv_primary(row: pd.Series) -> bool:
    """
    Primary HRV definition: early-stage AND hard-tech.

    Apply to each deal row.
    """
    early = is_early_stage(row.get('stage_std', ''))
    hardtech = is_hardtech_sector(
        row.get('sector_raw', ''),
        row.get('climate_tech', 0)
    )
    return early and hardtech


def classify_hrv_hardtech_only(row: pd.Series) -> bool:
    """
    Robustness HRV definition: hard-tech regardless of stage.
    """
    return is_hardtech_sector(
        row.get('sector_raw', ''),
        row.get('climate_tech', 0)
    )


def classify_hrv_early_only(row: pd.Series) -> bool:
    """
    Robustness: early-stage regardless of sector.
    """
    return is_early_stage(row.get('stage_std', ''))


def apply_hrv_classifications(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all HRV classifications to deals dataframe.

    Adds columns:
    - is_hardtech: deal is in hard-tech sector
    - is_early: deal is early-stage (Seed/Series A)
    - hrv_primary: early AND hardtech
    - hrv_hardtech_only: hardtech regardless of stage
    - hrv_early_only: early regardless of sector
    """
    deals = deals.copy()

    # Sector classification
    deals['is_hardtech'] = deals.apply(
        lambda row: is_hardtech_sector(
            row.get('sector_raw', ''),
            row.get('climate_tech', 0)
        ),
        axis=1
    ).astype(int)

    # Stage classification
    deals['is_early'] = deals['stage_std'].apply(is_early_stage).astype(int)

    # HRV definitions
    deals['hrv_primary'] = (
        (deals['is_early'] == 1) & (deals['is_hardtech'] == 1)
    ).astype(int)

    deals['hrv_hardtech_only'] = deals['is_hardtech']
    deals['hrv_early_only'] = deals['is_early']

    # Log stats
    logger.info(f"HRV Classification Stats:")
    logger.info(f"  Total deals: {len(deals)}")
    logger.info(f"  Hard-tech: {deals['is_hardtech'].sum()} ({deals['is_hardtech'].mean()*100:.1f}%)")
    logger.info(f"  Early-stage: {deals['is_early'].sum()} ({deals['is_early'].mean()*100:.1f}%)")
    logger.info(f"  HRV Primary: {deals['hrv_primary'].sum()} ({deals['hrv_primary'].mean()*100:.1f}%)")

    return deals


def compute_hrv_share(
    deals: pd.DataFrame,
    deal_investors: pd.DataFrame,
    focal_vc: str,
    year: int,
    hrv_column: str = 'hrv_primary'
) -> Dict[str, float]:
    """
    Compute HRV share for focal VC in year t.

    HRV_share = (# HRV deals) / (# total deals) in year t

    Parameters
    ----------
    deals : DataFrame
        Must have hrv classification columns
    deal_investors : DataFrame
    focal_vc : str
        Investor ID
    year : int
        Focal year t
    hrv_column : str
        Which HRV column to use

    Returns
    -------
    dict with:
        - hrv_share: proportion of HRV deals
        - n_deals: total deals in year
        - n_hrv: number of HRV deals
        - n_early: number of early-stage deals
        - n_hardtech: number of hard-tech deals
    """
    # Get focal VC's deals in year t
    vc_deal_ids = deal_investors[
        deal_investors['investor_id'] == focal_vc
    ]['deal_id'].unique()

    year_deals = deals[
        (deals['deal_id'].isin(vc_deal_ids)) &
        (deals['deal_year'] == year)
    ]

    total = len(year_deals)

    if total == 0:
        return {
            'hrv_share': np.nan,
            'n_deals': 0,
            'n_hrv': 0,
            'n_early': 0,
            'n_hardtech': 0,
            'hrv_share_early_only': np.nan,
            'hrv_share_hardtech_only': np.nan
        }

    n_hrv = year_deals[hrv_column].sum() if hrv_column in year_deals.columns else 0
    n_early = year_deals['is_early'].sum() if 'is_early' in year_deals.columns else 0
    n_hardtech = year_deals['is_hardtech'].sum() if 'is_hardtech' in year_deals.columns else 0

    # Alternative HRV definitions
    hrv_early = year_deals['hrv_early_only'].sum() if 'hrv_early_only' in year_deals.columns else 0
    hrv_hardtech = year_deals['hrv_hardtech_only'].sum() if 'hrv_hardtech_only' in year_deals.columns else 0

    return {
        'hrv_share': n_hrv / total,
        'n_deals': total,
        'n_hrv': n_hrv,
        'n_early': n_early,
        'n_hardtech': n_hardtech,
        'hrv_share_early_only': hrv_early / total,
        'hrv_share_hardtech_only': hrv_hardtech / total
    }


def compute_all_hrv_measures(
    deals: pd.DataFrame,
    deal_investors: pd.DataFrame,
    panel: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute HRV measures for all VC-years in panel.

    Parameters
    ----------
    deals : DataFrame
        Must have HRV classification columns applied
    deal_investors : DataFrame
    panel : DataFrame
        Must have 'investor_id', 'year' columns

    Returns
    -------
    DataFrame with panel augmented with HRV columns
    """
    logger.info("Computing HRV measures for all VC-years...")

    records = []
    for _, row in panel.iterrows():
        vc_id = row['investor_id']
        year = row['year']

        hrv = compute_hrv_share(deals, deal_investors, vc_id, year)

        records.append({
            'investor_id': vc_id,
            'year': year,
            **hrv
        })

    hrv_df = pd.DataFrame(records)

    # Merge with panel
    result = panel.merge(
        hrv_df,
        on=['investor_id', 'year'],
        how='left'
    )

    logger.info(f"HRV measures computed for {len(result)} VC-years")

    # Summary stats
    valid_hrv = result['hrv_share'].dropna()
    if len(valid_hrv) > 0:
        logger.info(f"  HRV share: mean={valid_hrv.mean():.3f}, std={valid_hrv.std():.3f}")
        logger.info(f"  Range: [{valid_hrv.min():.3f}, {valid_hrv.max():.3f}]")

    return result
