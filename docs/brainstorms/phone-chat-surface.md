# Brainstorm — the phone chat surface: an AFK front door that can only open brainstorms and findings

Captured by the orchestrator from a live owner ask (2026-07-25, session-49). Distinct from
`owner-cockpit.md` (the *desk* reading room: tmux + LazyVim) and from `command-center.md` (the
*live instrument* TUI). This is the **away-from-keyboard** surface.

## 2026-07-25 (session-49)

### The ask, verbatim

> *"is it possible to chat with you directly from my phone? and I know the claude app has claude
> code, but I can't start new chats that are independent of the current build, like maybe I have a
> question about a recent build but I just want to chat with it, or maybe this could also be a
> place where brainstorms can be born, sometimes I have an idea but I have to just write it in my
> notes app when I'm afk and remember to forward you the message, so it should have the same amount
> of context you do when you start, but the agent/chat/helper can only submit findings or
> brainstorms, and mostly relies on smaller models, more specialized in the philosophy, logic, and
> documents, not sure if through tailscale, we can have a direct messaging interface to communicate
> with you, my computer will always be on now, it's plugged in most of the times so it's on all day
> and night, the orchestrator still orchestrates, but like the command center agent, the chat agent
> should also be briefed with the latest news."*

### The real problem being solved: CAPTURE LOSS

The load-bearing sentence is *"I have to just write it in my notes app when I'm afk and remember to
forward you the message."* Ideas are being **buffered in a lossy external queue** whose flush is
manual and memory-dependent. The palace already has a phone lane in **one direction** — the exhaust
lane (`~/.mind-palace/exhaust/reports/` → Syncthing → phone) carries build reports *out*. There is
no lane *in*. This is that lane.

That reframing matters for scoping: the minimum viable version is not a chat agent at all, it is a
**capture inbox**. Chat is the enrichment.

### ⚑ The owner's write-authority instinct is EXACTLY right — and derivable, not arbitrary

*"the agent/chat/helper can only submit findings or brainstorms."*

This is precisely the constitutional boundary, not a conservative guess. The artifact chain is

    brainstorm → design note (draft→ratified) → build plan (proposed→ready→…) → journal + findings

**Brainstorms and findings are the only two artifact types that enter the chain without crossing an
owner gate.** A brainstorm is the front door; findings are *"the only channel from build back to
design, and they re-enter only through the same gate brainstorms do."* Everything else —
`draft→ratified`, `proposed→ready` — is owner-by-hand and hook-denied.

⇒ An agent restricted to brainstorms + findings **cannot violate a single gate**, by construction.
Its write authority is a strict subset of what an unprivileged session already has. That is what
makes this safe to expose on a phone, and it is worth stating as the design's central claim rather
than as a footnote. Corollary: it must NOT be able to write `docs/design-notes/**`, flip any
`status:`, or touch the foundation denylist — and the existing `gate-guard` / `scope-guard` hooks
already enforce exactly that if it runs as a normal session.

### ⚑ The briefing mechanism already exists — do not build a second one

*"it should have the same amount of context you do when you start"* and *"briefed with the latest
news."* Those artifacts are already materialized and already regenerated:

| context an orchestrator gets at start | artifact |
|---|---|
| the operational constitution | `CLAUDE.md` |
| what happened last session | `.claude/state/resume-brief.md` |
| the board, per-track phase | `docs/TRACKS.md` (derived, `scripts/board.py`) |
| what demos are owed | `docs/DESKCHECK-QUEUE.md` (derived) |
| what the owner owes a ruling on | `docs/inbox/owner-questions.md` (+ `scripts/docket.py`) |

So "briefed with the latest news" is **a read of five existing files**, not new machinery. This is
the cheapest part of the whole idea and should be built first to prove the loop.

### The transport — VERIFIED against current docs, not assumed

Checked 2026-07-25 (`code.claude.com/docs`). Four options, and they are not equivalent under
**non-negotiable 11** (*"the interface may transit a third party; the corpus never does… the private
default is local/Tailscale"*):

| option | where it runs | corpus reachable? | fits NN-11? |
|---|---|---|---|
| **Claude mobile app** | viewer/controller only | via the host session | cannot start an INDEPENDENT session — this is exactly the owner's complaint, and it is a real product limit, not a misconfiguration |
| **`claude.ai/code` (web)** | **Anthropic cloud sandbox**, clones a GitHub repo | ⚠ **NO** — cannot reach the local machine or Tailscale | ⚠ only if the corpus is already on the remote; see the open question below |
| **`claude remote-control`** | **the Mac**, locally | yes — filesystem/MCP stay local | ✅ mostly — outbound HTTPS only, no inbound ports; **but conversation history + session state are stored on Anthropic servers to sync devices** |
| **Claude Agent SDK service** | the Mac, a process the owner writes | yes | ✅✅ **the best NN-11 fit** — nothing but the owner's own network is involved; phone hits it over Tailscale |

⚑ **The NN-11 nuance that decides this, stated honestly:** the constitution permits the *interface*
to transit a third party and forbids the *corpus* from doing so. Remote Control keeps the corpus on
the Mac — but a chat **about** the corpus puts corpus excerpts into the conversation, and that
conversation syncs. So the distinction "adapters leak interactions, not the corpus" gets blurry
exactly in the use case being asked for (*"a question about a recent build"*). It is not obviously
disqualifying — the owner may well accept it, and NN-11 says opt-in — but it is a **deliberate
ruling to make, not a detail to discover later**.

The Agent SDK path has no such ambiguity and matches *"the private default is local/Tailscale"*
literally. It costs writing a small always-on service.

### The model tier

*"mostly relies on smaller models, more specialized in the philosophy, logic, and documents."*
Fits the local-runtime work already in flight (`bp-115`…`118`, `dn-local-model-runtime`) and is
bounded by **non-negotiable 8** (≤2 resident models, ~20–24 GB usable; the scheduler refuses
breaching work). A phone-facing chat model is a **third** resident demand competing with the
embedder and the chat tier — so residency is a real constraint on this design, not an
implementation detail. `bp-116`'s process manager is the component that would arbitrate it.

### Open questions

1. **Where does this live in the artifact chain?** There are already
   `dn-ambassador-interpretation-and-flow` and `dn-ambassador-as-reasoning-agent`, and Track B
   (Ambassador) is built. **Is this a new track, or the Ambassador growing a phone transport?** Not
   read at capture time — settle before graduating anything.
2. **Is the corpus already on a remote?** Pushing to `origin` is routine, so if `origin` is GitHub
   the corpus already rests off-machine, which changes the NN-11 calculus for `claude.ai/code`
   substantially. Worth stating explicitly rather than assuming either way.
3. **Authentication.** NN-12 sets the precedent for the voice adapter (owner-initiated, pre-
   registered number, passphrase before personalized content). A phone chat surface reaching the
   corpus deserves an analogous bar; Tailscale identity may or may not be deemed sufficient alone.
4. **Does it read the corpus, or only write to it?** The ask implies read (*"a question about a
   recent build"*). Read access is the part that carries NN-11 weight; a **write-only capture
   inbox** carries almost none. That asymmetry suggests shipping in two stages.

### Suggested shape (not a plan)

1. **Capture-only inbox first.** Phone → an endpoint → appends a timestamped capsule to
   `docs/brainstorms/<topic>.md` or files a finding. No read access, no model needed, kills the
   notes-app buffer immediately. Almost all of the value, almost none of the risk.
2. **Then briefed read-only chat** over the five existing context files.
3. **Then** the smaller specialized model, once `bp-116`'s process manager can arbitrate residency.

The orchestrator keeps orchestrating throughout; this surface never dispatches builds.

### Owner refinement — "a small Claude agent is my insider, that for now can also take the role of the ambassador"

Verbatim: *"in other words, a small claude agent is my insider, that for now, can also take the
role of the ambassador, I know there is risk, but the agent would be outside the core, and it's
true purpose is to only communicate with me via messages, and it would track conversations,
potentially dispatch a finding, jot down a brainstorm, answer a question I have about the latest
build, etc."*

⚑⚑ **This is not a new agent. It is the Ambassador — already ratified — plus a transport.**

`dn-ambassador-as-reasoning-agent` (**`status: ratified`**, Track B, warrant finding-0022) opens
by specifying:

> *"a pinned-scope agent (𝒜) that **reads only the mirror (π_MR)** and **proposes tasks through
> the gate** (family 3); a light consumer of the reasoning complex."*

and

> *"The Ambassador is a reasoning agent that is **computationally light, not cognitively shallow**.
> It is an agent, not a router."* … *"holds no heavy work inline; delegates expensive jobs to the
> async scheduler."*

Line up the owner's four verbs against that spec:

| owner's ask | already specified as |
|---|---|
| *"answer a question about the latest build"* | reads **only the mirror** (π_MR) — never the raw vault |
| *"dispatch a finding" / "jot down a brainstorm"* | **proposes through the gate**, never acts directly |
| *"a small model"* | **computationally light**, delegates heavy work to the scheduler |
| *"track conversations"* | history handling is one of the open questions that note explicitly resolves |

⇒ **Settles open question (a) above: this is the Ambassador growing a phone transport, not a new
track.** Do not design a second agent; read the ratified note first.

#### ⚑ Naming the risk precisely — it is NN-2, and "outside the core" is necessary but NOT sufficient

The owner said *"I know there is risk, but the agent would be outside the core."* Correct instinct,
incomplete as stated. **Non-negotiable 2**: *"Network and private data never share a component.
Only `edge/` touches the network; it never reads the vault."*

Outside-the-core means it lives in `edge/` — and NN-2 then **forbids that same component from
reading the vault**. So the risk is not diffuse; it is one specific, already-legislated boundary:
*a component cannot be both the thing that talks to the phone and the thing that reads private
data.* A single "insider" that messages the owner **and** reads the corpus to answer him would
violate NN-2 directly, no matter how small the model is or how good its intentions.

**The resolution already exists and is the same one the note specifies:** split along the mirror.
- the **transport** sits in `edge/` (`edge/interface` and `edge/bridge` already exist) and holds
  **no** corpus access;
- the **Ambassador** reasons over **π_MR — the mirror projection, not the vault** — and proposes;
- they meet at a bounded seam, exactly like the effector layer's propose-never-send with
  `MirrorView` tailoring.

This is the same shape as NN-3 (*the model advises; code acts*) and the existing `ObservedView` /
`MirrorView` seams. Nothing new has to be invented — the design's whole job is to say **what π_MR
must carry** for the questions the owner actually wants answered.

#### ⚑ The one genuinely open design question this exposes

*"Answer a question I have about the latest build"* is only satisfiable if **build state is inside
the mirror**. Much of what the owner would ask about — `docs/TRACKS.md`, the resume brief, a plan's
§7, a journal — is **repo material, not vault material**, so it plausibly sits on the permitted
side of NN-2 without any widening. But that has to be **established, not assumed**: the note says
π_MR, and if π_MR today projects only the corpus, then answering build questions either needs the
projection widened (a design change with a constitutional argument attached) or needs the build
artifacts classified as non-vault (a *cheaper* and probably correct move, but still a ruling).

⇒ **Next step is a read of `dn-ambassador-as-reasoning-agent` in full plus whatever defines π_MR**,
before any plan. The capture-inbox stage (write-only, stage 1 above) is unaffected by this question
and can proceed independently — another argument for shipping it first.
