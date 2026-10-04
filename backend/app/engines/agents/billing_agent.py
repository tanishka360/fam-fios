from typing import List
from app.engines.agents.base import BaseFitnessAgent
from app.models.genome import TenantGenome
from app.models.intents import IntentObject

class BillingAgent(BaseFitnessAgent):
    def __init__(self):
        super().__init__("BillingAgent")

    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        intents: List[IntentObject] = []
        sub = genome.subscription

        # Check cycle end approaching
        if sub.days_remaining_in_cycle <= 3:
            intent = IntentObject(
                tenant_id=genome.tenant_id,
                source_agent=self.name,
                proposed_action="CYCLE_RENEWAL_PREPARATION",
                expected_operational_impact=f"Billing cycle closes in {sub.days_remaining_in_cycle} days.",
                required_resources={"billing_service": 1},
                dependency_footprint=[f"TIER:{sub.tier}", "BILLING_CYCLE"],
                confidence_score=0.99,
                execution_priority=4,
                payload={"tier": sub.tier, "days_remaining": sub.days_remaining_in_cycle}
            )
            intents.append(intent)
            self.dispatch_intent(intent)

        return intents

billing_agent = BillingAgent()
