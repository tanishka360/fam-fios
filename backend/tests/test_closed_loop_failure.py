import pytest
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.engines.agents.membership_agent import membership_agent
from app.engines.sice import sice
from app.engines.acve import acve
from app.engines.tek import tek
from app.models.events import TenantEvent
from app.database import db_store

def test_full_fam_fios_closed_loop_rejection():
    db_store.reset()
    tenant_id = 'tenant_loop_fail'
    genome = tige.initialize_tenant_genome(tenant_id, 'Closed Loop Failure Gym', 'Free')
    assert genome.generation == 1
    initial_reputation = genome.trust.reputation_score
    initial_hash = genome.genome_integrity_hash

    fabric = dtdfe.construct_fabric(genome)
    assert len(fabric) >= 4

    member_data = {'name': 'Eve Intruder', 'email': 'eve@unauthorized.com'}
    intent = membership_agent.propose_enrollment(tenant_id, member_data)
    assert intent.status == 'PENDING'
    assert intent.proposed_action == 'ENROLL_MEMBER'

    # 4. ACVE Pre-execution Compliance Verification (FAILURE PATH)
    is_valid, verdict, violations = acve.verify_action_intent(
        intent,
        caller_role='member',
        caller_tenant_id=tenant_id
    )
    assert is_valid is False
    assert verdict == 'REJECTED_COMPLIANCE_FAILURE'
    assert len(violations) > 0
    assert any('RBAC policy violation' in v for v in violations)

    # 5. Verify Compliance Audit Record Logged
    audits = [a for a in db_store.compliance_audits if a['tenant_id'] == tenant_id]
    assert len(audits) >= 1
    latest_audit = audits[-1]
    assert latest_audit['verdict'] == 'REJECTED_COMPLIANCE_FAILURE'
    assert latest_audit['action'] == 'ENROLL_MEMBER'
    assert latest_audit['caller_role'] == 'member'

    # 6. Prove Closed Loop Halts: Event is Blocked, State Does Not Mutate
    current_genome = db_store.get_genome(tenant_id)
    assert current_genome.subscription.active_members == 0
    assert current_genome.role_permission.rbac_violations_logged == 1
    assert current_genome.compliance.total_violations_blocked == 1

    # 7. TEFR Fragment Logging with success=False
    frag = tek.record_execution_fragment(
        tenant_id=tenant_id,
        triggering_intent_id=intent.intent_id,
        action_type='ENROLL_MEMBER',
        pre_hash=initial_hash,
        post_hash=current_genome.genome_integrity_hash,
        resources={'db_write': 0},
        duration_ms=4.2,
        success=False,
        notes=f'Blocked by ACVE: {violations[0]}'
    )
    assert frag.success is False
    assert frag.validation_verdict == 'FAILED'
    tenant_frags = db_store.get_fragments_for_tenant(tenant_id)
    assert frag.fragment_id in [f.fragment_id for f in tenant_frags]

    # 8. TEK Evolution Cycle Penalizes Failure Path
    evo_result = tek.run_evolution_cycle(tenant_id)
    assert evo_result['new_generation'] == 2
    assert evo_result['success_rate'] == 0.0
    evolved_genome = db_store.get_genome(tenant_id)
    assert evolved_genome.trust.reputation_score < initial_reputation
    assert evolved_genome.generation == 2

def test_full_fam_fios_closed_loop_cross_tenant_rejection():
    db_store.reset()
    victim_id = 'tenant_victim_loop'
    attacker_id = 'tenant_attacker_loop'
    victim_genome = tige.initialize_tenant_genome(victim_id, 'Victim Gym', 'Free')
    attacker_genome = tige.initialize_tenant_genome(attacker_id, 'Attacker Gym', 'Free')
    initial_isolation = victim_genome.compliance.isolation_score

    intent = membership_agent.propose_enrollment(victim_id, {'name': 'Spy', 'email': 'spy@attacker.com'})
    is_valid, verdict, violations = acve.verify_action_intent(
        intent,
        caller_role='gym_admin',
        caller_tenant_id=attacker_id
    )
    assert is_valid is False
    assert verdict == 'REJECTED_COMPLIANCE_FAILURE'
    assert any('Cross-tenant isolation violation' in v for v in violations)

    audits = [a for a in db_store.compliance_audits if a['tenant_id'] == victim_id]
    assert len(audits) >= 1
    assert audits[-1]['verdict'] == 'REJECTED_COMPLIANCE_FAILURE'
    assert audits[-1]['action'] == 'ENROLL_MEMBER'

    victim_after = db_store.get_genome(victim_id)
    assert victim_after.subscription.active_members == 0
    assert victim_after.compliance.isolation_score < initial_isolation
    assert victim_after.compliance.total_violations_blocked >= 1
