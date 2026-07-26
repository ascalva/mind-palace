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
- status: answered   # 2026-07-26 — (B) stands (already enacted by bp-034); the membership-store route recorded as the successor mechanism
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
- answer: **(B) STANDS — and it is already ENACTED, which the owner's 2026-07-26 recollection
  reframes rather than reverses.** Two corrections to the state this entry recorded:
  **1. ⚑ This is no longer a pending choice. `bp-034` is `status: complete`** — the `id::` mint into
  the authored corpus already ran, and its consequences are on the record: it measurably shifted the
  mirror similarity graph (finding-0077: mirror edges 5 → 9 at σ=0.62), which is what forced the
  strip-properties-before-embed fix (bp-036) and, downstream, this session's σ retune (oq-0024). So
  the orchestrator draft below was never confirmed, but the world moved to (B) anyway.
  **2. The owner's recollection is substantively right, and it names a genuinely FOURTH mechanism.**
  Owner, 2026-07-26: *"didn't we argue something like the vector membership store would help us with
  identifying renames, like git, where after some threshold, its considered a new document?"*
  Verified: `docs/design-notes/vector-membership-store.md` exists and its model supports exactly
  this. Meaning lives in **membership** — which `(path, blob_sha)` versions contain an atom — and
  cross-path sharing is first-class (`:111-112`: *"one atom, two memberships … forks"*). ⇒ A rename is
  then **high overlap between two membership fibers across a path change**, and "after some threshold
  it is a new document" is git's own similarity heuristic (`-M`, 50% by default) expressed in the
  membership model. The note itself frames the design as *"git's content-addressed model, one level
  down"* (`:24`).
  **Why that matters even though (B) already shipped:** the membership route needs **no `id::` in the
  authored corpus at all** — it derives identity from content occupancy rather than from a stamped
  token. That is strictly better on the axis that made (B) expensive (a deliberate write into the
  owner's own notes, plus the embedding pollution it caused). It is the **successor mechanism**, not a
  live alternative: the mint is done and its lineage re-key is spent.
  **⚑ Two gates before it can be relied on, neither of which is close:** the note is `status: draft`,
  and it carries **`adversarial_review: OWED`** — the expert-panel gate the owner instituted on
  2026-07-23 (core + systems + math, BEFORE ratification). Nothing graduates until that panel runs.
  **Re-entry:** the adversarial review, then ratification, then a plan that derives rename/fork
  identity from fiber overlap; at that point the `id::` tokens become belt-and-suspenders rather than
  the mechanism, and whether to stop minting them is a separate, cheap decision.
  **Kept open on nothing** — this entry is answered; the successor work is tracked on the note.
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
- status: swept   # 2026-07-26 /triage — ruling ADOPT folded to origin (dn-magnetic-laplacian decision 3). The invariant currently HOLDS empirically: the G-A fiber survey measured supersession D at 19 docs / **0 triangles** ⇒ covering-only integrity clean. Still owed: the additive validator beside F2 in the A6 invariant list (`recursive-strata-amendment`) — a small plan, no gate.
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
- status: partially-answered   # 2026-07-26 — interim σ SET to 0.58 (owner-authorized); the sweep/benchmark axis stays OPEN
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
- answer (2026-07-26, part a — the σ VALUE, interim): **σ = 0.62 → 0.58**, owner-authorized:
  *"set it to a reasonable value for now, until we can perform another proper benchmark/experiment."*
  Applied as an **instance overlay** in `config/local.toml` `[dreaming] similarity_threshold = 0.58`,
  NOT to the shipped default — `config/defaults.toml:272` keeps 0.62 so a fresh clone and CI are
  unchanged, and reverting is deleting three lines. Registered lever:
  `config/tuning.toml:16 [tuning.dream_similarity_threshold]`.
  **Rationale for 0.58 specifically:** stripping `key::` property lines before embedding (bp-036)
  dropped every pairwise cosine ~5%, so the *same* σ silently became stricter than the value it was
  calibrated at. 0.58 gives back approximately that 5% — restoring the operating point rather than
  hunting for clusters. It readmits the two near-core recursion notes, measured at 0.005–0.018 below
  0.62 (≈0.602–0.615), so any σ ≤ 0.60 suffices.
  **⚑ CORRECTION TO finding-0079, which this ruling exposes:** the finding claims ~0.56–0.58
  *"recovers the art theme"*. It does not. The art/creation cluster sits at content cosines
  **0.46–0.57**, so it is not readmitted at 0.58, nor at 0.56, and only its top sliver at 0.57.
  Recovering that theme needs σ ≈ 0.50 — **below the documented bound σ ∈ [0.55, 0.75]** for this
  embedder (`config/defaults.toml:268`, gap G7). So either the art theme is not a σ problem, or the
  bound is wrong; both are questions for the sweep, and neither is settled by picking a number.
  **Timing note:** the daemon is DOWN, so nothing recomputes until `palace up` — the change takes
  effect on the next dream run, and the existing graph is untouched until then.
  **⚑ THIS OQ STAYS OPEN** on part (b): the σ-sweep harness (bp-046, gated on the WHICH-KNOB answer
  below) is what replaces this judgement with a curve. 0.58 is an operating point, not a finding.

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
- status: swept   # 2026-07-26 /triage — all four notes hand-ratified by the owner 2026-07-16; answer is self-contained, nothing left to fold. (Do not confuse with oq-0032, which batched two DIFFERENT drafts.)
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
- status: resolved
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
- answer: RESOLVED 2026-07-19 (session-32, bp-073 Phase Δ; finding-0113, owner-blessed). The owner's
  2026-07-18 steer was exactly right: the richer corpus already exists. Δ measured over the
  **dialogue-artifact** strata (208 docs carrying C-edges, embedded eval-side) — NOT the 13 mirror
  notes — feeding bp-071's proven C-edges as E_proven into D3's ComposedGraph. Verdict: the 13-doc
  saturation was **input-starvation, not a real ceiling** — at n=208 the connectivity gauge already
  discriminates under E_sim alone; E_proven adds a real second lever via σ*-uplift (+0.74 at σ=0.7).
  So the connectivity instruments DO earn their place at adequate corpus scale (option A/C, realized
  via the observed/dialogue strata rather than growing the mirror). Findings 0096/0099/0100 resolved
  directly; 0097/0098 resolved root-cause (the optimizer-rule hardening is a separate future finding).
  **oq-0024 (the σ re-tune) is UN-blocked** — it was gated on this; a fresh sweep on the 208-doc corpus
  can now discriminate σ. Diagnostic owed (why the mirror is stuck at 13) is a separate, still-open
  thread — NOT re-blocking, tracked independently.

## oq-0032 — Ratify the two session-39 draft notes (dn-fiber-geometry · dn-inner-outer-core), and rule the taste calls each carries
- status: swept   # 2026-07-26 /triage — both session-39 notes ratified by the owner's hand at `fbea48d` (dn-fiber-geometry · dn-inner-outer-core). ⚑ Its two PROSE RESIDUALS are not dropped: the headless-daemon-secret-bootstrap ratification and the finding-0125 Opus re-read are now batched explicitly as **oq-0041** and **oq-0042**.
- origin: session-39 (2026-07-21) — the dreamer track build wave + the fable synthesis pass
- blocking: false
- default_if_unanswered: both notes stay `draft`; `/graduate` refuses them; the next build waves
  (fiber-geometry's G-A survey; inner-outer-core's M0 + S1) do not mint. Nothing stalls a running
  builder — the dreamer track is complete and everything downstream is design-gated on these
  blessings, so an unanswered question simply PARKS the two waves with an obvious re-entry (the
  owner ratifies when ready). Park condition: revisit at the next design/ratify session.
- question: Two draft notes are on `main`, each needing a hand `draft → ratified` flip plus one or
  two embedded taste decisions:
  1. **dn-fiber-geometry** (dada719) — the fable synthesis (one typed graph; grammar/geometry/
     dynamics layers; clock-curvature ruled Layer-1; sheaf-coupling refuted; ML-d declined).
     Ratifying it (a) adopts the framework, (b) resolves finding-0140 (the S/F/D/C alphabet fix →
     flips to `promoted`), (c) licenses the read-only **G-A survey** (the M1–M10 measure-first
     battery). Embedded taste calls (§5, non-blocking — M10 data informs both): is a citation (F)
     an admissible grounding terminal, i.e. does `S*·(C|D)` extend to `S*·(C|D|F)`? and should a
     chain crossing a node superseded at the read's cut be *hard*-required to narrate its D-context
     (a candidate new hard production)?
  2. **dn-inner-outer-core** (7a532f0) — v2 predicate + the S1 temporal-math splits (both already
     inside from earlier this session). One open taste item: the physical directory name for the
     inner ring (`core/kernel/` proposed). Ratifying licenses M0 (the born-green ring) + S1.
  Also still owed before ITS ratify (tracked separately, not part of this oq): re-examine
  `dn-headless-daemon-secret-bootstrap` as an OPUS product (finding-0125 residual) — it was
  reported as a fable pass but composed on Opus.

## oq-0033 — structural model-per-phase: graduate a plan off the `transcript_path` model-id path, or keep P-WF1 parked?
- status: open
- blocking: false
- origin: docs/findings/finding-0155.md (the P-WF1 probe, bp-097 Item 7)
- question: The P-WF1 probe (finding-0155) found the running model id is NOT directly exposed to
  hooks (no env var; PreToolUse stdin has no `model` field — only `CLAUDE_EFFORT=high`), but IS
  reachable INDIRECTLY via the payload's `transcript_path` → the last assistant message's
  `message.model`. That partially satisfies D7's re-entry condition. Do you want to graduate a NEW
  plan for structural model-per-phase enforcement (e.g. gate-guard refusing a *non-Fable*
  design-note **creation**) on that indirect path — accepting its fragility (a transcript
  read+parse on every PreToolUse hot-path fire; a race against the in-flight turn; coupling to an
  undocumented transcript schema; must fail-open) — or keep P-WF1 parked pending a first-class
  model-id field in the hook payload (worth an upstream ask)? Default recorded: keep parked; the
  procedural backstop (banner + usage-verify + board visibility) stands.
- park condition: revisit when you decide, or if a fable↔opus mismatch actually produces a
  wrong-tier design note before then.

## oq-0034 — Should code-ingest be ON by default (defaults.toml), not opt-in per-instance (local.toml)?
- status: swept   # 2026-07-26 /triage — ruling ENACTED and verified live: `config/defaults.toml:96-110` carries `[code_ingest] enabled = true` with the comment citing finding-0161/oq-0034; folded to finding-0146 (resolved this sweep).
- blocking: false
- origin: docs/findings/finding-0161.md (raised 2026-07-22, at the code-ingest enable step)
- question: `[code_ingest].enabled` ships `false` in defaults.toml; this Mac opts in via local.toml
  (like secrets/backup). You question that placement — code-ingest is NOT a security gate (unlike
  secrets/backup), just fail-safe conservatism, and the Ouroboros is fundamentally about consuming
  itself, so ingesting its own code by default feels native to what mind-palace IS. The crux to
  weigh (finding-0161): defaults.toml is the FRAMEWORK default (every clone + CI); local.toml is
  THIS instance's posture — and ouroboros-naming already draws that line (framework = mind-palace,
  LIVE self-consuming system = Ouroboros), so the self-consumption thesis is arguably an INSTANCE
  property local.toml already expresses. Flipping defaults.toml asserts it for every clone/CI too —
  where there's no Ollama/daemon, and where "enabled" auto-embeds the whole tree on first
  housekeeping (cold store ⇒ incremental = full seed, the heavy-op-from-a-flag §2.7 was written to
  avoid). Middle paths exist: (a) keep OFF, just name the instance-ON as intentional; (b) default
  ON but gate the housekeeping auto-embed on "daemon+embedder present" (default-on-when-runnable);
  (c) an explicit "this is the Ouroboros instance" marker flipping instance-native defaults together.
- default_if_unanswered: status quo stands — defaults.toml OFF, this instance ON via local.toml
  (already live). Nothing is blocked; the deploy + seed proceed under the current opt-in. Parks as
  finding-0161; re-entry — you rule here, or the framework-vs-instance line is settled elsewhere.
- park condition: revisit when you decide; no builder waits on it.
- answer: DEFAULT ON (owner, 2026-07-22). Your own realization settled it — "gated off" here means a
  not-yet safeguard (off until ready; once on it stays on), not permanent conservatism. So the
  framework default should be ON: `config/defaults.toml [code_ingest].enabled = true`. Done this
  session (+ tests updated, the redundant local.toml opt-in removed). Safe because the daemon won't
  start without a live Ollama (preflight), so no clone/CI auto-embeds without an embedder. Owed
  (owner-hand): the dn-code-ingest-pipeline §2.7 "owner-visible seed" wording now coexists with
  default-on auto-seed-on-first-housekeeping — a ratified-note amendment for you. See finding-0161.

## oq-0035 — Graceful shutdown has no bound: bounded SIGKILL escalation, worker-enforced job budgets, or both? (finding-0171)
- status: open
- blocking: false
- origin: docs/findings/finding-0171.md (raised 2026-07-25, during the post-deploy incident)
- question: `palace down` returned success while the daemon kept running at 96% CPU. The graceful
  contract is SIGTERM → drain at the job boundary → exit, and the wedged `code_sync` job (the
  finding-0169 quadratic scan) never reached a boundary. `launchctl print` showed `active count = 1`
  pending on the process exiting; the projected natural exit was ~57 minutes away, at the job's own
  ~75-minute timeout. Resolution required `kill -9` with your authorization. This is a SAFETY
  property, not a performance one: the shutdown path's only working fallback is the ungraceful kill
  that the graceful design exists to avoid, and `deploy` shares the path (it calls `stop()` before
  waiting for the successor run, so a deploy issued during a wedge hangs and then reports
  `deploy: TIMED OUT` for an unrelated cause). Three ways to close it:
  (a) **Bounded drain with escalation** — SIGTERM, wait N seconds, SIGKILL; N configurable, the
  escalation logged and surfaced. Simple, conventional, guarantees termination. Cost: a killed job
  may lose in-flight work — concretely, `supersede_source`'s `delete → add` window can drop one
  path's rows (recoverable by re-embed from git, but genuine loss; tonight's kill missed that window
  by luck, verified after the fact).
  (b) **Worker-enforced job budgets** — each job carries a wall-clock budget the WORKER enforces
  from outside, so no job can exceed it and the drain boundary is always reachable. Fixes the class
  rather than the shutdown symptom, and pairs naturally with the lease/heartbeat parked in bp-101.
  Cost: needs a cancellation seam in the handlers that does not exist today.
  (c) **Both** — (b) as the real fix, (a) as the fail-safe behind it.
  The crux is whether an interrupted store write is acceptable to guarantee availability. That trades
  data integrity against a shutdown guarantee, which is your call, not a builder's.
- default_if_unanswered: no escalation is built. bp-102 Item 3 lands the HONEST-REPORTING half only
  (`down`/`stop` must not claim success while the process lives), which is builder-resolvable and
  needs no ruling. The operational knowledge stands in for the fix: **`down` may not stop a wedged
  daemon — check `ps` before trusting it.** Parks as finding-0171; nothing is blocked.
- park condition: revisit when you rule. No builder waits on it; bp-100/0101/0102 all proceed.
- answer: **(c) BOTH** — owner, 2026-07-25, verbatim: *"I like (c), feels like the most robust
  approach."* (b) worker-enforced job budgets is the real fix; (a) bounded SIGTERM → N → SIGKILL is
  the fail-safe behind it. Per `dn-supervision-and-liveness` (ratified 2026-07-25, `3945d9f`) the
  escalation is aimed **only at the WORKER, never at the supervisor** — killing the supervisor is
  what the lease/dead-man design makes unnecessary, and what would lose the landing step.

  ⚑ **The crux this question was originally framed on has DISSOLVED, and the ruling should be read
  in that light.** oq-0035 asked you to trade data integrity against a shutdown guarantee —
  *"whether an interrupted store write is acceptable."* The note's I1 survey (all 11 registered
  kinds) established that **no handler is irreducibly write-interleaved**, and that
  `ambassador_task` (`scheduler/interface.py:53-59`) **already** computes-then-returns while the
  supervisor lands the result (`scheduler/supervisor.py:94-95`). Under the compute/land split you
  never interrupt a write — you interrupt a *computation* and land nothing. So (c) does not buy the
  availability guarantee at the cost of integrity; single-writer gets **stronger**, because landing
  becomes a short atomic step the supervisor owns instead of an hours-long span it delegates.

  **Open implementation input, NOT a gate on this ruling — V3.** Does Ollama abandon its work when
  its HTTP client dies? If it does not, killing the worker stops the *accounting* but not the
  *burn*: the drain completes and the daemon exits (which is what this question actually asked
  for), but resource consumption continues on the Ollama side until that call finishes. (c) remains
  correct either way; V3 decides how much (a)'s half is really worth, and it is a direct argument
  for NEW NOTE 2 (llama.cpp-direct), where cancellation becomes ours to hold rather than to ask
  about. Not measured yet — see the note's V-series and finding-0199.

  Follow-through owed: reflect this ruling onto finding-0171, and carry it into
  `/graduate dn-supervision-and-liveness` (the escalation contract is OPS-4's design half).

## oq-0036 — What legitimises a COMMITTED `proposed→ready` flip that carries no grant record? (finding-0206; blocks one autopilot plan, not the graduation)

**Raised:** 2026-07-25, session-51, during the `/graduate` grounded pass on
`dn-autopilot-and-delegated-blessing` — *before* any plan was minted, which is where this class is
cheapest to catch.

**What the note assumed.** §2.3 says the Stop-gate clause (c) *"gains one narrow exception: a
committed `proposed→ready` flip is legitimate **iff** the same commit carries a grant record…"*.
Grounding says (c) never looks at committed flips at all — `.claude/hooks/_lib.py:826-833` and
`:852-858` both state it outright (*"a committed blessing … must self-clear"*, *"a committed
blessing (tracked, in HEAD) never trips it"*). So this is not an exception carved out of an
existing block; it is a **new, stricter post-hoc check** and a partial reversal of amendment A1.

**⚑ The part that actually blocks.** §2.3 ends *"All other agent-side flips remain violations"* —
but a commit carries no trustworthy agent-vs-owner signal. The author is you in **both** cases,
because our own blessing ceremony has the **agent commit your hand-made flip**. That is not
hypothetical: you ratified the autopilot note by hand this session and I committed it as `b27142d`.
So "committed flip, no grant record" is at once the signature of **every legitimate blessing you
have ever made** and of **the forgery the rule exists to catch**. Enforce it literally and your own
blessings read as unauthorized; relax it and the hole reopens.

**Options** (detail and trade-offs in `docs/findings/finding-0206.md`):

- **(a) Two legitimisers** — grant record **or** a genuine owner signature (commit signing, or an
  owner-side attestation over the flip). Closes it properly; costs friction in the by-hand ceremony
  you like precisely because it is frictionless.
- **(b) Scope the check to capsule-bearing plans only** — plans that never carried a capsule keep
  A1's committed-self-clears. Cheap; leaves the hole open for any plan an agent simply declines to
  give a capsule, which is every plan it would want to forge.
- **(c) Drop §2.3's post-hoc clause** — keep (c) uncommitted-only, check the grant tag at *use*
  rather than at Stop. Smallest build; gives up the offline post-hoc detection §2.3 wanted.

**Recommendation withheld.** This sits on a bright line (`CLAUDE.md:62`, NN-5), and the note is now
agent-immutable under A8 — so whichever way you rule, the note itself changes by a **superseding
note**, never an edit.

**park condition / blast radius:** deliberately narrow. Graduation proceeds now for every unit that
does not depend on the post-hoc rule — the verifier crypto, the capsule + templates, the P1–P5
predicate check, the `[autopilot]` config schema, the halt-list supervisor, the audit gates. **Only
the journal-gate / post-hoc-verification plan is parked**, and it is not minted until you rule. No
plan asserts the post-hoc rule as buildable before then.

- answer: **DEFERRED TO A FABLE DESIGN PASS — not an evasion, a tier call.** Owner, 2026-07-26:
  *"I don't actually know, and it may require a fable pass to get that tricky part right."*
  Recorded as the ruling on *how this gets decided*, not on the substance. Both questions sit on a
  bright line (`CLAUDE.md:62`, NN-5) and both are cryptographic/authority reasoning, which is exactly
  the "design / gates / scrutiny" row the tier table reserves the top tier for
  (`.claude/skills/context-economy/SKILL.md:33`).
  **Re-entry condition:** a Fable-tier session (owner re-tiers in place — the session cannot flip its
  own model, and this must NOT be delegated to a subagent: design-note work is never delegated, and a
  subagent cannot exceed its parent's model access, which is exactly how the finding-0125/0147
  "fable" passes turned out to be Opus products).
  **What is already grounded and must not be re-derived in that pass:** the externally-verified
  primitives (Apple passkeys are iCloud-synced P-256, NOT Secure-Enclave-bound — the real boundary is
  the OS user-verification gesture; **ES256 only**, so core's Ed25519 is not reusable; Shortcuts has
  no HMAC; a raw Tailscale IP origin fails WebAuthn even with valid TLS; `rpId` must be the full
  FQDN), and the 14 capsules in `docs/brainstorms/autopilot-mode.md` — several of which supersede
  earlier ones and say so.
  **Blast radius while parked (unchanged, deliberately narrow):** graduation continues for every unit
  that does not depend on these two; only the journal-gate/post-hoc-verification plan (oq-0036) and
  the verifier wiring/deployment plan (oq-0037) stay unminted. The verifier's **pure core** (HMAC
  derivation, the domain-separated attestation tag, capsule hashing, P1–P5 predicates) is testable
  with an injected secret behind a provider seam — the bp-115 shape — so the later decision is a
  config flip, not a rewrite.
  ⚑ **oq-0040 is the cheap half of oq-0036** and does NOT need the Fable pass: making `/graduate`
  commit the `proposed` mint gives every blessing a real tracked predecessor, which is a precondition
  for any post-hoc rule being enforceable at all.

## oq-0037 — ⚑ What actually stops the agent from reading the autopilot secret? (finding-0207; the design's load-bearing assumption)

**Raised:** 2026-07-25, session-51, during the `/graduate` grounded pass on
`dn-autopilot-and-delegated-blessing` — before any plan was minted.

**The assumption.** §2.3 / invariant 1: *"The shared secret lives in Keychain (NN-10); **the model
never sees it.** A small verifier script recomputes and compares."* That is the rule restated, not
a mechanism — and the whole design stands on it. The §2.3 HMAC attestation tag (the audit's best
catch, the thing that makes a grant record unforgeable rather than mere prose) is unforgeable only
relative to a secret the forger cannot reach.

**What grounding found — both obvious mechanisms fail.**

1. **Env-carried.** `core/kernel/config/loader.py:605-619` shows `get_secret(name)` is literally
   `os.environ.get(name)` — the repo's standing pattern is env-carried, Keychain-populated. But the
   verifier reads the secret *at invocation*, and **the agent is the invoker** (it runs
   `mfa-verifier --code …` after relaying your code). Secret in the invoker's env ⇒ the agent can
   read it.
2. **⚑ Keychain ACL pinning — fails for a non-obvious reason.** The natural fix is
   `security add-generic-password -T /path/to/verifier`. But §4 specifies the verifier as a
   **script**, and a script is not a binary: the ACL can only trust the **interpreter**
   (`python3`), which is exactly what the agent runs for everything else. Pinning the ACL to the
   interpreter grants the agent precisely what it grants the verifier.

**Measured safely** (names only, never values — NN-10 forbids a model reading or logging a secret):
your agent shell today carries **zero** secret-ish env var names; and the `security` CLI **is**
reachable non-interactively from it (a lookup for a deliberately nonexistent service returned
"item could not be found" — the search ran and was permitted). **This is not a live vulnerability**
— no secret, no verifier, nothing built. It is a gap caught at the cheapest possible moment.

**Options** (detail in `docs/findings/finding-0207.md`):

- **(a) The verifier becomes a separate actor** — a launchd service holds the secret in its own
  environment; the agent may only *drop a request* (capsule hash + code) and read a verdict, never
  run the code that holds the secret. Satisfies NN-3 structurally instead of by convention. Best
  fidelity to your intent; most build.
- **(b) Verification moves to the phone** — the phone holds the secret, verifies its own code, and
  pushes the flip + grant record. The secret never exists on this machine, so the question
  dissolves. Strongest; largest change, and entangles the parked phone-side work.
- **(c) State a weaker property honestly** — keep the script, and say plainly that the boundary is
  your Keychain ACL plus macOS's approval prompt: it resists a careless agent, not a determined
  one. Cheapest; but it means amending invariant 1 to say what it really guarantees, which is a
  constitutional change and must not happen quietly.

**park condition / blast radius — deliberately narrow, and graduation continues.** The verifier's
**pure core** (HMAC derivation, the domain-separated attestation tag, capsule hashing, P1–P5
predicate evaluation) is fully testable with an **injected** secret and needs no ruling; it is
planned now behind a provider seam — the same shape bp-115 used for the inference client, so your
decision later is a config flip, not a rewrite. **Only the wiring/deployment plan is parked**: what
actor runs the verifier, where the secret lives, and how invariant 1 gets *proven* rather than
asserted.

- answer: **DEFERRED TO A FABLE DESIGN PASS — not an evasion, a tier call.** Owner, 2026-07-26:
  *"I don't actually know, and it may require a fable pass to get that tricky part right."*
  Recorded as the ruling on *how this gets decided*, not on the substance. Both questions sit on a
  bright line (`CLAUDE.md:62`, NN-5) and both are cryptographic/authority reasoning, which is exactly
  the "design / gates / scrutiny" row the tier table reserves the top tier for
  (`.claude/skills/context-economy/SKILL.md:33`).
  **Re-entry condition:** a Fable-tier session (owner re-tiers in place — the session cannot flip its
  own model, and this must NOT be delegated to a subagent: design-note work is never delegated, and a
  subagent cannot exceed its parent's model access, which is exactly how the finding-0125/0147
  "fable" passes turned out to be Opus products).
  **What is already grounded and must not be re-derived in that pass:** the externally-verified
  primitives (Apple passkeys are iCloud-synced P-256, NOT Secure-Enclave-bound — the real boundary is
  the OS user-verification gesture; **ES256 only**, so core's Ed25519 is not reusable; Shortcuts has
  no HMAC; a raw Tailscale IP origin fails WebAuthn even with valid TLS; `rpId` must be the full
  FQDN), and the 14 capsules in `docs/brainstorms/autopilot-mode.md` — several of which supersede
  earlier ones and say so.
  **Blast radius while parked (unchanged, deliberately narrow):** graduation continues for every unit
  that does not depend on these two; only the journal-gate/post-hoc-verification plan (oq-0036) and
  the verifier wiring/deployment plan (oq-0037) stay unminted. The verifier's **pure core** (HMAC
  derivation, the domain-separated attestation tag, capsule hashing, P1–P5 predicates) is testable
  with an injected secret behind a provider seam — the bp-115 shape — so the later decision is a
  config flip, not a rewrite.
  ⚑ **oq-0040 is the cheap half of oq-0036** and does NOT need the Fable pass: making `/graduate`
  commit the `proposed` mint gives every blessing a real tracked predecessor, which is a precondition
  for any post-hoc rule being enforceable at all.

---

# ════════════════════════════════════════════════════════════════════════════
# BATCH — /triage session-52, 2026-07-26.  oq-0038 … oq-0048.
# Eleven questions from the four-session finding backlog (63 unswept findings
# re-verified against the tree this session). **None is blocking.** Each carries a
# default with a park condition, so leaving the whole batch unanswered costs you
# nothing but time. Every ID is glossed inline — you should never have to look one up.
# Suggested sitting order, because several genuinely sequence:
#   oq-0047 (ftype) → oq-0044 (two draft frames) → oq-0045 + oq-0046 (firewall pair)
#   → oq-0042 → oq-0041 (plane pair)  ·  oq-0040 with oq-0036  ·  the rest standalone.
# ════════════════════════════════════════════════════════════════════════════

---

## oq-0038 — Tidy `scripts/`, and does the package boundary apply to the eval-flavoured harnesses? (finding-0114)
- status: open
- origin: docs/findings/finding-0114.md (you flagged it mid-bp-072, 2026-07-19)
- blocking: false
- question: `scripts/` now holds **38 files / 4077 LOC** (up from 34 / ~2.8k when you flagged it),
  in three kinds. **Durable entrypoints:** `palace.py`, `cockpit.sh`, `docket.py`, `board.py`.
  **Spent one-off migrations** that already ran and are now archaeology: `migrate_chunk_keys.py`,
  `migrate_provenance_split.py`, `reembed_bodyonly.py`, `purge_raw.py`, `ingest*.py`,
  `snapshot_code.py`. **Substantial eval-flavoured harnesses:** `experiment.py`, `review.py`,
  `tune.py`, `sweep.py`, `report.py`, `verdict.py`, `fibers.py`, `eval.py` — which arguably belong in
  `eval/` under your own math→core / notebook→eval boundary. Nothing is broken; `CONVENTIONS.md`
  states no `scripts/` vs `eval/` rule at all.
  - **(a) Archive + relocate** — drawer 2 → `scripts/archive/` (or delete; git keeps history),
    drawer 3 → `eval/`, repointing docs/CI paths. Sharpens the same boundary the core
    self-containment ratchet enforces from the other side. Costs one small plan and touches `eval/`,
    which is outside every current `write_scope`.
  - **(b) Archive only** — retire the spent migrations, leave the harnesses; they are operator
    entrypoints, not library code. Cheapest; the boundary question stays open.
  - **(c) Won't-do** — the flat drawer is preferred; record that in `CONVENTIONS.md` so it stops
    resurfacing every few sweeps.
- default_if_unanswered: no tidy plan is minted; `scripts/` stays flat and finding-0114 stays open.
  Park condition — revisit at the next `/triage` after another spent one-off lands, or when someone
  next edits an eval-flavoured script. Pairs naturally with the worktree reaper (finding-0121) as one
  tidy/tooling wave.
- answer:

---

## oq-0039 — Ratify the four Chapter-1 draft theses, or confirm forward-referencing is the standing answer? (finding-0117)
- status: open
- origin: docs/findings/finding-0117.md (bp-077, reaffirmed by bp-104)
- blocking: false
- question: The manual's Philosophy chapter rests on four design notes still at `status: draft`:
  **`dn-authorship-distance-axis`** (the graded authorship coordinate — "every stratum is self-data,
  at a distance"), **`dn-the-sacred-boundary`** (model-advises / code-acts in its purest form),
  **`dn-recursive-strata`** (the dreamer-as-a-map framing), **`dn-founding-corpus`** (the Ouroboros
  naming claim). A *ratified* note — `dn-agent-workflow` — bars draft notes from the book, and the
  book skill says so outright ("Draft notes never enter the book"), so the scribe cannot cite them as
  authorities. bp-104 (complete) made the workaround structural: they are listed under
  `forward-referenced:` in `docs/book/SYNC.md` and named via `\fwdthesis`, never cited.
  - **(a) Ratify some or all four** — a hand `draft → ratified` flip each; a `/scribe` run can then
    cite them and deepen Philosophy (and Mathematics, for the authorship coordinate).
  - **(b) Confirm forward-referencing stands** — drafts stay named-but-uncited until ratified;
    finding-0117 flips to `resolved` with `SYNC.md`'s banner as the mechanism of record.
  - **(c) Ratify only `dn-the-sacred-boundary`** — the one the Architecture chapter already needs
    (see oq-0044a) — and leave the other three forward-referenced.
- default_if_unanswered: (b) — the forward-ref treatment stands, the four notes stay draft and
  uncitable, nothing in the book changes. Park condition — revisit at the next `/scribe`, or if
  oq-0044 forces the sacred-boundary taxonomy first.
- answer:

---

## oq-0040 — Should `/graduate` always commit the `proposed` mint, so a blessing is always a tracked one-line diff? (finding-0119; the cheap half of oq-0036)
- status: open
- origin: docs/findings/finding-0119.md (observed live re-graduating bp-076 → bp-078)
- blocking: false
- question: Blessing is two acts by two actors: the orchestrator mints a plan at `status: proposed`,
  you hand-flip it to `ready`. **Nothing forces the mint to be committed first.** When you bless an
  uncommitted mint, the plan exists only as an untracked file already at `ready` — the Stop gate
  correctly blocks it as a "from-nothing" blessing, and once committed it carries no `proposed`
  predecessor at all. ⚑ That is exactly **oq-0036**'s crux (*what legitimises a committed
  `proposed→ready` flip carrying no grant record?*) in its cheapest form, because our ceremony has
  the **agent** commit your hand flip. Note `palace bless` today is **flip-only**
  (`scripts/palace.py:50-118`): it refuses in agent sessions, requires exactly `proposed`, and
  rewrites only the status/updated lines — it does not mint-if-untracked, stage, or commit.
  - **(a) Mint-commit discipline** — `/graduate` commits each new plan at `proposed` before
    reporting. One line in the graduate skill; every bless becomes a small tracked diff with a real
    predecessor. No code, no gate change.
  - **(b) (a) plus make `palace bless` the sole atomic path** — extend it to mint-if-untracked, flip,
    and stage only that plan. Small build; removes the hazard even when you bless out of order or away
    from the keyboard.
  - **(c) Leave it** — the friction is real but rare, and every gate fired correctly each time.
- default_if_unanswered: (a) adopted as orchestrator discipline at the next `/graduate` — a committed
  `proposed` mint is strictly safer and changes nothing you do — with **no** amendment written into
  `dn-agent-workflow` until you rule. Park condition — revisit when oq-0036 is answered, since its
  answer decides whether (b) becomes mandatory.
- answer:

---

## oq-0041 — Ratify the headless-daemon secret-bootstrap design, or keep the core plane parked? (finding-0123)
- status: open
- origin: docs/findings/finding-0123.md (bp-078, mid plane-migration)
- blocking: false
- question: The **core-plane half** of the plane migration (runbook §7–§11: move the palace daemon and
  Vault to the headless `ouroboros` role account, chown the vault `0700`, pf egress) is still blocked.
  Its bootstrap reads the Vault **unseal key** from a *login* keychain
  (`ops/vault/vault-unseal.sh:31`, `security find-generic-password`) — and a role account has no login
  keychain; the daemon plist even lists that migration as a precondition it cannot meet. A design pass
  answered it — **`dn-headless-daemon-secret-bootstrap`** (System keychain with an ACL · an
  `ouroboros`-only file · a hybrid where Vault stays `ascalva`-operated · a boot-time unseal helper) —
  but that note is still **`status: draft`**, so `/graduate` refuses it and nothing can be built.
  - **(a) Re-read, then ratify** — one Fable pass over the draft (fable now works from the `ascalva`
    plane), then the hand flip; §7–§11 re-graduate and the core plane lands.
  - **(b) Ratify as-is** — accept the Opus product, flip, graduate. Fastest; accepts that the secrets
    architecture was designed one tier below policy.
  - **(c) Keep the core plane parked** — the workflow plane already delivers day-to-day isolation;
    revisit when the Vault posture actually changes.
- default_if_unanswered: (c) — the core plane stays parked, the note stays `draft`, the runbook keeps
  its §7 stop banner, and `ouroboros`/`ouroboros-edge` stay forward-provisioned (no work lost). Park
  condition — revisit the next time you touch Vault, or immediately after oq-0042's Opus re-read.
  ⚑ **Sequence oq-0042 first** — its residual is the gate on this ratification.
- answer:

---

## oq-0042 — Chase a fable-capable headless credential, or record the dormant workflow plane in the design record? (finding-0125)
- status: open
- origin: docs/findings/finding-0125.md (session-38, right after the workflow plane went live)
- blocking: false
- question: The role account **`ouroboros-work`** — the constrained principal agents were meant to run
  as — cannot reach the **fable** tier: its headless `claude setup-token` credential carries a
  narrower model entitlement than your interactive login. You chose the hybrid, we built the `PLANE`
  toggle, then you swapped its default to `ascalva` (`scripts/orchestrator-launch.sh:35`). So the
  workflow-plane isolation bp-078 delivered is **dormant by default**, one flag away
  (`PLANE=workflow`). Fable access via the human plane is confirmed in practice (a real Fable pass ran
  under the new default). Two residuals: option 3 (a fable-capable *headless* credential) is
  undecided, and **ratified `dn-plane-principals:160` still asserts the orchestrator runs as
  `ouroboros-work`** — which the tree no longer does, unannotated.
  - **(a) Chase option 3** — a scoped read-only investigation (or an upstream ask) into a headless
    credential carrying fable; if it works, `PLANE=workflow` becomes the default again and isolation
    stops being dormant.
  - **(b) Accept the dormancy, fix the record** — a short superseding note stating that the role
    principal is *not* model-equivalent to the human login and that isolation is opt-in.
    `dn-plane-principals` is ratified and agent-immutable (A8), so this is a **new note, never an
    edit**.
  - **(c) Both, in order** — (a) first, then write (b) around whatever it finds.
- default_if_unanswered: neither runs — the toggle stays as built, `dn-plane-principals` §3.2 stays
  stale, the finding stays open. Park condition — revisit when you want the isolated plane as the
  default again, or at the next plane-touching build.
- also owed under this finding (tracked with oq-0041): re-read `dn-headless-daemon-secret-bootstrap`
  as an **Opus** product before ratifying it — prior "fable" subagents actually ran on Opus, and a
  subagent cannot exceed its parent's model access.
- answer:

---

## oq-0043 — The fiber survey's similarity (S) rows are still unmeasured: grant an embed window now, or park them until the embedder moves out-of-process? (finding-0142)
- status: open
- origin: docs/findings/finding-0142.md (G-A survey, bp-085, sealed 2026-07-21)
- blocking: false
- question: The read-only fiber survey (`eval/harness/fiber_survey.py`) measured the **recorded**
  fibers — citation F (207 nodes / 593 edges), causal C (237 / 1193), supersession D (19 docs,
  **0 triangles** ⇒ covering-only integrity clean, which also discharges oq-0020's invariant
  empirically) — but every **similarity (S)** row deferred (M2/M4/M5/M8, plus the S columns of
  M1/M3/M7). Cause, now independently confirmed by finding-0174: the eval-side embedder shares the one
  Ollama with the live daemon, both model slots are held (non-negotiable #8, ≤2 resident models), so a
  single embed trips the 120 s fail-fast timeout. **No code change is needed** — it needs embed
  headroom, and the survey upgrades itself once it has one.
  - **(a) Grant a one-time embed window now** — you pause the daemon
    (`uv run scripts/palace.py down`), the survey re-runs, then `up`. Closes the survey's re-entry
    conditions 1–2 (is the fiber support non-degenerate / is the mismatch structure real), feeds the
    hop-priced-functional question oq-0024 owes, and gives the phase model its first look — today.
    Cost: one deliberate daemon outage.
  - **(b) Park the S rows until bp-118 lands** (the plan where the embedder cuts over to a
    palace-owned `llama-server` process). Then the re-run is free, repeatable, no outage, no owner
    act. Cost: it slips behind an 8-plan inference program.
  - **(c) Run against a scratch store with its own embedder** — no daemon contact, but a second
    embedder breaches the memory ceiling unless the daemon is down anyway, so it collapses into (a)
    with extra steps.
- default_if_unanswered: (b) — park the S rows on bp-118. Park condition — finding-0142 stays open as
  the record and the Fiber-geometry deskcheck row stays PENDING (it already names the owed S-rows);
  re-entry — bp-118 seals, or you grant a window sooner.
- note (no decision asked): the ratified premise *"the C live census read came back empty"*
  (`dn-fiber-geometry:96`, repeated `:386,:414,:523`) is now **false** — C is a populated fiber
  (1193 edges). A8 freezes the note; per the oq-0025/0026/0028 discipline **finding-0142 is the
  standing erratum** unless you choose to hand-annotate.
- answer:

---

## oq-0044 — Two unratified frames that the manual and a live hook already depend on (finding-0183 · finding-0184)
- status: open
- origin: docs/findings/finding-0183.md · docs/findings/finding-0184.md (both opened by bp-104)
- blocking: false
- question: **(a) `docs/design-notes/the-sacred-boundary.md` is still `draft`.** It is the *only* place
  the record states the three channels crossing the core boundary — verdict authorization, ingestion,
  effects — and it calls itself a spine note indexing five subsystem notes. Chapter 1 of the manual
  promised that taxonomy; drafts are barred as book sources, so Chapter 2 gave only the ratified
  partial (`dn-capability-scope`'s `A = P × W_Σ × W_world`) and the promise was downgraded to a
  forward reference. **Options:** (1) ratify as-is — cheapest, but its §1 predates both the plane split
  and the ring split (2026-07-04), so it may describe a mechanism that has since moved; (2) ratify a
  **successor** stating the taxonomy against today's mechanism (likelier right, one design pass);
  (3) leave draft — the book keeps a visible hole at its centre and five notes keep hanging off an
  unblessed spine.
  **(b) `docs/research/security-planes.md` is `draft`, and two things already stand on it.** A
  *ratified* note (`dn-type-system-as-core-audit`) takes its three-plane composition as doctrine, and
  the **foundation-file denylist enforced against every session — orchestrator included — cites it as
  its origin**: `.claude/hooks/_lib.py:27` reads verbatim *"(design-note §6, §10; origin:
  security-planes.md)"*, with the live `DENYLIST` at `:35-39` holding three entries — **narrower than
  the note's candidate enumeration**, exactly as finding-0184 predicted. Its own header asks to be
  promoted to `docs/design-notes/`. Unratified means its falsifier ("the composition claim fails if a
  demonstrated attack crosses planes") can never be a plan's acceptance criterion. **Options:**
  (1) promote to a design note and ratify, recording the reconciliation between its predicted
  foundation set and the three entries actually enforced — its §2 asked for exactly this check and it
  is now cheap; (2) ratify unchanged and file the reconciliation separately; (3) leave as research.
  Note oq-0012 ratified only the *extension*, never this base note.
- default_if_unanswered: both stay `draft`. Chapter 2 keeps the ratified partial plus its own reading
  of the composition; `SYNC.md` keeps the `forward-referenced:` row. Park condition — you ratify (then
  one `/scribe` run restores Chapter 1's citation, amends Chapter 2, and clears the row), or a
  cross-plane defect appears that the composition claim would have named.
- answer:

---

## oq-0045 — Should the import firewall walk the closure, or is the self-containment ratchet the intended discharge path? (finding-0185; oq-0046 is the live instance)
- status: answered   # 2026-07-26 — (a) walk the closure; the palace-as-oracle recorded as successor, not authority
- origin: docs/findings/finding-0185.md
- blocking: false
- question: `ops/import_lint.py` motivates itself with a **closure** claim — *"if no module under
  `core/` can **reach** a network-capable module, then no egress path exists"* — but it checks only
  **direct** imports, one AST walk per file, no traversal. The gap is not theoretical: `core/factory/
  factory.py:182 → config.secrets_backend → hvac` reaches a Vault HTTP client that the lint's own list
  marks *"never core"* (that is oq-0046). ⚑ So **non-negotiable #1/#2's *static* tier is conditional**
  on `tests/unit/test_core_self_containment.py` reaching zero — and it is at **20** violations today,
  having silently regressed 19→20 because the documented green gate deselects that very ratchet.
  - **(a) Make the lint walk the first-party closure** (~40 lines; `tests/unit/test_inner_ring.py`'s
    fixed-point scanner already does this walk). The claim becomes unconditional **today**, and the
    ratchet reverts to being hygiene rather than a safety dependency.
  - **(b) Keep the lint local and treat the ratchet cleanup (finding-0103) as the discharge path** —
    no new code, but the invariant stays conditional for as long as the ratchet is red, which has now
    been months.
  - **(c) Both** — closure lint now, ratchet continues as hygiene.
- default_if_unanswered: the lint stays direct-only and the record keeps the conditional (the book
  already documents it honestly as `Proposition 2.1/2.2`). Park condition — you rule here, or a new
  `core → sibling → network` chain is found. Also enacted by this triage regardless: finding-0103 is
  re-weighted on the board as a **safety-discharge** item, not hygiene.
- answer: **(a) — MAKE THE LINT WALK THE FIRST-PARTY CLOSURE.** Owner, 2026-07-26: *"yeah, I think
  so, or even better yet, use ouroboros, or find a way to use it, after some of the coming work, it
  might be able to trace an import path?"*
  ⇒ Two things, and they must not be conflated. **The ruling** is (a): the closure walk lands in
  `ops/import_lint.py`, so non-negotiable #1/#2's static tier stops being *conditional* on a red
  ratchet. ~40 lines, and the walker already exists as precedent — `tests/unit/test_inner_ring.py`
  does a fixed-point first-party scan. On landing, the `test_core_self_containment` ratchet reverts
  from a safety dependency to hygiene (which also removes the awkwardness that CI **deselects** the
  very ratchet the invariant leans on, `.github/workflows/ci.yml:50`).
  **The larger idea** — let the palace answer its own reachability question — is captured in full at
  `docs/brainstorms/autopilot-mode.md` (08:20Z capsule). Why it is sound: the AST-derived structural
  plane already holds the graph (`ops/code_snapshot.py`, `ops/code_sensor.py`,
  `reference_edges.sqlite` at ~1.53M edges over 1,135 commit snapshots), so "can core reach a
  network-capable module?" is a **reachability query over data that already exists**, not a new
  subsystem. Two hard constraints recorded there, both of which a future session will be tempted to
  erode: **(i) STRUCTURAL edges only, never semantic** — an invariant check must be sound, and a
  similarity answer admits false negatives; **(ii) THE LINT STAYS THE AUTHORITY** — a self-referential
  guard fails *silently* when its own graph is incomplete (a missed dynamic import, a stale snapshot),
  so the palace is a second opinion and a discovery tool, kept honest by a completeness ratchet (every
  edge the lint finds must also appear in the palace's graph).
  **Sequencing, matching the owner's "after some of the coming work":** the closure walk is startable
  now and closes this question; the oracle rides the reference-bookkeeper track (finding-0154), because
  the store has 1.53M accumulated edges and **no materialized current view**
  (`core/stores/reference_edges.py:299,329`) — a reachability query today would rebuild one per call.
  **Enacted by this triage regardless of the walk:** finding-0103 re-weighted on the board as a
  safety-discharge item, not hygiene.
  **Rule together with oq-0046** — same mechanism, two halves. Not yet minted as a plan.

---

## oq-0046 — Core can reach the Vault HTTP client in two hops, and the only unconditional guard is not loaded (finding-0190)
- status: answered   # 2026-07-26 — (a) load the anchor; commands supplied, owner-run and NOT yet executed
- origin: docs/findings/finding-0190.md
- blocking: false
- question: The chain is intact today: `core/factory/factory.py:182 → config.secrets_backend →
  hvac.Client(...)`. **Three things stand between a `[secrets]`-enabled core process and off-host
  egress, and none is a boundary:** (1) `hvac` is an *uninstalled optional extra* — a packaging
  accident; (2) `core/sealing.py`'s socket monkeypatch, whose own docstring concedes a native
  extension bypasses it; (3) the kernel **`pf` anchor** on the `ouroboros` uid — the one unconditional
  guard — which is committed but **owner-loaded**, and `scripts/verify_planes.py:270-291` can only
  report **SKIP** (*"pfctl … unreadable (needs root) — owner verifies with sudo"*) until you load it.
  Non-negotiable #1 says enforce structurally, not by convention. ⚑ The inert anchor is currently
  tracked **nowhere** — no owner question, no track, no board row.
  - **(a) Load the pf anchor now** — one sudo command; makes the guard real and turns the SKIP into a
    PASS. Leave the import inversion to finding-0103's programme.
  - **(b) (a) plus promote the `core/factory → config.secrets_backend` inversion into the next ops
    wave as a *safety* item**, not hygiene.
  - **(c) Accept and record** — the guard stays a packaging accident and the record says so plainly.
- default_if_unanswered: the anchor stays inert and the chain stays reachable-in-principle. Park
  condition — you load the anchor, or `[secrets]` is enabled on a host with `hvac` installed, which
  would make this live rather than latent. ⚑ Rule this **together with oq-0045** — same mechanism, two
  halves.
- answer: **(a) — LOAD THE pf ANCHOR.** Owner, 2026-07-26: *"sounds like a easy win to me, give me
  the command to execute."* Commands supplied same session; this is an **owner-run sudo step and has
  NOT been executed** — the anchor is still inert.
  **Preconditions verified before the commands were handed over** (so the parse cannot fail on the
  documented "unknown user ouroboros" trap): the `ouroboros` account **exists**, uid 550
  (`dscl . -read /Users/ouroboros UniqueID`); `/etc/pf.conf` currently carries **no** `mind-palace`
  anchor lines, so persistence is a separate edit; whether pf itself is enabled could not be checked
  without sudo (`pfctl -e` if not).
  ```
  sudo pfctl -n -f ops/network/ouroboros-egress.pf.conf                       # parse only, loads nothing
  sudo pfctl -a mind-palace/ouroboros -f ops/network/ouroboros-egress.pf.conf # load the sub-anchor
  sudo pfctl -a mind-palace/ouroboros -sr                                     # verify: 2 rules, lo0 pass FIRST
  ```
  then the two `/etc/pf.conf` loader lines from the conf file's own header, and
  `sudo pfctl -f /etc/pf.conf`.
  **⚑ HONEST SCOPE — it buys less than "easy win" implies, and this was stated to the owner before he
  ran anything.** The anchor blocks the **`ouroboros` uid**, and *nothing currently runs as
  `ouroboros`*: only user LaunchAgents are installed (`~/Library/LaunchAgents/com.mind-palace.*`) and
  there is **no** `/Library/LaunchDaemons/com.mind-palace.*`, so the daemon runs as `ascalva`.
  ⇒ Loading it turns `scripts/verify_planes.py:270-291`'s **SKIP into PASS** and pre-positions the
  guard, but it does **not** protect today's running daemon. It becomes load-bearing only when the
  core-plane migration lands — which is precisely what **oq-0041** is blocking. Real, cheap, correct
  to do now; not a hole closing today, and the record must not later read as if it were.
  **The import-inversion half** (`core/factory/factory.py:182 → config.secrets_backend → hvac`) is
  unchanged and stays with finding-0103's programme; the closure walk that would *detect* such chains
  is oq-0045.
  **Re-entry:** the owner runs the commands (then this flips to swept with the `-sr` output recorded);
  or oq-0041's core-plane migration lands and makes the anchor live.

---

## oq-0047 — Which `ftype` vocabulary is authoritative? The template's and CLAUDE.md's are disjoint sets (finding-0193; unblocks the autopilot routing tier)
- status: answered   # 2026-07-26 — owner: use ftype to route
- origin: docs/findings/finding-0193.md
- blocking: false
- question: A finding's `ftype` field has **two competing vocabularies and they do not overlap.**
  `docs/templates/finding.md:9` offers `blocker | spec-defect | question | discovery` (a
  severity/kind axis). `CLAUDE.md:51-54` — the routing rule that binds every session — routes on
  `design | math | direction | codebase | spec-fidelity` (a subject-matter axis). The `finding` skill
  prints both without reconciling them, **disjoint within one file**. In practice the corpus uses the
  **union**: across 182 findings — `discovery` 54 · `spec-defect` 54 · `spec-fidelity` 23 ·
  `direction` 24 · `design` 13 · `math` 5 · `codebase` 5 · `question` 3 · `blocker` 1. So "correctly
  typed and routed" is undecidable, and **no hook validates it** (`grep ftype` over hooks/scripts →
  zero). `dn-autopilot-and-delegated-blessing` §2.4 has its routing tier parked on exactly this, with
  two Parked rows whose re-entry is literally *"finding-0193 resolved by owner ruling"*.
  - **(a) Two orthogonal fields** — keep `ftype` = severity/kind (template set) and add `subject` =
    the routing axis (CLAUDE.md set). Nothing existing is wrong, both axes stay expressible, a hook can
    validate each. Costs a front-matter field and a 182-file backfill.
  - **(b) CLAUDE.md's set wins; the template is corrected** — `ftype` becomes the routing axis only;
    `blocker` degrades to a boolean or a `status`. Smallest vocabulary, directly enforceable. Loses the
    severity distinction, and 112 findings must be retyped.
  - **(c) The template's set wins; the routing rule is rewritten to route on `route:` alone** — which
    is already the field every finding actually carries and honours (111 `orchestrator` / 47 `builder` /
    2 `owner`). Zero retyping, matches observed behaviour. Concedes that the subject-matter axis stops
    being typed at all, which is what the autopilot tier wanted.
- default_if_unanswered: (c) — route on the existing `route:` field, `ftype` stays advisory prose, no
  sweep, no hook. Park condition — the autopilot routing tier stays at its conservative default (*any
  not-unambiguously-builder finding halts*) and no `ftype` validation hook is built. Re-entry — this
  ruling, or the first autopilot plan that needs typed routing. ⚑ **Time this with the autopilot
  superseding note**, which is in flight anyway.
- answer: **YES — `ftype` BECOMES THE ROUTING AXIS. Option (b).** Owner, 2026-07-26: *"yes,
  definitely start using ftypes to route findings appropriately around the system."*
  **Reading, stated explicitly because (a) and (b) both sound like "use ftype":** the ruling is (b),
  not (a). In (a) `ftype` would have STAYED the severity axis with a new `subject:` field doing the
  routing; the owner asked for *ftype* to route, so `CLAUDE.md:51-54`'s vocabulary
  (`design | math | direction | codebase | spec-fidelity`) is authoritative and
  `docs/templates/finding.md:9` is the surface that gets corrected. Option (c) (route on `route:`,
  `ftype` stays prose) is rejected by the same sentence.
  **Enactment, in dependency order — none of it done yet, and it is deliberately NOT being swept in
  the ruling session:**
  1. Correct `docs/templates/finding.md:9` and reconcile `.claude/skills/finding/SKILL.md:12-23`
     against `:25-32` (today they are disjoint *within one file*).
  2. Decide where `blocker` goes — see the residual below.
  3. Backfill: **112 findings** carry a value outside the routing vocabulary
     (`spec-defect` 54 · `discovery` 54 · `question` 3 · `blocker` 1). Mechanical but not free, and it
     rewrites `updated:` on every one of them unless done deliberately.
  4. Only then a validation hook (`grep ftype .claude/hooks/ scripts/` is currently **zero** — nothing
     mechanically checks this today, which is why the two vocabularies could diverge unnoticed).
  **⚑ RESIDUAL SUB-DECISION, defaulted not ruled:** `blocker` is a *severity*, not a subject, so it
  cannot survive as an `ftype` under (b). Default: it becomes a **boolean field** (`blocking: true`),
  which is what `owner-questions.md` entries already use — so the vocabulary shrinks and nothing is
  lost. Re-entry: the owner objects, or the backfill reaches the one `blocker`-typed finding.
  **⚑ WHAT THIS UNBLOCKS:** `dn-autopilot-and-delegated-blessing` §2.4's routing tier, whose two
  Parked rows (`:535`, `:538`) have re-entry conditions that read literally *"finding-0193 resolved by
  owner ruling"*. Time the enactment with the autopilot superseding note so the tier is designed
  against the settled vocabulary rather than around it. Also relevant to finding-0209: the
  builder-routed orphan register cannot be derived reliably until "is this builder-routed?" is
  decidable, which this ruling makes true.

---

## oq-0048 — The per-plan cost ledger has holes, and the cause is deferred sealing — not in-session work (finding-0200; the delegation budget gate calibrates off this ledger)
- status: open
- origin: docs/findings/finding-0200.md
- blocking: false
- question: The `cost.actual` block (`model`/`tokens`/`ratio`/`session_delta`/`week_delta`) is filled
  at seal from the harness's completion-notification usage figure. That figure exists only for a
  **delegated** agent, and only while the session that received it is alive. It was filed as "in-session
  builds seal with a hole" — but the tree shows worse: **bp-108 was delegated and still sealed
  `tokens: unmeasured`**, because the notification figure was never carried into the next session's
  resume brief. bp-115, also delegated, got tokens but lost **both** deltas. **Seven plans now read
  `unmeasured`** (bp-006, 012, 105, 108, 110, 115, 119). This matters because the delegate skill's
  pre-flight budget gate spawns a worker only if `padded_estimate ≲ available`, and the pad is
  calibrated from this ledger's own estimate/actual pairs — so the holes degrade the gate protecting
  every future delegation.
  - **(a) Make the figure a mandatory checkpoint field** — the moment a delegated agent's notification
    arrives, the orchestrator writes tokens/tool-calls/duration into the plan's **journal**, before any
    resume brief, so the seal reads the journal rather than memory. Also bracket `/usage` around
    in-session builds. Fixes both halves; costs one journal write per completion.
  - **(b) Declare the field N/A by construction for anything not sealed in its building session** —
    `tokens: n/a (deferred seal)` becomes a first-class ledger category, and the pad is calibrated only
    from same-session-sealed delegated pairs. Honest, zero cost; permanently abandons the
    plan-pinning-ratio hypothesis (well-pinned ~0.5× / loose ~1.5×), since deferred sealing is the norm.
  - **(c) Seal in the building session, always** — best data; conflicts with ending sessions at unit
    boundaries when a merge or gate run spans sessions.
- default_if_unanswered: (b) — mark the gaps `n/a` rather than `unmeasured`, and state in the delegate
  skill that the pad is delegated-and-same-session calibrated. Park condition — the pinning-ratio
  hypothesis stays unfalsifiable and the pad keeps its current empirical range; re-entry — the next
  in-session seal, or the next time the pad is re-tuned.
- the one thing NOT on the table: estimating a missing figure from the pinning heuristic. That feeds a
  prediction back into the ledger as an observation and would calibrate the next pad against the very
  heuristic it exists to test. bp-105 and bp-108 were both sealed `unmeasured` deliberately for this
  reason.
- answer:
