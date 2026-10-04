from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class IntentObject(BaseModel):
    intent_id: str = Field(default_factory=lambda: f"int_{uuid.uuid4().hex[:12]}")
    tenant_id: str
    source_agent: str # MembershipAgent, BillingAgent, AttendanceAgent, TrainerMatchingAgent, RecommendationAgent
    proposed_action: str # e.g. ENROLL_MEMBER, UPGRADE_SUBSCRIPTION, SCALE_PARTITIONS, ADJUST_WORKOUT_PLAN
    expected_operational_impact: str = "Standard operational impact"
    required_resources: Dict[str, Any] = Field(default_factory=dict)
    dependency_footprint: List[str] = Field(default_factory=list) # dynamic dependency references
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    execution_priority: int = Field(default=5, ge=1, le=10) # 1 highest, 10 lowest
    status: str = "PENDING" # PENDING, VALIDATED, EXECUTED, REJECTED
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
