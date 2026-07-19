"""The chat sensor — a model-less pipeline agent over the local Claude Code transcripts.

φ_chat: the sole interpreter of the session-transcript instrument (dn-chat-sensor CS-1/CS-2/
CS-3). Deterministic, model-free — no inference, no embedder, no network, no vault, no
attestor (v1, Q6). It is the SAME species as the vault watcher (`core/ingest/sync.py`) and
the code sensor (`ops/code_sensor.py`), reading LOCAL files already on this machine (bright
line #11 — no edge handoff, Q3) and writing local stores. It holds four handles and nothing
else: the transcripts dir (read-only), the immutable rawstore, the OBSERVED-only chatlog
store, and the fail-closed secret guard.

The pipeline, per closed session (CS-1 verbatim-first — retention BEFORE extraction):
  1. read the transcript, store it BYTE-VERBATIM in the immutable rawstore
     (`core/stores/rawstore.py` — content-addressed, dedup by SHA-256). The on-disk CLI
     transcript dir is EPHEMERAL (the CLI prunes by retention period); the rawstore is the
     archive. Every utterance is recoverable from its `transcript_digest`.
  2. extract utterance-grain prose (`text` blocks of `user`/`assistant` records only),
     stripping `tool_use`/`tool_result` STRUCTURALLY (CS-3 — anti-apophenia: tool output
     quotes repo files verbatim, embedding it manufactures spurious conductance) and
     `thinking` in v1 (Q2 — internal monologue, not a dialogue utterance; same apophenia +
     secret risk as tool blocks; parked).
  3. scan each surviving utterance with the secret guard (CS-3 fail-closed backstop, bright
     line #10). A match REFUSES the row whole and names the session (`SecretInUtteranceError`)
     — never truncated-and-stored. The primary defense is the structural tool-strip; the
     guard is the backstop over prose that survived it.
  4. land the extraction in the OBSERVED-only chatlog store (idempotent by (session_id,
     turn_index) — a frozen session re-ingested is a no-op).

Growth-aware (finding-0109 — the freeze-once fix, bp-069): the system is real-time, so a session
left open for hours must ingest its tail, not freeze at first read. `sync()` retains-then-extracts
EVERY transcript and lets the rawstore `is_new` signal skip the unchanged and re-ingest the grown
(`add_batch` is idempotent by `(session_id, turn_index)`, so a grown re-parse appends ONLY the new
turns). This AMENDS ratified dn-chat-sensor Q4 (freeze-once) — the owner is the design authority.

Open-session handling (Q4): `active_session_id` (this process's own transcript among the files) is
still excluded — the daemon does not ingest its own live session. Cut-time exclusion of open
sessions is bp-064's certificate concern.

Spine-invisible in v1: NO chain written, NO stratum registered (bp-064, CS-4). The
`reset_targets()` registration of `data/chatlog.sqlite` (corpus-side wipe target; rebuilds
by re-ingest from the IMMUTABLE rawstore, which is NOT reset) is the ORCHESTRATOR's
post-merge step (`ops/lifecycle/launcher.py` is outside this plan's write_scope).

The sole future reader is the ratified cross-strata correlator (CS-5 — its own scoped
grant, surfacing-only); this plan wires NO reader.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.loader import Config
from core.stores.chatlog import ChatlogStore, ChatUtterance, open_chatlog_store
from core.stores.rawstore import RawStore

# role → speaker (CS-3 metadata mapping). NEVER a provenance input (CS-2 firewall).
_ROLE_TO_SPEAKER = {"user": "owner", "assistant": "agent"}

# The block types the extractor knows (Q1). Extraction is an ALLOW-LIST — only `text` is
# kept; `thinking`/`tool_use`/`tool_result` are stripped structurally, and any NEW block type
# is dropped by the same construction (fail-closed — prose is always a `text` block, so a new
# type can carry no lost utterance). Listed so a §10 shape-change is grep-visible, not silent.
_KNOWN_BLOCK_TYPES = frozenset({"text", "thinking", "tool_use", "tool_result"})


def _transcript_digest(text: str) -> str:
    """The rawstore identity for a transcript's text — SHA-256 of its UTF-8 bytes, matching
    `RawStore.add_text` exactly (`core/stores/rawstore.py:42`), so the utterance's
    `transcript_digest` equals the digest the sensor stores the raw under (CS-1
    recoverability) by construction."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ParseOutcome:
    """The accounting-grade result of parsing one transcript (bp-069 §2.5 parity gauge): the
    utterances PLUS the tallies the total-accounting report needs to bucket a file that yielded no
    utterance. `decoded_records` counts lines that parsed as a JSON object (dialogue or not);
    `decode_failures` counts lines that raised `JSONDecodeError` (a torn/garbage line — skipped,
    never fatal). A file with 0 utterances is `empty` if any record decoded, `unparseable` if none
    did (only torn/garbage lines)."""

    utterances: tuple[ChatUtterance, ...]
    decoded_records: int
    decode_failures: int


def _parse_lines(text: str) -> ParseOutcome:
    """The parse, with the accounting tallies (bp-069). Torn-line tolerant: a `JSONDecodeError`
    (a live file read mid-append can catch a half-written line) is skipped and counted, never
    raised — the same record re-reads complete on the next event (a whole JSON object is one line,
    so a torn trailing line loses nothing already-committed). Extraction is otherwise the ratified
    allow-list (CS-3): `text` blocks of `user`/`assistant` records only."""
    digest = _transcript_digest(text)
    out: list[ChatUtterance] = []
    turn = 0
    decoded = 0
    failures = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            failures += 1                              # torn/garbage line — skip, count, continue
            continue
        if not isinstance(record, dict):
            continue                                   # a bare JSON scalar — not a record
        decoded += 1
        speaker = _ROLE_TO_SPEAKER.get(str(record.get("type", "")))
        if speaker is None:
            continue                                   # not a dialogue record (system/mode/…)
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        session_id = str(record.get("sessionId", ""))
        bookmark = str(record.get("timestamp", ""))
        for utterance_text in _text_blocks(message.get("content")):
            stripped = utterance_text.strip()
            if not stripped:
                continue
            out.append(ChatUtterance(
                session_id=session_id, turn_index=turn, speaker=speaker,
                text=utterance_text, transcript_digest=digest, ts_bookmark=bookmark))
            turn += 1
    return ParseOutcome(tuple(out), decoded, failures)


def parse_transcript(text: str) -> tuple[ChatUtterance, ...]:
    """JSONL transcript text → utterance-grain readings (CS-3), tool exhaust stripped.

    Deterministic and model-free. Keeps `text` blocks of `user`/`assistant` records ONLY;
    `tool_use`/`tool_result`/`thinking` are stripped structurally, as is any unknown block
    type (allow-list). Handles both `message.content` shapes (Q1): a block list, and a legacy
    bare string (⇒ one text utterance). `turn_index` is contiguous per session in file
    (extraction) order — the chain position (CS-4); the wall `timestamp` is a bookmark only,
    never an ordering key (Law C4). Empty/whitespace-only text is skipped (no null utterance).
    Torn/garbage lines are skipped (JSONDecodeError-tolerant — a live read never raises, bp-069)."""
    return _parse_lines(text).utterances


def _text_blocks(content: Any) -> list[str]:
    """The extracted prose of one `message.content` (Q1): a bare string ⇒ one utterance
    (legacy shape); a block list ⇒ the `text` blocks only, in order. Everything else
    (`thinking`/`tool_use`/`tool_result`/unknown) is dropped structurally."""
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            texts.append(str(block.get("text", "")))
    return texts


# ── The secret-scan backstop (CS-3, Q5 — authored here, no reusable scanner exists) ──────
# A conservative, HIGH-SIGNAL pattern set. It is a BACKSTOP; the primary defense is the
# structural tool-strip (secrets live in tool output, and that block class is already gone).
# Fail-closed: a match REFUSES the row whole and names the session — never truncated-and-
# stored. If these patterns false-positive at a rate that empties the corpus, that is the
# plan §10 stop-and-raise (a `design` finding — the guard's precision/recall is an owner
# call); the tool-strip stays in force meanwhile.
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # AWS access key id — the canonical AKIA + 16 base32 chars.
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # AWS secret access key, named-assignment form (the value itself is unstructured).
    ("aws-secret-access-key",
     re.compile(r"aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+]{20,}", re.IGNORECASE)),
    # PEM private key header (RSA/EC/OPENSSH/generic).
    ("pem-private-key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")),
    # `sk-`-prefixed API keys (OpenAI/Anthropic style): sk- then 20+ key chars.
    ("sk-api-key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b")),
    # A long high-entropy token bound to a secret-ish name by an assignment — the generic
    # backstop. Requires the keyword, an assignment operator, and a 32+ char opaque value, so
    # prose mentioning the word "key" does not trip it (only `key = <opaque32+>` does).
    ("keyword-bound-secret",
     re.compile(r"(?i)(?:api[_-]?key|secret|token|password|passwd|pwd)\s*[=:]\s*"
                r"['\"]?[A-Za-z0-9/+_-]{32,}")),
)


class SecretInUtteranceError(RuntimeError):
    """A candidate secret matched an extracted utterance (CS-3, bright line #10). Raised with
    the session id named so a refused session is auditable (never silently dropped). The
    matched value is NOT included in the message — a guard must never log the secret it caught
    (bright line #10, second half)."""


@dataclass
class ChatSecretGuard:
    """The fail-closed secret backstop (CS-3). `scan(text) -> True` iff a candidate secret
    matched — the caller REFUSES the row (never truncates). Stateless and deterministic."""

    def scan(self, text: str) -> bool:
        return any(pat.search(text) for _, pat in _SECRET_PATTERNS)

    def matched_pattern(self, text: str) -> str | None:
        """The NAME of the first matching pattern (never the value) — for the refusal message
        and dry-run diagnostics. None ⇒ clean."""
        for name, pat in _SECRET_PATTERNS:
            if pat.search(text):
                return name
        return None


@dataclass
class ChatSyncReport:
    """The pass's TOTAL accounting (dn-agent-taxonomy §2.5 parity gauge, bp-069): every transcript
    file on disk lands in EXACTLY ONE bucket — none silently skipped. The buckets partition
    `files_seen`:
      * `sessions_ingested` — a NEW session, ≥ 1 utterance stored;
      * `sessions_grown`    — an already-ingested session that gained turns (the Q4 fix);
      * `unchanged`         — content-identical (the rawstore `is_new` signal said skip — no churn);
      * `refused_sessions`  — a secret matched → the whole session is held at its pre-secret state;
      * `empty`             — parsed to 0 utterances (a system/tool-only or blank transcript);
      * `unparseable`       — every line failed to decode (a torn/garbage file);
      * `skipped_active`    — the excluded open session (Q4).
    Refused/empty/unparseable are NAMED (no silent cap). `is_fully_accounted()` is BOTH the test
    assertion surface and the ops log line — the sensor's required instrument (plan §2.5)."""

    files_seen: int = 0
    sessions_ingested: int = 0
    sessions_grown: int = 0              # already-known sessions that gained turns (Q4 fix)
    utterances_added: int = 0
    transcripts_retained: int = 0        # raw blobs newly written (is_new; dedup ⇒ 0 on re-run)
    refused_sessions: list[str] = field(default_factory=list)   # a secret matched → whole-session
    unchanged: list[str] = field(default_factory=list)          # is_new=False — nothing to do
    empty: list[str] = field(default_factory=list)              # parsed to 0 utterances
    unparseable: list[str] = field(default_factory=list)        # every line failed to decode
    skipped_active: str | None = None    # the excluded open session (Q4), if present

    def total_accounted(self) -> int:
        """The sum of the mutually-exclusive buckets — equals `files_seen` iff nothing skipped."""
        return (self.sessions_ingested + self.sessions_grown
                + len(self.refused_sessions) + len(self.unchanged)
                + len(self.empty) + len(self.unparseable)
                + (1 if self.skipped_active else 0))

    def is_fully_accounted(self) -> bool:
        """The parity gauge (plan §2.5): every seen file landed in exactly one bucket. A False here
        is the accounting law broken — a silent skip, the Item-1 falsifier."""
        return self.total_accounted() == self.files_seen

    def __str__(self) -> str:
        return (f"chat-sensor: files={self.files_seen} ingested={self.sessions_ingested} "
                f"grown={self.sessions_grown} utterances={self.utterances_added} "
                f"retained={self.transcripts_retained} unchanged={len(self.unchanged)} "
                f"refused={len(self.refused_sessions)} empty={len(self.empty)} "
                f"unparseable={len(self.unparseable)} "
                f"active_skipped={'yes' if self.skipped_active else 'no'} "
                f"accounted={'ok' if self.is_fully_accounted() else 'BROKEN'}")


@dataclass
class ChatSensor:
    """Tools are the wiring; the agent is the discipline over them (the code-sensor framing).

    Model-free, deterministic, no attestation, no edge handoff (Q3/Q6). Reads LOCAL
    transcripts, retains them verbatim (CS-1), extracts utterances with the structural
    tool-strip (CS-3), guards them fail-closed (CS-3), and lands them OBSERVED (CS-2)."""

    transcripts_dir: Path
    rawstore: RawStore
    store: ChatlogStore
    guard: ChatSecretGuard
    active_session_id: str | None = None      # the open session to EXCLUDE (Q4)

    def _transcript_paths(self) -> list[Path]:
        """The session transcripts on disk, in a stable (name-sorted) order — deterministic."""
        if not self.transcripts_dir.is_dir():
            return []
        return sorted(self.transcripts_dir.glob("*.jsonl"))

    def _ingest(self, path: Path, report: ChatSyncReport, known: set[str]) -> None:
        """Retain-raw-first, then (only if the raw is new) extract-guard-store ONE transcript
        (CS-1 → CS-3 → CS-2), bucketing it for the total accounting (bp-069 §2.5). `known` is the
        set of session ids already in the store at pass start, so a re-ingested-and-GROWN session
        is told apart from a brand-new one.

        Growth-aware (finding-0109): `is_new` from the content-addressed rawstore is the change
        signal. Unchanged ⇒ `unchanged` bucket, no re-parse (no churn). Grown ⇒ re-parse; add_batch
        appends ONLY new turns (idempotent by `(session_id, turn_index)`).

        A whole session is the refusal unit (fail-closed, bright line #10): if the guard matches ANY
        utterance the pass stores nothing NEW for the session — but turns committed in a PRIOR clean
        pass STAND (the store already holds them), so a secret arriving in a new turn holds the
        session at its pre-secret state (Q2). The raw is retained regardless (re-ingest after guard
        tuning recovers it), and the session is NAMED."""
        session_id = path.stem
        text = path.read_text(encoding="utf-8")
        # CS-1: byte-verbatim retention BEFORE any extraction. `is_new` is the growth signal — an
        # unchanged transcript hashes identically (skip, no churn); a grown one hashes anew (its
        # tail re-ingests). Retention is unconditional — even a refused/unparseable session's raw
        # is kept (the archive never depends on extraction succeeding).
        _digest, is_new = self.rawstore.add_text(text)
        if not is_new:
            report.unchanged.append(session_id)           # content-identical — nothing to do
            return
        report.transcripts_retained += 1
        outcome = _parse_lines(text)
        for u in outcome.utterances:                      # CS-3 guard, fail-closed, whole-session
            if self.guard.scan(u.text):
                report.refused_sessions.append(session_id)
                raise SecretInUtteranceError(
                    f"candidate secret in session {session_id} at turn {u.turn_index} "
                    f"(pattern {self.guard.matched_pattern(u.text)}) — row refused whole, session "
                    f"held at its pre-secret state (raw retained; re-ingest after guard tuning)")
        if not outcome.utterances:
            if outcome.decoded_records == 0 and outcome.decode_failures > 0:
                report.unparseable.append(session_id)     # nothing decoded — a torn/garbage file
            else:
                report.empty.append(session_id)           # valid records, no dialogue prose
            return
        report.utterances_added += self.store.add_batch(outcome.utterances)
        if session_id in known:
            report.sessions_grown += 1                    # Q4 fix: a grown session re-ingests
        else:
            report.sessions_ingested += 1

    def _run(self, paths: Iterable[Path]) -> ChatSyncReport:
        """The shared loop, with the total accounting (bp-069): every file counts into `files_seen`
        and lands in exactly one bucket. Excludes the active session (Q4). Catches a refusal
        per-session so one secret-bearing transcript never aborts the pass (named in the report —
        no silent cap)."""
        report = ChatSyncReport()
        known = set(self.store.sessions())                # session ids already stored at pass start
        for path in paths:
            report.files_seen += 1
            if self.active_session_id is not None and path.stem == self.active_session_id:
                report.skipped_active = path.stem
                continue
            try:
                self._ingest(path, report, known)
            except SecretInUtteranceError:
                continue                                  # named in report.refused_sessions
        return report

    def sync(self) -> ChatSyncReport:
        """Growth-aware incremental pass (finding-0109 — freeze-once REMOVED): retain-raw-first then
        extract for EVERY transcript, letting the rawstore `is_new` signal skip the unchanged and
        re-ingest the grown (the Q4 fix — a session left open no longer freezes at first ingest).
        Excludes the active session. Idempotent: a re-run over an unchanged corpus writes 0 (every
        file lands in `unchanged`)."""
        return self._run(self._transcript_paths())

    def backfill(self) -> ChatSyncReport:
        """Full pass. Since the sensor became growth-aware (finding-0109) a full pass and an
        incremental one are the SAME operation — `is_new` gates the work either way — so this IS
        `sync()`, kept as a named entry for the D2 semantics and the existing call sites."""
        return self.sync()


def _default_transcripts_dir() -> Path:
    """The local Claude Code transcript dir for this repo — the CLI's cwd→dir mangling
    convention (`~/.claude/projects/<abs-cwd with '/' → '-'>`), a RESOLVED default, not a
    config-schema change (Q4/Q1). Tests inject `transcripts_dir` directly; the owner overrides
    it when the canonical repo path differs from a worktree's."""
    from config.loader import REPO_ROOT

    mangled = str(REPO_ROOT).replace("/", "-")
    return Path.home() / ".claude" / "projects" / mangled


def build_chat_sensor(config: Config | None = None, *,
                      active_session_id: str | None = None) -> ChatSensor:
    """Wire φ_chat's handles against the real transcript dir, rawstore, and chatlog store.

    `active_session_id` excludes THIS process's own open transcript (Q4). The rawstore is the
    shared corpus archive (`cfg.paths.raw_store` — the ingest/watcher convention); the chatlog
    store is the sibling `data/chatlog.sqlite`. No attestor, no edge handoff (Q3/Q6)."""
    from config.loader import get_config

    cfg = config or get_config()
    return ChatSensor(
        transcripts_dir=_default_transcripts_dir(),
        rawstore=RawStore(cfg.paths.raw_store),
        store=open_chatlog_store(cfg),
        guard=ChatSecretGuard(),
        active_session_id=active_session_id,
    )
