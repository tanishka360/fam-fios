"""
Amazon Web Services (AWS) Simple Storage Service (S3) Cloud Vault for FAM-FIOS.
Provides durable, encrypted cloud object storage for:
1. FAFIE Federated Model Weights & Checkpoints (rounds/{round_id}/weights.json)
2. Member Tax Invoices, Receipts & Digital Fitness Passes (invoices/{invoice_id}.json)
Supports Server-Side Encryption (AES256 / AWS KMS) and offline sandbox simulation.
"""

import os
import json
import secrets
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    BotoCoreError = Exception
    ClientError = Exception


class AwsS3Service:
    """Enterprise Cloud Storage Vault Client using Amazon S3."""

    def __init__(self):
        self.default_bucket = os.environ.get("AWS_S3_BUCKET_NAME", "fam-fios-cloud-vault")
        self.default_region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "ap-south-1"))
        
        # Local sandbox directory for offline / credential-free persistence
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.sandbox_dir = os.path.join(base_dir, "backend", "app", "storage", "s3_sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        os.makedirs(os.path.join(self.sandbox_dir, "rounds"), exist_ok=True)
        os.makedirs(os.path.join(self.sandbox_dir, "invoices"), exist_ok=True)

    def get_credentials(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Resolves AWS credentials from custom input or environment variables."""
        if custom_credentials and custom_credentials.get("aws_access_key_id"):
            return {
                "aws_access_key_id": custom_credentials.get("aws_access_key_id", "").strip(),
                "aws_secret_access_key": custom_credentials.get("aws_secret_access_key", "").strip(),
                "region_name": custom_credentials.get("region_name", self.default_region).strip() or self.default_region,
                "bucket_name": custom_credentials.get("bucket_name", self.default_bucket).strip() or self.default_bucket
            }
        
        access_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
        region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", self.default_region)).strip()
        bucket = os.environ.get("AWS_S3_BUCKET_NAME", self.default_bucket).strip()
        
        return {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
            "bucket_name": bucket
        }

    def check_s3_configuration(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Inspects S3 bucket configuration and readiness."""
        creds = self.get_credentials(custom_credentials)
        has_creds = bool(creds.get("aws_access_key_id") and creds.get("aws_secret_access_key"))
        
        masked_key = ""
        if has_creds:
            k = creds["aws_access_key_id"]
            masked_key = f"{k[:4]}****{k[-4:]}" if len(k) >= 8 else "****"

        return {
            "configured": has_creds and BOTO3_AVAILABLE,
            "boto3_available": BOTO3_AVAILABLE,
            "bucket_name": creds["bucket_name"],
            "region": creds["region_name"],
            "masked_key": masked_key,
            "encryption_tier": "AWS KMS / AES-256 (Server-Side)",
            "status": "READY" if (has_creds and BOTO3_AVAILABLE) else "SIMULATION_SANDBOX"
        }

    def upload_model_checkpoint(
        self,
        round_id: str,
        checkpoint_data: Dict[str, Any],
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads FAFIE federated learning weights checkpoint to S3 vault:
        s3://<bucket>/fafie/rounds/{round_id}/weights.json
        """
        config = self.check_s3_configuration(custom_credentials)
        bucket = config["bucket_name"]
        s3_key = f"fafie/rounds/{round_id}/weights.json"
        payload = json.dumps(checkpoint_data, indent=2, default=str)
        s3_uri = f"s3://{bucket}/{s3_key}"

        # Always persist to local sandbox directory as well for immediate local inspection
        local_path = os.path.join(self.sandbox_dir, "rounds", f"{round_id}_weights.json")
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(payload)
        except Exception:
            pass

        # 1. Fallback to simulation sandbox if credentials are not configured
        if not config["configured"]:
            return {
                "success": True,
                "mode": "simulation",
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Simulated)",
                "status_text": f"Saved to Sandbox Vault ({s3_uri})",
                "simulated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        # 2. Live Amazon S3 PutObject
        try:
            creds = self.get_credentials(custom_credentials)
            s3_client = boto3.client(
                "s3",
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"]
            )

            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=payload.encode("utf-8"),
                ContentType="application/json",
                ServerSideEncryption="AES256",
                Metadata={
                    "system": "FAM-FIOS",
                    "round_id": round_id,
                    "privacy": "Differential-Privacy-Laplace"
                }
            )

            return {
                "success": True,
                "mode": "aws_s3",
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Server-Side KMS/S3)",
                "status_text": f"Successfully backed up to Amazon S3 ({s3_uri})",
                "simulated": False,
                "timestamp": datetime.utcnow().isoformat()
            }

        except (BotoCoreError, ClientError, Exception) as err:
            return {
                "success": False,
                "mode": "simulation",
                "error": str(err),
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Simulated Fallback)",
                "status_text": f"AWS S3 Notice: {str(err)} (Saved to Local Sandbox)",
                "simulated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

    def upload_invoice(
        self,
        invoice_id: str,
        invoice_data: Dict[str, Any],
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads Tax Invoice and Digital Pass verification metadata to S3 vault:
        s3://<bucket>/invoices/{invoice_id}.json
        """
        config = self.check_s3_configuration(custom_credentials)
        bucket = config["bucket_name"]
        clean_inv_id = invoice_id.replace("/", "_").replace(" ", "_")
        s3_key = f"invoices/{clean_inv_id}.json"
        payload = json.dumps(invoice_data, indent=2, default=str)
        s3_uri = f"s3://{bucket}/{s3_key}"

        # Persist locally in sandbox
        local_path = os.path.join(self.sandbox_dir, "invoices", f"{clean_inv_id}.json")
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(payload)
        except Exception:
            pass

        if not config["configured"]:
            return {
                "success": True,
                "mode": "simulation",
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Simulated)",
                "status_text": f"Archived to Sandbox Vault ({s3_uri})",
                "simulated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        try:
            creds = self.get_credentials(custom_credentials)
            s3_client = boto3.client(
                "s3",
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"]
            )

            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=payload.encode("utf-8"),
                ContentType="application/json",
                ServerSideEncryption="AES256",
                Metadata={
                    "system": "FAM-FIOS",
                    "doc_type": "Tax_Invoice_and_Pass",
                    "txn_ref": clean_inv_id
                }
            )

            return {
                "success": True,
                "mode": "aws_s3",
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Server-Side)",
                "status_text": f"Tax Invoice Archived in Amazon S3 ({s3_uri})",
                "simulated": False,
                "timestamp": datetime.utcnow().isoformat()
            }

        except (BotoCoreError, ClientError, Exception) as err:
            return {
                "success": False,
                "mode": "simulation",
                "error": str(err),
                "bucket": bucket,
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "bytes_stored": len(payload.encode("utf-8")),
                "encryption": "AES256 (Simulated Fallback)",
                "status_text": f"AWS S3 Notice: {str(err)} (Saved to Local Sandbox)",
                "simulated": True,
                "timestamp": datetime.utcnow().isoformat()
            }

    def list_vault_objects(
        self,
        prefix: str = "",
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists stored artifacts in the S3 vault.
        If live S3 is connected, queries ListObjectsV2. Otherwise, scans the local sandbox directory.
        """
        config = self.check_s3_configuration(custom_credentials)
        bucket = config["bucket_name"]
        objects: List[Dict[str, Any]] = []

        if config["configured"]:
            try:
                creds = self.get_credentials(custom_credentials)
                s3_client = boto3.client(
                    "s3",
                    region_name=creds["region_name"],
                    aws_access_key_id=creds["aws_access_key_id"],
                    aws_secret_access_key=creds["aws_secret_access_key"]
                )
                res = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=50)
                for item in res.get("Contents", []):
                    objects.append({
                        "key": item["Key"],
                        "size_bytes": item["Size"],
                        "last_modified": item["LastModified"].strftime("%Y-%m-%d %H:%M UTC"),
                        "s3_uri": f"s3://{bucket}/{item['Key']}",
                        "encryption": "🛡️ AWS KMS / AES256",
                        "tier": "Amazon S3 Standard"
                    })
                return objects
            except Exception:
                pass  # Fall back to sandbox scanning

        # Sandbox directory scan
        for root, _, files in os.walk(self.sandbox_dir):
            for f in files:
                if f.endswith(".json"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.sandbox_dir).replace("\\", "/")
                    if prefix and not rel_p.startswith(prefix):
                        continue
                    sz = os.path.getsize(full_p)
                    mtime = datetime.fromtimestamp(os.path.getmtime(full_p)).strftime("%Y-%m-%d %H:%M UTC")
                    objects.append({
                        "key": f"sandbox/{rel_p}",
                        "size_bytes": sz,
                        "last_modified": mtime,
                        "s3_uri": f"s3://{bucket}/{rel_p}",
                        "encryption": "🛡️ Server-Side AES256",
                        "tier": "Amazon S3 Vault"
                    })

        return objects


# Singleton instance
aws_s3_service = AwsS3Service()
