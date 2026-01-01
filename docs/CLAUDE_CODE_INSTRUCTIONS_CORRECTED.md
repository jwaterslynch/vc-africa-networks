# Claude Code Project Setup Instructions (v2 - CORRECTED)
## VC Social Networks and High-Risk Venture Investment in Africa (2019-2024)

**Project:** AIB Africa 2026 Submission  
**Deadline:** February 2026  
**Principal Investigator:** Jules  

---

## CRITICAL CORRECTIONS FROM v1

1. **Network density computation was WRONG** — now fixed with global graph approach
2. **Diversity composite** — changed from product to z-scored average (per design freeze)
3. **Hard-tech definition** — removed fintech from hard-tech (not defensible as technological uncertainty)
4. **Time scope** — adjusted to 2019-2024 (ATBD coverage), with 2019-2021 as burn-in for network windows

---

## 1. PROJECT OVERVIEW

### 1.1 Research Question
How do VC network structure (density) and composition (diversity) interact to shape investment in high-risk ventures (HRV) in African markets?

### 1.2 Core Hypothesis
Network density amplifies the effect of network diversity on HRV investment — dense, diverse networks provide both trust infrastructure AND heterogeneous information, enabling risk-taking.

### 1.3 Theoretical Engine
- **Density as closure**: trust, reputation enforcement, repeated interaction
- **Diversity as variety**: heterogeneous information, reduced correlated errors
- **Interaction**: density without diversity → herding; diversity without density → noise

### 1.4 Data Strategy
- **Primary source:** Africa: The Big Deal (ATBD) subscription — $219-229/year
- **Coverage:** 2019-2024 (investor-per-deal data)
- **Burn-in period:** 2019-2021 (for 3-year network windows)
- **Analysis period:** 2022-2024 (clean outcome years with full lag windows)

### 1.5 Key Variables
- **DV:** HRV share (proportion of deals that are early-stage + hard-tech)
- **IV1:** Network density (ego-network from t-3 to t-1 co-investments)
- **IV2:** Network diversity (z-scored average of Blau indices)
- **IV3:** Density × Diversity interaction

---

## 2. REPOSITORY STRUCTURE

```
vc-africa-networks/
│
├── README.md
├── CODEBOOK.md
├── PRE_ANALYSIS_PLAN.md
├── requirements.txt
│
├── data/
│   ├── raw/                     # ATBD Excel + any supplements
│   │   ├── .gitkeep
│   │   └── README.md            # Data provenance, download date
│   │
│   ├── processed/
│   │   ├── deals.parquet
│   │   ├── investors.parquet
│   │   ├── deal_investors.parquet
│   │   └── vc_year_panel.parquet
│   │
│   ├── interim/
│   │   ├── parsed_atbd.parquet          # After initial parse
│   │   ├── entity_resolution_log.csv    # Merge/split decisions
│   │   └── entity_overrides.csv         # Human-editable corrections
│   │
│   └── external/
│       ├── sector_taxonomy.csv
│       ├── stage_taxonomy.csv
│       ├── investor_types.csv
│       └── country_codes.csv
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingest_atbd.py       # ATBD Excel parser
│   │   ├── entity_resolution.py # Investor name standardization
│   │   ├── standardize.py       # Map to taxonomies
│   │   └── validate.py          # Data quality checks
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── network_construction.py  # CORRECTED: global graph approach
│   │   ├── network_measures.py      # Density, clustering on ego-networks
│   │   ├── diversity_measures.py    # Blau indices, z-score composite
│   │   ├── hrv_classification.py    # CORRECTED: hard-tech definition
│   │   └── build_panel.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── descriptives.py
│   │   ├── main_models.py
│   │   ├── robustness.py
│   │   └── visualizations.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── notebooks/
│   ├── 01_atbd_exploration.ipynb
│   ├── 02_entity_resolution_review.ipynb
│   ├── 03_network_visualization.ipynb
│   └── 04_stop_go_check.ipynb
│
├── tests/
│   ├── test_network_construction.py
│   ├── test_diversity_measures.py
│   └── test_hrv_classification.py
│
├── outputs/
│   ├── tables/
│   ├── figures/
│   └── reports/
│       └── stop_go_report.md
│
└── scripts/
    ├── 01_ingest_atbd.py
    ├── 02_entity_resolution.py
    ├── 03_build_networks.py
    ├── 04_construct_panel.py
    ├── 05_stop_go_check.py
    └── 06_run_analysis.py
```

---

## 3. CRITICAL FIX: NETWORK CONSTRUCTION

### The Bug in v1

The original `build_ego_network` function only created edges between partners when they co-invested **with the focal VC**. This is WRONG.

**Correct definition:** Ego-network density measures whether the focal VC's partners are connected to each other **anywhere in the ecosystem** — including deals the focal VC wasn't part of.

### Correct Algorithm

```python
"""
CORRECT Network Construction

For each focal VC i in year t:
1. Build GLOBAL co-investment graph for window [t-3, t-1]
   - Nodes: ALL investors active in window
   - Edges: connect two investors if they co-invested in ANY deal
2. Get focal VC's neighbors (partners) = nodes connected to VC i
3. Extract INDUCED SUBGRAPH on partners (excluding focal VC)
4. Compute density on this induced subgraph

This correctly captures partner-to-partner ties formed OUTSIDE
the focal VC's deals.
"""

import networkx as nx
import pandas as pd
import numpy as np
from itertools import combinations


def build_global_coinvestment_graph(
    deal_investors: pd.DataFrame,
    deals: pd.DataFrame,
    year: int,
    window: int = 3
) -> nx.Graph:
    """
    Build GLOBAL co-investment graph for all deals in [year-window, year-1].
    """
    # Get deals in window
    window_deals = deals[
        (deals['deal_year'] >= year - window) &
        (deals['deal_year'] < year)
    ]['deal_id'].unique()
    
    if len(window_deals) == 0:
        return nx.Graph()
    
    # Filter to window
    di_window = deal_investors[deal_investors['deal_id'].isin(window_deals)]
    
    # Build graph
    G = nx.Graph()
    all_investors = di_window['investor_id'].unique()
    G.add_nodes_from(all_investors)
    
    # For each deal, create edges between ALL co-investors
    for deal_id in window_deals:
        participants = di_window[
            di_window['deal_id'] == deal_id
        ]['investor_id'].tolist()
        
        for inv1, inv2 in combinations(participants, 2):
            if G.has_edge(inv1, inv2):
                G[inv1][inv2]['weight'] += 1
            else:
                G.add_edge(inv1, inv2, weight=1)
    
    return G


def compute_ego_density(G_global: nx.Graph, focal_vc: str) -> float:
    """
    Compute ego-network density for focal VC.
    
    Density is computed on the INDUCED SUBGRAPH of the focal VC's
    neighbors (excluding the focal VC itself).
    """
    if focal_vc not in G_global:
        return np.nan
    
    partners = list(G_global.neighbors(focal_vc))
    k = len(partners)
    
    if k < 2:
        return np.nan
    
    # Extract induced subgraph on partners
    ego = G_global.subgraph(partners)
    
    # Compute density
    return nx.density(ego)
```

---

## 4. CRITICAL FIX: DIVERSITY COMPOSITE

### The Bug in v1

v1 used `diversity_combined = diversity_type * diversity_geo` (product).

### Correct Approach (per Design Freeze)

```python
# Z-score each component, then average
diversity_combined = (z(diversity_type) + z(diversity_geo)) / 2
```

This is computed at the PANEL level after all VC-year observations are created.

---

## 5. CRITICAL FIX: HARD-TECH DEFINITION

### The Bug in v1

v1 included fintech in hard-tech sectors. This is NOT defensible — fintech involves market/regulatory uncertainty, not technological/engineering uncertainty.

### Correct Hard-Tech Sectors

```python
HARDTECH_SECTORS = {
    # Deep tech / engineering
    'deeptech', 'hardware', 'iot', 'ai', 'ml', 'robotics', 'spacetech',
    
    # Biotech / Healthtech  
    'biotech', 'healthtech', 'medtech', 'diagnostics', 'therapeutics',
    
    # Energy / Cleantech
    'cleantech', 'energy', 'renewables', 'solar', 'battery', 'ev', 'climate_tech',
    
    # Precision agriculture (not marketplaces)
    'agritech_precision', 'agritech_iot', 'precision_agriculture',
    
    # Tech-enabled infrastructure
    'supply_chain_tech', 'logistics_tech'
}

# NOT hard-tech
SOFTTECH_SECTORS = {
    'fintech', 'payments', 'lending', 'insurtech', 'neo_bank',
    'ecommerce', 'marketplace', 'edtech', 'media', 'hr_tech', 'proptech'
}
```

---

## 6. TIME SCOPE ADJUSTMENT

### Original Plan (v1)
- 2015-2024 (10 years)
- Would require manual data collection for 2015-2018

### Corrected Plan (v2)
- **Data:** 2019-2024 (ATBD coverage)
- **Burn-in:** 2019-2021 (for 3-year network windows)
- **Analysis:** 2022-2024 (clean outcome years)

This gives:
- 3 outcome years with full lag windows
- No reliance on incomplete pre-2019 data
- Clean "coverage regime" (ATBD threshold stable at $100K+ from 2021)

---

## 7. DATA SOURCE: ATBD

### Why ATBD?
- Only source with **investor-per-deal** data in structured format
- Monthly updated Excel with 30+ fields
- Coverage: 2019-present, $100K+ deals (varies by year)

### Key Fields We Need
- Deal date
- Company name, country, sector
- Stage (Seed, Series A, etc.)
- Amount (or bracket if undisclosed)
- **Investor names** (CRITICAL)

### Coverage Threshold by Year
| Year | Minimum Deal Size |
|------|-------------------|
| 2019 | $1M+ |
| 2020 | $500K+ |
| 2021+ | $100K+ |

**Implication:** Include `coverage_regime` control variable; restrict main analysis to 2021+ for stable coverage or test robustness across regimes.

---

## 8. ENTITY RESOLUTION

Investor names will have variations:
- "Y Combinator" vs "YCombinator" vs "Y-Combinator"
- "Partech Africa" vs "Partech"
- Typos, abbreviations

### Approach
1. **Deterministic normalization** — lowercase, remove punctuation, collapse whitespace
2. **Human-editable overrides** — `data/interim/entity_overrides.csv`
3. **Audit trail** — `data/interim/entity_resolution_log.csv`
4. **Fuzzy matching suggestions** — for human review, not auto-applied

---

## 9. STOP/GO CRITERIA

Before running main analysis, verify:

| Criterion | Threshold | Action if Fail |
|-----------|-----------|----------------|
| N (VC-years) | ≥ 100 | STOP |
| HRV variance | > 0.01 | STOP |
| Density variance | > 0.01 | STOP |
| Years covered | ≥ 3 | STOP |
| Median ego size | ≥ 3 | WARNING |
| % missing density | < 20% | WARNING |

---

## 10. PRIORITY TASKS FOR CLAUDE CODE

1. **Create repository structure** and reference files
2. **Write ATBD ingestion script** (parsing investor strings)
3. **Write entity resolution module** (with audit trail)
4. **Implement CORRECT network construction** (global graph approach)
5. **Implement diversity measures** (z-score composite)
6. **Implement HRV classification** (fintech NOT hard-tech)
7. **Write stop/go check script**

---

## 11. NEXT STEPS FOR JULES

1. ✅ Download this corrected instruction file
2. 📦 Purchase ATBD subscription ($219-229/year)
3. 📥 Download Excel export → `data/raw/`
4. 🤖 Provide to Claude Code with this file
5. 👀 Review entity resolution suggestions
6. ✅ Run stop/go check before analysis

---

**END OF CORRECTED INSTRUCTIONS**
