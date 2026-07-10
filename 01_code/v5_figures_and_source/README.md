
## Version 5 additions

    reconcile_2017_18_printout.py        parses "2017 Fall - 2018 Spring Harvest.FINAL.pdf"
                                         (pdftotext -layout) and reconciles it beach-day by
                                         beach-day against derived/harvest_by_beach_day.csv
    reconcile_2022_23_and_2023_24.py     tests both Effort tabs for completeness against the
                                         database; finds the missing 4-14 May 2023 tide series
    make_table_data_v5.py                writes the Table 5 reconciliation and the corrected
                                         census-backed coverage shares (coverage_fixed.json)
    make_figures_pass3_v5.py             re-renders Figure 4 (fig07) with all 19 seasons and
                                         Figure 12 (fig10) with 2017-18 and 2022-23 marked

Figures 4 and 12 in figures/ are the version 5 renders.
