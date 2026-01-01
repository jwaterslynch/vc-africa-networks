# Data Provenance

## Primary Data Source

**Africa: The Big Deal – Startup Deals Database**

Purchased via Gumroad on 1 January 2025 under an Individual Licence.

Dataset version: January 2019 – November 2025, monthly updated Excel file.

Source provides deal-level records including disclosed investor names, stage, sector, country, and links to press releases.

File accessed via purchaser's account; unauthorised redistribution prohibited.

## File Locations

| Location | Path | Purpose |
|----------|------|---------|
| Project | `data/raw/atbd_2019_2025_20251201.xlsx` | Working copy |
| Backup | `/Volumes/Jules Hardrive/data/atbd/atbd_2019_2025_20251201.xlsx` | Cold backup |

## Access

- **Password:** Stored in `.env` file (not committed to git)
- **Password backup:** Documented in `data/raw/README.md`

## Version History

| Version Date | File | Password | Notes |
|--------------|------|----------|-------|
| 2025-12-01 | atbd_2019_2025_20251201.xlsx | qZp84nHrS1wF29ktB6mJ3vLd | Initial purchase |

## Purchase Documentation

Store receipts and licence documentation in `docs/purchase/`:
- `atbd_receipt_2025-01-01.pdf` - Gumroad receipt
- `atbd_license_individual.txt` - Licence terms

## Data Processing Policy

1. Raw files in `data/raw/` are **never modified**
2. All transformations happen via scripts to `data/interim/` and `data/processed/`
3. Processing scripts must be reproducible from raw data
4. Entity resolution decisions logged in `data/interim/entity_resolution_log.csv`
