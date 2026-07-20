---
type: design-note
id: dn-exhaust-lane
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/exhaust-and-ingest-sync.md    # both capsules (2026-07-19)
  - docs/design-notes/vault-sync-and-capture.md     # the ingest side this note is the mirror of
  - docs/design-notes/ouroboros-principal.md        # the ownership/permission companion (separate build)
  - docs/design-notes/the-sacred-boundary.md
supersedes: null
superseded_by: null
warrant: null
---

# The exhaust lane — system-emitted artifacts on the owner's private sync

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it. `/graduate` refuses this note
> until `status: ratified`.

## 1. Purpose and scope

Give the system an **outbound** lane to the owner that mirrors the inbound one.
Today material flows one way: the Syncthing share "Mind Palace Vault"
(`~/.mind-palace/vault`, over Tailscale) carries the corpus **in**. The owner
wants the reverse direction made first-class — *exhaust*: artifacts the system
emits for him to read on his phone (Files-app shortcut), starting with the
delegated-build reports (memory `phone-build-report`; first proof:
`~/mind-palace-reports/2026-07-19-bp-074-*.html`).

**In scope:** the layout and its one load-bearing invariant, the report artifact
format, the writer, and enforcement. **Out of scope:** ownership/permissions and
the `ouroboros` OS user — that is `dn-ouroboros-principal`, deliberately a
separate trust-boundary build (owner rule: never mix a mechanical move with a
trust-boundary change). This lane must work correctly *before* that note lands
(status-quo ownership) and *better* after it.

## 2. Decision

### 2.1 Layout — a separate Syncthing share, sibling to the vault

`~/.mind-palace/exhaust/` is a **new, independent Syncthing share** — NOT a
subdirectory of the vault. Chosen over the unified-parent alternative
(restructure the share into `ingest/` + `exhaust/`) for three reasons:

1. **Structural isolation beats an honored exclude.** The ingest pipeline's
   source roots are config-driven (`config/defaults.toml:46` pins
   `path = "~/.mind-palace/vault"`; `config/local.toml:12` a subpath). A sibling
   directory is *outside every configured root by construction* — the scanner
   has no path to it. The unified layout would instead depend on an exclusion
   rule being honored forever.
2. **The lanes want different owners and modes** (capsule 2): ingest is
   owner-fed/system-read; exhaust is system-written/owner-read. Under
   `dn-ouroboros-principal` they get different `chown`/`chmod`; two shares make
   that natural, two subdirs make it awkward.
3. **Zero churn to the working vault.** No rename, no re-pair of the existing
   share, no migration of corpus content. The vault *is* the ingest lane; this
   note merely names that fact.

Cost accepted: one extra folder pairing on the phone (a one-time SyncTrain act,
owner-performed).

### 2.2 The invariant — exhaust never re-enters the system

**Reports describe the system; ingesting them is recursive self-ingestion of
meta-content.** The rule, stated as an enforced property, not a convention:

> No configured ingest/source root may lie inside `~/.mind-palace/exhaust/`,
> and no core/ingest code path may read from it.

Enforcement (the build's test, in the spirit of `structural-enforcement`): a
unit test that loads the merged config (defaults + local), resolves every
source `path`, and asserts none is inside the exhaust root; plus a grep-class
check that `exhaust` appears in no `core/` read path. The exhaust root itself
is pinned in config (single source of truth) so the test and the writer cannot
drift apart.

Direction discipline: `exhaust/` is system-written, owner-read; `ingest/`
(the vault) is owner-written, system-read. Neither lane reads the other.

### 2.3 The report artifact

- **Format: self-contained, theme-aware HTML** — one file, no external assets,
  renders in the iOS Files → browser path. (Chosen over PDF: no render step,
  dark-mode aware; over Markdown: phone Files preview is poor.) The bp-074
  proof-of-concept is the format's reference instance.
- **Content: the six-section spec** (memory `phone-build-report`): TL;DR ·
  what-was-built · math & notation (field-guide triples, N/A'd honestly) ·
  findings · cost/metrics table · symbol-glossary footnotes; then any
  owner-hand artifact verbatim, and commit hashes.
- **Naming:** `reports/YYYY-MM-DD-<bp-id>-<slug>.html` — date-sortable in
  Files, self-describing. Retention: keep all (they are small and are the
  build-history's readable face); pruning is parked.
- Reports are **review surfaces only** — every blessing/apply they mention is
  performed at the keyboard. Guide, not gate (the bp-072 rule).

### 2.4 The writer

A small `scripts/` helper (repo-workflow tooling, no `core` import — the
docket.py precedent) that takes the report HTML and writes it to
`<exhaust_root>/reports/<name>.html`, creating directories as needed and
reading the exhaust root from config. The orchestrator composes the report
content (single-writer judgment, per the memory); the script only places it.
The Gmail-draft path (proven 2026-07-19, connector is create_draft-only)
demotes to fallback; PushNotification remains the attention-ping.

### 2.5 Sequencing with `dn-ouroboros-principal`

This build lands under status-quo ownership (`ascalva:staff`) and is correct
there. When the principal note lands, exhaust gets `chown ouroboros` +
owner-only-write — with **zero changes to this design**: the layout, invariant,
format, and writer are ownership-agnostic. That independence is the point of
the two-build split.

## 3. Consequences

- **One mechanical build plan** (papercut-sized): create the exhaust root +
  `reports/` in config and on disk, the writer script + tests, the
  ingest-invariant test, migrate the bp-074 proof-of-concept file, update
  `docs/supplemental/cockpit.md` (the owner-side Files-shortcut note).
- The owner pairs `~/.mind-palace/exhaust` in SyncTrain and adds the iPhone
  Files shortcut (owner-side, by hand).
- The delegated-build flow's merge-ready step (memory `phone-build-report`)
  targets the exhaust file as primary delivery.
- `dn-vault-sync-and-capture` (draft) is extended, not amended: the vault is
  named as the ingest lane; the exhaust lane is its mirror.

## Parked decisions

- **Report pruning/retention policy.** Default: keep all. Re-entry: the folder
  becomes unwieldy on the phone (>~100 files) or sync cost is felt.
- **Other exhaust types** (dream digests, oq exports, weekly summaries).
  Default: reports only. Re-entry: the owner asks to read another artifact
  class on the phone; each type gets a subdir sibling to `reports/`.
- **A rolling `index.html`.** Default: none (Files sorts by name/date).
  Re-entry: navigating individual files proves annoying in real use.

## Cross-references

- Brainstorm: `docs/brainstorms/exhaust-and-ingest-sync.md` (both capsules)
- Ingest roots: `config/defaults.toml:46`, `config/local.toml:12`
- Companion (permissions/principal): `docs/design-notes/ouroboros-principal.md`
- Report spec + delivery workflow: memory `phone-build-report`
- Proof-of-concept: `~/mind-palace-reports/2026-07-19-bp-074-session-handoff-gate.html`
- Constitution: non-negotiable 11 (the private default is local/Tailscale —
  Syncthing-over-Tailscale is that default; no third party in this design)
