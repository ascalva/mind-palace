# bp-139 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan exists because AP1 shipped un-runnable.** `bp-120` delivered the capsule, green and
  complete, and the mechanism is unusable today: no config section, no way to put a capsule in front
  of the owner, no record for a grant to land in. Flag-off is not done; the ON switch must exist.
  The enable path is in `write_scope` deliberately (§5) — that list **is** the deliverable.

- ⚑ **The config degenerate input is live in the tree right now.** `config/defaults.toml:67`'s
  `[planes]` has no dataclass, so the loader parses it into `raw` and **silently drops it**
  (`finding-0115.md:32`) — and everything is green. A test that only reads the TOML with `tomllib`
  passes on exactly that state. Item 22's real acceptance is the **demonstration**: delete the
  `Config.autopilot` field, re-run, and show half (b) going red while half (a) stays green. Record
  the actual output here.

- **Four edits in two files, and omitting any one is silent.** TOML table, `AutopilotConfig`
  dataclass, the `Config` field, the `load_config` wiring block. Copy the `selfmod` idiom
  (`core/kernel/config/loader.py:646-650`), **not** `exhaust`'s bare subscript at `:544` — a config
  omitting the section must not raise.

- ⚑ **Two artifacts, not one.** The `.txt` carries the canonical bytes the phone hashes; the `.html`
  is a courtesy. HTML-only placement passes every file-exists check while defeating invariant 2
  exactly as `bp-120` §11 row 1 describes: render X, hand `sha256(Y)`. Assert the `.txt` is
  **byte-identical** to `capsule.canonical(raw)`, not merely equal after re-canonicalization.

- **Fail-closed means writing nothing.** Item 24's degenerate input is a flag read that logs
  "disabled" and places the files anyway — a non-zero exit code alone does not catch it. Assert the
  destination directory listing is **unchanged**.

- **Do not depend on ingestion or on a push notification.** The queue is wedged (a stranded
  `code_sync` since 07-25 with ~1,766 behind it), and nothing in the repo fires a notification —
  it is an agent harness action (§3 Q6). Every criterion here is file-existence, byte-equality or
  exit code.

- ⚑ **`oq-0054` is open with no recorded answer.** The capsule's caps bound shape, not bytes. Do not
  add a character cap; `bp-120` §11 row 3 also forbids making the caps configurable.

- ⚑ **After this plan, autopilot still cannot run.** Three parked plans hold the actor. Say so in
  the seal; do not let it read as "autopilot delivered."
