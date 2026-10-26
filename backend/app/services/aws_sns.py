"""
Amazon Web Services (AWS) Simple Notification Service (SNS) Adapter for FAM-FIOS.
Handles real transactional SMS dispatch of 6-digit verification OTPs to mobile phones.

Credentials are resolved in this order:
  1. Keys entered in the app for the current session (custom_credentials)
  2. boto3's default chain: environment variables, ~/.aws, or the EC2 instance
     role (e.g. LabInstanceProfile) — no keys need to be pasted on EC2.

The OTP is never returned for display: if SMS can't be sent, the result says so.

Optional environment variables for Indian (TRAI DLT) delivery:
  SNS_SMS_SENDER_ID, SNS_SMS_ENTITY_ID, SNS_SMS_TEMPLATE_ID
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
        self.default_region = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

    def _session(self, custom_credentials: Optional[Dict[str, str]] = None):
        """Builds a boto3 session from session-entered keys, or boto3's default credential chain."""
        if custom_credentials and custom_credentials.get("aws_access_key_id"):
            return boto3.Session(
                aws_access_key_id=custom_credentials.get("aws_access_key_id", "").strip(),
                aws_secret_access_key=custom_credentials.get("aws_secret_access_key", "").strip(),
                aws_session_token=(custom_credentials.get("aws_session_token") or "").strip() or None,
                region_name=(custom_credentials.get("region_name") or "").strip() or self.default_region
            )
        return boto3.Session(region_name=self.default_region)

    def check_sns_configuration(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Inspects whether AWS credentials are available for SMS dispatch."""
        if not BOTO3_AVAILABLE:
            return {
                "configured": False,
                "boto3_available": False,
                "region": self.default_region,
                "masked_key": "",
                "source": "",
                "status": "NOT_CONFIGURED"
            }

        session = self._session(custom_credentials)
        try:
            creds = session.get_credentials()
        except (BotoCoreError, ClientError, Exception):
            creds = None

        masked_key = ""
        source = ""
        if creds is not None:
            k = creds.access_key or ""
            masked_key = f"{k[:4]}****{k[-4:]}" if len(k) >= 8 else "****"
            source = getattr(creds, "method", "") or ""

        return {
            "configured": creds is not None,
            "boto3_available": True,
            "region": session.region_name or self.default_region,
            "masked_key": masked_key,
            "source": source,
            "status": "READY" if creds is not None else "NOT_CONFIGURED"
        }

    @staticmethod
    def _message_attributes() -> Dict[str, Dict[str, str]]:
        """Transactional SMS attributes, plus optional DLT registration values for India."""
        attrs = {
            "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"}
        }
        optional = {
            "AWS.SNS.SMS.SenderID": os.environ.get("SNS_SMS_SENDER_ID", "").strip(),
            "AWS.MM.SMS.EntityId": os.environ.get("SNS_SMS_ENTITY_ID", "").strip(),
            "AWS.MM.SMS.TemplateId": os.environ.get("SNS_SMS_TEMPLATE_ID", "").strip(),
        }
        for name, value in optional.items():
            if value:
                attrs[name] = {"DataType": "String", "StringValue": value}
        return attrs

    def send_sms_otp(
        self,
        phone_number: str,
        otp_code: str,
        custom_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches transactional SMS via Amazon SNS.
        Returns success=False (and never a displayable code) if credentials are
        missing or SNS rejects the message.
        """
        e164_phone = format_e164(phone_number)
        config = self.check_sns_configuration(custom_credentials)

        if not config["configured"]:
            return {
                "success": False,
                "mode": "not_configured",
                "error": "No AWS credentials available for Amazon SNS.",
                "message_id": None,
                "phone": e164_phone,
                "region": config["region"],
                "status_text": "SMS service is not configured (no AWS credentials or instance role).",
                "simulated": False
            }

        try:
            client = self._session(custom_credentials).client("sns", region_name=config["region"])

            message_body = (
                f"FAM-FIOS: Your login OTP is {otp_code}. "
                f"Valid for 5 minutes. Do not share it with anyone."
            )

            response = client.publish(
                PhoneNumber=e164_phone,
                Message=message_body,
                MessageAttributes=self._message_attributes()
            )

            aws_msg_id = response.get("MessageId", f"AWS-{secrets.token_hex(4)}")
            return {
                "success": True,
                "mode": "aws_sns",
                "message_id": aws_msg_id,
                "phone": e164_phone,
                "region": config["region"],
                "status_text": f"SMS accepted by Amazon SNS (MessageId: {aws_msg_id})",
                "simulated": False
            }

        except (BotoCoreError, ClientError, Exception) as err:
            return {
                "success": False,
                "mode": "aws_sns_error",
                "error": str(err),
                "message_id": None,
                "phone": e164_phone,
                "region": config["region"],
                "status_text": f"Amazon SNS rejected the SMS: {err}",
                "simulated": False
            }


# Singleton instance
aws_sns_service = AwsSnsService()
