from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
from app.engines.fafie.local_trainer import FafieLocalTrainer
from app.engines.fafie.aggregator import fafie_aggregator
from app.engines.fafie.plateau_detector import plateau_detector
from app.database import db_store

router = APIRouter(prefix="/federated", tags=["Federated Intelligence (FAFIE)"])

class TriggerRoundRequest(BaseModel):
    num_samples_per_tenant: int = 50

class MemberPlateauRequest(BaseModel):
    member_id: str
    sessions: List[Dict[str, Any]]

@router.post("/round")
def run_federated_round(req: TriggerRoundRequest):
    genomes = db_store.list_genomes()
    if not genomes:
        raise HTTPException(status_code=400, detail="No registered tenants found.")

    tenant_updates = []
    current_weights = db_store.global_model_weights

    # Each tenant calculates gradients LOCALLY on its own isolated data
    for genome in genomes:
        trainer = FafieLocalTrainer(genome.tenant_id)
        # Generate synthetic tenant-specific training batch (representing attendance, volume, recovery)
        np.random.seed(int(genome.tenant_id.replace("tenant_", "").replace("gym_", "") or "1") * 42)
        X = np.random.randn(req.num_samples_per_tenant, len(current_weights))
        # Ground truth local relation
        y = np.dot(X, current_weights) + np.random.normal(0, 0.1, size=req.num_samples_per_tenant)

        update = trainer.compute_local_gradient_update(current_weights, X, y)
        tenant_updates.append(update)

    # Central aggregator aggregates updates without ever viewing raw data
    round_result = fafie_aggregator.run_aggregation_round(tenant_updates)
    return round_result

@router.get("/status")
def get_federated_status():
    return {
        "current_global_weights": db_store.global_model_weights,
        "total_rounds_completed": len(db_store.federated_rounds),
        "round_history": db_store.federated_rounds
    }

@router.post("/{tenant_id}/plateau-check")
def check_member_plateau(tenant_id: str, req: MemberPlateauRequest):
    analysis = plateau_detector.analyze_member_trajectory(tenant_id, req.member_id, req.sessions)
    return analysis
