# Data Schema

Polyglot persistence (BUILD-SPEC §8). Each store is independently replaceable; access
is scoped in code (CONVENTIONS), not by convention. This doc tracks the live schema.

## Telemetry — DuckDB (`core/stores/telemetry.py`)

Quantitative time-series. **System vitals only at launch** — the system is itself a
sensor source. Body/health sensors are a deferred, dormant adapter (§20.6).

Current `SCHEMA_VERSION = 1`.

### `vitals` — system vitals (active)
| column   | type      | notes |
|----------|-----------|-------|
| ts       | TIMESTAMP | naive UTC |
| metric   | VARCHAR   | e.g. `mem.available_gb`, `cpu.percent`, `proc.rss_gb`, `load.1m` |
| value    | DOUBLE    | |
| unit     | VARCHAR   | e.g. `GB`, `%`, `procs` |
| source   | VARCHAR   | emitter, e.g. `vitals` |
| labels   | VARCHAR   | JSON object or NULL |

Metrics emitted now (`core/vitals.py`): `mem.total_gb`, `mem.available_gb`,
`mem.used_pct`, `cpu.percent`, `proc.rss_gb`, `load.1m`. Queue depth, model-load time,
error rates, and cron durations join as those subsystems land (Phases 3+).

### `sensor_readings` — body/health adapter target (DORMANT)
Defined now so a wearable can later emit into the same store without rework; no adapter
writes to it yet. Columns: `ts, sensor, metric, value, unit, meta`. Kept structurally
separate from `vitals`.

### `schema_migrations`
`version INTEGER PRIMARY KEY, applied_at TIMESTAMP`. Bump `SCHEMA_VERSION` and add a
migration step when the schema changes.

### Scoped access
`TelemetryWriter` exposes only writes; `TelemetryReader` only reads. The wrong access
is structurally impossible (e.g. the introspection agents get a reader; the vitals
emitter gets a writer), per CONVENTIONS.

## Derived store — SQLite (`core/stores/derived.py`)

The **INTERPRETED** layer (§8): artifacts the *system* inferred, kept separate and
provenance-marked from the owner's authored ground truth. Lands Phase 7 (dreaming + curator).

### `interpreted_artifacts`
| column     | type | notes |
|------------|------|-------|
| id         | TEXT PK | content-derived (`sha256(kind|subkind|sorted(subjects))[:16]`) → re-runs are idempotent |
| kind       | TEXT | `dream` (theme synthesis) \| `finding` (curator) |
| subkind    | TEXT | finding type: `near_duplicate` \| `prune_candidate` \| `contradiction` |
| provenance | TEXT | **always `interpreted`** — `add()` has no provenance parameter, so this store cannot hold authored truth (the §8 firewall, structural) |
| summary    | TEXT | the dream reflection / the finding detail |
| subjects   | TEXT | JSON array of note titles the artifact concerns |
| data       | TEXT | JSON, kind-specific (e.g. `{similarity, digests}`) |
| created_at | TEXT | naive UTC ISO |

**Regenerable:** `reset()` drops every artifact; a fresh dreaming/curation run rebuilds it
from the immutable corpus. Never holds anything not derivable from the raw + vector stores.

## Reserved (future phases)
- **Job/state/gate — SQLite** (Phase 3, landed): durable job table + scheduler state. The
  propose/approve/validate ledger, rollback metadata, and persisted-agent registry grow with
  Phases 5/10 (`core/factory/registry.py`, `ops/gate.py` seams exist).
