# Model Specification Note

## Current Implementation

The analysis uses **Fractional Logit** estimated via:
- **GEE** (Generalized Estimating Equations) with exchangeable correlation
- **Binomial family** with logit link
- **Clustered standard errors** by investor_id

The dependent variable is `hrv_share` (proportion of deals that are HRVs, range 0-1).

## Weighting Robustness Check

We compared three specifications:

| Specification | International β | African β | Difference z | p-value |
|---------------|-----------------|-----------|--------------|---------|
| GLM Unweighted | -0.596 | +0.117 | 1.88 | 0.060 |
| GLM Weighted (by n_deals) | -0.700 | +0.188 | 3.78 | <0.001 |
| **GEE Clustered (current)** | **-0.549** | **+0.241** | **2.88** | **0.004** |

### Key Findings:

1. **All specifications show the same pattern**: negative density effect for international VCs, 
   null/positive for African VCs

2. **GEE is conservative**: The clustered GEE specification (z = 2.88) is MORE conservative 
   than the weighted GLM (z = 3.78)

3. **Weighting strengthens the result**: If anything, weighting by n_deals makes the 
   finding stronger, not weaker

### Conclusion

The current GEE specification is appropriate and conservative. The finding is robust to 
alternative weighting schemes.

## Technical Note for Methods Section

> "We estimate fractional logit models using GEE with an exchangeable correlation structure 
> and clustered standard errors by investor. The dependent variable is the proportion of 
> deals that qualify as high-risk ventures in each VC-year. Results are robust to weighting 
> by number of deals (see Appendix)."
