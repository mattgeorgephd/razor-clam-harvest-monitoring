# WDFW Razor Clam Recreational Harvest Database: Data Dictionary, Methodology, and Data Quality Review

**Source file:** `Razor Clam Recreational Harvest Database iForms.accdb` (Access ACE14 / Access 2010+ format, ~121 MB)
**Reviewed:** June 2026
**Scope of database:** Recreational razor clam (*Siliqua patula*) creel and effort data for the five Washington coastal management beaches (Long Beach, Twin Harbors, Copalis, Mocrocks, Kalaloch). This is the **harvest-estimation** dataset (creel interviews, instantaneous digger censuses, wastage surveys, shell-length samples). It is distinct from, and complementary to, the population/biomass stock-assessment surveys (e.g., the Pumped Area Method work).

> Note on tooling: this database was read on Linux with mdbtools 1.0 (table data and schema) plus direct extraction of the Access system catalog (`MSysObjects`, `MSysQueries`) to recover relationships and the calculation formulas. mdbtools does not expose primary keys or indexes, so keys below are inferred from the relationship definitions and from the data (uniqueness, non-null structure).

---

## 1. Quick facts

| Item | Value |
|---|---|
| Format | Access ACE14 (`.accdb`, Access 2010+) |
| User data tables | 5 raw + several derived/legacy |
| Lookup tables | 10 (`lut_*`) |
| Saved queries | ~30, including a 16-step numbered processing pipeline |
| Forms / module / macro | 7 forms, 1 module (`AutoFillNewRecord`), 1 macro (`Macro Calculate Harvest Estimate`) |
| Date span | 1993-10-13 to 2026-05-06 (sparse pre-2008, dense 2008+) |
| Join key | `EventID` (parent to children); `LocationID` to `lut_Beach` |

### Row counts (true, CSV-aware)

| Table | Rows | Role |
|---|---:|---|
| `tbl_events` | 2,682 | Parent: one sampling event = one beach on one date |
| `tbl_Creel` | 53,511 | Child: one creel (digger-group) interview |
| `tbl_DiggerCounts` | 13,789 | Child: one instantaneous census count at a segment |
| `TBL Length` | 11,324 | Child: one clam shell-length measurement (mm) |
| `tbl_Wastage` | 1,023 | Child: one wastage-survey hole-dig record |
| `Spreadsheet` | 13,664 | Derived: pipeline working/output table (Event x Location grain) |
| `Creel Summary by Area` | 9,777 | Derived: creel sums per Event x Location |
| `CreelSumm` | 2,676 | Derived: creel sums per Event |
| `Wastage Summary` | 603 | Derived: wastage sums per Event |
| `Revised Data 2008 - 2011` | 561 | Legacy/corrected output for the 2008-2011 seasons |
| `Paste Errors` | 2 | Access-generated failed-append artifact (see 6.6) |

(`wc -l` reported 2,713 for `tbl_events`; the true count is 2,682. The 31-row difference is embedded newlines inside the free-text `Comments` field. Counts above are the correct logical row counts.)

---

## 2. Entity-relationship model

`EventID` is the spine. `tbl_events` holds one row per **beach-day sampling event**. The four child tables each hold many rows per event, tagged with a segment `LocationID`. Access defines explicit relationships from `tbl_events` to each child (`tbl_eventstbl_Creel`, `tbl_eventstbl_DiggerCounts`, `tbl_eventstbl_Wastage`, `tbl_eventsTBL Length`).

```
                         lut_Beach (LocationID -> BeachName, 28 segments)
                                        ^  (LocationID)
                                        |
            +----------------+----------+-----------+----------------+
            |                |                      |                |
   tbl_Creel (53,511)  tbl_DiggerCounts (13,789)  tbl_Wastage (1,023)  TBL Length (11,324)
   creel interviews    instantaneous censuses     wastage surveys     clam lengths
            |                |                      |                |
            +----------------+----------+-----------+----------------+
                                        | (EventID, 1-to-many)
                                        v
                              tbl_events (2,682)   <- one row per beach x date
                                        |
                            (condition codes via lut_* lookups)
```

**Grain summary**

- `tbl_events`: 1 row per (beach, date). No `LocationID` column here; the beach is denormalized into `BeachName` (and that field is dirty; see 6.1).
- `tbl_Creel`, `tbl_DiggerCounts`, `tbl_Wastage`, `TBL Length`: 1 row per observation, each carrying `EventID` (to the parent) and `LocationID` (to the segment). The segment-level beach must be obtained by joining `LocationID` to `lut_Beach`, since these children do not store `BeachName`.

---

## 3. Raw-table data dictionary

### 3.1 `tbl_events` (parent)

| Field | Type | Notes |
|---|---|---|
| `EventID` | Long | **Key.** Unique, non-null; range 1 to 2,776 with gaps (deleted events), 2,682 rows. |
| `BeachName` | Text(50) | **Dirty / not normalized.** Three spellings of Long Beach ("LongBeach", "Long Beach", "Longbeach"); 1 null. Normalize to the `lut_Beach` canonical "LongBeach". |
| `Date` | DateTime | Event date (time component 00:00). 1993-2026. |
| `DayofWeek` | Text(10) | Stored day name; ~26 rows blank or inconsistent with `Date`. Derive from `Date` instead of trusting this. |
| `Holiday?` | Boolean | Holiday flag (NOT NULL). |
| `Low Tide`, `StartTime`, `EndTime`, `Sunset` | DateTime | Time-of-day fields. |
| `TideHeight` | Double | Predicted low-tide height (ft). |
| `CountDirection` | Text(20) | Direction of the census walk (`lut_CountDirection`). |
| `Sampler1`, `Sampler2`, `Sampler3` | Text(50) | Sampler IDs (`lut_Sampler`). |
| `SurfConditions`, `PrecipConditions`, `SkyConditions`, `WindConditions`, `OtherConditions`, `WindDirection` | Text(20) | Coded conditions (`lut_Surf`, `lut_Rain`, `lut_Weather`, `lut_WindSpeed`, `lut_SpecialConditions`, `lut_DirectionWind`). |
| `Comments` | Text(200) | Free text; can contain embedded newlines. |
| `CorrectionFactor` | Single | Per-event effort correction (see 5). Mean 0.546, range 0.193 to 2.100; 10 nulls. The 2.100 value (EventID 717, Mocrocks 2003) is an outlier and probably an error. |
| `Field1`-`Field15` | Text/Memo(255) | **Empty import artifacts.** All null in all rows. Ignore/drop. |

### 3.2 `tbl_Creel` (child: creel interviews)

| Field | Type | Notes |
|---|---|---|
| `EventID` | Long | FK to `tbl_events`. 5 nulls; 1 orphan (2002) with no parent. |
| `LocationID` | Text(50) | Segment. 31 blank; **63 rows (0.12%) carry codes not in `lut_Beach`** (typos like `.426`, `1204`, `126`, `22309*`, `22309+`, `232309`, `310058`). |
| `CreelNPeople` | Double | People in the interviewed group. Mean 2.59. 40 nulls. |
| `CreelNDiggers` | Double | Diggers in the group. Mean 2.48. 44 nulls. |
| `CreelNClams` | Double | Clams the group held. Mean 32.8; 2,449 zeros (unsuccessful diggers, legitimate). |
| `CreelNLanterns` | Double | Lanterns for the group (night digs). **~99% null** (52,863 of 53,511 null). |
| `CreelNCars` | Double | **People per car, NOT a car count** (see 5 and 6.3). Mean ~2.52. ~85% null. |
| `autonumber` | Long | Surrogate primary key. |

> Impossible values: `CreelNClams` up to 28,576 and `CreelNPeople`/`CreelNDiggers` up to 1,928 in single interview rows (physically impossible; WA limit is 15 clams/digger). ~26 rows total but they would grossly inflate any sum. See 6.2.

### 3.3 `tbl_DiggerCounts` (child: instantaneous censuses)

| Field | Type | Notes |
|---|---|---|
| `EventID` | Long | FK. 3 nulls; 1 orphan (2409). |
| `LocationID` | Text(50) | Segment. 75 blank; 1 bad code (`526`). |
| `NPeople` | Double | Total people counted on the segment at count time. Mean ~252; max 4,470 (plausible on big digs). ~19% null. |
| `NLanterns` | Double | Lanterns counted. **~98% null.** |
| `NCars` | Double | Cars counted. ~82% null. |
| `Comments` | Text(50) | Free text. |
| `autonumber` | Long | Surrogate primary key. |

### 3.4 `tbl_Wastage` (child: wastage surveys)

| Field | Type | Notes |
|---|---|---|
| `EventID` | Long | FK. 1 orphan (2410). |
| `LocationID` | Text(50) | Segment. 2 blank; 1 bad code (`32005`). |
| `NHoles` | Long | Holes excavated in the wastage dig. Mean ~92; max 500. |
| `NClams` | Long | Clams recovered. Max 30. |
| `NMorts` | Long | Wasted/discarded (dead) clams. Max 30; mean ~3.3. Used as the wastage numerator (see 5). |

### 3.5 `TBL Length` (child: shell lengths)

| Field | Type | Notes |
|---|---|---|
| `EventID` | Long | FK. 1 orphan (2597). **Only 429 distinct events have length data (~16% of events).** Length sampling is sparse and not done at every event. |
| `LocationID` | Text(50) | Segment. 154 blank; 1 bad code (`11322`). |
| `Length` | Long | Shell length in **mm**. Distribution is biologically sensible (peak 100-130 mm, mean ~115 mm). One impossible value (1,110 mm) and one low value (58 mm). |

---

## 4. Lookups and derived tables

**Lookups.** `lut_Beach` (28 rows) is the authoritative `LocationID -> BeachName` map with a textual `Description` of each geographic segment; canonical beach spelling is "LongBeach" (no space). Long Beach has 7 numeric segments (11101-12600), Twin Harbors 4, Copalis 6, Mocrocks 6; Kalaloch uses 5 named access points (`Campground`, `Guard Rail`, `South Beach`, `Trail 1`, `Trail 2`), which is why `LocationID` is Text, not numeric. `lut_BeachName` lists the 5 canonical names. `lut_Sampler` (18) maps sampler IDs to names. The condition lookups (`lut_CountDirection`, `lut_DirectionWind`, `lut_Rain`, `lut_SpecialConditions`, `lut_Surf`, `lut_WindSpeed`, `lut_Weather`) are small code/description tables. The `IsPermanent` flag in `lut_Beach` is 0 for every row (apparently unused).

**Derived tables** are outputs of the query pipeline (section 5), not independent data: `Spreadsheet` (the working table, Event x Location grain, holds every computed quantity), `Creel Summary by Area`, `CreelSumm`, `Wastage Summary`, and the legacy `Revised Data 2008 - 2011`. **They are only as current as the last pipeline run and can be stale relative to the raw tables.** Treat the five raw tables as the source of truth; recompute derived quantities rather than trusting the stored copies unless they are confirmed current.

---

## 5. Recovered harvest-estimation methodology

The numbered queries (`01`-`16`) and the `Macro Calculate Harvest Estimate` implement WDFW's effort-expansion and harvest estimate. Formulas below were recovered verbatim from `MSysQueries`. All operate per `EventID`; the `Spreadsheet` row is the unit, then results roll up to beach/season totals.

Aggregates (from `CreelSumm` / `Creel Summary by Area`, grouped by event):
- `Sum Of CreelNClams`, `Sum Of CreelNDiggers`, `Sum Of CreelNPeople`, `Sum Of CreelNLanterns`, `Avg Of CreelNCars`.

Step formulas:

1. **CPUE** = `Sum(CreelNClams) / Sum(CreelNDiggers)`  (clams per digger from interviews).
2. **Diggers-People** = `Sum(CreelNDiggers) / Sum(CreelNPeople)`  (fraction of beach people who are actually digging).
3. **Diggers-Lanterns** = `Sum(CreelNDiggers) / Sum(CreelNLanterns)`  (diggers per lantern, for night digs).
4. **AvgOfCreelNCars** = `Avg(CreelNCars)`  (average people per car; query is literally named "07 UpdateAvgPplPerCar").
5. **CalcPeople** = `IIf(NPeople not null, NPeople, IIf(NCars not null, NCars * AvgOfCreelNCars, IIf(NLanterns not null, NLanterns * DiggersLanterns, NCars * 2.67)))`
   Hierarchical estimate of total people present: prefer the direct people census; else expand the car census by people-per-car; else expand the lantern census by diggers-per-lantern; else fall back to cars x 2.67 (the historical default people-per-car constant).
6. **EstCorEffort** (estimated corrected effort, i.e., total digger trips) = `CalcPeople * DiggersPeople / CorrectionFactor`.
   The instantaneous census captures only diggers present at count time; dividing by the correction factor (~0.5) expands to total trips over the dig, accounting for turnover.
7. **TotHarvest** (total clams) = `EstCorEffort * CPUE`.
8. **%Interviewed** (sampling intensity) = `Sum(CreelNPeople) / EstCorEffort`.
9. **Wastage %** = `Sum(NMorts) / Sum(NHoles)`  and  **Wastage** (count) = `TotHarvest * (Sum(NMorts) / Sum(NHoles))`.

Collapsed chain to harvest:

```
TotHarvest = [ CalcPeople * (SumDiggers / SumPeople) / CorrectionFactor ] * (SumClams / SumDiggers)
```

**Field-semantics correction (evidence-backed):** `tbl_Creel.CreelNCars` stores **people per car**, not a car count. Two independent confirmations: (a) the update query that consumes `Avg(CreelNCars)` is named "Update Avg Ppl Per Car"; (b) the observed mean of `CreelNCars` (~2.52) is almost exactly the hard-coded people-per-car fallback constant (2.67). Anyone interpreting `CreelNCars` as a vehicle count will be wrong.

**Open methodological question to verify against WDFW documentation:** the `CorrectionFactor` semantics (forms `CorFact`, `CFCopalis`, `CFKalaloch` compute it) and the provenance of the 2.67 constant should be confirmed against the agency's documented effort-expansion protocol before relying on recomputed estimates for any formal product.

---

## 6. Data quality findings (prioritized)

### 6.1 `BeachName` not normalized (high impact)
"LongBeach" (470) + "Long Beach" (259) + "Longbeach" (2) are the same beach. Grouping by raw `BeachName` undercounts Long Beach events by ~36% (731 true vs 470). Fix by mapping to the `lut_Beach` canonical spelling, or for child-level work by joining `LocationID -> lut_Beach.BeachName` rather than using the event's stored `BeachName` at all. Beach event totals after normalization: Twin Harbors 771, Long Beach 731, Mocrocks 628, Copalis 535, Kalaloch 16, 1 null.

### 6.2 Impossible count values (high impact on any sum)
`tbl_Creel`: `CreelNClams` up to 28,576 (and 24,214; 15,526; 6,680) and `CreelNPeople`/`CreelNDiggers` up to 1,928 in single interview rows. Roughly 26 rows, but four bad `CreelNClams` rows alone add ~75,000 phantom clams. Apply per-field sanity caps before aggregating (e.g., flag `CreelNClams` beyond a few hundred, `CreelNPeople`/`CreelNDiggers` beyond ~60).

### 6.3 Misnamed field
`CreelNCars` = people per car (see 5). Document and rename in any extract.

### 6.4 Dirty / orphan keys
- 28 distinct bad `LocationID` codes in `tbl_Creel` (63 rows); isolated bad codes elsewhere (`526`, `32005`, `11322`). These rows cannot be assigned to a beach via `lut_Beach` without cleaning.
- One orphan `EventID` in each child (2002, 2409, 2410, 2597) with no parent row (cascade-delete was not enforced).
- Null `EventID`: 5 in `tbl_Creel`, 3 in `tbl_DiggerCounts` (unlinkable rows).

### 6.5 Sparse fields and sparse length sampling
`CreelNLanterns`, `CreelNCars`, and the `tbl_DiggerCounts` lantern/car columns are ~80-99% null. `TBL Length` covers only 429 of 2,682 events (~16%). Length-based analyses are limited to that subset; the lantern/car expansion paths in `CalcPeople` are rarely the binding branch.

### 6.6 Benign artifacts
`Field1`-`Field15` in `tbl_events` are empty. `Paste Errors` holds two **duplicate** rows for the Long Beach 2025-10-24 event, which **does** exist in `tbl_events` (EventID 2595, sampler BlumenthalB); these are leftover failed-append attempts, not a missing event. One `CorrectionFactor` outlier (2.100, EventID 717) and six values < 0.25 warrant a look.

---

## 7. Extraction and analysis recommendations

1. **Treat the 5 raw tables as the source of truth.** Recompute CPUE / effort / harvest with the section-5 formulas rather than relying on the stored `Spreadsheet`/summary tables, which may be stale. Validate any recomputation against `Revised Data 2008 - 2011` for those seasons.
2. **Resolve beach identity by `LocationID -> lut_Beach`**, falling back to a normalized `BeachName` map only where `LocationID` is missing or bad. Build one canonical beach key.
3. **Apply a documented cleaning layer** before analysis: normalize `BeachName`; drop/flag null and orphan `EventID`; cap impossible `CreelNClams`/`CreelNPeople`/`CreelNDiggers`; quarantine bad `LocationID` codes; treat `CreelNCars` as people-per-car; derive `DayofWeek` from `Date`; drop empty `Field*`.
4. **Keep cleaning auditable.** Log every row dropped or altered (count and reason) so harvest estimates remain defensible.
5. **For length work**, restrict to the 429 events with data and exclude the 1,110 mm error; consider whether the 58 mm value is real.

---

*Prepared as a project reference. The raw `.accdb` only needs to be present transiently for re-extraction; this document is the durable artifact for the project knowledge base.*
