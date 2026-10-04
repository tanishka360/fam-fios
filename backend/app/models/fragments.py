from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class TenantExecutionFragment(BaseModel):
    fragment_id: str = Field(default_factory=lambda: f"frg_{uuid.uuid4().hex[:12]}")
    tenant_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    triggering_intent_id: str
    action_type: str
    pre_execution_state_hash: str
    post_execution_state_hash: str
    resources_utilized: Dict[str, Any] = Field(default_factory=dict)
    execution_duration_ms: float = 0.0
    success: bool = True
    validation_verdict: str = "APPROVED"
    feedback_score: float = 1.0 # Feedback metric (latency, accuracy, compliance satisfaction)
    audit_notes: Optional[str] = None
