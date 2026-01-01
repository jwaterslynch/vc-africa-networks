"""Central configuration for VC Africa Networks project."""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Config directory
CONFIG_DIR = PROJECT_ROOT / "config"

# Output directories
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

# Logs
LOGS_DIR = PROJECT_ROOT / "logs"

# Analysis parameters
ANALYSIS_PARAMS = {
    "start_year": 2019,
    "end_year": 2024,
    "burn_in_years": [2019, 2020, 2021],  # For 3-year network windows
    "analysis_years": [2022, 2023, 2024],
    "network_window": 3,  # Years for rolling network computation
    "min_ego_size": 2,  # Minimum partners for density computation
}

# African country ISO codes
AFRICAN_COUNTRIES = [
    'DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CV', 'CM', 'CF', 'TD',
    'KM', 'CG', 'CD', 'CI', 'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET',
    'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'LY', 'MG',
    'MW', 'ML', 'MR', 'MU', 'MA', 'MZ', 'NA', 'NE', 'NG', 'RW',
    'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG',
    'TN', 'UG', 'ZM', 'ZW'
]

# Hard-tech sectors (CORRECTED: fintech excluded)
HARDTECH_SECTORS = {
    'deeptech', 'hardware', 'iot', 'ai', 'ml', 'robotics', 'spacetech',
    'biotech', 'healthtech', 'medtech', 'diagnostics', 'therapeutics',
    'cleantech', 'energy', 'renewables', 'solar', 'battery', 'ev', 'climate_tech',
    'agritech_precision', 'agritech_iot', 'precision_agriculture',
    'supply_chain_tech', 'logistics_tech'
}

# Early stages for HRV definition
EARLY_STAGES = {'Seed', 'Series_A'}
