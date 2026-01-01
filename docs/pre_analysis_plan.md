# Pre-Analysis Plan: VC Networks & High-Risk Ventures in Africa

**Date:** January 2025  
**Authors:** Julian Waters-Lynch  
**Status:** Internal memo (not registered)  
**Purpose:** Lock specifications before data cleaning to prevent drift

---

## 1. Research Question

How do venture capital syndication network structures shape risk-taking in Africa's emerging startup ecosystem? Specifically: Does the effect of ego-network density on high-risk venture (HRV) investment depend on partner diversity?

---

## 2. Primary Model Specification

### 2.1 Unit of Analysis
**Primary:** VC-year (enables portfolio-level DV)

### 2.2 Dependent Variable
**HRV Share** = (HRV deals by VC i in year t) / (Total deals by VC i in year t)

**HRV primary definition:** Deal is HRV if:
- stage_std ∈ {Seed, Series_A} **AND**
- sector_tags_std ∩ {healthtech_biotech, cleantech_energy, agritech_hardware, industrial_deeptech} ≠ ∅

This captures "early-stage + high technological uncertainty" — where soft information and network-based trust matter most.

### 2.3 Independent Variables

| Variable | Definition | Computation |
|----------|------------|-------------|
| Density | Ego-network density | 2E / k(k-1), binary ties, 3-year rolling window (t-3 to t-1) |
| Diversity | Composite partner diversity | Z-scored average of Geographic Blau + Investor-type Blau |
| Density × Diversity | Interaction term | Product of standardised density and diversity |

### 2.4 Controls
- Ego-network size (k)
- Deal activity (deals in rolling window)
- Prior Africa deals (cumulative)
- Fund age (years since first Africa deal)
- Network centrality (degree)
- Portfolio concentration (sector Herfindahl, geography Herfindahl)

**Timing:** All controls computed over the same rolling window as network measures (t-3 to t-1) to avoid post-treatment bias. Portfolio concentration in year t's deals would be partly determined by HRV choices, creating endogeneity.

### 2.5 Fixed Effects
- Year FE only (VC FE would absorb slow-moving network measures)

### 2.6 Estimation
- Fractional logit (GLM, binomial family)
- Weighted by deal count (more deals = more information)
- Robust standard errors clustered at VC level

### 2.7 Sample Restrictions
- Rolling window requires ≥ 2 partners (k ≥ 2) to compute density
- First valid year: **2018** (requires 2015–2017 for full 3-year window)
- 2015–2017 used for network history and descriptives only

---

## 3. Hypotheses (Directional Predictions)

| Hypothesis | Prediction | Variable |
|------------|------------|----------|
| H1 | β > 0 (positive, contingent on H3) | Density |
| H2 | β > 0 | Diversity |
| H3 | β > 0 | Density × Diversity |

**Interpretation of H3:** Positive interaction means density's effect on HRV is stronger when diversity is high; effect attenuates (may reverse) when diversity is low.

---

## 4. Pre-Specified Robustness Checks

### 4.1 Alternative DVs
| # | DV | Purpose |
|---|-----|---------|
| R1 | HRV Share (Early) = hard-tech / (Seed + Series A) | Hard-tech selection within early-stage |
| R2 | HRV Hard-Tech Only (any stage) | Tests whether stage criterion matters |
| R3 | Sector distance (Jaccard vs prior portfolio) | Mechanical, VC-specific risk measure |
| R4 | Novel-market (exploratory) | New country/sector for VC |
| R5 | Exclude inferred-stage deals | Tests sensitivity to stage inference heuristic |

### 4.2 Alternative Network Specifications
| # | Specification | Purpose |
|---|---------------|---------|
| R6 | 5-year rolling window | Sensitivity to window length |
| R7 | Weighted density (repeated ties) | Captures tie strength |
| R8 | Company-based ties | Broader relationship definition |
| R9 | Include isolates (k = 0, 1) with indicator | Tests selection on network activity |

### 4.3 Alternative Diversity Measures
| # | Measure | Purpose |
|---|---------|---------|
| R10 | Geographic diversity only | Decomposition |
| R11 | Investor-type diversity only | Decomposition |
| R12 | Binary geographic (Africa vs International) | Simpler measure |
| R13 | Quadratic diversity term | Nooteboom inverted-U test |

### 4.4 Alternative Estimation
| # | Approach | Purpose |
|---|----------|---------|
| R14 | Poisson with VC FE + Year FE | Count DV with offset |
| R15 | Deal-level logit | Alternative unit |
| R16 | Two-way clustering (deal-level) | VC × venture |
| R17 | Exclude Nigeria/Kenya/SA | Dominant ecosystem sensitivity |

---

## 5. Exclusion Rules (Locked)

| Rule | Primary Sample | Robustness |
|------|----------------|------------|
| Minimum partners | k ≥ 2 | k ≥ 0 + sparse indicator (R7) |
| Network window | 3 years | 5 years (R4) |
| First analysis year | 2018 | — |
| Investment type | Equity/convertible only | — |
| Geography | HQ or primary ops in Africa | — |

---

## 6. Diversity Classification Algorithm

### 6.1 Investor-Type Diversity
Blau index over partner types in ego-network:
- Categories: IVC, CVC, DFI, Angel_Family, Accelerator, Other

### 6.2 Geographic Diversity
Blau index over partner geography relative to focal VC:
- Local = same country as focal VC's primary Africa market
- Regional = Africa, different country
- International = outside Africa

**Primary market determination:**
1. Modal country in focal VC's deals in 3-year window
2. Tie-breaker: earliest deal country
3. Fallback: country of first observed Africa investment
4. Missing: flag diversity as missing for VC-year

---

## 7. Coding Reliability Protocol

- 15% double-coding (minimum 30 investors)
- Variables: investor_type, hq_country
- Threshold: Cohen's κ ≥ 0.80
- Disagreements resolved by discussion; codebook updated

---

## 8. Analysis Timeline

| Phase | Activities | Target |
|-------|------------|--------|
| Jan Week 1–2 | Partech backbone extraction | Complete deals_rounds |
| Jan Week 3 | Supplement with secondary sources | Complete deal_investors |
| Jan Week 4 | Entity resolution, investor coding | Complete investors |
| Feb Week 1 | Network construction, descriptives | Tables 1–2B, Figure 1 |
| Feb Week 2 | Main models | Table 4, Figure 2 |
| Feb Week 3 | Robustness checks | Tables 5–7 |
| Mar Week 1–2 | Draft completion | AIB submission |

---

## 9. Stop/Go Criteria Before Modelling

Proceed to estimation only if:
- [ ] Partech coverage ≥ 95% by year
- [ ] Top 30 investors verified for duplicates
- [ ] κ ≥ 0.80 for double-coded variables
- [ ] Table 1 deal counts plausible by year/country
- [ ] Figure 1 network has visible structure (not all isolates)
- [ ] ≥ 100 VC-year observations with k ≥ 2
- [ ] Density distribution has variance (not all 0 or 1)
- [ ] HRV share has variance (not all 0% or 100%)

---

## 10. Changelog

| Date | Change |
|------|--------|
| Jan 2025 | Initial pre-analysis plan locked |

---

*This memo documents analytic decisions made before examining outcome data. Deviations will be noted in the final paper's limitations section.*
