#!/usr/bin/env python3
"""Rule-based typology of the label-family tags in F/F works of 2021 (Fig. 7).

Input:  ../golem/adhoc_results/q2a.csv (label-type freeform tags with the number of works per tag)
Output: outputs/tag_family_types_2021.csv           shares per family and type, weighted by tag uses
        outputs/tag_variants_typed_2021.csv          every tag variant with family and type
        outputs/tag_variants_sample_for_manual_check.csv
                                                     200 variants (seed 2027, stratified by family)

Families follow COND in golem_runner.py. Types are assigned by the keyword rules
below; the first matching rule wins. Counts are tag uses, not works.
"""
from pathlib import Path
import re
import pandas as pd

HERE = Path(__file__).resolve().parent
ADHOC = HERE.parent / "golem" / "adhoc_results"
OUT = HERE / "outputs"; OUT.mkdir(exist_ok=True)

q = pd.read_csv(ADHOC / "q2a.csv")          # columns: kw, n
q["k"] = q.kw.str.lower()

FAMILY = [  # same order and rules as COND in golem_runner.py
    ("femslash", lambda k: "femslash" in k),
    ("sapphic",  lambda k: "sapphic" in k),
    ("lesbian",  lambda k: "lesbian" in k),
    ("wlw",      lambda k: re.search(r"(^|[^a-z])wlw([^a-z]|$)", k) is not None or "women loving women" in k),
    ("yuri",     lambda k: k in {"yuri", "yuri - freeform", "shoujo ai", "shoujo-ai", "shojo ai", "shoujo ai - freeform"}),
    ("baihe",    lambda k: "百合" in k or "baihe" in k),
]
q["family"] = q.k.map(lambda k: next((f for f, test in FAMILY if test(k)), None))
q = q[q.family.notna()].copy()   # q2a also returns tags outside all families, e.g. "Yuri Plisetsky"

NEG = r"(^|\W)(not|no longer|non|anti|ex)[\s-]+(a\s+)?(lesbian|sapphic|wlw|femslash)"
PRE = r"pre[\s-]+(pre[\s-]+)*(femslash|lesbian|sapphic|wlw)|implied|subtext|one[\s-]sided|unrequited|background"
METRE = r"sapphic (verse|stanza|meter|metre|ode)"
EVENT = r"february|week|fortnight|friday|month|\bday\b|challenge|exchange|fest|bingo|community:|september|prompt|event|\d{4}"
SEX = r"\bsex\b|\brape\b|non-?con|dub-?con|smut|porn|pwp|fingering|cunnilingus|oral|scissor|strap|kink|nsfw|explicit|orgasm|tribad"
META = (r"harold|they('|’)?re (still )?lesbians|meme|\bau\b|alternate universe|vampire|werewolf|witch|pirate|mermaid|"
        r"knight|ghost|space|time travel|assassin|demon|angel|alien|zombie|cowgirl|lets go lesbians")
NOT_NAME = (r"(?i:characters?|vampires?|relationships?|culture|couples?|love|romance|pride|sex|au|in|and|of|with|"
            r"pirates?|witch(es)?|knights?|space|mermaids?|werewolf|ghosts?|feelings|yearning|energy|disasters?)\b")
GENERIC = {"lesbian", "lesbians", "lesbian character", "lesbian relationship", "canon lesbian relationship",
           "canon lesbian character", "pov lesbian character", "useless lesbians", "disaster lesbians",
           "lesbian romance", "lesbians in love", "lesbian love", "lesbian couple", "lesbian character of color",
           "lesbian culture", "lesbian pride", "femslash", "sapphic", "sapphics", "wlw", "women loving women",
           "yuri", "百合", "baihe - freeform", "wlw relationship", "sapphic relationship", "no lesbians die"}


def tag_type(row):
    k = row.k
    if re.search(NEG, k):
        return "possible false hit (negation)"
    if re.search(PRE, k):
        return "implied / pre-relationship / background"
    if re.search(METRE, k):
        return "possible false hit (metre)"
    if re.search(EVENT, k):
        return "event / community"
    if re.search(SEX, k):
        return "sexual content"
    if k in GENERIC:
        return "generic label"
    # label followed by a character name, e.g. "Lesbian Catra (She-Ra)"
    if row.family != "femslash" and re.match(
            r"^(?i:(useless |disaster |canon |soft |gay )?(lesbian|sapphic|wlw)( disaster)?) (?!" + NOT_NAME + r")[A-Z]",
            row.kw):
        return "identity ascribed to a character"
    if re.search(META, k):
        return "trope / meme / AU"
    return "other descriptive compound"


q["type"] = q.apply(tag_type, axis=1)
q[["kw", "n", "family", "type"]].sort_values(["family", "n", "kw"], ascending=[True, False, True]) \
    .to_csv(OUT / "tag_variants_typed_2021.csv", index=False)

tab = q.groupby(["family", "type"]).agg(variants=("kw", "size"), tag_uses=("n", "sum")).reset_index()
tab["pct_of_family_uses"] = tab.tag_uses / tab.groupby("family").tag_uses.transform("sum") * 100
tab.sort_values(["family", "tag_uses"], ascending=[True, False]).to_csv(OUT / "tag_family_types_2021.csv", index=False)

parts = []
for fam in sorted(q.family.unique()):
    g = q[q.family == fam]
    parts.append(g.sample(min(len(g), max(10, round(200 * len(g) / len(q)))), random_state=2027))
sample = pd.concat(parts).sample(frac=1, random_state=2027).head(200)
sample["manual_code (correct family? y/n; type)"] = ""
sample[["kw", "n", "family", "type", "manual_code (correct family? y/n; type)"]].to_csv(
    OUT / "tag_variants_sample_for_manual_check.csv", index=False)

print(tab.round(1).to_string(index=False))
