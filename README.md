# VC Syndication Networks and High-Risk Venture Investment in Africa

**Research Question:** How do VC network structure (density) and composition (diversity) interact to shape investment in high-risk ventures (HRV) in African markets?

**Target:** AIB Africa 2026 (Deadline: February 2026)

## Key Hypothesis

Network density amplifies the effect of network diversity on HRV investment. Dense, diverse networks provide both trust infrastructure AND heterogeneous information, enabling risk-taking in uncertain environments.

## Data

| Source | Description | Coverage |
|--------|-------------|----------|
| **Africa: The Big Deal** | Investor-per-deal structured data | 2019-2024 |

- **Burn-in period:** 2019-2021 (for 3-year network windows)
- **Analysis period:** 2022-2024

## Key Variables

| Variable | Definition |
|----------|------------|
| **DV: HRV Share** | (early-stage + hard-tech deals) / total deals |
| **IV1: Density** | Ego-network density from global co-investment graph |
| **IV2: Diversity** | Z-scored average of Blau indices (type + geography) |
| **IV3: Interaction** | Density × Diversity |

## Project Structure

```
vc-africa-networks/
├── data/
│   ├── raw/                  # ATBD Excel + supplements (never modify)
│   ├── interim/              # Intermediate processing outputs
│   ├── processed/            # Analysis-ready parquet files
│   └── external/             # Reference taxonomies, lookups
├── src/
│   ├── data/                 # Data ingestion, entity resolution
│   ├── features/             # Network, diversity, HRV measures
│   ├── analysis/             # Models, robustness checks
│   └── utils/                # Helpers
├── config/                   # YAML configuration files
├── notebooks/                # Exploratory notebooks
├── scripts/                  # Execution scripts
├── outputs/
│   ├── tables/               # Regression tables
│   ├── figures/              # Publication figures
│   └── reports/              # Stop/go reports
├── docs/                     # Design docs, codebook, pre-analysis plan
└── logs/                     # Processing logs
```

## Setup

```bash
cd "/Volumes/Jules Hardrive/active_projects/vc-africa-networks"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline

```bash
# 1. Ingest ATBD data
python scripts/01_ingest_atbd.py

# 2. Entity resolution (investor name standardization)
python scripts/02_entity_resolution.py

# 3. Build co-investment networks
python scripts/03_build_networks.py

# 4. Construct VC-year panel
python scripts/04_construct_panel.py

# 5. Stop/go check before analysis
python scripts/05_stop_go_check.py

# 6. Run main analysis
python scripts/06_run_analysis.py
```

## Stop/Go Criteria

Before running analysis, verify:
- [ ] N (VC-years) >= 100
- [ ] HRV variance > 0.01
- [ ] Density variance > 0.01
- [ ] Years covered >= 3
- [ ] Median ego size >= 3

## Key Documents

- `docs/data_dictionary_codebook.md` - Variable definitions
- `docs/pre_analysis_plan.md` - Locked analysis specifications
- `docs/CLAUDE_CODE_INSTRUCTIONS_CORRECTED.md` - Implementation guide (use this, not v1)

## Status

- [ ] ATBD subscription obtained
- [ ] Raw data ingested
- [ ] Entity resolution complete
- [ ] Networks constructed
- [ ] Panel built
- [ ] Stop/go passed
- [ ] Analysis complete
