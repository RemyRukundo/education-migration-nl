# ============================================================
# Project: Education & Migration Background in the Netherlands
# Data:    CBS StatLine table 80122NED (exam candidates and graduates,
#          secondary education, 2005/06 to 2020/21)
# Author:  Remy Rukundo
# Tool:    Python (pandas, scipy)
#
# Run from the repository root:  python python/01_analysis.py
# Input:   data/exam_results_clean.csv  (432 rows)
# Output:  outputs/*.csv  (result tables, used for the Tableau dashboard)
#
# Notes on the data
#  * 'All candidates (total)' is the total of ALL candidates, including
#    Dutch background. It is left out so nobody is counted twice.
#  * 'Unknown' has very few candidates and is left out of comparisons.
#  * 2020/21 figures are provisional (CBS).
#  * The data describe exam candidates, not all pupils, and show
#    differences between groups, not causes.
# ============================================================

import os
import pandas as pd
from scipy import stats

os.makedirs("outputs", exist_ok=True)

# ------------------------------------------------------------
# Setup: load the data and run checks
# ------------------------------------------------------------
df = pd.read_csv("data/exam_results_clean.csv")

assert df.shape == (432, 6), df.shape
assert df.isna().sum().sum() == 0
assert (df["graduates"] <= df["candidates"]).all()

# Keep only the real groups
df = df[~df.background.isin(["All candidates (total)", "Unknown"])]
print("Rows used in the analysis:", len(df))   # expected: 336


# ------------------------------------------------------------
# Question 1: How many percentage points per year did the
#             VWO + HAVO share rise for each group?
# ------------------------------------------------------------
share = df.pivot_table(index=["background", "school_year"], columns="school_type",
                       values="candidates", aggfunc="sum")
share["vwo_havo_pct"] = 100 * (share["VWO"] + share["HAVO"]) / (share["VWO"] + share["HAVO"] + share["VMBO"])
share = share.reset_index()
share["year_number"] = share["school_year"].str[:4].astype(int)

rows = []
for group, d in share.groupby("background"):
    fit = stats.linregress(d["year_number"], d["vwo_havo_pct"])
    rows.append({"background": group,
                 "points_per_year": round(fit.slope, 2),
                 "r_squared": round(fit.rvalue ** 2, 2),
                 "p_value": round(fit.pvalue, 4)})

q1 = pd.DataFrame(rows).sort_values("points_per_year", ascending=False)
q1.to_csv("outputs/q1_trend_by_group.csv", index=False)
print("\nQuestion 1: trend per group\n", q1.to_string(index=False))


# ------------------------------------------------------------
# Question 2: How big was the gap with Dutch background in the
#             VWO + HAVO share each year, and did it narrow?
# ------------------------------------------------------------
wide = share.pivot(index="school_year", columns="background", values="vwo_havo_pct")
gap = wide.drop(columns="Dutch background").sub(wide["Dutch background"], axis=0).round(1)

q2 = pd.DataFrame({"gap_2005_06": gap.loc["2005/06"],
                   "gap_2020_21": gap.loc["2020/21"]})
q2["change"] = (q2["gap_2020_21"] - q2["gap_2005_06"]).round(1)
q2["widest_gap_year"] = gap.abs().idxmax()
q2["widest_gap"] = gap.abs().max()

gap.to_csv("outputs/q2_gap_by_year.csv")
q2 = q2.sort_values("change", ascending=False)
q2.to_csv("outputs/q2_gap_summary.csv")
print("\nQuestion 2: gap with Dutch background (percentage points)\n", q2)


# ------------------------------------------------------------
# Question 3: Where did the change happen? How did the VWO, HAVO and
#             VMBO share of each group change, 2005/06 to 2020/21?
# ------------------------------------------------------------
q3 = df[df.school_year.isin(["2005/06", "2020/21"])]
q3 = q3.pivot_table(index=["background", "school_year"], columns="school_type",
                    values="candidates", aggfunc="sum")
q3 = q3[["VWO", "HAVO", "VMBO"]]

pct = q3.div(q3.sum(axis=1), axis=0) * 100
pct = pct.unstack("school_year")

q3_change = pd.DataFrame({
    "VWO_change":  (pct[("VWO",  "2020/21")] - pct[("VWO",  "2005/06")]).round(1),
    "HAVO_change": (pct[("HAVO", "2020/21")] - pct[("HAVO", "2005/06")]).round(1),
    "VMBO_change": (pct[("VMBO", "2020/21")] - pct[("VMBO", "2005/06")]).round(1),
    "VMBO_2005_06": pct[("VMBO", "2005/06")].round(1),
    "VMBO_2020_21": pct[("VMBO", "2020/21")].round(1)})

q3_change = q3_change.sort_values("VMBO_change")
q3_change.to_csv("outputs/q3_school_type_shift.csv")
print("\nQuestion 3: change in school-type share (percentage points)\n", q3_change)


# ------------------------------------------------------------
# Question 4: Do groups pass at similar rates within the same school
#             type, and what happened in 2019/20 and 2020/21?
# ------------------------------------------------------------
q4_data = df.copy()
q4_data["period"] = q4_data["school_year"].map(
    lambda year: "pandemic" if year in ("2019/20", "2020/21") else "normal")

g = q4_data.groupby(["school_type", "background", "period"])[["candidates", "graduates"]].sum()
g["pass_rate"] = (100 * g["graduates"] / g["candidates"]).round(1)
q4 = g["pass_rate"].unstack("period")
q4["pandemic_boost"] = (q4["pandemic"] - q4["normal"]).round(1)

normal = q4["normal"].unstack("school_type")
q4_gap = normal.sub(normal.loc["Dutch background"], axis=1).round(1)

q4.to_csv("outputs/q4_pass_rates.csv")
q4_gap.to_csv("outputs/q4_pass_rate_gap.csv")
print("\nQuestion 4: pass rate (%) by school type, group and period\n", q4)
print("\nPass rate gap with Dutch background, normal years (points)\n", q4_gap)


# ------------------------------------------------------------
# Question 5: How over- or under-represented is each group in VWO,
#             HAVO and VMBO, compared with its share of all candidates?
# ------------------------------------------------------------
results = {}
for year in ["2005/06", "2020/21"]:
    d = df[df.school_year == year]

    share_of_all = d.groupby("background")["candidates"].sum()
    share_of_all = share_of_all / share_of_all.sum()

    for level in ["VWO", "HAVO", "VMBO"]:
        share_in_level = d[d.school_type == level].groupby("background")["candidates"].sum()
        share_in_level = share_in_level / share_in_level.sum()
        results[(level, year)] = (share_in_level / share_of_all).round(2)   # 1.0 = proportional

q5 = pd.DataFrame(results)
q5.to_csv("outputs/q5_representation_index.csv")
print("\nQuestion 5: representation index (1.0 = proportional)\n", q5)

print("\nDone. Result tables saved in the outputs folder.")
