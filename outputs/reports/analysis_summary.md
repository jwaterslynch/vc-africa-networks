# VC Networks Analysis: Summary Report

Generated: 2026-01-01 23:48

## Sample

| Metric | Value |
|--------|-------|
| VC-year observations | 901 |
| Unique VCs | 558 |
| Years | [2022, 2023, 2024] |
| Mean HRV share | 12.2% |

## Key Result: Density × Diversity Interaction

**Coefficient: 0.0846 (p = 0.537)**

Standard Error: 0.1371

### Interpretation

The interaction is **positive but not statistically significant**.

While directionally consistent with the hypothesis, we cannot rule out that this pattern occurred by chance.


## Robustness Summary

| Check | Significant (p<0.05) | Positive |
|-------|---------------------|----------|
| Main (M4) | ❌ | ✅ |
| R1_early_only | ❌ | ✅ |
| R2_hardtech_only | ❌ | ❌ |
| R5_weighted_density | ❌ | ✅ |
| R7_no_inferred | ❌ | ✅ |
| R15_stable_regime | ❌ | ✅ |

**Overall: 0/6 specifications significant, 5/6 positive**

❌ **NOT ROBUST**: Interaction fails in most specifications


## Model Specifications

### Main Models

1. **Model 1**: HRV ~ density + controls
2. **Model 2**: HRV ~ diversity + controls
3. **Model 3**: HRV ~ density + diversity + controls
4. **Model 4**: HRV ~ density + diversity + density×diversity + controls

Controls: log(ego size), log(experience), year FE

Standard errors clustered by VC.

### Robustness Checks

- **R1**: Alternative DV — early-stage share (regardless of sector)
- **R2**: Alternative DV — hard-tech share (regardless of stage)
- **R5**: Weighted density (repeated co-investments)
- **R7**: Exclude deals with inferred stages
- **R15**: Stable coverage regime only (2023-2024)

## Output Files

- `outputs/tables/main_results.tex` - LaTeX regression table
- `outputs/tables/robustness_summary.csv` - Robustness comparison
- `outputs/figures/interaction_plot.png` - Marginal effects visualization
- `outputs/figures/distributions.png` - Variable distributions
- `outputs/figures/robustness_forest.png` - Coefficient comparison

