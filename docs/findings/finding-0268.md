---
type: finding
id: finding-0268
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/roles/orchestrator/readings.md
  - scripts/handoff.py
  - docs/findings/finding-0243.md
  - docs/findings/finding-0249.md
ftype: spec-fidelity
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# A readings row containing an escaped pipe is silently dropped — the MEASURED half of the seat loses rows without saying so

## What

`readings.md` rows are `| timestamp | command | result |`. A command that legitimately contains a
pipe character — anything ending `| wc -l`, `| head`, `| grep` — must escape it as `\|`, which is the
correct markdown way to put a literal pipe in a table cell.

⚑ **The parser splits the row on `|` without honouring the escape, so the row gains extra columns,
fails to match the expected shape, and is discarded — with no warning, no error, and no count.**

MEASURED during this pass, by accident, and then deliberately:

- Five rows were appended. Three of them contained `\|`.
- The row census went from 62 to **64**, not to 67. **Exactly the three escaped-pipe rows vanished.**
- Neither the pane render nor `--lint` mentioned it. `--lint` reported `9 of 64 rows are
  future-dated` — a confident, specific, and quietly wrong denominator.
- Rewriting the three commands to avoid the pipe (`… --standalone, line count (BEFORE …)`) restored
  the census to **67** and all three rows rendered.

The command strings that were lost were `bash .claude/hooks/session-brief.sh --standalone | wc -l` —
i.e. **the seat's own compaction before/after measurement**, the one artifact this pass was
explicitly sent to record.

## Why it matters

⚑ **A measurement you believe you recorded, and did not, is worse than one you never took.** The
whole point of splitting the seat into a NARRATIVE half and a MEASURED half is that the measured
half is the trustworthy one — `handoff.md` renders "the latest row per command" precisely so a stale
reading advertises its age instead of impersonating a current fact. A row that is silently discarded
does something worse than impersonate: it makes the *absence* of a measurement indistinguishable
from never having run it, and the author walks away believing the record was made.

⚑ **The affected rows are systematically the most valuable ones.** A pipe in a command is the
signature of a *measurement* rather than a status check — `| wc -l`, `| wc -c`, `| grep -c` are how
sizes and counts get taken. So the failure is biased: it drops disproportionately the rows that
carry quantities, which is exactly the class §2.5 sends to this file in the first place.

This is `finding-0249`'s class again — a check reporting success while its claim is untested — but
one layer down: here it is the *data ingestion* that fails silently, so every downstream verdict
(`--lint`'s denominator, the pane's "latest per command") is computed over a set nobody was told was
incomplete.

## Re-entry condition

Reopens whenever a row is appended whose command contains a pipe — which is unavoidable for size and
count measurements, so in practice: immediately, and every session. Concretely it closes when either
(a) the parser honours `\|`, or (b) the parser **refuses loudly** on a row it cannot parse instead of
discarding it. ⚑ **(b) is sufficient and is the cheaper, more important half** — the silent discard
is the defect; the escape handling is a convenience. A row census that does not match the file's row
count should redden.

**Workaround until then, and it must be stated because the file is append-only:** do not put a raw
or escaped pipe in a readings command cell. Describe the pipeline in words (`…, line count`). The
three rows this pass wrote have already been rewritten this way; no row was lost from the record.

## Routing

`spec-fidelity` → the **orchestrator**. It is a defect in the seat's own tooling, no active plan owns
`scripts/handoff.py`, and it is closely coupled to `finding-0267` (both are cases of an instrument on
this seat reporting green over a set it never actually examined). The two should be repaired together
and would make a small, well-bounded plan alongside `finding-0243`'s future-dated-row lint.
