from typing import List
from app.engines.agents.base import BaseFitnessAgent
from app.models.genome import TenantGenome
from app.models.intents import IntentObject

class MembershipAgent(BaseFitnessAgent):
    def __init__(self):
        super().__init__("MembershipAgent")

    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        intents: List[IntentObject] = []
        sub = genome.subscription
        utilization = sub.active_members / max(1, sub.max_members)
        
        # Check for member surge / capacity threshold
        if utilization >= 0.80:
            intent = IntentObject(
                tenant_id=genome.tenant_id,
                source_agent=self.name,
                proposed_action="EVALUATE_MEMBER_CAPACITY_SURGE",
                expected_operational_impact=f"Tenant is at {utilization*100:.1f}% member capacity ({sub.active_members}/{sub.max_members}).",
                required_resources={"action": "reconcile_subscription", "current_tier": sub.tier},
                dependency_footprint=[f"TIER:{sub.tier}", "MEMBER_CAP_ENFORCEMENT"],
                confidence_score=0.96,
                execution_priority=2,
                payload={
                    "active_members": sub.active_members,
                    "max_members": sub.max_members,
                    "utilization_ratio": utilization,
                    "growth_velocity": sub.member_growth_velocity
                }
            )
            intents.append(intent)
            self.dispatch_intent(intent)

        return intents

    def propose_enrollment(self, tenant_id: str, member_data: dict) -> IntentObject:
        intent = IntentObject(
            tenant_id=tenant_id,
            source_agent=self.name,
            proposed_action="ENROLL_MEMBER",
            expected_operational_impact=f"Adding new member {member_data.get('name', 'Anonymous')}.",
            required_resources={"db_write": 1, "quota_slot": 1},
            dependency_footprint=["MEMBER_CAP_ENFORCEMENT", "ISOLATION_GUARD"],
            confidence_score=1.0,
            execution_priority=3,
            payload=member_data
        )
        self.dispatch_intent(intent)
        return intent

membership_agent = MembershipAgent()
