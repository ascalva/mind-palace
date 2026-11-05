"""The chain language — a regular path over `Σ_move = {S, F, D, C}` compiled to a deterministic
automaton, and the product walk that finds the chains it admits (dn-query-sentence-algebra §2.2,
QSA-7 in `formal/Palace/Sentence.lean`; fiber-geometry §2.3's grammar layer).

* `compile_path("S{0,2}C+")` builds the automaton (Thompson's construction, then the subset
  construction); `DFA.live` is the set of states from which an accepting state is reachable, the
  viable-prefix test.
* `product_walk` runs the typed graph and the automaton in lockstep from `(start, q₀)`, prunes a
  branch the moment its state is dead, and returns the chains that end accepting
  (`admissible_iff_prodOk`; `prune_sound` says the pruning loses no admissible chain).
* `of_set` is today's `E ⊆ {F, D, C}` as the one-state automaton accepting `E*`
  (`ofSet_accepts`): order-blind, the shadow of the language.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping, Set
from dataclasses import dataclass, field
from functools import cached_property

from core.sentence.ast import Rel

ALPHABET: tuple[Rel, ...] = (Rel.S, Rel.F, Rel.D, Rel.C)
# Thompson's construction copies a counted body once per count: a bound on the copies, so a path
# of nested counts is refused before it is built (the ledger bounds each count too)
MAX_STATES = 20_000

TypedGraph = Mapping[Rel, Mapping[str, Set[str]]]


class PathError(ValueError):
    """The path is not a regular expression over S, F, D, C."""


# ── regular expressions over the moves ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Lit:
    move: Rel


@dataclass(frozen=True)
class _Eps:
    pass


@dataclass(frozen=True)
class _Cat:
    parts: tuple[_Re, ...]


@dataclass(frozen=True)
class _Alt:
    parts: tuple[_Re, ...]


@dataclass(frozen=True)
class _Rep:
    body: _Re
    lo: int
    hi: int | None    # None: unbounded


_Re = _Lit | _Eps | _Cat | _Alt | _Rep


class _ReParser:
    def __init__(self, text: str) -> None:
        self.s = text.replace(" ", "")
        self.i = 0

    def peek(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ""

    def parse(self) -> _Re:
        if not self.s:
            raise PathError("via: the path is empty")
        node = self.alt()
        if self.i != len(self.s):
            raise PathError(f"via: unexpected {self.peek()!r} at {self.i} in {self.s!r}")
        return node

    def alt(self) -> _Re:
        parts = [self.cat()]
        while self.peek() == "|":
            self.i += 1
            parts.append(self.cat())
        return parts[0] if len(parts) == 1 else _Alt(tuple(parts))

    def cat(self) -> _Re:
        parts: list[_Re] = []
        while self.peek() not in ("", "|", ")"):
            parts.append(self.rep())
        if not parts:
            return _Eps()
        return parts[0] if len(parts) == 1 else _Cat(tuple(parts))

    def rep(self) -> _Re:
        node = self.atom()
        while True:
            c = self.peek()
            if c == "*":
                self.i += 1
                node = _Rep(node, 0, None)
            elif c == "+":
                self.i += 1
                node = _Rep(node, 1, None)
            elif c == "?":
                self.i += 1
                node = _Rep(node, 0, 1)
            elif c == "{":
                self.i += 1
                lo = self.number()
                hi: int | None = lo
                if self.peek() == ",":
                    self.i += 1
                    hi = self.number() if self.peek().isdigit() else None
                if self.peek() != "}":
                    raise PathError(f"via: expected '}}' at {self.i} in {self.s!r}")
                self.i += 1
                if hi is not None and hi < lo:
                    raise PathError(f"via: {{{lo},{hi}}} is inverted in {self.s!r}")
                node = _Rep(node, lo, hi)
            else:
                return node

    def number(self) -> int:
        j = self.i
        while self.peek().isdigit():
            self.i += 1
        if j == self.i:
            raise PathError(f"via: expected a count at {self.i} in {self.s!r}")
        return int(self.s[j:self.i])

    def atom(self) -> _Re:
        c = self.peek()
        if c == "(":
            self.i += 1
            node = self.alt()
            if self.peek() != ")":
                raise PathError(f"via: expected ')' at {self.i} in {self.s!r}")
            self.i += 1
            return node
        if c in ("S", "F", "D", "C"):
            self.i += 1
            return _Lit(Rel(c))
        raise PathError(f"via: expected a move letter S, F, D or C at {self.i} in {self.s!r}, "
                        f"got {c!r}")


def letters(pattern: str) -> frozenset[Rel]:
    """The move letters a path mentions: what the clause's `E` must carry (S aside)."""
    return frozenset(Rel(c) for c in pattern if c in ("S", "F", "D", "C"))


# ── NFA by Thompson's construction ─────────────────────────────────────────────────────────────


@dataclass
class _NFA:
    moves: dict[int, dict[Rel, set[int]]] = field(default_factory=dict)
    eps: dict[int, set[int]] = field(default_factory=dict)
    count: int = 0

    def state(self) -> int:
        q = self.count
        if q >= MAX_STATES:
            raise PathError(f"via: the path's automaton passes {MAX_STATES} states; nested counts "
                            "multiply, so write a smaller count")
        self.count += 1
        self.moves[q] = {}
        self.eps[q] = set()
        return q

    def build(self, node: _Re) -> tuple[int, int]:
        """Return (entry, exit) states for the fragment."""
        if isinstance(node, _Lit):
            a, b = self.state(), self.state()
            self.moves[a].setdefault(node.move, set()).add(b)
            return a, b
        if isinstance(node, _Eps):
            a = self.state()
            return a, a
        if isinstance(node, _Cat):
            entry, cur = self.build(node.parts[0])
            for part in node.parts[1:]:
                a, b = self.build(part)
                self.eps[cur].add(a)
                cur = b
            return entry, cur
        if isinstance(node, _Alt):
            entry, exit_ = self.state(), self.state()
            for part in node.parts:
                a, b = self.build(part)
                self.eps[entry].add(a)
                self.eps[b].add(exit_)
            return entry, exit_
        # repetition: lo copies, then (hi − lo) optional copies, or a star
        entry = self.state()
        cur = entry
        for _ in range(node.lo):
            a, b = self.build(node.body)
            self.eps[cur].add(a)
            cur = b
        if node.hi is None:
            a, b = self.build(node.body)
            self.eps[cur].add(a)
            self.eps[b].add(cur)
            return entry, cur
        exit_ = self.state()
        self.eps[cur].add(exit_)
        for _ in range(node.hi - node.lo):
            a, b = self.build(node.body)
            self.eps[cur].add(a)
            self.eps[b].add(exit_)
            cur = b
        return entry, exit_

    def closure(self, states: Iterable[int]) -> frozenset[int]:
        seen = set(states)
        stack = list(seen)
        while stack:
            q = stack.pop()
            for r in self.eps[q]:
                if r not in seen:
                    seen.add(r)
                    stack.append(r)
        return frozenset(seen)


# ── the DFA ────────────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DFA:
    """A total deterministic automaton over the moves; `dead` is the sink."""

    start: int
    accept: frozenset[int]
    delta: Mapping[tuple[int, Rel], int]
    size: int

    def step(self, state: int, move: Rel) -> int:
        return self.delta[(state, move)]

    def run(self, state: int, word: Iterable[Rel]) -> int:
        for m in word:
            state = self.step(state, m)
        return state

    def accepts(self, word: Iterable[Rel]) -> bool:
        return self.run(self.start, word) in self.accept

    @cached_property
    def live(self) -> frozenset[int]:
        """States from which an accepting state is reachable: the viable-prefix test."""
        back: dict[int, set[int]] = {q: set() for q in range(self.size)}
        for (q, _m), r in self.delta.items():
            back[r].add(q)
        seen = set(self.accept)
        stack = list(seen)
        while stack:
            q = stack.pop()
            for p in back[q]:
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
        return frozenset(seen)

    def is_live(self, state: int) -> bool:
        return state in self.live


def _determinize(nfa: _NFA, entry: int, exit_: int) -> DFA:
    start = nfa.closure({entry})
    index: dict[frozenset[int], int] = {start: 0}
    order: list[frozenset[int]] = [start]
    delta: dict[tuple[int, Rel], int] = {}
    i = 0
    while i < len(order):
        states = order[i]
        for m in ALPHABET:
            targets: set[int] = set()
            for q in states:
                targets |= nfa.moves[q].get(m, set())
            closed = nfa.closure(targets)
            if closed not in index:
                index[closed] = len(order)
                order.append(closed)
            delta[(i, m)] = index[closed]
        i += 1
    accept = frozenset(index[s] for s in order if exit_ in s)
    return DFA(start=0, accept=accept, delta=delta, size=len(order))


def compile_path(pattern: str) -> DFA:
    """A regular path over the moves, as a total DFA. Raises `PathError` on a bad path."""
    tree = _ReParser(pattern).parse()
    nfa = _NFA()
    entry, exit_ = nfa.build(tree)
    return _determinize(nfa, entry, exit_)


def of_set(moves: Iterable[Rel]) -> DFA:
    """The set `E` as the one-state automaton accepting `E*` (QSA-7, `ofSet`)."""
    allowed = frozenset(moves)
    delta: dict[tuple[int, Rel], int] = {}
    for m in ALPHABET:
        delta[(0, m)] = 0 if m in allowed else 1
        delta[(1, m)] = 1
    return DFA(start=0, accept=frozenset({0}), delta=delta, size=2)


GROUNDING = "S*(C|D)"
"""The grounding production of fiber-geometry §2.3-4: resemblance, then one witnessed step."""


# ── chains and the product walk ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Chain:
    """A chain: the start note and the moves taken with the notes reached."""

    start: str
    steps: tuple[tuple[Rel, str], ...]

    @property
    def end(self) -> str:
        return self.steps[-1][1] if self.steps else self.start

    @property
    def word(self) -> tuple[Rel, ...]:
        return tuple(m for m, _ in self.steps)

    def __str__(self) -> str:
        return self.start + "".join(f" →{m.value}→ {v}" for m, v in self.steps)


def walk_product(graph: TypedGraph, dfa: DFA, start: str, *, depth: int,
                 target: str | None = None, limit: int = 200,
                 budget: int = 100_000) -> tuple[list[Chain], str]:
    """The chains from `start` of at most `depth` moves whose word the automaton accepts, ending
    at `target` when one is given: the product graph walked breadth first, so shorter chains come
    first, pruning a branch at a dead state (QSA-7), on simple paths (no note revisited). It stops
    at `limit` chains or after `budget` partial chains, and says why: the second value is empty
    when the walk was exhaustive, else the reason it stopped short."""
    found: list[Chain] = []
    queue: deque[tuple[str, int, tuple[tuple[Rel, str], ...], frozenset[str]]] = deque(
        [(start, dfa.start, (), frozenset({start}))])
    seen = 0
    while queue:
        if len(found) >= limit:
            return (sorted(found, key=lambda c: (len(c.steps), str(c))),
                    f"the {limit} shortest chains; longer ones were not enumerated")
        seen += 1
        if seen > budget:
            return (sorted(found, key=lambda c: (len(c.steps), str(c))),
                    f"the walk stopped at its budget of {budget} partial chains; chains longer "
                    f"than {len(queue[0][2]) if queue else depth} moves were not all enumerated")
        vertex, state, steps, visited = queue.popleft()
        if steps and state in dfa.accept and (target is None or vertex == target):
            found.append(Chain(start, steps))
        if len(steps) >= depth:
            continue
        for move in ALPHABET:
            next_state = dfa.step(state, move)
            if not dfa.is_live(next_state):
                continue                                     # the dead state: prune here
            for nxt in sorted(graph.get(move, {}).get(vertex, ())):
                if nxt not in visited:
                    queue.append((nxt, next_state, steps + ((move, nxt),), visited | {nxt}))
    found.sort(key=lambda c: (len(c.steps), str(c)))
    return found, ""


def product_walk(graph: TypedGraph, dfa: DFA, start: str, *, depth: int,
                 target: str | None = None, limit: int = 200,
                 budget: int = 100_000) -> list[Chain]:
    """`walk_product`'s chains alone."""
    return walk_product(graph, dfa, start, depth=depth, target=target, limit=limit,
                        budget=budget)[0]
