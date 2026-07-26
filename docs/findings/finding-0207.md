---
type: finding
id: finding-0207
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md   # §2.3 secret bullet, §2.9 invariant 1
  - core/kernel/config/loader.py                               # :605-619 get_secret == os.environ.get
  - config/secrets_backend.py                                  # the token-capable outside facade
  - docs/findings/finding-0206.md                              # the other graduation-time defect
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# "The model never sees the secret" is asserted, not mechanised — and because the verifier is a Python script, Keychain ACL pinning cannot enforce it

## What

Found during the `/graduate` grounded pass on `dn-autopilot-and-delegated-blessing` (ratified
`b27142d`), before any plan was minted. The design's entire security rests on one property, stated
in §2.3 and restated as invariant 1 (§2.9): *"The shared secret lives in Keychain (NN-10); **the
model never sees it.** A small verifier script recomputes and compares."*

That is a statement of the constitutional rule, not of a mechanism. Grounding shows the mechanism
is unspecified, and that the two obvious mechanisms both fail.

**How secrets actually reach code here.** `core/kernel/config/loader.py:605-619` —
`get_secret(name)` is exactly `os.environ.get(name)`, documented as *"Fetch a secret from the
ENVIRONMENT (Keychain-backed in the owner's setup)"*. So the repo's standing pattern is
**env-carried**, populated from Keychain by the owner's own setup.

**Measured this session (safely — names only, never values; NN-10 forbids a model reading or
logging a secret):**

- No secret-ish env var names are visible in the agent's Bash shell today (0 matches against
  `secret|token|password|api_key|credential`). The agent's shell is clean **as things stand**.
- The `security` CLI **is** reachable non-interactively from the agent's shell: a lookup against a
  deliberately nonexistent service returned *"The specified item could not be found in the
  keychain"* — i.e. the search executed and was permitted; only the item was absent. Keychains in
  scope: `login.keychain-db`, `System.keychain`.

**Why both candidate mechanisms fail.**

1. **Env-carried secret.** §2.3 requires the verifier to read the secret *at invocation*, and the
   invoker is the agent — the agent is what runs `mfa-verifier --code …` after relaying the
   owner's code. If the secret must be in the invoking process's environment, the agent's
   environment carries it, and the agent can read it. Invariant 1 is then false by construction.
2. **⚑ Keychain ACL pinned to the verifier — fails for a non-obvious reason.** The natural fix is
   `security add-generic-password -T /path/to/verifier`, so only the verifier may read the item.
   But §4 specifies the verifier as a **script** (*"the `mfa-verifier` script (dual-mode like every
   hook: stdin JSON and standalone)"*). A script is not a binary: the ACL can only trust the
   **interpreter** (`python3` / `bash`), which is precisely what the agent invokes for everything
   else. Pinning the ACL to the interpreter grants the agent the same access it grants the
   verifier. **ACL pinning cannot separate the two so long as the verifier is a script.**

Net: an agent that can run Bash can, on either mechanism, obtain the material needed to compute
`f(secret, capsule-hash)` — and therefore mint its own grant, forge the attestation tag of §2.3,
and satisfy the very post-hoc check that tag was introduced to make unforgeable.

## Why it matters

This is the load-bearing assumption. §2.3's HMAC attestation was the design audit's strongest catch
precisely because *"narrative alone never proves a grant"* (invariant 9) — but a tag is unforgeable
only relative to a secret the forger cannot reach. If the agent can reach the secret, the
attestation degrades to exactly the prose it replaced, and every downstream property built on it
(the post-hoc Stop-gate check, laundering-proofness, the A8 analogy) degrades with it.

It also collides with the standing rule that a property is real only when something **proves** it:
an out-of-context guardrail is not a guardrail, and an unenforced invariant is not an invariant.
Invariant 1 currently has no test, no ratchet, and no named mechanism.

Note this is **not** a live vulnerability today: no autopilot secret exists, no verifier exists, and
the agent's shell carries no secrets. It is a design gap caught before the build, which is the
cheapest possible place to catch it.

## Candidate resolutions (a ruling, not the agent's to make)

- **(a) The verifier is not invoked by the agent at all — it is a separate actor.** A long-running
  local service (launchd agent) holds the secret in its own process environment; the agent's only
  affordance is to *drop a request* (capsule hash + code) into a watched path and read a verdict.
  The agent never runs the code that holds the secret, so NN-3 ("the model advises; code acts") is
  satisfied structurally rather than by convention. Highest fidelity to the note's intent; most
  build.
- **(b) Verification moves off-box to the phone.** The phone holds the secret, verifies its own
  code against the capsule hash, and pushes the flip + grant record itself. The secret never exists
  on the machine the agent runs on, so the question dissolves. Strongest property; largest change,
  and entangles the parked phone-side implementation.
- **(c) Accept a weaker, honestly-stated property.** Keep the script, and state plainly that the
  boundary is the owner's Keychain ACL and macOS's GUI approval prompt — i.e. the design resists a
  *careless* agent, not a *determined* one. Cheapest; requires amending invariant 1 to say what it
  actually guarantees, which is a constitutional edit and must not be done silently.

**⚑ Whichever way this rules, it does not block the whole graduation** — see the re-entry
condition. The verifier's *pure core* (HMAC derivation, the domain-separated attestation tag,
capsule hashing, the P1–P5 predicate evaluation) is testable with an **injected** secret and needs
no decision here. What is blocked is only *where the secret lives and who invokes the verifier*.

## Re-entry condition

Graduation proceeds. The verifier's pure core is planned now with the secret behind a **provider
seam** (injected, never read from ambient env inside the crypto path) — the same shape bp-115 used
for the inference client, so the deployment decision is a later config flip and not a rewrite. The
**wiring/deployment plan** — what actor runs the verifier, where the secret lives, and how
invariant 1 is proven — is parked and is not minted until the owner rules among (a)/(b)/(c) or
supplies a fourth. No plan may assert invariant 1 as satisfied before that ruling.

## Routing

`spec-defect` against a **ratified** note, correction is design-level and constitutional (it bears
on NN-10 and NN-3) ⇒ `design` → orchestrator → batched to `docs/inbox/owner-questions.md`. The note
is agent-immutable (A8), so any change to invariant 1 is a **superseding note**, never an edit; per
§4 Reconciliation discipline this finding is the announced correction, and any plan touching the
secret path carries a banner-on-correction citing it.
