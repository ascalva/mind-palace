# Owner questions

The one file the owner answers. Orchestrator-maintained (`/triage` batches
routed `design | math | direction` findings here; never dripped). Each entry
carries a `default_if_unanswered` with a **park condition**, so an unanswered
question degrades to a parked item with a re-entry — never a stalled builder (§10).

To answer: edit the entry's `answer:` line and flip `status: open → answered`.
`/triage` then sweeps the answer back to its origin artifact and marks it `swept`.

Entry shape: `status`, `origin`, `blocking` (bool), `question`, `default_if_unanswered`
(with park), `answer`.

---

## oq-0001 — Should CLAUDE.md re-home any of the pre-BP-000 domain digest?
- status: swept
- origin: docs/findings/finding-0001.md
- blocking: false
- question: BP-000 replaced the pre-BP-000 CLAUDE.md (mind-palace operating rules)
  with the persona-neutral workflow constitution, keeping only a pointer to the
  domain layer (`CONSTITUTION.md` / `BUILD-SPEC.md` / `CONVENTIONS.md`). Dropped
  from the auto-loaded surface: the 12-item non-negotiables digest, the repo map,
  the "current phase" marker, and the live-verification directive. All remain in
  `BUILD-SPEC.md` / `CONVENTIONS.md` / git history. Do you want any of that digest
  re-homed into the constitution (which costs tokens every turn), or is the
  pointer sufficient?
- default_if_unanswered: pointer-only stands (workflow constitution stays lean per
  §5). Parks as finding-0001; re-entry — owner answers here, or a `direction`
  finding reports a session missing dropped context.
- answer: Re-home the **safety-critical non-negotiables digest** (only). Ratified as
  amendment A2 (warrant: finding-0001): §5 now exempts the domain bright-line digest
  from the constitution thinness rule — an out-of-context guardrail is not a
  guardrail, so it stays inline in the always-loaded body, not behind a pointer. The
  *other* dropped items (repo map, current-phase marker, live-verify directive) are
  operational context, not guardrails, and stay pointer-only per §5 — they remain in
  `BUILD-SPEC.md` / `CONVENTIONS.md` / git history. Landed by bp-001 in CLAUDE.md.

---

## oq-0002 — Fold bp-002 and bp-003 into the formal lifecycle (`complete`), or leave held at `proposed`?
- status: swept
- origin: docs/PROGRESS.md — the standing "Owner-pending (non-blocking)" lifecycle decision
  recorded in the bp-002 note (2026-07-05) and the bp-003 note (2026-07-06, backfilled)
- blocking: false
- question: bp-002 (amendment A3) and bp-003 (amendment A4) each landed and committed under owner
  authority but never took the owner-only `proposed → ready` blessing, so both sit at
  `status: proposed` while their work is terminal — a split board against bp-000/bp-001/bp-004
  (`complete`). Fold both into the formal `ready → in-progress → complete` lifecycle to match
  bp-004, or leave them held at `proposed` as landed-but-unblessed?
- default_if_unanswered: leave held at `proposed` (the recorded state); re-entry — owner rules
  here, or a `direction` finding reports the split board causing confusion.
- answer: **FOLD BOTH TO `complete`, matching bp-004 — uniform board, no drift** (owner ruling,
  2026-07-06). Enactment respects the blessing gate: the **owner** supplies the missing
  `proposed → ready` blessing by hand on `docs/build-plans/bp-002/plan.md` and
  `docs/build-plans/bp-003/plan.md` (owner-only, never in-session, §10); the **orchestrator** then
  flips `ready → complete`, seals each journal, and writes the PROGRESS checkpoints. An agent
  `proposed → complete` shortcut is deliberately NOT used — it would bypass the readiness gate
  (see finding-0009). bp-002's §14-parked pre-hoc `status: ready` denylist is a separate item,
  unaffected. Swept into the combined bp-002 + bp-003 seal checkpoint (`docs/PROGRESS.md`, 2026-07-06).

---

## oq-0003 — Ratify amendment A7: gate the *egress* from `proposed`, not just entry to `ready`?
- status: open
- origin: docs/findings/finding-0009.md
- blocking: false
- question: `gate-guard`'s `cmd_gate_check` denies only two destination values — a note `→ ratified`
  and a plan `→ ready` — by exact equality on the *new* status. Every other value falls through to
  ALLOW, so an agent editing a plan `proposed → in-progress` (or `→ complete`) directly reaches a
  build-implying state **without the owner's `proposed → ready` blessing ever occurring**. Same
  failure family as finding-0005/0006 (a bright line an ordinary edit silently bypasses). The finding
  proposes **A7**: gate the egress — deny an agent transition *into* `in-progress`/`complete` unless
  the on-disk `cur` is a legitimate predecessor (`in-progress` requires `cur ∈ {ready, in-progress}`;
  `complete` requires `cur == in-progress`), applied at `gate-guard` **and** both Stop-gate paths for
  A5 parity. Ratify A7 (owner-only, §10) so a builder can land the `_lib.py` change (as bp-002/bp-004
  did for prior amendments), or decline? The exact predecessor table is your ratification call; the
  finding names only the hole and direction.
- default_if_unanswered: A7 unratified; the hole stands (mitigated only by convention — the orchestrator
  never uses a `proposed → complete` shortcut, per oq-0002's enactment). Parks as finding-0009; re-entry —
  owner ratifies here, or a `direction` finding reports an ungated `proposed → {in-progress,complete}`
  flip actually occurring.
- answer:

---

## oq-0004 — Refresh the stale self-status on the BUILT & WIRED design-note cohort?
- status: open
- origin: docs/findings/finding-0010.md
- blocking: false
- question: A cohort of design notes carry self-status ("design only" / "not implemented" / "DRAFT —
  pending reconciliation") that understates code which is built, tested, and in several cases wired:
  `verdict-authority.md`, `vault-runtime-auth.md`, `skills-and-scope.md`, `attestation-layer.md`,
  `the-edge-model.md`, `the-sacred-boundary.md` (details + proposed completed-format front-matter in
  `docs/audits/corpus-state-audit-2026-07.md` §4). Because `/graduate` refuses any note not `ratified`,
  these cannot advance until their status is corrected **by hand at the blessing gate** (owner-only,
  §10 — the design-note surface is owner-gated even for a builder). Apply the audit §4 front-matter to
  this cohort? **Interaction:** bp-005 (in-progress) prepends *missing* front-matter at `status: draft`
  and explicitly never writes `ratified`; it targets notes *lacking* front-matter, disjoint from this
  cohort (which has stale-but-present status) — so the two do not collide, and `ratified` stays your
  hand in both.
- default_if_unanswered: the cohort keeps its stale status and stays ungraduatable. Parks as finding-0010;
  re-entry — owner applies the §4 status by hand, or a `/graduate` attempt is blocked by a stale
  non-`ratified` status on a note whose work is done.
- answer:

---

## oq-0005 — Apply the edge/supersession note↔code reconciliations (incl. the drafted `recursive-strata-amendment`)?
- status: open
- origin: docs/findings/finding-0013.md
- blocking: false
- question: Five citation-verified note/plan↔code contradictions in the edge/supersession area, several
  on load-bearing (Invariant-2-adjacent) partition claims: (1) `the-edge-model.md` §3 presents assertion
  authority as a per-edge typed field that doesn't exist — Item 7 realized it as store-identity; (2)
  `recursive-strata.md:45` cites a `SUPERSEDES` rel-type that was **removed** ("Do not re-add") — exactly
  the fix the already-drafted `recursive-strata-amendment.md` §1 makes, still unapplied; (3) "EdgeStore
  refuses supersedes" (edge plan + `build.py:149`) is literally false — the store accepts any `rel_type`;
  the real protection is *no writer + no handle* (sound, tested), so the wording invites a future edit to
  rely on a guarantee that isn't there; (4)(5) two stale status/tracking lines. Ratify+apply the drafted
  `recursive-strata-amendment.md` (§1/§5) and reconcile the three wordings at the blessing gate
  (owner-only — all fall on denylisted design-note/plan surfaces)? Item (5) alone (the `DERIVED_STRATUM`
  PROGRESS line) is orchestrator-writable and is being corrected in this triage's checkpoint.
- default_if_unanswered: the contradictions persist; the "store refuses" overclaim remains a latent hazard
  (a future edit could lean on a guard that isn't there). Parks as finding-0013; re-entry — owner applies
  the edits, or a builder relies on the false "EdgeStore refuses" guarantee.
- answer:

---

## oq-0006 — Close the Invariant-2 import-firewall asymmetry and confirm which CI enforces it?
- status: open
- origin: docs/findings/finding-0014.md
- blocking: false
- question: Invariant 2 ("network and private data never share a component; only `edge/` touches the
  network, never the vault") is enforced structurally by `ops/import_lint.py`, but asymmetrically:
  **core → edge/network** is comprehensively linted (test + a dedicated GitHub CI job), while
  **edge → core/vault** has no blanket static lint (only `edge/effectors/**` is narrowly barred; nothing
  stops `edge/interface`, `edge/monitor`, `edge/bridge` from importing `core`). Separately, `.gitlab-ci.yml`
  runs SAST/secret-detection/semantic-release but **no `import-firewall` job** — so if GitLab is
  authoritative, structural enforcement of this non-negotiable rides solely on the pytest integrity gate.
  Rule on: (a) add a `scan_edge` mirror barring `edge → core/vault` (the thinner-net, private-data-leak
  direction), and (b) which CI host is canonical + ensure `import-firewall` runs there (add to
  `.gitlab-ci.yml`, or confirm GitHub Actions is authoritative)? May graduate to a small builder task once
  ruled.
- default_if_unanswered: the one-directional lint stands; the edge→vault direction stays covered only by
  the pytest integrity gate on whichever host runs it. Parks as finding-0014; re-entry — owner rules, or
  an `edge/` module importing `core`/vault slips past because the authoritative CI didn't run the lint.
- answer:

---

## oq-0007 — Give the tracking surfaces an explicit *built vs deployed vs wired* distinction (a wiring board)?
- status: open
- origin: docs/findings/finding-0020.md (umbrella; facets: finding-0011, -0012, -0015, -0016, -0019)
- blocking: false
- question: Across the corpus, "complete" consistently means *built/deployed*, not *wired-into-the-live-loop*,
  but the terse summary surfaces (`CHANGELOG.md`, `README.md`, the archive Phase-10 roll-up) don't carry that
  distinction, so a reader materially overestimates the running system. Code-verified overclaims: "Phase 8
  Complete / research airlock (live)" — no live driver (finding-0019); "Vault Production … to access cloud" —
  nothing consumes Vault on the daemon; "WIRED ceiling ε = SENSING" — no effector wired at any tier
  (finding-0011); drift gauge A1 "keystone COMPLETE" — inert live, only the boot-time fingerprint conjunct
  runs (finding-0015); execution/agency substrate present but undriven (finding-0016); supersession/dialogue
  machinery dormant (finding-0012). The current `docs/PROGRESS.md` is itself honest/self-correcting; the
  overclaim lives in the summaries. Each of those findings offers an "OR annotate as dormant/not-wired" cheap
  path — this question is that shared decision. Introduce an explicit **built / deployed / wired** distinction
  — a dedicated wiring board, or annotate the summaries — and in what form? (The *building* of the missing
  drivers — Track D, A2, Item 8 — is normal roadmap sequencing, tracked separately, not this question.)
- default_if_unanswered: the summaries stay as-is; `docs/PROGRESS.md` remains the honest source and this
  triage's checkpoint records the specific overclaims in one place, but CHANGELOG/README still read as
  "wired." Parks as finding-0020 (with 0011/0012/0015/0016/0019 folded); re-entry — owner picks the
  annotation form, or a reader/agent is again misled by a summary surface.
- answer:

---

## oq-0008 — The research airlock: give it a design record, wire-or-defer its driver, and rule on the ahead-of-code Vault provisioning?
- status: open
- origin: docs/findings/finding-0019.md
- blocking: false
- question: The research airlock (BUILD-SPEC §16) is a substantial built + tested + **AWS-deployed**
  subsystem spanning four tiers (`core/research/*`, `edge/bridge/*`, `cloud/fetcher/*`, `cloud/terraform/*`)
  that the 2026-07 corpus audit missed entirely (its cloud tier was outside the audit's scope —
  finding-0018). **Not wired:** `build_bridge` raises without `[airlock] s3_bucket` (unset here); nothing on
  the live path calls `emit`/`collect`/`rank_literature`; the `"research"` router-kind has no handler.
  Separately, `ops/vault/policies/{correlator,dreamer}.hcl` provision a Vault `correlator` role reading
  `oura-daily-aggregates` for a biometric pipeline that **has no implementation** — deployed access for code
  that doesn't exist yet (a latent surface). Rule on: (a) give the airlock a design note (or an explicit
  BUILD-SPEC §16 cross-reference in the corpus index) so it isn't invisible to future audits; (b) wire the
  live driver (`research_criteria → emit → bridge → collect → rank_literature`) or explicitly defer it with a
  re-entry marker; (c) whether the correlator/biometric Vault provisioning should precede its implementation.
- default_if_unanswered: the airlock stays deployed-but-undriven and unindexed, and the ahead-of-code Vault
  role stays provisioned. Parks as finding-0019; re-entry — owner rules (a)/(b)/(c), or the next corpus audit
  re-misses the subsystem for lack of a design record.
- answer:

---

## oq-0009 — Catalogue or prune the orphan `docs/research/planar_graphs.md`?
- status: open
- origin: docs/findings/finding-0017.md
- blocking: false
- question: `docs/research/planar_graphs.md` is an external survey with **no implementation target** (grep for
  `planar|kuratowski|genus|planariz|fary|boyer|myrvold` across the source tree returns 0), is **not catalogued
  in `docs/README.md`** (which lists the other two research notes), and its "topology" framing name-collides
  with `core/complex/topology.py`, which implements a *different* body of math (persistent homology / Vietoris–
  Rips) — a genuine trip hazard given how central `core/complex/` is. Both research surveys are also statusless
  (no front-matter). Catalogue it in `docs/README.md` with an explicit "background reference, not a spec" line
  (as `un-represent-ability.md` already carries), or prune it? Optionally add minimal front-matter to both
  surveys for uniform headers. (bp-005 may add that front-matter under `docs/research/**` at `status: draft`;
  the catalogue-or-prune call is yours.)
- default_if_unanswered: the orphan stays uncatalogued with its name-colliding subject. Parks as finding-0017;
  re-entry — owner decides catalogue-or-prune.
- answer:

---

## oq-0010 — Ratify the provisional research-note front-matter convention (template + spec line)?
- status: open
- origin: docs/findings/finding-0023.md
- blocking: false
- question: bp-005 required front-matter on `docs/research/*.md`, but no research-note template or
  schema exists anywhere (`docs/templates/` covers design-note, build-plan, capsule, finding only;
  neither `BUILD-SPEC.md` nor `agent-workflow.md` defines a `type:`/id-prefix/field set for research
  notes). To complete without blocking (§5) the builder applied a **provisional convention** mirroring
  the design-note schema — `type: research`, `id: rn-<filename-slug>`, `status: draft`,
  `created`/`updated` from git history, `links: []`, `supersedes`/`superseded_by`/`warrant: null` —
  to the three research notes. Ratify it (add `docs/templates/research-note.md` + a line in the
  artifact-chain spec), amend it, or replace it? The three `rn-*` headers get a cheap reconciliation
  either way. **Secondary decision riding along:** for all 33 converted notes, `updated:` was set to
  each note's git last-commit date, not conversion date (a metadata-only migration shouldn't rewrite a
  note's recency) — confirm, or have it redone at the same cost.
  **Update 2026-07-10 (/triage):** the drift the finding predicted is already live — the new
  `docs/research/biometric-sensor-agent.md` (`38ccc85`) deviates from the provisional schema on three
  axes: `id:` lacks the `rn-` prefix, a novel `family:` field appears, and `created`/`updated` are
  absent (`supersedes: []` vs `null`). Each new research note without a ratified schema mints its own
  dialect; the reconciliation cost grows with every one.
- default_if_unanswered: the provisional convention stands, unratified. Parks as finding-0023;
  re-entry — owner ratifies/replaces here, or tooling starts keying on `type:`/id-prefix (the latent
  inconsistency the finding names).
- answer:

---

## oq-0011 — Ratify amendment A8: replace the design-notes *location* denylist with a *status*-aware guard?
- status: swept
- origin: docs/findings/finding-0025.md
- blocking: false
- question: The foundation denylist bars `docs/design-notes/**` wholesale, so *draft* notes — unblessed
  working material, same trust class as a build plan — are unwritable by any agent, structurally
  destroying the brainstorm → draft note → graduate flow the orchestrator exists for. The invariant
  actually worth protecting is **status**, not location: ratified/superseded notes agent-immutable
  (content and status, laundering-proof); draft notes writable under normal `write_scope`;
  `draft → ratified` owner-only, unchanged. **bp-005 proved the defect live:** its legal conversion
  could land only via an owner temp-lift of the global deny (`d6e518f`) that was then restored
  (`f5d435d`) — a hand-operated bypass, and while open, a hole in the very ratified-record guarantee
  the denylist exists for. finding-0025 specifies the guard precisely, including the two non-obvious
  requirements: a **content guard** in `cmd_scope_check` (gate-guard ALLOWs body-only writes that touch
  no status line, so it alone cannot protect ratified *content*), and a **HEAD-keyed Stop-side check**
  (post-hoc, on-disk status is the laundered value — compare against committed status, as
  `_blessing_in_diff` already does). Helpers exist (`is_design_note`, `status_of`); the other three
  denylist entries are untouched. Ratify A8 so a builder lands the `_lib.py` change with the six-case
  regression harness (finding-0025 §Disposition item 4), or decline?
- default_if_unanswered: the location denylist stands; agent draft-note authoring remains impossible
  except by per-episode owner temp-lifts. Parks as finding-0025; re-entry — owner ratifies here, or
  the next legal draft-note task forces another temp-lift.
- answer: **RATIFIED as A8** (owner's hand: edits 1+2 committed `8a5131e`, edit 3 `a19e030`,
  2026-07-11) and **IMPLEMENTED** same day (bp-010, `4fe6ad4`): status-aware guard live —
  draft-writable, ratified/superseded agent-immutable, HEAD-keyed laundering-proof, 11/11
  acceptance. finding-0025 → promoted. Swept to origin same day.

---

## oq-0012 — Ratify `type-system-as-core-audit.md`: give the code plane its missing enforcement?
- status: swept
- origin: docs/findings/finding-0026.md
- blocking: false
- question: `security-planes.md` composes three planes — types enforce the **code plane**, provenance
  labels the data plane, object capabilities the boundary — but the code plane is enforced by nothing:
  no type checker is installed or configured (`pyproject.toml` has no `[tool.mypy]`; dev deps are
  pytest/ruff/hypothesis; ruff's selected families lint style, not cross-boundary type consistency).
  The sharp point (finding-0026): the project already accepts and depends on promote-runtime-invariant-
  to-static-AST-proof — `ops/import_lint.py` does exactly that for I2 — yet applies it to no other
  invariant, while two invariants slated for TLA+/Alloy treatment (label monotonicity, capability
  non-amplification) have static shadows a checker would enforce at authorship time, free. The remedy
  note `type-system-as-core-audit.md` is drafted (committed `38ccc85`, `warrant: finding-0026`) as a
  conservative extension of `security-planes.md`. Ratify it at the blessing gate (by hand, §10) so
  `/graduate` can decompose its B-items, or decline? On ratification finding-0026 flips `→ promoted`.
- default_if_unanswered: the note stays `draft` and ungraduatable; the code plane stays enforcement-free
  and every builder session mutates `core/` under a weaker guarantee than the three-plane composition
  assumes. Parks as finding-0026; re-entry — owner ratifies/declines here, or a type-consistency defect
  in `core/` that a checker would have caught at authorship surfaces in a build session.
- answer: **RATIFIED** — owner hand-edited `status: draft → ratified` (2026-07-11, the blessing
  gate proper) and directed the mypy bootstrap to begin immediately. finding-0026 flipped
  `→ promoted`. The note's B-items are now licensed: B-1 (report-only audit) executed same day;
  B-2 (gate wiring) follows once both tiers are green; B-3 (static-shadow spike) per the note.
  Swept to the origin finding same day.

---
