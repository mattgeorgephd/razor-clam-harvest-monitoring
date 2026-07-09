# WDFW Razor Clam Recreational Harvest Database: full extraction and recompute

Source: `Razor Clam Recreational Harvest Database iForms.accdb` (Access ACE14, 126,554,112 bytes).
Extracted 2026-07-09 with mdbtools 1.0. Nothing in this bundle requires Access.

## Layout

    raw/        21 tables, exported verbatim. This is the lossless copy of the database.
    clean/      the 5 raw tables after the documented cleaning layer.
    derived/    recomputed estimates at four grains.
    audit_log.csv   every row dropped or nullified, with a reason and a count.
    code/recompute_harvest.py   the pipeline that turns raw/ into clean/ and derived/.

## Extraction command

    mdb-tables -1 "$DB" | while IFS= read -r t; do
      mdb-export -D '%Y-%m-%d %H:%M:%S' -T '%Y-%m-%d %H:%M:%S' "$DB" "$t" > "raw/${t}.csv"
    done

Row counts of the raw exports match the data dictionary exactly:
tbl_events 2,682 | tbl_Creel 53,511 | tbl_DiggerCounts 13,789 | tbl_Wastage 1,023 |
TBL Length 11,324 | Spreadsheet 13,664 | CreelSumm 2,676 | Creel Summary by Area 9,777 |
Wastage Summary 603 | Revised Data 2008 - 2011 561 | Paste Errors 2 | 10 lookup tables.

## The estimator

Recovered from the database's own saved queries `01` to `16` and the macro
`Macro Calculate Harvest Estimate`. All rates pool at the **event** grain (one beach, one date).

    CPUE_e            = sum(CreelNClams)   / sum(CreelNDiggers)
    DiggersPeople_e   = sum(CreelNDiggers) / sum(CreelNPeople)
    DiggersLanterns_e = sum(CreelNDiggers) / sum(CreelNLanterns)
    PplPerCar_e       = mean(CreelNCars)          # people per car, NOT a car count

    CalcPeople_{e,s}  = NPeople                       if recorded
                      = NCars * PplPerCar_e           else if NCars recorded
                      = NLanterns * DiggersLanterns_e else if NLanterns recorded
                      = NCars * 2.67                  otherwise

    EstCorEffort_{e,s} = CalcPeople_{e,s} * DiggersPeople_e / CorrectionFactor_e
    TotHarvest_{e,s}   = EstCorEffort_{e,s} * CPUE_e
    Wastage_e          = TotHarvest_e * sum(NMorts)/sum(NHoles)

`CorrectionFactor` is an Access `Single`. Cast to float32 before dividing, or the
reproduction fails on rounding alone.

## Validation

Against the database's own stored `Spreadsheet` table, row by row on (EventID, LocationID, NPeople):

| quantity | matches | of | tolerance |
|---|---:|---:|---|
| CalcPeople   | 13,651 | 13,653 | 1e-6 relative |
| CPUE         | 13,653 | 13,653 | 1e-6 relative |
| EstCorEffort | 13,651 | 13,653 | 1e-6 relative |
| TotHarvest   | 13,651 | 13,653 | 1e-6 relative |

Independently: the 2017-18 season, whose in-season Effort tab holds only 10 of 27 dig days,
recomputes to 256,925 digger trips against 257,003 in the FINAL printout, a 0.03% difference.
Long Beach (94,213) and Mocrocks (63,215) reproduce exactly.

**Do not read the stored `Spreadsheet`, `CreelSumm`, `Creel Summary by Area` or
`Wastage Summary` tables.** For 476 events the stored `EstCorEffort` does not equal that same
row's `CalcPeople * Diggers-People / CorrectionFactor`. They are cached outputs, and stale.
Their creel sum columns are additionally inflated by the census row count of the event.

## Cleaning layer (all logged in audit_log.csv)

1. `BeachName` normalized to the `lut_Beach` spelling. Three spellings of Long Beach.
2. Rows with a null or orphan `EventID` dropped.
3. `CreelNClams` > 200 and `CreelNPeople`/`CreelNDiggers` > 60 nullified. The bag limit is 15.
4. Shell lengths outside [50, 200] mm nullified.
5. Census rows with `NCars >= 2 * NPeople` dropped: these are per-group records typed into the
   census table. EventIDs 469, 509, 2590.
6. Exact-duplicate census rows removed (82 rows).
7. **Duplicate events.** Ten beach-dates carry two EventIDs whose census segment sets overlap.
   Those are duplicates; the event with fewer segments is dropped. Fifty-three further
   beach-dates carry two EventIDs with *disjoint* segments: Long Beach walks its seven segments
   as a four-segment count and a three-segment count, each its own event with its own correction
   factor. Those must be summed, not deduplicated.
8. `CorrectionFactor` above 1 set to NA (EventID 717, CF 2.100). CF is a fraction.

## What the database cannot give you

It holds a census only for beach-days a sampler worked. The in-season workbook fills the rest by
scaling one beach off another; that imputation exists nowhere in the database. Coastwide the
database backs 96% of the Effort tab season total in 2012-13 and 2013-14, and 64% in 2025-26.
Long Beach: 30.2% in 2025-26. Twin Harbors: 57.5%. Copalis and Mocrocks: 100%.

A ground-up rebuild therefore needs three layers, and only the first is in the database:

    1. event-level expansion  (here, validated)
    2. an explicit imputation rule for uncounted beach-days  (currently implicit in cell formulas)
    3. season rollup

Layer 2 is also where nearly all of the uncertainty lives.

## Known data problems that block publication

- Recomputed CPUE exceeds the 15-clam daily limit: 2021-22 at all four beaches (16.46 to 17.16),
  2020-21 (15.00 to 15.01), Long Beach 2016-17 (20.11).
- Kalaloch: 40 beach-days of typed effort in the Effort tabs, 15 distinct beach-dates in the
  database. All of 2009-10 (17 days) and all of 2018-19 (6 days) have no event at all.
- `tbl_DiggerCounts` has no count time, so replicate censuses at one segment cannot be matched
  to the correction-factor reference time.
