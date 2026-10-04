from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings, TIER_CONFIGS
from app.models.genome import TenantGenome
from app.database import db_store

class PredictiveTenantLoadMaterializationEngine:
    """
    Predictive Tenant Load Materialization Engine (PTLME):
    Anticipates tenant-specific compute and database demand ahead of peak attendance windows.
    Selectively pre-materializes tenant-scoped container & storage partitions to eliminate latency spikes.
    """

    def forecast_demand(self, genome: TenantGenome, target_hour: int) -> Dict[str, Any]:
        """
        Forecasts expected concurrent throughput and partition requirements
        for a specified hour based on the tenant's historical usage histogram.
        """
        hist = genome.usage.hourly_histogram
        hour_count = hist.get(str(target_hour), 0)
        total_hist = sum(hist.values())
        
        # Base hourly arrival probability
        arrival_prob = (hour_count / max(1, total_hist)) if total_hist > 0 else 0.04
        
        # Check if target hour falls within defined peak windows
        is_morning_peak = settings.PTLM_MORNING_PEAK[0] <= target_hour <= settings.PTLM_MORNING_PEAK[1]
        is_evening_peak = settings.PTLM_EVENING_PEAK[0] <= target_hour <= settings.PTLM_EVENING_PEAK[1]
        is_peak = is_morning_peak or is_evening_peak
        
        peak_multiplier = 1.8 if is_peak else 1.0
        predicted_concurrency = int(genome.subscription.active_members * arrival_prob * peak_multiplier)
        
        # Required partitions calculation
        tier_cfg = TIER_CONFIGS.get(genome.subscription.tier, TIER_CONFIGS["Free"])
        base_partitions = 1
        scale_needed = (predicted_concurrency > 15) or is_peak
        required_partitions = min(tier_cfg.partition_quota, (base_partitions + 2) if scale_needed else base_partitions)

        return {
            "target_hour": target_hour,
            "is_peak_window": is_peak,
            "predicted_concurrency": predicted_concurrency,
            "required_partitions": required_partitions,
            "lead_time_minutes": settings.PTLM_LEAD_MINUTES
        }

    def materialize_partitions_for_tenant(self, tenant_id: str, target_hour: Optional[int] = None) -> Dict[str, Any]:
        genome = db_store.get_genome(tenant_id)
        if not genome:
            raise ValueError(f"Tenant {tenant_id} not found.")

        if target_hour is None:
            # Look ahead by 1 hour
            target_hour = (datetime.utcnow().hour + 1) % 24

        forecast = self.forecast_demand(genome, target_hour)
        tier_cfg = TIER_CONFIGS.get(genome.subscription.tier, TIER_CONFIGS["Free"])

        # Pre-allocate compute & database partitions
        required_p = forecast["required_partitions"]
        genome.resource.materialized_partitions = required_p
        genome.resource.is_preemptively_scaled = forecast["is_peak_window"]
        genome.resource.allocated_cpu_cores = tier_cfg.base_cpu_cores * (1.5 if forecast["is_peak_window"] else 1.0)
        
        genome.update_integrity()
        db_store.save_genome(genome)

        allocation_status = {
            "tenant_id": tenant_id,
            "target_hour": target_hour,
            "is_peak": forecast["is_peak_window"],
            "materialized_partitions": required_p,
            "allocated_cpu_cores": genome.resource.allocated_cpu_cores,
            "allocated_memory_mb": genome.resource.allocated_memory_mb,
            "provisioned_at": datetime.utcnow().isoformat(),
            "status": "MATERIALIZED_AHEAD_OF_DEMAND"
        }
        db_store.load_partitions[tenant_id] = allocation_status
        return allocation_status

ptlme = PredictiveTenantLoadMaterializationEngine()
