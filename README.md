# VC Syndication Networks and High-Risk Venture Investment in Africa

[![Replication](https://img.shields.io/badge/replication-available-brightgreen)](scripts/replicate.py)
[![Data](https://img.shields.io/badge/data-proprietary-orange)](https://thebigdeal.com/database)

**Research Question:** How does VC network structure affect investment in high-risk ventures (HRV) in African markets?

**Target:** AIB Africa 2026 / JIBS

---

## Key Finding

**Network density constrains high-risk venture investment, but only for international VCs.**

| VC Type | Density Effect | p-value | Interpretation |
|---------|----------------|---------|----------------|
| International (N=606) | β = -0.55 | 0.002 | Dense networks suppress HRV |
| African (N=295) | β = +0.24 | 0.256 | No significant effect |
| **Difference** | z = 2.88 | **0.004** | Statistically significant |

Moving from low to high network density:
- **International VCs:** 15.3% → 5.2% HRV share (-10.1 pp)
- **African VCs:** 13.0% → 15.9% HRV share (+2.9 pp)

---

## Quick Start: Replication

```bash
# Clone the repository
git clone https://github.com/[username]/vc-africa-networks.git
cd vc-africa-networks

# Install dependencies
pip install -r requirements.txt

# Run replication script
python scripts/replicate.py
```

### Replication Modes

The script auto-detects available data:

| Mode | Condition | What Happens |
|------|-----------|--------------|
| **Full** | Raw ATBD data in `data/raw/` | Runs complete pipeline |
| **Demo** | No raw data | Loads pre-computed `paper_numbers.json` |

```bash
python scripts/replicate.py --check  # See what mode would run
python scripts/replicate.py --demo   # Force demonstration mode
python scripts/replicate.py --full   # Force full pipeline (requires data)
```

### Data Access

Raw data from **Africa: The Big Deal (ATBD)** is proprietary. To run full replication:

1. Purchase access at [thebigdeal.com/database](https://thebigdeal.com/database)
2. Download the Excel database
3. Place in `data/raw/`
4. Run `python scripts/replicate.py --full`

---

## Project Structure

```
vc-africa-networks/
├── scripts/
│   ├── replicate.py              # One-shot replication script
│   ├── 01_ingest_atbd.py         # Data ingestion
│   ├── 03_build_panel.py         # Panel construction
│   ├── 06_run_analysis.py        # Main analysis
│   ├── generate_paper_tables.py  # Generate all tables
│   ├── generate_figure1.py       # Generate figures
│   └── check_manuscript_consistency.py
├── src/
│   ├── features/
│   │   ├── network_construction.py   # Global graph density
│   │   ├── diversity_measures.py     # Blau indices
│   │   └── hrv_classification.py     # HRV definition
│   └── analysis/
│       └── main_models.py            # Fractional logit (GEE)
├── outputs/
│   ├── paper_numbers.json        # Single source of truth
│   ├── tables/                   # LaTeX + CSV tables
│   ├── figures/                  # PNG + PDF figures
│   └── final_checks/             # Validation logs
├── data/
│   ├── raw/                      # ATBD data (not committed)
│   └── processed/                # Panel data (not committed)
└── docs/                         # Documentation
```

---

## Methodology

### Network Density (Global Graph Approach)

For each focal VC *i* in year *t*:

1. Build **global** co-investment graph for window [*t*-3, *t*-1]
2. Get focal VC's partners (neighbors)
3. Extract **induced subgraph** on partners (excluding focal VC)
4. Compute density = actual_edges / possible_edges

This captures partner-to-partner ties formed *outside* the focal VC's own deals.

### High-Risk Venture (HRV) Definition

HRV = 1 if deal is:
- **Early-stage:** Seed or Series A
- **Hard-tech:** healthtech, cleantech, agritech, deeptech, biotech
- (Fintech excluded)

### Statistical Model

Fractional logit via GEE with:
- Binomial family, logit link
- Exchangeable correlation structure
- Clustered standard errors by investor

---

## Key Files

| File | Description |
|------|-------------|
| `outputs/paper_numbers.json` | All statistics for the paper |
| `outputs/tables/table3_split_sample.tex` | Main results table |
| `outputs/figures/figure1_marginal_effects.pdf` | Main figure |
| `docs/VERIFIED_RESULTS_SUMMARY.md` | Verified results documentation |

---

## Citation

```bibtex
@article{author2026vcnetworks,
  title={Network Density and High-Risk Venture Investment:
         Evidence from VC Syndication in Africa},
  author={[Authors]},
  journal={[Journal]},
  year={2026}
}
```

---

## Requirements

- Python 3.9+
- pandas, numpy, networkx
- statsmodels (GEE)
- matplotlib

See `requirements.txt` for full dependencies.

---

## License

Code: MIT License

Data: Raw ATBD data is proprietary and not included. Pre-computed aggregate outputs are included for replication purposes.
