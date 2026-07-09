# Razor Clam Ingress/Egress Survey Database, Data Dictionary

**Source file:** `Razor_Clam_Ingress.accdb`
**Format:** Microsoft Access, ACE12 engine (`.accdb`), 2.49 MB
**Scope:** 20 egress-survey events across 5 named beaches, survey dates 2004-04-21 to 2011-04-22
**Role:** This is the raw field-data layer beneath the harvest correction factor (CF). The "% available for beach count" curve that defines each beach's CF expansion table is derived directly from the `Cars On` and `Cars Off` counts stored here. It is the upstream companion to the recreational harvest (creel) database, not a copy of it.

---

## 1. What this database is for

WDFW expands an instantaneous digger count to a full day's effort by dividing by a correction factor, `E_total = E_t*(1-p)/CF`, where `CF = R_t` is the mean fraction of the day's total effort present on the beach during the count window. That fraction comes from **egress surveys**: staff stationed at beach access points count vehicles driving on and off the beach in 15-minute intervals across the tidal cycle (roughly 3 hours before to 2 hours after low water). This database stores those raw on/off counts, one record per survey, plus the survey's date, beach, tide, conditions, and sampler. Accumulating arrivals minus departures yields the number of vehicles on the beach at each interval, and normalizing by the day's total arrivals yields the "% available" curve that is the expansion table (Section 5).

---

## 2. Data model

Five tables. `Event Data` is the parent (one row per survey event); `Cars On` and `Cars Off` are each in a strict 1:1 relationship with `Event Data` through the shared `ID`; `Beach` and `Sampler` are foreign keys into the two lookup tables.

```
        LUT Beach Name (5)                 LUT Sampler (9)
              ^                                   ^
              | Beach (FK)                        | Sampler (FK)
              |                                   |
        +-----+-----------------------------------+-----+
        |                 Event Data (20)               |   one row per survey event
        |  ID (PK) ........ joins to both count tables  |
        +-----------------------+-----------------------+
                  | ID (1:1)    |    | ID (1:1)
                  v             |    v
            Cars On (20)        |  Cars Off (20)          arrivals / departures
            23 time-bin cols    |  23 time-bin cols       per 15-min interval
```

Verified: the `ID` sets of `Event Data`, `Cars On`, and `Cars Off` are identical (1..20), so every survey has exactly one arrivals row and one departures row.

| Table | Rows | Grain | Role |
|---|---|---|---|
| `Event Data` | 20 | one survey event | Survey metadata: beach, date, tide, conditions, sampler, baseline |
| `Cars On` | 20 | one survey event | Vehicle **arrivals** counted per 15-minute bin relative to low water |
| `Cars Off` | 20 | one survey event | Vehicle **departures** counted per 15-minute bin relative to low water |
| `LUT Beach Name` | 5 | one beach | Beach code to name |
| `LUT Sampler` | 9 | one staff member | Sampler code to name |

---

## 3. Field dictionary

### 3.1 `Event Data` (20 rows)

| Field | Type | Notes |
|---|---|---|
| `ID` | Long Integer | Primary key; joins 1:1 to `Cars On` and `Cars Off`. |
| `Beach` | Long Integer | FK to `LUT Beach Name` (1 Longbeach, 2 Twin Harbors, 3 Copalis, 4 Mocrocks, 5 Kalaloch). |
| `Event Date` | DateTime | Calendar date of the survey. Populated for all 20 rows. |
| `Tide Time` | DateTime | Clock time of the low tide the survey was built around. **Time-only field:** the date component is the Access sentinel (1899-12-30, surfaced by the export tool as a fixed dummy date); only the time is meaningful. |
| `Evening?` | Boolean (NOT NULL) | 1 = evening/near-dark tide series, 0 = morning/daylight. Distribution: 11 daylight, 9 evening. This flag, together with `Surf`/`Wind`/`Weather`, selects which condition table (daylight, near-dark, poor-weather) the curve belongs to. |
| `Weather` | Text(255) | Free-text sky/precipitation note (e.g., "Overcast, with showers"). Null in 8 of 20 rows. |
| `Wind` | Text(255) | Free-text direction and speed band (e.g., "SW, 5 - 15"). Null in 8 of 20. |
| `Surf` | Text(255) | Free-text surf condition (e.g., "High", "Low+", "Moderate, 6 - 8 ft."). Null in 9 of 20. Mirrors the harvest database `SurfConditions` vocabulary. |
| `Notes` | Text(255) | Free-text; null in 18 of 20. |
| `Cars Left In Area` | Double | Baseline vehicles already in the area at survey start (the "Prior To Start" standing count). Populated for all 20. |
| `Tide Level` | Double | Predicted low-tide height in feet (e.g., -1.6, 0.1). Populated for all 20. |
| `Sampler` | Long Integer | FK to `LUT Sampler`; null in 5 of 20. |

### 3.2 `Cars On` and `Cars Off` (20 rows each)

Both tables share an identical layout: `ID` (joins to `Event Data`) followed by 23 numeric (Double) columns, 22 of them 15-minute time bins plus one standing-count column.

- `Cars On` records **arrivals** (vehicles driving onto the beach) in each bin.
- `Cars Off` records **departures** (vehicles leaving) in each bin.

**Time-bin columns**, labeled by their position relative to low water (`H:MM - H:MM` before low, then `0:00` is low water, then after low). In **chronological order** they are:

`Prior To Start`, `3:30 - 3:15`, `3:15 - 3:00`, `3:00 - 2:45`, `2:45 - 2:30`, `2:30 - 2:15`, `2:15 - 2:00`, `2:00 - 1:45`, `1:45 - 1:30`, `1:30 - 1:15`, `1:15 - 1:00`, `1:00 - 0:45`, `0:45 - 0:30`, `0:30 - 0:15`, `0:15 - 0:00`, `0:00 - 0:15`, `0:15 - 0:30`, `0:30 - 0:45`, `0:45 - 1:00`, `1:00 - 1:15`, `1:15 - 1:30`, `1:30 - 1:45`, `1:45 - 2:00`.

Notes:
- **Storage order differs from chronological order.** In the table definition the bins run `3:15 - 3:00` first through `1:45 - 2:00`, and `3:30 - 3:15` and `Prior To Start` are appended at the end. Re-sort to the chronological order above before cumulating.
- `Prior To Start` is the standing count of vehicles already on the beach when the survey window opens (it equals `Cars Left In Area` on the parent row and seeds the cumulative arrivals).
- The active survey window varies by event, so not every bin is filled. Across the 20 surveys, 15 to 21 of the 23 columns carry a value; the outermost bins (`1:45 - 2:00`, `1:15 - 1:30`, `1:30 - 1:45`) are most often blank. Treat blanks as zero counts within the surveyed window.

### 3.3 `LUT Beach Name` (5 rows)

| ID | Beach Name |
|---|---|
| 1 | Longbeach |
| 2 | Twin Harbors |
| 3 | Copalis |
| 4 | Mocrocks |
| 5 | Kalaloch |

### 3.4 `LUT Sampler` (9 rows)

Staff lookup (`Sampler LastName`, `Sampler FirstName`): Deibert John, Parson Clayton, Ayres Dan, Sarich Alan, Haring Travis, Sanchez Polo, Wargo Lorna, Beck Glen, Wilson Terry. Codes are 1-7, 9, 10 (no code 8).

---

## 4. Survey coverage

| Beach | Daylight (`Evening?`=0) | Evening (`Evening?`=1) | Total | Date span |
|---|---|---|---|---|
| Longbeach | 3 | 2 | 5 | 2004-2011 |
| Twin Harbors | 4 | 2 | 6 | 2004-2011 |
| Copalis | 2 | 2 | 4 | 2004-2011 |
| Mocrocks | 2 | 3 | 5 | 2004-2011 |
| Kalaloch | 0 | 0 | **0** | none |
| **Total** | **11** | **9** | **20** | **2004-04-21 to 2011-04-22** |

Two things to flag. First, **Kalaloch has no surveys here** even though it is in the beach lookup; its daylight expansion table (present in `Master_Tables.xls`) was built from data not in this database. Second, **every survey predates mid-2011**, so this is the early survey collection, not a complete archive (Section 7).

---

## 5. How an expansion table (and CF) is derived from this data

For a single survey, order the bins chronologically (Section 3.2) and accumulate:

```
CumOn(b)   = sum of Cars On over all bins up to and including b   (seeded by Prior To Start)
CumOff(b)  = sum of Cars Off over all bins up to and including b
OnBeach(b) = CumOn(b) - CumOff(b)                  # vehicles physically on the beach during bin b
PctAvail(b)= OnBeach(b) / CumOn(last bin)          # share of the day's total arrivals present in bin b
```

`PctAvail(b)` is the "% available for beach count" curve. To build a **beach/condition expansion table**, the relevant surveys are **pooled** (sum `Cars On` and `Cars Off` across surveys per bin) and the formula above is applied to the pooled totals. The correction factor for an actual count is then

```
CF = R_t = mean of PctAvail over the bins spanning the count's start-to-end window relative to low water.
```

The standard beach count is run about 1 hour before low water at peak effort; a count takes roughly 26 to 31 minutes, so `R_t` typically averages two adjacent bins.

**Validation (this database reproduces the published tables exactly).** Pooling the two Long Beach evening surveys in this database (`ID` 9 and 7) and applying the formula reproduces the published "Longbeach Evening Tides Cumulative Ingress / Egress" table dated 01/25/2011 to three decimals (peak 0.716 at the `1:45 - 1:30` bin; `1:15 - 1:00` = 0.653; `1:00 - 0:45` = 0.565). Pooling the Copalis evening surveys reproduces the 11/03/2010 Copalis table identically. This confirms both the derivation method and that the database is the genuine source for those table versions.

---

## 6. Relationship to the harvest database and the correction-factor logs

- The condition fields here (`Surf`, `Wind`, `Weather`, `Evening?`, `Tide Level`) are the survey-side analogues of the per-event condition fields in the harvest database (`SurfConditions`, `WindConditions`, `SkyConditions`, etc.). Together they determine which condition table (daylight, near-dark, poor-weather) a count is expanded against.
- The harvest database stores a single resolved `CorrectionFactor` per event; this database stores the raw survey data from which the table behind that number is built. They share the same beach coding scheme (`LUT Beach Name` here matches `lut_Beach` there).
- The per-event correction-factor logs (2023-24 onward) record staff averaging two adjacent table bins "at peak effort." Those bin values are the `PctAvail` curve described in Section 5, read at the count's timing.

---

## 7. The expansion-table version history this database clarifies

Cross-checking the curves derived here against the published tables and the recent CF logs resolves how the tables have evolved:

1. **2010-2011 tables** (the date-less "Cumulative Ingress" PDFs, dated 11/03/2010 and 01/25/2011) are reproduced exactly by pooling the surveys in this database (Section 5).
2. **2013 tables** (the date-stamped PDFs: Long Beach 2013-02-11, Mocrocks 2013-09-18, Twin Harbors 2013-09-24) differ from the 2010-2011 versions in the peak window, so they were re-derived with **additional surveys collected between 2011 and 2013** that are not in this database.
3. **Current tables** (the values in the 2023-2026 CF logs, e.g., Long Beach 0.574/0.589, Copalis 0.541/0.547) differ again and are not contained in this database; they reflect the full multi-decade survey collection, only partly represented in the provided files. Recent raw surveys do exist as standalone spreadsheets in the project folder (for example `Ingress__Copalis__April_24_2023.xlsx`, `Ingress__Mocrocks__April_25_2023.xlsx`), which are the kind of records that would extend this database forward.

**Bottom line for the missing-tables question.** This database is the authoritative, reproducible *method and early-data* source: it shows precisely how the tables are built and regenerates the 2010-2011 tables to three decimals. It does **not** contain the post-2013 surveys that produced the current CF values, so it cannot, by itself, regenerate today's tables. The most direct path to a current, authoritative lookup is to extend this database (or its method) with every egress survey collected since 2011, including the 2022-2023 ingress spreadsheets already in the folder, and re-pool per beach and condition.

---

## 8. Data-quality and usage notes

1. **Time-only `Tide Time`.** The date component is a sentinel; use the time only. Pair it with `Event Date` for the full timestamp.
2. **Sparse conditions.** `Weather`/`Wind` are null in 8 of 20 rows, `Surf` in 9, `Sampler` in 5, `Notes` in 18. Condition-based table selection for those surveys must fall back on `Evening?` and `Tide Level` alone.
3. **Variable survey window.** Each survey fills 15 to 21 of the 23 bins; blanks inside the surveyed span are zero counts, blanks outside it are "not observed." Cumulating treats both as zero, which is correct for the pooled-curve method but means very short windows contribute thin tails.
4. **Low-turnout surveys carry noisy curves.** Some events have small crowds (for example Long Beach 2004-04-23 peaks at only 0.376; Copalis 2008-11-13 at 0.351). Pooling across surveys mitigates this, but a per-survey curve from a light day should not be used alone to set a table.
5. **Column order.** `Cars On`/`Cars Off` store `3:30 - 3:15` and `Prior To Start` out of sequence (appended last). Always re-sort to chronological order before cumulating.
6. **No Kalaloch surveys** are present despite Kalaloch being in the beach lookup (Section 4).
7. **Small, clean, and self-consistent.** Unlike the harvest database, this one has no duplicate-row or join-multiplication hazards; the 1:1 `ID` linkage is intact across all three core tables and the lookups resolve cleanly.

---

*Companion documents: `RazorClam_Harvest_DB_DataDictionary.md` (the creel/harvest database), `Effort_Expansion_Protocol.md` (the effort-to-harvest SOP, including CF derivation), and `RazorClam_CF_ExpansionTable_Lookup.xlsx` (the consolidated expansion-table lookup, which this database's survey curves feed).*
