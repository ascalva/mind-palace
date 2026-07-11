"""Property-based tests for the invariant catalog (docs/WHITEPAPER-FORMAL-PROPERTIES.md).

Hypothesis asserts each predicate over GENERATED inputs, not just hand-picked cases — the
tier-4 ("property-tested") discharge for the invariants that are not (yet) structural:

  * I6  — observed/interpreted data never survives the mirror projection (firewall).
  * I9  — grounded(A) ⇔ Cit(A) ⊆ Ret, decided over stable digest IDs (gap G1).
  * I10 — confidence decays (non-increasing) with derivation depth; cycles are rejected.
  * I13 — authority never widens under arbitrary skill composition / mint requests.
"""

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from core.factory.factory import AgentFactory
from core.factory.roles import PRE_DECLARED_MAX, RoleTemplate
from core.factory.tools import ToolRegistry, ToolSpec
from core.mirror import MirrorView
from core.provenance import MIRROR_READABLE, Provenance
from core.recursion import claim_confidence, decay_bound
from core.selfcheck import FAIL, PASS, Source, check_grounding
from core.stores.derived import DREAM, DerivationCycleError, DerivedStore
from ops.gate import GateRequest

_PROVENANCES = [p.value for p in Provenance]          # authored | interpreted | observed
_AUTHORED = {p.value for p in MIRROR_READABLE}        # {authored}


# --- I6 — the firewall: observed never reaches the mirror -----------------------

_row = st.fixed_dictionaries({
    "provenance": st.sampled_from(_PROVENANCES),
    "digest": st.text(alphabet="abcdef", min_size=1, max_size=4),
    "title": st.text(alphabet="abcde", max_size=4),
})


class _Source:
    def __init__(self, rows):
        self.rows = rows

    def all_rows(self, *, provenances=None):
        if provenances is None:
            return list(self.rows)
        allowed = {str(p) for p in provenances}
        return [r for r in self.rows if r["provenance"] in allowed]


@given(st.lists(_row, max_size=30))
def test_I6_mirror_admits_only_authored(rows):
    view = MirrorView.project(_Source(rows))
    # Every surviving row is authored, and exactly the authored rows survive.
    assert all(r["provenance"] in _AUTHORED for r in view.rows())
    assert len(view) == sum(1 for r in rows if r["provenance"] in _AUTHORED)


# --- I9 — grounding predicate decidable over stable digest IDs ------------------

_title = st.text(alphabet="abcde", min_size=1, max_size=3)        # small alphabet => collisions


@given(
    notes=st.lists(_title, min_size=1, max_size=6),
    fabricated=st.lists(st.text(alphabet="xyz", min_size=1, max_size=3), max_size=3),
    data=st.data(),
)
def test_I9_grounded_iff_citations_resolve_uniquely(notes, fabricated, data):
    # Each note gets a UNIQUE digest; titles may collide (that is the ill-posed case G1).
    sources = [Source(title=t, digest=f"dig{i}") for i, t in enumerate(notes)]
    # The model cites a mix of real titles (drawn from notes) and fabricated ones.
    cite_real = data.draw(st.lists(st.sampled_from(notes), max_size=4))
    cited = cite_real + fabricated
    output = " ".join(f"[[{t}]]" for t in cited)

    index: dict[str, set[str]] = {}
    for s in sources:
        index.setdefault(s.title.casefold(), set()).add(s.digest)
    expected_pass = all(
        len(index.get(t.casefold(), set())) == 1 for t in cited
    )

    finding = check_grounding(output, sources)
    assert finding.status == (PASS if expected_pass else FAIL)


# --- I10 — decay non-increasing in depth; cycles rejected -----------------------

@given(
    depth=st.integers(min_value=0, max_value=20),
    gamma=st.floats(min_value=0.01, max_value=0.99),
    grounding=st.floats(min_value=0.0, max_value=1.0),
)
def test_I10_decay_is_non_increasing_in_depth(depth, gamma, grounding):
    assert decay_bound(depth + 1, grounding=grounding, gamma=gamma) <= (
        decay_bound(depth, grounding=grounding, gamma=gamma) + 1e-12
    )


# --- Prompt R1 — the confidence clamp: c ∈ [0,1] and non-increasing in depth ----
# The single definition c = min{1, γ^d·g·(1+λ(|Agr|−1))} may not produce c>1 or a c that rises
# with depth, for ANY admissible (d, g, |Agr|, γ, λ) — including large agreement / grounding that
# would push the raw product past 1 (the clamp must bite).

@given(
    depth=st.integers(min_value=0, max_value=20),
    grounding=st.floats(min_value=0.0, max_value=1.0),
    agreement=st.integers(min_value=1, max_value=50),
    gamma=st.floats(min_value=0.01, max_value=0.99),
    lam=st.floats(min_value=0.0, max_value=2.0),
)
def test_claim_confidence_in_unit_interval(depth, grounding, agreement, gamma, lam):
    c = claim_confidence(depth, grounding=grounding, agreement=agreement, gamma=gamma, lam=lam)
    assert 0.0 <= c <= 1.0


@given(
    depth=st.integers(min_value=0, max_value=20),
    grounding=st.floats(min_value=0.0, max_value=1.0),
    agreement=st.integers(min_value=1, max_value=50),
    gamma=st.floats(min_value=0.01, max_value=0.99),
    lam=st.floats(min_value=0.0, max_value=2.0),
)
def test_claim_confidence_non_increasing_in_depth(depth, grounding, agreement, gamma, lam):
    deeper = claim_confidence(depth + 1, grounding=grounding, agreement=agreement,
                              gamma=gamma, lam=lam)
    here = claim_confidence(depth, grounding=grounding, agreement=agreement, gamma=gamma, lam=lam)
    assert deeper <= here + 1e-12


@settings(deadline=None, max_examples=50)
@given(n=st.integers(min_value=2, max_value=8))
def test_I10_chain_depths_increase_and_cycle_is_rejected(n):
    # A synthetic derivation DAG: a chain node0 <- node1 <- ... over an authored leaf.
    store = DerivedStore(Path(":memory:"))
    ids = []
    prev_parents = ["leaf-digest"]                 # node0's parent is an authored leaf
    for i in range(n):
        art = store.add(kind=DREAM, summary=f"d{i}", subjects=[f"n{i}"],
                        derived_from=prev_parents)
        ids.append(art.id)
        prev_parents = [art.id]                     # next node derives from this one
    depths = [store.depth(i) for i in ids]
    assert depths == list(range(1, n + 1))          # strictly increasing: 1,2,...,n
    # decay along the chain is non-increasing
    bounds = [decay_bound(d) for d in depths]
    assert all(bounds[i + 1] <= bounds[i] for i in range(len(bounds) - 1))
    # closing the chain (node0 derived_from the last node) is a cycle and is refused
    try:
        store.add(kind=DREAM, summary="d0", subjects=["n0"], derived_from=[ids[-1]])
        raised = False
    except DerivationCycleError:
        raised = True
    assert raised
    store.close()


# --- I13 — authority non-widening under arbitrary skill composition -------------

def _registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(ToolSpec("run_python", "sandboxed", handler=lambda a: {}, sandboxed=True))
    return reg


# A role's scope must be ⊆ MAX (the template enforces this); skills are arbitrary strings.
_scope = st.sets(st.sampled_from(sorted(PRE_DECLARED_MAX)))
_skills = st.lists(st.text(max_size=6), max_size=5).map(tuple)
# requested tools may reach beyond MAX (e.g. a non-existent 'deploy' capability).
_requested = st.sets(st.sampled_from(["run_python", "deploy", "shell", "read_secret"]))


@given(scope=_scope, skills=_skills, requested=_requested)
def test_I13_authority_does_not_widen(scope, skills, requested):
    role = RoleTemplate("r", "frag", scope=frozenset(scope), skills=skills)
    factory = AgentFactory(server=None, tools=_registry())
    resolved = role.scope & PRE_DECLARED_MAX
    factory.roles[role.name] = role                     # inject the ad-hoc role
    result = factory.mint(role.name, requested_tools=frozenset(requested))

    if requested - resolved:
        # Any capability beyond the resolved ceiling routes to the gate — never a wider agent.
        assert isinstance(result, GateRequest)
    else:
        # Authority is exactly role.scope ∩ MAX, regardless of the skills composed in.
        assert not isinstance(result, GateRequest)
        assert result.dispatcher.scope == resolved
        for t in ["deploy", "shell", "read_secret"]:
            assert not result.dispatcher.can_invoke(t)        # out-of-scope = unreachable
