#!/usr/bin/env python3
"""
Generate Synthetic Data for Code Demonstration

Creates a synthetic panel that:
- Has the same columns as the real data
- Has similar distributions and correlations
- Allows the full pipeline to run end-to-end
- Does NOT allow replication of empirical results

This is for code transparency and testing only.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Set seed for reproducibility
np.random.seed(42)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"


def generate_synthetic_panel(n_investors: int = 200, n_years: int = 3) -> pd.DataFrame:
    """
    Generate a synthetic VC-year panel.

    Mimics structure of real data without actual values.
    """
    print(f"Generating synthetic panel: {n_investors} investors × {n_years} years")

    # Create investor-year combinations
    investors = [f"inv_{i:04d}" for i in range(n_investors)]
    years = [2022, 2023, 2024]

    rows = []
    for inv_id in investors:
        # Each investor appears in 1-3 years (weighted toward more)
        n_years_active = np.random.choice([1, 2, 3], p=[0.2, 0.3, 0.5])
        active_years = np.random.choice(years, size=n_years_active, replace=False)

        for year in active_years:
            rows.append({
                'investor_id': inv_id,
                'year': year
            })

    df = pd.DataFrame(rows)
    n_obs = len(df)
    print(f"  Created {n_obs} VC-year observations")

    # Assign HQ location (roughly 33% African, 67% international)
    # Assign at investor level for consistency
    investor_hq = {inv: np.random.choice([0, 1], p=[0.67, 0.33])
                   for inv in investors}
    df['hq_in_africa'] = df['investor_id'].map(investor_hq)

    # Generate network variables
    # Ego size: log-normal distribution (mean ~20)
    df['ego_size'] = np.maximum(2, np.random.lognormal(mean=2.5, sigma=0.8, size=n_obs).astype(int))

    # Ego density: beta distribution (mean ~0.55, more variance)
    # African VCs slightly lower density on average
    base_density = np.random.beta(a=3, b=2.5, size=n_obs)
    df['ego_density'] = base_density - 0.1 * df['hq_in_africa'] + np.random.normal(0, 0.05, n_obs)
    df['ego_density'] = df['ego_density'].clip(0, 1)

    # Diversity measures
    df['diversity_type'] = np.random.beta(a=4, b=3, size=n_obs)
    df['diversity_geo'] = np.random.beta(a=3, b=4, size=n_obs)
    # African VCs have slightly higher diversity
    df['diversity_combined'] = (
        np.random.normal(0.25, 0.8, n_obs) +
        0.2 * df['hq_in_africa']
    )

    # Partner composition
    df['pct_local'] = np.random.beta(a=2, b=5, size=n_obs) + 0.15 * df['hq_in_africa']
    df['pct_regional'] = np.random.beta(a=2, b=8, size=n_obs)
    df['pct_international'] = 1 - df['pct_local'] - df['pct_regional']
    df['pct_international'] = df['pct_international'].clip(0, 1)

    # Experience (cumulative deals)
    df['experience_cumulative'] = np.maximum(1, np.random.lognormal(mean=1.5, sigma=1.0, size=n_obs).astype(int))

    # Number of deals in year
    df['n_deals'] = np.maximum(1, np.random.poisson(lam=2.5, size=n_obs))

    # HRV share: the key outcome
    # Generate with the effect structure we found:
    # - Negative density effect for international VCs
    # - Null density effect for African VCs
    # - Some noise

    logit_score = (
        -1.5  # baseline
        - 0.5 * df['ego_density'] * (1 - df['hq_in_africa'])  # density hurts intl
        + 0.1 * df['ego_density'] * df['hq_in_africa']  # no effect for african
        + 0.3 * df['diversity_combined']
        + 0.1 * np.log1p(df['experience_cumulative'])
        + np.random.normal(0, 0.5, n_obs)
    )

    # Convert to probability
    prob = 1 / (1 + np.exp(-logit_score))

    # Generate HRV share (bounded 0-1)
    df['hrv_share'] = prob.clip(0, 1)

    # Add some zeros (many VCs have no HRV)
    zero_mask = np.random.random(n_obs) < 0.4
    df.loc[zero_mask, 'hrv_share'] = 0

    # Clustering coefficient
    df['avg_clustering'] = np.random.beta(a=5, b=2, size=n_obs)

    # Ego edges (derived from density and size)
    max_edges = df['ego_size'] * (df['ego_size'] - 1) / 2
    df['ego_edges'] = (df['ego_density'] * max_edges).astype(int)

    # Add year dummies
    df['year_2023'] = (df['year'] == 2023).astype(int)
    df['year_2024'] = (df['year'] == 2024).astype(int)

    print(f"  HQ distribution: {df['hq_in_africa'].mean()*100:.1f}% African")
    print(f"  Mean HRV share: {df['hrv_share'].mean()*100:.1f}%")
    print(f"  Mean density: {df['ego_density'].mean():.3f}")

    return df


def main():
    print("=" * 70)
    print(" SYNTHETIC DATA GENERATOR")
    print("=" * 70)

    # Create output directory
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    # Generate panel
    panel = generate_synthetic_panel(n_investors=200, n_years=3)

    # Save
    output_path = SYNTHETIC_DIR / "synthetic_panel.parquet"
    panel.to_parquet(output_path, index=False)
    print(f"\nSaved: {output_path}")

    # Also save as CSV for inspection
    csv_path = SYNTHETIC_DIR / "synthetic_panel.csv"
    panel.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # Create README
    readme = """# Synthetic Data

This directory contains synthetic data for code demonstration purposes.

## Files

- `synthetic_panel.parquet` - Synthetic VC-year panel
- `synthetic_panel.csv` - Same data in CSV format

## Important Notes

1. **This is NOT real data** - it is synthetically generated
2. **Cannot be used to replicate empirical results** - only for code testing
3. **Mimics structure** of real data (same columns, similar distributions)
4. **Generated with fixed seed** (42) for reproducibility

## Usage

```python
import pandas as pd
panel = pd.read_parquet('data/synthetic/synthetic_panel.parquet')
```

## Generation

Generated by `scripts/make_synthetic_data.py` with:
- 200 synthetic investors
- 3 years (2022-2024)
- ~400 VC-year observations

The synthetic data includes:
- Similar distributional properties
- Embedded effect structure (for testing model code)
- NO real investor identities or values
"""

    readme_path = SYNTHETIC_DIR / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme)
    print(f"Saved: {readme_path}")

    print("\n" + "=" * 70)
    print(" SYNTHETIC DATA GENERATED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nPanel shape: {panel.shape}")
    print(f"Columns: {list(panel.columns)}")


if __name__ == "__main__":
    main()
