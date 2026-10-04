from typing import List, Dict, Any
from app.engines.agents.base import BaseFitnessAgent
from app.models.genome import TenantGenome
from app.models.intents import IntentObject

class RecommendationAgent(BaseFitnessAgent):
    def __init__(self):
        super().__init__("RecommendationAgent")

    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        intents: List[IntentObject] = []
        # If tenant has active plateau detections, generate plan adaptation intent
        if genome.trust.plateau_detection_count > 0:
            intent = IntentObject(
                tenant_id=genome.tenant_id,
                source_agent=self.name,
                proposed_action="TRIGGER_ADAPTIVE_WORKOUT_REVISION",
                expected_operational_impact=f"Detected {genome.trust.plateau_detection_count} member progress plateaus. Dynamic routine recalibration needed.",
                required_resources={"model_inference": 1},
                dependency_footprint=["FAFIE_LOCAL_MODEL", "WORKOUT_VOLUME_CALIBRATION"],
                confidence_score=0.97,
                execution_priority=4,
                payload={"plateau_count": genome.trust.plateau_detection_count}
            )
            intents.append(intent)
            self.dispatch_intent(intent)

        return intents

    def synthesize_recommendation_request(self, tenant_id: str, member_id: str, biometrics: Dict[str, Any]) -> IntentObject:
        intent = IntentObject(
            tenant_id=tenant_id,
            source_agent=self.name,
            proposed_action="GENERATE_PERSONALIZED_FITNESS_PLAN",
            expected_operational_impact=f"Synthesizing privacy-preserving ML workout/diet recommendation for member {member_id}.",
            required_resources={"fafie_inference": True},
            dependency_footprint=["FAFIE_GLOBAL_MODEL", "ISOLATION_GUARD"],
            confidence_score=0.95,
            execution_priority=3,
            payload={"member_id": member_id, "biometrics": biometrics}
        )
        self.dispatch_intent(intent)
        return intent

recommendation_agent = RecommendationAgent()
