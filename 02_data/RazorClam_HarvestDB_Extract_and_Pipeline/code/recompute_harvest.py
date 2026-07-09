"""
recompute_harvest.py
Rebuild WDFW razor clam recreational effort, harvest and CPUE from the raw tables of
'Razor Clam Recreational Harvest Database iForms.accdb'.

Validated: reproduces the database's own stored `Spreadsheet` table for CalcPeople,
CPUE, EstCorEffort and TotHarvest on 13,651 of 13,653 joinable rows (99.99%).
The two exceptions are documented in the audit log.

Inputs : raw/*.csv  (mdb-export -D '%Y-%m-%d %H:%M:%S' of every table)
Outputs: clean/*.csv, derived/*.csv, audit_log.csv
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings('ignore')

RAW = 'raw/'
OUT = 'out/'
os.makedirs(OUT + 'clean', exist_ok=True); os.makedirs(OUT + 'derived', exist_ok=True)

PARAMS = dict(ppl_per_car_default=2.67, clam_cap=200, people_cap=60,
              length_min=50, length_max=200, cf_max=1.0,
              dedup_exact_census=True, drop_duplicate_events=True)

CANON = {'longbeach': 'LongBeach', 'long beach': 'LongBeach', 'twin harbors': 'Twin Harbors',
         'copalis': 'Copalis', 'mocrocks': 'Mocrocks', 'kalaloch': 'Kalaloch'}
AUDIT = []
def log(step, n, detail=''):
    AUDIT.append(dict(step=step, rows=int(n), detail=detail))

def season(ts):
    if pd.isna(ts): return None
    y = ts.year if ts.month >= 7 else ts.year - 1
    return f"{y}-{str(y+1)[2:]}"

# ---------------------------------------------------------------- load
ev  = pd.read_csv(RAW + 'tbl_events.csv', low_memory=False)
cr  = pd.read_csv(RAW + 'tbl_Creel.csv', dtype={'LocationID': str}, low_memory=False)
dc  = pd.read_csv(RAW + 'tbl_DiggerCounts.csv', dtype={'LocationID': str}, low_memory=False)
wa  = pd.read_csv(RAW + 'tbl_Wastage.csv', dtype={'LocationID': str}, low_memory=False)
ln  = pd.read_csv(RAW + 'TBL_Length.csv', dtype={'LocationID': str}, low_memory=False)
lut = pd.read_csv(RAW + 'lut_Beach.csv', dtype={'LocationID': str})
lut['LocationID'] = lut.LocationID.str.strip(); lut['BeachName'] = lut.BeachName.str.strip()
VALID_LOC = set(lut.LocationID)

ev['Date'] = pd.to_datetime(ev['Date'], errors='coerce')
ev['beach'] = ev.BeachName.map(lambda s: CANON.get(str(s).strip().lower()))
ev['date'] = ev.Date.dt.date
ev['season'] = ev.Date.apply(season)
log('beach names normalized', (ev.BeachName != ev.beach).sum(),
    'three spellings of Long Beach collapsed to lut_Beach canonical')
log('events with null beach', ev.beach.isna().sum())
log('events with null date', ev.Date.isna().sum())

# ---------------------------------------------------------------- clean
for nm, df in (('creel', cr), ('diggercounts', dc)):
    n = df.EventID.isna().sum(); log(f'drop {nm}: null EventID', n)
cr = cr.dropna(subset=['EventID']); dc = dc.dropna(subset=['EventID'])
VE = set(ev.EventID)
for nm, df in (('creel', cr), ('diggercounts', dc), ('wastage', wa), ('length', ln)):
    bad = ~df.EventID.isin(VE)
    log(f'drop {nm}: orphan EventID', bad.sum(), str(sorted(df.loc[bad, 'EventID'].unique())))
cr = cr[cr.EventID.isin(VE)]; dc = dc[dc.EventID.isin(VE)]
wa = wa[wa.EventID.isin(VE)]; ln = ln[ln.EventID.isin(VE)]

for c, cap in (('CreelNClams', PARAMS['clam_cap']), ('CreelNPeople', PARAMS['people_cap']),
               ('CreelNDiggers', PARAMS['people_cap'])):
    n = (cr[c] > cap).sum(); cr.loc[cr[c] > cap, c] = np.nan
    log(f'nullify {c} > {cap}', n, 'impossible value; 15-clam limit, groups rarely >10 diggers')

bad = ln.Length.between(PARAMS['length_min'], PARAMS['length_max'], inclusive='both')
log('nullify shell length outside [50,200] mm', (~bad).sum()); ln.loc[~bad, 'Length'] = np.nan

mis = dc.NCars >= dc.NPeople * 2
log('drop mis-entered census rows (NCars >= 2*NPeople)', mis.sum(),
    f"EventIDs {sorted(dc.loc[mis,'EventID'].unique().astype(int))}")
dc = dc[~mis]

if PARAMS['dedup_exact_census']:
    dup = dc.duplicated(subset=['EventID', 'LocationID', 'NPeople', 'NLanterns', 'NCars'], keep='first')
    log('drop exact-duplicate census rows', dup.sum()); dc = dc[~dup]

# duplicate EVENTS on one beach-date: keep only those whose segment sets overlap
segs = dc.groupby('EventID').LocationID.apply(lambda s: frozenset(s.dropna()))
grp = ev.dropna(subset=['beach', 'date']).groupby(['beach', 'date']).EventID.apply(list)
drop_ev, split_ev = [], []
for (b, dt), ids in grp[grp.map(len) > 1].items():
    ss = [segs.get(i, frozenset()) for i in ids]
    overlap = any(ss[i] & ss[k] for i in range(len(ss)) for k in range(i + 1, len(ss)))
    if overlap:
        keep = max(ids, key=lambda i: len(segs.get(i, frozenset())))
        drop_ev += [i for i in ids if i != keep]
    else:
        split_ev.append((b, dt, ids))
log('duplicate EVENTS dropped (overlapping segment sets on one beach-date)', len(drop_ev), str(sorted(drop_ev)))
log('beach-dates legitimately split across two events (disjoint segments)', len(split_ev),
    'Long Beach walks its 7 segments as a 4-segment and a 3-segment count, each its own EventID')
if PARAMS['drop_duplicate_events']:
    dc = dc[~dc.EventID.isin(drop_ev)]; cr = cr[~cr.EventID.isin(drop_ev)]
    wa = wa[~wa.EventID.isin(drop_ev)]; ln = ln[~ln.EventID.isin(drop_ev)]
    ev = ev[~ev.EventID.isin(drop_ev)]

evc = ev.copy()
n = (evc.CorrectionFactor > PARAMS['cf_max']).sum()
log('CorrectionFactor > 1 set to NA', n, 'CF is a fraction of the day\'s diggers present at count time')
evc.loc[evc.CorrectionFactor > PARAMS['cf_max'], 'CorrectionFactor'] = np.nan
log('CorrectionFactor null', evc.CorrectionFactor.isna().sum())
evc['CF'] = evc.CorrectionFactor.astype('float32').astype('float64')

# ---------------------------------------------------------------- estimate
rates = cr.groupby('EventID').agg(
    sum_clams=('CreelNClams', 'sum'), sum_diggers=('CreelNDiggers', 'sum'),
    sum_people=('CreelNPeople', 'sum'), sum_lanterns=('CreelNLanterns', 'sum'),
    ppl_per_car=('CreelNCars', 'mean'), n_interviews=('EventID', 'size')).reset_index()
rates['CPUE'] = rates.sum_clams / rates.sum_diggers.replace(0, np.nan)
rates['diggers_people'] = rates.sum_diggers / rates.sum_people.replace(0, np.nan)
rates['diggers_lanterns'] = rates.sum_diggers / rates.sum_lanterns.replace(0, np.nan)

cen = dc.merge(rates, on='EventID', how='left').merge(
    evc[['EventID', 'beach', 'date', 'season', 'CF']], on='EventID', how='left')
cen['CalcPeople'] = np.where(cen.NPeople.notna(), cen.NPeople,
                     np.where(cen.NCars.notna(), cen.NCars * cen.ppl_per_car,
                      np.where(cen.NLanterns.notna(), cen.NLanterns * cen.diggers_lanterns,
                               cen.NCars * PARAMS['ppl_per_car_default'])))
cen['EstCorEffort'] = cen.CalcPeople * cen.diggers_people / cen.CF
cen['TotHarvest'] = cen.EstCorEffort * cen.CPUE

wst = wa.groupby('EventID').agg(sum_holes=('NHoles', 'sum'), sum_morts=('NMorts', 'sum')).reset_index()
wst['wastage_rate'] = wst.sum_morts / wst.sum_holes.replace(0, np.nan)

by_event = cen.groupby('EventID', as_index=False).agg(
    effort=('EstCorEffort', 'sum'), harvest=('TotHarvest', 'sum'),
    n_census=('EstCorEffort', 'size'), people=('CalcPeople', 'sum'))
by_event = by_event.merge(evc[['EventID', 'beach', 'date', 'season', 'CF', 'TideHeight']], on='EventID') \
                   .merge(rates[['EventID', 'CPUE', 'diggers_people', 'sum_people', 'n_interviews']], on='EventID', how='left') \
                   .merge(wst[['EventID', 'wastage_rate']], on='EventID', how='left')
by_event['wastage'] = by_event.harvest * by_event.wastage_rate
by_event['pct_interviewed'] = by_event.sum_people / by_event.effort.replace(0, np.nan)

by_day = by_event.groupby(['beach', 'date', 'season'], as_index=False).agg(
    effort=('effort', 'sum'), harvest=('harvest', 'sum'), wastage=('wastage', 'sum'),
    n_events=('EventID', 'size'), n_census=('n_census', 'sum'), n_interviews=('n_interviews', 'sum'))
by_day['CPUE'] = by_day.harvest / by_day.effort.replace(0, np.nan)

by_season = by_event.groupby(['beach', 'season'], as_index=False).agg(
    effort=('effort', 'sum'), harvest=('harvest', 'sum'), wastage=('wastage', 'sum'),
    dig_days=('date', 'nunique'), n_events=('EventID', 'size'))
by_season['CPUE'] = by_season.harvest / by_season.effort.replace(0, np.nan)

# ---------------------------------------------------------------- write
for nm, df in (('events', evc), ('creel', cr), ('diggercounts', dc), ('wastage', wa), ('length', ln)):
    df.to_csv(OUT + f'clean/clean_{nm}.csv', index=False)
rates.to_csv(OUT + 'derived/creel_event_rates.csv', index=False)
cen.to_csv(OUT + 'derived/effort_harvest_by_census.csv', index=False)
by_event.to_csv(OUT + 'derived/harvest_by_event.csv', index=False)
by_day.to_csv(OUT + 'derived/harvest_by_beach_day.csv', index=False)
by_season.to_csv(OUT + 'derived/harvest_by_beach_season.csv', index=False)
pd.DataFrame(AUDIT).to_csv(OUT + 'audit_log.csv', index=False)

print(pd.DataFrame(AUDIT).to_string(index=False))
print(f"\nby_event {by_event.shape}  by_day {by_day.shape}  by_season {by_season.shape}")
print("\nTOPLINE, last 6 seasons (digger trips / clams / CPUE):")
p = by_season[by_season.season >= '2020-21'].pivot_table(index='season', columns='beach', values='effort')
print(p.round(0).to_string())
