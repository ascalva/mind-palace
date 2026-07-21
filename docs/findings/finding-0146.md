---
type: finding
id: finding-0146
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - ops/code_sensor.py                            # the model-less structural sensor (the defect's home)
  - core/ingest/pipeline.py                        # the embed path — vault .md only, no code
  - core/stores/vectorstore.py                     # the semantic space — AUTHORED note chunks only
  - docs/design-notes/code-observation-projection.md   # the two-plane model this finding CHALLENGES (owner ruling)
  - docs/findings/finding-0145.md                  # sibling — the reference-sensor staleness/shorthand gap
  - docs/brainstorms/code-as-sensor-stream.md      # the sensor framing being revisited
ftype: design
route: orchestrator        # OWNER RULED this a bug (2026-07-21); needs a design pass, likely a note correction
resolution: null
---

# The code corpus is not vectorized at all (source + docstrings + comments), and code→doc references are literal-path-only — OWNER-RULED A BUG

## Owner ruling (2026-07-21)

Shown the evidence below, the owner ruled plainly: **"this is a bug, this is not a design that I
would ever think is ok"** — and, sharpening it: **"not just that [docstrings/comments], the code
itself is not being vectorized."** The current "code is a structural-only OBSERVED plane, kept out
of the semantic AUTHORED corpus" boundary (`dn-code-observation-projection`, the two-plane model) is
**rejected as the intended design** for this behavior. The code — its source, its docstrings, its
comments — IS a semantic source and must be embedded. A DEFECT to fix, not an open design question.
`[owner ruling]`

## The defect — the code corpus is absent from the semantic space, traced end-to-end

`[GROUNDED — code read + live-store counts, HEAD db5fc0d]`

1. **The code itself is never vectorized — source, docstrings, AND comments.** `ops/code_sensor.py`
   is model-less by construction (its own header: *"no model, no embedder, no vector corpus, no
   network"*). It projects the repo STRUCTURALLY into `code_snapshots.sqlite` — symbols, signatures,
   docstrings-as-SQL-text, regex references — and vectorizes **nothing**. The only embed path
   (`core/ingest/pipeline.py`, *"vault → raw store → chunks"*, globs `**/*.md`) takes ONLY vault
   notes; `vectors.lance` holds AUTHORED note chunks only (**28 chunk rows / 19 note centroids**
   live). **No `.py` source, no docstring, no comment ever enters the semantic space.** ⇒ code is
   not semantically retrievable (no "find the code that does X" by similarity), not a σ-graph
   (S-fiber) node, absent from σ*/conductance/curvature, and invisible to the mirror and the
   dreamer. The system reasons over its notes but is blind, semantically, to its own code.
2. **Inline `#` comments aren't even captured structurally.** The sensor works on docstrings
   (`"""…"""`); `#` comments enter no store at all — dropped, not just un-embedded.
3. **Code→doc references are literal-path-only.** `_RE_NOTE_CITATION`
   (`ops/code_sensor.py:109`) = `docs/(?:design-notes|findings|brainstorms)/…\.md` — it matches
   only a spelled-out path. So the dominant docstring citation forms are missed:

   | in core `.py` docstrings | count | captured? |
   |---|---|---|
   | files citing a note/finding | 71 | — |
   | `dn-<slug>` tokens | 165 | ✗ |
   | `finding-NNNN` tokens | 55 | ✗ |
   | `§`-section refs | 968 | ✗ |
   | explicit `docs/…md` paths | ~19 | ✓ (the only ones) |

   Captured code→corpus note-citations at HEAD: **19** (vs hundreds of real references). Plus a
   false-positive surface — a literal example path `docs/design-notes/x.md` was captured as a real
   edge (`ops/code_sensor.py` docstring).

## Why it matters

The palace is "a self-map — mining my own brain" ([[owner-background-self-mapping]]), yet its own
**code** — the largest, densest artifact it is made of, carrying the math, the `§`-warrants, the
logic and the "why" — is entirely outside the semantic map. Ouroboros can dream over its notes but
cannot see its own source. Every semantic instrument (similarity retrieval, σ*/conductance,
curvature, the dreamer, the S-fiber) operates on ~19 notes and zero lines of code. The code and its
design warrants are semantically disconnected from each other AND from the corpus.

## The fix surface (a design pass sizes it; owner ruled the direction)

- **Vectorize the code corpus** — the source itself (chunked, e.g. by symbol/def) WITH its
  docstrings and comments, as a first-class semantic source, under a provenance class that keeps the
  mirror=AUTHORED-only firewall intact (a `code`/OBSERVED-adjacent provenance in `vectorstore`, not
  AUTHORED). Reuse the existing `derive_chunks`/embed path, don't reinvent (the extractor exists;
  this adds a code→chunk→embed lane). This CORRECTS `dn-code-observation-projection`'s two-plane
  separation (banner-on-correction, not a silent edit) — the design note likely needs supersession.
- **Capture inline `#` comments** (not just docstrings) in the code sensor's text.
- **Resolve shorthand references** — `dn-<slug>` → the note, `finding-NNNN` → the finding, `§N`
  → the section anchor — not just literal `docs/…md` paths; and drop example-path false-positives.
  (This is the reference axis of finding-0145 / PD-5 — the two are siblings.)
- **Memory-ceiling note:** embedding the code corpus is a heavier ingest than 19 notes — size it
  against non-negotiable #8 (the deploy-vs-ingest memory race just seen is the live reminder).

## Routing

`design` → orchestrator. OWNER RULED it a bug; the next step is a design pass (capture → design
note) that scopes the code-as-semantic-source seam and reconciles `dn-code-observation-projection`.
NOT a mechanical build — it touches the plane model, the firewall provenance, and the embedder
inputs. Pairs with finding-0145 (the reference-sensor track).
