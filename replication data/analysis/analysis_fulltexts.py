#!/usr/bin/env python3
"""Regular-expression search for references to Sappho in the full texts of the Sappho corpus.

Usage:
    python analysis_fulltexts.py TEXT_DIR [--kwic DIR] [--kwic-n 10]

Input:  TEXT_DIR with one plain-text file per work, named <work_id>_<title>.txt (chapter
        texts without author notes; not published), and ../sappho_ao3/data/sappho_works_coded.csv
Output: outputs/fulltext_features_by_work.csv    word count and match count per pattern, per work
        outputs/fulltext_summary_by_tier.csv     shares and medians per tier
        outputs/fulltext_modes_by_tier.csv       mode of reference per tier
        outputs/fulltext_lines_and_figures.csv   works per line and figure pattern
        outputs/fulltext_patterns.csv            all patterns with their group
        outputs/key_numbers_fulltext.csv
        With --kwic, a keyword-in-context sample (--kwic-n random matches per pattern,
        seed 2027) is written to DIR/fulltext_kwic_sample.csv. It contains text excerpts
        and is not part of the published data.

Groups (PATTERNS, case-insensitive):
    mention    her name in several spellings and scripts
    source     attribution lines ("— Sappho"), fragment or poem numbers next to her name,
               poem titles, translators and editions
    quotation  nine preselected lines in common English translations (not exhaustive)
    figure, place, myth, epithet, label, greek   additional counts

Measures per work:
    mentions   number of matches of the mention group
    opening    first mention within the first 600 characters or the first 2% of the text
    source, quotation   at least one match in the group; citation = source or quotation
    mode       citation → recurring figure (≥ 10 mentions) → passing mention (1–9) → no mention
"""
from pathlib import Path
import argparse
import random
import re
import sys
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "sappho_ao3" / "data"
OUT = HERE / "outputs"; OUT.mkdir(exist_ok=True)

TRANSLATORS = (r"anne carson|mary barnard|willis barnstone|diane (j\.? )?rayor|philip freeman|josephine balmer|"
               r"aaron poochigian|guy davenport|stanley lombardo|julia dubnoff|jim powell|m\. ?l\. ?west|"
               r"h\. ?t\. ?wharton|richmond lattimore|sam hamill|paul roche|if not,? winter")

# group, label, regular expression
PATTERNS = [
    ("mention", "Sappho", r"\bsappho'?s?\b|\bsapphô\b|\bsapfo\b|\bsaffo\b|\bpsappha\b|σαπφ|ψάπφ|ψαπφ|サッフォー|萨福|사포"),
    ("source", "attribution line ('— Sappho')", r"(?m)^[ \t]*[-–—~―]+[ \t]*(sappho|sapphô)\b"),
    ("source", "'Sappho, Fragment/Poem N'", r"\bsappho\b[^\n.]{0,15}\b(fragment|frag\.|fr\.|poem|ode|lp|voigt)\s*\d+"),
    ("source", "'Fragment/Poem N … Sappho'", r"\b(fragment|frag\.|fr\.|poem)\s*\d+[^\n]{0,40}\bsappho\b"),
    ("source", "named poem", r"hymn to aphrodite|ode to aphrodite|brothers poem|tithonus poem|ode to anactoria|ode to anaktoria"),
    ("source", "translator or edition", TRANSLATORS),
    ("quotation", "'sweetbitter'", r"sweet[- ]?bitter|glukupikron|γλυκύπικρον"),
    ("quotation", "'loosener of limbs'", r"loosener of limbs|limb[- ]?loosen|loosens? (my|the|her) limbs"),
    ("quotation", "'the moon has set'", r"the moon has set|moon (has|is) set and the pleiades"),
    ("quotation", "'someone will remember us'", r"(will|shall) remember us|in another time.{0,20}remember"),
    ("quotation", "'tongue is broken'", r"tongue (is |breaks|snaps|has )?(broken|break|snapped)|my tongue breaks"),
    ("quotation", "'thin fire under the skin'", r"(thin|subtle|delicate) fire.{0,30}(skin|flesh)|fire races under"),
    ("quotation", "'greener than grass'", r"greener than (the )?grass|paler than grass"),
    ("quotation", "'I cannot weave'", r"i cannot weave|cannot work my loom|cannot do my weaving"),
    ("epithet", "'tenth Muse'", r"tenth muse"),
    ("quotation", "'violet-' epithets", r"violet[- ](haired|tressed|crowned|weaving|robed|lapped)"),
    ("figure", "Atthis", r"\batthis\b"),
    ("figure", "Anaktoria", r"\banak?ctoria\b|\banaktoria\b"),
    ("figure", "Gongyla", r"\bgongyla\b"),
    ("figure", "Kleis", r"\bc?kleis\b|\bcleis\b"),
    ("figure", "Charaxos", r"\bcharax(os|us)\b"),
    ("figure", "Alkaios", r"\balc?kaeus\b|\balkaios\b|\balcaeus\b"),
    ("figure", "Phaon", r"\bphaon\b"),
    ("place", "Lesbos", r"\blesbos\b|\blesvos\b|\blesbian island\b"),
    ("place", "Mytilene, Eresos", r"\bmytilene\b|\bmitilini\b|\beress?os\b"),
    ("myth", "Aphrodite", r"\baphrodite'?s?\b|\bcypris\b|\bkypris\b|\bcytherea\b"),
    ("label", "'sapphic'", r"\bsapphics?\b"),
    ("label", "'lesbian(s)'", r"\blesbians?\b"),
    ("greek", "Greek script (≥ 10 letters)", r"[Ͱ-Ͽἀ-῿][Ͱ-Ͽἀ-῿\s,.;·]{9,}"),
]
COMPILED = [(g, l, re.compile(p, re.IGNORECASE)) for g, l, p in PATTERNS]
NAME = COMPILED[0][2]
CITE_GROUPS = {"source", "quotation"}


def analyse(text):
    row = {"words": len(re.findall(r"\w+", text))}
    for g, l, rx in COMPILED:
        row[l] = sum(1 for _ in rx.finditer(text))
    m = NAME.search(text)
    row["first_mention_rel"] = round(m.start() / max(len(text), 1), 4) if m else None
    row["opening"] = bool(m and (m.start() < 600 or m.start() / max(len(text), 1) < 0.02))
    return row


def mode(r):
    if any(r[l] > 0 for g, l, _ in COMPILED if g in CITE_GROUPS):
        return "quotes or cites her poems"
    if r["Sappho"] >= 10:
        return "recurring figure (character or topic)"
    if r["Sappho"] >= 1:
        return "passing mention"
    return "no mention in the text"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text_dir", type=Path, help="folder with one <work_id>_<title>.txt per work")
    ap.add_argument("--kwic", type=Path, help="output folder for the keyword-in-context sample")
    ap.add_argument("--kwic-n", type=int, default=10, help="matches per pattern in the sample")
    a = ap.parse_args()

    coded = pd.read_csv(DATA / "sappho_works_coded.csv", usecols=["work_id", "tier", "cat_FF", "cat_MM"])
    files = {int(p.name.split("_", 1)[0]): p for p in a.text_dir.glob("*.txt")}
    missing = sorted(set(coded.work_id) - set(files))
    if missing:
        print(f"{len(missing)} works without full text, e.g. {missing[:5]}", file=sys.stderr)

    rows = []
    for wid in sorted(files):
        r = analyse(files[wid].read_text(encoding="utf-8", errors="replace"))
        r["work_id"] = wid
        rows.append(r)
    f = pd.DataFrame(rows).merge(coded, on="work_id", how="inner")
    for grp in ["source", "quotation"]:
        f[grp] = f[[l for g, l, _ in COMPILED if g == grp]].sum(axis=1) > 0
    f["citation"] = f.source | f.quotation
    f["mode"] = f.apply(mode, axis=1)
    f["sappho_per_10k"] = f.Sappho / f.words.clip(lower=1) * 10000
    cols = ["work_id", "tier", "words"] + [l for _, l, _ in COMPILED] + ["first_mention_rel", "opening", "source", "quotation", "citation", "mode"]
    f[cols].sort_values("work_id").to_csv(OUT / "fulltext_features_by_work.csv", index=False)
    pd.DataFrame(PATTERNS, columns=["group", "label", "regex"]).to_csv(OUT / "fulltext_patterns.csv", index=False)

    def summarise(g):
        out = {"works": len(g), "words_total": int(g.words.sum()), "words_median": g.words.median(),
               "pct_any_mention": (g.Sappho > 0).mean() * 100,
               "mentions_median_if_any": g.loc[g.Sappho > 0, "Sappho"].median(),
               "pct_opening_mention": g.opening.mean() * 100,
               "pct_citation": g.citation.mean() * 100,
               "pct_quotation_with_source": (g.quotation & g.source).mean() * 100,
               "pct_quotation_without_source": (g.quotation & ~g.source).mean() * 100,
               "pct_source_without_quotation": (g.source & ~g.quotation).mean() * 100}
        for grp in ["source", "quotation", "figure", "place", "myth", "label", "greek"]:
            labels = [l for gg, l, _ in COMPILED if gg == grp]
            out[f"pct_{grp}"] = (g[labels].sum(axis=1) > 0).mean() * 100
        for l in ["'sapphic'", "'lesbian(s)'", "Lesbos", "Aphrodite"]:
            out[f"pct_{l.strip(chr(39))}"] = (g[l] > 0).mean() * 100
        return pd.Series(out)

    f["tier_all"] = "all"
    summ = pd.concat([f.groupby("tier").apply(summarise, include_groups=False),
                      f.groupby("tier_all").apply(summarise, include_groups=False)])
    summ.round(1).to_csv(OUT / "fulltext_summary_by_tier.csv")
    modes = pd.crosstab(f.tier, f["mode"], margins=True, margins_name="all")
    modes.to_csv(OUT / "fulltext_modes_by_tier.csv")

    line_labels = [l for g, l, _ in COMPILED if g in {"quotation", "figure"}] + ["'Fragment/Poem N … Sappho'", "named poem"]
    lines = (f[line_labels] > 0).sum().sort_values(ascending=False)
    lines.rename("works").to_csv(OUT / "fulltext_lines_and_figures.csv")

    ff = f[f.cat_FF]
    key = {
        "works_with_fulltext": len(f),
        "words_total": int(f.words.sum()),
        "pct_any_sappho_mention_all": (f.Sappho > 0).mean() * 100,
        "pct_any_sappho_mention_tier3": (f[f.tier.str.startswith("3")].Sappho > 0).mean() * 100,
        "pct_citation_all": f.citation.mean() * 100,
        "works_citation": int(f.citation.sum()),
        "works_source": int(f.source.sum()),
        "works_quotation": int(f.quotation.sum()),
        "works_quotation_with_source": int((f.quotation & f.source).sum()),
        "works_quotation_without_source": int((f.quotation & ~f.source).sum()),
        "works_source_without_quotation": int((f.source & ~f.quotation).sum()),
        "works_quotation_without_name": int((f.quotation & (f.Sappho == 0)).sum()),
        "works_citation_without_name": int((f.citation & (f.Sappho == 0)).sum()),
        "works_citation_tier3": int(f.loc[f.tier.str.startswith("3"), "citation"].sum()),
        "pct_opening_if_mentioned": f.loc[f.Sappho > 0, "opening"].mean() * 100,
        "pct_sapphic_word_in_text_FF": (ff["'sapphic'"] > 0).mean() * 100,
        "pct_sapphic_word_and_no_sappho_FF": ((ff["'sapphic'"] > 0) & (ff.Sappho == 0)).mean() * 100,
        "pct_lesbian_word_in_text_FF": (ff["'lesbian(s)'"] > 0).mean() * 100,
    }
    pd.Series(key).round(2).rename("value").to_csv(OUT / "key_numbers_fulltext.csv", index_label="key")
    print(summ.round(1).T.to_string()); print(modes.to_string()); print(lines.to_string())
    print(pd.Series(key).round(2).to_string())

    if a.kwic:
        rnd = random.Random(2027); rows = []
        for g, l, rx in COMPILED:
            hits = []
            for wid in sorted(files):
                t = files[wid].read_text(encoding="utf-8", errors="replace")
                for m in rx.finditer(t):
                    hits.append((wid, t[max(0, m.start() - 80):m.end() + 80].replace("\n", " ")))
            for wid, ctx in rnd.sample(hits, min(a.kwic_n, len(hits))):
                rows.append({"group": g, "label": l, "work_id": wid, "context": ctx, "correct (y/n)": ""})
        Path(a.kwic).mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(Path(a.kwic) / "fulltext_kwic_sample.csv", index=False)


if __name__ == "__main__":
    main()
