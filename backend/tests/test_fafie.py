import pytest
import numpy as np
from app.engines.tige import tige
from app.engines.fafie.local_trainer import FafieLocalTrainer
from app.engines.fafie.aggregator import fafie_aggregator
from app.engines.fafie.plateau_detector import plateau_detector
from app.database import db_store

def test_fafie_federated_round_and_differential_privacy():
    db_store.reset()
    tige.initialize_tenant_genome("tenant_1", "Gym One", "Free")
    tige.initialize_tenant_genome("tenant_2", "Gym Two", "Silver")

    initial_weights = list(db_store.global_model_weights)

    # Local training on Tenant 1
    t1 = FafieLocalTrainer("tenant_1")
    X1 = np.random.randn(30, len(initial_weights))
    y1 = np.dot(X1, initial_weights) + 0.1
    up1 = t1.compute_local_gradient_update(initial_weights, X1, y1)

    # Local training on Tenant 2
    t2 = FafieLocalTrainer("tenant_2")
    X2 = np.random.randn(40, len(initial_weights))
    y2 = np.dot(X2, initial_weights) + 0.2
    up2 = t2.compute_local_gradient_update(initial_weights, X2, y2)

    assert "DiffPrivacy" in up1["privacy_guarantee"]
    assert len(up1["isolation_signature"]) > 0

    # Federated Aggregator combines gradients without seeing raw X1 or X2
    round_result = fafie_aggregator.run_aggregation_round([up1, up2])
    assert round_result["round_number"] == 1
    assert "tenant_1" in round_result["participating_tenants"]
    assert "tenant_2" in round_result["participating_tenants"]
    assert db_store.global_model_weights != initial_weights

def test_fafie_plateau_detection():
    db_store.reset()
    tige.initialize_tenant_genome("tenant_p", "Plateau Gym", "Free")

    # Stagnant volume sessions
    sessions = [
        {"total_volume_kg": 2000.0},
        {"total_volume_kg": 2001.0},
        {"total_volume_kg": 1999.0},
        {"total_volume_kg": 2000.5}
    ]
    analysis = plateau_detector.analyze_member_trajectory("tenant_p", "mem_007", sessions)
    assert analysis["is_plateau_detected"] is True
    assert analysis["recommended_action"] == "INCREASE_VARIETY_AND_DELOAD"

    genome = db_store.get_genome("tenant_p")
    assert genome.trust.plateau_detection_count >= 1
