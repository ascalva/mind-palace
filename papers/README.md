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

    scripts/build_papers.sh            # every paper, into build/papers/
    scripts/build_papers.sh <dir>...   # the named ones

It runs `latexmk -pdf` with TeX Live. The `papers` workflow builds every paper on a pull request that
touches `papers/` and uploads the PDFs as an artifact.
