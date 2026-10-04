from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from app.models.genome import TenantGenome
from app.models.fragments import TenantExecutionFragment
from app.core.config import settings
from app.database import db_store
from app.engines.dtdfe import dtdfe

class TenantEvolutionKernel:
    """
    Tenant Evolution Kernel (TEK):
    Ingests execution fragments from the Tenant Execution Fragment Repository (TEFR).
    Continuously refines tenant genomes, dependency fabric weights, predictive parameters,
    and federated contribution weights, enabling continuous closed-loop computational adaptation.
    """

    def record_execution_fragment(
        self,
        tenant_id: str,
        triggering_intent_id: str,
        action_type: str,
        pre_hash: str,
        post_hash: str,
        resources: Dict[str, Any],
        duration_ms: float,
        success: bool = True,
        notes: Optional[str] = None
    ) -> TenantExecutionFragment:
        fragment = TenantExecutionFragment(
            tenant_id=tenant_id,
            triggering_intent_id=triggering_intent_id,
            action_type=action_type,
            pre_execution_state_hash=pre_hash,
            post_execution_state_hash=post_hash,
            resources_utilized=resources,
            execution_duration_ms=round(duration_ms, 2),
            success=success,
            validation_verdict="APPROVED" if success else "FAILED",
            audit_notes=notes
        )
        db_store.log_fragment(fragment)
        return fragment

    def run_evolution_cycle(self, tenant_id: str) -> Dict[str, Any]:
        """
        Analyzes historical execution fragments for the tenant.
        Adjusts trust scores, federated contribution weights, and advances the genome generation.
        """
        fragments = db_store.get_fragments_for_tenant(tenant_id)
        genome = db_store.get_genome(tenant_id)
        if not genome or not fragments:
            return {"status": "NO_EVOLUTION", "reason": "Insufficient fragments"}

        successes = sum(1 for f in fragments if f.success)
        success_rate = successes / len(fragments)
        avg_latency = sum(f.execution_duration_ms for f in fragments) / len(fragments)

        # Evolutionary adaptation of trust and federated contribution weight
        if success_rate >= 0.90:
            genome.trust.reputation_score = min(1.0, genome.trust.reputation_score + 0.02)
            genome.trust.federated_contribution_weight = min(1.0, genome.trust.federated_contribution_weight + 0.05)
        else:
            genome.trust.reputation_score = max(0.2, genome.trust.reputation_score - 0.10)
            genome.trust.federated_contribution_weight = max(0.1, genome.trust.federated_contribution_weight - 0.15)

        # Increment generation counter
        genome.generation += 1
        genome.update_integrity()
        db_store.save_genome(genome)

        # Restructure Dynamic Tenant Dependency Fabric with updated parameters
        updated_fabric = dtdfe.construct_fabric(genome)

        evolution_summary = {
            "tenant_id": tenant_id,
            "new_generation": genome.generation,
            "success_rate": round(success_rate, 3),
            "avg_latency_ms": round(avg_latency, 2),
            "adapted_trust_score": round(genome.trust.reputation_score, 3),
            "adapted_federated_weight": round(genome.trust.federated_contribution_weight, 3),
            "active_dependency_edges": len(updated_fabric),
            "timestamp": datetime.utcnow().isoformat()
        }
        return evolution_summary

tek = TenantEvolutionKernel()
