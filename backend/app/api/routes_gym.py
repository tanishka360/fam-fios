from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import time
from app.models.events import TenantEvent
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.engines.agents.membership_agent import membership_agent
from app.engines.sice import sice
from app.engines.acve import acve
from app.engines.tek import tek
from app.database import db_store

router = APIRouter(prefix="/gym", tags=["Gym Operations"])

class EnrollMemberRequest(BaseModel):
    member_id: str
    name: str
    email: str
    goal: str = "hypertrophy"
    caller_role: str = "gym_admin"
    caller_tenant_id: Optional[str] = None

class CheckInRequest(BaseModel):
    member_id: str
    hour: Optional[int] = None

class LogWorkoutRequest(BaseModel):
    member_id: str
    exercise: str
    total_volume_kg: float
    rpe: float = 8.0

@router.post("/{tenant_id}/members")
def enroll_member(tenant_id: str, req: EnrollMemberRequest):
    start_time = time.time()
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    pre_hash = genome.genome_integrity_hash

    # 1. Specialized Agent synthesizes intent
    intent = membership_agent.propose_enrollment(tenant_id, req.model_dump())

    # 2. ACVE verifies compliance (isolation, RBAC, quota)
    is_valid, verdict, violations = acve.verify_action_intent(
        intent,
        caller_role=req.caller_role,
        caller_tenant_id=req.caller_tenant_id
    )

    if not is_valid:
        duration_ms = (time.time() - start_time) * 1000
        tek.record_execution_fragment(
            tenant_id=tenant_id,
            triggering_intent_id=intent.intent_id,
            action_type="ENROLL_MEMBER",
            pre_hash=pre_hash,
            post_hash=genome.genome_integrity_hash,
            resources={"rejection": True},
            duration_ms=duration_ms,
            success=False,
            notes=f"Compliance check failed: {', '.join(violations)}"
        )
        raise HTTPException(status_code=403, detail={"verdict": verdict, "violations": violations})

    # 3. Execution & TIGE state update
    event = TenantEvent(
        tenant_id=tenant_id,
        role_context=req.caller_role,
        event_type="member_signup",
        operational_params={"member_id": req.member_id, "name": req.name}
    )
    db_store.log_event(event)
    updated_genome = tige.update_genome_from_event(event)

    # 4. Check SICE pre-emptive convergence
    upgrade_intent = sice.evaluate_subscription_convergence(tenant_id)

    # 5. DTDF dynamic restructuring
    dtdfe.construct_fabric(updated_genome)

    # 6. TEFR Fragment recording
    duration_ms = (time.time() - start_time) * 1000
    tek.record_execution_fragment(
        tenant_id=tenant_id,
        triggering_intent_id=intent.intent_id,
        action_type="ENROLL_MEMBER",
        pre_hash=pre_hash,
        post_hash=updated_genome.genome_integrity_hash,
        resources={"db_write": 1, "genome_update": 1},
        duration_ms=duration_ms,
        success=True
    )

    return {
        "status": "ENROLLED",
        "member_id": req.member_id,
        "active_members": updated_genome.subscription.active_members,
        "max_members": updated_genome.subscription.max_members,
        "sice_upgrade_alert": updated_genome.subscription.upgrade_recommended,
        "recommended_tier": updated_genome.subscription.recommended_tier,
        "prorated_upgrade_cost": updated_genome.subscription.prorated_upgrade_cost
    }

@router.post("/{tenant_id}/checkin")
def record_checkin(tenant_id: str, req: CheckInRequest):
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    event = TenantEvent(
        tenant_id=tenant_id,
        role_context="member",
        event_type="check_in",
        operational_params={"member_id": req.member_id, "hour": req.hour}
    )
    db_store.log_event(event)
    updated_genome = tige.update_genome_from_event(event)
    dtdfe.construct_fabric(updated_genome)

    return {
        "status": "CHECKIN_RECORDED",
        "member_id": req.member_id,
        "peak_hour_ratio": updated_genome.usage.peak_hour_ratio,
        "daily_checkin_avg": updated_genome.usage.daily_checkin_avg
    }

@router.post("/{tenant_id}/workout")
def log_workout(tenant_id: str, req: LogWorkoutRequest):
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    event = TenantEvent(
        tenant_id=tenant_id,
        role_context="member",
        event_type="workout_logged",
        operational_params=req.model_dump()
    )
    db_store.log_event(event)
    updated_genome = tige.update_genome_from_event(event)

    # Store workout session in db_store
    if tenant_id not in db_store.workout_logs:
        db_store.workout_logs[tenant_id] = []
    db_store.workout_logs[tenant_id].append(req.model_dump())

    return {
        "status": "WORKOUT_RECORDED",
        "workout_velocity": updated_genome.usage.workout_log_velocity
    }

@router.get("/{tenant_id}/sice-status")
def get_sice_status(tenant_id: str):
    upgrade_intent = sice.evaluate_subscription_convergence(tenant_id)
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    return {
        "tenant_id": tenant_id,
        "tier": genome.subscription.tier,
        "active_members": genome.subscription.active_members,
        "max_members": genome.subscription.max_members,
        "projected_utilization_ratio": genome.subscription.projected_utilization_ratio,
        "upgrade_recommended": genome.subscription.upgrade_recommended,
        "recommended_tier": genome.subscription.recommended_tier,
        "prorated_upgrade_cost": genome.subscription.prorated_upgrade_cost,
        "intent_details": upgrade_intent.model_dump() if upgrade_intent else None
    }

class UpgradeTierRequest(BaseModel):
    target_tier: str

@router.post("/{tenant_id}/sice-upgrade")
def trigger_sice_upgrade(tenant_id: str, req: UpgradeTierRequest):
    success = sice.execute_preemptive_upgrade(tenant_id, req.target_tier)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to execute pre-emptive upgrade.")
    
    genome = db_store.get_genome(tenant_id)
    dtdfe.construct_fabric(genome)
    return {
        "status": "UPGRADE_SUCCESSFUL",
        "new_tier": genome.subscription.tier,
        "max_members": genome.subscription.max_members,
        "allocated_cpu": genome.resource.allocated_cpu_cores,
        "allocated_memory_mb": genome.resource.allocated_memory_mb
    }
