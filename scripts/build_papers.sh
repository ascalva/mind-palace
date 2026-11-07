#!/usr/bin/env bash
# Build every papers/*/paper.tex (or the directories named) with latexmk into $PAPERS_OUT/<dir>/.
# PAPERS_OUT defaults to build/papers; a relative one, like a directory named, is taken from the
# repository root. Exit nonzero if any paper fails, leaves an undefined reference or citation, or
# leaves no log to check. A failure prints its reason from the log that explains it, TeX's or
# latexmk's, and keeps that log as <dir>/failed.log, which the papers workflow uploads beside the
# PDFs. latexmk's own output goes to <dir>/latexmk.log.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
out="${PAPERS_OUT:-build/papers}"
case "$out" in /*) ;; *) out="$root/$out" ;; esac
out="${out%/}"
undefined='undefined (references|citations)|Citation .* undefined|Reference .* undefined'

indent() { sed 's/^/    /'; }
shown() { echo "${1#"$root"/}"; }   # a path from the repository root, when it lies inside it
last30() { echo "  the last 30 lines of $(shown "$1"):"; tail -n 30 "$1" | indent; }

# The useful part of a TeX log: its error lines (those starting with `!`, pdfTeX's, and file:line:
# ones), each with the two lines after it where TeX prints the context, then its last 30 lines.
tex_errors() {
  { grep -E -A2 '^!|pdfTeX error|^[^[:space:]:]+:[0-9]+: ' "$1" || true; } | sed -n '1,40p' | indent
  last30 "$1"
}

if [ "$#" -gt 0 ]; then dirs=("$@"); else dirs=(papers/*/); fi
status=0
for d in "${dirs[@]}"; do
  d="${d%/}"
  [ -f "$d/paper.tex" ] || continue
  name="$(basename "$d")"
  dir="$out/$name"
  tex="$dir/paper.log"
  lmk="$dir/latexmk.log"
  mkdir -p "$dir"
  rm -f "$dir/failed.log"
  if ! (cd "$d" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$dir" paper.tex) \
      >"$lmk" 2>&1; then
    echo "✗ $name: latexmk failed"
    if grep -q '^Collected error summary' "$lmk" && [ -f "$tex" ]; then
      # A rule failed: latexmk's summary names it, and TeX's log of this run says why.
      awk '/^Collected error summary/ {on = 1} on && /^$/ {exit} on' "$lmk" | indent
      log="$tex"
      tex_errors "$tex"
    else
      # latexmk stopped before running a rule (not installed, say): a paper.log there is old.
      log="$lmk"
      last30 "$lmk"
    fi
  elif [ ! -f "$tex" ]; then
    echo "✗ $name: no log at $(shown "$tex") to check for undefined references"
    log="$lmk"
    last30 "$lmk"
  elif grep -qE "$undefined" "$tex"; then
    echo "✗ $name: undefined references or citations"
    grep -E "$undefined" "$tex" | awk '!seen[$0]++ && n++ < 20' | indent
    log="$tex"
  else
    echo "✓ $name"
    continue
  fi
  status=1
  cp "$log" "$dir/failed.log"
  echo "  the full log: $(shown "$dir/failed.log")"
done
exit "$status"
