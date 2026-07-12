# Consolidated data suite — data dictionary

Tidy, analysis-ready CSVs that feed the pipeline in
`01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`. Beach names are standardized to
`Long Beach`, `Twin Harbors`, `Copalis`, `Mocrocks`, `Kalaloch` throughout. These files are
derived from the authoritative sources listed under "Source" and reflect the **completed
2022-23 season** (the 4–14 May 2023 tide series restored).

Every column is read with `janitor::clean_names()` in the pipeline, so a header such as
`effort (workbook)` is referenced in R as `effort_workbook`.

## Raw / input tables (the pipeline computes from these)

| File | Grain | Key columns | Figures | Source |
|---|---|---|---|---|
| `creel_events.csv` | one creel event (beach-day) | beach, date, season, effort, harvest, cpue, cf, people, n_census, wastage | 7 | HarvestDB extract `derived/harvest_by_event.csv` |
| `harvest_by_beach_day.csv` | beach × day | beach, date, season, effort, harvest | 4, 12 | HarvestDB extract `derived/` |
| `harvest_by_beach_season.csv` | beach × season | beach, season_label, total_effort, total_harvest, mean_cpue | (context) | HarvestDB extract `derived/` |
| `dig_days.csv` | beach × dig-day register | season, beach, date, monitored (Yes/Partial/No), effort (workbook), effort (database), donor beach(es), estimation method | 4, 12 | `WDFW_RazorClam_DigDay_Register_2007_2026.xlsx` → Dig_Days |
| `beach_day_2022_23_complete.csv` | beach × day, 2022-23 only | season, beach, date, monitored, effort_workbook, effort_database, estimation_method, donor_beach | 4, 12 | parsed from the **completed** `2022 Fall - 2023 Spring Harvest.xlsx` Effort tab |
| `tide_series.csv` | tide series | season, tide series, days, open beach-days, % monitored | 13 | DigDay_Register → Tide_Series |
| `egress_survey_inventory.csv` | one located egress survey | survey_key, beach, date, condition, use_for_pooling | 8 | `1993-2026_Ingress_Egress_Consolidated.xlsx` → Survey_Inventory |
| `egress_survey_counts.csv` | survey × 15-min bin | survey_key, beach, condition, bin_ord, min_from_low, pct_available, cars_on/off | 5, 6, 9 | IE consolidated → Survey_Counts |
| `imputation_validation_days.csv` | paired beach-day (leave-one-out) | target, donor, season, imputed effort, actual effort, ratio, log error | 11, 13, 14 | `WDFW_RazorClam_Imputation_Error_2007_2026.xlsx` → Validation_Days |
| `imputation_multipliers.csv` | target × donor × tercile | level, target, donor, imputed-value tercile, n, mean multiplier, median | 12 | Imputation_Error → Multiplier_Pools |
| `imputation_pair_errors.csv` | target × donor | target, donor, n, median ratio, sd of log error, MAPE % | (context) | Imputation_Error → Pair_Errors |
| `historical_harvest_effort.csv` | season (coastwide) | season, start_year, effort_digger_trips, harvest_clams_incl_wastage, days_offered | 1, 2 | WDFW season summary (`wdfw02656.pdf`). **1999–2024 only**; append the WDFW historical seasonal summary rows for 1949–1998 to restore the full range. |
| `management_milestones.csv` | milestone | year, event | 3 | v9 §6 / Figure 3 caption |
| `beach_metadata.csv` | beach | beach, order_n_to_s, color_hex, boundary, has_expansion_table | all (palette, order) | v9 §area description |

## Reference / pre-computed tables (carried for plotting and validation)

These hold outputs of the correction-factor bootstrap and the uncertainty model. The pipeline
recomputes the correction-factor uncertainty (Fig 6) and the CV simulations (Figs 13–14) in R
from the raw tables above; the tables below are read for the expansion-table curves, the
variance decomposition, and the 95 % bands, and can be used to validate the recomputation.

| File | Figures | Source |
|---|---|---|
| `expansion_tables_rebuilt.csv` | 5 | `WDFW_RazorClam_Expansion_Tables_Rebuilt.xlsx` → Rebuilt_Tables (pooled percent-available + bootstrap CI) |
| `expansion_operational_vs_vintage.csv` | 9 | Expansion_Tables_Rebuilt → Operational_Comparison |
| `cf_windows.csv` | 6, 13 | Expansion_Tables_Rebuilt → CF_Windows (modal window, CF, relative sd) |
| `cf_uncertainty.csv` | 6 (validation) | `WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx` → CF_Uncertainty |
| `cf_expansion_lookup.csv` | (context) | `RazorClam_CF_ExpansionTable_Lookup.xlsx` → Lookup_Tidy |
| `season_estimates.csv` | 12 | Corrected_Estimates → Season_Estimates (workbook, corrected, 95 % band, CV). **2022-23 rows are re-derived in the pipeline** from the completed workbook. |
| `variance_decomposition.csv` | 10 | Corrected_Estimates → Variance_Decomposition |
| `cpue_replacement.csv` | (context) | Corrected_Estimates → CPUE_Replacement |

## Notes on the 2022-23 re-derivation
The published/source workbooks (`…Corrected_Estimates…`, `…Imputation_Error…`, DigDay_Register)
were built when the 2022-23 in-season workbook was partial (ended 25 Apr 2023). The pipeline
uses `beach_day_2022_23_complete.csv` (parsed from the completed workbook, ending 14 May 2023)
in place of the stale 2022-23 rows, and re-derives that season's corrected effort:
Copalis 80,182 and Mocrocks 58,476 (fully counted → corrected = workbook, exact); Twin Harbors
93,294 (day-level median multipliers, reproduces the published partial to 0.006 %); Long Beach
106,199 (season bias fraction). Coastwide corrected ≈ 338,150 digger trips.
