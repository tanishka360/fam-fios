import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import jwt
from app.core.config import settings

SECRET_KEY = settings.JWT_SECRET_KEY

def compute_tenant_boundary_hash(tenant_id: str, data_payload: str) -> str:
    """Computes a cryptographically secure isolation hash to prevent cross-tenant leakage."""
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        f"{tenant_id}:{data_payload}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def verify_tenant_boundary(tenant_id: str, data_payload: str, signature: str) -> bool:
    """Verifies that an incoming tenant operation belongs strictly to the originating tenant."""
    expected = compute_tenant_boundary_hash(tenant_id, data_payload)
    return hmac.compare_digest(expected, signature)

def hash_password(password: str) -> str:
    """Generates a secure, salted PBKDF2-HMAC-SHA256 password hash."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}${key}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its salted hash in constant time."""
    try:
        salt, key = hashed_password.split('$')
        recomputed = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(key, recomputed)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a JWT token with user_id, tenant_id, role, and expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# --- In-Memory Cryptographic OTP Store ---
_ACTIVE_OTPS: Dict[str, Dict[str, Any]] = {}

def _normalize_identifier(identifier: str) -> str:
    """Normalizes phone or email identifier for consistent dictionary lookups."""
    ident = identifier.strip().lower()
    # If phone-like, remove spaces, dashes, parentheses
    if any(c.isdigit() for c in ident) and "@" not in ident:
        ident = "".join(c for c in ident if c.isdigit() or c == "+")
    return ident

def _mask_identifier(identifier: str) -> str:
    """Creates a privacy-masked representation of phone or email."""
    ident = identifier.strip()
    if "@" in ident:
        parts = ident.split("@")
        name, domain = parts[0], parts[1]
        masked_name = name[0] + "***" + (name[-1] if len(name) > 1 else "")
        return f"{masked_name}@{domain}"
    elif any(c.isdigit() for c in ident):
        digits = "".join(c for c in ident if c.isdigit())
        if len(digits) >= 6:
            return f"+91 ******{digits[-4:]}"
        return f"******{ident[-2:]}"
    return identifier

def generate_login_otp(
    identifier: str,
    custom_aws_credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Generates a secure, 6-digit numeric OTP valid for 5 minutes and dispatches it via AWS SNS if applicable."""
    from app.services.aws_sns import aws_sns_service
    normalized = _normalize_identifier(identifier)
    otp_code = str(secrets.randbelow(900000) + 100000)
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=5)
    
    channel = "Email" if "@" in normalized else "SMS"
    masked = _mask_identifier(identifier)
    
    dispatch_info: Dict[str, Any] = {}
    if channel == "SMS":
        # Dispatch via AWS SNS (or fallback to simulation)
        dispatch_info = aws_sns_service.send_sms_otp(
            phone_number=identifier,
            otp_code=otp_code,
            custom_credentials=custom_aws_credentials
        )
    else:
        dispatch_info = {
            "success": True,
            "mode": "email_simulation",
            "message_id": f"SIM-SES-{secrets.token_hex(3).upper()}",
            "status_text": "Email OTP Simulation Channel (AWS SES Sandbox)",
            "simulated": True,
            "region": "ap-south-1"
        }

    otp_record = {
        "otp": otp_code,
        "identifier": normalized,
        "raw_identifier": identifier.strip(),
        "channel": channel,
        "masked_target": masked,
        "created_at": now,
        "expires_at": expires_at,
        "dispatch_mode": dispatch_info.get("mode", "simulation"),
        "aws_message_id": dispatch_info.get("message_id"),
        "aws_status_text": dispatch_info.get("status_text"),
        "is_simulated": dispatch_info.get("simulated", True),
        "region": dispatch_info.get("region", "ap-south-1")
    }
    _ACTIVE_OTPS[normalized] = otp_record
    return otp_record

def verify_login_otp(identifier: str, input_otp: str) -> Tuple[bool, str]:
    """
    Verifies the OTP against the stored record.
    Returns (is_valid, message).
    """
    from typing import Tuple
    normalized = _normalize_identifier(identifier)
    clean_otp = input_otp.strip()
    
    if normalized not in _ACTIVE_OTPS:
        return False, "No active OTP found for this identifier. Please request a new OTP."
    
    record = _ACTIVE_OTPS[normalized]
    if datetime.utcnow() > record["expires_at"]:
        del _ACTIVE_OTPS[normalized]
        return False, "OTP has expired. Please request a fresh OTP."
    
    # Constant-time comparison
    if not hmac.compare_digest(record["otp"], clean_otp):
        return False, "Incorrect OTP code. Please check and re-enter."
    
    # Single-use consumption
    del _ACTIVE_OTPS[normalized]
    return True, "OTP verified successfully!"

