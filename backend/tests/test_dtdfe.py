import pytest
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.database import db_store

def test_dtdf_dynamic_reweighting():
    db_store.reset()
    g = tige.initialize_tenant_genome("tenant_test_dtdf", "Dynamic Gym", "Free")
    
    # Low usage fabric
    fabric_low = dtdfe.construct_fabric(g)
    member_edge_low = next(e for e in fabric_low if e.dependency_type == "MEMBER_CAP_ENFORCEMENT")
    assert member_edge_low.enforcement_weight <= 0.5
    assert member_edge_low.execution_priority == 5

    # Simulate near-capacity surge (45 / 50 members)
    g.subscription.active_members = 45
    fabric_high = dtdfe.construct_fabric(g)
    member_edge_high = next(e for e in fabric_high if e.dependency_type == "MEMBER_CAP_ENFORCEMENT")
    
    # Enforcement weight must increase and priority must become urgent (2)
    assert member_edge_high.enforcement_weight > 0.90
    assert member_edge_high.execution_priority == 2
