# papers

Every pull request carries an article that explains its change the way a short research paper would:
the problem, the theory, the concepts and their intuition, the evaluation, what remains, and the
references. The pull request's description is a summary of it.

## Layout

One directory per pull request, named by date and subject:

    papers/YYYY-MM-DD-<slug>/paper.tex
    papers/YYYY-MM-DD-<slug>/refs.bib

Each `paper.tex` carries its own preamble, so two papers never share a file and never conflict.
`_template/` is the starting point. Figures, when there are any, sit beside the source as PDF or
TikZ; compiled PDFs are build output and are never committed.

## Sections

An abstract; an introduction that states the problem and the contributions; background and related
work; the theory (definitions, theorems, proof sketches, and the Lean declarations that check them);
the concepts and their intuition; the implementation, in pseudocode where that is clearer than prose;
the evaluation (what is proved, what is measured, with the numbers and how they were obtained); the
limitations; future work; the conclusion; the references.

## Voice

Plain and specific. No pause dashes between words, no enthusiasm, no personal narration: state the
problem and the result. Every reference must be one the author has checked; omit a reference rather
than guess one. Numbers come from runs that can be repeated, and the paper says how.

## Building

    scripts/build_papers.sh                          # every paper, into build/papers/
    scripts/build_papers.sh <dir>...                 # the named ones
    PAPERS_OUT=/tmp/papers scripts/build_papers.sh   # into another directory

`PAPERS_OUT` may be absolute or relative; a relative one is taken from the repository root, as the
directories named are. The script runs `latexmk -pdf` with TeX Live and prints one line per paper.
A paper fails if latexmk fails, if its log reports an undefined reference or citation, or if it
leaves no log to check. A failure prints its reason from the log that explains it (for a TeX
error, latexmk's error summary, the TeX log's error lines and its last 30 lines) and keeps that log
as `failed.log` in the paper's output directory, beside `latexmk.log`, latexmk's own output.
`tests/integration/test_build_papers.py` tests the script; the tests that build need TeX and carry
the `needs_tex` marker.

The `papers` workflow builds every paper on a pull request that touches `papers/`, uploads the PDFs
with each failed paper's `failed.log` beside them as an artifact, and runs those tests. Its TeX Live
is Ubuntu's packages, which lack some fonts a full TeX Live has (cm-super among them). A paper that
sets T1 encoding without `\usepackage{lmodern}` falls back to bitmap fonts there, which microtype
cannot expand, so it passes locally and fails in the workflow; the template loads both.
