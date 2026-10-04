from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

class SubscriptionVector(BaseModel):
    tier: str = "Free" # Free, Silver, Gold
    active_members: int = 0
    max_members: int = 50
    active_trainers: int = 0
    max_trainers: int = 2
    days_remaining_in_cycle: int = 30
    member_growth_velocity: float = 0.0 # members/day
    projected_utilization_ratio: float = 0.0 # projected member count / max_members
    upgrade_recommended: bool = False
    recommended_tier: Optional[str] = None
    prorated_upgrade_cost: float = 0.0

class UsageVector(BaseModel):
    daily_checkin_avg: float = 0.0
    peak_hour_ratio: float = 0.0 # proportion of traffic in 6-9 AM and 5-8 PM
    workout_log_velocity: float = 0.0 # logs per day
    api_throughput_rps: float = 0.0
    hourly_histogram: Dict[str, int] = Field(default_factory=lambda: {str(h): 0 for h in range(24)})

class RolePermissionVector(BaseModel):
    admin_count: int = 1
    trainer_count: int = 0
    member_count: int = 0
    elevated_roles_granted: int = 0
    rbac_violations_logged: int = 0

class ResourceVector(BaseModel):
    allocated_cpu_cores: float = 1.0
    allocated_memory_mb: int = 512
    materialized_partitions: int = 1
    active_db_shards: int = 1
    buffer_headroom_pct: float = 25.0
    is_preemptively_scaled: bool = False

class ComplianceVector(BaseModel):
    isolation_score: float = 1.0 # 1.0 is strictly isolated
    data_residency_region: str = "ap-south-1" # Default region (VIT / India)
    gdpr_ccpa_compliant: bool = True
    compliance_audit_count: int = 0
    total_violations_blocked: int = 0

class TrustVector(BaseModel):
    reputation_score: float = 1.0
    federated_contribution_weight: float = 1.0
    anomaly_score: float = 0.0
    plateau_detection_count: int = 0

class TenantGenome(BaseModel):
    tenant_id: str
    gym_name: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    generation: int = 1
    subscription: SubscriptionVector = Field(default_factory=SubscriptionVector)
    usage: UsageVector = Field(default_factory=UsageVector)
    role_permission: RolePermissionVector = Field(default_factory=RolePermissionVector)
    resource: ResourceVector = Field(default_factory=ResourceVector)
    compliance: ComplianceVector = Field(default_factory=ComplianceVector)
    trust: TrustVector = Field(default_factory=TrustVector)
    genome_integrity_hash: str = ""

    def calculate_integrity_hash(self) -> str:
        """Computes SHA-256 hash across all computational vectors."""
        serialized = json.dumps({
            "tenant_id": self.tenant_id,
            "generation": self.generation,
            "subscription": self.subscription.model_dump(),
            "usage": self.usage.model_dump(),
            "role_permission": self.role_permission.model_dump(),
            "resource": self.resource.model_dump(),
            "compliance": self.compliance.model_dump(),
            "trust": self.trust.model_dump(),
        }, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def update_integrity(self):
        self.updated_at = datetime.utcnow().isoformat()
        self.genome_integrity_hash = self.calculate_integrity_hash()
