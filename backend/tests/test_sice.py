import pytest
from app.engines.tige import tige
from app.engines.sice import sice
from app.database import db_store

def test_sice_preemptive_upgrade_synthesis():
    db_store.reset()
    g = tige.initialize_tenant_genome("tenant_sice_test", "SICE Test Gym", "Free")
    
    # 44 members out of 50, with growth velocity 1.0/day and 15 days remaining in cycle
    g.subscription.active_members = 44
    g.subscription.member_growth_velocity = 1.0
    g.subscription.days_remaining_in_cycle = 15
    db_store.save_genome(g)

    # Evaluate SICE
    intent = sice.evaluate_subscription_convergence("tenant_sice_test")
    assert intent is not None
    assert intent.proposed_action == "PREEMPTIVE_UPGRADE_RECOMMENDATION"
    assert intent.payload["recommended_tier"] == "Silver"
    assert intent.payload["prorated_cost"] > 0.0

    # Execute upgrade
    upgraded = sice.execute_preemptive_upgrade("tenant_sice_test", "Silver")
    assert upgraded is True
    
    updated_g = db_store.get_genome("tenant_sice_test")
    assert updated_g.subscription.tier == "Silver"
    assert updated_g.subscription.max_members == 250
    assert updated_g.subscription.upgrade_recommended is False
