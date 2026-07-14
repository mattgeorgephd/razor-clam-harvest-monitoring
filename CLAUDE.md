# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A WDFW (Washington Dept. of Fish & Wildlife) scientific analysis of the Pacific razor
clam recreational harvest-estimation methodology. It reconstructs harvest, effort, and
CPUE estimates from source data, quantifies the uncertainty in the agency's effort-
expansion method, and produces the figures for a methodology-review document
(`04_documentation/2026-Review-WDFW_Harvest_Estimate_Methodology-v*.docx`). There is no
application to build — the deliverables are figures, tidy CSVs, and Word/PowerPoint docs.

It is an RStudio project (`razor-clam-harvest-monitoring.Rproj`, 2-space indent, UTF-8).

## Running the code

Two RMarkdown pipelines, run with `rmarkdown::render()` in RStudio or:
`Rscript -e "rmarkdown::render('<file>.Rmd')"`. Packages self-install via a
`load.lib`/`install.lib` loop on first run.

- **`01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`** — the main figure
  pipeline. Reads only the tidy CSVs in `02_data/consolidated/` and writes ~21 figures
  to a dated `03_analyses/YYYYMMDD-harvest-figures/` tree. Self-contained; needs no
  database or Access driver. Iterate faster by setting `save_fig <- FALSE` (Section 0)
  or toggling individual `save_plot()` calls. `set.seed(42)` and `n_boot <- 2000` govern
  all resampling — keep them fixed for reproducible bands.
- **`01_code/extract_recompute_harvest.Rmd`** — extracts the 5 raw tables from the Access
  `.accdb` and recomputes estimates from scratch. Requires 64-bit R paired with the
  **64-bit** Microsoft Access (ACE) driver — a bitness mismatch is the usual
  `IM002 data source name not found` failure. The `.accdb` is gitignored and not in the
  repo. `02_data/RazorClam_HarvestDB_Extract_and_Pipeline/code/recompute_harvest.py` is
  the equivalent Python extractor (pandas; reads `raw/*.csv` from `mdb-export`, no Access
  needed) and is the source of the `derived/` tables.

## Data flow (three layers, only the first is in the database)

    Access .accdb  ──extract_recompute_harvest.Rmd / recompute_harvest.py──▶  raw/ → clean/ → derived/
    (HarvestDB_Extract_and_Pipeline)                                          │
                                                                             ▼
    02_data/consolidated/*.csv  (tidy, analysis-ready; standardized beach names)
                                                                             │
                                        20260710-…-figures-pipeline.Rmd  ─────┘──▶  03_analyses/<date>/*.png

The estimator only covers **layer 1 (event-level expansion)**. Layer 2 (imputing
uncounted beach-days by scaling one beach off a donor beach) and layer 3 (season rollup)
live in in-season Excel workbooks, not the database, and layer 2 is where most of the
uncertainty lives. See `02_data/RazorClam_HarvestDB_Extract_and_Pipeline/README.md` for
the full estimator formulas, validation results, and cleaning rules.

## Critical data conventions (read before touching estimates)

- **Never read the database's stored `Spreadsheet`, `CreelSumm`, `Creel Summary by
  Area`, or `Wastage Summary` tables as truth.** They are stale cached outputs and their
  sum columns are inflated by a census-row-count join. Rates (CPUE) survive; totals do
  not. Recompute from the raw tables instead.
- **`CorrectionFactor` must be cast to float32 before dividing** — it is an Access
  `Single`; using float64 breaks the exact reproduction of stored values.
- Beach names are standardized everywhere to `Long Beach`, `Twin Harbors`, `Copalis`,
  `Mocrocks`, `Kalaloch` (three spellings of Long Beach exist in the raw data).
- All rates pool at the **event** grain (one beach, one date).
- The figure pipeline runs every column through `janitor::clean_names()`, so a header
  like `effort (workbook)` is referenced in R as `effort_workbook`.
- The consolidated suite reflects the **completed 2022-23 season** (restored 4–14 May
  2023 tides). Several published source workbooks were built when 2022-23 was still
  partial (ended 25 Apr 2023); the pipeline substitutes `beach_day_2022_23_complete.csv`
  and re-derives that season. Don't "fix" 2022-23 back to the stale published numbers.

Every dropped/nullified/flagged row is written to an **audit log** so estimates stay
defensible — preserve that pattern when adding cleaning steps.

## Repository layout

- `01_code/` — the two RMarkdown pipelines.
- `02_data/consolidated/` — tidy CSVs the figure pipeline reads; see its
  `DATA_DICTIONARY.md` for the file→figure→source map (start here to trace any figure).
- `02_data/RazorClam_HarvestDB_Extract_and_Pipeline/` — the lossless DB extract
  (`raw/`), cleaned tables (`clean/`), recomputed estimates (`derived/`), `audit_log.csv`,
  and the Python recompute code. Its `README.md` is the authoritative estimator spec.
- `02_data/IE data/` — ingress/egress survey data (drives the correction-factor and
  expansion-table work), including a consolidated 1993–2026 workbook.
- `03_analyses/` — dated figure output folders (regenerated; treat as disposable).
- `04_documentation/` — the methodology-review docs (versioned v8→v10), data
  dictionaries, and background narratives.
- `05_templates/` — WDFW Word/PowerPoint templates for deliverables.
- `06_marked_for_deletion/` — superseded files staged for removal; do not build on these.
- `07_presentations/` — presentation decks.
