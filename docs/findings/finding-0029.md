---
type: finding
id: finding-0029
status: open
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/design-notes/type-system-as-core-audit.md   # §2.5, the Tier-2 requirement this bears on
  - docs/build-plans/bp-007/plan.md                  # Item 7, §10 stop-and-raise
  - docs/build-plans/bp-007/journal.md               # the measured evidence (Item 7 entries)
ftype: discovery
origin_plan: bp-007
route: orchestrator
resolution: null
---

# finding-0029 — core's injectable dependencies are typed as concrete dataclasses, not Protocols; test doubles cannot satisfy them nominally

## What

Tier-2's load-bearing requirement (`type-system-as-core-audit.md` §2.5, verbatim: "the
load-bearing requirement is that arguments flowing into core calls are not `Any`") is
met honestly by this plan's test-side callers, but a large, systemic family of the
`tests/` package's mypy errors (measured: ~37+ of 123 `arg-type` errors at Item 7's
start, spanning at least 15 files) is caused the other direction: **core declares its
injectable collaborators as concrete `@dataclass`es, not `Protocol`s**, so a structurally
duck-typed test double can never nominally satisfy the parameter type mypy sees, no
matter how faithfully it implements the real interface.

Confirmed core classes with this shape (each used as an injected dependency at 2+ test
call sites): `core/ingest/embed.py: Embedder`, `core/models/server.py: ModelServer`,
`core/stores/vectorstore.py: VectorStore`, `core/stores/rawstore.py: RawStore`,
`core/sandbox/*.py: WasmRunner`/`PodmanRunner`, and `eval/drift.py`-adjacent
`DriftReport`. Representative errors (from the Item-7 measured baseline):

```
tests/integration/test_librarian.py:50: Argument "server" to "Librarian" has
  incompatible type "FakeServer"; expected "ModelServer"
tests/integration/test_verify.py:116: Argument "embedder" to "Librarian" has
  incompatible type "_Embedder"; expected "Embedder"
tests/unit/test_sandbox_wasm.py:64: Argument "wasm" to "RoutingRunner" has
  incompatible type "_FakeWasm"; expected "WasmRunner"
```

This is the SAME shape bp-006/bp-007 already resolved once, deliberately, in
`agents/ambassador/agent.py`'s `Ambassador.server` field: it was `object` with a
duck-type comment; this session (bp-007, Item 6) replaced it with a `ChatServer`
Protocol precisely because `tests/integration/test_librarian.py`'s `FakeServer` doesn't
inherit from the real `ModelServer` — the exact same test-authoring pattern recurs at
every site named above, but those sites are `core/**` signatures (`Embedder`,
`ModelServer`, `VectorStore`, `RawStore`, `WasmRunner`, `PodmanRunner` themselves, or the
functions/classes that take them as parameters), which is outside bp-007's write_scope
(`core/**` is explicitly denylisted; plan §10: "A Tier-2 error whose fix requires
changing a core signature — file a finding, park").

## Why it matters

Per-error `cast()`/`# type: ignore` at each of the 37+ test call sites would clear the
mypy count, but it is the anti-pattern the plan's own Item 6 falsifier names ("a fix
that silences the checker by widening a type to Any" — a cast at this volume is
adjacent to that, even though each individual cast is locally honest). It would also
scatter the SAME judgment call (concrete-class-vs-Protocol-for-an-injectable) across ~15
files instead of making it once, at each class's declaration, the way `ChatServer` did.
The design note's own §2.4 already names the general move ("capability non-amplification…
a privileged operation whose signature demands the capability object") and §2.1's
standing razor ("formalism must constrain, not decorate") both point toward Protocols
at injection boundaries being the more honest fix than either a concrete-class
requirement (over-constrains: forces inheritance a test fake can't cheaply provide) or a
scattering of casts (under-constrains: the checker stops verifying the shape at each
cast site).

## Re-entry condition

**Final measurement (Item 7 close, bp-007):** every mypy error left in `tests/**` at the
end of this plan's Item 7 — 69 errors in 20 files, entirely `arg-type` (66) and
`return-value` (3), ZERO of any other kind — is this exact shape. Confirmed classes
(each verified by reading the real signature, not inferred from the error text alone):
`core/ingest/embed.py: Embedder`, `core/models/server.py: ModelServer`,
`core/stores/vectorstore.py: VectorStore`, `core/stores/rawstore.py: RawStore`,
`core/sandbox/*.py: WasmRunner`/`PodmanRunner`/`SandboxPolicy`, `core/dreaming/dreamer.py:
Dreamer`, `core/curator/curator.py: Curator`, `core/ingest/sync.py: VaultSync`,
`scheduler/queue.py: Job` (via `cron_handlers`'s `Dreamer`/`Curator` params, not `Job`
itself — `Job`-as-parameter sites were fixable in-scope, see journal), and — confirmed
during Item 7's `operator`/`return-value` sweep, not just suspected — `eval/drift.py:
DriftReport`: `core/ops_view.py: OpsView.over`'s `drift: Callable[[], DriftReport] |
None` param rejects `tests/integrity/test_ops_view.py`'s `_FakeDrift`, which provides
only `within_tolerance`/`constitution_intact` of `DriftReport`'s five fields, by design —
a narrower Protocol is exactly what `OpsView` needs there, not the full report shape.

A future build plan with `core/**` in its write_scope (or an owner-approved narrow
exception) takes each of these confirmed classes and either (a) introduces a Protocol at
the exact call sites that accept them as injected dependencies (the `ChatServer`
precedent, `agents/ambassador/agent.py`), narrowed to only the methods actually called
through that parameter (per this session's `ops/lifecycle/launcher.py` lesson: a
Protocol should match the caller's actual usage, not the full concrete class), or (b)
records a reasoned decision that a concrete-class requirement is intentional for some of
them (e.g. if a class is never faked in tests, tightening it to a Protocol would add
complexity with no payoff) and narrows this finding's scope accordingly. Until then,
bp-007 leaves these 69 `arg-type`/`return-value` errors UNFIXED and measured-red — no
`cast`/`# type: ignore` was applied to any of them (the falsifier line was crossed
zero times: this finding's whole point is that per-site casts would be the anti-pattern,
so none were added at these specific sites — every `cast`/`# type: ignore` bp-007 DID
apply elsewhere this session was for a genuinely different, narrower reason, recorded
per-site in the Item-7 journal entries, e.g. "this Job/Config argument is a documented
placeholder the handler never reads").

## Routing

`discovery` → orchestrator. Not a `spec-defect` (the design note doesn't mandate
concrete-class parameters; this is silent on the question, so no contradiction — just an
unaddressed case the audit's build sequence didn't reach yet, since bp-006 sealed `core/`
before this pattern's full scope was visible). May promote into an amendment of
`type-system-as-core-audit.md` §2.4/§2.5 naming "injectable dependency ⇒ Protocol at the
call site" as a general convention, parallel to the T2 TypedDict convention it already
states — or into its own small build plan scoped to exactly the six classes above plus
their call sites, with `core/**` in write_scope.
