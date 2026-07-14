# bp-034 journal

## 2026-07-14 — Items 13/15/16 COMPLETE — the migrator, script + e2e verification (build green)

**Status:** all four items (13–16) built + green (4 fast legs; full `pytest -q` confirming). The tool is
delivered; the owner runs the mint offline, daemon down, post-bp-031-deploy (NEVER in-session).

**Completed — Items 13 (preview), 15 (mint), 16 (orchestration), all in `core/ingest/mint_ids.py`:**
- **`preview()` (Item 13)** — pure read: enumerates the mint set (no-stable-id notes), the re-key plan
  (`NotePlan` per note: mint / rekey-only / skip), and the §4a **pre-state manifest** (`ChainSnapshot`
  per chain: `(seq, digest)`) so `run()` verifies CARRIED CONTENT, not just old-key emptiness. Opens no
  write handle. Detection: `has_stable_id` = Logseq `id::` OR YAML `id:` front-matter (`has_yaml_id`
  added — `logseq.py._PROP` only matches `key:: value`, so YAML detection is ours); `logseq_id` is the
  re-key TARGET (what bp-031 resolution reads back).
- **`mint()` (Item 15)** — byte-preserving `id:: <uuid4>` PREPENDED as the first page-property line
  (`_insert_id_line`: one line added, original bytes verbatim after). REFUSES a YAML-front-matter note
  (`MintRefusedError`) rather than guess placement (§10). Idempotent-skip any note that gained an id.
- **`run()` (Item 16)** — daemon-down gate (`_daemon_is_up` via RunLedger.last() + `_pid_alive`, mirrors
  launcher; a crashed run counts as down) → confirm gate → **`preview` (capture §4a) → `_backup`
  (vault + versions/catalog sqlite, WAL-checkpointed, verified non-empty §4c) → PER-NOTE mint-then-rekey
  (§6 convergence: mint the note, then re-key its chain `source_path→id::` on both stores, owner-gated)
  → rescan → `_verify_no_fork`** (history(source_path) empty AND carried-content prefix == manifest).
  `restore_from_backup` reverses it (exercised by the test, §4b). Reversible; offline-only.
- **`scripts/mint_ids.py`** — owner entry mirroring `scripts/purge_raw.py`: `seal()` first; `--dry-run`
  (default, fail-safe) prints the plan; `--confirm` runs the real reversible migration and reports;
  refuses (exit 1) on `MintRefusedError` or a failed post-migration verify.
- **`tests/integration/test_mint_ids.py`** — 11 tests: preview-mutates-nothing (Item 13); one-line
  byte-diff + idempotent-skip + YAML-refusal (Item 15); no-fork end-to-end + post-rename lineage +
  second-run no-op + no-confirm/daemon-up refusal + daemon-stopped-allowed (Item 16); **§6
  crash-convergence** (mint-without-rekey → re-run converges, no orphan/no fresh-uuid fork); **§4b
  restore-rehearsal** (restore from backup → byte-identical vault + version history). All pass.

**Design decisions settled in code (beyond the plan):** (1) re-key `old` is universally the note's
`source_path`; convergence rides CHECK ORDER (ii). (2) A note can carry `id::` yet have its chain under
`source_path` (bp-031 preserves stored doc_id) → `run()` re-keys EVERY in-scope note toward its id::,
not just minted ones. (3) `id::` prepended as line 1 = a Logseq page property, byte-preserving; YAML
front-matter is refused, not guessed (§10 honored without needing the real vault). (4) Vector/raw NOT
backed up (self-heal / digest-safe, re-derive from raw) — only versions+catalog+vault, the reversible set.

**Green (all 5 legs):** ruff clean · `mypy core agents eval ops scheduler scripts` = 0 (184 files) ·
argless `mypy` = **69** (baseline held — new test files added 0 net errors after `_vs` narrowing) ·
`ops.type_gate` OK · full `pytest -q` = **1078 passed, 8 skipped** (1055 pre-bp-034 + 23 new; clean run,
no flake). Suite → 1078.

**Next action:** confirm full-suite green, commit (Item 14 = stores+rider+unit test; Items 13/15/16 =
migrator+script+integration test), flip plan `in-progress → complete`, checkpoint PROGRESS.md, seal with
enriched `cost.actual`. The mint RUN remains an owner touchpoint (offline, post-deploy).

**Context-manifest delta (this leg):** `ops/lifecycle/launcher.py:_pid_alive` (reimplemented locally, not
imported — avoids pulling the launcher's heavy deps into the ingest module).

## 2026-07-14 — BUILD started (opus/high, self-driven); Item 14 COMPLETE (re-key primitives + rider)

**Status:** `in-progress` (flipped from `ready`; `active-plan` set). Building against the §11 journal
determination (ADMIT-WITH-GUARDRAILS, owner-confirmed). Item 14 done + green; Items 13/15/16 next.

**Completed — Item 14 (the owner-gated re-key primitive + verifier rider):**
- **Verifier rider** (`core/stores/authored_supersession.py`): added `verify_owner_declaration(declaration)
  -> None` — the ONE owner-capability check factored out of `record()` (isinstance + guarded `_token`
  identity via `getattr`, defends `object.__new__` bypass). `record()` now delegates to it (DRY; one
  token system-wide, per §3 guardrail 1). No second owner token minted.
- **`versions.py`**: `RekeyRefusedError` (the `PurgeRefusedError` pattern) + `migrate_rekey_doc_id(old,
  new, *, declaration) -> int`. §3 CHECK ORDER enforced verbatim: owner-auth → input-sanity →
  (i) old==new no-op → (ii) old-empty no-op (the convergence case) → (iii) both-populated REFUSE (merge)
  → (iv) relabel (one UPDATE). §5 header ENFORCED block + module-docstring paragraph amended to the
  exact journal wording.
- **`catalog.py`**: `migrate_rekey_doc_id(source_path, new_doc_id, *, declaration) -> None` — keyed by
  the unchanged PK `source_path`; same owner gate; **guardrail 5** doc_id-uniqueness refusal (no unique
  index on `doc_id`, so this is the only guard against a resolution-layer merge); idempotent self-no-op.
- **`tests/unit/test_version_rekey.py`**: 12 tests — (seq,digest,at) byte-preservation, owner-refusal,
  forged-declaration refusal, all four CHECK ORDER branches, empty-key, re-run idempotency, catalog
  rebind + collision refusal + idempotence. All pass.
- **Verified green (Item 14 slice):** ruff clean; mypy clean (3 files); `pytest test_version_rekey.py
  + test_rename_identity.py + test_version_history.py` = 22 passed (no regression). Import-cycle checked:
  catalog → versions → authored_supersession → config.loader; no cycle.

**Design note carried into the build (from §3 grounding + code re-read):** the re-key `old` key is
ALWAYS the note's `source_path` — a chain lives under either its source_path (un-migrated) or its own
`id::` (already migrated, in which case source_path is empty → CHECK ORDER (ii) no-op). So the run loop
is universal: `old=source_path, new=note's id::`. Also confirmed the MINT set ≠ the RE-KEY set: a note
can carry `id::` yet still have its chain under source_path (bp-031 preserves stored doc_id on re-record
— "switching a historied note's identity is the owner re-key"), so run() must re-key EVERY in-scope
note toward its `id::`, not only freshly-minted ones. Item 16 builds to this.

**Next action:** build `core/ingest/mint_ids.py` — helpers (`has_stable_id`, `logseq_id`), `preview()`
(Item 13, pure read + pre-state manifest §4a), `mint()` (Item 15, byte-preserving `id::` insertion),
`run(confirm=...)` (Item 16, per-note mint-then-rekey §6 + daemon-down gate via RunLedger/`_pid_alive`).

**Context-manifest delta:** read beyond the manifest — `tests/integration/test_rename_identity.py` (the
Item-16(b) analog + `_sync` fixture idiom), `ops/lifecycle/runs.py` + `launcher.py:_pid_alive` (the
daemon-liveness gate), `config/defaults.toml [vault]`. YAML-`id:` detection is NOT in `logseq.py` (`_PROP`
only matches `key:: value`) — the minter must detect YAML front-matter `id:` itself for the skip decision.

## 2026-07-14 — authored `proposed` (orchestrator, opus/xhigh; the oq-0019 B follow-on)

Authored as the follow-on to **oq-0019's (B) ruling** (owner sided with mint-into-vault as the durable,
rename-stable identity). `depends_on: bp-031`. The owner asked for **extreme rigor** — grounded hard
against the ingest + store code.

**The decisive grounding (why the plan is precise, not hand-wavy):**
- **The re-key surface is TINY and exact.** Only `versions.doc_id` (+ the catalog `doc_id` column) needs
  an explicit re-key (`source_path → minted id`). The **vector store self-heals** (keyed by
  `(source_path, chunk_hash)`, `index.py:32,88`; `index_amendment` re-projects under the stable
  source_path, `:80`); the **raw store + `authored_supersession` are digest-keyed** (old digests persist,
  raw is sacred) — neither needs re-keying. Grounded, not assumed.
- **The owner's "won't ingest see it as an update?" is half-right.** The in-place mint IS detected as an
  amendment (`sync.py:89-113`), BUT the amendment `record()`s under the RESOLVED (new) doc_id, and
  `versions` is append-only with no self-heal → `current(new_id)` is None → **seq 1 → fork**
  (`versions.py:88-94`). So the **explicit version re-key is mandatory**; the digest change alone does
  not carry lineage. This is the load-bearing fact oq-0019 named.
- **An invariant tension surfaced (owner-gated):** `versions` is structurally append-only ("no
  update/delete"). The re-key is a **relabel** (preserves `(seq, digest, at)`), not a history rewrite —
  precedented by `catalog.relabel_provenance:124`. But it's invariant-adjacent → **§4/§10/§11 surface it
  as an owner ruling at blessing** (default: admit an `OwnerDeclaration`-gated `migrate_rekey_doc_id`;
  the capability model borrowed from `authored_supersession.py`).

**Shape: BUILD THE TOOL, don't run the migration** — mirrors `purge.py`/`scripts/purge_raw.py` (owner-
gated, `confirm=True` fail-closed, offline). The owner runs it once, corpus-wide, **daemon DOWN**
(deploy-coupled, finding-0066). Byte-preserving `id::` insertion (Item 15); idempotent-skip notes with
existing `id::`/YAML `id:` (this is why repo design-notes/findings — already `id:`-stamped — are
untouched, addressing the owner's "design notes and docs" concern). The build writes **no vault file**.

**Highest-blast plan to date** (first corpus write + first append-only relabel) → opus/high, maximal
scrutiny; a vault backup + store backup + dry-run + confirm all gate the real run; reversible.

write_scope names both test paths (finding-0075): `test_mint_ids.py` (end-to-end) + `test_version_rekey.py`
(the primitive). Items 13–16 continue the family. Estimate opus/450k. Awaiting the owner-only `proposed →
ready` blessing **and** the Q3 append-only-re-key ruling (§11). No code written.

## 2026-07-14 — blessed `proposed → ready` (owner, by hand); orchestrator commits the flip

Owner hand-blessed bp-034 `proposed → ready` (with the §11 default intact) → the blessing **carries the
Q3 ruling: the append-only `versions` store ADMITS the `OwnerDeclaration`-gated `migrate_rekey_doc_id`
relabel** (Item 14 unblocked). Orchestrator commits the flip (rule 0060). **`depends_on: bp-031` binds —
build bp-031 first; and the actual MINT is an owner-run offline act (daemon down), never in the build
session** — the build delivers the tested, dry-runnable TOOL only. No code written yet.

## 2026-07-14 — §11 admissibility — Fable/xhigh determination (pre-build; orchestrator)

Single-purpose Fable/xhigh session (resume-brief 2026-07-14): the rigorous §11 determination the blessed
default rides on. No code written; bp-034 stays `ready` untouched. **This entry is binding context for
the build session** — Item 14 builds against §3 below, Item 16 against §4/§6.

### 1. DETERMINATION

**ADMIT-WITH-GUARDRAILS.** The append-only `versions` store admits an owner-gated
`migrate_rekey_doc_id(old, new, *, declaration)` that relabels `doc_id` while preserving every row's
`(version_seq, digest, at)` byte-for-byte — PROVIDED the §3 guardrails (which tighten Item 14, incl. a
check-ORDER the plan left unpinned) and the §6 Item-16 convergence amendment (the one real gap found)
are adopted. The §11 default is CONFIRMED; neither rejected alternative should be revived.

### 2. Invariant argument

- **What append-only protects.** The truthfulness of history: the sequence, contents, and order of
  `(version_seq, digest, at)` per document — rows are never altered in substance, never destroyed,
  reverts append rather than mutate (C1), ordering authority is the seq (§4A). It does NOT elevate the
  `doc_id` byte-string to immutable historical content: the store's own DDL marks `doc_id` as a
  RESOLVED, PROVISIONAL label — "== source_path until a mechanism diverges it — a rename carries this
  forward, **so the chain does not fork**" (`versions.py:56-57`). bp-031/bp-034 IS that mechanism.
- **The purpose test settles it.** Refusing the relabel would CAUSE the fork (re-ingest under the minted
  id → `current(new)` is None → seq 1, §3 Q1/Q2) — one document falsely presented as two lineages. The
  re-key is not merely tolerated by the invariant; it is *required by the invariant's purpose* once
  identity migrates. The letter ("no update/delete") still binds every machine/runtime path — hence an
  explicit, narrow, owner-gated amendment (§5), never a silent broadening.
- **Version identity nuance.** `(doc_id, version_seq)` is version identity, so the relabel does change
  the *key* — but not the *denoted document*: the same vault note is filed under a migrated name. What
  separates an admissible relabel from an inadmissible rewrite is exactly the merge-refusal guard: moving
  a chain onto a key that already denotes ANOTHER document's history would be falsification; renaming
  the token for the SAME document is a label migration.
- **`relabel_provenance` is a partial precedent only.** Analogous in operational shape (owner-era,
  one-time, idempotent relabel-UPDATE migration); DISanalogous in invariant weight: the catalog has
  upsert/tombstone/DELETE semantics (no append-only contract to touch), and `provenance` is a non-key
  column while `doc_id` is a PK component. The precedent frames; the purpose argument settles.
- **The PK-component difference is real but neutralized.** Under the refuse-if-new-has-a-chain guard,
  PK uniqueness holds *by construction* (old's seqs are unique; new has no rows), so the UPDATE cannot
  conflict; SQLite's default `ON CONFLICT ABORT` makes even a surprise conflict statement-atomic. No FK
  references `versions` (its own sqlite file); the PK + `versions_doc` index entries are maintained
  automatically by the UPDATE; rowid table, rowids unchanged.
- (Cosmetic: the plan cites `relabel_provenance:124`; post-bp-031 it sits at `catalog.py:164` — line
  drift only, not a semantic issue.)

### 3. Guardrails Item 14 MUST enforce (binding; note the check ORDER)

1. **Owner authority verified at the store boundary**, same strength as `authored_supersession.record`
   (isinstance + module-private token identity; defends `object.__new__` bypass). **Do NOT mint a second
   token** — one owner-capability system-wide. Two compliant routes: **(preferred)** owner grants
   `core/stores/authored_supersession.py` into write_scope for ONE additive public helper
   `verify_owner_declaration(declaration) -> None` (raises `MachineAuthorityRefused`) that
   versions/catalog call; **(fallback, zero scope change)** a commented private import of `_OWNER_TOKEN`
   in `versions.py`. Fail-closed either way.
2. **Check order — idempotency depends on it:** (i) `old == new` → return 0, no-op; (ii) `old` has NO
   rows → return 0, no-op (nothing to move — this is also what makes a partial-failure re-run converge);
   (iii) `old` has rows AND `new` has rows → **REFUSE** (never merge lineages) with a named error
   (`RekeyRefusedError`, the `PurgeRefusedError` pattern); (iv) else relabel. A naive refuse-first
   implementation **breaks the plan's own re-run acceptance test** (`(P, X)` re-run: P empty, X
   populated — must be the no-op case ii, not the refusal case iii).
3. **Relabel-not-rewrite, single statement, single transaction per store:** exactly one
   `UPDATE versions SET doc_id = ? WHERE doc_id = ?`; no INSERT/DELETE; `version_seq`/`digest`/`at`
   never touched; returns rowcount.
4. **Input sanity:** refuse empty/None `old` or `new`.
5. **Catalog twin** (`migrate_rekey_doc_id(source_path, new_doc_id, *, declaration)`): keyed by the
   unchanged PK `source_path`; same declaration gate (marks migration-not-runtime even though the
   catalog isn't append-only); additionally **REFUSE if any OTHER row already carries
   `doc_id == new_doc_id`** — `doc_id` has no unique index, so this guard is the only thing preventing a
   resolution-level lineage merge.
6. **Cross-store non-atomicity is accepted and OWNED by Item 16, not hidden:** versions.sqlite and the
   catalog are separate files/connections — no joint transaction exists. Recovery = restore both from
   the pre-run backups, or idempotent re-run to convergence (guaranteed by 2.ii + the §6 amendment).

### 4. Reversibility & verification — sufficient WITH three additions

Store-backup + dry-run + Item 16's "no orphaned source_path chain" is necessary but not sufficient:

- **(a) Carried-content equality, not just old-key emptiness.** Verify `history(minted_id)` ==
  pre-migration `history(source_path)` + exactly the one "id added" amendment. The dry-run should emit a
  pre-state manifest (per-chain `(seq, digest)` snapshot/checksum) the verify step compares against.
  Cheap global invariant: versions row count EXACTLY unchanged by the re-key, then +|mint set| after the
  rescan.
- **(b) Rehearse the restore.** The integration test must actually restore-from-backup and assert
  byte-identical pre-state (Item 16 *claims* reversibility; the test must exercise it, not just assert
  the backups exist).
- **(c) Backup mechanics.** Copy the sqlite files BEFORE opening store connections (daemon down, no
  writers), and verify the backups are readable/non-empty before any mutation.

### 5. Exact `versions.py` header amendment (record the admitted path; never a silent broadening)

Replace the ENFORCED block with:

```
# ENFORCED:  structural — append + reads only (no update/delete) on every machine/runtime path; a
#            store distinct from EdgeStore, so no consumer of the signed graph (build_complex takes
#            an EdgeStore, not this) can reach a version row. Ordering is by version_seq, never by
#            walking edges (§4A). ONE owner-gated exception (bp-034; oq-0019 B; §11 ruling
#            2026-07-14): migrate_rekey_doc_id RELABELS doc_id — an identity migration
#            (source_path → minted id::), never a history rewrite: every row's
#            (version_seq, digest, at) is preserved byte-for-byte, chain merges are refused,
#            old==new / no-rows are no-ops, and the write requires a verified OwnerDeclaration
#            (authored_supersession's capability) — a machine caller is refused at this boundary.
#            The label moves; the sequence, contents, and order never do.
```

And append one paragraph to the module docstring (after the append-only paragraph):

```
One owner-gated identity migration is admitted (bp-034; §11 ruling 2026-07-14):
`migrate_rekey_doc_id` relabels which `doc_id` a chain is filed under — needed exactly once per
identity switch (the id:: mint) so the switch does not FORK lineage, which is the outcome
append-only exists to prevent. `doc_id` is the RESOLVED identity label (provisional
`== source_path` until diverged — see the DDL note), not historical content: the relabel preserves
every row's (version_seq, digest, at) exactly, refuses to merge two chains, and is fail-closed on
owner authority. Runtime paths remain append + reads only.
```

### 6. Risks the plan missed

- **THE gap — partial-failure convergence (the fresh-uuid orphan).** Item 16's pinned order (re-key ALL
  stores → mint ALL notes) has a crash window: chains re-keyed to id₁ that was never written into note
  N; a naive re-run mints a fresh id₂ for N, whose re-key matches 0 rows → **orphaned chain under id₁ +
  seq-1 fork under id₂** — precisely the failure the migration exists to prevent, surviving even the
  "second run is a no-op" falsifier (which only tests the completed case). FIX, either: **(i, preferred)
  per-note ordering** — mint the note first, then re-key that note's chain, with the re-key plan derived
  from ACTUAL state (the note's current `id::` vs which key holds its chain), so any interleaving
  converges; or **(ii)** persist the uuid manifest (`source_path → uuid`) to disk BEFORE any mutation
  and have re-runs reuse it. Acceptance addition: a crash-simulation test (interrupt after a subset,
  re-run, assert convergence — no orphan, no fresh-uuid fork). This amends Item 16's INTERNAL sequencing
  only; backups/confirm/daemon-down/dry-run all unchanged. Owner confirmation of this determination is
  the authorization for the builder to build to this amended sequencing (the plan itself is blessed and
  stays untouched; this journal entry is the binding rider).
- **SQLite mechanics** (all neutralized, recorded for the builder): PK-component UPDATE is safe under
  the merge-refusal guard (uniqueness by construction); `ON CONFLICT ABORT` is statement-atomic anyway;
  no FKs; indexes self-maintain; WAL not enabled on versions — irrelevant offline/single-writer.
- **uuid4 collision with an existing id:** negligible probability, and already covered by §10's
  stop-and-raise (`history(minted_id)` non-empty → refuse) + guardrail 3.2(iii).
- **Line drift:** `relabel_provenance` now at `catalog.py:164` (plan cites `:124`).

### 7. RECOMMENDATION to the owner

**CONFIRM the §11 default as ADMIT-WITH-GUARDRAILS**: the §3 guardrail set (owner-authority at the store
boundary, the pinned check order, refuse-merges, single-statement relabel, the catalog uniqueness guard)
+ the §4 verification additions + the §6 Item-16 convergence amendment. **One rider to decide:** grant
`core/stores/authored_supersession.py` into bp-034's write_scope for the ONE additive
`verify_owner_declaration()` helper (recommended — keeps a single owner-capability verifier at its home
module; finding-0075-style owner-gated scope grant), or accept the zero-scope-change private-token
import. Rejected alternatives stay rejected: (a) the alias/indirection store leaves TWO names for one
identity forever (permanent ambiguity — *worse* for the invariant's purpose than a clean relabel) and
taxes every version query for a one-time event; (b) the full table rebuild has identical UPDATE
semantics with more blast and no gain.

**Owner confirmation:** owner accepts (2026-07-14, in-session — "the plan looks well documented and
thought out, let's proceed"). The verifier rider was also decided the recommended way: the owner
hand-added `core/stores/authored_supersession.py` to bp-034's `write_scope` (the one additive
`verify_owner_declaration()` helper). **Item 14 is fully unblocked; the build session builds to this
entry.** Build session sizing (orchestrator rec, owner-agreed): **opus/high, self-driven full `/build`
in the main lane** — the judgment-dense design is done here; what remains is disciplined implementation
against a pinned spec (xhigh stays reserved for design/gates per the standing rule; no delegation at
this blast radius).
