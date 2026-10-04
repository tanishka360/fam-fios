"""
Amazon Web Services (AWS) Simple Notification Service (SNS) Adapter for FAM-FIOS.
Handles real transactional SMS dispatch of 6-digit verification OTPs to mobile phones
with high carrier priority and graceful sandbox simulation fallback.
"""

import os
import re
import secrets
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    BotoCoreError = Exception
    ClientError = Exception


def format_e164(phone: str, default_country_code: str = "+91") -> str:
    """
    Normalizes phone numbers to standard E.164 format (+[country code][number]).
    Example: '78880 85822' -> '+917888085822'
             '+91 98220-12345' -> '+919822012345'
             '09822012345' -> '+919822012345'
    """
    clean = re.sub(r"[^\d+]", "", phone.strip())
    if not clean:
        return ""
    
    # If already has leading +
    if clean.startswith("+"):
        return clean
    
    # If starts with leading zero (e.g. 098220...)
    if clean.startswith("0") and len(clean) == 11:
        clean = clean[1:]
        
    # If 10 digits without country code, assume India (+91)
    if len(clean) == 10:
        return f"{default_country_code}{clean}"
        
    # If 12 digits starting with 91 (e.g. 917888085822)
    if len(clean) == 12 and clean.startswith("91"):
        return f"+{clean}"
        
    return f"+{clean}"


class AwsSnsService:
    """Enterprise AWS SNS Client for Transactional SMS Verification."""

    def __init__(self):
        self.default_region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "ap-south-1"))

    def get_credentials(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Resolves AWS credentials from custom input or environment variables."""
        if custom_credentials and custom_credentials.get("aws_access_key_id"):
            return {
                "aws_access_key_id": custom_credentials.get("aws_access_key_id", "").strip(),
                "aws_secret_access_key": custom_credentials.get("aws_secret_access_key", "").strip(),
                "region_name": custom_credentials.get("region_name", self.default_region).strip() or self.default_region
            }
        
        access_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
        region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", self.default_region)).strip()
        
        return {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region
        }

    def check_sns_configuration(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Inspects whether active AWS credentials are ready for SMS dispatch."""
        creds = self.get_credentials(custom_credentials)
        has_creds = bool(creds.get("aws_access_key_id") and creds.get("aws_secret_access_key"))
        
        masked_key = ""
        if has_creds:
            k = creds["aws_access_key_id"]
            masked_key = f"{k[:4]}****{k[-4:]}" if len(k) >= 8 else "****"

        return {
            "configured": has_creds and BOTO3_AVAILABLE,
            "boto3_available": BOTO3_AVAILABLE,
            "region": creds.get("region_name", self.default_region),
            "masked_key": masked_key,
            "status": "READY" if (has_creds and BOTO3_AVAILABLE) else "SIMULATION_MODE"
        }

    def send_sms_otp(
        self,
        phone_number: str,
        otp_code: str,
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches transactional SMS via Amazon SNS.
        If credentials are not configured or dispatch fails, gracefully falls back to simulation.
        """
        e164_phone = format_e164(phone_number)
        config = self.check_sns_configuration(custom_credentials)
        
        # 1. Fallback to simulation if not configured
        if not config["configured"]:
            sim_ref = f"SIM-SNS-{secrets.token_hex(3).upper()}"
            return {
                "success": True,
                "mode": "simulation",
                "message_id": sim_ref,
                "phone": e164_phone,
                "region": config["region"],
                "status_text": "Sandbox Simulation Mode (Live AWS credentials not active)",
                "simulated": True
            }

        # 2. Attempt real Amazon SNS Publish
        try:
            creds = self.get_credentials(custom_credentials)
            client = boto3.client(
                "sns",
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"]
            )
            
            message_body = (
                f"FAM-FIOS Security: Your gym pass login OTP is {otp_code}. "
                f"Valid for 5 minutes. (Ref: {otp_code[:3]})"
            )
            
            response = client.publish(
                PhoneNumber=e164_phone,
                Message=message_body,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional"
                    }
                }
            )
            
            aws_msg_id = response.get("MessageId", f"AWS-{secrets.token_hex(4)}")
            return {
                "success": True,
                "mode": "aws_sns",
                "message_id": aws_msg_id,
                "phone": e164_phone,
                "region": creds["region_name"],
                "status_text": f"Live SMS Dispatched via Amazon SNS (MessageId: {aws_msg_id})",
                "simulated": False
            }

        except (BotoCoreError, ClientError, Exception) as err:
            sim_ref = f"SIM-SNS-FALLBACK-{secrets.token_hex(3).upper()}"
            return {
                "success": False,
                "mode": "simulation",
                "error": str(err),
                "message_id": sim_ref,
                "phone": e164_phone,
                "region": config["region"],
                "status_text": f"AWS SNS Notification Notice: {str(err)} (Fallback to Sandbox)",
                "simulated": True
            }


# Singleton instance
aws_sns_service = AwsSnsService()
