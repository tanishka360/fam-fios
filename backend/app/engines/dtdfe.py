from pydantic import BaseModel, Field
from typing import Dict, List, Any
from app.models.genome import TenantGenome
from app.database import db_store

class DependencyEdge(BaseModel):
    source_node: str # e.g. "ROLE:Member", "TIER:Free", "TENANT:gym_01"
    target_node: str # e.g. "RESOURCE:DB_Shard", "POLICY:ACVE_Boundary"
    dependency_type: str # MEMBER_CAP_ENFORCEMENT, ROLE_PRIVILEGE_BINDING, RESOURCE_QUOTA, ISOLATION_GUARD
    enforcement_weight: float = 0.5 # 0.0 to 1.0
    execution_priority: int = 5 # 1 (Critical) to 10 (Background)
    temporal_persistence: str = "CYCLICAL" # EPHEMERAL, SESSION, CYCLICAL, PERMANENT
    confidence_level: float = 0.95

class DynamicTenantDependencyFabricEngine:
    """
    Dynamic Tenant Dependency Fabric Engine (DTDFE):
    Constructs, links, and adapts runtime execution dependency graphs for each tenant.
    Enforcement weights and priorities scale dynamically according to tenant load,
    approaching limits, and compliance status.
    """
    def __init__(self):
        self._fabric_cache: Dict[str, List[DependencyEdge]] = {}

    def construct_fabric(self, genome: TenantGenome) -> List[DependencyEdge]:
        edges: List[DependencyEdge] = []
        tenant_id = genome.tenant_id
        
        # 1. Member Quota Dependency
        member_ratio = genome.subscription.active_members / max(1, genome.subscription.max_members)
        member_weight = min(1.0, 0.4 + (0.6 * member_ratio))
        member_prio = 2 if member_ratio > 0.85 else 5
        
        edges.append(DependencyEdge(
            source_node=f"TENANT:{tenant_id}",
            target_node=f"TIER:{genome.subscription.tier}",
            dependency_type="MEMBER_CAP_ENFORCEMENT",
            enforcement_weight=round(member_weight, 3),
            execution_priority=member_prio,
            temporal_persistence="CYCLICAL",
            confidence_level=0.98
        ))

        # 2. Resource Allocation Dependency (tied to peak hour usage)
        peak_ratio = genome.usage.peak_hour_ratio
        res_weight = min(1.0, 0.5 + (0.5 * peak_ratio))
        edges.append(DependencyEdge(
            source_node=f"TENANT:{tenant_id}",
            target_node="RESOURCE:Compute_Partitions",
            dependency_type="RESOURCE_QUOTA",
            enforcement_weight=round(res_weight, 3),
            execution_priority=3 if peak_ratio > 0.6 else 6,
            temporal_persistence="SESSION",
            confidence_level=0.92
        ))

        # 3. Isolation & Compliance Guard Dependency
        iso_score = genome.compliance.isolation_score
        edges.append(DependencyEdge(
            source_node=f"TENANT:{tenant_id}",
            target_node="POLICY:Tenant_Boundary_ACVE",
            dependency_type="ISOLATION_GUARD",
            enforcement_weight=1.0, # Always strictly enforced
            execution_priority=1,   # Top priority
            temporal_persistence="PERMANENT",
            confidence_level=round(iso_score, 3)
        ))

        # 4. Federated Intelligence Contribution Dependency
        trust_weight = genome.trust.federated_contribution_weight
        edges.append(DependencyEdge(
            source_node=f"TENANT:{tenant_id}",
            target_node="INTELLIGENCE:FAFIE_Global_Model",
            dependency_type="FEDERATED_GRADIENT_AGGREGATION",
            enforcement_weight=round(trust_weight, 3),
            execution_priority=7,
            temporal_persistence="CYCLICAL",
            confidence_level=round(genome.trust.reputation_score, 3)
        ))

        self._fabric_cache[tenant_id] = edges
        return edges

    def get_fabric(self, tenant_id: str) -> List[DependencyEdge]:
        if tenant_id not in self._fabric_cache:
            genome = db_store.get_genome(tenant_id)
            if genome:
                return self.construct_fabric(genome)
            return []
        return self._fabric_cache[tenant_id]

dtdfe = DynamicTenantDependencyFabricEngine()
