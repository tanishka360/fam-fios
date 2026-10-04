from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
from app.models.intents import IntentObject
from app.database import db_store

class AutonomousComplianceVerificationEngine:
    """
    Autonomous Compliance Verification Engine (ACVE):
    Multidimensional pre-execution policy verification gatekeeper.
    Enforces Role-Permission Rules, Subscription Constraints, Strict Tenant Isolation,
    Data Residency Policy, and Security Integrity.
    """

    ALLOWED_ROLE_ACTIONS = {
        "gym_admin": [
            "ENROLL_MEMBER", "ASSIGN_TRAINER", "UPGRADE_SUBSCRIPTION",
            "PREEMPTIVE_UPGRADE_RECOMMENDATION", "SCALE_PARTITION",
            "GENERATE_PERSONALIZED_FITNESS_PLAN", "CYCLE_RENEWAL_PREPARATION"
        ],
        "trainer": [
            "RECORD_ATTENDANCE", "LOG_WORKOUT", "TRIGGER_ADAPTIVE_WORKOUT_REVISION",
            "GENERATE_PERSONALIZED_FITNESS_PLAN"
        ],
        "member": [
            "CHECK_IN", "LOG_WORKOUT", "VIEW_PROFILE", "REQUEST_RECOMMENDATION"
        ],
        "system": [
            "EVALUATE_MEMBER_CAPACITY_SURGE", "PREEMPTIVE_UPGRADE_RECOMMENDATION",
            "SIGNAL_PEAK_ATTENDANCE_CONGESTION", "RECOMMEND_TRAINER_EXPANSION",
            "TRIGGER_ADAPTIVE_WORKOUT_REVISION", "SCALE_PARTITION", "FEDERATED_AGGREGATION"
        ]
    }

    def verify_action_intent(
        self,
        intent: IntentObject,
        caller_role: str = "gym_admin",
        caller_tenant_id: Optional[str] = None
    ) -> Tuple[bool, str, List[str]]:
        violations: List[str] = []
        tenant_id = intent.tenant_id
        genome = db_store.get_genome(tenant_id)

        if not genome:
            return False, "REJECTED_UNKNOWN_TENANT", ["Genome not found for tenant"]

        effective_caller_tenant = caller_tenant_id or tenant_id

        # 1. Strict Tenant Isolation Boundary Check
        if effective_caller_tenant != tenant_id:
            violations.append(
                f"Cross-tenant isolation violation: Caller tenant '{effective_caller_tenant}' attempted action on '{tenant_id}'."
            )
            # Log security penalty in genome
            genome.compliance.isolation_score = max(0.0, genome.compliance.isolation_score - 0.20)
            genome.compliance.total_violations_blocked += 1
            genome.update_integrity()
            db_store.save_genome(genome)

        # 2. Role-Based Access Control (RBAC) Check
        allowed_actions = self.ALLOWED_ROLE_ACTIONS.get(caller_role, [])
        if intent.proposed_action not in allowed_actions:
            violations.append(
                f"RBAC policy violation: Role '{caller_role}' is not authorized to execute '{intent.proposed_action}'."
            )
            genome.role_permission.rbac_violations_logged += 1
            genome.compliance.total_violations_blocked += 1

        # 3. Subscription Constraints Check
        if intent.proposed_action == "ENROLL_MEMBER":
            sub = genome.subscription
            if sub.active_members >= sub.max_members:
                violations.append(
                    f"Subscription quota breached: Tenant has reached tier limit ({sub.active_members}/{sub.max_members}). Upgrade required."
                )

        # 4. Data Residency Verification
        requested_region = intent.payload.get("data_residency_region", genome.compliance.data_residency_region)
        if requested_region != genome.compliance.data_residency_region:
            violations.append(
                f"Data residency policy violation: Mismatch between requested region '{requested_region}' and tenant home region '{genome.compliance.data_residency_region}'."
            )

        genome.compliance.compliance_audit_count += 1
        is_authorized = len(violations) == 0
        verdict = "AUTHORIZED" if is_authorized else "REJECTED_COMPLIANCE_FAILURE"

        # Log audit record
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "intent_id": intent.intent_id,
            "tenant_id": tenant_id,
            "action": intent.proposed_action,
            "caller_role": caller_role,
            "verdict": verdict,
            "violations": violations
        }
        db_store.log_compliance(audit_entry)

        genome.update_integrity()
        db_store.save_genome(genome)

        return is_authorized, verdict, violations

acve = AutonomousComplianceVerificationEngine()
