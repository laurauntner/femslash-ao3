#!/usr/bin/env python3
"""Figures 1–16 of the paper as PNG (300 dpi) and SVG.

Usage:
    python make_figures.py [OUT_DIR]

Input:  ../analysis/outputs/*.csv, ../golem/adhoc_results/{q0a,q5}.csv,
        ../golem/runner_results/T5_sappho_by_year.csv
Output: OUT_DIR/figNN_*.{png,svg}; OUT_DIR defaults to the folder "figures" next to this package.

The categorical palette is checked for colour-vision deficiency on adjacent pairs; series
are also identified by direct labels or marker shape.
"""
from pathlib import Path
import re
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text

HERE = Path(__file__).resolve().parent
AN = HERE.parent / "analysis" / "outputs"
G = HERE.parent / "golem"
FIG = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "figures"
FIG.mkdir(parents=True, exist_ok=True)

T1, T2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
GREY = "#b4b2ab"
C = {"lesbian": "#2a78d6", "femslash": "#eb6834", "wlw": "#1baf7a", "sapphic": "#eda100",
     "yuri": "#e87ba4", "baihe": "#008300"}
MK = {"lesbian": "o", "femslash": "s", "wlw": "^", "sapphic": "D", "yuri": "v", "baihe": "P"}
SAPPHO1, SAPPHO2 = "#6250d6", "#b3abee"
GOLEM_NOTE = "Data: GOLEM (Pannach et al. 2024), AO3 metadata up to September 2022."
OWN_NOTE = "Data: own AO3 corpus (March–May 2026), English-language works\nwith a visible Sappho reference (n = 738)."
SEX = re.compile(r"sex|cunnilingus|fingering|fingerfucking|nipple|toys|threesome|futanari|smut|bdsm|dom/sub|bondage|"
                 r"edging|masturbat|orgasm|oral|anal |^anal|rimming|scissor|strap|kink|porn|pwp|plot what plot|nsfw|erotica", re.I)
SYN = {"原神": "Genshin Impact (Video Game)", "僕のヒーローアカデミア": "My Hero Academia", "Boku no Hero Academia": "My Hero Academia",
       "Fire Emblem: Fuukasetsugetsu": "Fire Emblem: Three Houses", "Biohazard": "Resident Evil (Gameverse)",
       "魔道祖师 - 墨香铜臭": "Módào Zǔshī - Mòxiāng Tóngxiù", "Good Omens - Neil Gaiman & Terry Pratchett": "Good Omens (TV)",
       "陈情令": "The Untamed (TV)", "ジョジョの奇妙な冒険": "JoJo's Bizarre Adventure", "JoJo no Kimyou na Bouken": "JoJo's Bizarre Adventure"}

SHORT = {"Classical Greece and Rome History & Literature RPF": "Classical Greece & Rome RPF",
         "Percy Jackson and the Olympians & Related Fandoms - All Media Types": "Percy Jackson & Related Fandoms",
         "New Dangan Ronpa V3: Everyone's New Semester of Killing": "New Dangan Ronpa V3",
         "She-Ra and the Princesses of Power (2018)": "She-Ra and the Princesses of Power"}


def short(s, n=36):
    s = SHORT.get(s, s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# Typographic quotation marks for all figure text: 'x' → ‘x’, apostrophes → ’
_OPEN = re.compile(r"(?<![\w%.,;:!?)\]’])'")
_set_text = matplotlib.text.Text.set_text


def _typographic(self, s):
    if isinstance(s, str):
        s = _OPEN.sub("‘", s).replace("'", "’")
    return _set_text(self, s)


matplotlib.text.Text.set_text = _typographic


plt.rcParams.update({"font.family": ["DejaVu Sans", "Hiragino Sans GB"], "font.size": 9, "axes.edgecolor": T2, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white",
                     "svg.fonttype": "none", "svg.hashsalt": "dh2027"})


def save(fig, name):
    for ext in ("png", "svg"):   # no timestamp, fixed SVG ids → byte-identical reruns
        fig.savefig(FIG / f"{name}.{ext}", metadata={"Date": None} if ext == "svg" else None)
    plt.close(fig)


def title(ax, t):
    ax.set_title(t, loc="left", color=T1, fontsize=10)


def note(fig, t, y=-0.04):
    fig.text(0, y, t, color=T2, fontsize=7.4)


def hbar_labels(ax, ys, vals, fmt="{:.1f}%", dx=4):
    for y, v in zip(ys, vals):
        ax.annotate(fmt.format(v), (v, y), xytext=(dx, 0), textcoords="offset points", va="center", fontsize=8, color=T1)


survey = pd.read_csv(AN / "survey_by_year.csv"); yrs = survey.year

# ── Fig 1: romantic categories in GOLEM ───────────────────────────────────────
q0a = pd.read_csv(G / "adhoc_results" / "q0a.csv").sort_values("n")
fig, ax = plt.subplots(figsize=(6.3, 2.6))
ax.barh(q0a.cat, q0a.n / 1e6, color=[C["lesbian"] if c == "F/F" else GREY for c in q0a.cat], height=0.62)
hbar_labels(ax, range(len(q0a)), q0a.n / 1e6, fmt="{:.2f} M")
ax.set_xlabel("works (millions)"); ax.grid(axis="y", visible=False); ax.set_xlim(0, 4.9)
for t in ax.get_yticklabels(): t.set_color(T1)
title(ax, "AO3 works per romantic category in GOLEM")
note(fig, GOLEM_NOTE + " Works can carry several categories.", -0.13)
save(fig, "fig01_categories")

# ── Fig 2: F/F share of all works per year ────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.3, 2.6))
ax.plot(yrs, survey.ff_share_pct, color=C["lesbian"], lw=2, marker="o", ms=4)
for y in (2008, 2015, 2022):
    v = survey.set_index("year").ff_share_pct[y]
    ax.annotate(f"{v:.1f}%", (y, v), xytext=(0, 7), textcoords="offset points", ha="center", color=T1, fontsize=8.5)
ax.set_ylim(0, 12); ax.set_ylabel("% of all works"); ax.set_xticks(range(2008, 2023, 2))
title(ax, "F/F category as share of all AO3 works per year")
note(fig, GOLEM_NOTE + " 2022 = January–September.")
save(fig, "fig02_ff_share")

# ── Fig 3: label families as % of F/F works ───────────────────────────────────
fig, ax = plt.subplots(figsize=(6.3, 3.3))
ax.plot(yrs, survey.any_label_pct_of_ff, color=T2, lw=1.5, ls=(0, (4, 2)))
ax.annotate("any label", (2022, survey.any_label_pct_of_ff.iloc[-1]), xytext=(6, 0), textcoords="offset points",
            va="center", color=T2, fontsize=8.5)
fams5 = ["lesbian", "femslash", "wlw", "sapphic", "yuri"]
for k in fams5:
    ax.plot(yrs, survey[f"{k}_pct_of_ff"], color=C[k], lw=2, marker=MK[k], ms=3.8, markeredgecolor="white", markeredgewidth=0.6)
ly = {"lesbian": survey.lesbian_pct_of_ff.iloc[-1], "femslash": 3.5, "wlw": 2.3, "sapphic": 1.1, "yuri": -0.1}
for k in fams5:
    ax.annotate(f"'{k}'", (2022, survey[f"{k}_pct_of_ff"].iloc[-1]), xytext=(2022.45, ly[k]), textcoords="data",
                va="center", color=T1, fontsize=8.5,
                arrowprops=None if k == "lesbian" else dict(arrowstyle="-", color=C[k], lw=0.8, shrinkA=0, shrinkB=2))
ax.set_xlim(2007.5, 2024.6); ax.set_ylim(-0.6, 19); ax.set_xticks(range(2008, 2023, 2)); ax.set_ylabel("% of F/F works")
title(ax, "Share of F/F works carrying each label family")
note(fig, "Data: GOLEM; families matched by pattern in freeform tags of F/F-category works. 'baihe'/'百合' < 0.05% (not shown).", -0.03)
save(fig, "fig03_label_families_share")

# ── Fig 4: absolute works per family (small multiples, independent scales) ────
fig, axes = plt.subplots(2, 3, figsize=(6.6, 4.0), sharex=True)
for ax, k in zip(axes.flat, ["lesbian", "femslash", "wlw", "sapphic", "yuri", "baihe"]):
    ax.bar(yrs, survey[k], color=C[k], width=0.75)
    ax.set_title(f"'{k}'" if k != "baihe" else "'baihe'/'百合'", loc="left", fontsize=9, color=T1)
    ax.grid(axis="x", visible=False); ax.tick_params(labelsize=7.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    ax.set_xticks([2008, 2015, 2022])
fig.suptitle("F/F works per label family and year (note: separate y-scales)", x=0.01, ha="left", color=T1, fontsize=10)
fig.tight_layout()
note(fig, GOLEM_NOTE + " 2022 = January–September.", -0.02)
save(fig, "fig04_label_families_counts")


# ── Fig 5/6: log-odds ─────────────────────────────────────────────────────────
def logodds_fig(fname, a, b, na, nb, name):
    o = pd.read_csv(AN / fname)
    o = o.sort_values(["z", "tag"], ascending=[True, False])   # ties: deterministic
    s = pd.concat([o.head(12), o.tail(12)])
    fig, ax = plt.subplots(figsize=(6.3, 5.6))
    ax.barh(range(len(s)), s.z, color=[C[a] if z > 0 else C[b] for z in s.z], height=0.72)
    ax.set_yticks(range(len(s))); ax.set_yticklabels(s.tag, fontsize=8.3, color=T1)
    for i, (z, pa, pb) in enumerate(zip(s.z, s[f"pct_{a}"], s[f"pct_{b}"])):
        ax.annotate(f"{pa:.1f}% / {pb:.1f}%", (z, i), xytext=(4 if z > 0 else -4, 0), textcoords="offset points",
                    ha="left" if z > 0 else "right", va="center", fontsize=7.3, color=T2)
    lim = max(abs(s.z.min()), s.z.max())
    ax.axvline(0, color=T2, lw=0.8); ax.set_xlim(s.z.min() - lim * 0.55, s.z.max() + lim * 0.3); ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"weighted log-odds z   (← '{b}'   |   '{a}' →)")
    title(ax, f"Co-tags distinguishing '{a}' (n = {na:,}) from '{b}' (n = {nb:,}), 2020–2022")
    note(fig, f"Labels: % of '{a}' / % of '{b}' works. F/F-category works only; all co-tags shown except those defining either family.\n"
              "Method: weighted log-odds with informative Dirichlet prior (Monroe, Colaresi & Quinn 2008), work-level counts. Data: GOLEM.", -0.02)
    save(fig, name)


S = survey.set_index("year")
n = lambda k: int(S.loc[2020:2022, k].sum())
logodds_fig("logodds_sapphic_vs_femslash_2020_22.csv", "sapphic", "femslash", n("sapphic"), n("femslash"), "fig05_logodds_sapphic_femslash")
logodds_fig("logodds_lesbian_vs_femslash_2020_22.csv", "lesbian", "femslash", n("lesbian"), n("femslash"), "fig06_logodds_lesbian_femslash")

# ── Fig 7: what the tags in each family do (rule-based typology, 2021) ───────
ty = pd.read_csv(AN / "tag_family_types_2021.csv")
TYPES = [("generic label", "generic label", "#52514e"),
         ("identity ascribed to a character", "identity of a named character", C["lesbian"]),
         ("sexual content", "sexual content", "#c2338a"),
         ("event / community", "event or community", C["femslash"]),
         ("trope / meme / AU", "trope, meme or AU", C["sapphic"]),
         ("implied / pre-relationship / background", "implied or pre-relationship", C["wlw"]),
         ("other descriptive compound", "other compound", GREY)]
fams = ["lesbian", "femslash", "sapphic", "wlw"]
tot = ty.groupby("family").tag_uses.sum()
fig, ax = plt.subplots(figsize=(6.6, 2.9))
for i, f in enumerate(fams[::-1]):
    left = 0
    for key, lab, col in TYPES:
        v = ty[(ty.family == f) & (ty.type == key)].pct_of_family_uses.sum()
        if v > 0:
            ax.barh(i, v, left=left, color=col, height=0.62, edgecolor="white", linewidth=1.2, label=lab if i == len(fams) - 1 else None)
            if v >= 7:
                ax.text(left + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5, color="white")
        left += v
ax.set_yticks(range(len(fams))); ax.set_yticklabels([f"'{f}' ({tot[f]:,} uses)" for f in fams[::-1]], color=T1, fontsize=8.5)
ax.set_xlim(0, 100); ax.set_xlabel("% of the family's tag uses"); ax.grid(visible=False)
h, l = ax.get_legend_handles_labels()
ax.legend(h, l, frameon=False, fontsize=7.4, ncol=4, loc="upper left", bbox_to_anchor=(0, -0.22), handlelength=1, columnspacing=1)
title(ax, "What the label tags say, 2021: types of tag within each family")
note(fig, "Data: GOLEM (q2a), freeform tags of F/F-category works in 2021, weighted by number of works per tag. Types assigned by\n"
          "keyword rules (analysis/tag_family_types.py); 'yuri' (one tag) and 'baihe' (42 uses) not shown. Possible false hits < 0.1%.", -0.34)
save(fig, "fig07_tag_types")

# ── Fig 8: overlaps ───────────────────────────────────────────────────────────
ov = pd.read_csv(AN / "overlaps_by_year.csv").set_index("year")
rows = [("'sapphic' works also tagged 'lesbian' (2022)", ov.sapphic_x_lesbian[2022] / ov.sapphic[2022] * 100, C["sapphic"]),
        ("'femslash' works also tagged 'lesbian' (2022)", ov.femslash_x_lesbian[2022] / ov.femslash[2022] * 100, C["femslash"]),
        ("'sapphic' works also tagged 'femslash' (2008–2022)", ov.femslash_x_sapphic.sum() / ov.sapphic.sum() * 100, C["sapphic"]),
        ("'femslash' works also tagged 'sapphic' (2008–2022)", ov.femslash_x_sapphic.sum() / ov.femslash.sum() * 100, C["femslash"])]
fig, ax = plt.subplots(figsize=(6.3, 2.3))
ys = range(len(rows))[::-1]
ax.barh(list(ys), [r[1] for r in rows], color=[r[2] for r in rows], height=0.6)
ax.set_yticks(list(ys)); ax.set_yticklabels([r[0] for r in rows], color=T1, fontsize=8.5)
hbar_labels(ax, ys, [r[1] for r in rows]); ax.set_xlim(0, 40); ax.set_xlabel("% of works"); ax.grid(axis="y", visible=False)
title(ax, "How far the label families overlap")
note(fig, f"Data: GOLEM, F/F-category works. Only {int(ov.femslash_x_sapphic.sum())} works carry both 'femslash' and 'sapphic' tags.", -0.17)
save(fig, "fig08_overlaps")

# ── Fig 9: top fandoms per family (synonymous fandom tags merged) ─────────────
tf = pd.read_csv(AN / "top_fandoms_2020_22.csv")
tf["fandom"] = tf.fandom.replace(SYN)
tf = tf.groupby(["family", "fandom"], as_index=False).pct_of_family.max()   # same works under several names → max, not sum
fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.4))
for ax, k in zip(axes.flat, ["femslash", "lesbian", "wlw", "sapphic"]):
    t = tf[tf.family == k].sort_values(["pct_of_family", "fandom"], ascending=[False, True]).head(8)[::-1]
    ax.barh(t.fandom.map(short), t.pct_of_family, color=C[k], height=0.65)
    for y, v in enumerate(t.pct_of_family):
        ax.annotate(f"{v:.1f}", (v, y), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=T1)
    ax.set_title(f"'{k}' (n = {n(k):,})", loc="left", fontsize=9, color=T1)
    ax.tick_params(axis="y", labelsize=7.2); ax.tick_params(axis="x", labelsize=7); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 10)
fig.suptitle("Top fandoms per label family, 2020–2022 (% of the family's works)", x=0.01, ha="left", color=T1, fontsize=10)
fig.tight_layout()
note(fig, "Data: GOLEM, F/F-category works. Synonymous fandom tags (e.g. 原神 / Genshin Impact) merged.", -0.02)
save(fig, "fig09_top_fandoms")

# ── Fig 10: Original Work share ────────────────────────────────────────────────
q5 = pd.read_csv(G / "adhoc_results" / "q5.csv").set_index("cat").works
q0 = pd.read_csv(G / "adhoc_results" / "q0a.csv").set_index("cat").n
cat_share = (q5 / q0 * 100).sort_values()
ow = tf[tf.fandom == "Original Work"].set_index("family").pct_of_family.sort_values()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.6), sharex=True)
a1.barh(cat_share.index, cat_share.values, color=[C["lesbian"] if c == "F/F" else GREY for c in cat_share.index], height=0.6)
hbar_labels(a1, range(len(cat_share)), cat_share.values); a1.set_title("by romantic category (all years)", loc="left", fontsize=9, color=T1)
a2.barh([f"'{f}'" for f in ow.index], ow.values, color=[C[f] for f in ow.index], height=0.6)
hbar_labels(a2, range(len(ow)), ow.values); a2.set_title("by label family (F/F, 2020–2022)", loc="left", fontsize=9, color=T1)
for a in (a1, a2): a.grid(axis="y", visible=False); a.set_xlim(0, 11); a.set_xlabel("% Original Work")
fig.suptitle("Share of works in the fandom 'Original Work'", x=0.01, ha="left", color=T1, fontsize=10)
fig.tight_layout()
note(fig, GOLEM_NOTE, -0.04)
save(fig, "fig10_original_work")

# ── Fig 12: Sappho corpus, tiers × category ───────────────────────────────────
tc = pd.read_csv(AN / "sappho_tier_by_category.csv")
tc["pct"] = tc.works / tc.n_tier * 100
cats = ["F/F", "M/M", "F/M", "Gen", "Multi", "Other"]
p1 = tc[tc.tier.str.startswith("1_")].set_index("category").pct.reindex(cats)
p2 = tc[tc.tier.str.startswith("2_")].set_index("category").pct.reindex(cats)
n1 = int(tc[tc.tier.str.startswith("1_")].n_tier.iloc[0]); n2 = int(tc[tc.tier.str.startswith("2_")].n_tier.iloc[0])
fig, ax = plt.subplots(figsize=(6.3, 2.8))
x = np.arange(len(cats)); w = 0.38
ax.bar(x - w / 2 - 0.01, p1.values, w, color=SAPPHO1, label=f"Sappho as fandom, character or relationship (n = {n1})")
ax.bar(x + w / 2 + 0.01, p2.values, w, color=SAPPHO2, label=f"Sappho only in tags, title or summary (n = {n2})")
for xi, v in zip(x - w / 2, p1.values): ax.annotate(f"{v:.0f}", (xi, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7, color=T1)
for xi, v in zip(x + w / 2, p2.values): ax.annotate(f"{v:.0f}", (xi, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7, color=T1)
ax.set_xticks(x); ax.set_xticklabels(cats, color=T1); ax.set_ylabel("% of works"); ax.set_ylim(0, 85); ax.grid(axis="x", visible=False)
ax.legend(frameon=False, fontsize=7.8, loc="upper right")
title(ax, "Romantic categories in the Sappho corpus, by type of reference")
note(fig, OWN_NOTE + " Works can carry several categories.", -0.11)
save(fig, "fig12_sappho_categories")

# ── Fig 13: Sappho corpus, top fandoms ────────────────────────────────────────
sf = pd.read_csv(AN / "sappho_top_fandoms.csv")
sf["fandom"] = sf.fandom.replace(SYN); sf = sf.groupby("fandom", as_index=False).works.max().sort_values(["works", "fandom"], ascending=[True, False]).tail(12)
fig, ax = plt.subplots(figsize=(6.3, 3.4))
ax.barh(sf.fandom.map(lambda s: short(s, 40)), sf.works, color=SAPPHO1, height=0.62)
hbar_labels(ax, range(len(sf)), sf.works, fmt="{:.0f}")
ax.grid(axis="y", visible=False); ax.set_xlabel("works")
for t in ax.get_yticklabels(): t.set_color(T1); t.set_fontsize(8.3)
title(ax, "Most frequent fandoms in the Sappho corpus")
note(fig, OWN_NOTE + " Synonymous fandom tags merged.", -0.09)
save(fig, "fig13_sappho_fandoms")

# ── Fig 14: Sappho corpus tag profile ─────────────────────────────────────────
prof = pd.read_csv(AN / "sappho_tag_profile.csv")
fig, ax = plt.subplots(figsize=(6.3, 2.9))
ys = list(range(len(prof)))[::-1]
ax.barh(ys, prof.pct, color=SAPPHO1, height=0.62)
ax.set_yticks(ys); ax.set_yticklabels(prof.measure, color=T1, fontsize=8.5); hbar_labels(ax, ys, prof.pct)
ax.set_xlim(0, 40); ax.set_xlabel("% of works"); ax.grid(axis="y", visible=False)
title(ax, "Freeform tags in AO3 works with a visible Sappho reference")
note(fig, OWN_NOTE, -0.14)
save(fig, "fig14_sappho_tags")

# ── Fig 11: Sappho-tagged works in GOLEM per year ─────────────────────────────
t5 = pd.read_csv(G / "runner_results" / "T5_sappho_by_year.csv").set_index("year").reindex(range(2005, 2023), fill_value=0)
fig, ax = plt.subplots(figsize=(6.3, 2.5))
ax.bar(t5.index, t5.ff_works, color=SAPPHO1, width=0.75, label="F/F")
ax.bar(t5.index, t5.works - t5.ff_works, bottom=t5.ff_works + 0.4, color=SAPPHO2, width=0.75, label="other categories")
ax.set_xticks(range(2005, 2023, 2)); ax.grid(axis="x", visible=False); ax.set_ylabel("works"); ax.legend(frameon=False, fontsize=8)
title(ax, f"GOLEM works with a Sappho tag per year (n = {int(t5.works.sum())})")
note(fig, "Data: GOLEM; exact match on 260 Sappho tags (freeform, fandom, character). 2022 = January–September.")
save(fig, "fig11_sappho_golem")
# ── Fig 15: full texts – how often the texts themselves refer to Sappho ──────
FT_NOTE = ("Data: own AO3 corpus, full texts of all 1,837 works (14.5 million words), counted with regular expressions\n"
           "(analysis/analysis_fulltexts.py). 'Opening' = first 600 characters or 2% of the text. 'Source' = attribution line,\n"
           "fragment or poem number, poem title, or translator; 'line' = one of nine preselected lines in English\n"
           "translation; 'figure' = a figure from the poems (e.g. Atthis) or from the tradition about Sappho (Alkaios, Phaon).")
fs = pd.read_csv(AN / "fulltext_summary_by_tier.csv", index_col=0)
tiers = [("1_fandom_character_relationship", "Sappho as fandom, character\nor relationship", SAPPHO1),
         ("2_freeform_title_summary", "Sappho only in tags,\ntitle or summary", SAPPHO2),
         ("3_no_visible_reference", "no visible reference\nin the metadata", GREY)]
meas = [("pct_any_mention", "names Sappho\nin the text"), ("pct_opening_mention", "names her in\nthe opening"),
        ("pct_source", "refers to a\nsource"), ("pct_quotation", "quotes\na line"),
        ("pct_figure", "names\na figure")]
fig, ax = plt.subplots(figsize=(6.8, 3.0))
x = np.arange(len(meas)); w = 0.26
for j, (t, lab, col) in enumerate(tiers):
    vals = [fs.loc[t, m] for m, _ in meas]
    xs = x + (j - 1) * (w + 0.02)
    ax.bar(xs, vals, w, color=col, label=f"{lab.replace(chr(10), ' ')} (n = {int(fs.loc[t, 'works']):,})")
    for xi, v in zip(xs, vals):
        ax.annotate(f"{v:.0f}", (xi, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7, color=T1)
ax.set_xticks(x); ax.set_xticklabels([m[1] for m in meas], color=T1, fontsize=8.3); ax.set_ylabel("% of works")
ax.set_ylim(0, 88); ax.grid(axis="x", visible=False); ax.legend(frameon=False, fontsize=7.4, loc="upper right")
title(ax, "References to Sappho in the full texts, by type of metadata reference")
note(fig, FT_NOTE, -0.21)
save(fig, "fig15_fulltext_tiers")

# ── Fig 16: full texts – the lines and figures most often taken from the poems ─
ll = pd.read_csv(AN / "fulltext_lines_and_figures.csv", index_col=0).works
FR = {"'someone will remember us'": "'someone will remember us' (fr. 147)", "'tongue is broken'": "'tongue is broken' (fr. 31)",
      "'I cannot weave'": "'I cannot weave' (fr. 102)", "'greener than grass'": "'greener than grass' (fr. 31)",
      "'loosener of limbs'": "'loosener of limbs' (fr. 130)", "'thin fire under the skin'": "'thin fire under the skin' (fr. 31)",
      "'sweetbitter'": "'sweetbitter' (fr. 130)", "'the moon has set'": "'the moon has set' (fr. 168B)",
      "named poem": "poem named ('Hymn to Aphrodite' etc.)", "Kleis": "Kleis/Cleis", "Alkaios": "Alkaios/Alcaeus",
      "Anaktoria": "Anaktoria/Anactoria"}
ll = ll.drop(["named poem", "'Fragment/Poem N … Sappho'"], errors="ignore")   # sources, not lines or figures
ll = ll[ll >= 5].sort_index().sort_values(ascending=True, kind="stable")
is_fig = ll.index.isin(["Atthis", "Anaktoria", "Gongyla", "Kleis", "Charaxos", "Alkaios", "Phaon"])
fig, ax = plt.subplots(figsize=(6.3, 3.6))
ax.barh([FR.get(i, i) for i in ll.index], ll.values, color=[SAPPHO2 if f else SAPPHO1 for f in is_fig], height=0.62)
hbar_labels(ax, range(len(ll)), ll.values, fmt="{:.0f}")
ax.grid(axis="y", visible=False); ax.set_xlabel("works")
for t in ax.get_yticklabels(): t.set_color(T1); t.set_fontsize(8.2)
title(ax, "Lines from Sappho's poems (dark) and figures from the poems and tradition (light)")
note(fig, "Data: own AO3 corpus, full texts of all 1,837 works; patterns in analysis/analysis_fulltexts.py. Fragment numbers\n"
          "after Voigt. Patterns found in fewer than five works not shown.", -0.1)
save(fig, "fig16_fulltext_lines")
print("figures written to", FIG)
