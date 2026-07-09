# Effort-Expansion and Harvest-Estimation Protocol: Recreational Razor Clam Creel

**Status:** Draft for program review
**Derivation:** Reverse-engineered from, and validated against, the legacy WDFW Razor
Clam Recreational Harvest Access database (query pipeline `01`-`16` and the
`Macro Calculate Harvest Estimate`). Companion documents: `RazorClam_Harvest_DB_DataDictionary.md`
(data model and data-quality review) and `extract_recompute_harvest.Rmd` (reference
implementation in R).
**Validation:** The formulas in Section 3 were applied to the database's own inputs and
reproduce its stored `Spreadsheet` outputs (`CalcPeople`, `EstCorEffort`, `TotHarvest`)
to floating-point precision.

> This document formalizes the procedure the legacy database performs and exposes the
> methodological choices embedded in it so the program can ratify, revise, or document
> them. Items flagged **[DECISION]** are choices the existing system made implicitly and
> that a formal protocol should make explicitly.

---

## 1. Purpose and scope

Estimate total recreational razor clam (*Siliqua patula*) harvest, fishing effort, and
wastage for each Washington coastal management beach (Long Beach, Twin Harbors, Copalis,
Mocrocks, Kalaloch) and dig, by expanding two field data streams:

1. **Instantaneous effort censuses** (counts of people, and sometimes lanterns or cars,
   along beach segments at a point in time), and
2. **Creel interviews** (digging-group composition and catch sampled as diggers leave).

The instantaneous census provides a snapshot of who is present; the creel provides per-
capita catch and the composition ratios needed to convert the snapshot into total daily
digger-trips and total catch.

This protocol covers the harvest-estimation calculation only. It does not cover field
survey design (transect/segment definitions, count timing, interview selection), which it
treats as inputs and which should be documented separately.

**Fishery structure (context for the estimate).** WDFW opens the fishery as announced
**series of open digging days** per beach, beginning in fall and extended through the
following spring as the season progresses. Days are opened when the low tide is favorable
(low enough) and usually during daylight, though night digs occur in winter. Access is
time-restricted relative to the tide: during fall evening low tides digging is not allowed
before noon, and during spring morning low tides it is allowed only between midnight and
noon. An "event" in this protocol is one beach sampled on one open day within a series; a
season runs fall to spring and is labeled by its starting year. These windows are what the
correction factors (Section 3.3) summarize: effort builds toward the posted low tide
(typically peaking 1 to 2 hours before) and recedes afterward.

---

## 2. Units, entities, and field variables

**Sampling event** (`EventID`): one beach surveyed on one date. The estimation unit.

**Segment** (`LocationID`): a named stretch of a beach (7 on Long Beach, 4 on Twin
Harbors, 6 on Copalis, 6 on Mocrocks, 5 named access points on Kalaloch). Defined in the
`lut_Beach` lookup. Censuses and interviews are tagged to segments.

**Field data collected per event:**

| Stream | Variable | Meaning |
|---|---|---|
| Census (per segment) | `NPeople` | people counted on the segment at count time |
| Census (per segment) | `NCars`, `NLanterns` | vehicles / lanterns counted (often not recorded) |
| Creel (per group) | `CreelNPeople` | people in the interviewed group |
| Creel (per group) | `CreelNDiggers` | diggers in the group |
| Creel (per group) | `CreelNClams` | clams the group held |
| Creel (per group) | `CreelNLanterns` | lanterns for the group (night digs) |
| Creel (per group) | `CreelNCars` | **people per car for the group** (see note) |
| Event | `CorrectionFactor` (CF) | fraction of the day's diggers present at census time |
| Wastage survey (per dig) | `NHoles`, `NMorts` | holes excavated, wasted/dead clams found |

> **Field-name caution:** the database column `CreelNCars` stores *people per car*, not a
> vehicle count. This is confirmed by the update step that consumes it ("Update Avg Ppl
> Per Car") and by its mean (~2.52, near the historical default of 2.67). The reference
> implementation renames it `ppl_per_car`. Any new data collection or documentation should
> use an unambiguous name.

---

## 3. Estimation procedure

Notation: for event *e*, sum creel quantities over all interviews *i* in the event;
compute segment quantities for each census *s* in the event.

### 3.1 Event-level creel rates (pooled across the event)

```
CPUE_e            = Sum(CreelNClams_i)   / Sum(CreelNDiggers_i)      # clams per digger
DiggersPeople_e   = Sum(CreelNDiggers_i) / Sum(CreelNPeople_i)       # digging fraction
DiggersLanterns_e = Sum(CreelNDiggers_i) / Sum(CreelNLanterns_i)     # diggers per lantern
PplPerCar_e       = Mean(ppl_per_car_i)                              # people per car
```

These rates characterize the typical digging group on that beach-day and are applied to
every segment census in the event.

### 3.2 Estimate people present at each census (hierarchical)

The census ideally counts people directly. When it does not, people are inferred from the
secondary count that was recorded, using the event's creel ratios:

```
CalcPeople_{e,s} =
    NPeople                          if NPeople recorded
    NCars     * PplPerCar_e          else if NCars recorded
    NLanterns * DiggersLanterns_e    else if NLanterns recorded
    NCars     * 2.67                 otherwise (historical default people-per-car)
```

**People-per-car constant (documented).** The fallback constant 2.67 is the historical
average people-per-car derived from interview data; it is the long-run value of the same
quantity that `AvgOfCreelNCars` estimates per event. It is used only as the last resort in
the precedence above, when a census records cars but no people or lantern count and the
event has no creel-derived people-per-car. The one remaining item to confirm is the
precedence order itself (e.g., whether a recorded `NLanterns` should ever outrank a recorded
`NCars`). The `ppl_per_car_default` is a parameter in the reference implementation.

### 3.3 Expand to corrected effort, then harvest (per census)

```
EstCorEffort_{e,s} = CalcPeople_{e,s} * DiggersPeople_e / CF_e     # total digger-trips
Harvest_{e,s}      = EstCorEffort_{e,s} * CPUE_e                   # clams
```

Rationale: `CalcPeople * DiggersPeople` converts people present to diggers present at the
snapshot; dividing by `CF_e` (typically ~0.5) expands the snapshot to the full day's
digger-trips, because the instantaneous count captures only diggers present at count time,
while the dig spans a window of the tidal cycle.

**Correction factor derivation and history (from program records).** The correction
factor is **not** computed from an event's own data. It is a lookup from a beach- and
condition-specific **ingress/egress expansion table**. Those tables come from egress
surveys in which staff count cars on and off the beach at access points in 15-minute
intervals across the tidal cycle (about 3 hours before to 2 hours after low water); the
accumulated cars-on-beach at each interval, as a percentage of the peak, is the
"% available for the beach count" (the egress ratio R). For a given count, `CF = R_t`, the
mean % available over the count's time window relative to low water (a count takes ~26 to
31 minutes). The standard count is made about 1 hour before low water; the effort peak
itself varies by beach and tide (for Long Beach evening tides it is nearer 1:45 to 2:00
before low water at ~73%, while the 1-hour-prior bin is ~56%, which matches the stored Long
Beach CF values).

Separate tables exist for different conditions: program records include daylight,
near-dark (low tide just after dark), and poor-weather variants (`Master_Tables.xls` holds
Copalis daylight, Copalis near-dark, Mocrocks daylight, Mocrocks poor-weather, and Kalaloch
daylight tables; the evening-tide tables for Long Beach, Twin Harbors, Copalis, and
Mocrocks are separate files). Night and weather conditions therefore draw a different table
and explain CF values above the daylight range. The expansion form
`E_total = E_t(1-p)/CF` is the one corrected in May 2013, when WDFW found the 1987 method
(`CF = 1.0 + (1-R)`, applied multiplicatively) underestimated effort by ~16% and re-
estimated Copalis and Mocrocks back to 1997-98 (documented in the 2013 Ayres memo and
`harvest_correction_summary.xls`). The stored `CorrectionFactor` values are the post-2013
`CF = R_t` form.

**Vintage and the preset question.** Every ingress/egress table in the program records was
last updated in late 2012 or 2013 (Long Beach 2/11/2013, Mocrocks 9/18/2013, Twin Harbors
9/24/2013, Copalis 12/19/2012); no later re-derivation appears in the files. So although
egress data is reportedly still collected, the expansion tables that set CF have effectively
been frozen at their 2012-2013 values and reused every season since, which is the sense in
which CF is a fixed preset. Separately, the spread of stored CF values within a beach-season
narrows markedly from about 2023 on (coefficient of variation falling from ~0.08-0.15 to
~0.02-0.04), consistent with more uniform count timing or more standardized application of
the fixed tables in recent seasons; the cause should be confirmed with the biologists. Any
value outside (0, 1] is an error (one event carries CF = 2.1). Because CF is calibrated to a
single count near a reference time on the effort curve, the census used for expansion should
be the count at or nearest that time; this is the basis for the replicate-handling rule in
Section 4.

### 3.4 Event totals

```
EstCorEffort_e = Sum_s EstCorEffort_{e,s}
Harvest_e      = Sum_s Harvest_{e,s}
WastageRate_e  = Sum(NMorts) / Sum(NHoles)          # over wastage surveys in event e
Wastage_e      = Harvest_e * WastageRate_e          # estimated wasted clams
PctInterviewed_e = Sum(CreelNPeople_i) / EstCorEffort_e   # sampling-intensity diagnostic
```

### 3.5 Beach and season rollups

```
Harvest_{beach, season} = Sum over events in (beach, season) of Harvest_e
```

A **season-year** runs from the configured cut month (default July) so a single fall-to-
spring dig season carries one label (e.g., a dig in November 2024 and one in February
2025 both belong to season "2024-25").

### 3.6 Days with no count (estimated harvest)

When no crew counts a beach on an open day, that beach-day harvest is not left blank; it is
estimated from the beaches that were counted. For a missing beach B on day x, harvest is the
counted-beach total on day x scaled by B's share on the most recent counted day:

```
Harvest_{B,x} = ( sum of counted beaches on day x ) * Harvest_{B, prior} / ( sum of the same counted beaches on the prior day )
```

These estimated beach-days are flagged in the yearly workbooks (the `*` markers) and should
be carried as estimates, not measured values, when summarizing a season or propagating
uncertainty.

---

## 4. Aggregation grain rules

- Creel rates (Section 3.1) are pooled at the **event** level, not the segment level, so
  every segment in an event shares one CPUE and one set of ratios. This is the legacy
  behavior and is appropriate when within-event, between-segment catch rates are not
  separately estimable.
- Effort and harvest are computed at the **census** grain (Section 3.2-3.3) and summed to
  the event, because each segment census expands independently.
- **[DECISION] Replicate censuses at one segment.** When more than one census row exists
  for the same `(EventID, LocationID)`, two cases must be separated. (a) **Exact duplicates**
  (identical `NPeople`, `NLanterns`, `NCars`) are data-entry duplicates, in several events an
  entire event's census was entered twice, and must be removed (keep one) unconditionally;
  summing them double-counts effort and, in the observed data, overstates the Twin Harbors
  2022-23 season by ~16%. (b) **Genuine replicates** (different count values, taken at
  different times) should not be summed. Because the correction factor is calibrated to a
  single count at a reference point on the tidal effort curve (near the pre-low-tide peak;
  Section 3.3), the correct input is the one count taken at or nearest that reference time.
  When count times are recorded, select that count; when they are not (the current data has
  no per-count time field), the mean of the replicate counts is the best available
  approximation and is preferred over the sum, which double-applies the full-period
  expansion. The reference implementation removes exact duplicates by default
  (`dedup_exact_census`) and exposes `multi_count_handling` ("sum" reproduces WDFW, "mean"
  recommended) for the genuine replicates; after deduplication the sum-vs-mean choice
  affects only ~0.25% of the all-time total. Recording a per-count time (Section 5, item 7)
  would let the program replace this approximation with the reference-time count directly.
  Censuses with a blank `LocationID` and corrupted events (per-group records mis-entered as
  censuses; Section 5, item 3) are handled separately, not aggregated.

---

## 5. Data-cleaning and QA rules (defensible-estimate requirements)

The estimate must be reproducible from the raw tables with a logged cleaning step. Every
row dropped, nullified, or flagged is recorded with a reason (see `audit_log.csv`).

1. **Beach normalization.** Map the event's `BeachName` to the `lut_Beach` canonical
   spelling before any grouping. The raw field carries three spellings of Long Beach and
   undercounts it by ~36% if used as-is.
2. **Key integrity.** Drop creel/census/wastage/length rows with a null `EventID`
   (unlinkable) or an `EventID` with no parent event (orphans). Log counts and IDs.
3. **Duplicate censuses.** Remove exact-duplicate digger-count rows (identical `EventID`,
   `LocationID`, `NPeople`, `NLanterns`, `NCars`), keeping one. These are data-entry
   duplicates; leaving them double-counts effort. When a per-count time field exists, include
   it in the duplicate key (item 7).
4. **Mis-entered census rows.** Remove digger-count rows whose `NCars` is at least twice
   `NPeople`: a real census has more people than cars, so such rows are per-group records
   typed into the census table by mistake (in this data, only event 509, where `NCars` was
   set to `NPeople` times the 15-clam limit). Removing them corrects the census; it does not
   create a harvest estimate for an event that also lacks creel interviews.
5. **Impossible values.** Treat creel `CreelNClams` above a cap (default 200) and
   `CreelNPeople`/`CreelNDiggers` above a cap (default 60) as data-entry errors, since the
   per-digger limit is 15 clams and groups rarely exceed ~10 diggers. Default action is to
   nullify the offending value (exclude it from sums) rather than drop the whole interview
   or fabricate a capped number. Shell lengths outside [50, 200] mm are nullified.
6. **Source of truth.** Recompute all aggregates from the raw tables. Do **not** read the
   stored derived tables (`Spreadsheet`, `CreelSumm`, `Creel Summary by Area`,
   `Wastage Summary`): they can be stale, and their sum columns are inflated because the
   summary-build query joins creel to digger-counts, multiplying every creel sum by the
   number of census rows for the event (verified: inflation factor equals the census row
   count in 2,657 of 2,657 events). The CPUE ratio is unaffected, which is why the harvest
   chain still validates, but the totals are not usable.
7. **Record a per-count time (recommended collection change).** `tbl_DiggerCounts` has no
   time field, so replicate counts at one segment cannot currently be distinguished from
   duplicates except by value, nor matched to the correction-factor reference time. Adding a
   count-time column would make the duplicate key exact and let the expansion use the count
   nearest the CF reference time (Section 4) instead of a mean approximation.
8. **Validation.** Cross-check recomputed harvest against the legacy `Revised Data 2008 -
   2011` table for those seasons before publishing a back-revised series. The recompute with
   deduplication enabled reproduces the database's own stored `Spreadsheet` harvest for 100%
   of events.

---

## 6. Assumptions and limitations

- **Snapshot-to-total expansion** assumes the correction factor correctly scales one
  instantaneous count to total daily digger-trips for the beach-date; the estimate is only
  as good as CF.
- **Pooled creel rates** assume the interviewed groups represent all diggers on the
  beach-date (no strong segment- or time-of-day catch gradients within the event).
- **Hierarchical people estimate** introduces additional error whenever `NPeople` is not
  recorded and people are inferred from cars or lanterns; the car/lantern branches rely on
  event creel ratios that are themselves sampled.
- **Wastage** is expanded as a flat proportion of harvest from hole-dig surveys and is
  available for a subset of events only.
- **Length** sampling covers ~16% of events and is not part of the harvest estimate.
- **No variance is propagated** in the legacy method or this draft. CPUE, the digging
  fraction, people-per-car, and CF are all sampled or estimated quantities; a defensible
  program estimate should ultimately carry an uncertainty estimate (e.g., by bootstrapping
  interviews within event and propagating CF uncertainty). This is flagged as a future
  extension, not implemented here.

---

## 7. Open items for program ratification

1. **(Documented; two follow-ups)** CF is a lookup from beach- and condition-specific
   ingress/egress expansion tables (Section 3.3). The supplied tables are all 2012-2013
   vintage and have been reused since; confirm with the biologists (a) whether a refresh of
   the tables from the egress data still being collected is due, and (b) what changed around
   2022-23 that tightened the within-season CF spread. Store the daylight, near-dark, and
   poor-weather tables per beach in a versioned lookup, and correct out-of-range entries
   (e.g. the CF = 2.1 event) to the table value for the count's timing and condition.
2. **(Documented)** The 2.67 people-per-car fallback is the historical interview-derived
   average; confirm only the `CalcPeople` precedence order (whether `NLanterns` should ever
   outrank `NCars`).
3. Confirm exact-duplicate censuses are removed by default, and adopt the rule for the
   remaining genuine replicate counts at one segment (Section 4): deduplicate always, use
   the reference-time count when count times exist, otherwise mean-combine rather than sum.
4. Add a per-count time field to `tbl_DiggerCounts` collection so replicate counts are
   distinguishable from duplicates and can be matched to the CF reference time (Section 5,
   item 7).
5. Rename `CreelNCars` to a people-per-car name in any new collection or documentation.
6. Confirm the mis-entered-census repair rule (`NCars >= NPeople * 2`); manually review or
   re-key event 509 if its 1994 census should contribute to the Long Beach series (it
   currently yields no harvest because it has no creel interviews).
7. Decide the impossible-value policy (caps and nullify-vs-drop) and record the chosen
   thresholds; defaults are in the reference implementation `params`.
8. Decide whether to carry an uncertainty estimate (Section 6, final bullet).

---

*This draft is intended to become the program's documented effort-expansion SOP. The
companion R Markdown produces the estimates and the audit trail described here; the data
dictionary documents the underlying tables and their known issues.*
