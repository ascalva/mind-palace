# bp-129 — journal

## Pre-build notes for whoever picks this up

- ⚑ **There is ONE owner capability system-wide and it is not yours to mint.**
  `core/stores/authored_supersession.py:80` `verify_owner_declaration` — its own docstring at
  `:86-87` says so outright. Import it. If you find yourself writing `_OWNER_TOKEN = object()` in
  `errata.py`, stop: that is Item 1's falsifier, it is a DRY defect the owner treats as a bug
  rather than a nit, and it means E1 is enforced by a copy that can drift.

- ⚑ **`INSERT OR REPLACE` is right in the precedents and WRONG here.** `dispositions.py:86` and
  `authored_supersession.py:161` both use it, keyed on the *event's own* identity, so a re-apply
  is idempotent. Errata are keyed on an autoincrement `seq`, so every assertion is a new event.
  Plain `INSERT`. E2 is stronger here than in the code you are copying from — copy the shape, not
  the statement.

- **E5 is one self-referential fold, not a second mechanism.** An erratum is retracted by a later
  erratum with `surface='errata'` and `target_key=<seq>`. `targets_for()` computes
  `targets_for('errata')` first, then excludes those errata's contributions. Resist adding a
  `retracted` column; the relation already expresses it.

- ⚑ **Run the mutation campaign; do not reason about it.** finding-0249 measured the lesson in this
  repo: both surviving mutants in the last wave were found by mutating and running, **neither by
  reading**. Five mutants are listed in Item 2. Record each verdict here as you go, not at the end.

- **The store must stay surface-agnostic.** Target keys are opaque `TEXT`, never parsed. That is
  not fastidiousness — it is what keeps this plan panel-independent while
  `dn-vector-membership-store` sits at `draft` after a BLOCK · BLOCK · RATIFY-WITH-AMENDMENTS
  panel. The moment the store parses a chat coordinate, it has taken the panel's decision.

- **The mandatory `authored_supersession` import also keeps you OUT of the inner ring.**
  `tests/unit/test_inner_ring.py:170-190` asserts computed-inner == declared-inner both ways, so a
  `core/` module importing only stdlib + `core.kernel.*` would compute inner and go red until
  `core/kernel/rings.py` declares it. `errata.py` imports `core.stores.authored_supersession`
  (outer), so it computes outer and no rings diff is needed. Two reasons to make that import, then
  — E1 and the ring boundary. If you ever drop it, this test is how you will find out.

- **Item 3 is the only item that can be parked without stranding the plan.** If reset semantics
  feel wrong (§11 PD-B — should an owner's assertion survive a corpus wipe?), park it with the
  re-entry condition and close Items 1–2. Never block on the owner.

- **Do not touch `data/`.** No live store is opened, read, or written by this plan. Tests use
  `:memory:` / `tmp_path`. In particular never run `launcher.reset(confirm=True)` against the real
  config — Item 3's acceptance is a `tmp_path` fixture, and the real thing wipes the corpus.

## Grounding carried in from graduation (verified read-only, 2026-07-27)

- `chat_utterances` PRIMARY KEY `(session_id, turn_index)` — `core/stores/chatlog.py:90`. Confirmed.
- The 139: `speaker='owner' AND text LIKE 'Stop hook feedback:%'` = **139**, over **33** sessions,
  `interpreter` uniformly `1.0.0`, `observed_at` 2026-07-18…07-25, of 9,145 utterances. Re-derived
  from the live store `mode=ro`; A2's figure holds.
- All **92** distinct `transcript_digest` values behind those 139 rows resolve to files under
  `data/raw/` — so the parked re-projection is *technically* possible; it is blocked on design and
  queue grounds, not on missing bytes.
- The queue is **wedged**: 1,766 `queued`, 1 `running`, 300,242 `done`, 1 `failed`. Nothing in this
  plan depends on ingestion, deliberately.
