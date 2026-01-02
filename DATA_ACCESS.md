# Data Access Statement

## Overview

This research uses proprietary data from **Africa: The Big Deal (ATBD)**, a commercial database of startup funding deals in Africa. The data cannot be redistributed, but the analysis can be fully replicated by researchers who obtain their own license.

---

## Data Source

**Africa: The Big Deal (ATBD)**
- Website: https://thebigdeal.com/database
- License type: Individual License (annual subscription)
- Coverage: Startup funding deals in Africa, 2019-present
- Update frequency: Monthly

### What the data contains:
- Deal-level records (company, date, amount, stage, sector, country)
- Investor names per deal (comma-separated)
- Investor profiles (name, HQ location, type)

### What we use:
- 4,173 deals (2019-2024)
- 2,457 unique investors
- 901 VC-year observations for analysis (2022-2024 outcomes)

---

## Obtaining the Data

1. **Purchase a license** at https://thebigdeal.com/database
   - Cost: ~$219-229/year (Individual License)
   - Provides: Monthly updated Excel file

2. **Download the database file**
   - Filename pattern: `*Africa*Big*Deal*.xlsx` or similar
   - Place in: `data/raw/`

3. **Note the password** (provided on download page)
   - Store in: `.env` file as `ATBD_PASSWORD=your_password`

---

## Data Fingerprint

To verify you have the same data version used in this paper, compare your file's SHA256 hash against the stored fingerprint.

### Check your data:

```bash
# On macOS/Linux
shasum -a 256 data/raw/your_atbd_file.xlsx

# Compare to stored fingerprint
cat data/DATA_FINGERPRINTS.json | grep sha256
```

### Stored fingerprint (paper version):

See `data/DATA_FINGERPRINTS.json` for:
- Expected filename pattern
- File size
- SHA256 hash
- Download date

**Note:** ATBD updates monthly. If your file hash differs, you have a different version. Results should be similar but may not match exactly.

---

## Replication Without Data

If you do not have access to the proprietary data, you can still:

1. **View all results**: Pre-computed outputs are in `outputs/`
2. **Verify code runs**: Use synthetic data mode
3. **Inspect all statistics**: See `outputs/paper_numbers.json`

### Run demonstration mode:

```bash
python scripts/replicate.py --demo
```

### Run on synthetic data:

```bash
python scripts/replicate.py --synthetic
```

---

## Replication With Data

If you have obtained the ATBD data:

1. Place the Excel file in `data/raw/`
2. Create `.env` with `ATBD_PASSWORD=your_password`
3. Run the full pipeline:

```bash
python scripts/replicate.py --full
```

4. Verify outputs match:

```bash
python scripts/replicate.py --verify
```

---

## License Restrictions

The ATBD Individual License **prohibits redistribution** of:
- The raw Excel file
- Derived datasets containing identifiable investor/company information
- Any extract that could substitute for the original database

We therefore provide:
- ✓ All code (fully open)
- ✓ Pre-computed aggregate outputs
- ✓ Synthetic data for code testing
- ✓ Data fingerprints for verification
- ✗ Raw data files
- ✗ Processed panel with identifiers

---

## Third-Party Verification

For journal review or replication verification:

1. **Data editors** can contact the authors for a controlled verification run
2. **Researchers with ATBD access** can independently replicate
3. **Output hashes** in `outputs/OUTPUT_FINGERPRINTS.json` verify exact reproducibility

---

## Contact

For questions about data access or replication:
- Open an issue on the GitHub repository
- Contact the corresponding author

---

## Citation

If using this replication package, please cite:

```
[Author(s)]. (2026). VC Syndication Networks and High-Risk Venture
Investment in Africa. [Journal].
Replication materials: https://github.com/[repo]
```

Data citation:

```
Africa: The Big Deal. (2025). Startup Deals Database.
https://thebigdeal.com/database
```
