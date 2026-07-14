# bp-030 journal

## 2026-07-13 — authored `proposed` (orchestrator)

Authored directly from `docs/brainstorms/lifecycle-cli-overhaul.md` + finding-0066 (concrete
ops/infra — no ratified design note needed). Scope: the operational-control + cleanup + status
unit of the lifecycle overhaul — Item 1 `down`/`up`/`restart` (KeepAlive-aware `bootout`/`bootstrap`,
so maintenance-down ≠ operational-stop, finding-0066), Item 2 remove the dead edge monitor
(dormant, `enabled=false`, never worked; owner redoes it later), Item 3 enrich `status`.

§3 grounded against this session's read-only recon (citations inline): the KeepAlive/bootout
semantics (`com.mind-palace.palace.plist` header); the monitor is dormant + its ONLY child-model
caller (`launcher.py:238-243`); **`snapshot.build_status` already assembles the rich status dict** →
Item 3 reuses it (the "repurpose the snapshot" insight); `children.py`/`snapshot.py` are KEPT (dormant
+ reused, not deleted — avoid churn for the future dashboard redo).

**write_scope lists its 3 test paths** (finding-0072/0071 discipline applied at authoring):
`test_lifecycle.py` (extend) + `test_lifecycle_control.py` (Item 1) + `test_status_report.py` (Item 3).

The **diagnostic** subcommand is a SEPARATE plan (bp-031), fully scoped in the brainstorm (fixed-point
integrity · store/firewall health · ingestion freshness+completeness · runtime/drift · `--deep`).
bp-031 reuses this plan's enriched `status`/`build_status` seam → sequence bp-030 first.

Model estimate opus/300k (invariant-adjacent `launcher.py` + a Zone-B deletion; falsifiers need
judgment). Awaiting the owner-only `proposed → ready` blessing. No work started.
