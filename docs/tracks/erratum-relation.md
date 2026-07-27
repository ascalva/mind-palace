---
type: track
slug: erratum-relation
title: Erratum relation — correction as supersession ∧ warranted retraction
status: active
warrant: null
audit_refs: []
dod:
  - dn-erratum-relation ratified (owner) — DONE 2026-07-27
  - the erratum relation built as a typed, owner-warranted, append-only store honoring E1–E8
  - the `(I − Ε)` factor and π_valid present in the temporal operator algebra, with the commutation property tested on a NON-EMPTY erratum set
  - the chat lane's default view provably stops serving erratum-targeted rows (the §7 three-census check, on a fixture)
  - the live 139-row correction act performed by the owner, or explicitly declined
backlog_deskcheck: null
links:
  - docs/design-notes/erratum-relation.md
  - docs/design-notes/chat-sensor.md
  - docs/design-notes/vector-membership-store.md
  - docs/brainstorms/the-unchecked-claim.md
  - docs/brainstorms/the-false-success-rule.md
---
# Track — Erratum relation (correction as a composition)

The identity card for the erratum track, minted at **graduation** of the already-ratified
`dn-erratum-relation` (2026-07-27), because the note carried no board coordinate and its
plans would otherwise render as orphans. ⚑ **The owner renames or rejects this coordinate**
— it is a graduation-time convenience, following the `scored-beliefs` precedent (a track
minted by an agent alongside its founding note, adjudicated by the owner later).

**Scope:** the relation that expresses *"this record was wrong at write time"* — the
append-only, warranted, unary erratum record and its invariants E1–E8; the composition law
`correction(r) = supersession(r → r′) ∧ erratum(r)`; the `(I − Ε)` algebra factor and the
`π_valid = π_active ∘ (I − Ε)` projection; the belief-query / validity-query split; and the
chat stratum's semantics as the first concrete customer (the 139 hook-feedback rows
mis-attributed to `speaker='owner'`).

**Not in scope:** the erratum's physical storage home, the widened-PK-vs-membership-fibers
question, and whether "in the default view" is a row flag or a membership property — all
three are **panel-dependent** on `dn-vector-membership-store`, which is `draft` and returned
from a three-seat adversarial panel as BLOCK · BLOCK · RATIFY-WITH-AMENDMENTS. Also out of
scope: purge (disjoint by E7), the `OwnerVerdict` taxonomy (parked at `dn-recursive-strata`),
and any store-level erratum against a ratified design note (PD-4 — the owner-hand amendment
gate is that carrier).

**Standing dependency:** the back-correction of the live 139 rows requires φ_chat 2.0.0, a
widened identity, and a re-projection over the rawstore. All three wait on the membership
panel **and** on the ingestion queue, which is wedged (1,766 queued, one `code_sync` job
stuck `running` since 2026-07-25). This track builds the relation and the read discipline;
it does not perform the live correction act, which is the owner's to fire.
