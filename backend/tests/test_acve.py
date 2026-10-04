import pytest
from app.engines.tige import tige
from app.engines.acve import acve
from app.models.intents import IntentObject
from app.database import db_store

def test_acve_cross_tenant_isolation_interception():
    db_store.reset()
    tige.initialize_tenant_genome("tenant_victim", "Victim Gym", "Free")
    tige.initialize_tenant_genome("tenant_attacker", "Attacker Gym", "Free")

    # Attacker tries to modify victim's members
    malicious_intent = IntentObject(
        tenant_id="tenant_victim",
        source_agent="UnauthorizedAgent",
        proposed_action="ENROLL_MEMBER"
    )

    is_valid, verdict, violations = acve.verify_action_intent(
        malicious_intent,
        caller_role="gym_admin",
        caller_tenant_id="tenant_attacker"
    )

    assert is_valid is False
    assert verdict == "REJECTED_COMPLIANCE_FAILURE"
    assert any("Cross-tenant isolation violation" in v for v in violations)

def test_acve_rbac_enforcement():
    db_store.reset()
    tige.initialize_tenant_genome("tenant_rbac", "RBAC Gym", "Free")

    # Member role tries to execute gym admin action
    admin_action_intent = IntentObject(
        tenant_id="tenant_rbac",
        source_agent="ClientApp",
        proposed_action="UPGRADE_SUBSCRIPTION"
    )

    is_valid, verdict, violations = acve.verify_action_intent(
        admin_action_intent,
        caller_role="member"
    )

    assert is_valid is False
    assert any("RBAC policy violation" in v for v in violations)
