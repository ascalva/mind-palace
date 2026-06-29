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


CheckFn = Callable[[object], Check]


def run_preflight(cfg, *, ollama: CheckFn = check_ollama, vault: CheckFn = check_vault,
                  podman: CheckFn = check_podman) -> Preflight:
    """Assemble the full preflight. External checks are injectable for tests."""
    checks = [*check_own(cfg), ollama(cfg), vault(cfg), podman(cfg)]
    return Preflight(checks=tuple(checks))
