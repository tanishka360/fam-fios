import pytest
from app.engines.tige import tige
from app.engines.ptlme import ptlme
from app.database import db_store

def test_ptlm_peak_demand_materialization():
    db_store.reset()
    g = tige.initialize_tenant_genome("tenant_load_test", "Load Test Gym", "Silver")
    g.subscription.active_members = 150
    # Simulate heavy morning peak profile
    g.usage.hourly_histogram["7"] = 50
    g.usage.hourly_histogram["8"] = 60
    db_store.save_genome(g)

    # 1. Forecast for off-peak hour (2 PM / 14:00)
    fc_offpeak = ptlme.forecast_demand(g, 14)
    assert fc_offpeak["is_peak_window"] is False

    # 2. Forecast for morning peak hour (7 AM)
    fc_peak = ptlme.forecast_demand(g, 7)
    assert fc_peak["is_peak_window"] is True
    assert fc_peak["required_partitions"] > fc_offpeak["required_partitions"]

    # 3. Materialize ahead of morning peak
    mat_status = ptlme.materialize_partitions_for_tenant("tenant_load_test", target_hour=7)
    assert mat_status["status"] == "MATERIALIZED_AHEAD_OF_DEMAND"
    assert mat_status["materialized_partitions"] == fc_peak["required_partitions"]

    updated_g = db_store.get_genome("tenant_load_test")
    assert updated_g.resource.is_preemptively_scaled is True
