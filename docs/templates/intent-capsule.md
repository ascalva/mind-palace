<!-- The INTENT capsule (dn-autopilot-and-delegated-blessing §2.2) — the SMART readback a
grant binds to. NOT docs/templates/capsule.md, which is the brainstorm SESSION capsule
(chat-side protocol §8). Different artifact, different lifecycle, no shared machinery.
Caps (bp-120 §6, hard errors): <= 40 lines, <= 300 words of the CANONICAL text — the whole
file, this comment included. Canonical form: UTF-8 strict, CRLF/CR -> LF, trailing spaces
and blank lines stripped, exactly one final newline. capsule_hash = sha256(canonical).hex.
Fill every field; a bare <placeholder> counts as EMPTY and `capsule.py validate` fails. -->

goal: <one sentence — Specific>
definition-of-done: <runnable; the exact thing the deskcheck later evaluates — Measurable>
achievable: <write-surface summary + P1-P5 predicate results + no open decisions>
relevant: <trace to settled intent — Relevant>
time-bound: <budget ceiling + base commit + TTL>
falsifier: <the observation that would prove the run wrong>
non-goals:
  - <explicit non-goal; grade an inferred one [INFERENCE]>
  - <one per line; the plan's §9 must carry these and no others>
readback: <the readback close — owner recognition>
