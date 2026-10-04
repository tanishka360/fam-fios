from typing import List
from datetime import datetime
from app.engines.agents.base import BaseFitnessAgent
from app.models.genome import TenantGenome
from app.models.intents import IntentObject

class AttendanceAgent(BaseFitnessAgent):
    def __init__(self):
        super().__init__("AttendanceAgent")

    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        intents: List[IntentObject] = []
        usage = genome.usage
        
        # If peak hour ratio is elevated, signal demand for load materialization
        if usage.peak_hour_ratio >= 0.40:
            intent = IntentObject(
                tenant_id=genome.tenant_id,
                source_agent=self.name,
                proposed_action="SIGNAL_PEAK_ATTENDANCE_CONGESTION",
                expected_operational_impact=f"Observed {usage.peak_hour_ratio*100:.1f}% check-in concentration during peak windows.",
                required_resources={"compute_boost": True},
                dependency_footprint=["RESOURCE_QUOTA", "HOURLY_TRAFFIC_SHAPER"],
                confidence_score=0.94,
                execution_priority=3,
                payload={
                    "peak_ratio": usage.peak_hour_ratio,
                    "daily_avg": usage.daily_checkin_avg,
                    "hourly_histogram": usage.hourly_histogram
                }
            )
            intents.append(intent)
            self.dispatch_intent(intent)

        return intents

attendance_agent = AttendanceAgent()
