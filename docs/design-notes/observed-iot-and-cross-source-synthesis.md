---
type: design-note
id: dn-observed-iot-and-cross-source-synthesis
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-27
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Observed IoT sources + cross-source synthesis

*Family tag → family 1 (the observed label) + family 5 (cross-source synthesis): IoT/observed data kept out of the mirror; the correlator as a capability distinct from the Dreamer. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only. Extends `observed-data-and-the-assistant-tier.md` and the
dormant Phase-0 `sensor_readings` DuckDB schema. Honor when the assistant tier and
advisor agents land (Phase 5+). The cross-source correlator is a separate capability
from the dreamer — this note draws that line clearly.

---

## 0. The load-bearing rule

**Dreamers do not combine data sources.** The dreamer operates on a single
provenance-homogeneous view — `MirrorView`, authored content only. Biometric data
is `observed`; it is invisible to the dreamer by construction (`observed ∉
MIRROR_READABLE`). A dreamer that could read biometric data would conflate "what
the owner wrote" with "what the owner's body measured," corrupting the mirror's
entire purpose. The firewall holds at the dreamer boundary — structurally, not by
convention.

**Cross-source synthesis is a separate capability** — a *correlator* — that reads
`interpreted` dream outputs (already derived, safe) alongside aggregated `observed`
features, and produces `interpreted` correlations. It never merges the provenance
classes; it finds the relationship between their independently-derived signals.

---

## 1. Observed IoT sources

### 1a. Oura Ring (biometric exemplar)

**What it provides:** sleep stages + quality, HRV (heart rate variability), resting
heart rate, SpO2, skin temperature, activity, readiness scores. All continuous,
time-series, body-measured — paradigmatically `observed`.

**Two ingest paths:**

- **Official API (Oura v2):** personal access token, REST JSON polling. Clean and
  stable. Tradeoff: raw biometric data transits Oura's cloud before you fetch it —
  same class as iCloud Sync (vendor sees data before you do). Flagged; owner chooses.

- **Local Bluetooth extraction (preferred):** open-source BLE projects read the ring
  directly without the Oura app or cloud. Data never leaves the owner's devices
  before it lands in the local store. More setup; better aligned with the
  sealed-private philosophy. Worth it for biometric data specifically.

**Credentials:** personal access token in Keychain/edge layer, never in the sealed
core, never in an agent. The bridge (Zone B) polls; the core reads the already-landed
local store. Same pattern as the research airlock.

### 1b. Storage — the dormant Phase-0 slot

The `sensor_readings` table in `core/stores/telemetry.py` (DuckDB) is already in the
schema, dormant since Phase 0. Biometric IoT data extends it:

```
sensor_readings(
  ts          TIMESTAMPTZ,
  source      TEXT,          -- 'oura', 'phone_accelerometer', …
  metric      TEXT,          -- 'hrv', 'sleep_score', 'resting_hr', …
  value       DOUBLE,
  unit        TEXT,
  raw_json    JSON           -- full API payload, preserved
)
```

Provenance is implicit in the table — `sensor_readings` is `observed` by definition;
there is no provenance column because the wrong provenance is unrepresentable here.
This is the same structural pattern as `DerivedStore` (no provenance param ⇒ wrong
provenance unrepresentable).

### 1c. Normalization layer

Raw Oura JSON → normalizer → structured feature rows. What to extract:
- **Daily aggregates:** sleep score, HRV (RMSSD overnight), resting HR, readiness,
  activity calories, steps, temperature deviation.
- **Intranight resolution:** sleep stage sequence (wake/light/deep/REM) for pattern
  analysis.
- **Derived signals:** 7-day HRV rolling mean, sleep consistency score — computed
  deterministically, stored as `observed` rows (they're derived from observed, not
  authored).

The normalizer lives in `edge/` or a dedicated `core/ingest/biometric.py` — it
processes into the `sensor_readings` table. Core never imports the API client.

---

## 2. Cross-source synthesis — the correlator (NOT the dreamer)

### What it reads

| Source | Provenance | How accessed |
|--------|-----------|--------------|
| Dream outputs | `interpreted` | `DerivedStore` (safe to read — already derived) |
| Biometric features | `observed` | `sensor_readings` DuckDB |
| Authored corpus metadata | `authored` | Only aggregate/statistical — never raw text |

The correlator **never passes raw authored text to a model alongside observed data.**
It works with derived signals (dream theme-centroids, interpreted cluster labels,
authored-note-count time series) — not with the notes themselves. The firewall holds
on the text.

### What it produces

`interpreted` correlation records, stored in `DerivedStore`. Examples:

- "Creative-output volume (authored notes/week) is inversely correlated with HRV
  over 30-day windows (r = −0.62). Low-HRV weeks precede low-output weeks by 3–5
  days."
- "Dream cluster 'isolation / disconnection' co-occurs with sleep fragmentation
  (>30min wake-after-sleep-onset) at 2.3× base rate."
- "Readiness score <60 correlates with a 40% reduction in philosophical-musing
  note frequency the following day."

These are `interpreted`, confidence-decayed, grounded in the biometric and derived
signals that produced them. They are **never claimed as causal** — correlation only,
surfaced to the owner as an advisory signal.

### Safety rules

- Correlator inputs: interpreted + observed only. Never raw authored text.
- Outputs: `interpreted` always. Never `authored`, never `observed`.
- Consequential-advice-defers applies: health correlations surface with explicit
  uncertainty and "consult a professional" framing.
- The correlator has no write path to the mirror or the authored stores — read-only
  cross those two stores, write-only to `DerivedStore`.

---

## 3. Architectural position

```
authored mirror  ──→  dreamer  ──→  interpreted dream outputs ──┐
                                                                 │
observed biometric ──────────────────────────────────────────────┼──→  correlator ──→  interpreted correlations
(sensor_readings)                                                │
                                                                 │
                         (no direct path authored↔observed)     │
```

The correlator is the **only** component that reads across provenance classes, and it
does so via derived/aggregated signals, never raw text. The dreamer never sees
observed data. Observed data never enters the mirror.

---

## 4. Other IoT sources (same pattern)

All follow the same template: `observed` provenance, `sensor_readings` table, edge
ingest, correlator access only — never the dreamer, never the mirror.

- **Phone sensors** (accelerometer, GPS patterns, screen time via iOS Screen Time
  API): activity rhythms, location patterns, device-use cadence.
- **Financial transactions** (read-only aggregation API — no transaction scope):
  spending categories, merchant patterns, location-of-purchase. Correlator can find
  "categories you spend on spike before note-writing surges" without ever showing
  a transaction to a model.
- **Social media analytics** (export/API, owner-controlled): engagement, posting
  cadence, topic distribution. Fragile signal — social algorithms optimize for
  engagement, not authenticity — treat with documented skepticism in correlator
  outputs.
- **Photography metadata** (Lightroom/iCloud catalog export): shoot frequency, time
  of day, location clusters. Film photography rhythm is a genuine creative-output
  signal.
- **Google Analytics** (if applicable): reading patterns, search queries (from
  exported data), topic interests.

The correlator's job across all of these: find the relationships between the
owner's *observed* behavioral signals and the *interpreted* patterns from their
authored core — and surface them as `interpreted` correlations, confidence-bounded,
never causal claims.

---

## 5. What this is NOT

- **Not a surveillance system.** The owner controls every data source; each is
  opt-in; credentials stay local. The correlator's outputs are for the owner's
  benefit and reflection, not for any third party.
- **Not causal inference.** Correlations are surfaced as correlations. The system
  has no causal model and does not claim one.
- **Not a health advisor.** Health correlations defer to professionals. The system
  can say "your HRV pattern looks like it may warrant attention"; it cannot diagnose,
  prescribe, or advise specific health actions.
