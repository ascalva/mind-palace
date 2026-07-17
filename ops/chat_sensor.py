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

Open-session handling (Q4): `active_session_id` (this process's own transcript among the
files) is excluded — a mid-append session is out of v1 (a session is frozen once ingested;
re-ingest of a grown open session is out of scope). Backfill (D2) processes every transcript
except the active one. Cut-time exclusion of open sessions is bp-064's certificate concern.

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


def parse_transcript(text: str) -> tuple[ChatUtterance, ...]:
    """JSONL transcript text → utterance-grain readings (CS-3), tool exhaust stripped.

    Deterministic and model-free. Keeps `text` blocks of `user`/`assistant` records ONLY;
    `tool_use`/`tool_result`/`thinking` are stripped structurally, as is any unknown block
    type (allow-list). Handles both `message.content` shapes (Q1): a block list, and a legacy
    bare string (⇒ one text utterance). `turn_index` is contiguous per session in file
    (extraction) order — the chain position (CS-4); the wall `timestamp` is a bookmark only,
    never an ordering key (Law C4). Empty/whitespace-only text is skipped (no null utterance).
    """
    digest = _transcript_digest(text)
    out: list[ChatUtterance] = []
    turn = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
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
    return tuple(out)


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
    """The pass's honest tally — no silent cap: refused/skipped sessions are NAMED."""

    sessions_ingested: int = 0
    utterances_added: int = 0
    transcripts_retained: int = 0        # raw blobs newly written this pass (dedup ⇒ 0 on re-run)
    refused_sessions: list[str] = field(default_factory=list)   # a secret matched → whole-session
    skipped_active: str | None = None    # the excluded open session (Q4), if present

    def __str__(self) -> str:
        return (f"chat-sensor: sessions={self.sessions_ingested} "
                f"utterances={self.utterances_added} retained={self.transcripts_retained} "
                f"refused={len(self.refused_sessions)} "
                f"active_skipped={'yes' if self.skipped_active else 'no'}")


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

    def _ingest(self, path: Path, report: ChatSyncReport) -> None:
        """Retain-raw-first, then extract-guard-store ONE transcript (CS-1 → CS-3 → CS-2).

        A whole session is the refusal unit: if the guard matches ANY utterance, nothing from
        the session is stored (the raw is still retained — re-ingest after guard tuning
        recovers it) and the session is NAMED in the report. This is strictly more fail-closed
        than a per-row skip, and keeps a partially-stored session from ever existing."""
        session_id = path.stem
        text = path.read_text(encoding="utf-8")
        # CS-1: byte-verbatim retention BEFORE any extraction. The digest is the utterance's
        # recoverability anchor; dedup means a re-run retains nothing new.
        _digest, is_new = self.rawstore.add_text(text)
        if is_new:
            report.transcripts_retained += 1
        utterances = parse_transcript(text)
        for u in utterances:                              # CS-3 guard, fail-closed, whole-session
            if self.guard.scan(u.text):
                report.refused_sessions.append(session_id)
                raise SecretInUtteranceError(
                    f"candidate secret in session {session_id} at turn {u.turn_index} "
                    f"(pattern {self.guard.matched_pattern(u.text)}) — row refused whole, "
                    f"session not stored (raw retained; re-ingest after guard tuning)")
        added = self.store.add_batch(utterances)
        if utterances:
            report.sessions_ingested += 1
        report.utterances_added += added

    def _run(self, paths: Iterable[Path]) -> ChatSyncReport:
        """The shared loop: exclude the active session (Q4), ingest each, catching a refusal
        per-session so one secret-bearing transcript never aborts the whole pass (the refused
        session is named in the report — no silent cap)."""
        report = ChatSyncReport()
        for path in paths:
            if self.active_session_id is not None and path.stem == self.active_session_id:
                report.skipped_active = path.stem
                continue
            try:
                self._ingest(path, report)
            except SecretInUtteranceError:
                continue                                  # named in report.refused_sessions
        return report

    def sync(self) -> ChatSyncReport:
        """Incremental pass: retain-raw-first then extract, for each CLOSED session not yet
        ingested (a session already in the store is frozen, Q4 — skipped cheaply). Excludes
        the active session. Idempotent (the store's identity key makes a re-run a no-op even
        without the skip)."""
        known = set(self.store.sessions())
        paths = [p for p in self._transcript_paths() if p.stem not in known]
        return self._run(paths)

    def backfill(self) -> ChatSyncReport:
        """Full backfill (D2 default): every transcript except the active session. Idempotent
        — a second `backfill()` writes 0 new rows (the store's identity key) and retains 0 new
        raw blobs (rawstore dedup)."""
        return self._run(self._transcript_paths())


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
