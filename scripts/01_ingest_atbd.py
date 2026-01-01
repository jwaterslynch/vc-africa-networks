#!/usr/bin/env python3
"""
ATBD Data Ingestion Script

Loads Africa: The Big Deal Excel file and creates three normalized tables:
- deals: deal-level records
- investors: investor entities
- deal_investors: junction table linking deals to investors

Outputs to data/interim/ as parquet files.
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import msoffcrypto
import io
from dotenv import load_dotenv

from src.config import (
    RAW_DATA_DIR, INTERIM_DATA_DIR, LOGS_DIR,
    EARLY_STAGES, HARDTECH_SECTORS
)

# Setup logging
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f'ingest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

RAW_FILE = RAW_DATA_DIR / "atbd_2019_2025_20251201.xlsx"

# Stage mapping: raw → standardized
STAGE_MAPPING = {
    # Early stages
    'pre-seed': 'Seed',
    'seed': 'Seed',
    # Series A
    'pre-series a': 'Series_A',
    'series a': 'Series_A',
    'series a extension': 'Series_A',
    # Series B
    'pre-series b': 'Series_B',
    'series b': 'Series_B',
    'series b2': 'Series_B',
    # Series C
    'pre-series c': 'Series_C',
    'series c': 'Series_C',
    # Growth / Later
    'series d': 'Growth',
    'series e': 'Growth',
    # Other types
    'grant': 'Grant',
    'debt': 'Debt',
    'bonds': 'Debt',
    'green bonds': 'Debt',
    'm&a': 'M&A',
    'ipo': 'IPO',
    'pipo': 'IPO',
    'pipe': 'Other',
    'secondary': 'Other',
    # Ambiguous - needs inference
    'venture round': 'Venture_Round',
}

# Amount-based stage inference thresholds (in $M)
AMOUNT_THRESHOLDS = {
    'Seed': (0, 2),           # <$2M
    'Series_A': (2, 8),       # $2-8M
    'Series_B': (8, 25),      # $8-25M
    'Growth': (25, float('inf'))  # >$25M
}

# Coverage regime thresholds by year
COVERAGE_REGIMES = {
    2019: ('1M+', 1.0),
    2020: ('500K+', 0.5),
    2021: ('100K+', 0.1),
    2022: ('100K+', 0.1),
    2023: ('100K+', 0.1),
    2024: ('100K+', 0.1),
    2025: ('100K+', 0.1),
}

# HQ Region to in_africa mapping
AFRICA_REGIONS = {'Africa'}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_encrypted_excel(filepath: Path, password: str) -> dict:
    """Load password-protected Excel file into dict of DataFrames."""
    logger.info(f"Loading encrypted Excel: {filepath}")

    with open(filepath, 'rb') as f:
        file = msoffcrypto.OfficeFile(f)
        file.load_key(password=password)

        decrypted = io.BytesIO()
        file.decrypt(decrypted)
        decrypted.seek(0)

        xl = pd.ExcelFile(decrypted)
        sheets = {}
        for sheet_name in xl.sheet_names:
            decrypted.seek(0)
            sheets[sheet_name] = pd.read_excel(decrypted, sheet_name=sheet_name)
            logger.info(f"  Loaded sheet '{sheet_name}': {sheets[sheet_name].shape}")

        return sheets


def normalize_string(s: str) -> str:
    """Normalize string for matching."""
    if pd.isna(s):
        return ''
    return str(s).strip().lower()


def infer_stage_from_amount(amount_m: float) -> str:
    """Infer stage from deal amount in millions USD."""
    if pd.isna(amount_m) or amount_m <= 0:
        return 'Unknown'

    for stage, (low, high) in AMOUNT_THRESHOLDS.items():
        if low <= amount_m < high:
            return stage

    return 'Growth'  # Default for very large amounts


def parse_investor_string(investor_str: str) -> list:
    """Parse comma-separated investor string into list of names."""
    if pd.isna(investor_str):
        return []

    # Handle common NA values
    if str(investor_str).strip().lower() in ['n.a', 'n.a.', 'na', 'nan', '']:
        return []

    # Split on comma, strip whitespace
    investors = [inv.strip() for inv in str(investor_str).split(',')]

    # Filter empty strings
    return [inv for inv in investors if inv and inv.lower() not in ['n.a', 'n.a.', 'na']]


def map_hq_to_country_code(hq: str) -> str:
    """Map HQ string to ISO country code (simplified)."""
    # Common mappings - extend as needed
    HQ_MAP = {
        'u.s.': 'US',
        'u.s': 'US',
        'usa': 'US',
        'united states': 'US',
        'u.k.': 'GB',
        'uk': 'GB',
        'united kingdom': 'GB',
        'u.a.e.': 'AE',
        'uae': 'AE',
        'south africa': 'ZA',
        'nigeria': 'NG',
        'kenya': 'KE',
        'egypt': 'EG',
        'ghana': 'GH',
        'morocco': 'MA',
        'tanzania': 'TZ',
        'uganda': 'UG',
        'rwanda': 'RW',
        'senegal': 'SN',
        'mauritius': 'MU',
        'france': 'FR',
        'germany': 'DE',
        'netherlands': 'NL',
        'sweden': 'SE',
        'switzerland': 'CH',
        'japan': 'JP',
        'china': 'CN',
        'singapore': 'SG',
        'india': 'IN',
        'canada': 'CA',
        'saudi arabia': 'SA',
        'tunisia': 'TN',
        'cote d\'ivoire': 'CI',
        'ivory coast': 'CI',
        'ethiopia': 'ET',
        'cameroon': 'CM',
        'zambia': 'ZM',
        'zimbabwe': 'ZW',
        'botswana': 'BW',
        'namibia': 'NA',
        'malawi': 'MW',
        'mozambique': 'MZ',
        'angola': 'AO',
        'drc': 'CD',
        'congo': 'CG',
        'benin': 'BJ',
        'togo': 'TG',
        'mali': 'ML',
        'burkina faso': 'BF',
        'niger': 'NE',
        'gambia': 'GM',
        'liberia': 'LR',
        'sierra leone': 'SL',
        'guinea': 'GN',
        'algeria': 'DZ',
        'libya': 'LY',
        'sudan': 'SD',
        'somalia': 'SO',
        'eritrea': 'ER',
        'djibouti': 'DJ',
        'madagascar': 'MG',
        'seychelles': 'SC',
        'comoros': 'KM',
        'cabo verde': 'CV',
        'cape verde': 'CV',
        'sao tome': 'ST',
        'eswatini': 'SZ',
        'lesotho': 'LS',
        'gabon': 'GA',
        'equatorial guinea': 'GQ',
        'central african republic': 'CF',
        'chad': 'TD',
        'south sudan': 'SS',
        'burundi': 'BI',
        'spain': 'ES',
        'italy': 'IT',
        'belgium': 'BE',
        'austria': 'AT',
        'portugal': 'PT',
        'ireland': 'IE',
        'denmark': 'DK',
        'norway': 'NO',
        'finland': 'FI',
        'poland': 'PL',
        'australia': 'AU',
        'new zealand': 'NZ',
        'brazil': 'BR',
        'mexico': 'MX',
        'israel': 'IL',
        'korea': 'KR',
        'south korea': 'KR',
        'taiwan': 'TW',
        'hong kong': 'HK',
        'indonesia': 'ID',
        'malaysia': 'MY',
        'thailand': 'TH',
        'vietnam': 'VN',
        'philippines': 'PH',
        'pakistan': 'PK',
        'bangladesh': 'BD',
        'n.a': None,
        'n.a.': None,
    }

    if pd.isna(hq):
        return None

    normalized = normalize_string(hq)
    return HQ_MAP.get(normalized, hq.upper()[:2] if len(hq) >= 2 else None)


# =============================================================================
# MAIN PROCESSING FUNCTIONS
# =============================================================================

def process_investors_sheet(investors_df: pd.DataFrame) -> pd.DataFrame:
    """Process Investors sheet into normalized investors table."""
    logger.info("Processing Investors sheet...")

    investors = pd.DataFrame()

    # Generate investor IDs
    investors['investor_id'] = [f'INV-{i:04d}' for i in range(1, len(investors_df) + 1)]

    # Canonical name
    investors['name_canonical'] = investors_df['Investor'].str.strip()
    investors['name_normalized'] = investors['name_canonical'].apply(normalize_string)

    # Geography
    investors['hq_raw'] = investors_df['HQ']
    investors['hq_region'] = investors_df['HQ Region']
    investors['hq_country'] = investors_df['HQ'].apply(map_hq_to_country_code)
    investors['hq_in_africa'] = investors_df['HQ Region'].apply(
        lambda x: 1 if x == 'Africa' else 0
    )

    # Deal counts (for reference)
    investors['total_deals_2019_2025'] = investors_df['2019-25 deals']

    logger.info(f"  Created {len(investors)} investor records")
    logger.info(f"  Africa HQ: {investors['hq_in_africa'].sum()}")
    logger.info(f"  Non-Africa HQ: {(investors['hq_in_africa'] == 0).sum()}")

    return investors


def process_deals_sheet(deals_df: pd.DataFrame) -> pd.DataFrame:
    """Process Deals sheet into normalized deals table."""
    logger.info("Processing Deals sheet...")

    deals = pd.DataFrame()

    # Generate deal IDs
    deals['deal_id'] = [f'D{deals_df.iloc[i]["Deal Year"]}-{i:04d}'
                        for i in range(len(deals_df))]

    # Basic fields
    deals['company_name'] = deals_df['Start-up name'].str.strip()
    deals['website'] = deals_df['Website']
    deals['deal_date'] = pd.to_datetime(deals_df['Deal Date'], errors='coerce')
    deals['deal_year'] = deals_df['Deal Year'].astype(int)

    # Geography
    deals['country_raw'] = deals_df['Country']
    deals['country_primary_ops'] = deals_df['Country'].apply(map_hq_to_country_code)
    deals['region'] = deals_df['Region']

    # Sector
    deals['sector_raw'] = deals_df['Sector']
    deals['climate_tech'] = deals_df['Climate Tech'].apply(
        lambda x: 1 if str(x).strip().lower() == 'yes' else 0
    )

    # Stage
    deals['stage_raw'] = deals_df['Type']
    deals['stage_std'] = deals_df['Type'].apply(
        lambda x: STAGE_MAPPING.get(normalize_string(x), 'Other')
    )

    # Amount
    deals['amount_usd_m'] = pd.to_numeric(deals_df['Amount raised $M'], errors='coerce')
    deals['amount_disclosed'] = deals['amount_usd_m'].notna().astype(int)
    deals['bracket'] = deals_df['Bracket']

    # Infer stage for "Venture Round" based on amount
    venture_round_mask = deals['stage_std'] == 'Venture_Round'
    deals.loc[venture_round_mask, 'stage_inferred'] = 1
    deals.loc[~venture_round_mask, 'stage_inferred'] = 0

    # Apply amount-based inference
    inferred_stages = deals.loc[venture_round_mask, 'amount_usd_m'].apply(infer_stage_from_amount)
    deals.loc[venture_round_mask, 'stage_std'] = inferred_stages

    # Log inference stats
    n_venture = venture_round_mask.sum()
    n_inferred = (deals['stage_inferred'] == 1).sum()
    logger.info(f"  Venture Round deals: {n_venture}")
    logger.info(f"  Stage inferred from amount: {n_inferred}")
    logger.info(f"  Stage inference breakdown:")
    for stage in deals.loc[venture_round_mask, 'stage_std'].value_counts().items():
        logger.info(f"    {stage[0]}: {stage[1]}")

    # Coverage regime
    deals['coverage_regime'] = deals['deal_year'].apply(
        lambda y: COVERAGE_REGIMES.get(y, ('Unknown', 0))[0]
    )
    deals['coverage_threshold_m'] = deals['deal_year'].apply(
        lambda y: COVERAGE_REGIMES.get(y, ('Unknown', 0))[1]
    )

    # Equity flag
    deals['equity'] = deals_df['Equity'].apply(
        lambda x: 1 if str(x).strip().lower() == 'yes' else 0
    )

    # Exit flag
    deals['exit'] = deals_df['Exit'].apply(
        lambda x: 1 if pd.notna(x) and str(x).strip().lower() not in ['', 'n.a', 'n.a.'] else 0
    )

    # Y Combinator flag
    deals['y_combinator'] = deals_df['Y Combinator'].apply(
        lambda x: 1 if str(x).strip().lower() == 'yes' else 0
    )

    # Founder info
    deals['n_founders'] = pd.to_numeric(deals_df['# of Founders'], errors='coerce')
    deals['woman_cofounder'] = deals_df['Woman co-founder'].apply(
        lambda x: 1 if str(x).strip().lower() == 'yes' else 0
    )

    # Source
    deals['source_link'] = deals_df['Link to news']

    # Raw investor string (for junction table creation)
    deals['investors_raw'] = deals_df['Investors']

    logger.info(f"  Created {len(deals)} deal records")
    logger.info(f"  Year range: {deals['deal_year'].min()} - {deals['deal_year'].max()}")
    logger.info(f"  Countries: {deals['country_raw'].nunique()}")

    return deals


def create_deal_investors_junction(
    deals: pd.DataFrame,
    investors: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create deal_investors junction table by parsing investor strings.

    Returns:
        deal_investors: junction table
        unmatched: DataFrame of investor names not found in Investors sheet
    """
    logger.info("Creating deal_investors junction table...")

    # Build lookup from normalized name to investor_id
    investor_lookup = dict(zip(
        investors['name_normalized'],
        investors['investor_id']
    ))

    # Also create lookup from canonical name
    canonical_lookup = dict(zip(
        investors['name_canonical'].str.strip(),
        investors['investor_id']
    ))

    records = []
    unmatched_names = []

    for _, deal in deals.iterrows():
        deal_id = deal['deal_id']
        investor_names = parse_investor_string(deal['investors_raw'])

        for inv_name in investor_names:
            # Try exact match first
            inv_id = canonical_lookup.get(inv_name.strip())

            # Try normalized match
            if inv_id is None:
                inv_id = investor_lookup.get(normalize_string(inv_name))

            if inv_id is not None:
                records.append({
                    'deal_id': deal_id,
                    'investor_id': inv_id,
                    'investor_name_raw': inv_name
                })
            else:
                unmatched_names.append({
                    'deal_id': deal_id,
                    'investor_name_raw': inv_name,
                    'investor_name_normalized': normalize_string(inv_name)
                })

    deal_investors = pd.DataFrame(records)
    unmatched = pd.DataFrame(unmatched_names)

    # Stats
    n_links = len(deal_investors)
    n_deals_with_investors = deal_investors['deal_id'].nunique()
    n_unique_investors = deal_investors['investor_id'].nunique()
    n_unmatched = len(unmatched)
    n_unmatched_unique = unmatched['investor_name_normalized'].nunique() if len(unmatched) > 0 else 0

    logger.info(f"  Deal-investor links: {n_links}")
    logger.info(f"  Deals with investors: {n_deals_with_investors}")
    logger.info(f"  Unique investors matched: {n_unique_investors}")
    logger.info(f"  Unmatched investor mentions: {n_unmatched}")
    logger.info(f"  Unique unmatched names: {n_unmatched_unique}")

    if n_unmatched_unique > 0:
        logger.warning(f"  Top unmatched names:")
        top_unmatched = unmatched['investor_name_raw'].value_counts().head(10)
        for name, count in top_unmatched.items():
            logger.warning(f"    '{name}': {count}")

    return deal_investors, unmatched


def generate_summary_stats(
    deals: pd.DataFrame,
    investors: pd.DataFrame,
    deal_investors: pd.DataFrame
) -> dict:
    """Generate summary statistics for stop/go check."""
    logger.info("Generating summary statistics...")

    stats = {}

    # Deal counts
    stats['total_deals'] = len(deals)
    stats['deals_by_year'] = deals['deal_year'].value_counts().sort_index().to_dict()
    stats['deals_by_stage'] = deals['stage_std'].value_counts().to_dict()
    stats['deals_with_amount'] = deals['amount_disclosed'].sum()
    stats['deals_inferred_stage'] = (deals['stage_inferred'] == 1).sum()

    # Investor counts
    stats['total_investors'] = len(investors)
    stats['investors_africa_hq'] = (investors['hq_in_africa'] == 1).sum()
    stats['investors_matched_in_deals'] = deal_investors['investor_id'].nunique()

    # Network potential
    stats['deal_investor_links'] = len(deal_investors)
    stats['deals_with_multiple_investors'] = (
        deal_investors.groupby('deal_id').size() > 1
    ).sum()
    stats['avg_investors_per_deal'] = deal_investors.groupby('deal_id').size().mean()

    # Coverage
    stats['countries'] = deals['country_raw'].nunique()
    stats['sectors'] = deals['sector_raw'].nunique()

    # Early-stage deals (for HRV)
    early_stage_mask = deals['stage_std'].isin(['Seed', 'Series_A'])
    stats['early_stage_deals'] = early_stage_mask.sum()
    stats['early_stage_pct'] = early_stage_mask.mean() * 100

    return stats


def print_summary_report(stats: dict):
    """Print formatted summary report."""
    print("\n" + "="*60)
    print("ATBD INGESTION SUMMARY")
    print("="*60)

    print("\n📊 DEALS")
    print(f"  Total deals: {stats['total_deals']:,}")
    print(f"  With disclosed amount: {stats['deals_with_amount']:,}")
    print(f"  Stage inferred from amount: {stats['deals_inferred_stage']:,}")
    print(f"  Early-stage (Seed/Series A): {stats['early_stage_deals']:,} ({stats['early_stage_pct']:.1f}%)")

    print("\n  By year:")
    for year, count in sorted(stats['deals_by_year'].items()):
        print(f"    {year}: {count:,}")

    print("\n  By stage:")
    for stage, count in sorted(stats['deals_by_stage'].items(), key=lambda x: -x[1]):
        print(f"    {stage}: {count:,}")

    print("\n👥 INVESTORS")
    print(f"  Total in database: {stats['total_investors']:,}")
    print(f"  Africa HQ: {stats['investors_africa_hq']:,}")
    print(f"  Matched in deals: {stats['investors_matched_in_deals']:,}")

    print("\n🔗 NETWORK")
    print(f"  Deal-investor links: {stats['deal_investor_links']:,}")
    print(f"  Deals with 2+ investors: {stats['deals_with_multiple_investors']:,}")
    print(f"  Avg investors per deal: {stats['avg_investors_per_deal']:.2f}")

    print("\n🌍 COVERAGE")
    print(f"  Countries: {stats['countries']}")
    print(f"  Sectors: {stats['sectors']}")

    print("\n" + "="*60)
    print("✅ STOP/GO PRELIMINARY CHECK")
    print("="*60)

    # Check thresholds
    checks = []

    if stats['deals_with_multiple_investors'] >= 100:
        checks.append("✅ Syndicated deals >= 100")
    else:
        checks.append(f"⚠️  Syndicated deals = {stats['deals_with_multiple_investors']} (need >= 100)")

    if stats['early_stage_deals'] >= 200:
        checks.append("✅ Early-stage deals >= 200")
    else:
        checks.append(f"⚠️  Early-stage deals = {stats['early_stage_deals']} (want >= 200)")

    if stats['investors_matched_in_deals'] >= 100:
        checks.append("✅ Active investors >= 100")
    else:
        checks.append(f"⚠️  Active investors = {stats['investors_matched_in_deals']} (need >= 100)")

    for check in checks:
        print(f"  {check}")

    print("\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main ingestion pipeline."""
    logger.info("="*60)
    logger.info("ATBD INGESTION PIPELINE")
    logger.info("="*60)

    # Load environment
    load_dotenv(PROJECT_ROOT / '.env')
    password = os.getenv('ATBD_PASSWORD')

    if not password:
        logger.error("ATBD_PASSWORD not found in .env file")
        sys.exit(1)

    # Check raw file exists
    if not RAW_FILE.exists():
        logger.error(f"Raw file not found: {RAW_FILE}")
        sys.exit(1)

    # Load Excel
    sheets = load_encrypted_excel(RAW_FILE, password)

    # Process sheets
    investors = process_investors_sheet(sheets['Investors 2019-2025'])
    deals = process_deals_sheet(sheets['Deals 2019-2025'])
    deal_investors, unmatched = create_deal_investors_junction(deals, investors)

    # Generate stats
    stats = generate_summary_stats(deals, investors, deal_investors)
    print_summary_report(stats)

    # Create output directory
    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    logger.info("Saving to parquet files...")

    # Remove raw investor string before saving deals
    deals_clean = deals.drop(columns=['investors_raw'])

    deals_clean.to_parquet(INTERIM_DATA_DIR / 'deals.parquet', index=False)
    investors.to_parquet(INTERIM_DATA_DIR / 'investors.parquet', index=False)
    deal_investors.to_parquet(INTERIM_DATA_DIR / 'deal_investors.parquet', index=False)

    if len(unmatched) > 0:
        unmatched.to_parquet(INTERIM_DATA_DIR / 'unmatched_investors.parquet', index=False)
        unmatched.to_csv(INTERIM_DATA_DIR / 'unmatched_investors.csv', index=False)
        logger.info(f"  Saved unmatched investors for review: {len(unmatched)} records")

    logger.info(f"  Saved deals.parquet: {len(deals_clean)} rows")
    logger.info(f"  Saved investors.parquet: {len(investors)} rows")
    logger.info(f"  Saved deal_investors.parquet: {len(deal_investors)} rows")

    # Save summary stats
    import json
    with open(INTERIM_DATA_DIR / 'ingestion_stats.json', 'w') as f:
        json.dump(stats, f, indent=2, default=str)

    logger.info("="*60)
    logger.info("INGESTION COMPLETE")
    logger.info("="*60)

    return deals_clean, investors, deal_investors, stats


if __name__ == '__main__':
    main()
