#!/usr/bin/env python3
"""Run the analysis pipeline.

Usage:
    python reproduce.py                      analysis and figures
    python reproduce.py analysis             GOLEM analysis and tag typology
    python reproduce.py figures [OUT_DIR]    Figures 1–16
    python reproduce.py sappho               Sappho metadata (requires the unpublished raw metadata)
    python reproduce.py fulltexts TEXT_DIR   Sappho full texts (requires the unpublished full texts)
    python reproduce.py queries [ARGS ...]   GOLEM queries (requires network access)
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = {
    "analysis": ["analysis/analysis_golem.py", "analysis/tag_family_types.py"],
    "figures": ["figure_scripts/make_figures.py"],
    "sappho": ["analysis/analysis_sappho.py"],
    "fulltexts": ["analysis/analysis_fulltexts.py"],
    "queries": ["golem/golem_runner.py"],
}


def run(step, args):
    for script in STEPS[step]:
        subprocess.run([sys.executable, str(HERE / script), *args], check=True)


def main():
    if len(sys.argv) == 1:
        run("analysis", [])
        run("figures", [])
    elif sys.argv[1] in STEPS:
        run(sys.argv[1], sys.argv[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
