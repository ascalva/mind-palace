# ambassador-open-webui-bridge

## 2026-10-28

```capsule
topic: ambassador-open-webui-bridge
date: 2026-10-28

seed (owner, verbatim): |
  "create the needed mcp infrastructure to be able to make use of the query algebra and be able to
  easily write/ingest via mcp server, specifically the dialogue from the open ui gui chats with the
  qwen model"

what exists (2026-10-28):
  - The palace MCP server (agents/ambassador/mcp.py) speaks MCP over STDIO only, sealed, spawned by
    a local harness. OpenCode uses it (`palace` server, `ambassador` agent, `palace` skill).
  - Open WebUI chats ALREADY reach the dialogue stratum: `palace dialogue-sync` (edge/openwebui.py
    reads the container's webui.db read-only into a handoff file; owner turns authored-dialogue,
    model turns observed). The Ambassador can trigger it (`palace_sync_dialogue`).
  - What does NOT exist: Qwen *inside Open WebUI* calling palace tools.

why it is not a one-line config:
  - Open WebUI runs in lmtune's podman stack on internal networks with no route out except Tor and
    `lmtune-relay` (fixed byte pipes to host ports: 8080 llama-server, 8095 the media worker). It
    speaks MCP over streamable HTTP, never stdio.
  - Invariant 2: network and private data never share a component. An HTTP listener that also
    opened the vault would be exactly that. The palace's own seam for this is the filesystem
    handoff (`[interface] handoff_dir`, CoreInbox): Zone B writes a request file, the sealed core
    answers with a response file. Pipes and shared imports are not the channel.

shape (proposal):
  1. edge/mcp_http.py — Zone B. Streamable-HTTP MCP on 127.0.0.1:8096, bearer key from a file
     (0600), Host/Origin checks like lmtune's media relay. It holds NO store handle: `tools/list` is
     a static schema; each `tools/call` becomes `data/handoff/mcp/requests/<id>.json`, and it waits
     for `responses/<id>.json` (deadline, then a typed error — never a fabricated answer).
  2. A core responder — `palace mcp-serve-handoff`: sealed, polls `requests/`, runs the SAME
     `Ambassador` tool methods under the SAME `AMBASSADOR` grant, writes `responses/`. On-demand
     like everything else: started by the edge on first request, exits after N idle minutes.
  3. lmtune: one more relay pipe (8096) and one more entry in the `lmtune-webui-tool-servers`
     secret (`type: mcp`, url via the relay, the key) — the media worker's exact pattern
     (stack.py RELAY / TOOL_SERVERS). Open WebUI then shows the tools as `palace_*`.
  4. Scope: the Open WebUI client gets a NARROWER grant than OpenCode's (read + capture; no
     dream/relate/link) — a meet of AMBASSADOR with a web-facing template, by construction.

open questions for the owner:
  - Should Open WebUI's Qwen see `observed` turns (its own past replies) or only authored strata?
  - Auto-sync Open WebUI chats on a timer (a LaunchAgent — persistence, owner-approved) vs on demand.
  - Bearer key in Keychain vs a 0600 file (lmtune uses files; the palace's Invariant 10 prefers
    Keychain/env).
```
