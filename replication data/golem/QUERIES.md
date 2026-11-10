# GOLEM queries

Every SPARQL query of the study: what it counts, why it was needed, how it was built, and where its result is
used. The queries were run against the public GOLEM endpoint (`http://graph.golemlab.eu:8890/sparql`;
Pannach et al. 2024) on 5 November 2026. Each query is stored as a `.rq` file and each result as a `.csv` file of
the same name.

## Rationale

GOLEM represents the metadata of over eight million AO3 works (up to September 2022) as an RDF graph. A work is a
node; its properties include `golem:romanticCategory` (F/F, M/M, F/M, Gen, Multi, Other), `golem:keyword` (freeform
tags), `golem:fandom`, `golem:characters`, `golem:datePublished` (string "YYYY-MM-DD") and `golem:author`
(anonymised IDs). The graph contains no texts. Querying it directly has three advantages:

1. **Coverage.** Every F/F work on AO3 up to 2022 is included, not a sample.
2. **Aggregation on the server.** Queries return counts, not records. No personal data leave the server apart from
   anonymised author IDs (task T4).
3. **Repeatability.** Each number in the paper corresponds to a query that can be rerun or adapted to other labels.

## Design

The public endpoint (OpenLink Virtuoso) stops queries after a time limit and may then return partial counts
("anytime" results), flagged in the HTTP headers `X-SQL-State` and `X-SQL-Message`.

- **Restriction to F/F works.** Pattern searches over the tags of all eight million works timed out. All label
  queries therefore start from `?s golem:romanticCategory "F/F"`, which reduces the search space to about 770,000
  works. Of the works carrying one of ten common 'sapphic' tags, 97% also carry the F/F category (q2b).
- **One query per year (T2–T6) or month (T1).** Smaller queries stay below the time limit. Monthly totals use an exact
  list of dates (`VALUES ?d { "2008-01-01" … }`), so that each query only touches one month.
- **Patterns instead of tag lists.** Users write their own tags, so families are defined by string patterns on the
  lower-cased tag (`COND` in `golem_runner.py`). A nested `IF` assigns each tag to exactly one family (first match
  wins).
- **`COUNT(DISTINCT ?s)`** throughout, so that a work with several matching tags is counted once.
- **Completeness check.** `golem_runner.py` checks every response for the partial-result flag, logs incomplete
  queries in `_problems.txt` and retries them. Two exploratory queries (q1c_fm, q1c_mm) remained incomplete and are
  not used.

## Automated queries (`golem_runner.py`; `runner_queries/`, `runner_results/`)

| Task | Queries | What is counted | Why | Used in |
|---|---|---|---|---|
| T1 | 180 (`T1_total_YYYY_MM`) | all works per month, 2008–2022 | denominator for the F/F share; documents the 2022 cut-off (no works after early September 2022) | Fig. 2; `cutoff_2022_by_month.csv` |
| T2 | 30 (`T2_families_YYYY`, `T2_any_YYYY`) | F/F works per label family and year; F/F works with any label | how labelling changes over time (RQ1) | Figs. 3–4; `survey_by_year.csv` |
| T3 | 12 (`T3_cotags_FAMILY_YYYY`) | all co-tags of each family's works (≥ 3 works), 2020–2022 | which tags distinguish the families (RQ2); input for the weighted log-odds | Figs. 5–6 |
| T4 | 48 (`T4_nauthors_…`, `T4_topauthors_…`, `T4_nfandoms_…`, `T4_topfandoms_…`) | distinct authors and fandoms per family; top 25 authors (anonymised) and top 40 fandoms, 2020–2022 | whether a family is spread across fandoms or concentrated in a few authors or fandoms (RQ2) | Fig. 9; `concentration_2020_22.csv` |
| T5 | 1 (`T5_sappho_by_year`) | works per year carrying one of 260 Sappho tags as freeform, fandom or character tag, and how many are F/F | links the Sappho corpus to GOLEM (RQ3) | Fig. 11 |
| T6 | 36 (`T6_…_x_…_YYYY`) | works carrying tags of two families ('femslash' ∩ 'sapphic', 'femslash' ∩ 'lesbian', 'sapphic' ∩ 'lesbian'); 'sapphic' works with a Sappho tag | whether the families are used by the same works (RQ2), and whether 'sapphic' refers to Sappho (RQ3) | Fig. 8; `overlaps_by_year.csv` |

The 260 Sappho tags (`sappho_tags.txt`) are all tag names containing "Sappho" that occur in the metadata of the AO3
Sappho corpus. That corpus was collected via AO3's tag search for canonical and synonymous tags containing "Sappho",
with seven tags excluded (see README). Three of the excluded tags appear in the list because works collected via other
tags carry them; none of them occurs in GOLEM. The tags are matched exactly.

## Exploratory queries (`adhoc_queries/`, `adhoc_results/`)

Written by hand to explore the graph and to answer single questions. Each `.rq` file starts with a comment stating
its purpose.

| Query | What | Why | Used in |
|---|---|---|---|
| q0a | works per romantic category, all years | overall baseline | Fig. 1 |
| q0b | format of `golem:datePublished` | needed to filter by year (string, not date type) | query design |
| q0c | all predicates of two works | schema check; published only as a redacted list of predicates | query design |
| q0d | categories in a sample of 5,000 works | checks whether works carry several categories | query design |
| q1a | F/F works per year | numerator of the F/F share | Fig. 2 |
| q1b | works with F/F as their only category | checks the effect of multi-category works | not reported |
| q1c_fm, q1c_mm | F/M and M/M works for one year | comparison with F/F; incomplete (timeout) | not used |
| q2a | all label-type freeform tags of F/F works in 2021, with counts | inventory of tag variants; basis of the tag typology and of the 'femslash' event share | Fig. 7; `tag_family_types.py` |
| q2b | works with one of ten common 'sapphic' tags (a list compiled at the start, not the ten most frequent), and how many are F/F | compares a fixed list with patterns; justifies the F/F restriction | Data and Method; superseded by T2 |
| q3a–q3d, q4 | authors, fandoms, ratings and co-tags of 'Sapphic'/'Sapphics' | first exploration | superseded by T3–T4 |
| q5 | works in the fandom 'Original Work' per category | how far each label is used outside media fandom | Fig. 10 |
| q6a, q6c | Sappho tags per year; 'sapphic' works with Sappho tags | first exploration | superseded by T5–T6 |
| q6b | F/F works of 2021 whose summary mentions Sappho | first exploration | not used |

## References

Pannach, F., Yang, X., Visser Solissa, N., Yu, Z., van Cranenburgh, A., van der Ree, M., & Pianzola, F. (2024).
The GOLEM triple store: A graph-based representation of narrative and fiction. In *ESWC 2024 Workshops and Tutorials
Joint Proceedings* (CEUR Workshop Proceedings, Vol. 3749).
