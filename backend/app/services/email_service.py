"""
Transactional Email Service for FAM-FIOS.
Handles real transactional Email dispatch of 6-digit verification OTPs
via standard SMTP (Gmail App Passwords, Outlook, AWS SES SMTP, or Custom SMTP servers)
with high carrier priority and graceful sandbox simulation fallback.
"""

import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional


class EmailService:
    """Enterprise Email Client for Transactional OTP and Verification Alerts."""

    def __init__(self):
        self.default_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.default_port = int(os.environ.get("SMTP_PORT", "587"))
        self.default_user = os.environ.get("SMTP_USER", "")
        self.default_password = os.environ.get("SMTP_PASSWORD", "")
        self.default_from = os.environ.get("SMTP_FROM_EMAIL", self.default_user)

    def get_credentials(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Resolves SMTP credentials from custom session input or environment variables."""
        if custom_credentials and custom_credentials.get("smtp_user"):
            return {
                "smtp_host": custom_credentials.get("smtp_host", self.default_host).strip() or self.default_host,
                "smtp_port": int(custom_credentials.get("smtp_port", self.default_port) or self.default_port),
                "smtp_user": custom_credentials.get("smtp_user", "").strip(),
                "smtp_password": custom_credentials.get("smtp_password", "").strip(),
                "from_email": custom_credentials.get("from_email", custom_credentials.get("smtp_user", "")).strip()
            }
        
        return {
            "smtp_host": self.default_host,
            "smtp_port": self.default_port,
            "smtp_user": self.default_user,
            "smtp_password": self.default_password,
            "from_email": self.default_from or self.default_user
        }

    def check_email_configuration(self, custom_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Inspects whether active SMTP credentials are ready for email dispatch."""
        creds = self.get_credentials(custom_credentials)
        has_creds = bool(creds.get("smtp_user") and creds.get("smtp_password"))
        
        masked_user = ""
        if has_creds:
            u = creds["smtp_user"]
            parts = u.split("@")
            if len(parts) == 2:
                name, domain = parts
                masked_user = f"{name[:2]}***@{domain}"
            else:
                masked_user = f"{u[:2]}***"

        return {
            "configured": has_creds,
            "smtp_host": creds.get("smtp_host"),
            "smtp_port": creds.get("smtp_port"),
            "masked_user": masked_user,
            "status": "READY" if has_creds else "SIMULATION_MODE"
        }

    def send_email_otp(
        self,
        recipient_email: str,
        otp_code: str,
        custom_credentials: Optional[Dict[str, str]] = None,
        custom_aws_credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches transactional verification OTP email via SMTP.
        If credentials are not configured or dispatch fails, gracefully falls back to simulation.
        """
        clean_email = recipient_email.strip()
        config = self.check_email_configuration(custom_credentials)

        # 1. Fallback to simulation if not configured
        if not config["configured"]:
            sim_ref = f"SIM-SES-{secrets.token_hex(3).upper()}"
            return {
                "success": True,
                "mode": "email_simulation",
                "message_id": sim_ref,
                "email": clean_email,
                "host": config["smtp_host"],
                "status_text": "Email Sandbox Simulation (Live SMTP/Gmail credentials not active)",
                "simulated": True
            }

        # 2. Attempt real SMTP dispatch
        creds = self.get_credentials(custom_credentials)
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"FAM-FIOS Security: Your Verification Code is {otp_code}"
            from_addr = creds.get("from_email") or creds.get("smtp_user")
            msg["From"] = f"FAM-FIOS Security <{from_addr}>"
            msg["To"] = clean_email

            text_body = f"""
Hello,

Your verification code for FAM-FIOS Gym Operating System is: {otp_code}

This code is valid for 5 minutes.
If you did not request this verification code, please ignore this email.

Best regards,
FAM-FIOS Security Team
"""
            html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0F172A; margin: 0; padding: 24px; color: #F8FAFC;">
  <div style="max-width: 520px; margin: 0 auto; background: #1E293B; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.3); padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
    <div style="text-align: center; margin-bottom: 24px;">
      <h2 style="color: #38BDF8; margin: 0; font-size: 24px; letter-spacing: 1px;">🏋️ FAM-FIOS</h2>
      <p style="color: #94A3B8; font-size: 13px; margin: 4px 0 0 0;">Intelligent Multi-Tenant Gym Operating System</p>
    </div>
    
    <div style="background: rgba(15, 23, 42, 0.7); border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 24px;">
      <p style="margin: 0 0 8px 0; color: #CBD5E1; font-size: 14px;">Your 6-digit login verification code:</p>
      <div style="font-size: 36px; font-weight: 800; color: #FCD34D; letter-spacing: 8px; margin: 12px 0;">{otp_code}</div>
      <p style="margin: 0; color: #94A3B8; font-size: 12px;">⏳ Valid for <b>5 minutes</b> only. Single use.</p>
    </div>

    <p style="font-size: 13px; color: #94A3B8; line-height: 1.5; margin: 0 0 16px 0;">
      Enter this code in your FAM-FIOS portal login screen to verify your identity and access your dashboard.
    </p>

    <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 16px; font-size: 11px; color: #64748B; text-align: center;">
      If you did not request this verification code, please ignore this email or contact your gym administration.
    </div>
  </div>
</body>
</html>
"""
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Connect via SMTP
            host = creds["smtp_host"]
            port = int(creds["smtp_port"])
            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(creds["smtp_user"], creds["smtp_password"])
            server.sendmail(from_addr, [clean_email], msg.as_string())
            server.quit()

            msg_id = f"SMTP-{secrets.token_hex(4).upper()}"
            return {
                "success": True,
                "mode": "smtp_live",
                "message_id": msg_id,
                "email": clean_email,
                "host": host,
                "status_text": f"Live Email Dispatched via SMTP to {clean_email}",
                "simulated": False
            }

        except Exception as err:
            sim_ref = f"SIM-SES-FALLBACK-{secrets.token_hex(3).upper()}"
            return {
                "success": False,
                "mode": "simulation",
                "error": str(err),
                "message_id": sim_ref,
                "email": clean_email,
                "host": creds.get("smtp_host", self.default_host),
                "status_text": f"SMTP Dispatch Notice: {str(err)} (Fallback to Sandbox)",
                "simulated": True
            }


# Singleton instance
email_service = EmailService()
