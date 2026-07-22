# Deskcheck queue

> **Done ≠ sealed.** A track/feature is done only when it is *deskchecked* — the builder shows
> it working (or clearly shows its true state), walks through what/how/surprises, and the
> **owner has the final say**. This board is the follow-through ledger (finding-0153). Seeded
> 2026-07-21; maintained by `/triage` and every seal. Verdict column: `PENDING` (awaiting owner
> deskcheck) · `DONE` (owner-accepted) · `NEEDS-WORK` (owner found a gap → follow-up plan/finding).

## A. Awaiting deskcheck — sealed, but never demonstrated + owner-accepted as done

| track | build state (verified 2026-07-21) | how to deskcheck it | verdict |
|---|---|---|---|
| **Sync/diac dreamers** (bp-079 D-0 · bp-080 D-1 · bp-081 H-0/H-1 · bp-082 H-2) | **built, NOT wired** — `[dream_rnd] enabled=false`; no live entry point constructs a DreamCharter (finding-0141). Diachronic exec (SD-a) parked. | show the sealed machinery + the flag; decide: wire it live (a dispatch entry point) or accept dormant-by-design like effectors | **PENDING** — likely NEEDS-WORK (built-not-delivered) |
| **Reference bookkeeper** (F-edge consistency, PD-5 — scope EXPANDED, finding-0154) | **mostly unbuilt** — minting is LIVE (`code_sensor` post-commit) but: no deferred resolution, **no external-research citations** (book→paper inert), no continuous reconciliation, no current-view (finding-0145: 950k accumulated vs 2,199 current) | show minting live + book/research citations NOT resolving + the accumulation with no served view; this is an async bookkeeper agent (librarian's sibling), not a small pass | **PENDING** — track largely incomplete |
| **Track G — effectors / hands** | built, **dormant by design** (max tier NONE, finding-0011) | confirm the dormancy is still the intended state (the *acceptable* built-not-wired — but confirm, don't assume) | **PENDING** — confirm-only |
| **Inner/outer core — M0+S1** (bp-083, bp-089) | **built + LIVE** — the two-ring ratchet runs; INNER=37 | show the inner-ring test green + the map; the M0/S1 *enforcement* half is real | **PENDING** — enforcement done; physical half is §B below |

## B. In-flight — blessed `ready`, not yet built (deskcheck on completion)

| plan | what | gate |
|---|---|---|
| bp-090 | **K1** — born-30 → `core/kernel/**` (the physical inner/outer split the M0/S1 work never did) | first; not concurrent with bp-092 |
| bp-091 | **K3** — the S1 seven into the kernel | after bp-090 SEALS |
| bp-092 | **CI-1** — the code embed lane (L0a/L0b/L1, Provenance.CODE) — *code + docstrings + comments actually embedded* | not concurrent with bp-090 |
| bp-093 | **CI-2** — retrieval/geometry/scale proof (PD-J authorship reader PULLED → finding-0151) | after bp-092 |
| bp-094 | **CI-3** — reference layer: dn-slug/finding-id/§ resolvers + inherits/calls edges | after bp-092 Item 1 |
| bp-095 | **CI-4** — the S↔F code↔design lens | after 092+093+094 AND M-C4 informative |

## C. Pending design — Fable pass, AFTER the §B builds (owner re-tiers)

| track | warrant | what the design pass decides |
|---|---|---|
| **Integrator densification** | finding-0151 | dense, version-grain dialogue→code authorship (commit-diff capture / blob-tagged writes / ComposedGraph composition). **Part of code-ingest's definition-of-done.** Also fixes general C-thinness. |
| **Deskcheck workflow** | finding-0153 | the gate + state machine + `/deskcheck` ceremony + seal-time enforcement that makes this board authoritative |
| **Reference bookkeeper agent** | finding-0154 | async librarian-sibling owning F-edge consistency across code/docs/book/external-research; deferred resolution; external citation endpoint-kind; the current-view/prune half |

## Notes

- §A entries were surfaced by investigation this session, not from a maintained ledger — which
  is the whole point (finding-0153). Going forward, every seal files its own row here.
- "Verdict = DONE" is the owner's word alone. The agent's job is to reach `ready to deskcheck`
  and present the bundle (what / how / surprises / it-working-or-its-state).
