---
name: palace
description: How to query and write to the owner's mind palace (Ouroboros) through the palace_* tools — which tool for which question, the beta dial, history, relations, and when to sync, capture, dream or relate. Use whenever answering from the owner's notes or past conversations.
---

# Using the palace

The palace answers one kind of sentence: a verb under a scope. Your scope is fixed (see
`palace_overview` → `your_grant`); the tools only let you say what it allows. The mode of each
answer — semantic, structural, temporal — follows from the verb.

## Which tool

| You want | Tool | Notes |
|---|---|---|
| Notes or turns about a topic | `palace_search(query, strata?, k?)` | Start here. Default strata = mirror + dialogue. Add `interpreted` for dreams, `reference` for code. `include_history: true` also returns superseded versions. |
| The full text of a hit | `palace_read(ref)` | Search returns snippets; read before you quote. |
| Notes near a given note | `palace_neighbors(note, beta?, k?)` | Structural, along the β-curve. `beta` 0.1 = diffuse neighbourhood (many weak paths); 10+ = the shortest-path chain. Default 1. |
| Near a topic AND near a note | `palace_hybrid(query, note, beta?, k?)` | Product of semantic and structural closeness. Good for "what else connects to this idea". |
| How a note changed | `palace_history(note, direction?)` | `forward` = from first version; `back` = newest first. |
| What supports or contradicts a note | `palace_related(note)` | Signed relations. `interpreted` ones were proposed by a model; `authored-solo` ones the owner wrote. |
| Code/doc references | `palace_reach(ref, depth?)`, `palace_origin(edge_id)` | Only populated once the code lane has run. |
| Counts and your own grant | `palace_overview()` | Cheap. Use when unsure what exists. |

`note` arguments take the `ref` a search returned (a path), a title, or a digest.

## How often

- One search per question, with the owner's own words as the query. Rephrase once if it misses;
  after two misses, say the palace has nothing on it.
- Read at most the 2–3 hits you will actually use.
- Never repeat a call on the same arguments in one conversation: the answer will not change.

## Writing

- `palace_sync_dialogue()` pulls the owner's Open WebUI chats and OpenCode sessions in (their turns stay authored, yours
  are observed). Run it when the owner refers to a recent chat you cannot find.
- `palace_sync_notes()` re-ingests the notes vault after the owner says they wrote something new.
- `palace_capture(text)` stores something YOU were asked to remember. It is filed as observed, never
  as the owner's words — so capture summaries and decisions, not quotes you invented.
- `palace_link(note_a, note_b, relation)` proposes supports / contradicts / contextualizes between
  two notes when the owner asks you to connect them.

## Heavy work (minutes; wakes the large model)

- `palace_dream()` — one dreaming pass over the notes.
- `palace_relate(max_pairs?)` — label relations among similar notes.

Only run these when the owner asks, and tell them it takes minutes.
