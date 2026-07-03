"""The reversible-write effector (Zone B) — Track G item G5, blast radius small (β small).

Materializes an APPROVED class-2 effect into a **staged draft artifact** the owner can review and
delete — a draft reply, a tentative calendar hold, a staged file. Never a sent artifact: staging is
the whole action, and it is reversible by construction (`rollback` unlinks the draft). Sending a
staged draft is a *different*, irreversible, full-gated act (G6, `ops/effect_exec.py`) — this
effector has no send path at all.

Same Zone-B discipline as the sensing effector:

  * **It never imports core** (nor ops, nor scheduler). It is driven by an approved
    `(actuator, params)` pair the orchestrator passes in; the wire shape is agreed, not imported
    (Invariant 2 — this process has no vault handle to leak, and stages only local files).
  * **Traversal is unrepresentable.** The on-disk name is chosen by THIS effector (`<ref>.draft`),
    never by a param: a `stage_file` whose `name` is "../../etc/authorized_keys" still lands as a
    single file inside `drafts_dir` (the requested name rides *inside* the envelope, as data). The
    staged path is re-checked to resolve within `drafts_dir` before any write (fail-closed).
  * **OFF by default**: `enabled=False` on the dataclass and `[effectors] enabled=false` in config
    — `build_reversible_write_effector` refuses, and a directly-constructed instance refuses to
    stage. And even enabled, it is unreachable in the wired system until ε is raised past sensing.

A staged draft is a JSON envelope — `{actuator, params, staged_at}` — not the final artifact: the
drafts area is a review surface, so what lands is the *proposed* effect, awaiting a separate act to
realize it. That keeps staging reversible (delete the envelope) and safe (no arbitrary path write).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# The reversible (class-2) actuators this effector knows how to stage. An actuator outside this set
# is refused (fail-closed) — the effector stages only what it has a reviewed materialization for.
_STAGEABLE = frozenset({"draft_reply", "calendar_hold", "stage_file"})

# A ref is an effector-chosen id: a uuid hex, or a caller id constrained to a safe filename token.
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class EffectorsDisabled(RuntimeError):
    """The reversible-write effector is off (`enabled=False` / `[effectors] enabled=false`)."""


class NotStageableError(ValueError):
    """An actuator this effector has no reviewed materialization for was offered to it."""


def _utcnow() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


@dataclass
class ReversibleWriteEffector:
    """Stages approved reversible writes into `drafts_dir`, one JSON envelope each. `stage` returns
    the artifact ref the `EffectLedger` records; `rollback` removes it. Local, no network."""

    drafts_dir: Path
    enabled: bool = False

    def __post_init__(self) -> None:
        self.drafts_dir = Path(self.drafts_dir)
        self.drafts_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, ref: str) -> Path:
        """The staged path for `ref`, re-checked to resolve strictly within `drafts_dir` (a second
        line after the `_SAFE_REF` shape check — traversal is refused, never honored)."""
        if not _SAFE_REF.match(ref):
            raise ValueError(f"unsafe artifact ref {ref!r}")
        path = (self.drafts_dir / f"{ref}.draft").resolve()
        root = self.drafts_dir.resolve()
        if root not in path.parents:
            raise ValueError(f"artifact ref {ref!r} escapes the drafts dir")
        return path

    def stage(self, actuator: str, params: dict, *, ref: str | None = None) -> str:
        """Stage one approved reversible write as a draft envelope. Returns the artifact ref (for
        the ledger + rollback). Refuses (fail-closed) unless `enabled`, and refuses an actuator with
        no reviewed materialization. The requested filename (for `stage_file`) is stored as DATA in
        the envelope — never used as the on-disk path — so no param can direct the write."""
        if not self.enabled:
            raise EffectorsDisabled("reversible-write effector is off — [effectors] enabled=false")
        if actuator not in _STAGEABLE:
            raise NotStageableError(
                f"actuator {actuator!r} is not a stageable reversible write "
                f"(stageable: {sorted(_STAGEABLE)})"
            )
        ref = ref or uuid4().hex
        path = self._path_for(ref)
        envelope = {"actuator": actuator, "params": dict(params), "staged_at": _utcnow()}
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)                       # atomic: a reviewer never sees a partial draft
        return ref

    def rollback(self, ref: str) -> bool:
        """Remove a staged draft (the reversible undo). Returns True if an artifact was removed,
        False if it was already gone — idempotent, so a double-rollback is not an error."""
        path = self._path_for(ref)
        existed = path.exists()
        path.unlink(missing_ok=True)
        return existed

    def read(self, ref: str) -> dict | None:
        """Read back a staged draft envelope (for the owner's review surface). None if absent."""
        path = self._path_for(ref)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


def build_reversible_write_effector(config: object | None = None) -> ReversibleWriteEffector:
    """Wire the effector from config (lazy import, mirroring the sensing builder). REFUSES unless
    `[effectors] enabled` — the whole Track-G surface is OFF by default."""
    from config.loader import get_config

    cfg = config or get_config()
    if not cfg.effectors.enabled:
        raise EffectorsDisabled("[effectors] enabled is false — reversible-write effector off")
    return ReversibleWriteEffector(drafts_dir=cfg.effectors.drafts_dir, enabled=True)
