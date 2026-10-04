from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.engines.acve import acve
from app.models.intents import IntentObject
from app.database import db_store

router = APIRouter(prefix="/compliance", tags=["Autonomous Compliance (ACVE)"])

class CrossTenantTestRequest(BaseModel):
    attacker_tenant_id: str
    target_tenant_id: str
    action: str = "ENROLL_MEMBER"

@router.get("/audits")
def get_compliance_audits():
    return {
        "total_audits": len(db_store.compliance_audits),
        "audit_records": db_store.compliance_audits[-50:] # latest 50 audits
    }

@router.post("/test-cross-tenant")
def simulate_cross_tenant_intrusion(req: CrossTenantTestRequest):
    """
    Simulates an unauthorized attempt by attacker_tenant_id
    to modify resources belonging to target_tenant_id.
    Demonstrates ACVE boundary defense and isolation penalty logging.
    """
    intent = IntentObject(
        tenant_id=req.target_tenant_id,
        source_agent="ExternalSpoofedAgent",
        proposed_action=req.action,
        expected_operational_impact="Malicious cross-tenant operation attempt",
        payload={"infiltrate": True}
    )

    is_authorized, verdict, violations = acve.verify_action_intent(
        intent=intent,
        caller_role="gym_admin",
        caller_tenant_id=req.attacker_tenant_id
    )

    return {
        "test_status": "INTERCEPTED" if not is_authorized else "LEAK_WARNING",
        "verdict": verdict,
        "violations": violations,
        "target_tenant": req.target_tenant_id,
        "caller_tenant": req.attacker_tenant_id
    }
