import pytest
from app.engines.tige import tige
from app.models.events import TenantEvent
from app.database import db_store

def test_tige_initialization_and_isolation():
    db_store.reset()
    g_a = tige.initialize_tenant_genome("tenant_alpha", "Alpha Gym", "Free")
    g_b = tige.initialize_tenant_genome("tenant_beta", "Beta Gym", "Silver")

    assert g_a.subscription.tier == "Free"
    assert g_a.subscription.max_members == 50
    assert g_b.subscription.tier == "Silver"
    assert g_b.subscription.max_members == 250
    assert g_a.genome_integrity_hash != ""
    assert g_a.genome_integrity_hash != g_b.genome_integrity_hash

def test_tige_event_update():
    db_store.reset()
    g = tige.initialize_tenant_genome("tenant_gamma", "Gamma Gym", "Free")
    orig_hash = g.genome_integrity_hash

    # Signup event
    evt = TenantEvent(
        tenant_id="tenant_gamma",
        role_context="gym_admin",
        event_type="member_signup",
        operational_params={"name": "John Doe"}
    )
    updated = tige.update_genome_from_event(evt)
    
    assert updated.subscription.active_members == 1
    assert updated.role_permission.member_count == 1
    assert updated.genome_integrity_hash != orig_hash
