import openpyxl, csv, collections, datetime, json, numpy as np
D=json.load(open("tabdata.json"))

# ---- 2017-18 printout (parsed) ----
pr = {"Longbeach":(94213,823281,16), "Twin Harbors":(55588,619897,18),
      "Copalis":(43987,543238,13), "Mocrocks":(63215,745045,20)}
dbe = {"Longbeach":94213.34,"Twin Harbors":54895.70,"Copalis":44600.60,"Mocrocks":63215.27}
dbd = {"Longbeach":16,"Twin Harbors":17,"Copalis":13,"Mocrocks":20}
dbh = {"Longbeach":843102,"Twin Harbors":611866,"Copalis":547903,"Mocrocks":771322}
wast_pr = {"Longbeach":16466,"Twin Harbors":12398,"Copalis":33952,"Mocrocks":46565}
wast_db = {"Longbeach":0,"Twin Harbors":3691,"Copalis":0,"Mocrocks":9073}
tac_pct = {"Longbeach":"96.2%","Twin Harbors":"124.8%","Copalis":"97.6%","Mocrocks":"101.7%"}
D["recon1718"]=[]
for b in ["Longbeach","Twin Harbors","Copalis","Mocrocks"]:
    e,h,od = pr[b]
    D["recon1718"].append([b, str(od), str(dbd[b]), f"{e:,}", f"{dbe[b]:,.0f}", f"{dbe[b]/e:.3f}",
                           f"{h:,}", f"{dbh[b]:,}", f"{(dbh[b]/h-1)*100:+.1f}%",
                           f"{wast_pr[b]:,}", f"{wast_db[b]:,}", tac_pct[b]])
D["cw1718"]={"pr_eff":257003,"db_eff":256925,"pr_harv":2731461,"db_harv":2774193,
             "pr_wast":109381,"db_wast":12764,"open_bd":67,"db_bd":66}

# ---- coverage (census-backed share) per season/beach ----
wb=openpyxl.load_workbook("repo/02_data/WDFW_RazorClam_HarvestDB_Recompute_and_Reconciliation.xlsx",data_only=True,read_only=True)
cov=[list(r) for r in wb["Coverage_And_Imputation"].iter_rows(values_only=True)][2:]
wb.close()
B4=["Longbeach","Twin Harbors","Copalis","Mocrocks"]
share=collections.defaultdict(dict)
for r in cov:
    if r and r[0] and r[1] in B4 and isinstance(r[4],float): share[r[0]][r[1]]=r[4]
# overrides computed from the repo files
share["2017-18"]={b: dbe[b]/pr[b][0] for b in B4}
share["2022-23"]={"Longbeach":24448/67589,"Twin Harbors":40722/61500,"Copalis":62512/62523,"Mocrocks":45856/45807}
share["2023-24"]={"Longbeach":45457/114614,"Twin Harbors":58457/90082,"Copalis":86088/86088,"Mocrocks":60278/60278}
json.dump({s:share[s] for s in share}, open("coverage_fixed.json","w"), indent=1)

# ---- season effort override for Figure 12 ----
D["printout1718"]={b: pr[b][0] for b in B4}
D["missing2223"]={"db_eff":61959,"open_bd":33,"counted_bd":22,"tab_cw":237419,"tab_harv_wast":3570881,
                  "lb_open":11,"lb_counted":5,"th_open":11,"th_counted":5}
json.dump(D, open("tabdata.json","w"), indent=1)
print("coverage overrides:")
for s in ["2017-18","2022-23","2023-24"]:
    print(" ", s, {b: round(share[s][b],3) for b in B4})
print("\n2017-18 recon rows:")
for r in D["recon1718"]: print(" ", r)
print("\ncoastwide:", D["cw1718"])
