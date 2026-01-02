# Exploratory Analysis Summary

Generated: 2026-01-01 23:56

## Overview

This report explores the diversity/density effects to understand where the action is,
given that the hypothesized Density × Diversity interaction was not significant.

---

## 1. Diversity Decomposition

**Question:** Is the diversity effect driven by investor-type heterogeneity,
geographic reach, or specifically by international partner access?

- **5a_type_only**: diversity_type_std = 0.2317* (p=0.049)
- **5a_type_only**: density_std = -0.3299* (p=0.021)
- **5a_type_only**: log_ego_size = -0.5709*** (p=0.001)
- **5a_type_only**: log_experience = 0.2805* (p=0.048)
- **5a_type_only**: year_2024 = 0.3731† (p=0.064)
- **5b_geo_only**: density_std = -0.3329* (p=0.022)
- **5b_geo_only**: log_ego_size = -0.4794** (p=0.002)
- **5b_geo_only**: log_experience = 0.2484† (p=0.089)
- **5b_geo_only**: year_2024 = 0.3331† (p=0.098)
- **5b_geo_only**: diversity_geo_std = 0.1977† (p=0.058)
- **5c_both_components**: density_std = -0.3223* (p=0.025)
- **5c_both_components**: log_ego_size = -0.5663*** (p=0.001)
- **5c_both_components**: log_experience = 0.2686† (p=0.061)
- **5c_both_components**: year_2024 = 0.3483† (p=0.085)
- **5d_pct_international**: density_std = -0.3570* (p=0.015)
- **5d_pct_international**: log_ego_size = -0.4115** (p=0.007)
- **5d_pct_international**: year_2024 = 0.3495† (p=0.082)
- **5e_all_geo_components**: density_std = -0.3587* (p=0.013)
- **5e_all_geo_components**: log_ego_size = -0.4165** (p=0.007)
- **5e_all_geo_components**: log_experience = 0.2418† (p=0.089)
- **5e_all_geo_components**: year_2024 = 0.3441† (p=0.086)


---

## 2. Heterogeneity by Focal Investor Type

**Question:** Does density hurt local VCs more? Do international VCs benefit more from diversity?


### 6a_african_only (African HQ)

### 6b_international_only (International HQ)
- density_std = -0.5485** (p=0.002)
- log_ego_size = -0.8168*** (p=0.000)

### 6c_interaction (nan)
- density_std = -0.4324** (p=0.009)
- log_ego_size = -0.5637*** (p=0.001)
- log_experience = 0.2841† (p=0.052)
- year_2024 = 0.3443† (p=0.088)
- density_x_african = 0.3719† (p=0.077)


---

## 3. Nonlinearity in Density

**Question:** Is moderate density beneficial but high density harmful?


### 7a_quadratic
- density_std = -0.3139† (p=0.052)
- diversity_std = 0.3319* (p=0.024)
- log_ego_size = -0.5622*** (p=0.001)
- log_experience = 0.2752† (p=0.072)
- year_2024 = 0.3477† (p=0.084)

### 7b_terciles
- diversity_std = 0.3178* (p=0.031)
- log_ego_size = -0.5681*** (p=0.001)
- log_experience = 0.2932† (p=0.051)
- year_2024 = 0.3474† (p=0.083)
- density_high = -0.7974* (p=0.029)


---

## 4. Alternative Interactions

**Question:** Are there conditional effects the main interaction missed?


### 8a_diversity_x_intl
- diversity_std = 0.3440* (p=0.030)
- density_std = -0.3218* (p=0.025)
- log_ego_size = -0.5680*** (p=0.001)
- log_experience = 0.2663† (p=0.066)
- year_2024 = 0.3488† (p=0.083)

### 8b_density_x_african
- diversity_std = 0.3259* (p=0.023)
- density_std = -0.4005* (p=0.012)
- log_ego_size = -0.5465** (p=0.001)
- log_experience = 0.2684† (p=0.062)
- year_2024 = 0.3480† (p=0.084)

### 8c_density_x_egosize
- diversity_std = 0.3472* (p=0.017)
- log_ego_size = -0.6134** (p=0.003)
- year_2024 = 0.3496† (p=0.082)


---

## 5. Temporal Dynamics

**Question:** Are effects strengthening or weakening as ecosystem matures?

See `temporal_by_year.csv` and `key_plots/temporal_effects.png` for year-by-year coefficients.

---

## Key Takeaways

**51 findings with p < 0.10**

- Decomposition: diversity_type_std
- Decomposition: density_std
- Decomposition: log_ego_size
- Decomposition: log_experience
- Decomposition: year_2024
- Decomposition: density_std
- Decomposition: log_ego_size
- Decomposition: log_experience
- Decomposition: year_2024
- Decomposition: diversity_geo_std


---

## Output Files

- `decomposition_results.csv` - Models 5a-5e
- `heterogeneity_results.csv` - Models 6a-6c
- `nonlinearity_results.csv` - Models 7a-7c
- `alt_interactions_results.csv` - Models 8a-8c
- `temporal_results.csv` - Model 9a
- `temporal_by_year.csv` - Coefficients by year
- `key_plots/` - Visualization files
