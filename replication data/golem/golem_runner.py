#!/usr/bin/env python3
"""Generate, run and store the automated GOLEM queries (tasks T1–T6).

Usage:
    python golem_runner.py [--tasks T1 T2 ...] [--out DIR] [--dry-run]

Each query is written to DIR/queries/<name>.rq and its result to DIR/<name>.csv.
Completed queries are skipped, so interrupted runs can be resumed. Responses that
time out or are flagged as partial by the endpoint (Virtuoso "anytime" results)
are logged in DIR/_problems.txt and retried on the next run.

The published run (5 November 2026) is stored in runner_queries/ and
runner_results/. Requires Python >= 3.9 and no third-party packages.

Tasks:
    T1  all works per month, 2008–2022
    T2  F/F works per label family and per year, 2008–2022; F/F works with any label
    T3  co-tags per label family, 2020–2022
    T4  authors and fandoms per label family, 2020–2022
    T5  works per year carrying a Sappho tag (freeform, fandom or character)
    T6  overlaps per year: femslash ∩ sapphic, sapphic ∩ Sappho tag (2008–2022);
        femslash ∩ lesbian, sapphic ∩ lesbian (2020–2022)
"""

from __future__ import annotations

import argparse
import calendar
import csv
import io
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "http://graph.golemlab.eu:8890/sparql"
PREFIX   = "PREFIX golem: <https://golemlab.eu/graph/>\n"
HERE     = Path(__file__).resolve().parent
PAUSE    = 2.0          # seconds between queries
TIMEOUT  = 600          # seconds per HTTP request
YEARS    = range(2008, 2023)
MATCHED  = ("2020", "2021", "2022")
FAMILIES = ("femslash", "sapphic", "lesbian", "wlw", "yuri", "baihe")

# ── tag families (applied to ?k = lower-case keyword) ─────────────────────────
COND = {
    "femslash": 'CONTAINS(?k, "femslash")',
    "sapphic":  'CONTAINS(?k, "sapphic")',
    "lesbian":  'CONTAINS(?k, "lesbian")',
    "wlw":      'REGEX(?k, "(^|[^a-z])wlw([^a-z]|$)") || CONTAINS(?k, "women loving women")',
    "yuri":     '?k IN ("yuri", "yuri - freeform", "shoujo ai", "shoujo-ai", "shojo ai", "shoujo ai - freeform")',
    "baihe":    'CONTAINS(?k, "百合") || CONTAINS(?k, "baihe")',
}
ANY_COND = " || ".join(f"({c})" for c in COND.values())
FAM_BIND = '""'
for fam in reversed(FAMILIES):                       # nested IF: one family per tag, first match wins
    FAM_BIND = f'IF({COND[fam]}, "{fam}", {FAM_BIND})'


def ff_year(year: str) -> str:
    return (f'  ?s golem:romanticCategory "F/F" ; golem:datePublished ?d .\n'
            f'  FILTER(STRSTARTS(STR(?d), "{year}"))\n')


# ── query builders ─────────────────────────────────────────────────────────────
def q_month_total(y: int, m: int) -> str:
    days = calendar.monthrange(y, m)[1]
    vals = " ".join(f'"{y}-{m:02d}-{d:02d}"' for d in range(1, days + 1))
    return PREFIX + ("SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {\n"
                     f"  VALUES ?d {{ {vals} }}\n  ?s golem:datePublished ?d .\n}}")


def q_families(year: str) -> str:
    return PREFIX + ("SELECT ?fam (COUNT(DISTINCT ?s) AS ?works) WHERE {\n" + ff_year(year) +
                     "  ?s golem:keyword ?kw .\n  BIND(LCASE(STR(?kw)) AS ?k)\n"
                     f"  BIND({FAM_BIND} AS ?fam)\n  FILTER(?fam != \"\")\n}}\nGROUP BY ?fam")


def q_any(year: str) -> str:
    return PREFIX + ("SELECT (COUNT(DISTINCT ?s) AS ?works) WHERE {\n" + ff_year(year) +
                     "  ?s golem:keyword ?kw .\n  BIND(LCASE(STR(?kw)) AS ?k)\n"
                     f"  FILTER({ANY_COND})\n}}")


def _fam_subset(fam: str, year: str) -> str:
    return (ff_year(year) + "  ?s golem:keyword ?kw .\n  BIND(LCASE(STR(?kw)) AS ?k)\n"
            f"  FILTER({COND[fam]})\n")


def q_cotags(fam: str, year: str) -> str:
    return PREFIX + ("SELECT ?co (COUNT(DISTINCT ?s) AS ?n) WHERE {\n" + _fam_subset(fam, year) +
                     "  ?s golem:keyword ?co .\n}\nGROUP BY ?co HAVING (COUNT(DISTINCT ?s) >= 3)\n"
                     "ORDER BY DESC(?n)")


def q_count_distinct(fam: str, year: str, pred: str) -> str:
    return PREFIX + (f"SELECT (COUNT(DISTINCT ?s) AS ?works) (COUNT(DISTINCT ?x) AS ?distinct_{pred}) WHERE {{\n"
                     + _fam_subset(fam, year) + f"  OPTIONAL {{ ?s golem:{pred} ?x }}\n}}")


def q_top(fam: str, year: str, pred: str, n: int) -> str:
    return PREFIX + ("SELECT ?x (COUNT(DISTINCT ?s) AS ?n) WHERE {\n" + _fam_subset(fam, year) +
                     f"  ?s golem:{pred} ?x .\n}}\nGROUP BY ?x ORDER BY DESC(?n) LIMIT {n}")


SAPPHO_TAGS_FILE = HERE / "sappho_tags.txt"


def q_sappho() -> str:
    tags = [t for t in SAPPHO_TAGS_FILE.read_text(encoding="utf-8").splitlines() if t.strip()]
    vals = "\n    ".join('"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"' for t in tags)
    return PREFIX + ("SELECT ?year (COUNT(DISTINCT ?s) AS ?works) (COUNT(DISTINCT ?ff) AS ?ff_works) WHERE {\n"
                     f"  VALUES ?t {{\n    {vals}\n  }}\n"
                     "  { ?s golem:keyword ?t } UNION { ?s golem:fandom ?t } UNION { ?s golem:characters ?t }\n"
                     "  ?s golem:datePublished ?d .\n  BIND(SUBSTR(STR(?d), 1, 4) AS ?year)\n"
                     '  OPTIONAL { ?s golem:romanticCategory "F/F" . BIND(?s AS ?ff) }\n'
                     "}\nGROUP BY ?year ORDER BY ?year")


def _sappho_values() -> str:
    tags = [t for t in SAPPHO_TAGS_FILE.read_text(encoding="utf-8").splitlines() if t.strip()]
    return "\n    ".join('"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"' for t in tags)


def q_overlap(fam_a: str, fam_b: str, year: str) -> str:
    return PREFIX + ("SELECT (COUNT(DISTINCT ?s) AS ?works) WHERE {\n" + ff_year(year) +
                     "  ?s golem:keyword ?kw1 .\n  BIND(LCASE(STR(?kw1)) AS ?k)\n"
                     f"  FILTER({COND[fam_a]})\n"
                     "  ?s golem:keyword ?kw2 .\n  BIND(LCASE(STR(?kw2)) AS ?k2)\n"
                     f"  FILTER({COND[fam_b].replace('?k', '?k2')})\n}}")


def q_sapphic_sappho(year: str) -> str:
    return PREFIX + ("SELECT (COUNT(DISTINCT ?s) AS ?works) WHERE {\n" + ff_year(year) +
                     "  ?s golem:keyword ?kw .\n  BIND(LCASE(STR(?kw)) AS ?k)\n"
                     f"  FILTER({COND['sapphic']})\n"
                     f"  VALUES ?t {{\n    {_sappho_values()}\n  }}\n"
                     "  { ?s golem:keyword ?t } UNION { ?s golem:fandom ?t } UNION { ?s golem:characters ?t }\n}")


def build_jobs() -> dict[str, list[tuple[str, str]]]:
    jobs: dict[str, list[tuple[str, str]]] = {k: [] for k in ("T1", "T2", "T3", "T4", "T5", "T6")}
    for y in YEARS:
        for m in range(1, 13):
            jobs["T1"].append((f"T1_total_{y}_{m:02d}", q_month_total(y, m)))
    for y in YEARS:
        jobs["T2"].append((f"T2_families_{y}", q_families(str(y))))
        jobs["T2"].append((f"T2_any_{y}", q_any(str(y))))
    for fam in ("femslash", "sapphic", "lesbian", "wlw"):
        for y in MATCHED:
            jobs["T3"].append((f"T3_cotags_{fam}_{y}", q_cotags(fam, y)))
            jobs["T4"].append((f"T4_nauthors_{fam}_{y}", q_count_distinct(fam, y, "author")))
            jobs["T4"].append((f"T4_topauthors_{fam}_{y}", q_top(fam, y, "author", 25)))
            jobs["T4"].append((f"T4_nfandoms_{fam}_{y}", q_count_distinct(fam, y, "fandom")))
            jobs["T4"].append((f"T4_topfandoms_{fam}_{y}", q_top(fam, y, "fandom", 40)))
    if SAPPHO_TAGS_FILE.exists():
        jobs["T5"].append(("T5_sappho_by_year", q_sappho()))
    for y in YEARS:
        jobs["T6"].append((f"T6_femslash_x_sapphic_{y}", q_overlap("femslash", "sapphic", str(y))))
        if SAPPHO_TAGS_FILE.exists():
            jobs["T6"].append((f"T6_sapphic_x_sappho_{y}", q_sapphic_sappho(str(y))))
    for y in MATCHED:
        jobs["T6"].append((f"T6_femslash_x_lesbian_{y}", q_overlap("femslash", "lesbian", y)))
        jobs["T6"].append((f"T6_sapphic_x_lesbian_{y}", q_overlap("sapphic", "lesbian", y)))
    return jobs


# ── query file headers (see QUERIES.md) ───────────────────────────────────────
TASK_DOC = {
    "T1_total":   ("all works published in this month", "denominator of the F/F share; documents the 2022 cut-off", "Fig. 2"),
    "T2_families": ("F/F works per label family in this year (each tag assigned to one family)", "change in labelling over time (RQ1)", "Figs. 3-4"),
    "T2_any":     ("F/F works with a tag of any label family in this year", "share of F/F works with any label (RQ1)", "Fig. 3"),
    "T3_cotags":  ("co-tags (>= 3 works) of this family's F/F works in this year", "tags that distinguish the families (RQ2); input for weighted log-odds", "Figs. 5-6"),
    "T4_nauthors": ("works and distinct (anonymised) authors of this family in this year", "concentration of a family in few authors (RQ2)", "concentration_2020_22.csv"),
    "T4_topauthors": ("top 25 (anonymised) authors of this family in this year", "concentration of a family in few authors (RQ2)", "concentration_2020_22.csv"),
    "T4_nfandoms": ("works and distinct fandoms of this family in this year", "spread of a family across fandoms (RQ2)", "concentration_2020_22.csv"),
    "T4_topfandoms": ("top 40 fandoms of this family in this year", "which fandoms use the family (RQ2)", "Fig. 9"),
    "T5_sappho":  ("works per year with one of 260 Sappho tags (freeform, fandom or character), and how many are F/F", "links the Sappho corpus to GOLEM (RQ3)", "Fig. 11"),
    "T6_sapphic_x_sappho": ("'sapphic' F/F works that also carry a Sappho tag, this year", "whether 'sapphic' refers to Sappho (RQ3)", "key_numbers_golem.csv"),
    "T6":         ("F/F works carrying tags of both families, this year", "whether the families are used by the same works (RQ2)", "Fig. 8"),
}


def header(name: str) -> str:
    key = next(k for k in sorted(TASK_DOC, key=len, reverse=True) if name.startswith(k))
    what, why, used = TASK_DOC[key]
    return f"# {name}: {what}.\n# Purpose: {why}. Used in: {used}.\n"


# ── HTTP ───────────────────────────────────────────────────────────────────────
def run_query(query: str) -> tuple[str, str]:
    """Returns (csv_text, problem). problem == '' if the result is complete."""
    data = urllib.parse.urlencode({"query": query, "format": "text/csv",
                                   "timeout": str(TIMEOUT * 1000)}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, method="POST",
                                 headers={"Accept": "text/csv", "User-Agent": "golem-runner (research)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode("utf-8")
        state = resp.headers.get("X-SQL-State", "") or ""
        msg = resp.headers.get("X-SQL-Message", "") or ""
    problem = ""
    if state or "S1TAT" in msg.upper() or "partial" in msg.lower():
        problem = f"PARTIAL RESULT ({state} {msg})"
    rows = max(0, len(list(csv.reader(io.StringIO(text)))) - 1)
    if rows in (10000, 100000):
        problem = (problem + " " if problem else "") + f"possibly truncated at {rows} rows"
    return text, problem


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", nargs="*", default=["T2", "T6", "T3", "T4", "T5", "T1"])
    ap.add_argument("--out", type=Path, default=HERE / "golem_results", help="output directory")
    ap.add_argument("--dry-run", action="store_true", help="write the queries without running them")
    args = ap.parse_args()

    OUT = args.out
    OUT.mkdir(parents=True, exist_ok=True)
    qdir = OUT / "queries"; qdir.mkdir(exist_ok=True)
    problems = OUT / "_problems.txt"
    jobs = build_jobs()
    todo = [(n, q) for t in args.tasks for n, q in jobs.get(t, [])]
    for name, q in todo:
        (qdir / f"{name}.rq").write_text(header(name) + q, encoding="utf-8")
    if args.dry_run:
        print(f"{len(todo)} queries written to {qdir}/"); return

    pending = [(n, q) for n, q in todo if not (OUT / f"{n}.csv").exists()]
    print(f"{len(todo)} queries, {len(todo) - len(pending)} already completed, {len(pending)} pending.")
    for i, (name, q) in enumerate(pending, 1):
        t0 = time.time()
        try:
            text, problem = run_query(q)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            problem, text = f"ERROR {e}", ""
        dt = time.time() - t0
        if problem:
            with problems.open("a", encoding="utf-8") as f:
                f.write(f"{name}\t{problem}\n")
            print(f"[{i}/{len(pending)}] {name}: {problem} ({dt:.0f}s); retried on next run")
            if text:
                (OUT / f"{name}.PARTIAL.csv").write_text(text, encoding="utf-8")
        else:
            (OUT / f"{name}.csv").write_text(text, encoding="utf-8")
            print(f"[{i}/{len(pending)}] {name}: ok ({dt:.0f}s)")
        time.sleep(PAUSE)
    print(f"Done. Results in {OUT}/; incomplete queries are listed in {problems}.")


if __name__ == "__main__":
    main()
