import openpyxl, numpy as np, json, collections
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
plt.rcParams.update({
 "font.family":"DejaVu Sans","font.size":8.5,"axes.titlesize":9.5,"axes.labelsize":8.5,
 "axes.spines.top":False,"axes.spines.right":False,"axes.edgecolor":"#555555","axes.linewidth":0.8,
 "xtick.color":"#333333","ytick.color":"#333333","grid.color":"#DDDDDD","grid.linewidth":0.6,
 "legend.frameon":False,"legend.fontsize":8,"figure.dpi":170,"savefig.dpi":170,
 "savefig.bbox":"tight","savefig.facecolor":"white"})
C={"Longbeach":"#1B4965","Twin Harbors":"#5FA8D3","Copalis":"#C1666B","Mocrocks":"#E0A458"}
ORDER=["Longbeach","Twin Harbors","Copalis","Mocrocks"]
LBL={"Longbeach":"Long Beach","Twin Harbors":"Twin Harbors","Copalis":"Copalis","Mocrocks":"Mocrocks"}
FIG="/home/claude/work/fig/"
pct=FuncFormatter(lambda v,p:f"{v:.0f}%")
cov=json.load(open("coverage_fixed.json"))
D=json.load(open("tabdata.json"))

# ---- Figure 4 : census-backed share, all 19 seasons ----
seasons=sorted(cov)
fig,ax=plt.subplots(figsize=(6.25,3.35))
i0=seasons.index("2019-20")
ax.axvspan(i0-0.5,len(seasons)-0.5,color="#C1666B",alpha=.07,lw=0)
ax.text((i0+len(seasons)-1)/2,26.5,"2019-20 onward",ha="center",fontsize=7.4,color="#8a3b3f")
for b in ORDER:
    xs=[i for i,s in enumerate(seasons) if b in cov[s]]
    ys=[min(cov[seasons[i]][b]*100,104) for i in xs]
    ax.plot(xs,ys,marker="o",ms=3.4,lw=1.6,color=C[b],label=LBL[b])
i17=seasons.index("2017-18"); i22=seasons.index("2022-23")
for i in (i17,i22):
    for b in ORDER:
        if b in cov[seasons[i]]:
            ax.plot([i],[min(cov[seasons[i]][b]*100,104)],marker="o",ms=7,mfc="none",mec="#333",mew=0.9,zorder=5)
ax.annotate("restored from the\nFINAL printout", xy=(i17,99), xytext=(i17-2.9,64),
            fontsize=6.8,color="#333",arrowprops=dict(arrowstyle="->",color="#777",lw=.8))
ax.annotate("May 2023 tide series\nabsent from the workbook", xy=(i22,36.2), xytext=(i22-5.4,31),
            fontsize=6.8,color="#333",arrowprops=dict(arrowstyle="->",color="#777",lw=.8))
ax.axhline(100,color="#bbb",lw=.8,ls="--")
ax.set_ylim(22,112);ax.set_ylabel("Share of the Effort-tab season total\nbacked by an actual census")
ax.yaxis.set_major_formatter(pct)
ax.set_xticks(range(len(seasons)));ax.set_xticklabels(seasons,rotation=60,ha="right",fontsize=7)
ax.grid(axis="y");ax.set_axisbelow(True)
ax.legend(loc="lower center",bbox_to_anchor=(.5,-.36),ncol=4,fontsize=7.6)
fig.savefig(FIG+"fig07.png");plt.close(fig)
print("fig07 seasons:", len(seasons))

# ---- Figure 12 : season effort with 2017-18 restored, 2022-23 flagged ----
wb=openpyxl.load_workbook("repo/02_data/WDFW_RazorClam_Corrected_Estimates_and_Uncertainty.xlsx",data_only=True,read_only=True)
se=[list(r) for r in wb["Season_Estimates"].iter_rows(values_only=True)][2:]
wb.close()
se=[r for r in se if r and r[0]]
pr1718=D["printout1718"]
fig,axs=plt.subplots(2,2,figsize=(6.5,4.6),sharex=True)
for ax,b in zip(axs.ravel(),ORDER):
    d=[r for r in se if r[1]==b]
    ss=[r[0] for r in d]; x=np.arange(len(ss))
    lo=np.array([r[5] for r in d],float)/1000; hi=np.array([r[6] for r in d],float)/1000
    cor=np.array([r[3] for r in d],float)/1000; wbk=np.array([r[2] for r in d],float)/1000
    mask=np.array([s!="2017-18" for s in ss])
    lo2,hi2=lo.copy(),hi.copy(); lo2[~mask]=np.nan; hi2[~mask]=np.nan
    cor2=cor.copy(); wbk2=wbk.copy()
    cor2[~mask]=np.nan; wbk2[~mask]=np.nan
    ax.fill_between(x,lo2,hi2,color=C[b],alpha=.18,lw=0)
    ax.plot(x,cor2,color=C[b],lw=1.6,marker="o",ms=2.6,label="corrected")
    ax.plot(x,wbk2,color="#666",lw=1.0,ls="--",label="workbook")
    if "2017-18" in ss:
        i=ss.index("2017-18")
        ax.plot([i],[pr1718[b]/1000],marker="D",ms=5,mfc="none",mec=C[b],mew=1.4,zorder=6,label="2017-18 printout")
        ax.plot([i],[cor[i]/1000],marker="x",ms=4.5,color="#999",mew=1.1,zorder=6)
    if "2022-23" in ss:
        j=ss.index("2022-23")
        ax.plot([j],[cor[j]/1000],marker="v",ms=6,mfc="none",mec="#8a3b3f",mew=1.2,zorder=6)
    ax.set_title(LBL[b],fontsize=8.8);ax.grid(axis="y");ax.set_axisbelow(True)
    ax.set_xticks(x);ax.set_xticklabels(ss,rotation=70,ha="right",fontsize=6)
    if b=="Longbeach": ax.legend(fontsize=6.2,loc="upper right")
axs[0,0].set_ylabel("thousand digger trips");axs[1,0].set_ylabel("thousand digger trips")
fig.text(0.5,-0.055,"Open diamond: 2017-18 FINAL printout (the season). Grey cross: the mid-season snapshot the workbooks hold. "
                    "Red triangle: 2022-23, which omits the May 2023 tide series.",ha="center",fontsize=6.6,color="#444")
fig.savefig(FIG+"fig10.png");plt.close(fig)
print("fig10 ok")
