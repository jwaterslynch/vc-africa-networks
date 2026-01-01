# VC Networks Africa: Data Dictionary & Codebook

**Version:** 1.0  
**Date:** January 2025  
**Project:** VC Syndication Networks and High-Risk Venture Investment in Africa (2015–2024)

---

## 1. Overview

Three source-of-truth tables:
- **deals_rounds** — one row per financing round
- **investors** — one row per investor entity
- **deal_investors** — many-to-many link (one row per participation)

All derived variables (HRV flags, network measures, diversity indices) computed mechanically from these tables.

---

## 2. Table A: deals_rounds

| Field | Type | Allowed Values | Coding Rules |
|-------|------|----------------|--------------|
| deal_id | string | Unique identifier | Format: `D{YYYY}-{NNN}` (e.g., D2023-042) |
| company_id | string | Unique identifier | Format: `C{NNN}` — links to company if needed |
| company_name | string | As appears in source | Standardise capitalisation |
| deal_date | date | YYYY-MM-DD or YYYY-MM | Use YYYY-06-15 if only year known |
| deal_year | integer | 2015–2024 | Derived from deal_date |
| country_primary_ops | string | ISO 3166-1 alpha-2 | See §4.1 for assignment rules |
| sector_tags_raw | string | Comma-separated | Exactly as source reports |
| sector_tags_std | string | Comma-separated | From standard taxonomy (§3.1) |
| stage_raw | string | As appears in source | Keep original terminology |
| stage_std | string | Seed / Series_A / Series_B_plus / Grant / Unknown | See §3.2 |
| stage_inferred | integer | 0 / 1 | 1 if stage_std was inferred (not explicit in source) |
| stage_inference_rule | string | Nullable | Brief note on inference logic (e.g., "amount <$2M → Seed") |
| amount_usd | numeric | Nullable | In millions USD; NULL if undisclosed |
| amount_disclosed | integer | 0 / 1 | 1 = amount known; 0 = undisclosed |
| source_primary | string | Partech / DisruptAfrica / TechCabal / Crunchbase / PitchBook / Other | Primary data source |
| source_secondary | string | Nullable | Corroborating source if any |
| hrv_primary | integer | 0 / 1 | Derived: see §5.1 |
| hrv_hardtech | integer | 0 / 1 | Derived: see §5.1b (robustness) |
| hrv_sector_distance | numeric | 0–1 | Derived: see §5.2 (computed at VC-year level) |
| notes_conflict | string | Free text | Document any ambiguities or source conflicts |
| coder_initials | string | 2–3 chars | Who coded this row |
| coded_date | date | YYYY-MM-DD | When coded |

---

## 3. Coding Taxonomies

### 3.1 Sector Taxonomy (sector_tags_std)

| Standard Tag | Includes | HRV Category? |
|--------------|----------|---------------|
| fintech | Payments, lending, insurtech, wealthtech, banking infra | No |
| healthtech_biotech | Digital health, telemedicine, biotech, medtech, pharmatech | **Yes** |
| cleantech_energy | Solar, off-grid, EV, climate tech, energy storage | **Yes** |
| agritech_hardware | Farm inputs, precision ag hardware, post-harvest tech | **Yes** |
| agritech_software | Marketplace, farm management software, agri-fintech | No |
| logistics_mobility | Last-mile, fleet, ride-hailing, freight | No |
| edtech | E-learning, skills platforms, school management | No |
| ecommerce_retail | Marketplaces, D2C, retail tech | No |
| proptech | Real estate tech, construction tech | No |
| hrtech_future_of_work | Recruitment, payroll, remote work tools | No |
| enterprise_saas | B2B SaaS, productivity tools | No |
| media_entertainment | Content, gaming, streaming | No |
| industrial_deeptech | Manufacturing tech, robotics, advanced materials | **Yes** |
| other | Does not fit above | No |

**Coding rule:** If venture spans multiple sectors, list ALL applicable tags. HRV = 1 if ANY tag is in HRV set.

### 3.2 Stage Taxonomy (stage_std)

| Standard Stage | Source Terms Mapped |
|----------------|---------------------|
| Seed | Pre-seed, Seed, Angel, Friends & Family |
| Series_A | Series A, Round A |
| Series_B_plus | Series B, C, D, E+, Growth, Late Stage |
| Grant | Grant, Non-dilutive |
| Unknown | Undisclosed, not stated |

**Coding rule:** If source says "early stage" without specifics, code as Seed unless amount suggests otherwise (>$5M typically = Series A+).

---

## 4. Investor Coding Rules

### 4.1 Table B: investors

| Field | Type | Allowed Values | Coding Rules |
|-------|------|----------------|--------------|
| investor_id | string | Unique identifier | Format: `I{NNN}` |
| investor_name_raw | string | As appears in sources | May have multiple variants |
| investor_name_canonical | string | Standardised name | Single canonical form |
| investor_type | string | IVC / CVC / DFI / Angel_Family / Accelerator / Other / Unknown | See §4.2 |
| hq_country | string | ISO 3166-1 alpha-2 | Legal HQ or primary office |
| hq_in_africa | integer | 0 / 1 | 1 if hq_country in Africa |
| diaspora_flag | integer | 0 / 1 / -1 | 1 = diaspora-led; -1 = unknown |
| website | string | URL | Primary website |
| classification_confidence | string | High / Medium / Low | Confidence in type/HQ coding |
| merge_notes | string | Free text | Document any entity resolution decisions |
| coder_initials | string | 2–3 chars | |
| coded_date | date | YYYY-MM-DD | |

**Note:** Geographic diversity categories (Local/Regional/International) are NOT stored here — they are computed dynamically during analysis based on the focal VC's primary market (see §4.3).

### 4.2 Investor Type Definitions

| Type | Definition | Examples |
|------|------------|----------|
| IVC | Independent VC fund (GP/LP structure, financial return mandate) | Partech Africa, TLcom, Norrsken22 |
| CVC | Corporate venture arm (strategic + financial mandate) | Google Ventures, Naspers/Prosus, Orange Ventures |
| DFI | Development finance institution (development mandate, often concessional) | IFC, CDC/BII, Proparco, AfDB |
| Angel_Family | Individual angels, family offices, HNW investors | Named individuals, family office vehicles |
| Accelerator | Accelerator/incubator making equity investments | Y Combinator, Techstars, Flat6Labs |
| Other | Doesn't fit above (e.g., crowdfunding, SPVs) | |
| Unknown | Cannot determine from available sources | |

**Decision rules:**
- If fund has both DFI and private LPs, classify by GP mandate (usually IVC)
- If corporate invests via separate fund vehicle, classify as CVC
- If angel invests via personal holding company, still Angel_Family

### 4.3 Geographic Classification for Diversity (Computed Dynamically)

**Important:** Local/Regional/International is NOT stored in the investors table. It is computed during diversity calculation because it depends on the focal VC's primary market.

**Step 1: Store only stable attributes in investors table**
- hq_country (ISO code)
- hq_in_africa (0/1)

**Step 2: Determine focal VC's "primary Africa market" (dynamic, per VC-year)**

Algorithm:
1. In rolling 3-year window (t-3 to t-1), count deals by country_primary_ops for focal VC
2. Primary market = modal country (most frequent)
3. **Tie-breaker:** If tied, use country of earliest deal in window
4. **Fallback:** If VC has no deals in window, use country of first observed Africa investment
5. **Missing:** If still ambiguous, flag geographic diversity as missing for that VC-year

**Step 3: Classify each partner relative to focal VC's primary market (at analysis time)**

```python
def classify_partner(partner_hq_country, partner_hq_in_africa, focal_vc_primary_market):
    if partner_hq_country == focal_vc_primary_market:
        return "Local"
    elif partner_hq_in_africa == 1:
        return "Regional"
    else:
        return "International"
```

**Step 4: Compute Blau index over classified partners**

---

## 5. Derived Variables: HRV Definitions

### 5.1 HRV Primary (Deal-Level)

```
hrv_primary = 1 IF:
  stage_std ∈ {Seed, Series_A}
  AND
  sector_tags_std ∩ {healthtech_biotech, cleantech_energy, agritech_hardware, industrial_deeptech} ≠ ∅
ELSE:
  hrv_primary = 0
```

**Rationale:** Primary HRV captures "early-stage + high technological uncertainty" — the combination that makes due diligence hardest and soft information most valuable.

### 5.1b HRV Hard-Tech Only (Robustness DV)

```
hrv_hardtech = 1 IF:
  sector_tags_std ∩ {healthtech_biotech, cleantech_energy, agritech_hardware, industrial_deeptech} ≠ ∅
ELSE:
  hrv_hardtech = 0
```

**Purpose:** Tests whether results hold for hard-tech regardless of stage.

### 5.2 HRV Share (VC-Year Level)

```
HRV_Share_{it} = Σ(hrv_primary) / Σ(all deals) for VC i in year t
```

### 5.3 HRV Share Early (Key Robustness)

```
HRV_Share_Early_{it} = Σ(hrv_primary AND stage_std ∈ {Seed, Series_A}) / Σ(stage_std ∈ {Seed, Series_A})
```

**Purpose:** Separates "hard-tech selection" from "early-stage orientation"

### 5.4 Sector Distance (Robustness HRV)

Computed at VC-year level:
```
For each deal d by VC i in year t:
  sector_distance_d = 1 - Jaccard(sector_tags_std_d, VC_i_prior_sector_tags)
  
Where VC_i_prior_sector_tags = union of all sector tags from VC i's deals before year t
```

Average across deals to get VC-year measure.

---

## 6. Table C: deal_investors

| Field | Type | Allowed Values | Coding Rules |
|-------|------|----------------|--------------|
| deal_id | string | FK to deals_rounds | |
| investor_id | string | FK to investors | |
| role | string | Lead / Participant / Unknown | Lead if explicitly stated; else Participant or Unknown |
| source_for_participation | string | Source documenting this participation | |

---

## 7. Network Construction Specifications

### 7.0 Timing Convention

**For each VC-year t, we compute network measures from co-investments in years t-3 to t-1; these measures therefore predate investments in year t.**

In notation: Density_{it} refers to VC i's ego-network density computed from the window ending at t-1, merged into year t for analysis. This ensures temporal ordering: network structure → investment outcomes.

### 7.1 Primary Network Definition

- **Nodes:** Investors with ≥1 deal in window
- **Edges:** Undirected; edge exists if two investors co-invested in same financing round (same deal_id)
- **Ties:** Binary (edge exists or not)
- **Window:** Rolling 3-year (t-3 to t-1)

### 7.2 Robustness Network: Company-Based Ties

Edge exists if two investors invested in same company within window (regardless of whether same round).

### 7.3 Ego-Network Measures

For focal VC i in year t:
- **k_{it}** = number of unique partners (degree)
- **E_{it}** = number of edges among partners (ties between alters)
- **Density_{it}** = 2 × E_{it} / (k_{it} × (k_{it} - 1))

### 7.4 Inclusion Rules

| Rule | Primary Sample | Robustness |
|------|----------------|------------|
| Minimum partners (k) | k ≥ 2 | k ≥ 0 (include isolates with indicator) |
| Minimum deals in window | ≥ 1 | Same |
| First valid year | 2018 (full 3-yr window) | 2016–2017 with window_length control |

---

## 8. Quality Checks (Built Into Workflow)

### 8.1 Data Coverage Checks

| Check | Threshold | Action if Fail |
|-------|-----------|----------------|
| Deal count vs Partech reported | ≥95% coverage | Investigate missing deals |
| Investor entity duplicates | Top 30 by deal count manually verified | Merge or document distinction |
| Double-coding agreement (type) | κ ≥ 0.80 | Revise codebook, re-code |
| Double-coding agreement (HQ) | κ ≥ 0.80 | Revise codebook, re-code |
| HRV classification spot-check | 20 random deals verified | Adjust taxonomy if systematic errors |

### 8.2 Network Sanity Checks (Before Modelling)

| Check | Warning Sign | Action |
|-------|--------------|--------|
| Distribution of k (ego-network size) | Mostly 0–1 | Entity resolution issues; check for missed syndications |
| Distribution of density | Mostly 0 or 1 | Coverage gaps; small networks inflate density |
| % VCs in giant component by period | < 50% | Fragmented network; check data completeness |
| Mean ties per VC | < 2 | May need to relax k ≥ 2 threshold |

### 8.3 Raw vs Standardised Policy

**Mandatory rule:** 
- `*_raw` fields = verbatim from source (never edit after initial entry)
- `*_std` fields = mapped to standard taxonomy for analysis
- **No manual edits to `*_std` without a data_diary entry**

This ensures auditability when reconciling disputes or explaining coding decisions to reviewers.

---

## 9. Changelog

| Date | Version | Changes |
|------|---------|---------|
| Jan 2025 | 1.0 | Initial codebook aligned with Design Freeze v2 |
