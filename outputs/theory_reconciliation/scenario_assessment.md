# Theory Reconciliation: Scenario Assessment

**Date:** 2026-01-02
**Purpose:** Determine which theoretical scenario fits the data

---

## Summary of Key Results

### 1. Original Density × Diversity Hypothesis

| Sample | density × diversity | p-value | Conclusion |
|--------|---------------------|---------|------------|
| Pooled (N=901) | +0.085 | 0.537 | **NOT SIGNIFICANT** |
| International VCs (N=606) | +0.039 | 0.836 | Not significant |
| African VCs (N=295) | +0.201 | 0.247 | Not significant |

**Finding:** The original pre-registered hypothesis (H2/H3) is NOT supported. Diversity does not significantly moderate the density effect in any sample.

---

### 2. Diversity by HQ Location

| Variable | African VCs | International VCs | Difference | p-value |
|----------|-------------|-------------------|------------|---------|
| diversity_type | 0.564 | 0.568 | -0.004 | 0.770 |
| diversity_geo | 0.460 | 0.351 | **+0.109** | <0.001 |
| diversity_combined | 0.405 | 0.175 | **+0.230** | <0.001 |
| pct_local | 0.296 | 0.105 | **+0.191** | <0.001 |
| pct_international | 0.536 | 0.722 | **-0.186** | <0.001 |

**Finding:** African VCs have significantly HIGHER geographic diversity and MORE local partners. They are also less reliant on international partners.

**Correlation:** hq_in_africa × diversity_combined = +0.134

---

### 3. Three-Way Interaction (Model 16a)

| Variable | Coefficient | p-value |
|----------|-------------|---------|
| density_std | -0.441 | 0.008 ** |
| density × diversity | +0.110 | 0.532 |
| density × african | +0.390 | 0.086 † |
| diversity × african | +0.313 | 0.247 |
| **triple interaction** | -0.075 | 0.742 |

**Finding:** The three-way interaction is NOT significant. The density × african effect persists (p=0.086) even after controlling for diversity interactions.

---

### 4. Horse Race: Which Mechanism Survives?

| Model | density × diversity | density × african |
|-------|---------------------|-------------------|
| Both included | β = 0.076, p = 0.580 | β = 0.280, p = 0.143 |

**Finding:** Neither interaction is significant when both are included, but both are underpowered. The HQ effect has a larger coefficient.

### Does Controlling for Diversity Reduce the HQ Effect?

| Specification | density × african | p-value |
|---------------|-------------------|---------|
| WITHOUT diversity control | β = 0.292 | 0.125 |
| WITH diversity control | β = 0.285 | 0.134 |
| **Reduction** | **2.3%** | |

**Finding:** Controlling for diversity barely changes the HQ effect. Diversity is NOT driving the HQ effect.

---

## Scenario Assessment

### SCENARIO A: "Diversity moderation is real, HQ is confound"
- ❌ Density × diversity is NOT significant (p = 0.54)
- ❌ HQ effect does NOT disappear when controlling for diversity
- **VERDICT: REJECTED**

### SCENARIO B: "Local knowledge is real, diversity is secondary"
- ✅ Density × african is significant in split sample (p = 0.004)
- ✅ Density × diversity is weak (p > 0.50)
- ⚠️ African VCs DO have higher diversity (potential confound)
- ⚠️ BUT: controlling for diversity doesn't eliminate HQ effect
- **VERDICT: BEST FIT, but with caveats**

### SCENARIO C: "Both mechanisms operate independently"
- ❌ Neither interaction is significant when both included
- ❌ Horse race is inconclusive
- **VERDICT: INSUFFICIENT EVIDENCE**

### SCENARIO D: "Diversity matters MORE for international VCs"
- ❌ Three-way interaction is NOT significant (p = 0.74)
- ❌ Density × diversity for International VCs is p = 0.84
- **VERDICT: REJECTED**

---

## Recommended Theoretical Framing

Based on the evidence, **SCENARIO B** is the best fit, with important nuances:

### What the Data Shows

1. **Density hurts international VCs** (β = -0.55, p = 0.002) but not African VCs (β = +0.24, p = 0.26)

2. **Diversity does NOT moderate the density effect** in any specification

3. **African VCs have higher geographic diversity**, but this does not explain their immunity to the density penalty

4. **The HQ effect is robust** to controlling for diversity (only 2.3% reduction)

### Theoretical Interpretation

The findings suggest that what matters is **local knowledge** (proxied by HQ location), not **network diversity** per se.

- International VCs in dense networks face conformity pressure AND lack independent evaluation capacity
- African VCs have local knowledge that allows independent evaluation, making them immune to density-induced herding
- Diversity alone doesn't provide this protection — you need LOCAL knowledge

### Honest Framing for the Paper

> "We hypothesized that network diversity would moderate the constraining effect of network density on high-risk investment. This hypothesis was NOT supported. Instead, we find that the density penalty is moderated by investor HQ location: international VCs in dense networks invest less in high-risk ventures, while African-headquartered VCs show no such penalty. This suggests that local knowledge—not network diversity per se—provides the independent evaluation capacity that prevents dense networks from becoming conformity traps."

---

## Key Caveats to Report

1. **Pre-registered hypothesis not confirmed:** Must acknowledge that H2/H3 were not supported

2. **HQ effect is exploratory:** The heterogeneity by HQ was discovered post-hoc, not pre-registered

3. **African VCs have higher diversity:** This is a potential confound, though controlling for it doesn't eliminate the HQ effect

4. **Interaction p-values are marginal:** The HQ interaction ranges from p=0.04 to p=0.14 depending on specification

5. **Split-sample is cleanest:** The formal difference test (z=2.88, p=0.004) is the strongest evidence

---

## Summary Table

| Model | density × diversity | density × african | 3-way | Interpretation |
|-------|---------------------|-------------------|-------|----------------|
| Original (15a) | 0.085 (p=0.54) | — | — | H2/H3 not supported |
| HQ only | — | 0.285 (p=0.13) | — | Marginal |
| Both 2-way (17a) | 0.076 (p=0.58) | 0.280 (p=0.14) | — | Neither survives |
| Full 3-way (16a) | 0.110 (p=0.53) | 0.390 (p=0.09) | -0.075 (p=0.74) | HQ marginally stronger |
| **Split sample** | — | **z=2.88, p=0.004** | — | **Cleanest evidence** |

---

## Files Generated

- `diversity_by_hq_descriptives.csv`
- `original_hypothesis_test.csv`
- `three_way_interaction.csv`
- `horse_race_results.csv`
- `scenario_assessment.md` (this file)
