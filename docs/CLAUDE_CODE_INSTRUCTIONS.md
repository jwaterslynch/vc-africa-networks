# Claude Code Project Setup Instructions
## VC Social Networks and High-Risk Venture Investment in Africa (2015-2024)

**Project:** AIB Africa 2026 Submission  
**Deadline:** February 2026  
**Principal Investigator:** Jules  

---

## 1. PROJECT OVERVIEW

### 1.1 Research Question
How do VC network structure (density) and composition (diversity) interact to shape investment in high-risk ventures (HRV) in African markets?

### 1.2 Core Hypothesis
Network density amplifies the effect of network diversity on HRV investment — dense, diverse networks provide both trust infrastructure AND heterogeneous information, enabling risk-taking.

### 1.3 Data Requirements
- **Unit of analysis:** VC-year (focal VC × calendar year)
- **Time window:** 2015–2024 (10 years)
- **Geography:** African startup ecosystem
- **Key variables:**
  - DV: HRV share (proportion of deals that are early-stage + hard-tech)
  - IV1: Network density (ego-network from t-3 to t-1 co-investments)
  - IV2: Network diversity (Blau index over partner types/geographies)
  - IV3: Density × Diversity interaction

---

## 2. REPOSITORY STRUCTURE

Create the following directory structure:

```
vc-africa-networks/
│
├── README.md                    # Project overview and quick start
├── CODEBOOK.md                  # Variable definitions (copy from governance docs)
├── PRE_ANALYSIS_PLAN.md         # Hypotheses and analysis specification
├── requirements.txt             # Python dependencies
├── environment.yml              # Conda environment (alternative)
│
├── data/
│   ├── raw/                     # Original data files (NEVER modify)
│   │   ├── .gitkeep
│   │   └── README.md            # Data provenance notes
│   │
│   ├── processed/               # Cleaned, standardized data
│   │   ├── deals.parquet
│   │   ├── investors.parquet
│   │   ├── deal_investors.parquet
│   │   └── vc_year_panel.parquet
│   │
│   ├── interim/                 # Intermediate processing outputs
│   │   └── .gitkeep
│   │
│   └── external/                # Reference data (taxonomies, lookups)
│       ├── sector_taxonomy.csv
│       ├── stage_taxonomy.csv
│       ├── investor_types.csv
│       └── country_codes.csv
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/                    # Data processing modules
│   │   ├── __init__.py
│   │   ├── load_raw.py          # Load raw data files
│   │   ├── clean_deals.py       # Deal-level cleaning
│   │   ├── clean_investors.py   # Investor entity resolution
│   │   ├── standardize.py       # Map to taxonomies
│   │   └── validate.py          # Data quality checks
│   │
│   ├── features/                # Feature engineering
│   │   ├── __init__.py
│   │   ├── network_measures.py  # Density, centrality, components
│   │   ├── diversity_measures.py # Blau indices, geographic diversity
│   │   ├── hrv_classification.py # HRV primary/robustness definitions
│   │   └── build_panel.py       # Construct VC-year panel
│   │
│   ├── analysis/                # Statistical analysis
│   │   ├── __init__.py
│   │   ├── descriptives.py      # Summary statistics
│   │   ├── main_models.py       # Primary regression specifications
│   │   ├── robustness.py        # R1-R17 robustness checks
│   │   └── visualizations.py    # Figures for paper
│   │
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── logging_config.py
│       └── helpers.py
│
├── notebooks/                   # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_network_visualization.ipynb
│   ├── 03_descriptive_stats.ipynb
│   └── 04_model_results.ipynb
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_data_cleaning.py
│   ├── test_network_measures.py
│   └── test_hrv_classification.py
│
├── outputs/
│   ├── tables/                  # Regression tables (LaTeX/Word)
│   ├── figures/                 # Publication-ready figures
│   └── logs/                    # Processing logs
│
├── docs/
│   ├── data_diary.md            # Running log of data decisions
│   ├── entity_resolution_log.md # Investor merge/split decisions
│   └── variable_construction.md # Detailed variable notes
│
└── scripts/
    ├── 01_ingest_raw_data.py
    ├── 02_clean_and_standardize.py
    ├── 03_build_networks.py
    ├── 04_construct_panel.py
    ├── 05_run_analysis.py
    └── run_all.sh               # Master execution script
```

---

## 3. KEY DATA SCHEMAS

### 3.1 deals.parquet Schema

| Column | Type | Description |
|--------|------|-------------|
| deal_id | str | Unique identifier (format: YYYY-NNNN) |
| company_id | str | Company identifier |
| company_name | str | Company name |
| deal_date | date | Date of deal announcement |
| deal_year | int | Year (2015-2024) |
| country_primary_ops | str | ISO 3166-1 alpha-2 code |
| sector_tags_raw | str | Original sector labels (pipe-delimited) |
| sector_tags_std | str | Standardized to taxonomy |
| stage_raw | str | Original stage label |
| stage_std | str | Standardized: Seed, Series_A, Series_B, Series_C, Growth, Other |
| stage_inferred | bool | True if stage was inferred (not explicit) |
| stage_inference_rule | str | Rule used for inference (if applicable) |
| amount_usd | float | Deal amount in USD (null if undisclosed) |
| amount_disclosed | bool | Whether amount was publicly disclosed |
| hrv_primary | bool | Primary HRV definition: (Seed OR Series_A) AND hard-tech |
| hrv_hardtech | bool | Robustness: hard-tech regardless of stage |
| source_primary | str | Primary data source |
| source_secondary | str | Secondary verification source |
| notes | str | Any notes or flags |

### 3.2 investors.parquet Schema

| Column | Type | Description |
|--------|------|-------------|
| investor_id | str | Unique identifier (format: INV-NNNN) |
| investor_name_raw | str | Original name as found in source |
| investor_name_canonical | str | Standardized canonical name |
| investor_type | str | VC_Local, VC_Regional, VC_International, CVC, Angel, DFI, Accelerator, Other |
| hq_country | str | ISO code of headquarters |
| hq_in_africa | bool | True if HQ in African country |
| diaspora_flag | bool | True if diaspora-focused fund |
| website | str | Investor website URL |
| classification_confidence | str | high, medium, low |
| merge_notes | str | Notes on entity resolution |

### 3.3 deal_investors.parquet Schema

| Column | Type | Description |
|--------|------|-------------|
| deal_id | str | Foreign key to deals |
| investor_id | str | Foreign key to investors |
| role | str | lead, co-lead, participant, unknown |
| source_for_participation | str | Source confirming participation |

---

## 4. CORE ALGORITHMS

### 4.1 Network Construction (src/features/network_measures.py)

```python
"""
Network Measures Module

For each focal VC i in year t:
1. Identify all deals VC i participated in during years [t-3, t-1]
2. Find all co-investors in those deals
3. Construct ego-network where:
   - Nodes = co-investors
   - Edge exists if two investors co-invested in at least one deal
4. Compute measures on this ego-network
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List

def get_coinvestment_window(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3
) -> pd.DataFrame:
    """
    Get all deals involving focal VC in the [year-window, year-1] period.
    
    Parameters
    ----------
    deal_investors : DataFrame with deal_id, investor_id
    deals : DataFrame with deal_id, deal_year
    focal_vc : str, investor_id of focal VC
    year : int, focal year t
    window : int, lookback window (default 3 years)
    
    Returns
    -------
    DataFrame of deals in the window
    """
    # Merge to get years
    di_with_year = deal_investors.merge(
        deals[['deal_id', 'deal_year']], 
        on='deal_id'
    )
    
    # Filter to focal VC's deals in window
    focal_deals = di_with_year[
        (di_with_year['investor_id'] == focal_vc) &
        (di_with_year['deal_year'] >= year - window) &
        (di_with_year['deal_year'] < year)
    ]['deal_id'].unique()
    
    return di_with_year[di_with_year['deal_id'].isin(focal_deals)]


def build_ego_network(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3,
    weighted: bool = False
) -> nx.Graph:
    """
    Build ego-network for focal VC based on co-investments.
    
    Edges connect investors who co-invested in at least one deal.
    If weighted=True, edge weight = number of shared deals.
    """
    window_deals = get_coinvestment_window(
        deal_investors, deals, focal_vc, year, window
    )
    
    if len(window_deals) == 0:
        return nx.Graph()
    
    # Get all co-investors (excluding focal)
    partners = window_deals[
        window_deals['investor_id'] != focal_vc
    ]['investor_id'].unique()
    
    if len(partners) == 0:
        return nx.Graph()
    
    # Build co-investment edges
    G = nx.Graph()
    G.add_nodes_from(partners)
    
    # For each deal, add edges between all participant pairs
    for deal_id in window_deals['deal_id'].unique():
        participants = window_deals[
            (window_deals['deal_id'] == deal_id) &
            (window_deals['investor_id'] != focal_vc)
        ]['investor_id'].tolist()
        
        for i, inv1 in enumerate(participants):
            for inv2 in participants[i+1:]:
                if G.has_edge(inv1, inv2):
                    if weighted:
                        G[inv1][inv2]['weight'] += 1
                else:
                    G.add_edge(inv1, inv2, weight=1)
    
    return G


def compute_density(G: nx.Graph) -> float:
    """
    Compute network density.
    
    Density = 2E / (N * (N-1)) where E = edges, N = nodes
    
    Returns 0 if fewer than 2 nodes.
    """
    n = G.number_of_nodes()
    if n < 2:
        return np.nan  # Undefined for isolates
    
    return nx.density(G)


def compute_network_measures(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3
) -> Dict[str, float]:
    """
    Compute all network measures for a focal VC-year.
    
    Returns
    -------
    dict with keys:
        - ego_size: number of unique co-investors (k)
        - density: network density
        - density_weighted: weighted density (if repeated ties)
        - avg_clustering: average clustering coefficient
        - n_components: number of connected components
        - in_giant_component: fraction of nodes in largest component
    """
    G = build_ego_network(deal_investors, deals, focal_vc, year, window)
    G_weighted = build_ego_network(
        deal_investors, deals, focal_vc, year, window, weighted=True
    )
    
    n = G.number_of_nodes()
    
    if n == 0:
        return {
            'ego_size': 0,
            'density': np.nan,
            'density_weighted': np.nan,
            'avg_clustering': np.nan,
            'n_components': 0,
            'in_giant_component': np.nan
        }
    
    # Basic measures
    density = compute_density(G)
    
    # Weighted density: sum(weights) / max_possible_edges
    if n >= 2:
        total_weight = sum(d['weight'] for _, _, d in G_weighted.edges(data=True))
        max_edges = n * (n - 1) / 2
        density_weighted = total_weight / max_edges if max_edges > 0 else np.nan
    else:
        density_weighted = np.nan
    
    # Clustering
    avg_clustering = nx.average_clustering(G) if n >= 2 else np.nan
    
    # Components
    if n > 0:
        components = list(nx.connected_components(G))
        n_components = len(components)
        largest = max(len(c) for c in components)
        in_giant = largest / n
    else:
        n_components = 0
        in_giant = np.nan
    
    return {
        'ego_size': n,
        'density': density,
        'density_weighted': density_weighted,
        'avg_clustering': avg_clustering,
        'n_components': n_components,
        'in_giant_component': in_giant
    }
```

### 4.2 Diversity Measures (src/features/diversity_measures.py)

```python
"""
Diversity Measures Module

Computes Blau indices for investor-type and geographic diversity.

CRITICAL: Geographic diversity must be computed DYNAMICALLY based on
focal VC's primary market, not as a static investor attribute.
"""

import pandas as pd
import numpy as np
from typing import Dict, List

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
    
    counts = pd.Series(categories).value_counts(normalize=True)
    return 1 - sum(counts ** 2)


def get_focal_vc_primary_market(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    focal_vc: str,
    year: int,
    window: int = 3
) -> str:
    """
    Determine focal VC's primary Africa market.
    
    Primary market = modal country of deals in [year-window, year-1].
    
    Returns ISO country code or 'MULTI' if tied.
    """
    # Get focal VC's deals in window
    di_with_year = deal_investors.merge(
        deals[['deal_id', 'deal_year', 'country_primary_ops']], 
        on='deal_id'
    )
    
    focal_deals = di_with_year[
        (di_with_year['investor_id'] == focal_vc) &
        (di_with_year['deal_year'] >= year - window) &
        (di_with_year['deal_year'] < year)
    ]
    
    if len(focal_deals) == 0:
        return None
    
    # Find modal country
    country_counts = focal_deals['country_primary_ops'].value_counts()
    
    if len(country_counts) == 0:
        return None
    
    # Check for ties
    max_count = country_counts.max()
    top_countries = country_counts[country_counts == max_count].index.tolist()
    
    if len(top_countries) == 1:
        return top_countries[0]
    else:
        return 'MULTI'  # Tied - flag for review


def classify_partner_geography(
    partner_hq_country: str,
    partner_hq_in_africa: bool,
    focal_primary_market: str,
    african_countries: List[str]
) -> str:
    """
    Classify partner as Local, Regional, or International
    relative to focal VC's primary market.
    
    - Local: Same country as focal VC's primary market
    - Regional: Different African country
    - International: Outside Africa
    """
    if focal_primary_market is None:
        return 'Unknown'
    
    if partner_hq_country == focal_primary_market:
        return 'Local'
    elif partner_hq_in_africa or partner_hq_country in african_countries:
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
    african_countries: List[str] = None
) -> Dict[str, float]:
    """
    Compute diversity measures for focal VC-year.
    
    Returns
    -------
    dict with keys:
        - diversity_type: Blau index over investor types
        - diversity_geo: Blau index over Local/Regional/International
        - diversity_combined: Product of type and geo diversity
        - pct_local: % of partners that are Local
        - pct_regional: % Regional
        - pct_international: % International
    """
    if african_countries is None:
        # Default African ISO codes
        african_countries = [
            'DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CV', 'CM', 'CF', 'TD',
            'KM', 'CG', 'CD', 'CI', 'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET',
            'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'LY', 'MG',
            'MW', 'ML', 'MR', 'MU', 'MA', 'MZ', 'NA', 'NE', 'NG', 'RW',
            'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG',
            'TN', 'UG', 'ZM', 'ZW'
        ]
    
    # Get co-investors from window
    di_with_year = deal_investors.merge(
        deals[['deal_id', 'deal_year']], 
        on='deal_id'
    )
    
    focal_deals = di_with_year[
        (di_with_year['investor_id'] == focal_vc) &
        (di_with_year['deal_year'] >= year - window) &
        (di_with_year['deal_year'] < year)
    ]['deal_id'].unique()
    
    partners = di_with_year[
        (di_with_year['deal_id'].isin(focal_deals)) &
        (di_with_year['investor_id'] != focal_vc)
    ]['investor_id'].unique()
    
    if len(partners) == 0:
        return {
            'diversity_type': np.nan,
            'diversity_geo': np.nan,
            'diversity_combined': np.nan,
            'pct_local': np.nan,
            'pct_regional': np.nan,
            'pct_international': np.nan
        }
    
    # Get partner attributes
    partner_info = investors[investors['investor_id'].isin(partners)].copy()
    
    # Type diversity
    types = partner_info['investor_type'].tolist()
    diversity_type = blau_index(types)
    
    # Geographic diversity (computed dynamically)
    focal_market = get_focal_vc_primary_market(
        deal_investors, deals, focal_vc, year, window
    )
    
    geo_classes = []
    for _, row in partner_info.iterrows():
        geo = classify_partner_geography(
            row['hq_country'],
            row['hq_in_africa'],
            focal_market,
            african_countries
        )
        geo_classes.append(geo)
    
    diversity_geo = blau_index(geo_classes)
    
    # Combined diversity
    if pd.notna(diversity_type) and pd.notna(diversity_geo):
        diversity_combined = diversity_type * diversity_geo
    else:
        diversity_combined = np.nan
    
    # Percentages
    geo_series = pd.Series(geo_classes)
    total = len(geo_series)
    
    return {
        'diversity_type': diversity_type,
        'diversity_geo': diversity_geo,
        'diversity_combined': diversity_combined,
        'pct_local': (geo_series == 'Local').sum() / total,
        'pct_regional': (geo_series == 'Regional').sum() / total,
        'pct_international': (geo_series == 'International').sum() / total
    }
```

### 4.3 HRV Classification (src/features/hrv_classification.py)

```python
"""
High-Risk Venture (HRV) Classification

Primary Definition: HRV = (Seed OR Series_A) AND (hard-tech sector tag)

Hard-tech sectors (high technological uncertainty):
- Fintech (infrastructure/payments, not lending)
- Healthtech / Medtech
- Cleantech / Energy
- Agritech (precision ag, not marketplace)
- Logistics (tech-enabled, not asset-heavy)
- AI / ML
- Hardware
- Biotech
- Spacetech

Soft-tech sectors (lower technological uncertainty):
- E-commerce / Marketplace
- Media / Entertainment
- Edtech (content, not platform)
- HR / Recruitment
- Real Estate / Proptech (marketplace)
- Social platforms
"""

import pandas as pd
import numpy as np
from typing import List, Set

# Hard-tech sector tags (standardized)
HARDTECH_SECTORS: Set[str] = {
    'fintech_infrastructure',
    'fintech_payments',
    'fintech_banking',
    'healthtech',
    'medtech',
    'biotech',
    'cleantech',
    'energy',
    'renewables',
    'agritech_precision',
    'agritech_iot',
    'logistics_tech',
    'supply_chain',
    'ai',
    'ml',
    'hardware',
    'iot',
    'spacetech',
    'deeptech'
}

# Early stages
EARLY_STAGES: Set[str] = {'Seed', 'Series_A'}


def is_hardtech(sector_tags_std: str) -> bool:
    """
    Check if deal has any hard-tech sector tag.
    
    sector_tags_std is pipe-delimited string (e.g., "fintech_payments|ai")
    """
    if pd.isna(sector_tags_std) or sector_tags_std == '':
        return False
    
    tags = set(sector_tags_std.lower().split('|'))
    return len(tags & HARDTECH_SECTORS) > 0


def is_early_stage(stage_std: str) -> bool:
    """Check if deal is early-stage (Seed or Series A)."""
    return stage_std in EARLY_STAGES


def classify_hrv_primary(row: pd.Series) -> bool:
    """
    Primary HRV definition: early-stage AND hard-tech.
    
    Apply to each deal row.
    """
    early = is_early_stage(row['stage_std'])
    hardtech = is_hardtech(row['sector_tags_std'])
    return early and hardtech


def classify_hrv_hardtech(row: pd.Series) -> bool:
    """
    Robustness HRV definition: hard-tech regardless of stage.
    """
    return is_hardtech(row['sector_tags_std'])


def apply_hrv_classifications(deals: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all HRV classifications to deals dataframe.
    
    Adds columns:
    - hrv_primary: main definition
    - hrv_hardtech: robustness (any stage)
    """
    deals = deals.copy()
    deals['hrv_primary'] = deals.apply(classify_hrv_primary, axis=1)
    deals['hrv_hardtech'] = deals.apply(classify_hrv_hardtech, axis=1)
    return deals


def compute_hrv_share(
    deals: pd.DataFrame,
    deal_investors: pd.DataFrame,
    focal_vc: str,
    year: int,
    hrv_column: str = 'hrv_primary'
) -> float:
    """
    Compute HRV share for focal VC in year t.
    
    HRV_share = (# HRV deals) / (# total deals) in year t
    
    Returns NaN if no deals in year.
    """
    # Get focal VC's deals in year t
    vc_deals = deal_investors[
        deal_investors['investor_id'] == focal_vc
    ]['deal_id'].unique()
    
    year_deals = deals[
        (deals['deal_id'].isin(vc_deals)) &
        (deals['deal_year'] == year)
    ]
    
    total = len(year_deals)
    if total == 0:
        return np.nan
    
    hrv_count = year_deals[hrv_column].sum()
    return hrv_count / total
```

### 4.4 Panel Construction (src/features/build_panel.py)

```python
"""
Panel Construction Module

Builds the VC-year panel dataset for analysis.
"""

import pandas as pd
import numpy as np
from typing import List
from .network_measures import compute_network_measures
from .diversity_measures import compute_diversity_measures
from .hrv_classification import compute_hrv_share


def identify_active_vcs(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    min_deals: int = 2,
    years: List[int] = None
) -> List[str]:
    """
    Identify VCs with sufficient activity for analysis.
    
    Active VC = at least min_deals across the full period.
    """
    if years is None:
        years = list(range(2015, 2025))
    
    di_with_year = deal_investors.merge(
        deals[['deal_id', 'deal_year']], 
        on='deal_id'
    )
    
    di_in_period = di_with_year[di_with_year['deal_year'].isin(years)]
    
    deal_counts = di_in_period.groupby('investor_id')['deal_id'].nunique()
    active_vcs = deal_counts[deal_counts >= min_deals].index.tolist()
    
    return active_vcs


def build_vc_year_panel(
    deals: pd.DataFrame,
    investors: pd.DataFrame,
    deal_investors: pd.DataFrame,
    years: List[int] = None,
    window: int = 3,
    min_ego_size: int = 2
) -> pd.DataFrame:
    """
    Build VC-year panel with all variables.
    
    Parameters
    ----------
    deals : DataFrame
    investors : DataFrame
    deal_investors : DataFrame
    years : list of years to include (default 2018-2024, allowing 3-year lookback)
    window : lookback window for network measures
    min_ego_size : minimum ego-network size to include (isolates excluded by default)
    
    Returns
    -------
    DataFrame with one row per VC-year, columns:
        - investor_id, year
        - Network: ego_size, density, density_weighted, avg_clustering, etc.
        - Diversity: diversity_type, diversity_geo, diversity_combined, etc.
        - DV: hrv_share_primary, hrv_share_hardtech, total_deals
        - Controls: portfolio_concentration, experience, etc.
    """
    if years is None:
        # Start at 2018 to allow 3-year lookback to 2015
        years = list(range(2015 + window, 2025))
    
    # Get active VCs
    active_vcs = identify_active_vcs(deal_investors, deals)
    print(f"Found {len(active_vcs)} active VCs")
    
    rows = []
    
    for vc in active_vcs:
        for year in years:
            # Network measures
            network = compute_network_measures(
                deal_investors, deals, vc, year, window
            )
            
            # Skip if insufficient network size
            if network['ego_size'] < min_ego_size:
                continue
            
            # Diversity measures
            diversity = compute_diversity_measures(
                deal_investors, deals, investors, vc, year, window
            )
            
            # HRV outcomes (year t)
            hrv_primary = compute_hrv_share(
                deals, deal_investors, vc, year, 'hrv_primary'
            )
            hrv_hardtech = compute_hrv_share(
                deals, deal_investors, vc, year, 'hrv_hardtech'
            )
            
            # Total deals in year t
            vc_deals = deal_investors[
                deal_investors['investor_id'] == vc
            ]['deal_id'].unique()
            total_deals = len(deals[
                (deals['deal_id'].isin(vc_deals)) &
                (deals['deal_year'] == year)
            ])
            
            # Skip if no deals in outcome year
            if total_deals == 0:
                continue
            
            # Control: experience (cumulative deals up to t-1)
            cum_deals = len(deals[
                (deals['deal_id'].isin(vc_deals)) &
                (deals['deal_year'] < year)
            ])
            
            # Control: portfolio concentration (HHI over sectors, t-3 to t-1)
            window_deals = deals[
                (deals['deal_id'].isin(vc_deals)) &
                (deals['deal_year'] >= year - window) &
                (deals['deal_year'] < year)
            ]
            if len(window_deals) > 0:
                sector_counts = window_deals['sector_tags_std'].str.split('|').explode().value_counts(normalize=True)
                sector_hhi = (sector_counts ** 2).sum()
            else:
                sector_hhi = np.nan
            
            # Build row
            row = {
                'investor_id': vc,
                'year': year,
                # Network
                **{f'net_{k}': v for k, v in network.items()},
                # Diversity
                **{f'div_{k}': v for k, v in diversity.items()},
                # DVs
                'hrv_share_primary': hrv_primary,
                'hrv_share_hardtech': hrv_hardtech,
                'total_deals_t': total_deals,
                # Controls
                'experience_cumulative': cum_deals,
                'sector_concentration_hhi': sector_hhi
            }
            
            rows.append(row)
    
    panel = pd.DataFrame(rows)
    print(f"Built panel with {len(panel)} VC-year observations")
    
    return panel
```

---

## 5. EXTERNAL DATA FILES

Create these reference files in `data/external/`:

### 5.1 sector_taxonomy.csv

```csv
sector_raw,sector_std,is_hardtech
fintech,fintech_general,1
payments,fintech_payments,1
banking,fintech_banking,1
lending,fintech_lending,0
insurance,insurtech,0
healthtech,healthtech,1
health,healthtech,1
medtech,medtech,1
biotech,biotech,1
cleantech,cleantech,1
energy,energy,1
solar,renewables,1
agritech,agritech_general,1
agtech,agritech_general,1
precision agriculture,agritech_precision,1
logistics,logistics_tech,1
supply chain,supply_chain,1
ecommerce,ecommerce,0
e-commerce,ecommerce,0
marketplace,marketplace,0
edtech,edtech,0
education,edtech,0
media,media,0
entertainment,entertainment,0
hr,hr_recruitment,0
recruitment,hr_recruitment,0
proptech,proptech,0
real estate,proptech,0
ai,ai,1
artificial intelligence,ai,1
machine learning,ml,1
hardware,hardware,1
iot,iot,1
deeptech,deeptech,1
mobility,mobility,1
transport,mobility,1
```

### 5.2 stage_taxonomy.csv

```csv
stage_raw,stage_std,is_early
pre-seed,Seed,1
preseed,Seed,1
seed,Seed,1
seed+,Seed,1
angel,Seed,1
series a,Series_A,1
series-a,Series_A,1
a,Series_A,1
series b,Series_B,0
series-b,Series_B,0
b,Series_B,0
series c,Series_C,0
series-c,Series_C,0
c,Series_C,0
series d,Growth,0
series e,Growth,0
growth,Growth,0
late stage,Growth,0
bridge,Other,0
extension,Other,0
undisclosed,Other,0
```

### 5.3 investor_types.csv

```csv
type_raw,type_std
venture capital,VC_International
vc,VC_International
vc fund,VC_International
africa vc,VC_Regional
africa-focused vc,VC_Regional
local vc,VC_Local
corporate venture,CVC
cvc,CVC
strategic investor,CVC
angel,Angel
angel investor,Angel
angel network,Angel
dfi,DFI
development finance,DFI
ifc,DFI
fmo,DFI
accelerator,Accelerator
incubator,Accelerator
y combinator,Accelerator
techstars,Accelerator
family office,Other
pe fund,Other
private equity,Other
```

---

## 6. TESTING REQUIREMENTS

Create unit tests in `tests/`:

### 6.1 test_network_measures.py

```python
"""Tests for network measures."""

import pytest
import pandas as pd
import networkx as nx
from src.features.network_measures import (
    compute_density,
    build_ego_network,
    compute_network_measures
)


def test_density_complete_graph():
    """Complete graph should have density 1."""
    G = nx.complete_graph(5)
    assert compute_density(G) == 1.0


def test_density_empty_graph():
    """Graph with <2 nodes should return NaN."""
    G = nx.Graph()
    assert pd.isna(compute_density(G))
    
    G.add_node('A')
    assert pd.isna(compute_density(G))


def test_density_star_graph():
    """Star graph with n nodes has density 2/(n-1)."""
    G = nx.star_graph(4)  # 5 nodes total (center + 4 leaves)
    expected = 2 * 4 / (5 * 4)  # 4 edges, 5 nodes
    assert abs(compute_density(G) - expected) < 0.001


# Add more tests for edge cases...
```

### 6.2 test_hrv_classification.py

```python
"""Tests for HRV classification."""

import pytest
import pandas as pd
from src.features.hrv_classification import (
    is_hardtech,
    is_early_stage,
    classify_hrv_primary
)


def test_hardtech_fintech():
    """Fintech payments should be hardtech."""
    assert is_hardtech('fintech_payments') == True
    assert is_hardtech('fintech_payments|ai') == True


def test_hardtech_ecommerce():
    """E-commerce should NOT be hardtech."""
    assert is_hardtech('ecommerce') == False
    assert is_hardtech('marketplace|ecommerce') == False


def test_early_stage():
    """Only Seed and Series_A are early stage."""
    assert is_early_stage('Seed') == True
    assert is_early_stage('Series_A') == True
    assert is_early_stage('Series_B') == False
    assert is_early_stage('Growth') == False


def test_hrv_primary():
    """HRV primary = early AND hardtech."""
    row = pd.Series({
        'stage_std': 'Seed',
        'sector_tags_std': 'fintech_payments'
    })
    assert classify_hrv_primary(row) == True
    
    row = pd.Series({
        'stage_std': 'Series_B',
        'sector_tags_std': 'fintech_payments'
    })
    assert classify_hrv_primary(row) == False
    
    row = pd.Series({
        'stage_std': 'Seed',
        'sector_tags_std': 'ecommerce'
    })
    assert classify_hrv_primary(row) == False
```

---

## 7. REQUIREMENTS.TXT

```
# Core data processing
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0

# Network analysis
networkx>=3.1

# Statistics
scipy>=1.10.0
statsmodels>=0.14.0
linearmodels>=5.3  # For panel FE models

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0

# Jupyter
jupyter>=1.0.0
jupyterlab>=4.0.0

# Testing
pytest>=7.3.0
pytest-cov>=4.1.0

# Utilities
tqdm>=4.65.0
python-dotenv>=1.0.0
pyyaml>=6.0

# Excel handling (for raw data input)
openpyxl>=3.1.0
xlrd>=2.0.0
```

---

## 8. EXECUTION WORKFLOW

### 8.1 Master Script (scripts/run_all.sh)

```bash
#!/bin/bash
# Master execution script for VC Africa Networks analysis

set -e  # Exit on error

echo "=== VC Africa Networks Analysis Pipeline ==="
echo "Started at: $(date)"

# 1. Ingest raw data
echo "Step 1: Ingesting raw data..."
python scripts/01_ingest_raw_data.py

# 2. Clean and standardize
echo "Step 2: Cleaning and standardizing..."
python scripts/02_clean_and_standardize.py

# 3. Build networks
echo "Step 3: Building co-investment networks..."
python scripts/03_build_networks.py

# 4. Construct panel
echo "Step 4: Constructing VC-year panel..."
python scripts/04_construct_panel.py

# 5. Run analysis
echo "Step 5: Running analysis..."
python scripts/05_run_analysis.py

echo "=== Pipeline completed at: $(date) ==="
```

---

## 9. STOP/GO CRITERIA CHECKS

Before running main analysis, verify these criteria are met:

```python
# In scripts/04_construct_panel.py or separate validation script

def check_stop_go_criteria(panel: pd.DataFrame, deals: pd.DataFrame) -> bool:
    """
    Check stop/go criteria before proceeding to analysis.
    """
    issues = []
    
    # 1. Sample size
    n_vc_years = len(panel)
    if n_vc_years < 100:
        issues.append(f"STOP: Only {n_vc_years} VC-year observations (need ≥100)")
    
    # 2. HRV variance
    hrv_var = panel['hrv_share_primary'].var()
    if hrv_var < 0.01:
        issues.append(f"STOP: HRV share variance too low ({hrv_var:.4f})")
    
    # 3. Density variance
    density_var = panel['net_density'].var()
    if density_var < 0.01:
        issues.append(f"STOP: Density variance too low ({density_var:.4f})")
    
    # 4. Diversity variance
    div_var = panel['div_diversity_combined'].var()
    if div_var < 0.01:
        issues.append(f"STOP: Diversity variance too low ({div_var:.4f})")
    
    # 5. Coverage check
    years_covered = panel['year'].nunique()
    if years_covered < 5:
        issues.append(f"STOP: Only {years_covered} years covered (need ≥5)")
    
    # 6. Network size distribution
    median_ego = panel['net_ego_size'].median()
    if median_ego < 3:
        issues.append(f"WARNING: Median ego-network size only {median_ego}")
    
    # Report
    if issues:
        print("=== STOP/GO CHECK FAILED ===")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("=== STOP/GO CHECK PASSED ===")
        print(f"  - {n_vc_years} VC-year observations")
        print(f"  - HRV share variance: {hrv_var:.4f}")
        print(f"  - Density variance: {density_var:.4f}")
        print(f"  - {years_covered} years covered")
        return True
```

---

## 10. DATA INGESTION NOTES

When the Africa: The Big Deal dataset is obtained ($219 subscription), it should be placed in `data/raw/` as:

```
data/raw/
├── atbd_deals_2019_2024.xlsx    # Main deals file
└── README.md                     # Document source, download date, version
```

The raw data likely has columns like:
- Deal disclosure date
- Startup name
- Website
- Country
- Sector
- Founder names
- Deal amount
- Amount bracket
- Deal type (Seed, Series A, etc.)
- Investor names (critical!)
- Source link

The `01_ingest_raw_data.py` script should:
1. Load the Excel file
2. Parse investor names (likely comma/pipe separated)
3. Create the three-table structure (deals, investors, deal_investors)
4. Save to `data/interim/` for review before standardization

---

## 11. FINAL NOTES

### Priority Order
1. Set up repository structure
2. Create reference files (taxonomies)
3. Implement network measures (most complex)
4. Implement diversity measures
5. Implement HRV classification
6. Build panel construction
7. Write tests
8. Create analysis scripts

### Key Dependencies
- Africa: The Big Deal subscription for raw data
- Python 3.10+ recommended
- ~4GB RAM for full network computation

### Contact
Questions about variable definitions → refer to CODEBOOK.md
Questions about analysis choices → refer to PRE_ANALYSIS_PLAN.md

---

**END OF INSTRUCTIONS**
