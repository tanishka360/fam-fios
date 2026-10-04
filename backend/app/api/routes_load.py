from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.engines.ptlme import ptlme
from app.database import db_store

router = APIRouter(prefix="/load", tags=["Predictive Load Materialization (PTLM)"])

class MaterializeRequest(BaseModel):
    target_hour: Optional[int] = None

@router.get("/{tenant_id}/forecast")
def get_24hr_demand_forecast(tenant_id: str):
    genome = db_store.get_genome(tenant_id)
    if not genome:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    forecast_24h = []
    for h in range(24):
        f = ptlme.forecast_demand(genome, h)
        forecast_24h.append(f)

    return {
        "tenant_id": tenant_id,
        "active_members": genome.subscription.active_members,
        "peak_hour_ratio": genome.usage.peak_hour_ratio,
        "hourly_forecasts": forecast_24h
    }

@router.post("/{tenant_id}/materialize")
def materialize_partitions(tenant_id: str, req: MaterializeRequest):
    try:
        status = ptlme.materialize_partitions_for_tenant(tenant_id, req.target_hour)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/all-partitions")
def get_all_materialized_partitions():
    return db_store.load_partitions
