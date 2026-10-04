import os
import json
import pytest
from unittest.mock import MagicMock, patch
from app.services.aws_s3 import aws_s3_service
from app.engines.fafie.aggregator import fafie_aggregator
from app.core.security import compute_tenant_boundary_hash
from app.database import db_store

def test_s3_configuration_inspector():
    config = aws_s3_service.check_s3_configuration()
    assert "bucket_name" in config
    assert config["bucket_name"] == "fam-fios-cloud-vault"
    assert config["boto3_available"] is True
    assert "encryption_tier" in config
    assert "AES-256" in config["encryption_tier"]

def test_upload_model_checkpoint_sandbox():
    round_id = "test_round_999"
    dummy_data = {
        "round_number": 999,
        "weights": [0.12, 0.45, -0.22, 0.89],
        "algorithm": "FedAvg_DP"
    }
    res = aws_s3_service.upload_model_checkpoint(round_id, dummy_data, custom_credentials=None)
    assert res["success"] is True
    assert res["mode"] == "simulation"
    assert "s3://fam-fios-cloud-vault/fafie/rounds/test_round_999/weights.json" == res["s3_uri"]
    assert res["bytes_stored"] > 0
    assert res["simulated"] is True
    
    # Check that file exists in local sandbox directory
    local_file = os.path.join(aws_s3_service.sandbox_dir, "rounds", f"{round_id}_weights.json")
    assert os.path.exists(local_file)
    with open(local_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert loaded["round_number"] == 999

def test_upload_invoice_sandbox():
    inv_id = "TXN_2026_TEST_01"
    inv_data = {
        "txn_id": inv_id,
        "member_name": "Tanishka Shah",
        "gym": "Titan Fitness Network",
        "amount_inr": 2999.0
    }
    res = aws_s3_service.upload_invoice(inv_id, inv_data, custom_credentials=None)
    assert res["success"] is True
    assert "s3://fam-fios-cloud-vault/invoices/TXN_2026_TEST_01.json" == res["s3_uri"]
    assert res["bytes_stored"] > 0
    assert res["simulated"] is True

def test_upload_with_mocked_boto3_s3():
    fake_creds = {
        "aws_access_key_id": "AKIA_FAKE_S3_KEY_123",
        "aws_secret_access_key": "SECRET_FAKE_S3_XYZ",
        "region_name": "ap-south-1",
        "bucket_name": "production-fitness-vault"
    }

    mock_s3_client = MagicMock()
    mock_s3_client.put_object.return_value = {"ETag": '"abc123etag"'}

    with patch("boto3.client", return_value=mock_s3_client) as mock_boto:
        res = aws_s3_service.upload_model_checkpoint(
            round_id="round_live_01",
            checkpoint_data={"weights": [1.0, 2.0]},
            custom_credentials=fake_creds
        )

        assert res["success"] is True
        assert res["mode"] == "aws_s3"
        assert res["s3_uri"] == "s3://production-fitness-vault/fafie/rounds/round_live_01/weights.json"
        assert res["simulated"] is False

        # Verify put_object arguments
        mock_s3_client.put_object.assert_called_once()
        kwargs = mock_s3_client.put_object.call_args[1]
        assert kwargs["Bucket"] == "production-fitness-vault"
        assert kwargs["Key"] == "fafie/rounds/round_live_01/weights.json"
        assert kwargs["ServerSideEncryption"] == "AES256"

def test_list_vault_objects():
    objects = aws_s3_service.list_vault_objects()
    assert isinstance(objects, list)
    assert len(objects) >= 1
    sample = objects[0]
    assert "s3_uri" in sample
    assert "key" in sample
    assert "size_bytes" in sample

def test_fafie_aggregator_backs_up_to_s3():
    # Construct a valid tenant update with boundary hash matching global model weight dimensions
    num_w = len(db_store.global_model_weights)
    grad = [0.01] * num_w
    grad_str = ",".join(f"{x:.6f}" for x in grad)
    sig = compute_tenant_boundary_hash("tenant_apex", grad_str)
    
    update = {
        "tenant_id": "tenant_apex",
        "gradient": grad,
        "num_samples": 50,
        "isolation_signature": sig,
        "loss": 0.35
    }
    
    round_info = fafie_aggregator.run_aggregation_round([update])
    assert "s3_uri" in round_info
    assert round_info["s3_uri"].startswith("s3://")
    assert "weights.json" in round_info["s3_uri"]
    assert "s3_status" in round_info
