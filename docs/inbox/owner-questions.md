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

## oq-0013 — Amend bp-012's write_scope with `ops/lifecycle/launcher.py` (one line) so Item 4 can register the store for reset?
- status: swept   # 2026-07-12 /triage — grant applied in bp-012 front-matter (owner-concurred comment in place); Item 4 landed + sealed; the trailing-comment parser wrinkle this exposed fixed by bp-014's §5 fold (`_scalar()`)
- origin: docs/build-plans/bp-012/plan.md §5 (scope amendment note) + §7 Item 4
- blocking: false
- question: bp-012 (B-b, the code-observation store) has Item 4 "reset registration" — the new
  `data/code_observations.sqlite` store is corpus-side (the observed stratum), so it must join
  `reset_targets()` in `ops/lifecycle/launcher.py` (Q4; the versions.sqlite/`bp-fix` sidecar precedent:
  reset targets are listed explicitly). But `ops/lifecycle/launcher.py` is NOT in bp-012's front-matter
  `write_scope` — only "the one `reset_targets()` line" is contemplated (§5 keeps the rest of
  `ops/lifecycle/**` out of scope). The plan defers the one-line scope amendment to you: add
  `"ops/lifecycle/launcher.py"` to bp-012's `write_scope`, and the builder lands Item 4 (one list entry +
  comment + an additive seed line in the existing reset test — the ONE permitted existing-test edit); or
  decline, and Item 4 parks with a finding (the store works but is NOT wiped on corpus reset until a later
  scoped plan adds it — the versions.sqlite defect class, a hygiene gap, not a correctness break).
  This is a capability grant, not a blessing gate — your call by hand on the plan front-matter (or a word
  here and the orchestrator adds the single line before spawning bp-012).
- default_if_unanswered: `ops/lifecycle/launcher.py` stays out of bp-012's write_scope; Item 4 parks with a
  finding and Items 3+5 proceed (the store + projection land; reset-registration deferred). Re-entry — owner
  adds the line (here or by hand), or a corpus reset is observed to leave `code_observations.sqlite` behind.
- answer: **YES — add it** (owner, 2026-07-11). `"ops/lifecycle/launcher.py"` added to bp-012's
  front-matter `write_scope` so Item 4 registers `data/code_observations.sqlite` in
  `reset_targets()`. Applied by the orchestrator (capability grant, not a blessing gate). This
  edit + answer were Bash-mediated: the finding-0031 pointer bleed (running bp-011 worktree
  builder set MAIN's active-plan pointer) falsely scoped the orchestrator to bp-011, so the
  Edit-tool scope-guard would deny these legitimate orchestrator writes — documented workaround
  per finding-0031's precedent. Swept when /triage runs.

---

## oq-0014 — Ratify `ci-platform-and-runner-strategy.md`, and rule D4 (release home = repo host)?
- status: swept   # 2026-07-12 /triage — ratification + D4(i) folded to origin finding-0034 (→ promoted); note ratified by owner hand; Plan A = bp-015 sealed, Plans B/C = bp-016/bp-017 ready
- origin: docs/design-notes/ci-platform-and-runner-strategy.md (promoted from finding-0034 + finding-0032)
- blocking: true   # the only working CI gate + the deploy-attestation path hang on it (GitLab minutes = 0)
- question: The runner/CI strategy note is drafted per your 2026-07-11 direction: GitHub Actions
  becomes the authoritative gate now (repo public → unlimited free; Gate-0 public-tree check
  CLEARED — see note §2); AWS Lambda MicroVM runners PARK on three named triggers (§4 D7);
  finding-0032's `needs:[]` closes as subsumed-by-construction (D6). Two asks: (1) ratify the
  note by hand (`status: draft → ratified`) so `/graduate` can mint Plan A (parity gate — the
  stale GitHub workflow is currently red-at-install on every mirrored main push), Plan B
  (witness re-point), Plan C (docs home). (2) Rule **D4**: `.releaserc.json`'s commit-back
  means the release host must BE the origin host — so either (i) **end-state, recommended:
  GitHub becomes origin** (release via workflow_dispatch, plugin swap, PR/branch CI unlocked),
  or (ii) **interim default: GitLab stays origin and you cut releases locally**
  (`npm run release`, zero minutes, no divergence). The diverging shape (GitHub-hosted release
  + GitLab origin) is forbidden either way.
- default_if_unanswered: the note stays draft and ungraduatable — the CI gate stays dead
  (GitLab 0 min; GitHub red-at-install), deploy stays hard-blocked (no attestable green), and
  pushing stays unconstrained. D4 defaults to (ii) interim. Parks on finding-0034; re-entry —
  owner ratifies here/by hand, or the monthly GitLab reset arrives and the metered leak resumes.
- answer: **RATIFIED + D4 = (i) END-STATE** (owner, 2026-07-11). The owner hand-flipped the
  note `draft → ratified` (the blessing gate proper) and ruled in-session: *"semantic release
  happens on the GitHub side — GitHub is shaping up to be the new home for releases and
  running CI tests."* So GitHub becomes origin per D4(i): release runs on GitHub
  (`workflow_dispatch`, witness-dispatched), `@semantic-release/gitlab → @semantic-release/github`,
  mirror reverses/retires, PR/branch CI unlocks. Plan B carries the release relocation (the
  note §5 anticipated this iff D4 ruled end-state); the origin re-point + mirror reversal are
  owner-console steps carried in Plan B as owner-steps with park conditions. Answer transcribed
  by the orchestrator (a ruling record, not a blessing gate — the gate was the owner's hand
  edit). Swept when /triage runs.

---

## oq-0015 — The ported `semgrep --error` gate is blocking and red on the existing tree (22 findings); keep blocking, or match GitLab's report-only parity?
- status: swept   # 2026-07-12 /triage — ruling (report-only, GitLab parity) already enacted + folded to origin finding-0037 (resolved) in the bp-015 seal session; 22-finding backlog persists there as triage backlog
- origin: docs/findings/finding-0037.md
- blocking: true   # gates bp-015's seal, and the bp-016 witness's definition of "attestable green"
- question: bp-015's first clean live CI run (sha `8d534a0`, run 29179448272) is **4/5 green** —
  `ratchet`, `type-gate` (the exact-69 mypy baseline holds on GitHub), `vault-axis` (the Vault
  service container works under host networking), and `gitleaks` all pass. **`semgrep` fails**: the
  scan completes fine (432 rules, 508 files) and reports **22 blocking findings**, and §6(f)'s
  `uvx semgrep scan --config p/default --error` makes findings fatal. The 22 are a pre-existing
  **audit backlog**, not a new regression — loopback `urllib` calls (one already `# noqa: S310`-annotated),
  internal-constant migration SQL f-strings (false-positive-in-context), two Terraform AWS hardening
  items, a Flask format-string, and — pointedly — a `mutable-action-tag` rule flagging our own
  `@v7`/`@v8.3.2` refs for not being SHA-pinned. None are exploitable sealed-core vulns. **The crux:**
  GitLab's SAST template is **report-only** (job exits 0; findings go to the MR widget), so the plan's
  deliberate `--error` choice made the GitHub gate **stricter than the original it ports**, and it was
  never verified green-on-clean before merge. I cannot resolve this in bp-015: fixing 22 code sites is
  out of scope (§9) and needs your judgment on acceptability; dropping `--error` is a gate-content change
  (§10). Three paths (detail in finding-0037): **(1) keep blocking + triage/suppress the 22** (nosemgrep
  the reviewed-intentional ones, SHA-pin actions, open follow-ups for the real hardening; code edits land
  in a separate scoped plan); **(2) match GitLab parity → report-only** (drop `--error`; restores true
  parity, loses the blocking guarantee); **(3) narrow/path-scope the ruleset** (may extend above p/default,
  never drop below it). Rule the direction (and, if (1), a suppression-policy sketch).
- default_if_unanswered: the `semgrep` job stays **parked** and red (it is one of five independent jobs —
  its red does not stop the other four greening; main's `ci` badge reads failing until ruled). bp-015 stays
  `in-progress` with semgrep parked; bp-016/bp-017 wait on bp-015's seal; deploy stays hard-blocked (no
  clean attestable green). Parks on finding-0037; re-entry — owner rules here, or a reader/witness is
  blocked by the persistently-red `semgrep` job.
- answer: **REPORT-ONLY — match GitLab parity** (owner, 2026-07-12, via AskUserQuestion). Drop
  `--error` so semgrep reports findings in the log but does not fail the pipeline — exactly the
  GitLab SAST template's non-blocking behavior; restores true parity (the `--error` blocking was
  the plan's over-reach beyond the ported original). The 22 findings are preserved in finding-0037
  as a triage backlog (not lost, not fixed here). Enacted THIS session (a gate change now
  owner-authorized, not a unilateral one): `.github/workflows/ci.yml` semgrep step → report-only;
  finding-0037 → resolved; bp-015 re-verified 5/5 green + ratchet canary, then sealed. Swept to
  origin (finding-0037) same session.

---

## oq-0016 — Hand-repair three formatter-mangled spans in the now-ratified `dn-self-sensing`?
- status: swept   # 2026-07-12 /triage — owner repaired by hand (3a873c2) + permanently removed the formatter; answer self-contained, origin is the note itself (no finding to fold)
- origin: docs/design-notes/self-sensing.md (the ratification save, 2026-07-12; committed verbatim as 8deab2a)
- blocking: false   # renders broken in three spots; semantics still legible — P3 graduation proceeds regardless
- question: Your ratification save ran the editor's markdown auto-formatter. Most of the pass is
  benign (emphasis restyle, table realignment — kept), but three spans corrupted where `_italics_`
  collided with the underscores in `φ_code`/`φ_self`, and one paragraph list-ified because a
  continuation line began with `+`. A8 correctly denied agent repair the moment the status flipped
  (working-tree-keyed, laundering-proof — the guard did its job), so the blessed record is frozen
  as your hand left it and the repair is yours. The three spans, as they should read (backticking
  `φ_code`/`φ_self` and replacing the line-leading `+` with "plus" makes them formatter-stable, so
  a future save won't re-mangle):

  **§3.3 B-a** (now `φ*code … \_Falsifier: … *`):

  ```
  - **B-a** — interpreter-version supersession mechanics in the observation-store family
    (additive migration; `φ_code` inherits). _Falsifier: a re-projection under a bumped
    interpreter version either mutates rows in place or is silently ignored._
  ```

  **§3.3 B-b** (now `φ*self … \_Falsifier: … *`):

  ```
  - **B-b** — `AgentSensingHandoff` + `AgentObservationStore` + `φ_self` over the cost
    stream; attested, idempotent per commit. _Falsifier: a second projection of the same
    commit changes row count; or any API surface accepts a provenance parameter._
  ```

  **Cross-references, first sentence** (now a broken bullet — rejoin to one paragraph):

  ```
  Verified in-session 2026-07-12: `core/sensing.py` (`SensingHandoff`; `CodeSensingHandoff`
  plus the Q1 sibling-precedent comment; `ObservedView` constructor-enforced observed-only);
  `core/stores/code_observations.py` (structural OBSERVED mint; `PRIMARY KEY (commit_sha,
  path, qualname)` + `INSERT OR IGNORE`; `projections` bookkeeping; SQLite Q2 note;
  ```

  (rest of that paragraph unchanged, de-indented back to column 0).
- update (2026-07-12, owner): **the markdown auto-formatter is permanently removed** — no future
  save can re-mangle. The three spans above are still owed a hand-repair (the note is ratified,
  agent-immutable), but the formatter-stability rationale is now moot: restoring the original
  spans verbatim is equally safe; the block above works either way.
- default_if_unanswered: the blessed record stays as-is — three spans render broken but read
  unambiguously; nothing downstream consumes the rendering. Re-entry: any future owner hand-edit
  of the note (fold the repair in), or the note's first supersession.
- answer: **REPAIRED BY HAND** (owner, 2026-07-12, same day). All three spans restored (§3.3
  B-a/B-b falsifiers, the Cross-references paragraph incl. its original `+` continuation —
  safe again with the formatter permanently removed), and the formatter's benign underscore
  restyling reverted to the original asterisk italics throughout. Committed verbatim by the
  orchestrator. Swept when /triage runs.

---

## oq-0017 — Pin a "side-effect audit before falsifier-demo runs" rule (finding-0039)? Plus a notice: your GitLab PAT was incidentally rotated.
- status: swept   # 2026-07-12 — owner accepted same day; amendment landed in build-plan SKILL.md §7, finding-0039 → promoted
- origin: docs/findings/finding-0039.md
- blocking: false
- question: bp-016's falsifier-demo run (the discipline that points a NEW test suite at
  the PRE-change module to show red) executed the old module's `rotate()` live — it
  rotated the real GitLab PAT as a side effect. Outcome benign (fail-safe ordering
  completed; no secret exposed; details in the finding), but the hazard class is real:
  pre-change code may hold live side-effecting functions, and the demo run executes
  them un-mocked. Proposed one-line amendment to the falsifier-demo discipline (lives in
  the build-plan/checkpoint skills): "before running any suite against a pre-change
  module, enumerate its live side-effecting functions and mock/skip them for the demo
  run." Ratify (or re-word) the amendment? Interim mitigation already active: the
  orchestrator now includes the side-effect audit line verbatim in every delegation
  prompt (bp-018/bp-021 onward, 2026-07-12).
  **NOTICE riding along (no action needed):** the Keychain `gitlab-api` PAT was rotated
  by that demo run — new token id 25599923, expires 2026-08-11, old value revoked
  server-side, stored + read-back verified. The plan's parked decision (you revoke the
  GitLab token at mirror retirement, Item 11c) is unchanged — there is simply a newer
  value in the same slot.
- default_if_unanswered: the prompt-level mitigation stands (orchestrator-enforced per
  delegation); the skill files stay unamended. Parks as finding-0039; re-entry — owner
  ratifies the skill amendment here, or a falsifier-demo side effect recurs despite the
  prompt line.
- answer: owner accepts

---

## oq-0018 — Delegated-parallel-builders + live tests: machine-global lock, scheduler policy, or accept the re-run fallback? (finding-0069)
- status: open
- origin: docs/findings/finding-0069.md
- blocking: false
- question: bp-023 landed the live-test lock (Item 12) and PROVED it correct — a
  server-log cross-reference showed exactly one endpoint cold-load during a two-process
  race, i.e. the fixture serializes two live tests in ONE worktree as designed. But
  Item 13's literal "both processes pass" flaked under a WIDER axis this plan could not
  reach: whole-machine RAM pressure from the *sibling builder worktrees* — i.e. THIS
  session's own decision to run bp-023/024/025 in parallel starved the shared physical
  Ollama daemon (server log: "predicted to exceed available memory, evicting …
  system_free=3.2 GiB"; two sibling worktrees' gate suites running concurrently). A
  single worktree's `write_scope` cannot install a lock spanning worktrees it may not
  write. So: the delegated-parallel-builders mode (now standard) introduces a
  cross-worktree, machine-capacity contention the repo-scoped lock doesn't cover. Which
  answer do you want — (a) a MACHINE-GLOBAL lock outside any worktree's write_scope
  (e.g. a scheduler-level or ~/.ollama-adjacent convention, keyed by endpoint hash,
  shared across worktrees); (b) a SCHEDULER/DELEGATE POLICY ("no two delegated builders
  run `-m live` concurrently" — a policy fix, encoded in the delegate skill, not code);
  or (c) ACCEPT the residual as the documented cost of parallel builders for the live
  tier, with finding-0046's "re-run before investigating" the permanent fallback for
  this cross-worktree case?
- default_if_unanswered: (c) — accept the fallback. Item 12's lock stands as the fix for
  the ORIGINALLY-MODELED class (one worktree's live tests racing, or a builder's suite
  overlapping the orchestrator's gate in the SAME checkout); the cross-worktree residual
  is documented and the CI gate never runs live tests anyway (`-m "not live …"`), so it
  does not gate merges. Re-entry — the live-flake tax under parallel builders becomes
  painful enough to warrant (a) or (b), or /triage promotes finding-0069 to a design note
  amending the delegate skill.
- answer:

---

## oq-0019 — bp-031 rename-stable identity: which `doc_id` mechanism? (the A6 prerequisite)
- status: open
- origin: docs/build-plans/bp-031/plan.md §11
- blocking: false
- question: `dn-temporal-retrieval-algebra`'s A6 ruling made rename-stable note identity a HARD
  prerequisite (it gates the diachronic reader / Result-1 H1 / β\*-over-lineage), and bp-031 is the
  FIRST graduated plan. The note deliberately left the *mechanism* open ("front-matter uuid **or
  equivalent**", `supersession-lifecycle.md:290`), so graduation parked it rather than infer it (A4).
  Two grounding facts sharpen the choice: (1) the `versions` store is ALREADY keyed on a generic
  `doc_id` column (`versions.py:54`) — today `sync.py:112` just passes `source_path` as that id, so the
  version schema needs NO change; (2) `parse_note` ALREADY extracts `id::`-style properties into
  `parsed.properties` (`logseq.py:19,64`) — reading an EXISTING Logseq page id is zero-new-code and
  zero-vault-mutation. The open question is what to do when a note has no id: (A) read an existing
  `id::` when present + detect renames by EXACT-CONTENT match on rescan, and do NOT mint into the vault
  (non-mutating, deterministic, but rename+edit falls back to a new lineage); (B) MINT an `id::` into
  every note's front-matter (guarantees stability incl. rename+edit, but WRITES the owner's authored
  corpus — a vault mutation); or (C) an external-only `doc_id ↔ source_path` map with no rename
  detection (adds a store but leaves the same rename gap as A without A's content-match coverage).
  Which mechanism? (bp-031 Item 1 — the additive `doc_id := source_path` foundation — is
  mechanism-agnostic and buildable regardless; only Items 2–3, the resolution + rename carry-forward,
  wait on this.)
- default_if_unanswered: (A) — existing-`id::` + exact-content rename detection on rescan, NO
  mint-into-vault. It is deterministic, non-corpus-mutating, and exact for the common case
  (rename-without-edit); rename+edit degrades to a new lineage, which is no worse than today. Parks as
  bp-031 §11; re-entry — owner rules here at `proposed → ready`, or a measured rename+edit frequency
  warrants escalating to (B) mint-into-vault (which makes it exact but requires an explicit vault-write
  grant).
- answer: **(B) — mint a stable `id::` into each note as the durable identity (owner ruling,
  2026-07-14).** _[ORCHESTRATOR DRAFT at owner direction; owner confirms by flipping `status: open →
  answered`.]_ Rationale: B is the only mechanism exact in **all** cases, including rename+edit (A/C fork
  there); it is idiomatic to Logseq (`id::` is native); and it is the "front-matter uuid"
  `supersession-lifecycle.md:290` named first. The cost — a deliberate, one-time write into the authored
  corpus — is accepted as an owner-gated operation. **Sequencing (nothing blessed changes):** bp-031 stays
  the foundation, unchanged — Item 1 decouples `doc_id`; Item 2 resolves `doc_id` from an existing `id::`
  when present (content-match belt-and-suspenders for not-yet-minted notes) — a superset-compatible base
  for B. The mint is a **separate owner-gated migration plan (bp-034, `depends_on: bp-031`)** whose
  load-bearing step is the **version/catalog re-key** (`UPDATE … SET doc_id = <minted id> WHERE doc_id =
  source_path`): the digest change alone does NOT preserve lineage across the identity switch — the version
  store is append-only and keyed by `doc_id`, so resolving from the new id without a re-key forks at the
  transition. The migration is dry-runnable on a copy, idempotent, reversible, and triggers a one-time
  corpus-wide "id added" amendment (one new version per note); it is RUN deliberately by the owner (the
  purge/deploy pattern), never in a build session.

---

## oq-0020 — Covering-only `supersedes` as a checked A6 invariant? (dn-magnetic-laplacian decision 3)
- status: open
- origin: docs/design-notes/magnetic-laplacian.md § Owner rulings (decision 3)
- blocking: false
- question: The magnetic-Laplacian pass (Q1c) surfaced a cheap data-integrity rider: rule that
  `supersedes` front-matter declares **covering** relations only (no transitive shortcuts — i.e. never
  `supersedes: [P, P′]` where P′ already supersedes P), and add the check beside F2 in the A6 invariant
  list (`recursive-strata-amendment`). Payoff: it keeps the Hasse supersession skeleton **triangle-free**,
  which the magnetic operator (if ever built) requires and the diamond census prefers. Cost: constrains
  authoring practice slightly + one cheap checker. Adopt it as a checked invariant? (Rec: adopt.)
- default_if_unanswered: adopt — near-zero cost, keeps the skeleton clean, and the check is a small
  additive validator. Parks as `dn-magnetic-laplacian` decision 3; re-entry — owner rules here, or a
  transitive-shortcut supersession is observed in the corpus and forces the question.
- answer: adopt

---

## oq-0021 — Dream-narration vocabulary for the arrow-aware census? (dn-magnetic-laplacian decision 2)
- status: open
- origin: docs/design-notes/magnetic-laplacian.md § Owner rulings (decision 2)
- blocking: false
- question: The arrow-aware combinatorial census the magnetic pass licensed (directed influence cycles on
  `X_cite`, revision-effort asymmetry / unbalanced diamonds, retro-citations) is exact and mirror-safe.
  Does this claim family enter the **dreamer's narration**, and with what language? This extends the
  standing `dn-edge-dynamics` §5 vocabulary question — a taste call, not a correctness one. Costs nothing
  until a lens/narration plan exists.
- default_if_unanswered: defer — no narration vocabulary is committed; the census computes its exact
  invariants (via the Thread-C sweep) and emits nothing about dreams until a lens plan is proposed. Parks
  as `dn-magnetic-laplacian` decision 2 (with `dn-edge-dynamics` §5); re-entry — owner rules here, or a
  directed-census lens plan is graduated and needs the vocabulary decided.
- answer:

---

## oq-0022 — Concur with the `workflow` node-kind ruling for the citation graph, and mint the follow-up plan? (finding-0065)
- status: open
- origin: docs/findings/finding-0065.md
- blocking: false
- question: The doc→doc citation scan excludes build-plans (bp-026 §6c pinned "`docs/**`" but landed
  as `_CORPUS_DIRS` = design-notes/findings/brainstorms only), so a plan's `design_ref: dn-…` mints no
  edge and nothing targets a build-plan — exactly finding-0059's motivating pain (a note's stale count
  cited by build **plans**). A 2026-07-13 fable ruling (tier-verified) settled the shape: **add a
  distinct `workflow` node kind** (build-plans as source + target) rather than widen `corpus` — folding
  process artifacts into `corpus` would make the kind-name lie and erode the §2.4 "corpus-structural, not
  observed exhaust" boundary; and "`docs/**`" was a scope typo (it sweeps templates/archive/book). Two
  non-blocking follow-ups: (1) shape `dn-core-query-protocol`'s kind vocabulary `{code, corpus, workflow}`
  at its already-owed pre-ratification vet; (2) a small plan (warrant finding-0065) — `KINDS`/`DIRECTIONS`
  + a path→kind classifier + scan/target-regex widening + a build-plan source in the grep-oracle
  acceptance (the exact gap) + the additive backfill (a strict superset → INSERT-OR-IGNORE no-ops, in an
  owner-coordinated finding-0066 window). Concur with the `workflow`-kind ruling + mint the plan when a
  graduation slot opens?
- default_if_unanswered: proceed with the `workflow`-kind ruling (option 2-narrow); the follow-up plan
  waits for a slot. The v2 store is live + correct for the authored-corpus graph. Parks as finding-0065;
  re-entry — owner concurs here, or a consumer needs plan-cites-note edges (finding-0059's pain) badly
  enough to prioritize the plan.
- answer:

---

## oq-0023 — Strip metadata property lines before embedding: `id::` only, or all `key::` page-properties? (finding-0077)
- status: swept   # MOOT — already resolved by bp-036 (sealed) before this was batched: strip_properties
                  # removes ALL key:: props (core/ingest/pipeline.py:33,57) + owner re-embedded 2026-07-14.
                  # /triage-8 batched this without checking bp-036; closed at the 2026-07-15 σ-scoping pass.
- origin: docs/findings/finding-0077.md
- blocking: false
- question: The bp-034 `id::` mint MEASURABLY changed the mirror similarity graph. An A/B on the owner's
  13-note corpus through the real `qwen3-embedding:4b` embedder: the shared `"id:: "` prefix + random
  uuid lifted borderline pairs over σ (mirror edges @σ=0.62: **5 → 9, +4/−0**; per-note centroid drift
  mean 0.953, min 0.891). The dreams now partly cluster on IDENTITY METADATA, not content — a quality
  regression on the semantic layer (not data loss; the mint's rename-stability purpose is intact). The
  fix is additive with no rollback: strip metadata property lines from the DERIVED/embedded text
  (`logseq.py`/`index.py`), leaving raw + the authored file byte-identical, then re-embed from raw (§8,
  regenerable). Scope call: strip **`id::` only**, or **all `key::` page-property lines** (they are
  uniformly metadata, not authored prose)? Then a small ingest plan graduates (strip-props-before-embed
  + re-embed-from-raw).
- default_if_unanswered: strip ALL page-property (`key::`) lines — they are uniformly metadata, not
  prose; the broadest strip restores a content-only graph and forecloses the same regression from any
  future property. Parks as finding-0077 / bp-034 parked-decision-4; re-entry — owner rules scope here,
  then the ingest plan graduates. Until then the live mirror graph carries the +4-edge artifact.
- answer:

---

## oq-0024 — Re-tune σ (dreaming threshold) on the clean graph, and build a σ-sweep harness? (finding-0079)
- status: open
- origin: docs/findings/finding-0079.md
- blocking: false
- question: σ = `dreaming.similarity_threshold` = 0.62 was implicitly calibrated on the id::-polluted
  graph (finding-0077). Removing the properties dropped all pairwise cosines ~5%, so the SAME σ is now
  materially STRICTER and under-clusters genuine themes: the art/creation cluster (content cosines
  0.46–0.57, thematically real but artifact-driven before) and two near-core recursion notes (0.005–0.018
  below σ) are now dropped. Two asks: (a) the σ value — a candidate **~0.56–0.58** recovers the art theme
  + the near-core notes; (b) whether to build a proper **σ-sweep harness** (mirror `reembed_bodyonly`)
  that sweeps [0.55, 0.75], records the graph + resulting dreams at each step, and picks σ by the curve —
  evidence-based + repeatable when the embedder/corpus changes — rather than this session's one-off N=13
  gauge. A config tune (`config/local.toml` / `levers.toml`) is owner-gated, never auto-modified.
- default_if_unanswered: keep σ = 0.62 until the owner runs/reviews a sweep — a single-guess retune risks
  over/under-clustering the other way. Parks as finding-0079; re-entry — owner sets σ here (and rules on
  the harness), or the dream layer's missed-theme cost (the art cluster) becomes painful enough to tune.
- update 2026-07-16 (finding-0087, from the E3a graduation grounding): the σ-sweep harness now has a
  concrete WHICH-KNOB fork that must be decided BEFORE the harness can produce a meaningful σ curve. The
  BUILT `ShadowRunner` computes dream_v2 from `[dream_rnd].sigma` (unregistered), while the registered
  lever is `[dreaming].similarity_threshold` = 0.62 (this oq's σ) — and the runner only *fingerprints*
  `[dreaming]`. So a sweep over the registered lever yields flat curves against the runner. The fork
  (finding-0087): (1) register `[dream_rnd]` knobs as levers [orchestrator's lean — most faithful here];
  (2) fix ShadowRunner to read `[dreaming]`; (3) widen the sweep grammar past the lever registry [weak].
  This BLOCKS graduating E3a-1 (bp-046 reserved); E3a-2 (bp-047) + E6 (bp-048) graduated regardless.
- answer (2026-07-16, the WHICH-KNOB fork only): owner chose **register the `[dream_rnd]` knobs as
  levers** (finding-0087 option 1) — the sweep varies what the runner reads, every swept knob stays a
  registered lever inside the §14 gate. E3a-1 (bp-046) graduates against this next session. The σ VALUE
  (part a) + the final σ pick REMAIN open — the sweep harness is what will determine them; this oq stays
  open on that axis until the owner reviews the first σ sweep.

---

## oq-0025 — `dn-core-query-protocol` note-erratum: annotate the ratified note by hand, or leave the finding as the standing erratum? (finding-0080)
- status: open
- origin: docs/findings/finding-0080.md
- blocking: false
- question: Ratified `dn-core-query-protocol` (`implementation: design-only`) is overtaken by the live
  code on two facts: (1) its frontmatter says the reference substrate is **61k edges** — the live store
  now holds **~272k** (corpus_to_corpus ~73k); (2) §3.1 names the doc→doc extractor as the "recommended
  *first* graduation," but the sensor **already mints** doc→doc edges — bp-035's `ReferenceView` oracle
  measured the graph at doc→doc recall **227/228 = 0.996** (vs the note's stale **0/16** hand-demo). The
  note is ratified → **immutable (A8)**; it is never hand-edited to "fix" this — finding-0080 IS the
  standing-erratum channel (the same discipline supersession uses; the discredited claim stays
  inspectable, bp-035 carries the corrected plan-of-record). Decision: **annotate** the ratified note by
  hand (owner-only — a dated "superseded by finding-0080" pointer), or **leave** finding-0080 as the
  erratum of record?
- default_if_unanswered: leave finding-0080 as the standing erratum (the note stays frozen per A8; bp-035
  is the corrected plan-of-record). Parks as finding-0080; re-entry — owner annotates the note by hand,
  or a book chapter / downstream design is about to cite the stale 61k / extractor-first framing.
- answer:

---

## oq-0026 — `dn-evaluation-harness` note-erratum: `implementation: not-built` is now stale (milestone-1 code-complete) — annotate by hand, or leave PROGRESS as the standing erratum?
- status: open
- origin: docs/build-plans/bp-042/plan.md §4, bp-043/plan.md §4, bp-044/plan.md §4 (batched on completion, the bp-039 pattern)
- blocking: false
- question: Ratified `dn-evaluation-harness` carries frontmatter `implementation: not-built`. That is now
  overtaken by the code: **milestone-1 is code-complete** — E1 (bp-042 eval-results store + registry),
  E2 (bp-043 run ledger + shadow runner), E4 (bp-044 report generator + cost ledger), and E5(A2) (bp-045
  SnapshotStore-into-build_dreamer) are all BUILT + SEALED. The harness §3 decomposition still lists them
  as pending, and §2.2/§2.6 describe several surfaces as "NOT built" that now exist. The note is ratified
  → **immutable (A8)**; it is never hand-edited to "fix" this. Decision: **annotate** the ratified note by
  hand (owner-only — a dated "milestone-1 built; see PROGRESS 2026-07-16 + bp-042/043/044/045" pointer in
  the frontmatter or a header banner), or **leave** PROGRESS.md + the sealed plans as the erratum of record
  (same discipline as oq-0025 / finding-0080 — the note stays frozen, the plan board is the plan-of-record)?
- default_if_unanswered: leave PROGRESS.md + the sealed plans as the standing erratum (the note stays frozen
  per A8; the plan board is the built-reality-of-record). Re-entry — owner annotates the note by hand, or a
  book chapter / downstream design is about to cite the stale "not-built" / "NOT built" framing (the harness
  chapter is the likely trigger — book debt is growing).
- answer:

---

## oq-0027 — the Fable design pass shipped THREE draft notes with three different blessing stakes: ratification review requested (σ-fibers · Res(π) algebra amendment · cross-strata fork)
- status: ANSWERED (2026-07-16) — **ALL FOUR notes hand-ratified by the owner** same session
  (frontmatter flips observed on disk; the chat rulings in the answer field below are the recorded
  rationale, folded into the notes pre-flip). /graduate is unlocked per dn-global-event-clock §3.1;
  dn-cross-strata-dreamer's ratification licenses NO build by its own terms (G1–G4 still front any
  cross-strata plan).
- origin: the 2026-07-16 Fable+xhigh design pass on docs/brainstorms/cross-strata-and-multiscale-dreamers.md
- blocking: false (each note records its default-if-unratified; nothing waits)
- question: The pass split the brainstorm into three drafts, deliberately separable because their blessing
  stakes differ. Review in this order (independent decisions — any subset may ratify):
  1. **`dn-sigma-fibers`** (docs/design-notes/sigma-fibers-and-multiscale-dreaming.md) — Idea A, the
     ratifiable near-term half. Fiber object = the content-addressed CLAIM carrying its σ-support (parked
     (b), sharpened — bare-edge persistence proved degenerate ≡ cosine); pers(χ) = normalized support
     measure with a three-clause falsifier incl. an exact grid-free oracle (the pipeline is piecewise-
     constant in σ with breakpoints at cosine values); a two-axis lexicographic surfacing gate
     (SETTLED/HUNCH/RETAINED; I1 untouched — surfacing only, never weight/promotion) F9-validated before
     shipping; zero schema change, zero models resident. Standard stake: new-subsystem design note.
  2. **`dn-resolution-result-typing`** (docs/design-notes/resolution-result-typing.md) — the HIGHEST
     stake: drafts an ADDITIVE amendment to the RATIFIED dn-capability-scope §2.3 (Inv/Rate(κ) →
     +Res(π), Rule SCALE). The verdict: σ-persistence is neither Inv (it rescales under a change of
     declared σ-range — the A7 ruler-confound) nor Rate (no clock), and scale must NOT become a scope
     coordinate (proved: every σ reads identical rows under the identical MirrorView grant — capability-
     invisible). Rejecting it is safe: dn-sigma-fibers records the fallback (register as Inv + grid in
     spec_hash + comparability string — weaker typing, identical arithmetic).
  3. **`dn-cross-strata-dreamer`** (docs/design-notes/cross-strata-dreamer.md) — Idea B, the fork that
     sits NEAR an inviolable: ratification of THIS note IS the human decision the founding capsule parked.
     Ruling drafted: firewall stands as written (MIRROR_READABLE untouched); the cross-strata dreamer is a
     correlator-family interpreted-tier client class with an owner-declared read-exemption from ι_MR;
     the type system ALREADY forces the pairwise per-stratum shape (SliceError + NoCommonClockError —
     a unified snapshot is ill-typed until CS-a); ratification licenses NO build (gate chain G1–G4:
     verdict taxonomy → Track D charter → cut discipline → mirror-dreamer-value-first).
- default_if_unanswered: all three stay `draft` (agent-writable working material); the firewall default
  (nothing cross-strata reads anything) and single-σ selection (bp-049) remain the operative reality. The
  σ-sweep RUN (oq-0024) is unaffected and, once run, its retained cells are FB-1's first dataset whenever
  dn-sigma-fibers ratifies.
- update 2026-07-16 (same session, owner-extended charter): a FOURTH note joins the bundle —
  **`dn-global-event-clock`** (docs/design-notes/global-event-clock.md), the designed RE-ENTRY of the
  ratified algebra's CS-a + CS-b parks (the re-entry condition is met: dn-cross-strata-dreamer G3 is the
  named consumer). Ruling: N = the DERIVED causal event poset (Ev, ≼) — per-store total chains + reads-from
  reference edges (the built attestation auto-link, attestor.py:59-69, is the mechanized exemplar) +
  recorded program order; materialized READ-SIDE only — a write-side global sequencer is REJECTED
  STRUCTURALLY (it would couple the sealed core and edge zone through a shared synchronous component; the
  async handoff is deliberately the only coupling, #1/#2). Wall-time never generates order. Cuts =
  certified quiescent frontiers (commit ∧ trough-empty ∧ handoff-empty), typing Scope.cut and completing
  SLICE for non-repo strata. On ratification + build (GC-1..GC-4): the T-meet totalizes over registered
  clocks (NoCommonClockError narrows to genuinely-exogenous cases), CS-b's antichain windows are
  inhabited, (N,∗) the dilation space becomes queryable, CS-f re-binning becomes possible as
  re-measurement, and N_s materializes (the parked prerequisite of the locally-clocked superconnection +
  DD-1 anchoring). Ratifying this note IS the owner-blessed unpark of CS-a/CS-b — the highest-leverage
  item in the bundle after the Res(π) amendment. Corrections recorded: the temporal-clocks capsule's
  "op-seq is already the spine" gloss (op-seq is ONE store's chain); the eval store records NO append
  order (keyed only — its events order via references alone).
- update 2026-07-16 (final pass, same session): the whole temporal stack was audited against the spine
  (dn-global-event-clock §2.9 — TRA's dilation scoped per-stratum; A7's void-the-reading rule becomes a
  checkable window-purity spine predicate; TG-a's admissibility oracle = GC-3 cuts; the A-4 routing pin
  IS the chain/chain-less boundary; TRA's β-dial + TG's α-knob join Res(π) as inhabitants from RATIFIED
  notes — five total). One erratum filed: **finding-0090** (dn-temporal-geometry §2.1 "proper time =
  per-stratum event count, exactly" holds per CHAIN, not per stratum — standing-erratum channel, the
  ratified note untouched). **Recommended ratification order** (each unlock maximal; any subset safe):
  Res(π) → global-event-clock → σ-fibers → cross-strata. Full design/build/test path:
  dn-global-event-clock §3.1 (wave 1: FB-1 + GC-1 + the ratified velocity pair + the σ-sweep RUN;
  wave 2: GC-2 + FB-2; wave 3: GC-3 + GC-4 + FB-3; wave 4: the gated instruments, incl. uuid-identity
  before Track D).
- answer (2026-07-16, owner in chat — RECORDED; ratification itself remains the owner's hand edit of
  each note's `status:` frontmatter; the notes stay `draft` and /graduate refuses them until flipped):
  - item 2 (Res(π)) — **leaning YES**: "Res will give us a generic and powerful way to specify
    resolution, and it feels like at different resolutions, different processes could be visible."
    (The motivation is folded into the note, attributed.)
  - item 3 (cross-strata fork) — **YES, in GENERALIZED form**: "dreamers can be scoped to different
    strata layers, and different combinations, so the generalized answer would be yes — dreamers
    should be allowed to be scoped to use non-authored seeds; we can test it all." I.e. the fork
    resolves as: the firewall binds the MIRROR dreamer, not dreaming per se; scoped dreamers over
    non-authored / composed strata are grantable per-scope (the capability algebra is the mechanism),
    with the bounding conditions unchanged (interpreted-only output; MIRROR_READABLE untouched; the
    mirror dreamer stays authored-only; owner ratification the only authored crossing; the harness
    evaluates each scoped dreamer). Folded into the note as an owner-ruling block; XS-a updated
    (Σ-extent becomes per-grant, harness-tested, not a fixed list).
  - item 4 (global event clock) — **YES, with the named condition**: accepted as the derived,
    read-side, partially-ordered causal spine "as long as it can act as a bridge between clocks
    without sacrificing structure and zone separation." Condition mapped to the note's falsifiers:
    the bridge = GC-4 pullback meets (structure preserved: bit-identical on all previously-legal
    meets); zone separation = GC-N1 read-side-only (the sequencer rejection). Folded into the note.
  - item 1 (dn-sigma-fibers) — no chat ruling; ratified directly by the hand flip (observed on disk
    2026-07-16, same session as items 2–4's flips).

---

## oq-0028 — two ratified-note errata from the 2026-07-16 design pass: annotate by hand, or leave the findings as standing errata? (finding-0090 · finding-0091)
- status: open
- origin: docs/findings/finding-0090.md · docs/findings/finding-0091.md (batched by /triage 2026-07-17)
- blocking: false
- question: The 2026-07-16 design/build passes surfaced two note-vs-reality fidelity gaps in RATIFIED
  (A8-immutable) notes — each a `math` finding, non-blocking, implying NO code change:
  1. **finding-0090** — `dn-temporal-geometry` §2.1 asserts "proper time = per-stratum event count,
     exactly" because "each stratum's store is totally ordered." The `dn-global-event-clock` §2.2 store
     audit overtakes the premise: DuckDB stores (eval, telemetry) carry no append chain at all, and
     chained stores are per-KEY chains (per-doc `version_seq`), so a stratum's restriction is a union of
     chains — a partial order. Exactness holds PER CHAIN, not per stratum; the corrected statement is
     already carried by `dn-global-event-clock` §2.3/GC-N6.
  2. **finding-0091** — `dn-velocity-instruments` §2.2(a) pins `RotationReport` principal angles between
     two harmonic subspaces whose restricted complexes do NOT share an edge set, without naming the shared
     ambient space the SVD of `Qₐᵀ Q_b` lives in. bp-052 resolved it constructively (zero-embed both bases
     into the union edge space over the common nodes — the standard principal-angles construction; all
     pinned falsifiers pass, 6 tests green). The note and code now agree by the builder's judgment, not the
     note's letter.
  Both notes are ratified → immutable (A8); neither is hand-edited to "fix" this — the findings ARE the
  standing-erratum channel (the oq-0025/oq-0026 discipline). Decision, per finding (independent): for each,
  **annotate** the ratified note by hand (owner-only — a dated "superseded/clarified by finding-00NN"
  pointer), or **leave** the finding as the erratum of record?
- default_if_unanswered: leave both findings as standing errata (the notes stay frozen per A8; the corrected
  statements live in `dn-global-event-clock` (0090) and `core/temporal_view.py` + bp-052 (0091)). Parks as
  finding-0090 / finding-0091; re-entry — owner annotates a note by hand, or a book chapter / successor
  design is about to cite §2.1's exactness claim or §2.2(a)'s under-specified cross-space construction.
- answer:

---

## oq-0029 — bless the connectivity-instruments tranche `proposed → ready`, item-by-item (bp-059 · bp-060 · bp-061 · bp-062)
- status: swept
- swept: 2026-07-18 (triage) — MOOT / overtaken by events: the tranche was reconciled into core/graph (oq-0030 answer). bp-059 COMPLETE; bp-060/061/062 SUPERSEDED (re-mint against core/graph is a separate standing item). No blessing of the original proposed tranche is needed.
- origin: /graduate dn-connectivity-instruments (2026-07-17, session-24) — the owner's "build out what we
  have already designed" lead
- blocking: false
- question: The RATIFIED `dn-connectivity-instruments` note is graduated into four `proposed` build plans
  (all eval-side, read-side, model-free, disjoint write_scopes). This is the owner-only `proposed → ready`
  blessing gate — an agent may not flip it (`gate-guard` denies the Edit path; the Stop-gate audit catches a
  Bash-minted `ready`). Bless by hand (edit each plan's `status:` and record a `bless(...)` commit):
  1. **bp-059** (σ*/MST — the keystone; no deps) — `eval/harness/connectivity.py`. **~180k opus. BUILDABLE
     FIRST.**
  2. **bp-060** (the (σ,t) conductance profile + churn change-of-measure + reconnection) — depends on bp-059.
     **~200k opus.**
  3. **bp-061** (type-checked bridges + bidirectional arc search) — depends on bp-059 + bp-060. **~200k opus.**
  4. **bp-062** (the helix detector) — **GATED on uuid-identity** (D3). Item 10 (synthetic detector) is
     buildable now; item 11 (real-corpus π wiring) waits on uuid-identity. **~180k opus.** Default per your
     ruling: the whole plan waits behind uuid-identity; the surfaced option is to bless item 10 forward for
     early value (its correctness is fully provable on synthetic gain graphs).
  Each plan pins its interfaces inline, grounds against the six built substrate modules with `path:line`
  citations, and honors the run-1 findings (0096: NO golden_recall coupling — the falsifiers are structural,
  not recall signals). One load-bearing grounding fact carried in all four: `MirrorView` has no cut-restriction
  surface, so v1 pins to the latest certified cut (historical restriction is a parked `core/` prerequisite).
- default_if_unanswered: the four plans stay `proposed` (unblessed, unbuilt); no agent flips readiness. Parks
  as the tranche; re-entry — owner blesses one or more plans `proposed → ready` by hand, then `/build <id>`.
  bp-059 is the natural first bless (the keystone all three others consume).
- answer:

## oq-0030 — connectivity instruments re-derive `core/complex/` primitives: reconcile the design, or land-and-unify-later? (finding-0101)
- status: swept
- swept: 2026-07-18 (triage) — answered (A) reconcile; delivered by bp-065 (core/graph σ*/conductance on core/complex's Laplacian); finding-0101 promoted; dn-core-graph-instruments ratified.
- origin: bp-060 post-build review + owner dialogue (2026-07-17, session-26) — owner's "these are core
  graph instruments operating on the raw graph across strata" lead
- blocking: false (connectivity lane held; chat lane bp-063/064 proceeds regardless)
- question: bp-060's built `eval/harness/conductance.py` rolls its OWN Laplacian + diffusion-distance while
  `core/complex/` already provides them as first-class core primitives — `laplacian.py` (L=D−A),
  `spectral.py` (`diffusion_map` = diffusion distance at scale t, `fiedler` connectivity), `cut.py`
  (`conductance` Φ(S), `grounding_cut`), `curvature.py` (`most_negative_edges` = candidate cross-domain
  bridges = bp-061's job). Same graph: `core/complex/build.py`'s `build_complex(view: MirrorView)` derives
  its adjacency from the same cosine-over-notes source as `MirrorGraph.sim`. The tranche
  (`dn-connectivity-instruments`: bp-059 σ* merged, bp-060 conductance built-unmerged, bp-061 bridges,
  bp-062 helix) never reconciled with `core/complex/`. Full evidence + honest caveats in finding-0101.
  Two paths:
  - **(A) Reconcile first** — pause the connectivity lane, revisit `dn-connectivity-instruments` against
    `core/complex/` (build on / move beside the core primitives; re-graduate bp-060/061 as needed). Cheapest
    now (before bp-061/062 build); avoids cementing a second Laplacian across three plans. **Orchestrator
    recommends (A).**
  - **(B) Land as-is, unify later** — merge bp-060 (built + green on its branch), note the duplication, and
    schedule a dedicated "unify on `core/complex` primitives" plan afterward. Faster; risks calcification +
    bp-061/062 compounding it.
- default_if_unanswered: connectivity lane STAYS held — bp-060 unmerged (built + green on branch
  `worktree-agent-a1d5f2b78350b8586`), bp-061/062 unspawned. Chat lane proceeds (bp-064 after bp-063).
  Re-entry — owner picks (A) or (B). finding-0101 flips to `promoted` on (A) (a note amendment), or stays
  `open` linked to the unify plan on (B).
- answer: **(A) — reconcile immediately** (owner, in-session 2026-07-17: "I do not agree with that
  machinery being outside of the core"; architecture selected = new `core/graph/` reusing `core/complex`,
  eval thin wrappers; session switched to fable/xhigh and the refactor directed performed now). Recorded
  in `dn-core-graph-instruments` (draft; owner ratification pending); finding-0101 → promoted; bp-065
  staged for mint-on-ratification.

## oq-0031 — Connectivity/sweep instruments can't discriminate at 13-doc corpus scale: grow the corpus, defer validation, or accept "built-but-unvalidated"? (findings 0096/0097/0098; entangles oq-0024)
- status: open
- origin: docs/findings/finding-0096.md (+ 0097, 0098) — the σ-sweep-experiment run-1 results
- blocking: false
- question: The connectivity/sweep track is CODE-COMPLETE but its instruments have no discriminating
  power at the current 13-doc corpus. Concretely (run-1): `golden_recall` is SATURATED at 1.0 across
  the entire σ-grid (0096) — the sweep objective can't rank σ; SE-3 persistence-tiering does NOT rate
  SETTLED claims more real than RETAINED (0098) — tiering doesn't yet track owner-perceived realness;
  and SE-1's decision rules are ambiguous on a perfectly flat curve (0097). This is the reflection's
  "construction outran validation" pattern: the machinery is right, but nothing at 13 docs can PROVE it
  earns its place. It also blocks a meaningful answer to oq-0024 (the σ re-tune). Direction options:
  - **(A) Grow the corpus first** — make corpus growth an explicit track (more of the owner's own
    notes) so the metrics gain discriminating range, THEN validate the sweep/persistence instruments
    against real signal. Slower, but it's the only path that actually validates them.
  - **(B) Defer the connectivity-validation lane** — freeze the instruments as built-but-unvalidated
    (they're read-side, model-free, harmless off), park findings 0096/0097/0098 + oq-0024, and revisit
    when the corpus is naturally larger. Cheapest; accepts the instruments sit unproven.
  - **(C) Shrink the ambition to what 13 docs CAN show** — re-scope the sweep objective to a metric
    that isn't saturated at this scale (structural, not golden_recall), per finding-0096's own hint.
- default_if_unanswered: (B) — the connectivity-validation lane stays PARKED (instruments built, flags
  off, no harm), findings 0096/0097/0098 + oq-0024 park with it. Re-entry: the owner picks A/B/C, or the
  corpus crosses a scale where `golden_recall` de-saturates (the metrics regain range on their own).
- update 2026-07-18 (owner steer + live-state check): the owner reframed this — the richer corpus
  **already exists**, in the OBSERVED strata, not the 13 mirror notes. Live state: Ouroboros is UP
  (launchd, very active — code_observations ~1GB, code_snapshots ~1.1GB, reference_edges ~200MB, 676
  commits); but the VAULT note-corpus is still **13** files and **chat has NEVER been ingested**
  (`data/chatlog.sqlite` absent — the bp-063 sensor never ran). So the path the owner wants is (roughly
  a variant of A/C): **continue the connectivity track** to build the **scope/machinery for a privileged
  core reader / dreamer to access the full strata (or a chosen subset) WITHOUT widening MirrorView's
  scope** — that unlocks the already-large observed-strata data for the sweep/dreamer to test against,
  rather than waiting on 13 notes. DIAGNOSTIC also owed: why the mirror note-corpus is stuck at 13 while
  Ouroboros runs (owner expected more) — vault-sync not finding new notes, or none added? Verify next
  session. This effectively supersedes the pure A/B/C fork; oq-0024 stays parked under it.
- answer:
