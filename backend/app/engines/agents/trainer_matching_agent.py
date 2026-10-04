from typing import List
from app.engines.agents.base import BaseFitnessAgent
from app.models.genome import TenantGenome
from app.models.intents import IntentObject

class TrainerMatchingAgent(BaseFitnessAgent):
    def __init__(self):
        super().__init__("TrainerMatchingAgent")

    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        intents: List[IntentObject] = []
        sub = genome.subscription
        active_trainers = max(1, sub.active_trainers)
        ratio = sub.active_members / active_trainers
        
        # If client-to-trainer ratio exceeds 30:1, suggest trainer expansion
        if ratio > 30 and sub.active_trainers < sub.max_trainers:
            intent = IntentObject(
                tenant_id=genome.tenant_id,
                source_agent=self.name,
                proposed_action="RECOMMEND_TRAINER_EXPANSION",
                expected_operational_impact=f"High client-to-trainer ratio ({ratio:.1f}:1). Slot availability constrained.",
                required_resources={"trainer_roster": 1},
                dependency_footprint=["TRAINER_CLIENT_RATIO", "ROLE_PRIVILEGE_BINDING"],
                confidence_score=0.91,
                execution_priority=5,
                payload={"current_ratio": ratio, "active_trainers": sub.active_trainers}
            )
            intents.append(intent)
            self.dispatch_intent(intent)

        return intents

trainer_matching_agent = TrainerMatchingAgent()
