import pytest
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.engines.agents.membership_agent import membership_agent
from app.engines.sice import sice
from app.engines.acve import acve
from app.engines.tek import tek
from app.models.events import TenantEvent
from app.database import db_store

def test_full_fam_fios_closed_loop():
    db_store.reset()
    
    # 1. Tenant Data Acquisition & Genome Initialization
    genome = tige.initialize_tenant_genome("tenant_loop", "Closed Loop Gym", "Free")
    assert genome.generation == 1
    
    # 2. Dynamic Fabric Construction
    fabric = dtdfe.construct_fabric(genome)
    assert len(fabric) >= 4

    # 3. Autonomous Agent Intent Synthesis
    member_data = {"name": "Alice Wonderland", "email": "alice@loop.com"}
    intent = membership_agent.propose_enrollment("tenant_loop", member_data)
    assert intent.status == "PENDING"

    # 4. ACVE Pre-execution Compliance Verification
    is_valid, verdict, violations = acve.verify_action_intent(
        intent,
        caller_role="gym_admin",
        caller_tenant_id="tenant_loop"
    )
    assert is_valid is True
    assert verdict == "AUTHORIZED"

    # 5. Execution & TIGE Event Processing
    event = TenantEvent(
        tenant_id="tenant_loop",
        role_context="gym_admin",
        event_type="member_signup",
        operational_params=member_data
    )
    updated_genome = tige.update_genome_from_event(event)
    assert updated_genome.subscription.active_members == 1

    # 6. SICE Predictive Convergence Evaluation
    sice.evaluate_subscription_convergence("tenant_loop")

    # 7. TEFR Fragment Logging
    frag = tek.record_execution_fragment(
        tenant_id="tenant_loop",
        triggering_intent_id=intent.intent_id,
        action_type="ENROLL_MEMBER",
        pre_hash=genome.genome_integrity_hash,
        post_hash=updated_genome.genome_integrity_hash,
        resources={"db_write": 1},
        duration_ms=12.5,
        success=True
    )
    assert frag.fragment_id in [f.fragment_id for f in db_store.get_fragments_for_tenant("tenant_loop")]

    # 8. TEK Evolution Cycle
    evo_result = tek.run_evolution_cycle("tenant_loop")
    assert evo_result["new_generation"] == 2
    assert evo_result["success_rate"] == 1.0

    evolved_genome = db_store.get_genome("tenant_loop")
    assert evolved_genome.generation == 2
