# ORIENTATION

Top-of-session card for a fresh building agent. Stable and short by design: this is the
map and the reading protocol, **not** a status log. Current state lives in `PROGRESS.md`;
the design lives in `BUILD-SPEC.md`; the inviolable frame lives in `CONSTITUTION.md`.
If this card and those files ever disagree, they win — fix this card.

---

## What this is (three lines)

A single-user, offline-first, privacy-sealed personal AI over the owner's private notes:
it indexes them and reflects patterns back (**mirror, not oracle**), with a gated agent
layer, an agent factory, a pluggable messaging interface, and a one-way research airlock.
Built to be **extended over time**, not shipped as a fixed product. Owner is a
security-focused DevOps/AWS engineer with strong Python — write to that level.

## The floor you never break (structural, not stylistic)

These are enforced in code, not by good intentions. Breaking one is a build-breaking
defect, not a preference. Full list: `CLAUDE.md` non-negotiables + `BUILD-SPEC §3`.

1. **`core/` has zero network egress.** An accidental network-capable import in `core/`
   is a defect. Only `edge/` touches the network; it never reads the vault.
2. **The model advises; code acts.** No model holds a shell, raw secrets, or infra
   mutation. Executed agent code is powerless: sandboxed, no creds/net/vault, returns
   data, never actions.
3. **Self-modification is propose → approve → execute → validate → rollback**, human-gated,
   no step skipped. The fixed points (frozen golden set, `CONSTITUTION.md`) are never
   auto-modified.
4. **Provenance firewall.** `MIRROR_READABLE` is authored-only (`AUTHORED_SOLO` +
   `AUTHORED_DIALOGUE`); `CURATED`, `OBSERVED`, and derived exhaust never leak into the
   mirror. One ingest pipeline, provenance-parametric — never a bespoke writer.
5. **Scoped store access is structural.** Each role gets a handle limited to exactly its
   reads/writes; the wrong access is made impossible, not discouraged.

## Reading protocol (do this; skip the rest)

Orientation is slow only if you read everything. Don't.

1. **This card is the whole map.** You do not need to crawl the tree.
2. **Get current from one place:** the newest entry of `PROGRESS.md` (the "Forward layer"
   section at the top). Read that entry, not the 214 KB of history beneath it. Work is
   now **Track items** (`ROADMAP-V1.md`), not numbered phases; phases 0–10 are done.
3. **For your task, read only:** the one spec section that governs it (`BUILD-SPEC §N`, or
   the relevant `docs/design-notes/*.md`), plus the module you're editing. Nothing else.
4. **Authority order when docs conflict:** `CONSTITUTION.md` > `BUILD-SPEC.md` >
   `CONVENTIONS.md` > `docs/design-notes/` > `docs/research/` (drafts). `PROGRESS.md` is
   state-of-the-world, never a spec.

## Repo map

```
core/     Zone A — SEALED, no network (ingest, librarian, curator, dreaming, complex,
          matching, factory, sandbox, stores, provenance.py, constitution.py)
edge/     Zone B — networked, containerized (bridge, interface gateway) — no vault handle
cloud/    Zone C — Terraform + research fetcher (least-privilege IAM)
agents/   persistent role definitions        scheduler/  supervisor + queue + budgeter
ops/      gate, levers, rollback, effects     eval/  golden sets, metrics, baselines
docs/     BUILD-SPEC.md (design) · PROGRESS.md (build log) · schema.md (live schema) ·
          design-notes/ (parked designs, each with re-entry conditions) · research/
          (drafts) · audits/
root:     CONSTITUTION.md · CONVENTIONS.md · CLAUDE.md
```

## How to work

- **One track-item (or phase) per session.** Build it, verify against its gate, checkpoint
  with the owner, append a terse `PROGRESS.md` entry (built / verified / next / decisions).
  Don't carry chat history; a fresh session re-grounds from that entry + this card + the
  task's spec section.
- **Tests alongside code, not after.** `pytest` deselecting `live`/`podman` is the fast
  deterministic ratchet — keep it green. It is not the finish line: run `pytest -m live`
  when the tier's model is pulled, `pytest -m podman` when podman is up. If a live gate was
  skipped, say so and why. (`live` = real Ollama tiers; `podman` = the sandbox `run_python`
  path — two different axes, don't conflate.)
- **Ask, don't guess** on `BUILD-SPEC §20` decisions. Everywhere else, pick a sensible
  default and state it inline.
- **Reference paths, don't echo file contents.** Small, reversible steps. Content-address;
  derived layers (chunks, vectors, dreams) are regenerable — rebuild from the raw store
  rather than mutating in place.
- **Comment the *why* at trust boundaries** (airlock asymmetry, propose/execute split,
  scope ceiling) so a later edit can't quietly erode the property.
- **Frameworks:** hand-roll the loop. No LangGraph/CrewAI/AutoGen. Thin wrappers over
  Ollama HTTP, LanceDB, DuckDB, SQLite, Podman.

## House style (owner's standing preferences)

- **Exact, dry language.** No sales-adjacent or performative framing in docs or docstrings.
- **Formalism must constrain, not decorate** — every construct earns its place or is cut.
- **Parked decisions are first-class:** written up with explicit re-entry conditions, not
  discarded. Null results are "no signal at this scale," parked, not deleted.
- **Direct technical pushback is expected.** Flag imprecision; don't pad with caveats.
- **Scoped, builder-ready output** over expansive design notes. Restraint at moments of
  excitement is the standing posture.
