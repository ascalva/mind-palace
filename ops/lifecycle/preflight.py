"""Preflight — ensure our own components, VERIFY the external daemons (fail-closed).

Owner's chosen scope: the launcher manages the mind-palace's own pieces (data dirs, the queue,
the supervisor/watcher loop) and only *checks* the external daemons it depends on — Vault,
Ollama, podman — which have their own lifecycles (LaunchAgents / the Ollama app / a podman VM).
A required external being down is a fail-closed refusal with a clear checklist, not an attempt
to start it.

`ops/` is outside the core import firewall, so a loopback health probe here is fine (Vault and
Ollama both listen on 127.0.0.1; this never reaches off-box). The check functions are injectable
so tests assert the aggregation/fail-closed logic without any live daemon.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    required: bool      # a required check failing refuses the start
    ok: bool
    detail: str

    def render(self) -> str:
        mark = "✓" if self.ok else ("✗" if self.required else "⚠")
        return f"  {mark} {self.name}: {self.detail}"


@dataclass(frozen=True)
class Preflight:
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        """All REQUIRED checks pass (a failed optional check is a warning, not a blocker)."""
        return all(c.ok for c in self.checks if c.required)

    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.required and not c.ok]

    def render(self) -> str:
        return "\n".join(c.render() for c in self.checks)


# --- the real checks (each best-effort; never raises — a probe failure IS the signal) ---------
def check_ollama(cfg) -> Check:
    from core.models.ollama_client import OllamaClient
    try:
        v = OllamaClient(cfg.ollama).version()
        return Check("ollama", required=True, ok=True, detail=f"up ({v})")
    except Exception as e:  # noqa: BLE001 — any failure means "not ready", report it
        return Check("ollama", required=True, ok=False,
                     detail=f"unreachable at {cfg.ollama.base_url} ({e!r}) — start Ollama")


def check_vault(cfg) -> Check:
    if not getattr(cfg.secrets, "enabled", False):
        return Check("vault", required=False, ok=True, detail="not enabled ([secrets] off)")
    import urllib.error
    import urllib.request
    url = f"{cfg.secrets.addr}/v1/sys/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # noqa: S310 — loopback only
            return Check("vault", required=True, ok=(r.status == 200), detail=f"health {r.status}")
    except urllib.error.HTTPError as e:
        detail = "SEALED — run the unseal LaunchAgent" if e.code == 503 else f"health {e.code}"
        # 429 = unsealed but standby (still usable for reads)
        return Check("vault", required=True, ok=(e.code == 429), detail=detail)
    except Exception as e:  # noqa: BLE001
        return Check("vault", required=True, ok=False,
                     detail=f"unreachable at {cfg.secrets.addr} ({e!r})")


def check_podman(cfg) -> Check:
    # Warn-only: the sandbox is not on the ingest/dream/chat hot path, and the podman-machine
    # empirical gap is documented (runbook → Sandbox runtime). A missing podman doesn't block.
    if getattr(cfg.sandbox, "runtime", "podman") != "podman":
        return Check("sandbox", required=False, ok=True, detail=f"runtime={cfg.sandbox.runtime}")
    if shutil.which("podman") is None:
        return Check("sandbox", required=False, ok=False, detail="podman not found (sandbox off)")
    return Check("sandbox", required=False, ok=True, detail="podman present")


def check_own(cfg) -> list[Check]:
    checks: list[Check] = []
    data = cfg.paths.data_dir
    data.mkdir(parents=True, exist_ok=True)
    checks.append(Check("data_dir", required=True, ok=data.is_dir(), detail=str(data)))
    vp = cfg.vault.path
    notes = list(vp.glob(cfg.vault.pattern)) if vp.is_dir() else []
    # warn-only: on a first start before the re-export/sync there are simply no notes yet.
    checks.append(Check(
        "vault_notes", required=False, ok=bool(notes),
        detail=(f"{len(notes)} note(s) at {vp}" if vp.is_dir() else f"vault path missing: {vp}"),
    ))
    return checks


def _constitution_check(live: str, blessed: str | None) -> Check:
    """Pure comparison of the live Constitution fingerprint against the owner-blessed anchor.

    A mismatch is a REQUIRED (fail-closed) failure: the fixed point (Invariant 9) must not change
    silently — a divergence is either an un-blessed edit or tampering, and either way the owner
    should look before the system frames any agent with it. Overridable with `start --force`. A
    missing anchor cannot verify anything, so it warns rather than blocks.
    """
    if blessed is None:
        return Check("constitution", required=False, ok=False,
                     detail="no blessed fingerprint in baseline.json — cannot verify "
                            "(bless with `scripts/eval.py --bless`)")
    if live == blessed:
        return Check("constitution", required=True, ok=True,
                     detail=f"matches blessed anchor ({live[:12]}…)")
    return Check("constitution", required=True, ok=False,
                 detail=(f"CONSTITUTION.md {live[:12]}… ≠ blessed anchor {blessed[:12]}… — "
                         "re-bless with `scripts/eval.py --bless` if you amended it deliberately, "
                         "else investigate tampering"))


def check_constitution(cfg) -> Check:
    """Fail-closed integrity check on the fixed point: the live `CONSTITUTION.md` must match the
    owner-blessed fingerprint in `eval/golden/baseline.json` (BUILD-SPEC §15, Invariant 9).

    This runs the drift gauge's Constitution-breach comparison AT STARTUP, so a tampered or
    un-blessed Constitution is caught *before* any agent is framed with it — the runtime half that
    was missing: the fingerprint was recorded post-hoc in attestations but never compared in the
    live loop (a tampered file would otherwise be served to every agent after the next restart).
    """
    try:
        from core.constitution import constitution_fingerprint
        from eval.drift import load_drift_config
        live = constitution_fingerprint()
        blessed = load_drift_config().blessed_fingerprint
    except Exception as e:  # noqa: BLE001 — a probe failure is a warning, never a hard crash
        return Check("constitution", required=False, ok=False,
                     detail=f"could not read the blessed anchor ({e!r})")
    return _constitution_check(live, blessed)


CheckFn = Callable[[object], Check]


def run_preflight(cfg, *, ollama: CheckFn = check_ollama, vault: CheckFn = check_vault,
                  podman: CheckFn = check_podman,
                  constitution: CheckFn = check_constitution) -> Preflight:
    """Assemble the full preflight. External checks are injectable for tests."""
    checks = [*check_own(cfg), constitution(cfg), ollama(cfg), vault(cfg), podman(cfg)]
    return Preflight(checks=tuple(checks))
