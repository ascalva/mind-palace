#!/usr/bin/env bash
# Build every papers/*/paper.tex (or the directories named) into build/papers/<dir>/, with latexmk.
# Exit nonzero if any paper fails, or leaves an undefined reference or citation.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${PAPERS_OUT:-build/papers}"
if [ "$#" -gt 0 ]; then dirs=("$@"); else dirs=(papers/*/); fi
status=0
for d in "${dirs[@]}"; do
  d="${d%/}"
  [ -f "$d/paper.tex" ] || continue
  name="$(basename "$d")"
  mkdir -p "$OUT/$name"
  if (cd "$d" && latexmk -pdf -interaction=nonstopmode -halt-on-error \
        -outdir="$OLDPWD/$OUT/$name" paper.tex >/dev/null); then
    if grep -qE "undefined (references|citations)|Citation .* undefined|Reference .* undefined" \
        "$OUT/$name/paper.log"; then
      echo "✗ $name: undefined references or citations"; status=1
    else
      echo "✓ $name"
    fi
  else
    echo "✗ $name: see $OUT/$name/paper.log"; status=1
  fi
done
exit "$status"
