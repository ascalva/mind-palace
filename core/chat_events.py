# ── Family 1 boundary (labelings & information-flow) · symbols in docs/NOTATION.md ──
# OBJECT:    the L1 projector of the dialogue sensor (bp-069 Item 3, dn-agent-taxonomy §2.4c) — a
#            deterministic, MODEL-FREE reduction of a session transcript to its ordered ACTION LOG:
#            WHAT was performed, in order (owner_prompt → response → commit(sha) → file_edit(path) →
#            build_plan(id) → …). It reads the FULL raw transcript (turns + the tool records L0
#            strips), never a model, and emits only STRUCTURAL refs.
# INVARIANT: no verbatim content leaves in a `ref` — a ref is a sha, a path, an artifact-id, or a
#            turn_index. The extraction rules are an ALLOW-LIST of mind-palace-aware tool shapes;
#            an unknown tool FAILS OPEN to a recorded `tool_use(name)`, never a dropped action.
# ENFORCED:  static (pure reduction; no store write here — the projector hands events to the store)
#            + guard (tests/unit/test_chat_events.py pins the exact ordered typed sequence and that
#            no ref carries content).
"""The L1 action log — WHAT was performed in a Claude Code session, in order (bp-069 Item 3).

`extract_events` is a pure, model-free reduction of one raw transcript to a typed, ordered
`list[ChatEvent]`: owner prompts and agent responses (from the text turns — the SAME grain L0 reads)
interleaved with the actions the agent performed (from the tool records L0 strips). Every `ref` is
STRUCTURAL — a commit sha, a file path, a build-plan/finding id, or a turn_index — never verbatim
prose ("for prose, read L0"). The rules are an allow-list of the tool shapes this repo uses; an
unrecognised tool RECORDS a generic `tool_use(name)` (fail-open — never a dropped action).

`ChatEventProjector.project` drives it over the corpus: for each session it reads the session's OWN
raw via the chatlog's `transcript_digest` (the projection fiber back into L0) and re-extracts iff
that digest changed (replace-per-session — a grown session's log stays consistent). It is the
substrate the integrator (bp-071) reuses for its tool-record parse.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from core.stores.chat_events import ChatEventStore
from core.stores.chatlog import ChatlogStore
from core.stores.rawstore import RawStore

# role → actor (the L0 mapping, reused). NEVER a provenance input (chat rows stay OBSERVED, §2.3).
_ROLE_TO_ACTOR = {"user": "owner", "assistant": "agent"}

# The typed action vocabulary (grep-visible — a §10 shape change is not silent). `ratify` is
# RESERVED: a draft→ratified flip is a design-note edit whose status change is content-level, so v1
# records the touch as `design_note` and defers explicit ratify detection (plan §11 — event taxonomy
# breadth re-enters when bp-071 needs a finer kind).
EVENT_KINDS = frozenset({
    "prompt", "response", "commit", "file_edit", "build_plan", "finding", "design_note",
    "ratify", "tool_use",
})

# Tools that write a file — their `input.file_path` is the structural ref (classified below).
_FILE_WRITE_TOOLS = frozenset({"Edit", "MultiEdit", "Write", "NotebookEdit"})

# A commit sha inside a `git commit` result: `[branch abc1234] message` (or detached-HEAD form).
_COMMIT_SHA = re.compile(r"\[[^\]]*?\b([0-9a-f]{7,40})\b[^\]]*?\]")
_BP_ID = re.compile(r"(bp-\d+)")
_FINDING_ID = re.compile(r"(finding-\d+)")


@dataclass(frozen=True)
class ChatEvent:
    """One typed action in one session's log. `ref` is STRUCTURAL (sha|path|artifact-id|turn_index),
    never verbatim content. `turn_index` is the L0 backpointer — the dialogue turn the action ran
    under (the projection fiber)."""

    session_id: str
    order: int           # position in this session's action log (0-based, dense)
    actor: str           # owner | agent
    kind: str            # one of EVENT_KINDS
    ref: str             # sha | path | artifact-id | turn_index — NEVER content
    turn_index: int      # the L0 turn this action ran under (backpointer into the chatlog)


def _classify_file_write(file_path: str) -> tuple[str, str]:
    """A file-writing tool's (kind, ref) from its target path — mind-palace-aware, structural. A
    build-plan / finding / design-note write is typed as such (ref = the artifact id or note name);
    anything else is a generic `file_edit` (ref = the path). A path is structure, never content."""
    posix = file_path.replace("\\", "/")
    if "docs/build-plans/" in posix and (m := _BP_ID.search(posix)):
        return "build_plan", m.group(1)
    if "docs/findings/" in posix and (m := _FINDING_ID.search(posix)):
        return "finding", m.group(1)
    if "docs/design-notes/" in posix:
        return "design_note", PurePosixPath(posix).name
    return "file_edit", posix


def _tool_event(session_id: str, order: int, turn: int, block: dict[str, Any],
                results: dict[str, str]) -> ChatEvent:
    """One `tool_use` block → its typed action (agent actor). `results` maps a tool_use id → its
    result text (first pass) so a `git commit` resolves the sha it produced. Unknown tools fail open
    to `tool_use(name)`."""
    name = str(block.get("name", ""))
    raw_input = block.get("input")
    tool_input = raw_input if isinstance(raw_input, dict) else {}
    if name == "Bash":
        command = str(tool_input.get("command", ""))
        if "git commit" in command:
            result = results.get(str(block.get("id", "")), "")
            m = _COMMIT_SHA.search(result)
            return ChatEvent(session_id, order, "agent", "commit", m.group(1) if m else "", turn)
        return ChatEvent(session_id, order, "agent", "tool_use", "Bash", turn)
    if name in _FILE_WRITE_TOOLS:
        kind, ref = _classify_file_write(str(tool_input.get("file_path", "")))
        return ChatEvent(session_id, order, "agent", kind, ref, turn)
    return ChatEvent(session_id, order, "agent", "tool_use", name, turn)   # fail-open: recorded


def _collect_results(records: list[dict[str, Any]]) -> dict[str, str]:
    """First pass: tool_use id → its result text, so a later `commit` action resolves its sha. The
    result text is used ONLY to extract the structural sha — it is never stored."""
    out: dict[str, str] = {}
    for record in records:
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tid = str(block.get("tool_use_id", ""))
                out[tid] = _result_text(block.get("content"))
    return out


def _result_text(content: Any) -> str:
    """A tool_result block's content text — a bare string, or the joined `text` sub-blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(b.get("text", "")) for b in content
                        if isinstance(b, dict) and b.get("type") == "text")
    return ""


def extract_events(session_id: str, transcript_text: str) -> list[ChatEvent]:
    """Reduce one raw transcript to its ordered, typed action log (pure, model-free). Torn/garbage
    lines are skipped (JSONDecodeError-tolerant, like the L0 parse). `turn_index` tracks the L0
    chatlog's turn counter — incremented on each non-empty text utterance — so a tool action carries
    the dialogue turn it ran under. `order` is a dense per-session counter over all events."""
    records: list[dict[str, Any]] = []
    for line in transcript_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)

    results = _collect_results(records)
    events: list[ChatEvent] = []
    order = 0
    l0_turn = 0                              # mirrors parse_transcript's per-text-block counter
    for record in records:
        actor = _ROLE_TO_ACTOR.get(str(record.get("type", "")))
        if actor is None:
            continue                               # not a dialogue record (system/mode/…)
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in _content_blocks(content):
            btype = block.get("type")
            if btype == "text":
                if not str(block.get("text", "")).strip():
                    continue                       # empty text — no L0 utterance, no event
                kind = "prompt" if actor == "owner" else "response"
                events.append(ChatEvent(session_id, order, actor, kind, str(l0_turn), l0_turn))
                order += 1
                l0_turn += 1
            elif btype == "tool_use":              # agent action (tool records in assistant turns)
                events.append(_tool_event(session_id, order, l0_turn, block, results))
                order += 1
            # tool_result / thinking / unknown blocks emit nothing (results already collected)
    return events


def _content_blocks(content: Any) -> list[dict[str, Any]]:
    """`message.content` as a block list. A legacy bare string ⇒ one synthetic text block (matches
    L0's legacy-shape handling), so a bare-string user message still logs as a `prompt`."""
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


@dataclass
class ChatEventProjector:
    """Drives `extract_events` over the corpus, incrementally. Reads each session's OWN raw via the
    chatlog's latest `transcript_digest` (the projection fiber), re-extracts iff it changed,
    and replaces the session's log wholesale. Model-free; the sole writer of the L1 store."""

    chatlog: ChatlogStore
    rawstore: RawStore
    store: ChatEventStore

    def project(self, *, max_sessions: int) -> int:
        """Re-project up to `max_sessions` sessions whose transcript changed since last extraction.
        Returns the number of sessions (re)projected. A session is skipped when its latest digest
        equals the stored one (no churn). The latest raw (a grown session's newest, fullest blob) is
        the last row's `transcript_digest`."""
        projected = 0
        for session_id in self.chatlog.sessions():
            if projected >= max_sessions:
                break
            rows = self.chatlog.rows_for(session_id)
            if not rows:
                continue
            digest = str(rows[-1]["transcript_digest"])         # the newest (fullest) raw for it
            if self.store.digest_for(session_id) == digest:
                continue                                        # unchanged — nothing to re-extract
            raw = self.rawstore.get(digest).decode("utf-8")
            self.store.replace_session(session_id, extract_events(session_id, raw), digest)
            projected += 1
        return projected


def build_chat_event_projector(config: Any = None) -> ChatEventProjector:
    """Wire the projector's handles: the L0 chatlog (read), the immutable rawstore (read), the L1
    store (write) — all DIALOGUE-stratum, model-free. Same-species as `build_chat_sensor`."""
    from core.config import get_config
    from core.stores.chat_events import open_chat_event_store
    from core.stores.chatlog import open_chatlog_store

    cfg = config or get_config()
    return ChatEventProjector(
        chatlog=open_chatlog_store(cfg),
        rawstore=RawStore(cfg.paths.raw_store),
        store=open_chat_event_store(cfg),
    )
