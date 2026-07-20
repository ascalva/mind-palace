# bp-075 — journal

## 2026-07-19 — minted at graduation (orchestrator, session-36, fable pass)

Graduated from `dn-exhaust-lane` minutes after the owner ratified it
(`d3366a5`) — capture → note → ratify → plan in one evening, same arc as
bp-074. Grounding was done at design time (config-pinned ingest roots
`defaults.toml:46` / `local.toml:12`; scripts-side `get_config` precedent
`verify_attestation.py:25`; the docket no-core AST-test pattern
`test_docket.py:120-134`) and is cited in §3. One question left deliberately
code-settled by the builder: loader passthrough for a new `[exhaust]` table
(§3 Q2) — with a hard stop-and-raise if it turns out to need `core/`.

Builder discipline notes: never write outside the repo (`~/.mind-palace/**`
is live data — the real exhaust dir materializes at first orchestrator use);
the writer places content, never composes it.

Status: `proposed`. Awaiting the owner's `palace bless bp-075` + hand commit.
