# From Femslash to Lesbian: replication data

Replication data for Laura Untner and Anastasia Glawion, *From Femslash to Lesbian: Marking Female Same-Sex Desire
on AO3, with Sappho as a Case Study* (DH 2027, Glasgow).

The package contains all SPARQL queries against GOLEM with their results, the derived data of the AO3 Sappho corpus,
the analysis scripts with all tag rules and regular expressions, and the scripts that produce Figures 1–16. Every
number reported in the paper is collected in `analysis/outputs/key_numbers_*.csv`.

## Structure

```
golem/
  QUERIES.md               documentation of every query (purpose, design, use)
  golem_runner.py          generates and runs the automated queries (tasks T1–T6)
  sappho_tags.txt          260 Sappho tag names, matched exactly in T5 and T6
  adhoc_queries/           19 exploratory queries (q0a–q6c)
  adhoc_results/           their results
  runner_queries/          307 automated queries
  runner_results/          their results
sappho_ao3/data/
  sappho_works_coded.csv           AO3 work IDs and derived variables (1,837 works)
  sappho_tag_classification.csv    Sappho tag names and their classes
analysis/
  analysis_golem.py        survey, overlaps, concentration, fandoms, weighted log-odds
  tag_family_types.py      typology of the label-family tags (2021)
  analysis_sappho.py       tiers, tag classes and fandoms of the Sappho corpus
  analysis_fulltexts.py    regular-expression search in the full texts of the Sappho corpus
  outputs/                 all derived tables
figure_scripts/
  make_figures.py          Figures 1–16 (PNG, 300 dpi, and SVG)
reproduce.py               runs the pipeline
requirements.txt
```

## Requirements

Python 3.14 with the packages in `requirements.txt` (pandas 3.0.5, numpy 2.5.3, matplotlib 3.11.2).
`golem_runner.py` uses the standard library only.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Reproduction

| Step | Command | Input | Output |
|---|---|---|---|
| GOLEM analysis | `python reproduce.py analysis` | `golem/` | `analysis/outputs/` |
| Figures | `python reproduce.py figures` | `analysis/outputs/`, `golem/` | `../figures/` |
| Sappho metadata | `python reproduce.py sappho` | `sappho_ao3/data/sappho_ao3_metadata_all_works.csv` (not published) | `sappho_ao3/data/`, `analysis/outputs/sappho_*.csv` |
| Sappho full texts | `python reproduce.py fulltexts <dir>` | full texts (not published) | `analysis/outputs/fulltext_*.csv` |
| GOLEM queries | `python reproduce.py queries` | public SPARQL endpoint | `golem/golem_results/` |

`python reproduce.py` runs the first two steps; they need no network access and reproduce all GOLEM-based results and all
figures. The outputs of the two Sappho steps are included, since their inputs cannot be published. With Python 3.14.6
and the pinned packages, all tables in `analysis/outputs/` are reproduced byte-identically. Figures were rendered on
macOS with Hiragino Sans GB as fallback font for CJK labels; renderings on other systems differ slightly.

`python reproduce.py queries` writes to `golem/golem_results/` and leaves the published results untouched. The published results
were obtained on 5 November 2026; the public graph may change.

## Data

### GOLEM

GOLEM (Pannach et al. 2024) is an RDF graph of AO3 metadata (`PREFIX golem: <https://golemlab.eu/graph/>`), queried
at `http://graph.golemlab.eu:8890/sparql`. Design and purpose of all queries are documented in `golem/QUERIES.md`.

- The graph contains works dated up to early September 2022 (`cutoff_2022_by_month.csv`).
- The monthly totals for 2008–2022 sum to 8,427,536 works; Pannach et al. (2024) report 8,007,442. The difference
  presumably reflects changes to the public graph after publication.
- Exploratory queries q1c_fm and q1c_mm returned incomplete results and are not used. q2b, q3a–q3d, q4, q6a and q6c are
  superseded by the automated tasks.

### AO3 Sappho corpus

Collected from AO3 between March and May 2026 (latest publication date: 11 May 2026):

1. AO3's tag search was queried for tags whose name contains "Sappho", restricted to canonical and synonymous tags
   (`wrangling_status = canonical_synonymous`).
2. Seven tags were excluded to keep the corpus manageable: "After Sappho", "Its-Sappho-Bitch Bohemian Rhapsody Tumblr
   meme", "beta is a gift from sappho themself", "Sappho (Final Fantasy XIV)", "sappho (ffxiv)",
   "Sappho/Venat (Final Fantasy XIV)" and "Sappho would be worried levels of longing". Tags of this kind list very
   large numbers of works, and some refer to something other than the poet (e.g. a game character in Final Fantasy XIV).
3. All works listed under the remaining tags were collected; works whose AO3 language is not English were skipped.
   Result: 1,837 works.

Each work is assigned to a tier by where Sappho appears in its metadata: tier 1, fandom, character or relationship
tag (122 works); tier 2, only freeform tags, title or summary (616); tier 3, nowhere (1,099). Tier 3 presumably results
from AO3 listing works tagged with synonyms and subordinate tags under a canonical tag; this could not be verified,
as AO3 was unavailable during the analysis. The metadata analysis uses tiers 1–2, the full-text search all tiers.

`golem/sappho_tags.txt` lists the 260 tag names containing "Sappho" in the collected metadata. It includes three of
the excluded tags ("After Sappho", "sappho (ffxiv)", "Sappho would be worried levels of longing"), which occur on works
collected via other tags; none of them occurs in GOLEM.

## Methods

### Label families

Freeform tags (`golem:keyword`) of F/F works (`golem:romanticCategory "F/F"`) are lower-cased and matched as follows
(`COND` in `golem_runner.py`):

| Family | Rule |
|---|---|
| femslash | contains "femslash" |
| sapphic | contains "sapphic" |
| lesbian | contains "lesbian" |
| wlw | token "wlw", or contains "women loving women" |
| yuri | equals "yuri", "yuri - freeform", "shoujo ai", "shoujo-ai", "shojo ai" or "shoujo ai - freeform" |
| baihe | contains "百合" or "baihe" |

Each tag is assigned to the first matching family in this order. A work is counted once for every family in which it
carries at least one tag. Pattern searches are restricted to F/F works because searches across all works exceed the
endpoint's time limit.

In 2021, 377 different tags in F/F works contain "sapphic" (q2a). A fixed list of ten common 'sapphic' tags (q2b;
compiled at the start of the exploration, not the ten most frequent) finds 1,312 F/F works in 2008–2022, the pattern
2,674 (sum of yearly counts, T2). Of the 1,353 works carrying one of the ten tags, 1,312 (97%) carry the F/F category.

The 'lesbian' family includes the content tag "Lesbian Sex". In 2021, at least 73% of 'lesbian' works carry another
'lesbian' tag (12,842 works, of which at most 3,442 carry "Lesbian Sex").

### Tag typology (Figure 7)

`tag_family_types.py` assigns every tag variant in q2a (label-type freeform tags of F/F works in 2021; 4,300 variants)
to a family by the rules above (4,089 variants, 23,358 uses; 211 variants belong to no family) and then to one type.
Rules are checked in order:

1. possible false hit: negation ("not", "non", "anti", "ex") before the label, or the metre ("sapphic stanza", etc.)
2. implied, pre-relationship or background ("pre-", "implied", "subtext", "one-sided", "unrequited", "background")
3. event or community ("february", "week", "challenge", "exchange", "fest", "bingo", "prompt", "community:", a year)
4. sexual content ("sex", "smut", "porn", "pwp", "kink", "explicit", …)
5. generic label (fixed list, e.g. "Lesbian Character", "Useless Lesbians", "Femslash", "wlw")
6. named character (label, optionally after "useless", "disaster", "canon", "soft" or "gay", followed by a
   capitalised name, e.g. "Lesbian Catra (She-Ra)")
7. trope, meme or AU ("au", "harold", "they're lesbians", "vampire", "space", …)
8. other compound

Shares are weighted by tag uses. `tag_variants_typed_2021.csv` lists every variant with its type;
`tag_variants_sample_for_manual_check.csv` contains 200 variants (seed 2027, stratified by family).

### Distinctive co-tags (Figures 5–6)

Weighted log-odds with an informative Dirichlet prior (Monroe, Colaresi & Quinn 2008, eq. 22) at work level:
*y* = works carrying a co-tag, *n* = works in the family (2020–2022 pooled), prior = pooled share of works carrying the
tag, scaled to 100 pseudo-works. Tags that define either family are excluded. GOLEM returns only co-tags used on at
least three works per year.

### Concentration and fandoms (Figure 9)

The author ID `A000000000`, used by GOLEM for anonymous and orphaned works, is excluded. Synonymous fandom tags
(e.g. 原神 / Genshin Impact) are merged by taking the maximum, since the same works carry both (`SYN` in
`make_figures.py`).

### Sappho tag classes (Figure 14)

Sappho tag names are classified by keyword as *reception* (poem, title, quote, fragment, inspired, reference, mention,
verse, ode, hymn, lyric, school) or *label* (proud, friend, yearn, lesbian, gay, sapphos); see
`sappho_tag_classification.csv`. The raw metadata join tags with " | ", which also occurs inside some tag names;
character and relationship counts are therefore approximate.

### Full-text search (Figures 15–16)

`analysis_fulltexts.py` searches the chapter texts (without author notes) of all 1,837 works (14,485,784 words; 13
texts have fewer than 20 words) case-insensitively with the regular expressions in `PATTERNS`
(`fulltext_patterns.csv`):

| Group | Matches |
|---|---|
| mention | Sappho, Sapphô, Psappha, Σαπφώ and other spellings |
| source | "— Sappho" at the start of a line; "Sappho, Fragment 31"; "Fragment 31 … Sappho"; poem titles ("Hymn to Aphrodite"); translators and editions (Anne Carson, If Not, Winter, …) |
| quotation | nine preselected lines in common English translations, e.g. "someone will remember us", "my tongue is broken", "sweetbitter" |
| figure | from the poems: Atthis, Anaktoria, Gongyla, Kleis, Charaxos; from the tradition: Alkaios, Phaon |
| place, myth, epithet, label, greek | Lesbos, Mytilene, Eresos; Aphrodite, Kypris; "tenth Muse"; "sapphic", "lesbian"; Greek script |

A work *cites* Sappho if it matches a source or a quotation pattern. A mention is *in the opening* if it occurs within
the first 600 characters or 2% of the text. Mode of reference, first rule that applies: cites → recurring figure (≥ 10
mentions) → passing mention (1–9) → no mention. The list of lines was compiled in advance and is not exhaustive;
paraphrases, allusions and other translations or languages are not found, so all counts are lower bounds.

### Precision of the full-text patterns

With `--kwic DIR`, `analysis_fulltexts.py` draws 10 random matches per pattern (seed 2027) with 80 characters of
context on either side. 227 matches from the groups mention, source, quotation, figure, place and epithet were coded
manually. Precision per pattern and group is given in `fulltext_kwic_precision.csv`: mention 100%, source 100%,
quotation 96.1%, figure 98.5%, place 95.0%, epithet 80.0%; overall 96.9%. The coded sample contains text excerpts and
is not published; it can be regenerated from the full texts with the same seed.

## Data protection

- GOLEM author IDs are anonymised. Exploratory query q0c returned the raw records of two works; its result is published
  only as a redacted list of predicates.
- The raw Sappho metadata (titles, usernames, summaries, URLs), the full texts and the scraping code are not published.
- `sappho_works_coded.csv` and `fulltext_features_by_work.csv` contain AO3 work IDs, derived variables and counts only.
- Tag names are reproduced as written by AO3 users, since they are the object of analysis.

## References

Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for
identifying the content of political conflict. *Political Analysis*, 16(4), 372–403.

Pannach, F., Yang, X., Visser Solissa, N., Yu, Z., van Cranenburgh, A., van der Ree, M., & Pianzola, F. (2024).
The GOLEM triple store: A graph-based representation of narrative and fiction. In *ESWC 2024 Workshops and Tutorials
Joint Proceedings* (CEUR Workshop Proceedings, Vol. 3749).
