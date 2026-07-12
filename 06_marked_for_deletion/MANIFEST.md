# Marked for deletion

These files were **moved here (not deleted)** during the July 2026 repo consolidation.
They are superseded by the consolidated data suite (`02_data/consolidated/`), the RMD
figure pipeline (`01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`), and the
current methodology document (`04_documentation/2026-Review-WDFW_Harvest_Estimate_Methodology-v9.docx`).
Each file keeps its original relative path under this folder, so restoring any item is a
plain `git mv 06_marked_for_deletion/<path> <path>`.

Nothing here is required to run the pipeline. Review, then delete the folder when satisfied.

## What was moved and why (28 files)

**Draft methodology documents (superseded by v9); 7 files in `04_documentation/`**
`2026-Review-WDFW_Harvest_Estimate_Methodology.docx` and `-v2` through `-v7.docx`. These are
the draft versions that led to v9. Kept on `main`: `-v8` (immediate predecessor), `-v9`
(current), and the original `2010-WDFW-Harvest-Estimate-Methodology.docx` historical source
under review.

**Superseded harvest-DB output dump; 10 files in `02_data/RazorClam_Harvest_Outputs/`**
An earlier output snapshot. The authoritative extract is
`02_data/RazorClam_HarvestDB_Extract_and_Pipeline/` and the tidy `02_data/consolidated/` CSVs.

**Loose intermediate / dedup working files; 9 files matching `02_data/*.csv`**
`audit_log.csv`, `audit_log_dedup.csv`, `audit_log_final.csv`, `creel_event_rates.csv`,
`decomposition_duplicate_vs_replicate.csv`, `harvest_by_beach_season.csv`,
`harvest_by_beach_season_dedup.csv`, `harvest_by_event.csv`, `harvest_by_event_final.csv`.
Scratch outputs from building the extract; the derived tables live under the pipeline folder
and `consolidated/`.

**Raw iForms export; 1 file in `02_data/`**
`iFormsSpreadsheetFall2025Spring2026.xls`. Superseded by the
`2025 Fall - 2026 Spring Harvest.xlsx` in-season workbook.

**Duplicate harvest workbook; 1 file in `02_data/harvest_inseason_records/`**
`2009 Fall - 2010 Spring Harvest(revised 8-29-13).xlsx`. The `(FINAL)` copy of the same
season was kept.

## Already removed in earlier commits (not reproduced here)

The original consolidation plan also called for retiring the per-survey ingress/egress
transcriptions (`02_data/IE data/`, 19 files) and the v4/v5 figure-source bundles
(`04_documentation/v4_figures_and_source/`, `v5_figures_and_source/`, 29 items). Those were
already removed from `main` in the prior "move" commits; the IE data was compiled into
`1993-2026_Ingress_Egress_Consolidated.xlsx`, so they are not moved into this folder.
