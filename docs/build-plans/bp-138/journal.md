# bp-138 — journal

## Pre-build notes for whoever picks this up

- ⚑ **Read §0.1 before anything else.** This is the wave's authentication path. The `depends_on`
  edge is **not technical** — nothing here imports the three plans it names. It exists so the wave
  cannot be built in an order where grant machinery precedes the machinery that occupies the seat
  the grant vacates. It is satisfiable on paper at any moment; starting anyway removes the only
  thing holding the order.

- ⚑ **This plan ships no verification oracle, and that is a security decision, not an omission.**
  `finding-0262`: §2.3's 6–8 digit code has **no bound on verification attempts** — single-use burns
  on *success* and the note never says a failure burns anything, so an unbounded caller searches
  10^8 in seconds inside a 72-hour TTL. The impoverished CLI (`selftest`, `explain` — no `verify`,
  no `derive`, no `--secret`) is the structural response. Do not add a subcommand for convenience;
  a `--secret` flag would also put a secret on a process command line, visible to any process list.

- ⚑ **`tests/unit/test_capsule.py:430` forbids `capsule.py` the `hmac` import, and it must stay
  that way.** That test is a structural guarantee `finding-0207` bought. This is a **new module**
  precisely so that guarantee is not relaxed. If an item seems to need `capsule.py`, the item is
  wrong.

- **The AST cage (Item 18) is the load-bearing gate.** The precedent at `test_capsule.py:419-427`
  already uses `ast.walk`, so nested imports are caught — but `__import__("os")`,
  `importlib.import_module("os")` and `sys.modules["os"]` are **not**. Tighten it, and prove the
  tightening reddens on fixtures using all three.

- **The domain-separation test must not be `tag != code`.** They are 64 and 8 characters; they can
  never be equal, so that check greens without testing the claim. The claim is *non-recoverability*
  — assert over windows and reductions of the tag, and demo the no-separation variant leaking.

- **Item 21's `DriftInput.drift_checked` is the point of the type.** `changed_paths=()` cannot
  distinguish "the diff found nothing" from "nobody ran the diff". The second must void the grant.

- **§10's first condition outranks finishing the work.** If any criterion would put a secret, a
  derived code, or a candidate code within a model's reach — command line, log, exception message,
  or a callable oracle — stop and raise. Do not design around it.
