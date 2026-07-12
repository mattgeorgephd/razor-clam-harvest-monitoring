# Figure Review and Proposed Improvements

**Document reviewed:** `04_documentation/2026-Review-WDFW_Harvest_Estimate_Methodology-v7.docx`
**Prepared:** 2026-07-10
**Scope:** A complete review of all 14 figures and the data behind them, identifying where the figures still describe limitations caused by missing data in the past harvest spreadsheets, and proposing concrete updates using the data that is now in the repository.

---

## 1. Executive summary

Three of the fourteen figures carry limitation language that the current repository data now supersedes, and two structural problems sit underneath the whole figure set. The single most consequential change since the figures were rendered is that the **2022-23 in-season workbook has been completed**: the May 2023 tide series (4–14 May 2023, 11 dig days) is now present in `02_data/harvest_inseason_records/2022 Fall - 2023 Spring Harvest.xlsx`. That series was the specific "missing data" that Figures 4 and 12 annotate. Its addition raises the 2022-23 workbook effort from the partial 237,419 digger trips the figures used to a complete 332,629, and it removes the basis for the "understates coastwide effort by at least 26 percent" caption on Figure 12.

Separately, the egress-survey record behind Figure 8 has grown: the consolidated ingress/egress workbook now contains 15 Copalis and Mocrocks surveys from 2022 through 2026 that post-date the record the figure shows, so the "survey program stopped" story the figure tells is now only half the picture.

Two structural findings limit how far the figures can be refreshed and should be resolved regardless of the individual updates:

- **Finding A — figure source code is largely missing.** Only 2 of the 14 figures have generating code in the repository (`v5_figures_and_source/make_figures_pass3_v5.py` renders Figure 4 and Figure 12). No source exists for Figures 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, or 14. The project brief expects figure source in the documentation folder; for twelve figures it is not there. Any faithful re-render of those twelve currently requires reconstructing the plotting code from the data.
- **Finding B — the corrected-estimates workbook is stale for 2022-23.** `02_data/WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx` still holds the pre-completion 2022-23 season (workbook 237,419; corrected ~240,828). Figure 12, Table 17, and the §10 text all read from it, so all three understate 2022-23 until that workbook is regenerated against the completed harvest spreadsheet.

Confidence and priority for every figure are given in §3. The prioritized action list is in §4.

---

## 2. The data that changed since the figures were rendered

Every number below was read directly from the repository on 2026-07-10; provenance is in §5.

| Quantity | Value the figures use (v5) | Value in the repo now | Source of the change |
|---|---|---|---|
| 2022-23 workbook last dig day | ~19 Apr 2023 (partial) | **14 May 2023** | `2022 Fall - 2023 Spring Harvest.xlsx`, Effort tab |
| 2022-23 workbook coastwide effort | 237,419 | **332,629** | same |
| 2022-23 workbook effort, Long Beach / Twin Harbors / Copalis / Mocrocks | 67,589 / 61,500 / 62,523 / 45,807 | **102,568 / 91,403 / 80,182 / 58,476** | same |
| 2022-23 census-backed share (Fig 4), LB / TH / Cop / Moc | 0.362 / 0.662 / 1.00 / 1.00 | **0.394 / 0.617 / 1.00 / 1.00** | recomputed on completed workbook |
| Located egress surveys behind Fig 8 | ends 2011, then a gap | **15 new Copalis/Mocrocks surveys, 2022–2026** | `1993-2026_Ingress_Egress_Consolidated.xlsx`, Survey_Inventory |
| Corrected-estimates workbook, 2022-23 | (unchanged, stale) | still 237,419 / 240,828 | **not yet regenerated** (Finding B) |

The 2017-18 case is different and is **not** a data-availability change. The original 2017-18 in-season workbook does not survive; the FINAL printout is the only record and is already incorporated (Table 5, and the open diamond on Figure 12). No repository data can improve it, so Figure 12's 2017-18 treatment should stay.

---

## 3. Figure-by-figure review

Legend: **Update now** = repo data supports a faithful refresh; **Proposed** = worth doing but needs data or code not yet in the repo; **No change** = figure is current or describes a permanent structural fact.

### Figure 1 — Coastwide harvest, 1949–2024
- **Stated limit:** series ends at 2024; wastage only from 1999.
- **Now available:** the database-derived coastwide series exists through 2025-26, but as *harvest before wastage* and only reliably from 2007-08. The 1949–2024 series the figure plots (WDFW historical summary 1949–1998 plus season summaries 1999–2024) is **not in the repo**; the closest file, `harvest_yearly_summaries/WA Razor Clam Historical Harvest Effort Summary 2000 to 2021.xlsx`, is 2000–2021 only and is a different quantity.
- **Proposal:** append 2024-25 and 2025-26 once the original 1949–2024 source series is located, so the axis and the definition of "harvest" stay consistent. Do not splice the database series onto the historical one; the two measure different things (before vs. including wastage).
- **Verdict:** Proposed (blocked on source data). Confidence: high on the diagnosis, low on doing it from repo data alone.

### Figure 2 — Coastwide participation (effort), 1949–2024
- Same situation and same source gap as Figure 1.
- **Verdict:** Proposed (blocked on source data).

### Figure 3 — Management milestones, 1929–present
- Static timeline, no underlying dataset.
- **Verdict:** No change.

### Figure 4 — Census-backed share of the Effort-tab season total, by beach
- **Stated limit (caption):** "…2022-23, where the share is computed only on the part of the season the workbook holds, since the May 2023 tide series is absent from it."
- **Now available:** the May 2023 series is in the workbook. Recomputed on the completed season the 2022-23 shares are Long Beach 0.394, Twin Harbors 0.617, Copalis 1.000, Mocrocks 1.001.
- **Proposal:** recompute the 2022-23 point on the full-season denominator and replace the "absent from the workbook" annotation with a note that the season is now complete. Keep the 2017-18 circled point (permanent). Source exists (`make_figures_pass3_v5.py`).
- **Verdict:** **Update now.** Confidence: high.

### Figure 5 — The four operational expansion tables
- Structural (Kalaloch has no table). Not a data gap.
- **Verdict:** No change (optionally note the post-2021 surveys now available for future rebuilds; see Fig 8).

### Figure 6 — Correction-factor RSD vs. count-window position
- Rests on the surveys behind each table. New 2022–2026 Copalis/Mocrocks surveys exist but are not yet pooled into operational tables, so they should not silently change the curve.
- **Verdict:** No change now; revisit if/when the tables are rebuilt with the new surveys.

### Figure 7 — Within-season CV of the stored correction factor
- **Now available:** the recomputed event table spans 2007-08 to 2025-26, so the figure can already reach 2025-26. Worth confirming the render includes 2024-25 and 2025-26.
- **Verdict:** Proposed (low effort) — confirm season span; reconstruct code (none in repo).

### Figure 8 — Every located egress survey, by beach and year
- **Stated limit (caption):** "No survey exists between 2012 and 2021…"
- **Now available:** the consolidated inventory holds 15 surveys after the gap — Copalis and Mocrocks in 2022 (2), 2023 (2), 2024 (6), 2025 (2), 2026 (3). The 2012–2021 gap is real and stays, but the record no longer ends at 2011.
- **Proposal:** extend the axis to 2026 and plot the resumed Copalis/Mocrocks program; keep the gap visible; keep the Kalaloch-is-really-Mocrocks-1998 note. Reconstruct code (none in repo); data is clean in `Survey_Inventory`.
- **Verdict:** **Update now.** Confidence: high.

### Figure 9 — Operational table vs. its 2012/2013 vintage
- Structural comparison of published tables. No data gap; new surveys are not yet in operational tables.
- **Verdict:** No change.

### Figure 10 — Variance shares by source, 2019-20 onward
- Reads the same corrected/variance workbook as Figure 12. Because that workbook is stale for 2022-23 (Finding B), the 2019-20-onward average includes a 2022-23 that is wrong.
- **Verdict:** Proposed — re-render after the corrected workbook is regenerated (§4, item 2).

### Figure 11 — Imputation-error distribution
- Derived from the full paired-day pool (2,889 beach-days). Adding the completed 2022-23 counted days would grow the pool slightly; effect is marginal.
- **Verdict:** Proposed (low priority) — refresh the pool count after 2022-23 is folded in.

### Figure 12 — Season effort by beach, 2007-08 to 2025-26
- **Stated limits (caption):** the 2022-23 inverted triangle "understates coastwide effort by at least 26 percent"; and the 2017-18 grey cross "understates the season by a factor of two to three."
- **Now available:** the 2022-23 workbook is complete (332,629 coastwide). The 26 percent understatement is resolved in the data. The 2017-18 case is permanent and stays.
- **Blocker:** the corrected line and the 95% band for 2022-23 come from the stale workbook (Finding B). The corrected value is exactly `workbook × (1 + bias/100)`, and bias is ~0 for the fully-counted beaches (Copalis, Mocrocks) but nonzero for the imputed ones (Long Beach, Twin Harbors), so the corrected 2022-23 must be re-derived on the completed season, not simply re-plotted.
- **Proposal:** (a) update the 2022-23 workbook line to 332,629 per beach; (b) remove the inverted-triangle / 26-percent annotation; (c) re-derive the corrected 2022-23 point and band from the completed workbook, validating the re-derivation reproduces every other season's published corrected value before trusting it.
- **Verdict:** **Update now** for (a) and (b); (c) depends on regenerating the corrected workbook (§4, item 2).

### Figure 13 — Tide-series CV vs. days counted
- Design/simulation figure driven by the correction-factor floors, not by season data.
- **Verdict:** No change.

### Figure 14 — Season harvest CV vs. imputed share
- Driven by the correction-factor floors and 2025-26 imputed shares, which are current.
- **Verdict:** No change.

---

## 4. Prioritized action list

1. **Figure 4 — recompute the 2022-23 census-backed share and re-annotate.** Repo data complete; source code exists. *(Update now.)*
2. **Regenerate the corrected-estimates workbook for 2022-23**, then re-render **Figure 12** (workbook line, corrected line, band, annotation), **Figure 10** (variance shares), and **Table 17 / §10 text**. This is the highest-value item because one stale workbook propagates into a figure, a table, and the prose. *(Update now for the figure's workbook line and annotation; corrected line/band after the workbook is rebuilt.)*
3. **Figure 8 — extend to 2026 with the resumed Copalis/Mocrocks surveys**, keeping the 2012–2021 gap visible. *(Update now.)*
4. **Restore figure source code to the documentation folder** for every figure touched, and ideally for all fourteen, so future updates do not require reverse-engineering. *(Structural fix — Finding A.)*
5. **Figures 1, 2 — extend to 2025** once the original 1949–2024 coastwide harvest/effort source is located. *(Proposed; blocked on source data.)*
6. **Figures 7, 11 — confirm/refresh season span and paired-day pool** after 2022-23 is folded in. *(Proposed; low priority.)*

Figures 3, 5, 6, 9, 13, 14 need no change; 5, 6, 9 should be revisited only if the expansion tables are rebuilt with the newly available 2022–2026 surveys, which is a separate methodological decision, not a figure edit.

---

## 5. Data provenance (verified 2026-07-10)

- **2022-23 workbook completion:** `02_data/harvest_inseason_records/2022 Fall - 2023 Spring Harvest.xlsx`, Effort tab — 125 dated rows, first 2022-09-22, last 2023-05-14; May 2023 rows present (4,5,6,7,8,9,10,11,12,13,14 May). Per-beach season effort: Long Beach 102,568; Twin Harbors 91,403; Copalis 80,182; Mocrocks 58,476; coastwide 332,629.
- **2022-23 database (census) effort:** `…/derived/harvest_by_beach_day.csv`, season 2022-23 — Long Beach 40,452 (24 days); Twin Harbors 56,353 (26); Copalis 80,171 (38); Mocrocks 58,525 (27); coastwide 235,501.
- **Census-backed shares (completed workbook):** LB 40,452/102,568 = 0.394; TH 56,353/91,403 = 0.617; Cop 80,171/80,182 = 1.000; Moc 58,525/58,476 = 1.001.
- **Egress-survey inventory:** `02_data/IE data/1993-2026_Ingress_Egress_Consolidated.xlsx`, Survey_Inventory — 55 surveys total; post-gap: Copalis 2022,2023,2024×3,2025,2026×2; Mocrocks 2022,2023,2024×3,2025,2026.
- **Corrected estimate is workbook × (1+bias/100):** verified against `WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx`, Season_Estimates (2019-20 and 2023-24 reproduce exactly). 2022-23 rows there still read workbook 237,419 / corrected 240,828 — stale.
- **Figure source inventory:** repository contains generating code only in `04_documentation/v5_figures_and_source/` (`make_figures_pass3_v5.py` → Figures 4 and 12; `make_table_data_v5.py` → their input JSON). No source for the other twelve figures.

---

## 6. Execution status

**v9 (current)** — `2026-Review-WDFW_Harvest_Estimate_Methodology-v9.docx` completes the full re-derivation and consistency pass on top of v8. The 2022-23 season is re-derived on the completed workbook and every dependent figure, table, and passage is updated:

- **Figure 12** corrected line/band for 2022-23 are now the re-derived values (no longer provisional): Copalis 80,182 and Mocrocks 58,476 (fully counted, so corrected = workbook, exact); Twin Harbors 93,294 (day-level pair-median multiplier method, which reproduces the published *partial*-season value to 0.006%); Long Beach 106,199 (season bias fraction +3.54%, valid because the imputed fraction is stable at 38.2%→39.3%). Coastwide corrected ≈ 338,150.
- **Table 1** (composition) 2022-23 row → 64% direct census / 13% Long Beach section ratio / 23% cross-beach borrowed (was 67/14/20 on the partial season).
- **Table 10** (defects) 2022-23 row reframed from "omits an entire tide series" to a resolved defect (restored; season re-derived; official WDFW total still predates the restoration).
- **§4.5, §12.3, §12.4 (Table 23), §13 References** — every "the workbook omits May 2023 / ends 25 Apr 2023" statement reframed to reflect the restoration and re-derivation; recommendation #1 changed from "restore and republish" to "republish from the completed workbook."

The corrected estimate = workbook × (1 + bias/100) relationship was validated against all 19 seasons. The one item the artifacts cannot fully reproduce is Long Beach's exact pipeline internals (its §5.4 two-count second imputation plus the undocumented imputed-value tercile boundaries), because the corrected-estimates pipeline *code* is not in the repo; two independent methods bound Long Beach to 106,199–106,319 (±0.1%), which is immaterial to the figure and the numbers reported.

**v8** — `2026-Review-WDFW_Harvest_Estimate_Methodology-v8.docx` regenerated three figures and their captions (Figure 12's corrected values were provisional there). Source and PNGs are in `04_documentation/v8_figures_and_source/`.

- **Figure 4 (rzc11.png)** — 2022-23 census-backed share recomputed on the completed workbook (Long Beach 0.39, Twin Harbors 0.62; Copalis and Mocrocks at 1.00). The "May 2023 absent" marker and annotation are removed; the 2017-18 marker is kept. Every other season is byte-identical to v5. **Fully verified.**
- **Figure 8 (rzc14.png)** — rebuilt from the consolidated Survey_Inventory. It now shows the resumed 2022–2026 Copalis/Mocrocks program. Its per-beach counts (Long Beach 6, Twin Harbors 7, Copalis 12, Mocrocks 13) and survey-years now match **Table 4 exactly** — the figure had been lagging its own table, which already listed the 2022–2026 surveys. **Fully verified and now internally consistent.**
- **Figure 12 (rzc3.png)** — the 2022-23 workbook line moves to the completed 332,629 coastwide (from the partial 237,419); the false "understates by at least 26 percent" triangle is removed. The corrected point and 95 percent band for 2022-23 are **provisional** (workbook × the season's imputation-bias fraction; band scaled by the point ratio) pending a proper regeneration of the corrected-estimates workbook. The 2017-18 diamond/cross (a permanent limitation) is unchanged.

Table renumbering from the prior step is intact (23 tables, captions 1–23 sequential, all cross-references resolve) and `updateFields` is set so Word rebuilds the List of Tables/Figures on open.

## 7. Downstream consistency — the 2022-23 completion is entangled with the prose

Figure 8's update is self-contained. The 2022-23 harvest completion behind Figures 4 and 12 is **not**: the same "missing May 2023" fact is asserted across the body text, the defects material, the error budget, a citation, and the recommendations. Updating only the figures leaves the document internally inconsistent. The affected passages split into two kinds.

**Now factually incorrect (the workbook was completed after v7's analysis ran):**

- "The Effort tab ends 25 Apr 2023" — it now ends **14 May 2023**.
- "The 2022-23 workbook omits an entire tide series" / "the workbook omits the May 2023 tide series entirely, so the row describes part of a season" — the workbook now holds the 4–14 May 2023 series (11 dig days).
- Any table row or prose count tied to "the 62 dig days the workbook holds" for 2022-23 — the completed workbook is larger.

**Still valid, because the derived estimates were not re-run (this is the real remaining work):**

- The recommendation "Restore the 4 to 14 May 2023 tide series to the 2022-23 workbook **and re-derive** that season's effort, harvest, wastage…" — part one (restore to the workbook) is **done**; part two (re-derive) is **not**. `WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx` and `…Imputation_Error…xlsx` still carry the partial season.
- The error-budget figure "understated by at least 61,959 digger trips, 26.1 percent" — still the correct magnitude of the pending re-derivation.
- "the published 2022-23 season totals are not season totals" — the officially published totals remain partial until the season is re-derived and re-published.

**Status: completed in v9.** The 2022-23 season was re-derived on the completed workbook and every affected figure, table, and passage updated (see §6). Two items remain genuinely outstanding and are noted as such in the document rather than silently resolved: (a) the *harvest* (clams), wastage, and percent-of-TAC for 2022-23 were not re-derived here — only effort — and (b) official WDFW republication of the season is an agency action outside this review. Both are flagged in §12.3 and the References. The corrected-estimates *workbook* (`WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx`) and the imputation-error workbook still carry the partial 2022-23 internally; regenerating those data artifacts (as opposed to the document's reported values, which are now correct) is the remaining data-pipeline task.
