from typing import Dict, Any, Optional
from app.models.genome import TenantGenome
from app.models.intents import IntentObject
from app.core.config import TIER_CONFIGS
from app.database import db_store

class SubscriptionIntentConvergenceEngine:
    """
    Subscription Intent Convergence Engine (SICE):
    Predictively anticipates plan limit breaches ahead of cycle boundaries.
    Synthesizes pre-emptive, prorated upgrade recommendations before hard rejections occur.
    """

    def evaluate_subscription_convergence(self, tenant_id: str) -> Optional[IntentObject]:
        genome = db_store.get_genome(tenant_id)
        if not genome:
            return None

        sub = genome.subscription
        current_tier_cfg = TIER_CONFIGS.get(sub.tier, TIER_CONFIGS["Free"])
        
        # Calculate velocity and projected utilization
        days_rem = max(1, sub.days_remaining_in_cycle)
        velocity = sub.member_growth_velocity
        projected_at_end = sub.active_members + (velocity * days_rem)
        projected_ratio = projected_at_end / max(1, sub.max_members)
        
        sub.projected_utilization_ratio = round(projected_ratio, 3)

        # Breach condition: Projected > 95% of cap or current >= 85%
        current_ratio = sub.active_members / max(1, sub.max_members)
        if (projected_ratio >= 0.95 or current_ratio >= 0.85) and sub.tier != "Gold":
            next_tier = "Silver" if sub.tier == "Free" else "Gold"
            next_tier_cfg = TIER_CONFIGS[next_tier]
            
            # Prorated calculation
            price_diff = next_tier_cfg.monthly_price - current_tier_cfg.monthly_price
            prorated_amount = round(price_diff * (days_rem / 30.0), 2)

            sub.upgrade_recommended = True
            sub.recommended_tier = next_tier
            sub.prorated_upgrade_cost = max(0.0, prorated_amount)
            genome.update_integrity()
            db_store.save_genome(genome)

            intent = IntentObject(
                tenant_id=tenant_id,
                source_agent="SubscriptionIntentConvergenceEngine",
                proposed_action="PREEMPTIVE_UPGRADE_RECOMMENDATION",
                expected_operational_impact=(
                    f"Tenant projected to reach {int(projected_at_end)} members by cycle end "
                    f"(cap: {sub.max_members}). Recommending pre-emptive upgrade to {next_tier} "
                    f"at prorated cost of ${prorated_amount} ({days_rem} days remaining)."
                ),
                required_resources={"billing_reconciliation": True, "tier_switch": next_tier},
                dependency_footprint=[f"TIER:{sub.tier}", f"TIER:{next_tier}", "MEMBER_CAP_ENFORCEMENT"],
                confidence_score=0.98,
                execution_priority=1, # High priority to prevent operational blockage
                payload={
                    "current_tier": sub.tier,
                    "recommended_tier": next_tier,
                    "active_members": sub.active_members,
                    "max_members": sub.max_members,
                    "projected_members": int(projected_at_end),
                    "days_remaining": days_rem,
                    "prorated_cost": prorated_amount
                }
            )
            db_store.save_intent(intent)
            return intent

        return None

    def execute_preemptive_upgrade(self, tenant_id: str, target_tier: str) -> bool:
        """Executes the upgrade cleanly, updating genome quotas and resource vectors."""
        genome = db_store.get_genome(tenant_id)
        if not genome or target_tier not in TIER_CONFIGS:
            return False

        cfg = TIER_CONFIGS[target_tier]
        genome.subscription.tier = target_tier
        genome.subscription.max_members = cfg.max_members
        genome.subscription.max_trainers = cfg.max_trainers
        genome.subscription.upgrade_recommended = False
        genome.subscription.recommended_tier = None
        genome.subscription.prorated_upgrade_cost = 0.0

        # Scale base resource allocations
        genome.resource.allocated_cpu_cores = cfg.base_cpu_cores
        genome.resource.allocated_memory_mb = cfg.base_memory_mb
        genome.resource.materialized_partitions = max(genome.resource.materialized_partitions, cfg.partition_quota)

        genome.update_integrity()
        db_store.save_genome(genome)
        return True

sice = SubscriptionIntentConvergenceEngine()
