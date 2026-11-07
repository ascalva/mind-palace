#!/usr/bin/env bash
# Build every papers/*/paper.tex (or the directories named) with latexmk into $PAPERS_OUT/<dir>/.
# PAPERS_OUT defaults to build/papers; a relative one, like a directory named, is taken from the
# repository root. Exit nonzero if any paper fails, leaves an undefined reference or citation, or
# leaves no log to check.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
out="${PAPERS_OUT:-build/papers}"
case "$out" in /*) ;; *) out="$root/$out" ;; esac
out="${out%/}"
undefined='undefined (references|citations)|Citation .* undefined|Reference .* undefined'

shown() { echo "${1#"$root"/}"; }   # a path from the repository root, when it lies inside it

if [ "$#" -gt 0 ]; then dirs=("$@"); else dirs=(papers/*/); fi
status=0
for d in "${dirs[@]}"; do
  d="${d%/}"
  [ -f "$d/paper.tex" ] || continue
  name="$(basename "$d")"
  dir="$out/$name"
  tex="$dir/paper.log"
  mkdir -p "$dir"
  if ! (cd "$d" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$dir" paper.tex \
      >/dev/null); then
    echo "✗ $name: see $(shown "$tex")"
  elif [ ! -f "$tex" ]; then
    echo "✗ $name: no log at $(shown "$tex") to check for undefined references"
  elif grep -qE "$undefined" "$tex"; then
    echo "✗ $name: undefined references or citations"
  else
    echo "✓ $name"
    continue
  fi
  status=1
done
exit "$status"
