import re, datetime, csv, collections
txt=open("/tmp/lb1718.txt").read().splitlines()
BE=["Longbeach","Twin Harbors","Copalis","Mocrocks","Kalaloch"]
MON={m:i+1 for i,m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
def n(t): return None if t=="Closed" else float(t.replace(",",""))
rows=[]
for ln in txt:
    m=re.match(r"\s*(\d{1,2})-([A-Z][a-z]{2})\s+(\w+)\s+(-?\d+\.\d)\s+(\d{1,2}:\d{2}\s*[AP]M)\s+(.*)$", ln)
    if not m: continue
    dd,mon,day,tide,time,rest=m.groups()
    yr = 2017 if MON[mon]>=9 else 2018
    d=datetime.date(yr,MON[mon],int(dd))
    toks=re.findall(r"Closed|[\d,]+\.\d|[\d,]+", rest)
    rec={"date":d,"day":day}
    for i,b in enumerate(BE):
        rec[b]=(n(toks[3*i]), n(toks[3*i+1]), n(toks[3*i+2]))
    rec["daily"]=(n(toks[15]), n(toks[16]))
    rows.append(rec)
assert len(rows)==27
# season totals from printout
sub={"Longbeach":(94213,823281),"Twin Harbors":(55588,619897),"Copalis":(43987,543238),"Mocrocks":(63215,745045)}
# sum daily
tot=collections.defaultdict(lambda:[0.0,0.0]); open_bd=collections.Counter()
for r in rows:
    for b in BE[:4]:
        e,h,c = r[b]
        if e is not None:
            tot[b][0]+=e; tot[b][1]+=h; open_bd[b]+=1
print("PRINTOUT: beach | sum of daily effort | printed subtotal | diff | open beach-days")
for b in BE[:4]:
    print(f"  {b:14s} {tot[b][0]:>9,.0f} {sub[b][0]:>9,} {tot[b][0]-sub[b][0]:>7,.0f}   {open_bd[b]}")
print("  coastwide sum of beach subtotals:", sum(sub[b][0] for b in sub), " printed DAILY TOTALS row: 257,004")
print("  total open beach-days:", sum(open_bd.values()), " dig days:", len(rows))

# DB
db=collections.defaultdict(float); dbdays=collections.Counter(); dbday={}
with open("repo/02_data/RazorClam_HarvestDB_Extract_and_Pipeline/derived/harvest_by_beach_day.csv") as f:
    for r in csv.DictReader(f):
        if r["season"]!="2017-18": continue
        b=r["beach"].replace("LongBeach","Longbeach")
        d=datetime.date.fromisoformat(r["date"][:10])
        db[b]+=float(r["effort"]); dbdays[b]+=1; dbday[(b,d)]=float(r["effort"])
print("\nDATABASE 2017-18: beach | effort | beach-days")
for b in BE[:4]:
    print(f"  {b:14s} {db[b]:>9,.0f}  {dbdays[b]}")
print(f"  coastwide {sum(db.values()):,.0f}")

print("\nCOVERAGE vs the FINAL printout")
print(f"{'beach':14s} {'printout effort':>16s} {'DB effort':>12s} {'share':>8s} {'open bd':>8s} {'DB bd':>6s} {'uncounted bd':>13s}")
for b in BE[:4]:
    unc=[r['date'] for r in rows if r[b][0] is not None and (b,r['date']) not in dbday]
    print(f"{b:14s} {sub[b][0]:>16,} {db[b]:>12,.0f} {db[b]/sub[b][0]:>8.3f} {open_bd[b]:>8} {dbdays[b]:>6} {len(unc):>13}  {unc}")
extra=[(b,d) for (b,d) in dbday if not any(r['date']==d and r[b][0] is not None for r in rows)]
print("DB beach-days not open in the printout:", extra)
cw_db=sum(db.values()); cw_pr=sum(sub[b][0] for b in sub)
print(f"\ncoastwide DB-backed share {cw_db/cw_pr:.4f}  ({cw_db:,.0f} of {cw_pr:,})")

# day-by-day differences on matched days
print("\nLargest per-day differences (DB minus printout), matched beach-days:")
diffs=[]
for r in rows:
    for b in BE[:4]:
        e=r[b][0]
        if e is not None and (b,r['date']) in dbday:
            diffs.append((abs(dbday[(b,r['date'])]-e), b, r['date'], e, dbday[(b,r['date'])]))
diffs.sort(reverse=True)
for d,b,dt,e,x in diffs[:8]:
    print(f"  {b:14s} {dt}  printout {e:>8,.0f}  DB {x:>9,.1f}  diff {x-e:>+8,.1f}  ({(x-e)/e*100:+.1f}%)")
print(f"  matched beach-days: {len(diffs)}; median abs diff {sorted(x[0] for x in diffs)[len(diffs)//2]:.1f}")
