# The query battery — 2026-11-04

dn-query-sentence-algebra §2.8 (QL-4), run read-only on the live instance at 2026-11-04T21:15:19 with `k = 5`, 24.2 s in all. Each question three ways: the flat `near`, the composed sentence, the plan. **The `endorsed` column is the owner's** — the held-out arm; the proxy beside it is mechanical and never replaces it. A majority of ties or losses for the sentence retires the layer to a planning aid (QSF-5).

**Runs today.** Run 1 (18:57) refused two questions and found two defects, fixed in b9a0058: the hypothetical overlay moved an edge's weight without moving the graph's degrees (RSP-5's guard refused it), and `as of` with a short sha matched nothing (now resolved as git does, ambiguity refused). Run 2 (21:10) had no refusals but asked `as of` at a cut from before `core/query.py` existed — a truthful empty answer to a useless question — and the hypothetical's proxy cell broke the table; both are the battery's own defects, fixed with this record. Run 3 is the day's record, below.

| # | question | wins when | proxy (measured) | endorsed (owner) |
|---|---|---|---|---|
| 1 | near-and-cited-by: the code near 'the egress guard' among what core/sealing.py cites | the endorsed cited files rank above uncited near ones; flat search interleaves them | 1 of 5 flat hits dropped by the composition |  |
| 2 | near-t1-far-t2: notes near 'retrieval' that are far from 'dreaming' | the endorsed set excludes the dreaming-near notes flat search keeps | 5 of 5 flat hits dropped by the composition |  |
| 3 | far-in-text-close-by-citation: what core/sealing.py cites that is far from 'attestation' | the endorsed cross-domain imports appear; flat search returns none | — |  |
| 4 | as-of-a-past-cut: what core/query.py cited at a past cut | the answer matches the snapshot's; the present differs | 3 now-only, 0 then-only, 14 shared |  |
| 5 | onboarding-with-bounds: how the palace stays sealed, bounded to the sealing module's neighbourhood | the endorsed direction files appear and the unbounded list's noise does not | — |  |
| 6 | a-hypothetical-s-response: the owner's note's neighbourhood if two notes were linked | the symbolic sign agrees with the numeric response on every pair | adds weight on the backbone: every effective resistance falls or holds (CND-2); diffusion ; the region gained [] and lost [] |  |
| 7 | papers-then-read: papers on Kaplansky's direct finiteness, and the one to read | the endorsed papers appear under `over curated`; the flat mirror answer has none | — |  |
| 8 | dialogue-recall: what we talked about regarding the capstone | the endorsed turns appear under `over dialogue` | — |  |

## 1. near-and-cited-by

*the code near 'the egress guard' among what core/sealing.py cites*

**flat** `top 5 near "the sealed core's egress guard" over reference` (4.29 s)

- `core/sealing.py` {qualname: , lines: 0–0}
- `tests/integrity/test_sealing.py` {qualname: , lines: 1–50}
- `scripts/ingest.py` {qualname: main, lines: 20–25}
- `tests/unit/test_worker_protocol.py` {qualname: , lines: 0–0}
- `core/runtime.py` {qualname: , lines: 1–29}

**composed** `top 5 near "the sealed core's egress guard" over reference within reach F from "core/sealing.py" depth 1` (0.39 s)

- `tests/integrity/test_sealing.py` {qualname: , lines: 1–50}
- `scripts/ingest.py` {qualname: main, lines: 20–25}
- `tests/unit/test_worker_protocol.py` {qualname: , lines: 0–0}
- `core/runtime.py` {qualname: , lines: 1–29}

<details><summary>the plan</summary>

```
plan (region):
  within
    over reference
      top 5
        near "the sealed core's egress guard"
    region:
      reach F from 'core/sealing.py' depth 1 both
clauses:
  near: semantic; Σ={reference,reference_repo} E={∅} T=(projection_event, point)
  reach F: structural; Σ={reference,reference_repo} E={F} T=(commit, point)
```

notes: the universe is the sentence's support: 146 nodes (dialogue 17, mirror 29, reference 100); 131 with vectors; the citation graph at cut e91ef | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | reference: 85 files from the 200 nearest code atoms to "the sealed core's egress guard" (the index's top 200) | degrees: the backbone among files is induced on the support; `diffuse S` over reference is not one-sided

</details>

## 2. near-t1-far-t2

*notes near 'retrieval' that are far from 'dreaming'*

**flat** `top 5 near "retrieval"` (0.33 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md` — note-2026-07-11-000843 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032312.md` — note-2026-07-12-032312 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-130454.md` — note-2026-07-14-130454 {}
- `dialogue/opencode/ses_e79d1e4f8ffeoV9753ame6kWl4/msg_1862e1b1e0010A3qloddX7LzR6` — dialogue/opencode/ses_e79d1e4f8ffeoV9753ame6kWl4/2026-10-29T05:42:10+0 {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/afe691d7-6c31-43f5-b08f-7a2c2eb68a` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}

**composed** `top 5 (near "retrieval" and far near "dreaming")` (0.36 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-23-003624.md` — note-2026-07-23-003624 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-23-005432.md` — note-2026-07-23-005432 {}
- `dialogue/opencode/ses_e96a9b760ffeCz2rWPpxM6anBU/msg_1695648ad001FJ1DtJFtFn48ZG` — dialogue/opencode/ses_e96a9b760ffeCz2rWPpxM6anBU/2026-10-23T15:17:04+0 {}
- `dialogue/opencode/ses_e96a9b760ffeCz2rWPpxM6anBU/msg_16958cb48001g6DcPHZi0c7M0R` — dialogue/opencode/ses_e96a9b760ffeCz2rWPpxM6anBU/2026-10-23T15:19:49+0 {}
- `dialogue/openwebui/a59124bb-7f9e-44f3-85ed-3c9852299336/6d943649-8a95-4ffa-be3a-bab047dc38` — dialogue/openwebui/a59124bb-7f9e-44f3-85ed-3c9852299336/2026-10-22T19: {}

<details><summary>the plan</summary>

```
plan (region):
  top 5
    and
      far
        near 'dreaming'
      near 'retrieval'
clauses:
  near: semantic; Σ={mirror_authored} E={∅} T=(projection_event, point)
  near: semantic; Σ={mirror_authored} E={∅} T=(projection_event, point)
```

notes: the universe is the sentence's support: 46 nodes (dialogue 17, mirror 29); 46 with vectors; the citation graph at cut e91ef02 | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | D and C moves at the note grain: the version chains are per note (use trace) and the causal edges key on structural endpoints

</details>

## 3. far-in-text-close-by-citation

*what core/sealing.py cites that is far from 'attestation'*

**flat** `top 5 near "attestation" over reference` (0.41 s)

- `core/attestation/verify.py` {qualname: , lines: 1–68}
- `core/attestation/store.py` {qualname: AttestationStore.get, lines: 102–107}
- `tests/integration/test_attestation_store.py` {qualname: _att, lines: 16–32}
- `core/attestation/record.py` {qualname: Attestation, lines: 51–120}
- `core/attestation/__init__.py` {qualname: , lines: 1–43}

**composed** `reach F from "core/sealing.py" depth 1 minus top 20 near "attestation" over reference` (0.40 s)

- `core/runtime.py`
- `docs/design-notes/dn-amnesiac-clones.md`
- `docs/design-notes/dn-local-model-runtime.md`
- `docs/design-notes/dn-supervision-and-liveness.md`
- `docs/design-notes/inner-outer-core.md`

<details><summary>the plan</summary>

```
plan (region):
  minus
    reach F from 'core/sealing.py' depth 1 both
    over reference
      top 20
        near 'attestation'
clauses:
  reach F: structural; Σ={reference,reference_repo} E={F} T=(commit, point)
  near: semantic; Σ={reference,reference_repo} E={∅} T=(projection_event, point)
```

notes: the universe is the sentence's support: 121 nodes (dialogue 17, mirror 29, reference 75); 90 with vectors; the citation graph at cut e91ef02 | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | reference: 44 files from the 200 nearest code atoms to 'attestation' (the index's top 200) | degrees: the backbone among files is induced on the support; `diffuse S` over reference is not one-sided

</details>

## 4. as-of-a-past-cut

*what core/query.py cited at a past cut*

**flat** `reach F from "core/query.py" depth 1` (0.33 s)

- `agents/ambassador/mcp.py` {hops: 1}
- `core/ingest/embed.py` {hops: 1}
- `core/kernel/scope.py` {hops: 1}
- `core/origin_view.py` {hops: 1}
- `core/reference_view.py` {hops: 1}

**composed** `reach F from "core/query.py" depth 1 as of "a25fc257504b"` (0.23 s)

- `agents/ambassador/mcp.py` {hops: 1}
- `core/ingest/embed.py` {hops: 1}
- `core/kernel/scope.py` {hops: 1}
- `core/origin_view.py` {hops: 1}
- `core/reference_view.py` {hops: 1}

<details><summary>the plan</summary>

```
plan (region):
  as of 'a25fc257504b'
    reach F from 'core/query.py' depth 1 both
clauses:
  reach F: structural; Σ={reference,reference_repo} E={F} T=(commit, point)
```

notes: the universe is the sentence's support: 61 nodes (dialogue 17, mirror 29, reference 15); 46 with vectors; the citation graph at cut a25fc25 | degrees: the backbone among files is induced on the support; `diffuse S` over reference is not one-sided | D and C moves at the note grain: the version chains are per note (use trace) and the causal edges key on structural endpoints

</details>

## 5. onboarding-with-bounds

*how the palace stays sealed, bounded to the sealing module's neighbourhood*

**flat** `top 5 near "how does the palace stay sealed"` (0.35 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032312.md` — note-2026-07-12-032312 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-130454.md` — note-2026-07-14-130454 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-27-231318.md` — note-2026-07-27-231318 {}
- `dialogue/opencode/ses_e79d1e4f8ffeoV9753ame6kWl4/msg_1862e1b1e0010A3qloddX7LzR6` — dialogue/opencode/ses_e79d1e4f8ffeoV9753ame6kWl4/2026-10-29T05:42:10+0 {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/9ee6b27d-1b32-4ccb-82e1-4b87a7a372` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T16: {}

**composed** `top 5 near "how does the palace stay sealed" over reference within reach F from "core/sealing.py" depth 2` (0.49 s)

- `scripts/palace_mcp.py` {qualname: main, lines: 23–27}
- `scripts/palace.py` {qualname: , lines: 1–271}

<details><summary>the plan</summary>

```
plan (region):
  within
    over reference
      top 5
        near 'how does the palace stay sealed'
    region:
      reach F from 'core/sealing.py' depth 2 both
clauses:
  near: semantic; Σ={reference,reference_repo} E={∅} T=(projection_event, point)
  reach F: structural; Σ={reference,reference_repo} E={F} T=(commit, point)
```

notes: the universe is the sentence's support: 306 nodes (dialogue 17, mirror 29, reference 260); 124 with vectors; the citation graph at cut e91ef | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | reference: 78 files from the 200 nearest code atoms to 'how does the palace stay sealed' (the index's top 200) | reference: the neighbourhood of 'core/sealing.py' was cut at the support of 200 nodes; reach past it is not answered

</details>

## 6. a-hypothetical-s-response

*the owner's note's neighbourhood if two notes were linked*

**flat** `top 5 diffuse S from "/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md"` (0.33 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md` — note-2026-07-11-000928 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032240.md` — note-2026-07-12-032240 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032312.md` — note-2026-07-12-032312 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-130834.md` — note-2026-07-14-130834 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-132412.md` — note-2026-07-14-132412 {}

**composed** `assume S "/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md" "/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md" +0.5 in top 5 diffuse S from "/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md"` (0.33 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md` — note-2026-07-11-000928 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032240.md` — note-2026-07-12-032240 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032312.md` — note-2026-07-12-032312 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-130834.md` — note-2026-07-14-130834 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-14-132412.md` — note-2026-07-14-132412 {}
- under the assumption: `note-2026-07-11-000928`, `note-2026-07-12-032240`, `note-2026-07-12-032312`, `note-2026-07-14-130834`, `note-2026-07-14-132412`

<details><summary>the plan</summary>

```
plan (region, Hyp):
  assume S '/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md' '/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md' +0.5 in
    top 5
      diffuse S from '/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md'
clauses:
  diffuse S: semantic; Σ={hypothetical,mirror_authored} E={∅} T=(projection_event, point)
assumptions:
  S '/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md' '/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md' +0.5
```

notes: the universe is the sentence's support: 46 nodes (dialogue 17, mirror 29); 46 with vectors; the citation graph at cut e91ef02 | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | D and C moves at the note grain: the version chains are per note (use trace) and the causal edges key on structural endpoints | adds weight on the backbone: every effective resistance falls or holds (CND-2); diffusion and reach can only grow

</details>

## 7. papers-then-read

*papers on Kaplansky's direct finiteness, and the one to read*

**flat** `top 5 near "Kaplansky direct finiteness conjecture"` (0.36 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md` — note-2026-07-11-000843 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000928.md` — note-2026-07-11-000928 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-12-032312.md` — note-2026-07-12-032312 {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/9ee6b27d-1b32-4ccb-82e1-4b87a7a372` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T16: {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/afe691d7-6c31-43f5-b08f-7a2c2eb68a` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}

**composed** `top 5 near "Kaplansky direct finiteness conjecture" over curated` (6.89 s)

- `reference:openai-math:A-Counterexample-to-Kaplanskys-Direct-Finiteness-Conjecture-in-Chara` — [unreviewed · OpenAI 2026-09-23] A Counterexample to Kaplansky's Direc {chunk: 0, chunks_hit: 2}
- `reference:openai-math:A-Counterexample-to-Kaplanskys-Direct-Finiteness-Conjecture-in-Odd-C` — [unreviewed · OpenAI 2026-09-26] A Counterexample to Kaplansky's Direc {chunk: 0, chunks_hit: 3}
- `reference:openai-math:A-Torsion-Free-Counterexample-to-the-Kadison-Kaplansky-Projection-Co` — [unreviewed · OpenAI 2026-09-23] A torsion-free counterexample to the  {chunk: 0, chunks_hit: 2}
- `reference:openai-math:CONTENTS` — [unreviewed · OpenAI 2026-10-26] OpenAI Math Release — the result map  {chunk: 318, chunks_hit: 9}
- `reference:openai-math:Finite-generation-for-the-Kn-local-sphere-September-24-2026` — [unreviewed · OpenAI 2026-09-24] Finite generation for the K(n)-local  {chunk: 5, chunks_hit: 12}

<details><summary>the plan</summary>

```
plan (region):
  over curated
    top 5
      near 'Kaplansky direct finiteness conjecture'
clauses:
  near: semantic; Σ={curated} E={∅} T=(projection_event, point)
```

notes: the universe is the sentence's support: 152 nodes (curated 106, dialogue 17, mirror 29); 152 with vectors; the citation graph at cut e91ef02 | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | curated: 106 papers from the 200 nearest chunks to 'Kaplansky direct finiteness conjecture' (the index's top 200) | degrees: 106 papers' censuses were cut at the index's top 200; their nearness bound is loose by that much

</details>

## 8. dialogue-recall

*what we talked about regarding the capstone*

**flat** `top 5 near "my grad capstone"` (0.40 s)

- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-11-000843.md` — note-2026-07-11-000843 {}
- `/Users/ascalva/.mind-palace/vault/janus_notes/note-2026-07-17-123350.md` — note-2026-07-17-123350 {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/776d1b45-4c64-4b84-a94e-d2e4a2310e` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T16: {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/dcc7ba7c-3fee-40e9-95a1-f58b35e696` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/afe691d7-6c31-43f5-b08f-7a2c2eb68a` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}

**composed** `top 5 near "my grad capstone" over dialogue` (0.38 s)

- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/776d1b45-4c64-4b84-a94e-d2e4a2310e` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T16: {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/dcc7ba7c-3fee-40e9-95a1-f58b35e696` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}
- `dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/afe691d7-6c31-43f5-b08f-7a2c2eb68a` — dialogue/openwebui/80cbfdf1-a89f-438e-88d6-89fa29aa4d37/2026-10-23T17: {}

<details><summary>the plan</summary>

```
plan (region):
  over dialogue
    top 5
      near 'my grad capstone'
clauses:
  near: semantic; Σ={dialogue,dialogue_artifact,dialogue_transcript} E={∅} T=(projection_event, point)
```

notes: the universe is the sentence's support: 46 nodes (dialogue 17, mirror 29); 46 with vectors; the citation graph at cut e91ef02 | the citation graph is read at e91ef02, the newest cut the store holds; it has no edges at 3badfbf | D and C moves at the note grain: the version chains are per note (use trace) and the causal edges key on structural endpoints

</details>

