"""Dynamic agent factory (BUILD-SPEC §10).

Mints a personalized agent on demand as nested frames, outermost-first (Invariant 6):
    Constitution → base role template → task
then resolves the tool scope and binds a dispatcher holding ONLY the in-scope handles.

The scope ceiling is the whole safety story: a minted agent can never exceed its template's
scope, never be granted scope beyond `PRE_DECLARED_MAX`, and always inherits the
Constitution. A request for capability beyond that is **routed to the human gate**, never
satisfied by minting a privileged agent (§10). Capability is checked twice, by two
subsystems, at two times: at mint (scope resolution) and at dispatch (object-capability).
The advisory path (`respond`) and the action path (`invoke`) are kept separate — model
advises, code acts (Invariant 3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from core.constitution import Message, frame_context
from core.factory.registry import AgentRegistry
from core.factory.roles import BASE_ROLES, PRE_DECLARED_MAX, RoleTemplate
from core.factory.tools import (
    ToolDispatcher,
    ToolNotInScopeError,
    ToolRegistry,
    ToolResult,
    dispatcher_for,
)
from core.models import ModelServer
from core.selfcheck import SelfCheck, SubjectiveJudge, self_evaluate
from ops.gate import GateRequest, HumanGate

if TYPE_CHECKING:  # annotations only — no runtime import (config.secrets_backend stays lazy)
    from config.secrets_backend import MintedToken, SecretsBackend
    from core.attestation.attestor import Attestor


@dataclass
class MintedAgent:
    name: str
    role: RoleTemplate
    scope: frozenset[str]            # resolved = role.scope ∩ PRE_DECLARED_MAX
    dispatcher: ToolDispatcher
    gate: HumanGate
    server: ModelServer | None = None
    ephemeral: bool = True
    # The credential-level scope (vault-runtime-auth.md §2), parallel to the tool scope above.
    # `token` is the ephemeral Vault credential — held OFF the model prompt (repr=False; never in
    # build_context) so the model never sees it (Invariant 10). `accessor` is its non-secret audit
    # handle, recorded in the mint attestation. Both None unless the role got a grant at mint.
    token: str | None = field(default=None, repr=False)
    accessor: str | None = None

    def build_context(self, task: str, *, history: list[Message] | None = None) -> list[Message]:
        """Constitution outermost (Invariant 6); the role nests inside; task last. The credential
        token is deliberately NOT here — the model advises, code reads secrets (`read_secret`)."""
        return frame_context(self.role.prompt_fragment, task, history=history)

    def grant(self, minted: MintedToken) -> None:
        """Bind an ephemeral scoped token (the supervisor-mints-at-dispatch path, §2 step 3).
        Holds the credential off the prompt; keeps only the non-secret accessor for the audit."""
        self.token = minted.token
        self.accessor = minted.accessor

    def read_secret(self, name: str) -> str | None:
        """Read a scoped secret using this agent's grant (§2 step 4). CODE-ONLY: the orchestration
        around the agent calls this to fetch data the agent's REASONING then uses; the MODEL never
        calls it and never sees the token. `get_secret` presents the token to Vault, which enforces
        the role's policy and raises `VaultPermissionDenied` for an out-of-scope path — the agent
        learns nothing beyond 'denied' (§2 step 5). No grant at all => RuntimeError."""
        if self.token is None:
            raise RuntimeError(
                f"agent {self.name!r} holds no credential grant — its role is not in "
                "[secrets].grant_roles, or [secrets] is disabled"
            )
        from config.loader import get_secret

        return get_secret(name, token=self.token)

    def respond(self, task: str, *, history: list[Message] | None = None,
                judge: SubjectiveJudge | None = None,
                think: bool | None = None) -> tuple[str, SelfCheck]:
        """Advisory path: generate + run the Constitution pre-return check (§4)."""
        if self.server is None:
            raise RuntimeError(f"agent {self.name!r} has no model server bound")
        out = self.server.chat(self.role.default_tier,
                               self.build_context(task, history=history), think=think)
        return out, self_evaluate(out, judge=judge)   # advisory => no retrieval sources

    def invoke(self, tool_id: str, args: dict) -> ToolResult:
        """Action path: dispatch a tool the agent is scoped for. An out-of-scope id is
        unreachable in the dispatcher → route to the human gate and refuse (§10)."""
        try:
            return self.dispatcher.invoke(tool_id, args)
        except ToolNotInScopeError:
            self.gate.submit(
                "out_of_scope_tool",
                f"agent {self.name!r} requested {tool_id!r} outside its scope "
                f"{sorted(self.scope)}",
                agent=self.name,
            )
            raise


@dataclass
class AgentFactory:
    server: ModelServer | None = None
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    gate: HumanGate = field(default_factory=HumanGate)
    roles: dict[str, RoleTemplate] = field(default_factory=lambda: dict(BASE_ROLES))
    agent_registry: AgentRegistry | None = None
    # Credential-level scoping (vault-runtime-auth.md §2). When `secrets` is wired and a role is in
    # `grant_roles`, minting also mints an ephemeral scoped Vault token, binds it to the agent, and
    # records the non-secret accessor in a `mint_token` attestation (the Vault↔attestation join).
    secrets: SecretsBackend | None = None
    attestor: Attestor | None = None
    grant_roles: frozenset[str] = frozenset()
    token_ttl: str = "10m"

    def mint(self, role_name: str, *, requested_tools: frozenset[str] = frozenset(),
             name: str | None = None, persist: bool = False) -> MintedAgent | GateRequest:
        """Mint an agent for `role_name`. If `requested_tools` reaches beyond the role's
        resolved scope ceiling, route to the human gate instead of minting (§10)."""
        if role_name not in self.roles:
            raise KeyError(f"unknown role {role_name!r}")
        role = self.roles[role_name]
        resolved = role.scope & PRE_DECLARED_MAX          # never beyond the pre-declared max
        beyond = frozenset(requested_tools) - resolved
        if beyond:
            return self.gate.submit(
                "privileged_mint",
                f"mint {role_name!r} requested capability beyond scope: {sorted(beyond)}",
            )
        agent = MintedAgent(
            name=name or role_name,
            role=role,
            scope=resolved,
            dispatcher=dispatcher_for(resolved, self.tools),
            gate=self.gate,
            server=self.server,
            ephemeral=not persist,
        )
        self._grant_credential(agent, role_name)
        if persist and self.agent_registry is not None:
            self.agent_registry.promote(agent.name, role.name, resolved, role.default_tier)
        return agent

    def _grant_credential(self, agent: MintedAgent, role_name: str) -> None:
        """Mint an ephemeral scoped token for `role_name` and bind it to the agent (§2 step 2–3),
        when a backend is wired AND the role opted in via `grant_roles` (fail-closed otherwise — an
        ungranted agent simply holds no token, and `read_secret` raises). Records the non-secret
        accessor in a `mint_token` attestation; NEVER the token (MintedToken docstring)."""
        if self.secrets is None or role_name not in self.grant_roles:
            return
        minted = self.secrets.mint_token(role_name, self.token_ttl)
        agent.grant(minted)
        if self.attestor is not None:
            self.attestor.emit(agent_role=role_name, action="mint_token",
                               vault_token_accessor=minted.accessor)


def build_factory(config=None, *, broker=None) -> AgentFactory:
    """Wire a factory against the real model server + default tool registry (run_python is
    available only if a sandbox `broker` is supplied). When `[secrets]` is enabled, also wire the
    credential-grant path: a backend (mint authority), the attestor (records accessors), and the
    `grant_roles` opt-in set — so a minted agent in a granted role carries an ephemeral token."""
    from core.factory.tools import build_default_registry
    from core.models import build_model_server

    if config is False:                                  # server-less wiring (tests)
        return AgentFactory(server=None, tools=build_default_registry(broker))

    from config.loader import get_config
    from config.secrets_backend import build_secrets_backend

    cfg = config or get_config()
    secrets = build_secrets_backend(cfg)         # None unless [secrets] enabled (fail-closed)
    attestor = None
    if secrets is not None:
        from core.attestation import build_attestor
        attestor = build_attestor(cfg)
    return AgentFactory(
        server=build_model_server(cfg),
        tools=build_default_registry(broker),
        secrets=secrets,
        attestor=attestor,
        grant_roles=cfg.secrets.grant_roles if secrets is not None else frozenset(),
        token_ttl=cfg.secrets.token_ttl,
    )
