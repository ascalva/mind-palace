# Archive / supersession recommendation (2026-07-06)

**Type:** recommendation for owner approval. **Read-only** — no note moved, edited, or
converted; supersession is an owner-only lifecycle act (§10, and `supersession-lifecycle.md`'s
three-place P → P′ + warrant). This file only names candidates and the evidence.

**Sources:** `docs/audits/corpus-state-audit-2026-07.md` (prior audit) and
`docs/audits/corpus-state-audit-2026-07-verification.md` (verification), plus each note's
git creation date (`git log --diff-filter=A --format=%ai -1 -- <file>`).

**A candidate must meet ≥ 2 of 3 signals:** (1) older than another note covering the same
subsystem [dates]; (2) subject overlaps a newer note [named]; (3) the audit shows the newer
note is the one actually built [cited].

### Date caveat (read before trusting signal 1)
Git creation dates here are **commit-batch dates, not authoring order.** Seven notes share
`2026-06-27 12:52:23` and seven share `2026-07-04 04:11:44` — bulk imports. Where two notes
in a supersession relationship share a commit, **signal 1 is unavailable** and the
recommendation rests on the note's *self-declared* supersession + the audit (signals 2 & 3).
This is called out per-row.

---

## Recommended for supersession

Both are **SUPERSEDE-in-place** (keep the file, add `status: superseded` + a `superseded_by`
pointer) — **not** ARCHIVE (move-out): each is recent, part of an active design lineage, and
retains provenance/residual-accuracy value. Neither is a full replacement (both supersessions
are *partial*), so removing them would lose live design context.

| Note path | Created | Disposition | Overruling note (created) | Signals + citations | Rationale (1 line) |
|-----------|---------|-------------|---------------------------|---------------------|--------------------|
| `docs/design-notes/ambassador-interpretation-and-flow.md` | 2026-06-28 | **SUPERSEDE-in-place** (`superseded_by: dn-ambassador-as-reasoning-agent`) | `ambassador-as-reasoning-agent.md` (2026-06-29) | **1,2,3** — see below | The authoritative Ambassador note refines+corrects it; note self-declares partial supersession; both built. |
| `docs/design-notes/secrets-management-evolution.md` | 2026-06-27 | **SUPERSEDE-in-place** (`superseded_by: dn-vault-runtime-auth`) | `vault-runtime-auth.md` (2026-06-27, same commit) | **2,3** (1 N/A — same commit) | Successor self-declares supersession and is the design that was actually implemented (local Vault + AWS engine); server-Vault proposal never built. |

### Evidence detail

**1. `ambassador-interpretation-and-flow.md` → superseded by `ambassador-as-reasoning-agent.md`**
- **Signal 1 (older):** ✅ interpretation `2026-06-28 13:46:37` < reasoning-agent `2026-06-29 10:57:40` (~21 h; distinct commits — reliable here).
- **Signal 2 (subject overlap, newer named):** ✅ same subsystem (Ambassador interpretation/flow). Successor self-describes as "Refines and *corrects*" it; the older note itself declares `**⚠️ PARTIALLY SUPERSEDED (2026-06-28)** — ambassador-as-reasoning-agent.md is the [authoritative note]` (`ambassador-interpretation-and-flow.md:5`).
- **Signal 3 (audit shows newer is built):** ✅ prior audit §2 marks `ambassador-as-reasoning-agent.md` "the *authoritative* Ambassador note" (BUILT & WIRED, `agents/ambassador/*`, `launcher.py:117-124`); §2 says interpretation "Should carry a `superseded_by`" and §4 (proposal 7) already proposes `status: superseded`; verification §3 upholds both as wired and notes interpretation "trails the code (4 intents vs 6)."
- **Disposition:** SUPERSEDE-in-place — partial supersession; interpretation's §3 conversation-time-interpretation doctrine still has value, so keep with a pointer, don't archive.

**2. `secrets-management-evolution.md` → superseded by `vault-runtime-auth.md`**
- **Signal 1 (older):** ❌ **N/A** — both created in the *same* commit (`2026-06-27 12:52:23`); no chronological ordering. (Honest gap — not fudged.)
- **Signal 2 (subject overlap, newer named):** ✅ same subsystem (secrets/Vault). The successor self-declares it: `vault-runtime-auth.md:5` "**Supersedes `secrets-management-evolution.md`**."
- **Signal 3 (audit shows newer is the built design):** ✅ prior audit §2 (secrets-management "PARTIAL (superseded)… `vault-runtime-auth.md:5` declares it supersedes this note, but this note carries no superseded/deprecated marker"); finding-0010 (stale-status cohort); verification §1 EXISTS-as-IaC — `cloud/terraform/airlock/vault_engine.tf` realizes vault-runtime-auth's §4 AWS engine, while secrets-management's distinctive proposal (server-hosted Vault / KMS auto-unseal / AppRole-per-component) is confirmed **not built** (verification §2). The corpus implemented the *successor's* local design.
- **Disposition:** SUPERSEDE-in-place — meets 2 of 3 signals (per the rule). Keep, don't archive: its "Keychain now" description is still the **current** operational reality (`run_with_secrets.sh` is wired), so the file documents live state; only its *future* proposal is superseded. Marking `superseded_by` resolves the "unmarked supersession" flagged in finding-0010.

---

## Considered but LEFT as-is (evidence ambiguous — not recommending on a guess)

Every remaining same-subsystem cluster was examined; each is left in place, with why:

| Note(s) | Why not a supersession-archive candidate |
|---------|------------------------------------------|
| `nervous-system-and-ambassador.md` (2026-06-28) | Only its **§4** (Ambassador) is refined by the ambassador notes; it uniquely owns §1 (graduated tamper tripwire) and §2 (async auditor), both designed-but-unbuilt (prior audit §2; verification §2 confirms `class Auditor` absent). Partial-overlap, not whole-note supersession. **Keep.** |
| `observed-data-and-the-assistant-tier.md` (2026-06-25) ↔ `observed-iot-and-cross-source-synthesis.md` (2026-06-27) | Newer note **extends** (not supersedes) the base; the base owns the firewall + assistant-tier concept. Signal 3 fails — the audit shows **neither** is built (both PARTIAL/seam-only). Additive family. **Keep both.** |
| Dream R&D family: `dream-phase-rnd-charter.md` (umbrella), `dreaming-v2-interpreter-panel.md`, `recursive-dreaming-bounded-by-grounding.md`, `dreaming-on-curated-graphs.md` (all 2026-06-26), `stability-adjudication.md` (2026-07-02) | Layered **extensions** (charter → panel → R3 → R5 → post-panel enhancement), not supersessions. Signal 3 fails uniformly — all flag-off / not wired (prior audit §2 cluster D + F). No intra-family overruling. **Keep all.** |
| `holistic-testing.md` ↔ `test-organization.md` (both 2026-06-27, same commit) | Overlap "testing" but **complementary**: holistic = the six test *categories* + "test process not product" philosophy (owns the unbuilt emergent/longitudinal); test-organization = the *directory reorg* (built skeleton). Neither overrules the other; signal 1 N/A (same commit). **Keep both.** |
| `recursive-strata-amendment.md` (2026-07-04) | A **pending patch-spec** (edits to apply to `recursive-strata.md`), not a superseding note; its edits are *unapplied* (prior audit §2; finding-0013). Archiving would drop the pending patch. **Keep as draft until applied**, then it folds into `recursive-strata.md`. |
| Sacred-boundary reconciliation set: `the-sacred-boundary.md`, `the-edge-model.md`, `ingest-identity-and-amendment.md`, `dialogue-ingest-and-recursion.md`, `supersession-lifecycle.md`, `founding-corpus.md`, `verdict-authority.md` (all 2026-07-04) | Complementary pieces of **one** design set (indexed by `the-sacred-boundary.md`); each covers a distinct aspect. No intra-set overruling. **Keep all.** |
| `attestation-layer.md` (2026-06-27) | **Extends** `vault-runtime-auth.md` (does not supersede it). **Keep.** |

### Separate track — not a supersession question
| Note | Disposition |
|------|-------------|
| `docs/research/planar_graphs.md` (2026-07-03) | **Archive candidate on ORPHAN grounds, NOT supersession** — it meets **0** of the 3 signals (no newer overlapping note; its subject, planar-graph drawing, is unbuilt and unreferenced; `core/complex/` is *different* math). Its disposition is the "catalogue-or-prune" decision already owned by **finding-0017**, on a different basis than this table's supersession logic. Flagged here for completeness; owner rules via finding-0017, not here. |

---

## Summary
- **2 notes recommended for SUPERSEDE-in-place** (ambassador-interpretation-and-flow;
  secrets-management-evolution) — both partial supersessions with a named, built/declared
  successor; keep the file + add `superseded_by`. **0 notes recommended for physical ARCHIVE**
  on supersession grounds.
- The corpus is otherwise a set of complementary and additive design families, not redundant
  duplicates — so the conservative recommendation is small by design.
- One orphan (`planar_graphs.md`) is an archive question, but on **orphan** grounds via
  finding-0017, not supersession.

*Owner approves before any status is set or any note moved. Applying `superseded_by` is a
by-hand edit at the blessing gate on the denylisted `docs/design-notes/**` surface (§10).*
