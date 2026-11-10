#!/usr/bin/env python3
"""Tiers, tag classes, categories and fandoms of the AO3 Sappho corpus.

Input:  ../sappho_ao3/data/sappho_ao3_metadata_all_works.csv (raw metadata, not published)
Output: ../sappho_ao3/data/sappho_works_coded.csv, ../sappho_ao3/data/sappho_tag_classification.csv,
        outputs/sappho_*.csv, outputs/key_numbers_sappho.csv

The raw file joins AO3 tags with " | ", which also occurs inside some tag names
(e.g. "Geralt z Rivii | Geralt of Rivia/Jaskier"). Character and relationship
counts are therefore approximate; freeform tags are not affected.
"""
from pathlib import Path
import re
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "sappho_ao3" / "data"
OUT = HERE / "outputs"; OUT.mkdir(exist_ok=True)

RAW = DATA / "sappho_ao3_metadata_all_works.csv"
if not RAW.exists():
    raise SystemExit(f"Raw CSV not found: {RAW}\nThe raw metadata file is not part of the published replication data (see README, 'Data ethics').")
df = pd.read_csv(RAW, dtype=str).fillna("")
SAPPHO = re.compile(r"sappho|σαπφ|psappho", re.I)
split = lambda s: [x.strip() for x in s.split("|") if x.strip()]
for c in ["fandoms", "characters", "relationships", "freeforms", "categories"]:
    df[c + "_l"] = df[c].map(split)
for c in ["words", "kudos", "hits"]:
    df[c + "_n"] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
df["year"] = df.published.str[:4].astype(int)

# ── Tiers ──────────────────────────────────────────────────────────────────────
has = lambda l: any(SAPPHO.search(x) for x in l)
df["sappho_in_fandom"] = df.fandoms_l.map(has)
df["sappho_in_character"] = df.characters_l.map(has)
df["sappho_in_relationship"] = df.relationships_l.map(has)
df["sappho_in_freeform"] = df.freeforms_l.map(has)
df["sappho_in_title"] = df.title.str.contains(SAPPHO)
df["sappho_in_summary"] = df.summary.str.contains(SAPPHO)
df["tier"] = "3_no_visible_reference"
df.loc[df.sappho_in_freeform | df.sappho_in_title | df.sappho_in_summary, "tier"] = "2_freeform_title_summary"
df.loc[df.sappho_in_fandom | df.sappho_in_character | df.sappho_in_relationship, "tier"] = "1_fandom_character_relationship"

# ── Tag classes ────────────────────────────────────────────────────────────────
POETRY = r"\bpoe(m|ms|try|tic)\b|\bpoet\b|\bverse\b|\bfragments?\b|\bode\b|\blyric"
RECEPTION = r"poe|title|quot|fragment|inspir|referen|mention|verse|ode|hymn|lyric|school"
LABEL = r"proud|friend|yearn|lesbian|gay|sapphos"
non_s = df.freeforms_l.map(lambda l: [x for x in l if not SAPPHO.search(x)])
s_tags = df.freeforms_l.map(lambda l: [x for x in l if SAPPHO.search(x)])
anyrx = lambda lists, rx: lists.map(lambda l: any(re.search(rx, x, re.I) for x in l))
df["tag_femslash"] = anyrx(df.freeforms_l, r"femslash")
df["tag_sapphic"] = anyrx(df.freeforms_l, r"sapphic")
df["tag_wlw"] = anyrx(df.freeforms_l, r"\bwlw\b|women loving women")
df["tag_lesbian_nonSappho"] = anyrx(non_s, r"lesbian")
df["tag_poetry_nonSappho"] = anyrx(non_s, POETRY)
df["sappho_tag_reception"] = anyrx(s_tags, RECEPTION)
df["sappho_tag_label"] = anyrx(s_tags, LABEL)
cats = ["F/F", "M/M", "F/M", "Gen", "Multi", "Other"]
for c in cats:
    df["cat_" + c.replace("/", "")] = df.categories_l.map(lambda l, c=c: c in l)
df["original_work"] = df.fandoms_l.map(lambda l: "Original Work" in l)
df["antiquity_fandom"] = df.fandoms_l.map(lambda l: any(
    re.search(r"Greek|Roman|Classical|Ancient|Iliad|Odyssey|Homer|Ovid|Mytholog", x, re.I) and not SAPPHO.search(x) for x in l))
df["single_poem_fandom"] = df.fandoms_l.map(lambda l: any(re.search(r"fragment|hymn", x, re.I) and SAPPHO.search(x) for x in l))

# coded file without titles, summaries or author names
keep = ["work_id", "year", "rating", "tier"] + [c for c in df if c.startswith(("sappho_", "tag_", "cat_"))] + \
       ["original_work", "antiquity_fandom", "single_poem_fandom", "words_n", "kudos_n", "hits_n"]
df[keep].to_csv(DATA / "sappho_works_coded.csv", index=False)

tagcls = pd.Series([t for l in s_tags for t in l]).value_counts().rename_axis("tag").reset_index(name="works") \
    .sort_values(["works", "tag"], ascending=[False, True])   # ties: alphabetical
tagcls["class"] = tagcls.tag.map(lambda t: "label" if re.search(LABEL, t, re.I) else ("reception" if re.search(RECEPTION, t, re.I) else "other"))
tagcls.to_csv(DATA / "sappho_tag_classification.csv", index=False)

# ── Numbers for the paper (visible corpus = tiers 1+2) ─────────────────────────
v = df[df.tier != "3_no_visible_reference"].copy()
core = v.tier.str.startswith("1_")
pct = lambda m: m.mean() * 100
key = {
    "n_all": len(df), "n_visible": len(v), "n_tier1_core": int(core.sum()), "n_tier2": int((~core).sum()),
    "n_tier3_invisible": int((df.tier == "3_no_visible_reference").sum()),
    "visible_year_min": int(v.year.min()), "visible_year_max": int(v.year.max()),
    "ff_pct": pct(v.cat_FF), "mm_pct": pct(v.cat_MM),
    "femslash_pct": pct(v.tag_femslash), "sapphic_pct": pct(v.tag_sapphic), "wlw_pct": pct(v.tag_wlw),
    "lesbian_nonSappho_pct": pct(v.tag_lesbian_nonSappho), "poetry_nonSappho_pct": pct(v.tag_poetry_nonSappho),
    "sappho_reception_tag_pct": pct(v.sappho_tag_reception), "sappho_label_tag_pct": pct(v.sappho_tag_label),
    "n_sappho_fandom_tag": int(v.sappho_in_fandom.sum()),
    "n_single_poem_fandom": int(v.single_poem_fandom.sum()),
    "median_kudos_core": v[core].kudos_n.median(), "median_kudos_tier2": v[~core].kudos_n.median(),
    "core_antiquity_or_original_pct": pct((v.antiquity_fandom | v.original_work)[core]),
}
pd.Series(key, name="value").to_csv(OUT / "key_numbers_sappho.csv")

# tables for figures
tc = []
for t, g in v.groupby("tier"):
    for c in cats:
        tc.append({"tier": t, "category": c, "works": int(g["cat_" + c.replace("/", "")].sum()), "n_tier": len(g)})
pd.DataFrame(tc).to_csv(OUT / "sappho_tier_by_category.csv", index=False)
prof = pd.DataFrame({"measure": ["Sappho tags marking reception", "'lesbian' tags", "Poetry tags (not naming Sappho)",
                                 "'sapphic' tags", "Sappho as label for queer desire", "'femslash' tags", "'wlw' tags"],
                     "pct": [key["sappho_reception_tag_pct"], key["lesbian_nonSappho_pct"], key["poetry_nonSappho_pct"],
                             key["sapphic_pct"], key["sappho_label_tag_pct"], key["femslash_pct"], key["wlw_pct"]]})
prof.to_csv(OUT / "sappho_tag_profile.csv", index=False)
fan = v.fandoms_l.explode().value_counts().rename_axis("fandom").reset_index(name="works") \
    .sort_values(["works", "fandom"], ascending=[False, True]).head(15)   # ties: alphabetical
fan.to_csv(OUT / "sappho_top_fandoms.csv", index=False)
rel = v.relationships_l.explode().dropna().value_counts().rename_axis("relationship").reset_index(name="works") \
    .sort_values(["works", "relationship"], ascending=[False, True])   # approximate, see caveat above
rel.head(15).to_csv(OUT / "sappho_top_relationships.csv", index=False)
rel[rel.relationship.str.contains(SAPPHO)].to_csv(OUT / "sappho_relationships_naming_sappho.csv", index=False)
sf_ = v.fandoms_l.explode().dropna()
sf_[sf_.str.contains(SAPPHO)].value_counts().rename_axis("fandom").reset_index(name="works") \
    .sort_values(["works", "fandom"], ascending=[False, True]).to_csv(OUT / "sappho_fandoms_naming_sappho.csv", index=False)
print(pd.Series(key).round(2).to_string())
