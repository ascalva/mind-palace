"""Assemble the 2026-10-29 curated-literature sources into plain documents + one manifest.

    python3 -I assemble.py --openai DIR --anthropic DIR --out DIR [--pdftext BIN]

A probe, not a tool (the bp-011 convention): it turns already-downloaded files into
`<out>/texts/*` and `<out>/manifest.json` for `scripts/curate_local.py`, which embeds them into the
curated store. Stdlib only; it never executes anything from the sources and reads them as text.

  * OpenAI Math Release (`openai/math`, Apache-2.0): one document per manuscript, the LATEST dated
    version of each title (folders differ only by their date suffix). Its LaTeX body is assembled
    from `build/paper.tex` with every `\\input`/`\\include` inlined, comments, the preamble and
    figures dropped — the mathematics stays as written. The repo's `CONTENTS.md` (the result map
    with every abstract) is one more document.
  * Anthropic (Fermat's Last Theorem, the Riemann-zeta bound): the research posts' article text,
    and each PDF's text through PDFKit (`pdftext.swift`, compiled by the caller).

Every document is tagged unreviewed (the owner's ruling, 2026-10-29): none of these claims had
been checked by outside experts when it was ingested. Anthropic's two results were Lean-checked,
which the tag also says.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

_DATED = re.compile(r"^(?P<base>.+)-(?P<month>[A-Z][a-z]+)-(?P<day>\d{1,2})-(?P<year>\d{4})$")
_ISO = re.compile(r"^(?P<base>.+)-(?P<iso>\d{4}-\d{2}-\d{2})$")
_INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
_COMMENT = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
# a compiled sub-document pulled in whole; its own .tex sits beside it (`\includepdf{part-1.pdf}`)
_INCLUDEPDF = re.compile(r"\\includepdf(?:\[[^\]]*\])?\{([^}]+?)(?:\.pdf)?\}")


def _dated(folder: str) -> tuple[str, date] | None:
    """`Title-October-25-2026` (most folders) or `Title-2026-09-24`."""
    iso = _ISO.match(folder)
    if iso:
        return iso["base"], date.fromisoformat(iso["iso"])
    m = _DATED.match(folder)
    if not m:
        return None
    when = datetime.strptime(f"{m['month']} {m['day']} {m['year']}", "%B %d %Y").date()
    return m["base"], when


def _inline(path: Path, root: Path, seen: set[Path]) -> str:
    """The file's LaTeX with every \\input/\\include replaced by its (recursively inlined) text."""
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    text = _COMMENT.sub("", path.read_text(encoding="utf-8", errors="replace"))

    def sub(m: re.Match[str]) -> str:
        name = m.group(1).strip()
        target = (root / name) if name.endswith(".tex") else (root / f"{name}.tex")
        resolved = target.resolve()
        return _inline(resolved, root, seen) if resolved.is_relative_to(root) else ""

    def subdoc(m: re.Match[str]) -> str:
        target = (root / f"{m.group(1).strip()}.tex").resolve()
        inner = _inline(target, root, seen) if target.is_relative_to(root) else ""
        return _body(inner) if inner else ""

    return _INCLUDEPDF.sub(subdoc, _INPUT.sub(sub, text))


def _root_tex(build: Path) -> Path | None:
    """The manuscript's top-level file — `paper.tex`, `main.tex` or `source/main.tex` across the
    release: a .tex holding `\\begin{document}`, named paper/main if one is (standalone figures
    and sub-documents have their own), then the shallowest, then the largest."""
    candidates = [f for f in build.rglob("*.tex")
                  if "\\begin{document}" in f.read_text(encoding="utf-8", errors="replace")]
    named = [f for f in candidates if f.name in ("paper.tex", "main.tex")]
    return min(named or candidates,
               key=lambda f: (len(f.relative_to(build).parts), -f.stat().st_size), default=None)


def _body(tex: str) -> str:
    start, end = tex.find("\\begin{document}"), tex.rfind("\\end{document}")
    if start != -1:
        tex = tex[start + len("\\begin{document}"):end if end != -1 else None]
    tex = re.sub(r"\\(?:bibliography|bibliographystyle)\{[^}]*\}", "", tex)
    tex = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", "[figure]", tex)
    return re.sub(r"\n{3,}", "\n\n", tex).strip()


def _readme_title(readme: Path, fallback: str) -> str:
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s*\[(.+?)\]\(", text, re.M)
        if m:
            return m.group(1).strip()
    return fallback.replace("-", " ")


def openai_documents(repo: Path, out: Path, commit: str) -> list[dict[str, object]]:
    latest: dict[str, tuple[date, str]] = {}
    for folder in sorted(p.name for p in (repo / "preprints").iterdir() if p.is_dir()):
        parsed = _dated(folder)
        if parsed is None:
            continue
        base, when = parsed
        if base not in latest or when > latest[base][0]:
            latest[base] = (when, folder)
    docs: list[dict[str, object]] = []
    for base, (when, folder) in sorted(latest.items()):
        build = (repo / "preprints" / folder / "build").resolve()
        root = _root_tex(build) if build.is_dir() else None
        if root is None:
            continue   # no LaTeX in the release for this one
        text = _body(_inline(root, root.parent, set()))
        if len(text) < 500:
            continue   # no LaTeX in the release for this one
        dest = out / "texts" / f"openai-math--{folder}.tex"
        dest.write_text(text, encoding="utf-8")
        docs.append({
            "source": "openai-math", "id": folder, "path": str(dest), "chars": len(text),
            "title": _readme_title(repo / "preprints" / folder / "README.md", base),
            "tag": f"unreviewed · OpenAI {when.isoformat()}", "date": when.isoformat(),
            "url": f"https://github.com/openai/math/tree/{commit}/preprints/{folder}",
            "licence": "Apache-2.0",
        })
    contents = repo / "CONTENTS.md"
    if contents.is_file():
        text = html.unescape(re.sub(r"<[^>]+>", " ", contents.read_text(encoding="utf-8")))
        dest = out / "texts" / "openai-math--CONTENTS.md"
        dest.write_text(re.sub(r"[ \t]+", " ", text), encoding="utf-8")
        docs.append({
            "source": "openai-math", "id": "CONTENTS", "path": str(dest), "chars": len(text),
            "title": "OpenAI Math Release — the result map (every manuscript's abstract)",
            "tag": "unreviewed · OpenAI 2026-10-26", "date": "2026-10-26",
            "url": f"https://github.com/openai/math/blob/{commit}/CONTENTS.md",
            "licence": "Apache-2.0",
        })
    return docs


class _Article(HTMLParser):
    """The text of a research post's <article>/<main>, without scripts, styles or navigation."""

    SKIP = {"script", "style", "nav", "footer", "header", "svg", "noscript", "button"}
    BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "figcaption", "td", "br"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth, self.skip, self.parts = 0, 0, []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("article", "main"):
            self.depth += 1
        elif tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK and self.depth:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("article", "main"):
            self.depth = max(0, self.depth - 1)
        elif tag in self.SKIP:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data: str) -> None:
        if self.depth and not self.skip:
            self.parts.append(data)


def _article_text(page: Path) -> str:
    p = _Article()
    p.feed(page.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", "".join(p.parts))).strip()


ANTHROPIC = (  # file, title, date — the two results' posts and every document they publish
    ("flt-post.html", "Formalizing Fermat's Last Theorem (Anthropic research post)", "2026-09-04"),
    ("flt-reasoning-excerpts.pdf", "Formalizing Fermat's Last Theorem — excerpts of Claude's "
     "reasoning", "2026-09-04"),
    ("zeta-post.html", "Riemann zeta: the proportion of zeros on the critical line raised from "
     "41.6% to 67.2% (Anthropic research post)", "2026-08-10"),
    ("zeta-paper.pdf", "Riemann zeta critical-line proportion 67.2% — the paper", "2026-08-10"),
    ("zeta-expert-note.pdf", "Riemann zeta critical-line proportion — an expert's concise note on "
     "the proof", "2026-08-10"),
    ("zeta-claude-explanation.pdf", "Riemann zeta critical-line proportion — Claude's account of "
     "how it reached the result", "2026-08-10"),
    ("zeta-process-transcripts.pdf", "Riemann zeta critical-line proportion — process "
     "transcripts", "2026-08-10"),
)
ANTHROPIC_URLS = {
    "flt": "https://www.anthropic.com/research/formalizing-fermats-last-theorem",
    "zeta": "https://www.anthropic.com/research/riemann-zeta",
}


def anthropic_documents(src: Path, out: Path, pdftext: Path) -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []
    for name, title, when in ANTHROPIC:
        path = src / name
        dest = out / "texts" / f"anthropic--{Path(name).stem}.txt"
        if name.endswith(".pdf"):
            subprocess.run([str(pdftext), str(path), str(dest)], check=True, capture_output=True)
        else:
            dest.write_text(_article_text(path), encoding="utf-8")
        text = dest.read_text(encoding="utf-8")
        docs.append({
            "source": "anthropic", "id": Path(name).stem, "path": str(dest), "chars": len(text),
            "title": title, "tag": f"unreviewed · Anthropic {when} · Lean-checked", "date": when,
            "url": ANTHROPIC_URLS[name.split("-", 1)[0]], "licence": "published by Anthropic",
        })
    return docs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--openai", type=Path, required=True)
    ap.add_argument("--anthropic", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pdftext", type=Path, required=True)
    ap.add_argument("--commit", required=True)
    a = ap.parse_args()
    (a.out / "texts").mkdir(parents=True, exist_ok=True)
    docs = openai_documents(a.openai.resolve(), a.out, a.commit)
    docs += anthropic_documents(a.anthropic.resolve(), a.out, a.pdftext)
    (a.out / "manifest.json").write_text(json.dumps(docs, indent=1, ensure_ascii=False))
    n_oai = sum(d["source"] == "openai-math" for d in docs)
    total = sum(int(str(d["chars"])) for d in docs)
    print(f"{len(docs)} documents ({n_oai} OpenAI, {len(docs) - n_oai} Anthropic), "
          f"{total / 1e6:.1f} M characters → {a.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
