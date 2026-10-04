from typing import Optional, Dict, Any
from datetime import datetime
from app.models.genome import (
    TenantGenome, SubscriptionVector, UsageVector,
    RolePermissionVector, ResourceVector, ComplianceVector, TrustVector
)
from app.models.events import TenantEvent
from app.core.config import TIER_CONFIGS
from app.database import db_store

class TenantIsolationGenomeEngine:
    """
    Tenant Isolation Genome Engine (TIGE):
    Constructs, maintains, and evolves each tenant as an executable runtime object (TIG)
    consisting of Subscription, Usage, Role-Permission, Resource, Compliance, and Trust vectors.
    """

    def initialize_tenant_genome(self, tenant_id: str, gym_name: str, tier: str = "Free") -> TenantGenome:
        cfg = TIER_CONFIGS.get(tier, TIER_CONFIGS["Free"])
        
        subscription_vec = SubscriptionVector(
            tier=tier,
            active_members=0,
            max_members=cfg.max_members,
            active_trainers=0,
            max_trainers=cfg.max_trainers,
            days_remaining_in_cycle=30,
            member_growth_velocity=0.0,
            projected_utilization_ratio=0.0,
            upgrade_recommended=False,
            prorated_upgrade_cost=0.0
        )
        
        usage_vec = UsageVector()
        role_vec = RolePermissionVector(admin_count=1, trainer_count=0, member_count=0)
        resource_vec = ResourceVector(
            allocated_cpu_cores=cfg.base_cpu_cores,
            allocated_memory_mb=cfg.base_memory_mb,
            materialized_partitions=1,
            active_db_shards=1
        )
        compliance_vec = ComplianceVector(isolation_score=1.0)
        trust_vec = TrustVector(reputation_score=1.0, federated_contribution_weight=1.0)

        genome = TenantGenome(
            tenant_id=tenant_id,
            gym_name=gym_name,
            subscription=subscription_vec,
            usage=usage_vec,
            role_permission=role_vec,
            resource=resource_vec,
            compliance=compliance_vec,
            trust=trust_vec
        )
        genome.update_integrity()
        db_store.save_genome(genome)
        return genome

    def update_genome_from_event(self, event: TenantEvent) -> TenantGenome:
        genome = db_store.get_genome(event.tenant_id)
        if not genome:
            raise ValueError(f"Genome for tenant {event.tenant_id} not found.")

        # Process event by type
        if event.event_type == "member_signup":
            genome.subscription.active_members += 1
            genome.role_permission.member_count += 1
            # Update member growth velocity estimate
            days_elapsed = max(1, 30 - genome.subscription.days_remaining_in_cycle)
            genome.subscription.member_growth_velocity = genome.subscription.active_members / days_elapsed

        elif event.event_type == "trainer_assigned":
            genome.subscription.active_trainers += 1
            genome.role_permission.trainer_count += 1

        elif event.event_type == "check_in":
            hour = event.operational_params.get("hour", datetime.utcnow().hour)
            hour_str = str(hour)
            genome.usage.hourly_histogram[hour_str] = genome.usage.hourly_histogram.get(hour_str, 0) + 1
            
            total_checkins = sum(genome.usage.hourly_histogram.values())
            # Peak hours: 6-9 AM (6,7,8) and 5-8 PM (17,18,19)
            peak_checkins = sum(
                genome.usage.hourly_histogram.get(str(h), 0)
                for h in [6, 7, 8, 17, 18, 19]
            )
            genome.usage.peak_hour_ratio = round(peak_checkins / max(1, total_checkins), 3)
            genome.usage.daily_checkin_avg = round(total_checkins / 30.0, 2)

        elif event.event_type == "workout_logged":
            genome.usage.workout_log_velocity = round(genome.usage.workout_log_velocity + 0.1, 2)

        elif event.event_type == "rbac_violation":
            genome.role_permission.rbac_violations_logged += 1
            genome.compliance.isolation_score = max(0.0, genome.compliance.isolation_score - 0.05)
            genome.compliance.total_violations_blocked += 1

        genome.update_integrity()
        db_store.save_genome(genome)
        return genome

tige = TenantIsolationGenomeEngine()
