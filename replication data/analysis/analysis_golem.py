#!/usr/bin/env python3
"""Survey statistics, overlaps, concentration, fandoms and weighted log-odds from GOLEM.

Input:  ../golem/runner_results/*.csv, ../golem/adhoc_results/{q0a,q1a,q2a,q2b,q5}.csv
Output: outputs/ (survey_by_year, overlaps_by_year, concentration_2020_22, top_fandoms_2020_22,
        logodds_*_2020_22, cutoff_2022_by_month, key_numbers_golem)
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "golem" / "runner_results"
ADHOC = HERE.parent / "golem" / "adhoc_results"
OUT = HERE / "outputs"; OUT.mkdir(exist_ok=True)
YEARS = range(2008, 2023)
MATCHED = (2020, 2021, 2022)
FAMS = ["femslash", "sapphic", "lesbian", "wlw", "yuri", "baihe"]
ANON = "A000000000"   # GOLEM placeholder ID for anonymous/orphaned works (excluded from concentration)


def one(path):  # single-value CSV
    return pd.read_csv(path).iloc[0, 0]


# ── 1. Survey per year (Figs. 1–4) ─────────────────────────────────────────────
ff = pd.read_csv(ADHOC / "q1a.csv").set_index("year").ff          # F/F works per year (q1a)
rows = []
for y in YEARS:
    total = sum(one(RUN / f"T1_total_{y}_{m:02d}.csv") for m in range(1, 13))
    fam = pd.read_csv(RUN / f"T2_families_{y}.csv").set_index("fam").works.to_dict()
    anyl = one(RUN / f"T2_any_{y}.csv")
    r = {"year": y, "all_works": total, "ff_works": int(ff[y]),
         "ff_share_pct": ff[y] / total * 100, "any_label": anyl, "any_label_pct_of_ff": anyl / ff[y] * 100}
    for k in FAMS:
        r[k] = fam.get(k, 0)
        r[f"{k}_pct_of_ff"] = fam.get(k, 0) / ff[y] * 100
    rows.append(r)
survey = pd.DataFrame(rows)
survey.to_csv(OUT / "survey_by_year.csv", index=False)

months_2022 = [one(RUN / f"T1_total_2022_{m:02d}.csv") for m in range(1, 13)]
pd.DataFrame({"month": range(1, 13), "all_works": months_2022}).to_csv(OUT / "cutoff_2022_by_month.csv", index=False)

# ── 2. Overlaps (Fig. 8) ────────────────────────────────────────────────
ov = []
for y in YEARS:
    ov.append({"year": y, "femslash_x_sapphic": one(RUN / f"T6_femslash_x_sapphic_{y}.csv"),
               "sapphic_x_sappho_tag": one(RUN / f"T6_sapphic_x_sappho_{y}.csv"),
               "femslash_x_lesbian": one(RUN / f"T6_femslash_x_lesbian_{y}.csv") if y in MATCHED else np.nan,
               "sapphic_x_lesbian": one(RUN / f"T6_sapphic_x_lesbian_{y}.csv") if y in MATCHED else np.nan})
ov = pd.DataFrame(ov).merge(survey[["year", "femslash", "sapphic"]], on="year")
ov.to_csv(OUT / "overlaps_by_year.csv", index=False)

# ── 3. Author and fandom concentration, top fandoms (Fig. 9) ───────────────────
conc, topf = [], []
for f in ("femslash", "sapphic", "lesbian", "wlw"):
    for y in MATCHED:
        a = pd.read_csv(RUN / f"T4_nauthors_{f}_{y}.csv"); fa = pd.read_csv(RUN / f"T4_nfandoms_{f}_{y}.csv")
        t = pd.read_csv(RUN / f"T4_topauthors_{f}_{y}.csv"); t = t[t.x != ANON]
        works = a.iloc[0, 0]
        conc.append({"family": f, "year": y, "works": works, "distinct_authors": a.iloc[0, 1],
                     "distinct_fandoms": fa.iloc[0, 1], "top1_author_works": int(t.n.iloc[0]),
                     "top10_authors_share_pct": t.n.head(10).sum() / works * 100})
    s = pd.concat([pd.read_csv(RUN / f"T4_topfandoms_{f}_{y}.csv") for y in MATCHED]).groupby("x").n.sum()
    w = survey.set_index("year").loc[list(MATCHED), f].sum()
    for fandom, n in s.sort_index().sort_values(ascending=False, kind="stable").head(40).items():   # ties: alphabetical
        topf.append({"family": f, "fandom": fandom, "works_2020_22": int(n), "pct_of_family": n / w * 100})
pd.DataFrame(conc).to_csv(OUT / "concentration_2020_22.csv", index=False)
pd.DataFrame(topf).to_csv(OUT / "top_fandoms_2020_22.csv", index=False)

# ── 4. Weighted log-odds with informative Dirichlet prior (Monroe et al. 2008) ─
FAM_RX = {"femslash": "femslash", "sapphic": "sapphic", "lesbian": "lesbian",
          "wlw": r"(^|[^a-z])wlw([^a-z]|$)|women loving women"}


def cotags(f):
    return pd.concat([pd.read_csv(RUN / f"T3_cotags_{f}_{y}.csv") for y in MATCHED]).groupby("co").n.sum()


def logodds(a, b, a0=100.0):
    """Weighted log-odds with informative Dirichlet prior (Monroe, Colaresi & Quinn 2008, eq. 22),
    applied at the WORK level: y = number of works carrying a co-tag, n = number of works in the
    family (2020–2022). Normalising by works rather than by tag tokens avoids an artefact when one
    family carries more tags per work. Prior: pooled share of works carrying the tag, scaled to a0
    pseudo-works. Tags that define either family are removed (tautological)."""
    A, B = cotags(a), cotags(b)
    excl = f"{FAM_RX[a]}|{FAM_RX[b]}"
    idx = [t for t in A.index.union(B.index) if not re.search(excl, t.lower())]
    A = A.reindex(idx, fill_value=0).astype(float); B = B.reindex(idx, fill_value=0).astype(float)
    S_ = survey.set_index("year")
    wa = S_.loc[list(MATCHED), a].sum(); wb = S_.loc[list(MATCHED), b].sum()
    alpha = (A + B) / (wa + wb) * a0
    delta = np.log((A + alpha) / (wa + a0 - A - alpha)) - np.log((B + alpha) / (wb + a0 - B - alpha))
    z = delta / np.sqrt(1 / (A + alpha) + 1 / (B + alpha))
    return pd.DataFrame({"tag": idx, "z": z.values, f"pct_{a}": (A / wa * 100).values,
                         f"pct_{b}": (B / wb * 100).values}).sort_values(["z", "tag"], ascending=[False, True]), wa, wb


lo, na, nb = logodds("sapphic", "femslash")
lo.to_csv(OUT / "logodds_sapphic_vs_femslash_2020_22.csv", index=False)
lo2, _, _ = logodds("lesbian", "femslash")
lo2.to_csv(OUT / "logodds_lesbian_vs_femslash_2020_22.csv", index=False)

# ── 5. Key numbers quoted in the paper ─────────────────────────────────────────
q0a = pd.read_csv(ADHOC / "q0a.csv").set_index("cat").n
q5 = pd.read_csv(ADHOC / "q5.csv").set_index("cat").works
q2a = pd.read_csv(ADHOC / "q2a.csv").set_index("kw").n   # label-type tags in F/F works of 2021 (works per tag)
lesbian_sex_2021 = q2a["Lesbian Sex"]   # upper bound: works carrying "Lesbian Sex"
fem = q2a[q2a.index.str.contains("femslash", case=False)]
fem_event = fem[fem.index.str.contains(r"february|week|fortnight|friday|month|day|challenge|exchange|fest|bingo|community:",
                                       case=False, regex=True)]   # event and community tags (e.g. "Femslash February")
q2b = pd.read_csv(ADHOC / "q2b.csv")   # fixed list of ten 'sapphic' tags
S = survey.set_index("year")
key = {
    "golem_works_2008_2022_sum_of_monthly_counts": int(survey.all_works.sum()),
    "golem_last_month_with_works": "2022-09 (Oct–Dec = 0; Sep partial: %d works)" % months_2022[8],
    "ff_share_2008_pct": S.ff_share_pct[2008], "ff_share_2015_pct": S.ff_share_pct[2015], "ff_share_2022_pct": S.ff_share_pct[2022],
    "any_label_2010_pct_of_ff": S.any_label_pct_of_ff[2010], "femslash_2010_pct_of_ff": S.femslash_pct_of_ff[2010],
    "any_label_min_max_2012_2019_pct": f"{S.any_label_pct_of_ff.loc[2012:2019].min():.2f}–{S.any_label_pct_of_ff.loc[2012:2019].max():.2f}",
    "any_label_2022_pct_of_ff": S.any_label_pct_of_ff[2022], "lesbian_2022_pct_of_ff": S.lesbian_pct_of_ff[2022],
    "femslash_2022_pct_of_ff": S.femslash_pct_of_ff[2022],
    "first_year_lesbian_gt_femslash": int(S.index[(S.lesbian > S.femslash)].min()),
    "max_wlw_pct": S.wlw_pct_of_ff.max(), "max_sapphic_pct": S.sapphic_pct_of_ff.max(), "max_yuri_pct": S.yuri_pct_of_ff.max(),
    "max_baihe_pct": S.baihe_pct_of_ff.max(),
    "sapphic_works_2020_22": int(na), "femslash_works_2020_22": int(nb),
    "femslash_x_sapphic_total_2008_22": int(ov.femslash_x_sapphic.sum()),
    "sapphic_total_2008_22": int(survey.sapphic.sum()), "sapphic_x_sappho_tag_total": int(ov.sapphic_x_sappho_tag.sum()),
    "sapphic_x_lesbian_2022_pct": ov.set_index("year").sapphic_x_lesbian[2022] / S.sapphic[2022] * 100,
    "femslash_x_lesbian_2022_pct": ov.set_index("year").femslash_x_lesbian[2022] / S.femslash[2022] * 100,
    "max_top10_author_share_pct": pd.DataFrame(conc).top10_authors_share_pct.max(),
    "ff_share_all_golem_pct (Q0a/8,007,442)": q0a["F/F"] / 8007442 * 100,
    "original_work_share_of_ff_pct (Q5/Q0a)": q5["F/F"] / q0a["F/F"] * 100,
    "original_work_share_of_mm_pct (Q5/Q0a)": q5["M/M"] / q0a["M/M"] * 100,
    "lesbian_works_2021": int(S.lesbian[2021]),
    "lesbian_sex_works_2021 (q2a)": int(lesbian_sex_2021),
    "lesbian_2021_min_pct_with_other_lesbian_tag": (S.lesbian[2021] - lesbian_sex_2021) / S.lesbian[2021] * 100,
    "sapphic_fixed_list_ff_works (q2b, ten tags)": int(q2b.labelled_and_FF.sum()),
    "femslash_event_tag_use_share_2021_pct (q2a)": fem_event.sum() / fem.sum() * 100,
    "sappho_tagged_works_golem_2005_2022 (T5)": int(pd.read_csv(RUN / "T5_sappho_by_year.csv").works.sum()),
}
tf = pd.DataFrame(topf)
for f in ("femslash", "sapphic", "lesbian", "wlw"):
    key[f"original_work_pct_{f}_2020_22"] = tf[(tf.family == f) & (tf.fandom == "Original Work")].pct_of_family.iloc[0]
pd.Series(key, name="value").to_csv(OUT / "key_numbers_golem.csv")
print(pd.Series(key).to_string())
