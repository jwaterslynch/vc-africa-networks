"""
Diversity Measures Module

Computes Blau indices for investor-type and geographic diversity.

CRITICAL: Geographic diversity is computed DYNAMICALLY based on
focal VC's primary market, not as a static investor attribute.

Final diversity composite = z-scored average of type and geo diversity.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set
import logging

from src.config import AFRICAN_COUNTRIES

logger = logging.getLogger(__name__)


def blau_index(categories: List[str]) -> float:
    """
    Compute Blau index of heterogeneity.

    Blau = 1 - sum(p_i^2) where p_i is proportion in category i

    Range: [0, 1] where 0 = complete homogeneity,
                        1 approaches max diversity

    Returns NaN if empty list.
    """
    if len(categories) == 0:
        return np.nan

    # Filter out None/NaN values
    valid_categories = [c for c in categories if pd.notna(c) and c != '']
    if len(valid_categories) == 0:
        return np.nan

    counts = pd.Series(valid_categories).value_counts(normalize=True)
    return 1 - (counts ** 2).sum()


def get_focal_vc_primary_market(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3
) -> Optional[str]:
    """
    Determine focal VC's primary Africa market.

    Primary market = modal country of deals in [year-window, year-1].

    Parameters
    ----------
    deal_investors : DataFrame
    deals : DataFrame
    focal_vc : str
        Investor ID
    year : int
        Focal year t
    window : int
        Lookback window

    Returns
    -------
    str : ISO country code, 'MULTI' if tied, or None if no deals
    """
    window_start = year - window
    window_end = year - 1

    # Get focal VC's deals in window
    focal_deals = deal_investors[
        deal_investors['investor_id'] == focal_vc
    ]['deal_id'].unique()

    deals_in_window = deals[
        (deals['deal_id'].isin(focal_deals)) &
        (deals['deal_year'] >= window_start) &
        (deals['deal_year'] <= window_end)
    ]

    if len(deals_in_window) == 0:
        return None

    # Find modal country
    country_counts = deals_in_window['country_primary_ops'].value_counts()

    if len(country_counts) == 0:
        return None

    # Check for ties
    max_count = country_counts.max()
    top_countries = country_counts[country_counts == max_count].index.tolist()

    if len(top_countries) == 1:
        return top_countries[0]
    else:
        # Tie-breaker: use country of earliest deal
        earliest = deals_in_window.sort_values('deal_date').iloc[0]['country_primary_ops']
        return earliest


def classify_partner_geography(
    partner_hq_country: str,
    partner_hq_in_africa: int,
    focal_primary_market: str,
    african_countries: Set[str] = None
) -> str:
    """
    Classify partner as Local, Regional, or International
    relative to focal VC's primary market.

    Parameters
    ----------
    partner_hq_country : str
        ISO code of partner's HQ
    partner_hq_in_africa : int
        1 if partner HQ in Africa
    focal_primary_market : str
        Focal VC's primary Africa market (ISO code)
    african_countries : set
        Set of African ISO codes

    Returns
    -------
    str : 'Local', 'Regional', 'International', or 'Unknown'
    """
    if african_countries is None:
        african_countries = set(AFRICAN_COUNTRIES)

    if focal_primary_market is None or pd.isna(focal_primary_market):
        return 'Unknown'

    if pd.isna(partner_hq_country):
        return 'Unknown'

    if partner_hq_country == focal_primary_market:
        return 'Local'
    elif partner_hq_in_africa == 1 or partner_hq_country in african_countries:
        return 'Regional'
    else:
        return 'International'


def compute_diversity_measures(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    investors: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3,
    partner_ids: List[str] = None
) -> Dict[str, float]:
    """
    Compute diversity measures for focal VC-year.

    Parameters
    ----------
    deal_investors : DataFrame
    deals : DataFrame
    investors : DataFrame
    focal_vc : str
        Investor ID
    year : int
        Focal year t
    window : int
        Lookback window
    partner_ids : list, optional
        Pre-computed list of partner IDs (from network construction)
        If None, will compute from deal_investors

    Returns
    -------
    dict with keys:
        - diversity_type: Blau index over investor types
        - diversity_geo: Blau index over Local/Regional/International
        - n_partners: number of partners used for diversity
        - pct_local: % of partners that are Local
        - pct_regional: % Regional
        - pct_international: % International
        - focal_primary_market: focal VC's primary market
    """
    african_countries = set(AFRICAN_COUNTRIES)

    # Get partners if not provided
    if partner_ids is None:
        window_start = year - window
        window_end = year - 1

        # Get focal VC's deals in window
        focal_deals = deal_investors[
            deal_investors['investor_id'] == focal_vc
        ]['deal_id'].unique()

        window_deal_ids = deals[
            (deals['deal_id'].isin(focal_deals)) &
            (deals['deal_year'] >= window_start) &
            (deals['deal_year'] <= window_end)
        ]['deal_id'].unique()

        # Get co-investors (partners)
        partner_ids = deal_investors[
            (deal_investors['deal_id'].isin(window_deal_ids)) &
            (deal_investors['investor_id'] != focal_vc)
        ]['investor_id'].unique().tolist()

    if len(partner_ids) == 0:
        return {
            'diversity_type': np.nan,
            'diversity_geo': np.nan,
            'n_partners': 0,
            'pct_local': np.nan,
            'pct_regional': np.nan,
            'pct_international': np.nan,
            'focal_primary_market': None
        }

    # Get partner attributes
    partner_info = investors[investors['investor_id'].isin(partner_ids)].copy()

    if len(partner_info) == 0:
        return {
            'diversity_type': np.nan,
            'diversity_geo': np.nan,
            'n_partners': 0,
            'pct_local': np.nan,
            'pct_regional': np.nan,
            'pct_international': np.nan,
            'focal_primary_market': None
        }

    # Type diversity (using investor type if available, else HQ region as proxy)
    # Note: ATBD doesn't have explicit investor type, use HQ region as proxy
    if 'hq_region' in partner_info.columns:
        types = partner_info['hq_region'].tolist()
    else:
        types = partner_info['hq_country'].tolist()

    diversity_type = blau_index(types)

    # Geographic diversity (computed dynamically)
    focal_market = get_focal_vc_primary_market(
        deal_investors, deals, focal_vc, year, window
    )

    geo_classes = []
    for _, row in partner_info.iterrows():
        geo = classify_partner_geography(
            row.get('hq_country'),
            row.get('hq_in_africa', 0),
            focal_market,
            african_countries
        )
        geo_classes.append(geo)

    diversity_geo = blau_index(geo_classes)

    # Percentages
    geo_series = pd.Series(geo_classes)
    total = len(geo_series)

    pct_local = (geo_series == 'Local').sum() / total if total > 0 else np.nan
    pct_regional = (geo_series == 'Regional').sum() / total if total > 0 else np.nan
    pct_international = (geo_series == 'International').sum() / total if total > 0 else np.nan

    return {
        'diversity_type': diversity_type,
        'diversity_geo': diversity_geo,
        'n_partners': len(partner_ids),
        'pct_local': pct_local,
        'pct_regional': pct_regional,
        'pct_international': pct_international,
        'focal_primary_market': focal_market
    }


def compute_diversity_composite(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Compute z-scored diversity composite.

    diversity_combined = (z(diversity_type) + z(diversity_geo)) / 2

    This is computed at the PANEL level after all VC-year observations.

    Parameters
    ----------
    panel : DataFrame
        Must have columns 'diversity_type' and 'diversity_geo'

    Returns
    -------
    DataFrame with added columns:
        - diversity_type_z: z-scored type diversity
        - diversity_geo_z: z-scored geographic diversity
        - diversity_combined: average of z-scores
    """
    panel = panel.copy()

    # Z-score each component (handling NaN)
    def zscore(x):
        valid = x.dropna()
        if len(valid) < 2:
            return pd.Series(np.nan, index=x.index)
        return (x - valid.mean()) / valid.std()

    panel['diversity_type_z'] = zscore(panel['diversity_type'])
    panel['diversity_geo_z'] = zscore(panel['diversity_geo'])

    # Combined = average of z-scores
    panel['diversity_combined'] = (
        panel['diversity_type_z'] + panel['diversity_geo_z']
    ) / 2

    return panel


def compute_all_diversity_measures(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    investors: pd.DataFrame,
    network_panel: pd.DataFrame,
    window: int = 3
) -> pd.DataFrame:
    """
    Compute diversity measures for all VC-years in network panel.

    Uses partner lists from network construction (more efficient than
    recomputing from deal_investors).

    Parameters
    ----------
    deal_investors : DataFrame
    deals : DataFrame
    investors : DataFrame
    network_panel : DataFrame
        Must have columns 'investor_id', 'year'
    window : int

    Returns
    -------
    DataFrame with network panel augmented with diversity columns
    """
    logger.info("Computing diversity measures for all VC-years...")

    from src.features.network_construction import (
        build_global_coinvestment_graph,
        get_partner_list
    )

    # Cache graphs by year
    graphs = {}

    records = []
    for _, row in network_panel.iterrows():
        vc_id = row['investor_id']
        year = row['year']

        # Get or build graph for this year
        if year not in graphs:
            graphs[year] = build_global_coinvestment_graph(
                deal_investors, deals, year, window
            )

        # Get partner list from graph
        partners = get_partner_list(graphs[year], vc_id)

        # Compute diversity
        diversity = compute_diversity_measures(
            deal_investors, deals, investors,
            vc_id, year, window,
            partner_ids=partners
        )

        records.append({
            'investor_id': vc_id,
            'year': year,
            **diversity
        })

    diversity_df = pd.DataFrame(records)

    # Merge with network panel
    panel = network_panel.merge(
        diversity_df,
        on=['investor_id', 'year'],
        how='left'
    )

    # Add z-scored composite
    panel = compute_diversity_composite(panel)

    logger.info(f"Diversity measures computed for {len(panel)} VC-years")

    return panel
