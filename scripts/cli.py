"""`mind-palace <verb> [args...]`: the console-script form of `bin/mind-palace`.

The same dispatch over `scripts/*`, for an installed copy (`pip install mind-palace`), where there
is no checkout to resolve a shell shim against. A Python script runs in this process under
`runpy` with `sys.argv` set as if invoked directly; a shell script is exec'd from the package.
`bin/mind-palace` stays the front door of the live checkout (it wraps `uv run`); the verb table
here and there are the same table, and `tests/unit/test_cli_dispatch.py` pins that they agree.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

USAGE = """\
mind-palace <verb> [args...]   — run from any directory

DAY-TO-DAY
  start | stop | status | reset [--force|--confirm]    the supervised lifecycle (scripts/palace.py)
  talk [--offline]                                      interactive chat (--offline = no-Ollama demo)
  monitor                                                run the dashboard/chat HTTP server standalone
  sandbox <code.py|-> [--input NAME=PATH] [--timeout N]  run code in the powerless sandbox
  query "<sentence>" [--json|--no-plan|--trace|--as <role>]  ask a sentence of the query algebra (read-only)
  query --log                                            the query sensor: strata by role, failed translations
  shell                                                  compose and run sentences read-only, with completion

INGEST / KNOWLEDGE
  ingest                                                 (re)build the knowledge base from the vault
  ingest-self-knowledge                                  ingest docs/ so "how do you work?" is grounded
  migrate-provenance [--apply]                           relabel legacy authored rows (moot post-reset)
  purge-raw <digest> --confirm | --list                  owner-gated TRUE deletion of a tombstoned blob

SECURITY / AUDIT
  gen-attestation-keys <supervisor|owner>                generate + print an Ed25519 signing seed
  verify-attestation <id> | --all | --list               verify the attestation chain
  check-imports                                          the import-firewall lint (Invariant 2)
  run-with-secrets <cmd...>                              inject Keychain secrets, then exec <cmd...>

OUROBOROS STACK (on demand — models wake when needed)
  stack up|status|check|down                             embedder service + OpenCode wiring + checks
  mcp                                                    the Ambassador's MCP server on stdio
  dream | relate                                         one dreaming pass | signed relation edges
  vault-sync | dialogue-sync                             re-ingest notes | pull Open WebUI chats
  lanes [code-observe|code-embed|dialogue]               edge-producing lanes, in-process
  reembed --confirm                                      re-embed everything (model change)
  tick [pause <30m|2h|1d> | resume | status]             the heartbeat: one beat, or its kill switch

EVAL / OPS
  eval [--bless]                                         score the frozen golden set
  build-sandbox-image [tag]                              build the scientific-libs sandbox image
  keep-awake [-- <cmd>]                                  block system sleep (optionally just for <cmd>)
  watch                                                  ⚠ deprecated — superseded by `start`

  help | -h | --help                                     this message
"""

_PALACE = ("start", "stop", "status", "reset", "deploy", "dream", "relate", "lanes", "reembed",
           "vault-sync", "dialogue-sync", "tick", "queue", "query", "ingest-chat", "code-seed",
           "code-backfill", "code-rebuild")

# verb -> python script under scripts/ (run with the verb as argv[1] when it is a palace verb)
PY_VERBS: dict[str, str] = {
    **dict.fromkeys(_PALACE, "palace.py"),
    "stack": "stack.py", "mcp": "palace_mcp.py", "talk": "talk.py", "supersede": "supersede.py",
    "monitor": "monitor.py", "shell": "shell.py", "sandbox": "sandbox.py", "ingest": "ingest.py",
    "ingest-self-knowledge": "ingest_self_knowledge.py",
    "migrate-provenance": "migrate_provenance_split.py", "purge-raw": "purge_raw.py",
    "gen-attestation-keys": "gen_attestation_keys.py",
    "verify-attestation": "verify_attestation.py", "check-imports": "check_imports.py",
    "eval": "eval.py", "watch": "watch.py",
}
# verb -> shell script under scripts/ (exec'd)
SH_VERBS: dict[str, str] = {
    "run-with-secrets": "run_with_secrets.sh", "build-sandbox-image": "build_sandbox_image.sh",
    "keep-awake": "keep-awake.sh",
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    verb = args.pop(0) if args else ""
    if verb in ("", "help", "-h", "--help"):
        sys.stdout.write(USAGE)
        return 0
    if verb in SH_VERBS:
        script = str(HERE / SH_VERBS[verb])
        os.execv(script, [script, *args])
    if verb in PY_VERBS:
        script = str(HERE / PY_VERBS[verb])
        if verb == "watch":
            sys.stderr.write("mind-palace: scripts/watch.py is superseded by 'mind-palace start'; "
                             "running it standalone anyway.\n")
        sys.argv = [script, *([verb] if PY_VERBS[verb] == "palace.py" else []), *args]
        sys.path.insert(0, str(HERE.parent))
        try:
            runpy.run_path(script, run_name="__main__")
        except SystemExit as e:
            code = e.code
            return code if isinstance(code, int) else (0 if code is None else 1)
        return 0
    sys.stderr.write(f"mind-palace: unknown verb '{verb}'\n{USAGE}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
