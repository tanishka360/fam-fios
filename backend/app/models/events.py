from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class TenantEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tenant_id: str
    role_context: str # e.g., 'gym_admin', 'trainer', 'member', 'system'
    event_type: str # 'member_signup', 'check_in', 'workout_logged', 'payment_received', etc.
    operational_params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    isolation_signature: Optional[str] = None
