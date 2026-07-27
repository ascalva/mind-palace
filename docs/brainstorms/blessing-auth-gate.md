# blessing-auth-gate

## 2026-07-26T00:00:00Z

```capsule
topic: blessing-auth-gate
date: 2026-07-26

seed: |
  Owner, on finding-0206: "we can now use an MFA auth code, we came back via all the aws talk, auth
  created from aws, not from computer, each code and its user is tracked."
  Then, on oq-0040/oq-0036: "again, can't we solve this via MFA? an auth gate."

  Three open items, one proposed mechanism ⇒ design-note-shaped, not three separate answers.

⚑⚑ THE DISTINCTION THAT DECIDES THE DESIGN — MFA answers "WHO", not "FROM WHAT": |
  - **finding-0206 = AUTHENTICITY.** "Did the owner actually authorise this flip, or did an agent
    forge it?" Today nothing can tell: an agent with shell writes the same bytes, and git authorship
    is the owner's name on agent commits too (verified — every commit in this session is authored
    `Alberto Serrano-Calva`). ⇒ **MFA/signature solves this decisively.** It introduces a factor the
    agent structurally cannot possess, because the seed is not on the machine the agent runs on.
  - **oq-0040 / oq-0036 = PROVENANCE.** "Is there a committed `proposed` predecessor to diff
    against?" ⇒ **MFA does NOT solve this.** A perfectly authenticated flip can still be a
    from-nothing blessing: the owner could sign a plan that never existed as `proposed`. Signing
    proves *who acted*, not *what state preceded the act*.

⚑ BUT SIGNING THE TRANSITION UNIFIES ALL THREE: |
  Do not sign the ACT; sign the TRANSITION:

      sig over  (plan_id, from_status, from_content_hash, to_status, to_content_hash)

  - forged flip      -> no valid signature                    (finding-0206)
  - from-nothing     -> no `from_content_hash` exists to sign (oq-0040)
  - no grant record  -> the signature IS the grant record     (oq-0036)

  A from-nothing blessing becomes UNEXPRESSIBLE rather than merely detectable, because the
  pre-image hash is part of what is signed. That is the difference between a check and a structure.

⚑ WHERE IT IS VERIFIED IS THE WHOLE BALLGAME: |
  A local check of a remote factor is still a local check — an agent with shell can patch the
  verifier. Mitigation with existing precedent: **verify in CI**, outside the agent's reach. The
  deploy gate ALREADY has a remote attestation leg (`ops/ci_witness.py`, gate 6), so a
  CI-verified blessing signature is the same shape as machinery that already exists, not a new
  trust anchor.

⚑ AND THE OPTION THE OWNER KEEPS WALKING PAST — for THIS gate, local may beat AWS: |
  He reaches for AWS because the KMS thread got there first. But blessing is a LOCAL, FREQUENT,
  OFFLINE-CAPABLE act (he batch-blessed nine plans at once on 2026-07-26), whereas decrypting an
  effector credential is rare and already cloud-bound.
  A **Secure-Enclave key with `userPresence`** gives the identical security property — a factor the
  agent cannot produce — with NO network dependency: it works on a plane, and when AWS is down.
  ⇒ Probably: SEP for blessing (local, frequent), AWS MFA for effector credentials (oq-0057's (c)).
  Same principle, different substrate, chosen by the act's availability profile.

open_questions:
  - ⚑ TOTP CODES ARE REPLAYABLE inside their window unless consumed. The owner already said "each
    code and its user is tracked" — that tracking is LOAD-BEARING, not hygiene: an agent that
    observes a code being typed can reuse it within ~30-90s. Signing over content sidesteps this
    entirely, which is another argument for signature-over-code.
  - AWS exposes no "verify this TOTP" API. The real flow is `sts get-session-token --serial-number
    --token-code` yielding creds carrying `aws:MultiFactorAuthPresent=true`, which then call
    `kms:Sign` on an MFA-conditioned key. Buildable and standard — but it is a FLOW, not a call.
  - ⚑ A stolen session token still signs. Minimum duration is 900s, which narrows but does not
    close it. HONEST FRAMING: this does not make forgery impossible for a determined local
    adversary — it converts gate-crossing from something that can happen by ACCIDENT OR DRIFT into
    something requiring DELIBERATE CREDENTIAL THEFT. For the actual threat model (agent overreach,
    a bug, drift — finding-0109's failure mode) that is decisive.
  - PROPORTIONALITY: per-plan signing would make a nine-plan batch blessing painful. Sign per
    BATCH, or make the signature cover a set of transitions.
  - Does oq-0040's cheap half still land regardless? Making `/graduate` COMMIT the mint is a
    workflow fix that needs no cryptography and makes every blessing a one-line diff. ⚑ Worth doing
    even if signing lands, because it is what gives `from_content_hash` something to point at.

next_steps:
  - Design note, `draft`, covering finding-0206 + oq-0040 + oq-0036 together.
  - Sequence AFTER the role-state note (landed, `draft`, awaiting ratification) and the spike note.
  - ⚑ It touches `CONSTITUTION.md`-adjacent gate semantics, so the amendment lands owner-hand-only.
```
