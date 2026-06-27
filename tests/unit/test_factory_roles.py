"""Base role library + scope ceiling (BUILD-SPEC §9, §10)."""

import pytest

from core.factory.roles import BASE_ROLES, PRE_DECLARED_MAX, RoleTemplate


def test_all_base_role_scopes_are_within_the_pre_declared_max():
    for role in BASE_ROLES.values():
        assert role.scope <= PRE_DECLARED_MAX   # no role can exceed the ceiling (§10)


def test_expected_roles_present():
    assert {
        "personal_assistant", "coder", "data_analyst", "financial_advisor",
        "health_research_advisor", "writer_editor", "general_conversation",
    } <= set(BASE_ROLES)


def test_only_compute_roles_hold_run_python():
    assert BASE_ROLES["coder"].scope == frozenset({"run_python"})
    assert BASE_ROLES["data_analyst"].scope == frozenset({"run_python"})
    assert BASE_ROLES["financial_advisor"].scope == frozenset()   # advisory, defers (Inv 7)
    assert BASE_ROLES["writer_editor"].scope == frozenset()


def test_template_rejects_scope_beyond_max():
    with pytest.raises(ValueError):
        RoleTemplate("rogue", "frag", scope=frozenset({"deploy_aws"}))
