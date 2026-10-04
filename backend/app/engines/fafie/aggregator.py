import numpy as np
from typing import List, Dict, Any
from app.core.config import settings
from app.core.security import verify_tenant_boundary
from app.database import db_store

class FafieFederatedAggregator:
    """
    Central Privacy-Preserving Federated Aggregator:
    Collects encrypted, differentially private gradient updates from all tenants.
    Never observes raw gym attendance, biometrics, or member data.
    Aggregates updates via weighted Federated Averaging (FedAvg).
    """

    def run_aggregation_round(self, tenant_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not tenant_updates:
            return {"status": "NO_UPDATES", "global_weights": db_store.global_model_weights}

        current_weights = np.array(db_store.global_model_weights)
        total_samples = 0
        weighted_grad_sum = np.zeros_like(current_weights)
        valid_tenants = []
        round_losses = []

        for update in tenant_updates:
            tenant_id = update["tenant_id"]
            grad = np.array(update["gradient"])
            n_k = update["num_samples"]
            sig = update["isolation_signature"]
            grad_str = ",".join(f"{x:.6f}" for x in update["gradient"])

            # Verify cryptographic isolation boundary
            if not verify_tenant_boundary(tenant_id, grad_str, sig):
                continue # Discard spoofed or cross-tenant poisoned update

            genome = db_store.get_genome(tenant_id)
            trust_weight = genome.trust.federated_contribution_weight if genome else 1.0

            effective_weight = n_k * trust_weight
            weighted_grad_sum += effective_weight * grad
            total_samples += effective_weight
            valid_tenants.append(tenant_id)
            round_losses.append(update.get("loss", 0.0))

        if total_samples > 0:
            avg_grad = weighted_grad_sum / total_samples
            updated_weights = current_weights - (settings.FAFIE_GLOBAL_LEARNING_RATE * avg_grad)
            db_store.global_model_weights = updated_weights.tolist()

        avg_loss = float(np.mean(round_losses)) if round_losses else 0.0
        round_num = len(db_store.federated_rounds) + 1
        round_info = {
            "round_number": round_num,
            "participating_tenants": valid_tenants,
            "global_weights": [round(w, 4) for w in db_store.global_model_weights],
            "average_loss": round(avg_loss, 4),
            "privacy_guarantee": f"Epsilon={settings.FAFIE_DIFF_PRIVACY_EPSILON}, Zero Raw Data Shared"
        }

        # Backup round weights to Amazon S3 Vault with server-side encryption
        try:
            from app.services.aws_s3 import aws_s3_service
            s3_res = aws_s3_service.upload_model_checkpoint(
                round_id=f"round_{round_num:03d}",
                checkpoint_data=round_info
            )
            round_info["s3_uri"] = s3_res.get("s3_uri")
            round_info["s3_status"] = s3_res.get("status_text")
            round_info["encryption"] = s3_res.get("encryption", "AES256")
        except Exception as e:
            round_info["s3_uri"] = f"s3://fam-fios-cloud-vault/fafie/rounds/round_{round_num:03d}/weights.json"
            round_info["s3_status"] = f"S3 Offline: {str(e)}"
            round_info["encryption"] = "Local"

        db_store.federated_rounds.append(round_info)
        return round_info

fafie_aggregator = FafieFederatedAggregator()
