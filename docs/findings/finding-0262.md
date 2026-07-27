---
type: finding
id: finding-0262
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
  - docs/findings/finding-0207.md
  - docs/inbox/owner-questions.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# §2.3's grant code is a 6–8 digit secret with no bound on verification attempts — single-use burns on success, and the note never says a failure burns anything

## What

`dn-autopilot-and-delegated-blessing` §2.3 specifies the grant code as *"HMAC-style over the
capsule hash, truncated to 6–8 digits"*, and defends its transmissibility over an untrusted
channel on the grounds that *"it is useless without a matching artifact hash and it expires"*
(`docs/design-notes/dn-autopilot-and-delegated-blessing.md:247-248, :257-259`).

The note then states the single-use property, and states it **only over successful
verification**: *"Single-use is verifier-enforced: the verifier records each consumed
capsule-hash on its own side, and a second presentation fails."*
(`:267-269`). "Consumed" is the language of a *successful* redemption.

**Nothing in the note bounds the number of unsuccessful attempts.** The three stated
defences are all orthogonal to guessing:

- **hash-binding** fixes *which* code is correct; it does not make the correct code hard to find;
- **single-use** retires a code *after* it is accepted;
- **TTL** (default 72 h) is the *window* in which guessing is allowed, not a limit on it.

A verifier that answers `verify(capsule_hash, code) -> bool` without an attempt bound is an
offline-speed oracle over a keyspace of 10^6 (6 digits) to 10^8 (8 digits). Against a local
script that is a search of seconds to minutes, well inside a 72-hour TTL.

## Why it matters

The grant *is* the `proposed → ready` blessing (§2.3: *"The verifier performs the
`proposed→ready` flip, not the model"*). An adversary — including a misaligned or
prompt-injected agent on this machine, which is precisely the threat `finding-0207` names —
that can call the verifier repeatedly does not need the Keychain secret at all. It needs
patience measured in seconds. That collapses the design's central authentication claim
without ever violating invariant 1 ("the model never sees the secret").

It also collapses invariant 9 (*"A grant record without a re-verifiable attestation tag is
not a grant record"*): the attestation tag is minted **by the verifier on successful code
verification** (`:260-266`). A guessed code produces a genuine tag. The tag proves the
verifier ran, not that the owner read anything.

⚑ This is not a live vulnerability. Nothing is built: there is no verifier, no secret, and no
grant. It is a gap caught at the cheapest possible moment — during graduation, before the
plan that would build the verifier as an actor is minted. It sits in the same place, and for
the same reason, as `finding-0207`.

## Re-entry condition

The graduation wave `bp-135`–`bp-139` proceeds now: **none of the five minted plans builds a
verification oracle.** `bp-138` builds the grant's *pure core* with the secret behind an
injection-only seam and no actor, no invocation boundary, and no attempt counter to get
wrong — its §10 forbids exactly that.

This finding parks a criterion of the **un-minted** verifier-as-actor plan (the plan already
parked on `oq-0037`). **Re-entry:** the Fable-tier design pass that answers `oq-0036`/`oq-0037`
answers this at the same time, because it is the same object — the actor that holds the
secret is the actor that must count failures. That pass must decide, at minimum:

1. whether a **failed** verification consumes the capsule-hash (fail-once), or a bounded
   counter with lockout applies, or both;
2. where the counter lives such that the counting party is not the party being
   authenticated (a counter an agent can reset is not a counter — the `finding-0207`
   structure repeated one level up);
3. whether 6 digits survives any of this, or the code widens.

## Routing

`spec-defect`, `design` → **orchestrator**. Batched to `owner-questions.md` as a limb of the
existing `oq-0036`/`oq-0037` Fable pass rather than as a new standalone question: it needs the
same session, the same tier, and the same primitives already grounded there. It is **not**
blocking — the parked plan was already un-minted for two other reasons.

⚑ The note is `status: ratified` and therefore agent-immutable under A8. This finding does not
edit it. Whatever the ruling, §2.3 changes by a **superseding note or an owner-ratified
amendment**, never by an edit.
