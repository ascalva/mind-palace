---
type: design-note
id: dn-wasm-sandbox-runtime
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-27
updated: 2026-07-03
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — WASM sandbox runtime (wasmtime + Pyodide)

*Family tag → family 1 (labelings & flow): the sandbox is powerless — 𝒜(exec) ∩ {net, vault, cred} = ∅ (I4); a WASM runtime for pure compute. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** partially built (corrected 2026-07-03 audit — the original "design only" header was
stale). `WasmRunner` + `RoutingRunner` now exist with a **real wasmtime execution path**
(`core/sandbox/runner.py`; `build_runner` has `wasm`/`routing` branches) — no longer the empty seam
this note first scoped. They are **dormant and fail-closed**: `available()` returns False until a
WASI CPython (`python.wasm`) asset is placed, so `RoutingRunner` falls back to Podman and nothing
runs under WASM yet. Remaining before it is a live substrate: place/pin the `python.wasm` asset,
benchmark it against the Podman warm pool, and close Podman's own empirical gap (`docs/runbook.md` →
"Sandbox runtime"). The design below still governs finishing the work.

---

## 0. The gap this closes

Phase 4 shipped one substrate: rootless Podman, network-off, no-mount, capability-dropped
(`core/sandbox/policy.py` `_isolation_flags`). That satisfies Invariant 4 today. The
`WasmRunner` stub and the `runtime: "wasm"` branch of `build_runner()` exist as a *seam*
only — calling any of its methods raises `NotImplementedError`. CONVENTIONS.md and
BUILD-SPEC §11 both name **wasmtime + Pyodide** as the intended pure-compute path
("strongest isolation, no syscalls"); this note is the design that seam was left for.

The gap is not "Podman is insecure" — it's that Podman's isolation is a kernel boundary
(namespaces, cgroups, seccomp, capabilities) that has to be configured correctly every
time, whereas wasmtime's is a **language-level capability boundary**: a WASM module has no
ambient access to *any* syscall, including network ones, unless the host explicitly wires
an import for it. We currently get to "no network" by dropping it; wasmtime gets there by
never having had it to drop.

| | Podman (current) | wasmtime + Pyodide (this note) |
|---|---|---|
| Isolation mechanism | Kernel: namespaces + seccomp + cap-drop | Language: no syscall imports wired at all |
| Network | Removed (`--network=none`) | Absent (no socket import exists to call) |
| Filesystem | Removed (no `-v`/`--mount`, read-only rootfs) | Absent (no filesystem import wired) |
| Startup cost | Container start (~100s of ms, amortized by warm pool) | Module instantiation (single-digit ms) |
| Language coverage | Any image (`python`, `bash`, `node`, …) | Python only, and only pure-Python-reachable packages |
| Failure mode if misconfigured | A flag is omitted → kernel boundary has a hole | N/A — there is nothing to omit; the import table is the boundary |

Neither replaces the other. Podman stays the default substrate for anything Pyodide can't
run; WASM becomes the **preferred** path for the common case (a Python snippet, no exotic
package, short-lived) once built.

---

## 1. Architecture

A wasmtime `Engine`/`Store` hosts a single WASM module: Pyodide (CPython compiled to WASM,
plus the subset of the scientific-Python stack that has WASM builds — numpy, pandas, and
similar pure-or-WASM-portable packages). The broker hands the runner Python source on
"stdin" (in practice: written into the module's linear memory, same *shape* of contract as
the existing stdin-pipe approach in `policy.py`'s `RUNTIMES["python"]`); the runner pumps
the wasmtime event loop to completion or timeout and reads stdout/stderr back out of
memory.

No socket, filesystem, clock-set, or process-spawn import is ever linked into the module's
import table. This is the WASM analogue of `--network=none --read-only --cap-drop=ALL`,
except it's not a flag that disables a capability the host *could* have granted — the
capability is simply never wired, the same way `core/` never imports `boto3` (a static,
structural absence, not a runtime-checked one).

---

## 2. Fitting the existing `SandboxRunner` Protocol

No change to `core/sandbox/runner.py`'s `SandboxRunner` Protocol, `core/sandbox/spec.py`'s
`ExecSpec`/`ExecResult`/`Limits`/`Network`, or `core/sandbox/broker.py`'s `ExecutionBroker`.
The seam was deliberately shaped to be substrate-agnostic; WASM fills it, doesn't widen it.

| Protocol method | Podman today | wasmtime tomorrow |
|---|---|---|
| `available()` | `True` (binary present check could be added) | `True` iff `wasmtime`/Pyodide assets are installed |
| `run_once(spec, policy)` | `podman run --rm -i …` | Fresh `Store` + module instantiation, run, drop the `Store` |
| `start(policy, limits, image)` | `podman run -d … sleep infinity` (warm pool) | Instantiate Pyodide once, keep the `Store` alive, parked |
| `exec_in(container, spec)` | `podman exec` into the warm container | Re-enter the parked `Store`'s interpreter with new source |
| `reset(container)` | (declared, scopes a future fresh-state-without-respawn path) | Reset Pyodide's namespace/globals dict — cheaper than Podman's equivalent, since there's no filesystem state to scrub |
| `destroy(container)` | `podman rm -f` | Drop the `Store` |

`Limits` maps loosely: wasmtime has its own memory-pages cap (`Limits.memory` converts to a
page count) and a fuel/epoch-deadline mechanism for `timeout_s` (interrupting a WASM
module doesn't need a process kill — wasmtime can preempt at a bytecode-instruction
granularity, which is *more* precise than `timeout_s` enforcement over a subprocess).
`Limits.cpus` and `Limits.pids` have no WASM equivalent (no threads, no processes) — they
become no-ops for this runner, asserted-ignored rather than silently dropped, mirroring how
`_guard_network` already raises rather than ignoring an unsupported `Network` value.

---

## 3. Routing: per-execution, not per-broker

Today routing is static: `build_broker()` reads `[sandbox] runtime` once and builds exactly
one runner (`build_runner(sb.runtime)`); every `ExecSpec` in the process's lifetime goes
through that runner. Adding WASM as a *second* substrate without breaking that simplicity
needs a small `RoutingRunner` that itself implements `SandboxRunner` and holds both a
`WasmRunner` and a `PodmanRunner`:

```python
@dataclass
class RoutingRunner:
    wasm: WasmRunner
    podman: PodmanRunner

    def _pick(self, spec: ExecSpec) -> SandboxRunner:
        if spec.language == "python" and self.wasm.available() and _pyodide_compatible(spec):
            return self.wasm
        return self.podman
```

`ExecutionBroker` never learns this happened — it still calls `self.runner.run_once(spec,
policy)` against whatever `build_runner()` returned. This keeps the broker, the warm pool,
and the telemetry call untouched; `_log()` gains one more label (`runtime: "wasm"|"podman"`)
so the audit trail (§11's existing concern: every execution logged) records which substrate
actually ran the code, the same way it already records network mode.

`_pyodide_compatible(spec)` is a conservative static check, not a try-and-see: unknown or
denylisted packages route to Podman *before* execution, never as an after-the-fact retry.
Fail toward the substrate with broader coverage, not toward re-running already-executed
(possibly side-effecting-on-stdout) code twice.

---

## 4. Pyodide package-compatibility constraints

This is the actual scope-limiter, not the wasmtime plumbing:

- **Pure-Python stdlib** — full coverage. `json`, `re`, `itertools`, `dataclasses`, etc. all
  work unmodified.
- **Packages with official Pyodide/WASM builds** — numpy, pandas, and similar are usable,
  but only the versions Pyodide ships, not arbitrary PyPI versions. A package-allowlist
  (not a denylist) keeps this decidable: if a package isn't on the allowlist,
  `_pyodide_compatible()` returns `False` and Podman runs it, full stop.
- **C-extension packages without a WASM build** — unsupported. No fallback compilation;
  these always route to Podman.
- **`bash` and `node` runtimes** (`policy.py`'s other two `RUNTIMES` entries) — Pyodide is a
  Python interpreter; this note's WASM path only ever serves `language == "python"`. Bash
  and Node code always route to Podman, indefinitely — there's no proposed WASM path for them
  here.
- **Anything needing real wall-clock I/O, even loopback** — `Network.NONE` is the only mode
  either substrate supports today (`core/sandbox/spec.py`); this is unaffected by adding
  WASM. A future scoped-network grant (already flagged in `policy.py`'s `_guard_network` as
  a "deliberate, logged later extension") would need its own design note regardless of
  which substrate runs it.

---

## 5. What does NOT change

- `ExecSpec`, `ExecResult`, `Limits`, `Network` — unchanged. The WASM runner adapts to the
  existing shapes; the shapes don't grow WASM-specific fields.
  `Limits.cpus`/`Limits.pids` become asserted no-ops under WASM, not new optional fields.
- `ExecutionBroker.run()` — unchanged. Routing lives inside the runner it holds, not in the
  broker's control flow.
  `WarmPool` — unchanged in shape; a WASM-backed pool just parks instantiated `Store`s
  instead of running containers, same `acquire()`/`release(container, healthy=...)` contract.
- `[sandbox]` config schema — one new value for `runtime` (`"wasm"` already routes through
  `build_runner`'s existing `if runtime == "wasm"` branch) plus, if `RoutingRunner` lands, a
  `runtime: "auto"` value that builds the router instead of a single substrate. No renames.
- Invariant 4's guarantee (no creds, no network, no vault, data-not-actions) — held by both
  substrates; WASM does not relax it, it tightens the mechanism.

---

## 6. Open questions / risks (resolve before building, not while building)

1. **Pyodide load cost.** Loading the Pyodide runtime itself (not the user's code) has
   nontrivial startup cost — likely worth a warm-pool-equivalent (one parked `Store`,
   `reset()` between jobs) rather than instantiating fresh per `run_once`. Needs a benchmark
   against the existing Podman warm pool before claiming WASM is faster in practice, not just
   in principle.
2. **Fuel/epoch tuning.** Mapping `timeout_s` onto wasmtime's interruption mechanism needs
   real numbers (fuel-per-typical-workload) before the timeout becomes trustworthy — too
   loose and it's not a real limit, too tight and ordinary code times out.
3. **Allowlist maintenance.** The Pyodide-compatible package allowlist is a hand-maintained
   list that drifts as Pyodide ships new builds. Needs an owner-reviewed update path, not
   silent auto-expansion (same spirit as §9's "never silent" pattern elsewhere in this repo).
4. **Worth it before the empirical Podman gap closes?** `docs/runbook.md` still has Phase 4's
   `-m podman` verification pending on this machine. Standing up a second sandbox substrate
   before the first one's empirical gap is closed adds surface area without retiring any
   risk. Recommend this stays unbuilt until that closes.

---

## 7. Rough scope (when picked up)

Not a phase; sized here only so a future session can decide whether it fits in one sitting.

1. Vendor `wasmtime` (Python embedding API) + a pinned Pyodide distribution; both as
   optional deps (mirrors `watchdog`'s optional+lazy import pattern in `core/ingest/watch.py`
   — `core/` must still import cleanly with neither installed, `WasmRunner.available()`
   returns `False`).
2. Implement `WasmRunner` against the six `SandboxRunner` methods (§2 table).
3. Build + hand-write the Pyodide package allowlist (§4); a deny-by-default static check,
   unit-tested against both allowed and rejected package names — no live Pyodide needed for
   that test.
4. `RoutingRunner` (§3) + the `runtime: "auto"` config value + the one new telemetry label.
5. Property tests mirroring `policy.py`'s existing pure-function isolation tests: assert the
   WASM path never wires a network/filesystem/process import, the same way today's tests
   assert the Podman argv never carries a mount flag.
6. A `needs_wasm`-style capability marker (mirrors `needs_podman`/`needs_models`) for the one
   or two tests that need the real Pyodide asset present, so the fast suite stays fast.
