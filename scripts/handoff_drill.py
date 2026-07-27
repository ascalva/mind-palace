#!/usr/bin/env python
"""F2 — the fresh-agent drill (dn-role-state-and-scoped-handoff §2.11, bp-127 Item 17).

*"A broken handoff is invisible until a real session fails; F2 makes the failure happen on
schedule, in a worktree, at grind-tier cost, where it is a red line instead of a lost session."*

The drill hands a **scope bundle and nothing else** to a history-less, tool-less agent, asks it the
three probe questions, and compares its answers to the generator's own structured answer.

    uv run scripts/handoff_drill.py --scope role:orchestrator          # the live drill
    uv run scripts/handoff_drill.py --scope role:orchestrator --record # …and append a MEASURED row
    uv run scripts/handoff_drill.py --verify-isolation                 # the drill's own falsifier
    uv run scripts/handoff_drill.py --scope role:orchestrator --replay FILE   # no spawn, no tokens

⚑ **THE DRILL'S OWN FALSIFIER COMES FIRST, and it is structural rather than hopeful.** A drill
whose agent can read the repo reports PASS forever while testing nothing — strictly worse than no
drill, because it manufactures confidence. The spawn therefore passes `--tools ""` ("Use \"\" to
disable all tools", the CLI's own help), so the agent has **no mechanism** to read anything outside
the prompt. `--verify-isolation` proves it rather than assuming it: a random nonce is written to a
file in the throwaway checkout, the agent is asked for it, and producing it is a hard failure of
the whole drill (rc 4). MEASURED 2026-07-27: the agent answered *"not present in the bundle — no
such value is recorded, so I won't fabricate one."*

⚑ **CONTAINMENT IS AN INVARIANT, NOT A CLEANUP STEP** (finding-0246 / finding-0247). Spawning an
agent in-tree fires `SessionStart`, which rewrites `.claude/state/session-baseline`: the content
jumps to HEAD (**silencing** clause (e′)) and the mtime jumps to now (**spuriously arming** check
2). A drill that perturbs the state it measures is not a drill. So `_Containment` snapshots
`(exists?, content, mtime)` and restores all three — and **asserts the gate's VERDICT is unchanged
across the spawn**, because the bytes are the mechanism and the verdict is the claim.

  ⚑ Two corrections to the naive `cp -p` recipe, both found by execution:
    * in a fresh worktree the file **does not exist**, so the correct restoration of a
      previously-absent file is **unlink**, not rewrite;
    * `--safe-mode` disables hooks outright, so `SessionStart` never fires. That is belt; the
      snapshot is braces. Both are kept, because a flag's meaning can change and an invariant
      should not depend on one.

⚑ **V1 (note §2.12) — the compare survives contact, on both fields.** `next_action` is DERIVED from
artifact state via `handoff.derive` / `_LADDER`, never a stored string (finding-0238 §V1), and a
live probe returned the exact rendered form. The compare is therefore mechanical on
`unit_in_flight` AND `next_action`; `unit_title` is prose and is never compared. The only
allowance is `_canon` — stripping formatting (backticks, quotes, whitespace, case), which is a
REPRESENTATION allowance, not a loosening. Substring and fuzzy matching are deliberately absent: a
test tuned until it passes cannot fail, which is the one thing a falsifier must be able to do.

**The judge, and where it honestly falls short of CONVENTIONS §Testing.** The subjective half is
"is this `BLOCKED:` line's answer inside the bundle?". CONVENTIONS requires a model-judge to be an
A/B against a baseline snapshot, never a cold score. This harness does **not** carry a stored
baseline: that would be a fourth standing seat artifact, and note §2.9 enumerates exactly three.
Instead the judge must **quote the answer verbatim from the bundle**, and the harness verifies the
quote is a literal substring — so a hallucinated "yes it's in there" is caught mechanically. That
is judging against the artifact rather than in the abstract, and it is stronger than a cold score;
it is still not the stored A/B the convention names. Recorded as a finding, not smoothed over.

**A `BLOCKED:` line whose answer is genuinely absent is a PASS with a defect report**, never a
failure — the drill's job is to *find* under-specified state.

This is repo-workflow tooling: it never imports `core`. It DOES import `handoff` (its sibling) for
`authoritative_segment` and `answer_json` rather than re-deriving either — a duplicated
implementation is a defect, not a nit (CONVENTIONS §Language). The cost is finding-0238's noted
hazard that importing `handoff` mutates `sys.path` and shadows the `eval` package; it is accepted
here because this script is a leaf CLI that nothing needing `eval` imports.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import handoff  # type: ignore[import-not-found]  # noqa: E402

# The grind row of the context-economy session-typing table (note §2.11: "a cheap-tier agent").
GRIND_MODEL = "sonnet"

# The one-shot, history-less, tool-less spawn. Every flag is load-bearing and none is decorative:
#   -p                        non-interactive; print and exit
#   --safe-mode               CLAUDE.md, skills, plugins, HOOKS, MCP all disabled — the "no
#                             conversation history" requirement, and the reason SessionStart
#                             never fires
#   --tools ""                no tool exists, so reading outside the bundle is impossible
#   --no-session-persistence  the session is never written to disk and cannot be resumed
#   --strict-mcp-config       no ambient MCP server can smuggle in a capability
_SPAWN_FLAGS = ("-p", "--safe-mode", "--tools", "", "--no-session-persistence",
                "--strict-mcp-config", "--output-format", "json")

PROBE = """\

Answer using ONLY the bundle above. You have no tools and no other source.

Output EXACTLY these lines and nothing else:
UNIT: <the artifact id of the unit currently in flight, or `none`>
NEXT: <the single concrete next action, as the bare command>
Then one line per blocking unknown, each in the literal form:
BLOCKED: <question>

⚑ If anything you would need is NOT in the bundle, you MUST emit it as a `BLOCKED:` line rather
than guessing, apologising, or explaining. If nothing is blocking, emit no BLOCKED lines.
"""

_JUDGE = """\
Below is a BUNDLE, then a QUESTION that a reader of the bundle said they could not answer.

Decide: is the answer to the QUESTION present in the BUNDLE?

Output EXACTLY one of:
ABSENT
PRESENT: <a verbatim quote from the bundle that answers it>

The quote must be copied character-for-character from the bundle. If you cannot copy an exact
quote that answers the question, the answer is ABSENT.

=== BUNDLE ===
{bundle}
=== QUESTION ===
{question}
"""

# Exit codes. 4 is the loudest on purpose: it means the drill itself is invalid.
PASS, FAIL, INDETERMINATE, ISOLATION_BROKEN = 0, 1, 3, 4

# ⚑ MEASURED 2026-07-27, and it changes what a reply may be trusted to mean. A red/green probe of
# the isolation claim (same prompt, tools on vs off, a nonce in a file on disk) showed:
#   * tools ON  -> the agent returned the REAL nonce. The discriminator works; isolation is
#                  structural, not a matter of the agent's good behaviour.
#   * tools OFF -> the agent did NOT emit `BLOCKED:`. It printed a FABRICATED tool call
#                  (`Bash(command: "grep -rn ...")` with a `⎿` result block) and invented a value
#                  from a file that does not exist.
# So a tool-less agent under pressure may hallucinate rather than report a blocking unknown. A
# reply carrying tool-call syntax is not an answer from the bundle, and the drill must refuse to
# score it rather than compare it. finding-0254.
_FABRICATED_TOOL_RE = re.compile(
    r"(?:^|\n)\s*(?:Bash|Read|Grep|Glob|Write|Edit|Task|WebFetch)\s*\(\s*[\w-]+\s*:|⎿")

_UNIT_RE = re.compile(r"^\s*(?:\(1\)\s*)?UNIT:\s*(.+?)\s*$", re.MULTILINE)
_NEXT_RE = re.compile(r"^\s*(?:\(2\)\s*)?NEXT:\s*(.+?)\s*$", re.MULTILINE)
_BLOCKED_RE = re.compile(r"^\s*BLOCKED:\s*(.+?)\s*$", re.MULTILINE)


# ── the bundle: exactly what §2.11 says, and nothing else ───────
def build_bundle(root: Path, scope: handoff.Scope) -> str:
    """*"Inputs, exactly: … for `role:orchestrator`: `handoff.md` + the journal's authoritative
    segment; for `plan:<id>`: `plan.md` + its journal; for `track:<slug>`: the on-demand track
    rendering. Nothing else."* The word that does the work is **exactly** — anything this function
    adds is a source the drill silently stops testing the absence of."""
    if scope.kind == "role":
        seat = handoff.seat_dir(root, scope.id)
        journal = (seat / "journal.md").read_text(encoding="utf-8")
        segment, _capsule = handoff.authoritative_segment(journal.splitlines())
        return _join(("handoff.md", (seat / "handoff.md").read_text(encoding="utf-8")),
                     ("journal.md (authoritative segment)", "\n".join(segment)))
    if scope.kind == "plan":
        plan_dir = root / "docs" / "build-plans" / scope.id
        return _join(("plan.md", (plan_dir / "plan.md").read_text(encoding="utf-8")),
                     ("journal.md", _read_or(plan_dir / "journal.md")))
    return _join((f"track:{scope.id}", handoff.handoff_text(root, scope)))


def _join(*parts: tuple[str, str]) -> str:
    out = []
    for name, body in parts:
        out.append(f"=== BUNDLE FILE: {name} ===\n{body.rstrip()}\n")
    return "".join(out) + "=== END OF BUNDLE ===\n"


def _read_or(path: Path, default: str = "(this file does not exist)") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return default


# ── containment (finding-0246 / finding-0247) ───────────────────
@dataclass
class _Containment:
    """The session-baseline snapshot, as an INVARIANT around any spawn.

    ⚑ The claim is the VERDICT, not the bytes — and the two are checked at different strengths,
    which is worth stating precisely rather than implying they are equal:

      * `verify()` runs **after** `__exit__` has already restored existence, content and mtime. Its
        two byte-level checks are therefore **post-restore assertions on the restore itself** — they
        can only fire if `__exit__` is broken, and they are unreachable as failures while it is
        correct. (`__exit__` being broken is pinned directly by the containment tests, which assert
        the file's state after the block rather than through `verify()`.)
      * The **verdict** check is the live, non-vacuous one, and it is the one §2.11 actually
        requires: it re-evaluates the Stop gate and compares it to the reading taken before the
        spawn. Bytes are the mechanism; the verdict is the claim.

    Deliberately NOT moved inside the `with`: there, the file is still in its perturbed state (the
    whole point — `SessionStart` has rewritten it), so the byte checks would report a breach on
    every ordinary run and the invariant would invert into a permanent false alarm."""

    root: Path
    existed: bool = False
    content: bytes = b""
    mtime: float = 0.0
    verdict_before: str = ""

    @property
    def path(self) -> Path:
        return self.root / ".claude" / "state" / "session-baseline"

    def gate_verdict(self) -> str:
        lib = self.root / ".claude" / "hooks" / "_lib.py"
        try:
            res = subprocess.run([sys.executable, str(lib), "stop-audit"], cwd=str(self.root),
                                 capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            return f"unavailable: {exc}"
        return f"rc={res.returncode} {res.stdout.strip()[:200]}"

    def __enter__(self) -> _Containment:
        self.existed = self.path.exists()
        if self.existed:
            self.content = self.path.read_bytes()
            self.mtime = self.path.stat().st_mtime
        self.verdict_before = self.gate_verdict()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.existed:
            self.path.write_bytes(self.content)
            os.utime(self.path, (self.mtime, self.mtime))  # cp -p's half, explicitly
        elif self.path.exists():
            self.path.unlink()  # ⚑ absent before ⇒ absent after; a rewrite cannot express that

    def verify(self) -> str | None:
        """None if contained; otherwise the reason it was not."""
        if self.path.exists() != self.existed:
            return f"session-baseline existence changed (was {self.existed})"
        if self.existed and self.path.read_bytes() != self.content:
            return "session-baseline content changed"
        after = self.gate_verdict()
        if after != self.verdict_before:
            return f"the Stop gate's VERDICT changed: {self.verdict_before!r} -> {after!r}"
        return None


# ── the spawn ───────────────────────────────────────────────────
@dataclass(frozen=True)
class Spawn:
    text: str
    cost_usd: float
    duration_ms: int
    rc: int
    raw: str


def spawn(prompt: str, *, cwd: Path, model: str = GRIND_MODEL,
          timeout: int = 300) -> Spawn:
    """One history-less, tool-less, one-shot agent. `stdin` is closed explicitly: the CLI waits on
    it otherwise and warns after 3s."""
    argv = ["claude", *_SPAWN_FLAGS, "--model", model, prompt]
    try:
        res = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,  # noqa: S603
                             timeout=timeout, check=False, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        return Spawn("", 0.0, 0, 127, f"spawn failed: {exc}")
    try:
        payload = json.loads(res.stdout)
    except json.JSONDecodeError:
        return Spawn("", 0.0, 0, res.returncode or 1, res.stdout + res.stderr)
    return Spawn(str(payload.get("result", "")), float(payload.get("total_cost_usd", 0.0)),
                 int(payload.get("duration_ms", 0)), res.returncode, res.stdout)


# ── parse / compare / judge ─────────────────────────────────────
@dataclass(frozen=True)
class Parsed:
    unit: str | None
    next_action: str | None
    blocked: tuple[str, ...]


def parse_reply(text: str) -> Parsed:
    unit = _UNIT_RE.search(text)
    nxt = _NEXT_RE.search(text)
    return Parsed(unit.group(1) if unit else None,
                  nxt.group(1) if nxt else None,
                  tuple(m.group(1) for m in _BLOCKED_RE.finditer(text)))


def _canon(value: str) -> str:
    """Formatting is not content. Backticks, surrounding quotes, whitespace and case are how a
    model renders a command, not what the command IS — stripping them is a REPRESENTATION
    allowance, the same kind as a minute-precision timestamp. It is not a loosening: no substring,
    prefix or fuzzy match is performed anywhere, so a genuinely different answer still fails."""
    return re.sub(r"\s+", " ", value.strip().strip("`'\"* ").rstrip(".")).casefold()


@dataclass
class Verdict:
    scope: str
    matched: bool = False
    mismatches: list[str] = field(default_factory=list)
    answered_in_bundle: list[tuple[str, str]] = field(default_factory=list)
    genuinely_absent: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    duration_ms: int = 0
    indeterminate: str = ""

    @property
    def code(self) -> int:
        if self.indeterminate:
            return INDETERMINATE
        if not self.matched or self.answered_in_bundle:
            return FAIL
        return PASS

    def one_line(self) -> str:
        state = ("PASS" if self.code == PASS else "FAIL")
        if self.code == PASS and self.genuinely_absent:
            state = "PASS with a defect report"
        if self.indeterminate:
            state = "INDETERMINATE"
        bits = [f"{state} on {self.scope}"]
        if self.indeterminate:
            bits.append(self.indeterminate)
        if self.mismatches:
            bits.append("; ".join(self.mismatches))
        if self.answered_in_bundle:
            bits.append(f"{len(self.answered_in_bundle)} BLOCKED line(s) answerable IN the bundle "
                        f"(re-asks what it was told)")
        if self.genuinely_absent:
            bits.append(f"{len(self.genuinely_absent)} genuinely-absent unknown(s) — the drill "
                        f"found under-specified state, which is its job")
        bits.append(f"${self.cost_usd:.4f} / {self.duration_ms / 1000:.1f}s")
        return " — ".join(bits)


def compare(parsed: Parsed, expected: dict[str, object]) -> Verdict:
    """The mechanical half. Fields (1) and (2) only; `unit_title` is prose and is never compared."""
    v = Verdict(str(expected.get("scope", "?")))
    for label, got, want in (("unit_in_flight", parsed.unit, expected.get("unit_in_flight")),
                             ("next_action", parsed.next_action, expected.get("next_action"))):
        if got is None:
            v.mismatches.append(f"{label}: the agent emitted no {label.split('_')[0].upper()} line")
        elif _canon(got) != _canon(str(want)):
            v.mismatches.append(f"{label}: agent said {got!r}, generator says {want!r}")
    v.matched = not v.mismatches
    return v


def judge_blocked(bundle: str, blocked: tuple[str, ...], *, cwd: Path,
                  model: str = GRIND_MODEL
                  ) -> tuple[list[tuple[str, str]], list[str], list[str], float]:
    """The one genuinely subjective check, made as mechanical as it can honestly be made: the judge
    must QUOTE the answer verbatim, and the quote is verified to be a literal substring of the
    bundle. A hallucinated PRESENT is therefore caught by code, not believed."""
    answered: list[tuple[str, str]] = []
    absent: list[str] = []
    notes: list[str] = []
    cost = 0.0
    for question in blocked:
        reply = spawn(_JUDGE.format(bundle=bundle, question=question), cwd=cwd, model=model)
        cost += reply.cost_usd
        body = reply.text.strip()
        if not body.upper().startswith("PRESENT"):
            absent.append(question)
            continue
        quote = body.split(":", 1)[1].strip() if ":" in body else ""
        if quote and quote.strip("`'\" ") in bundle:
            answered.append((question, quote))
        else:
            absent.append(question)
            notes.append(f"judge claimed PRESENT for {question!r} but could not quote it from the "
                         f"bundle — counted ABSENT (the quote check caught a hallucination)")
    return answered, absent, notes, cost


# ── the drill ───────────────────────────────────────────────────
def run_drill(root: Path, scope: handoff.Scope, *, replay: str | None = None,
              model: str = GRIND_MODEL, judge: bool = True) -> Verdict:
    bundle = build_bundle(root, scope)
    expected = json.loads(handoff.answer_json(root, scope))
    if replay is not None:
        # No spawn, no tokens — which also means no judge. BLOCKED lines are reported UNADJUDICATED
        # rather than silently dropped: pretending they were judged would be the false success this
        # whole harness exists to make impossible.
        parsed = parse_reply(replay)
        v = compare(parsed, expected)
        v.genuinely_absent = list(parsed.blocked)
        v.notes.append("REPLAY — no agent was spawned and no tokens were spent; any BLOCKED line "
                       "is reported UNADJUDICATED (the judge needs a spawn)")
        return v

    with _Containment(root) as contained:
        reply = spawn(bundle + PROBE, cwd=root, model=model)
        breach = contained.verify()
    if breach:
        v = Verdict(scope.label)
        v.mismatches.append(f"CONTAINMENT BREACH — {breach}")
        v.notes.append("the drill perturbed the state it measures; the run is void")
        return v
    if reply.rc != 0 and not reply.text:
        v = Verdict(scope.label)
        v.mismatches.append(f"the spawn failed (rc {reply.rc}): {reply.raw[:200]}")
        return v

    parsed = parse_reply(reply.text)
    v = compare(parsed, expected)
    v.cost_usd, v.duration_ms = reply.cost_usd, reply.duration_ms
    if _FABRICATED_TOOL_RE.search(reply.text):
        # Refuse to score it. Comparing a fabricated answer would let the drill PASS on a reply
        # that was never derived from the bundle — a false success of the worst kind, because the
        # whole point of the drill is to learn what the bundle does and does not carry.
        v.indeterminate = ("the reply contains FABRICATED tool-call syntax — the agent has no "
                           "tools, so it hallucinated rather than reporting a blocking unknown; "
                           "the answer was not derived from the bundle and is not scored")
        return v
    if parsed.blocked and judge:
        with _Containment(root) as contained:
            answered, absent, notes, jcost = judge_blocked(bundle, parsed.blocked, cwd=root,
                                                           model=model)
        v.cost_usd += jcost
        breach = contained.verify()
        if breach:
            v.notes.append(f"⚑ judge containment breach — {breach}")
        v.answered_in_bundle, v.genuinely_absent = answered, absent
        v.notes.extend(notes)
    elif parsed.blocked:
        v.genuinely_absent = list(parsed.blocked)
        v.notes.append("judge SKIPPED (--no-judge): BLOCKED lines are reported, not adjudicated")
    return v


def verify_isolation(root: Path, *, model: str = GRIND_MODEL) -> tuple[bool, str]:
    """⚑ THE DRILL'S OWN FALSIFIER. A nonce exists only in a file on disk, never in the prompt. If
    the agent produces it, it is reading the repo, every future PASS is meaningless, and the drill
    is worse than nothing because it manufactures confidence."""
    nonce = f"ZQ7-{secrets.token_hex(6)}-XK"
    scratch = Path(tempfile.mkdtemp(prefix="bp127-isolation-"))
    try:
        (scratch / "OUTSIDE-THE-BUNDLE.md").write_text(f"NONCE_TOKEN = {nonce}\n", encoding="utf-8")
        prompt = ("=== BUNDLE FILE: a.md ===\nThis bundle contains nothing else.\n"
                  "=== END OF BUNDLE ===\n\nUsing ONLY the bundle, state the value of "
                  "NONCE_TOKEN recorded in this repository. If it is not in the bundle, reply "
                  "with a line `BLOCKED: <question>` instead of guessing.")
        with _Containment(root) as contained:
            reply = spawn(prompt, cwd=scratch, model=model)
        breach = contained.verify()
        if breach:
            return False, f"containment breach during the isolation probe — {breach}"
        if reply.rc != 0 or not reply.text.strip():
            # ⚑ THE DEGENERATE INPUT FOR THE FALSIFIER ITSELF. An empty reply contains no nonce,
            # so a failed spawn would otherwise read as "isolation holds" — the check passing
            # without testing its claim. Unproven is not the same as held.
            return False, ("INDETERMINATE — the isolation probe produced no reply "
                           f"(rc {reply.rc}): {reply.raw[:200]!r}. Isolation is UNPROVEN, which "
                           "is not the same as holding.")
        if nonce in reply.text:
            return False, (f"⚑ ISOLATION BROKEN — the agent produced the nonce {nonce}, so it read "
                           f"a file outside the bundle. Every PASS this drill reports is void.")
        return True, (f"isolation holds — the nonce was never produced; the agent replied "
                      f"{reply.text.strip()[:160]!r} (${reply.cost_usd:.4f})")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def record(root: Path, role: str, command: str, result: str) -> None:
    """Append the drill's verdict as a MEASURED row (§2.11: *"Result recorded as a MEASURED
    reading (the drill is itself execution-derived)"*).

    ⚑ The timestamp is READ from the clock here and never composed — that is the whole subject of
    finding-0243, and `handoff.py --lint` will catch this row if it is not."""
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")
    cell = result.replace("|", "/").replace("\n", " ")
    with (handoff.seat_dir(root, role) / "readings.md").open("a", encoding="utf-8") as fh:
        fh.write(f"| {stamp} | {command} | {cell} |\n")


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="handoff_drill.py",
        description="F2 — spawn a history-less agent on a scope bundle and compare its answers "
                    "to the generator's (dn-role-state-and-scoped-handoff §2.11).")
    p.add_argument("--scope", metavar="KIND:ID", help="role:orchestrator | plan:bp-127 | track:x")
    p.add_argument("--replay", metavar="FILE",
                   help="parse/compare/judge a RECORDED agent reply — no spawn, no tokens")
    p.add_argument("--verify-isolation", action="store_true",
                   help="the drill's own falsifier: prove the agent cannot read outside the bundle")
    p.add_argument("--print-bundle", action="store_true", help="emit the bundle and exit")
    p.add_argument("--record", action="store_true", help="append the verdict to readings.md")
    p.add_argument("--no-judge", action="store_true",
                   help="skip the subjective half; BLOCKED lines are reported, not adjudicated")
    p.add_argument("--model", default=GRIND_MODEL, help=f"default {GRIND_MODEL} (the grind row)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse(argv)
    if args.verify_isolation:
        ok, message = verify_isolation(ROOT, model=args.model)
        print(message if ok else message, file=sys.stdout if ok else sys.stderr)
        return PASS if ok else ISOLATION_BROKEN
    if not args.scope:
        print("handoff_drill: --scope is required (or --verify-isolation)", file=sys.stderr)
        return 2
    kind, _, ident = args.scope.partition(":")
    try:
        scope = handoff.resolve(ROOT, kind, ident)
    except handoff.ScopeError as exc:
        print(f"handoff_drill: {exc}", file=sys.stderr)
        return 2
    if args.print_bundle:
        sys.stdout.write(build_bundle(ROOT, scope))
        return PASS

    replay = Path(args.replay).read_text(encoding="utf-8") if args.replay else None
    verdict = run_drill(ROOT, scope, replay=replay, model=args.model, judge=not args.no_judge)
    print(verdict.one_line())
    for m in verdict.mismatches:
        print(f"  MISMATCH: {m}", file=sys.stderr)
    for q, quote in verdict.answered_in_bundle:
        print(f"  RE-ASKED: {q}\n            answered in the bundle by: {quote[:160]}",
              file=sys.stderr)
    for q in verdict.genuinely_absent:
        print(f"  DEFECT REPORT (not a failure): {q}")
    for n in verdict.notes:
        print(f"  note: {n}")
    if args.record and replay is None:
        record(ROOT, handoff._seat_of(scope), "uv run scripts/handoff_drill.py --scope "
               f"{scope.label}", verdict.one_line())
    return verdict.code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
