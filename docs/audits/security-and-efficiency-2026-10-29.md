# Ouroboros security and efficiency review — 2026-10-29

The owner asked: "is the whole system safe, secure, and efficient?" Scope: the palace, lmtune's
serving stack, the Open WebUI bridge, and the curated-literature import, as they run on ouroboros
today. Everything below was checked on the machine; nothing is assumed from design documents.

## Verdict

Safe and secure for a single-owner machine, with **one real gap** (cross-tool egress in Open WebUI,
below) and a few small items. Efficient for today's corpus; **two scaling costs** will bite as it
grows (REACH over per-commit readings; DIFFUSE's dense kernel), and GPU work is not yet sequenced.

## What holds (verified)

| control | evidence |
|---|---|
| Nothing listens beyond loopback | `lsof`: 3000, 8080, 8081, 8095, 8096, 8888 all on 127.0.0.1 |
| Tailnet exposure is deliberate and gated | `tailscale serve`: Open WebUI (login, MFA, signup off) and lmtune's model (API key), tailnet-only |
| Secrets are files the owner alone can read | lmtune and bridge keys 0600 in 0700 dirs; lmtune's in-container secrets are podman secrets; Jev's key in Keychain |
| Disk encryption | FileVault on |
| Open WebUI is boxed | podman, internal networks; the relay forwards only listed ports (lmtune's probes refuse the rest); web only via Tor |
| The palace core is sealed | responder, stdio MCP and lanes seal sockets to loopback before opening a store |
| The bridge edge holds nothing | no store handle, no private-zone import (test-pinned); Host allowlist, Origin refused, bearer key |
| Tools are least-privilege | the web tool set is reads plus capture and the two syncs; no dream, relate, link or delete; enforced in the sealed responder |
| Literature never touches the mirror | separate store; curated is not mirror-readable; a default search returns none (verified live) |
| Backups run | `com.mind-palace.backup` last exit 0 |

## Gaps

1. **Cross-tool egress in Open WebUI (medium).** lmtune enables web search (`search_web`,
   `fetch_url`, over Tor), and the palace tools now start on in every chat. A prompt injection — in
   a fetched page or a curated paper — could make Qwen put palace text into a search query or URL,
   which leaves the Mac. Soft control in place: the brief says never to. Structural fix (proposed):
   an Open WebUI filter that refuses a web-tool call whose arguments contain text a palace tool
   returned in the same chat.
2. **`com.mind-palace.token-rotate` last exited -9 (killed).** If that is the Vault token rotation,
   tokens may not be rotating. Check its log.
3. **A stale tailnet route:** `:8444 → 127.0.0.1:8090`, where nothing listens today; anything that
   binds 8090 later would be exposed on the tailnet. Remove it if unused (owner's call).
4. **Same-user trust.** Any process running as the owner can read the keys and call the bridge or
   the key-less embedder (compute only, no data). The macOS user is the trust boundary, as designed.
5. **The responder is not OS-sandboxed** (its network is sealed in-process; its file access is the
   owner's). Its code paths read only the palace's stores and vault notes. A sandbox profile like
   lmtune's media worker would add defence in depth.
6. **Prompt injection → junk captures (low):** capture writes observed-provenance notes only, never
   the mirror, and is reversible.
7. **Uncommitted lmtune work** (the media wiring since 2026-10-23, the tool servers since today):
   the deployed tool is a snapshot of an uncommitted tree.

## Efficiency (measured)

- Embedding: EmbeddingGemma-2 at ~24 documents/s (the 4B did 1.7); the 148,228-chunk literature
  import ran at ~23 chunks/s while sharing the GPU.
- Conversations (Qwen3.8-27B, thinking off): a direct answer in 2 s; search-read-answer in 1–2.5
  minutes; prefill ~90 tok/s dominates. The brief's prefix is cached by llama-server across turns.
- The bridge: a cold call (responder start) 5.4 s, warm ~1 s through Open WebUI's relay.
- No GPU sequencing yet (bp-116): the import slowed visibly while conversations ran.
- Storage: reference edges 1.0 GB (+~5.5 MB per commit), code observations 3.3 GB, vectors 178 MB,
  curated literature ~237 MB+ (import running); 100 GiB free.
- Query algebra: see `eval/query_bench.py` and the section below.

## Found and fixed while measuring: REACH (e983ff4)

REACH, the reference-chaining verb, was both **stale** and **slow**. Its default anchor took the
last daemon run's commit even after that run had stopped — on this on-demand palace a run from
2026-10-22, before the reset — so every REACH answered from an old graph (`core/query.py`: 0
refs). And each hop loaded a ref's readings across all 1,467 commits, then filtered to one in
Python. Now only an active run anchors (else HEAD, the design's own rule), the store filters by
commit in SQL, and two (ref, commit) indexes make each lookup a seek.

| target | depth 2 before | depth 1 / 2 / 3 after |
|---|---|---|
| docs/design-notes/agentic-loop.md | 22.6 s | 0.00 / 0.02 / 0.06 s (46 / 380 / 926 refs) |
| ops/code_sensor.py | 8.8 s | 0.00 / 0.01 / 0.06 s |
| core/kernel/scope.py | 3.5 s | 0.00 / 0.01 / 0.03 s |

## The heartbeat (added the same day)

Phase 1's `palace tick` (ops/heartbeat.py, LaunchAgent `com.mind-palace.tick`), reviewed and
tested as it was built:

| concern | control | proof |
|---|---|---|
| Egress | runs under `seal()`; its only sockets are two loopback probes; the edge readers run as their own processes, as in the sync | the import firewall still passes; no new network module in core |
| Shell injection | every subprocess is a fixed argv with a deadline (pmset, ps, osascript, the readers) | review |
| AppleScript injection | a reminder's text reaches osascript as an argument to a constant script | test: a title carrying `do shell script` stays inert text |
| SQL injection | the ledger's queries are parameterized | test: a `DROP TABLE` title is stored verbatim |
| Secrets | lmtune's key is read from its 0600 file for the loopback probe only | test: a planted sentinel key appears in no file the tick writes and not in its output |
| Trust boundary (edge) | the notices file must be a list from the last 3 hours, not the future; lines capped at 240 characters, newlines flattened | tests; the first run found a string read as a list of characters, and a forged future timestamp that would never expire |
| A stuck switch | a pause always ends (7 days at most); an unreadable or forged pause file counts as none | property test over arbitrary bytes |
| Failure loops | fail-safe readings; a circuit breaker with backoff stops a failing sync from retrying every beat; errors land in `data/tick.json` and exit non-zero | tests |

Efficiency (measured on ouroboros): a beat costs 0.37 s wall, 0.24 s CPU and 37 MB peak; a paused
beat returns before reading anything. The launcher (~190 ms of imports, duckdb behind it) loads only
when a sync runs. The two source checks run in parallel; Open WebUI's 0.4 s `podman exec`
dominates. No model is touched unless a sync has new turns and a good moment.
