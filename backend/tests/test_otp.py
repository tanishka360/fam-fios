import pytest
from app.core.security import generate_login_otp, verify_login_otp
from app.database import db_store, init_db

def test_otp_generation_and_success_verification():
    identifier = '+91 98220 54321'
    otp_data = generate_login_otp(identifier)
    assert len(otp_data['otp']) == 6
    assert otp_data['otp'].isdigit()
    assert otp_data['channel'] == 'SMS'
    is_valid, msg = verify_login_otp(identifier, otp_data['otp'])
    assert is_valid is True
    # Single-use check
    is_valid_again, _ = verify_login_otp(identifier, otp_data['otp'])
    assert is_valid_again is False

def test_otp_incorrect_code_rejection():
    identifier = 'user.test@gmail.com'
    otp_data = generate_login_otp(identifier)
    assert otp_data['channel'] == 'Email'
    is_valid, msg = verify_login_otp(identifier, '000000')
    assert is_valid is False

def test_find_account_by_identifier():
    import secrets
    init_db()
    test_id = f"usr_test_{secrets.token_hex(3)}"
    test_email = f"otp.{test_id}@titan.com"
    test_phone = f"+91 98231 {secrets.randbelow(89999)+10000}"
    db_store.save_user(
        user_id=test_id,
        tenant_id="tenant_titan",
        email=test_email,
        hashed_pw="hash_dummy",
        role="gym_admin",
        full_name="Titan OTP Admin",
        phone=test_phone,
        city="Pune",
        branch="Baner High Street Franchise"
    )
    admin_acc = db_store.find_account_by_identifier(test_phone)
    assert admin_acc is not None
    assert admin_acc["role"] == "gym_admin"
    assert admin_acc["full_name"] == "Titan OTP Admin"

def test_email_otp_generation_and_simulation_dispatch():
    from app.services.email_service import email_service
    test_email = "member.fit@gmail.com"
    otp_data = generate_login_otp(test_email)
    assert otp_data["channel"] == "Email"
    assert len(otp_data["otp"]) == 6
    assert otp_data["raw_identifier"] == test_email
    assert "member.fit" not in otp_data["masked_target"] or "***" in otp_data["masked_target"]
    assert otp_data["is_simulated"] is True
    assert "SIM-SES" in otp_data["aws_message_id"]

def test_email_service_configuration_inspector():
    from app.services.email_service import email_service
    status = email_service.check_email_configuration()
    assert "configured" in status
    assert "status" in status
    assert "smtp_host" in status

def test_email_service_mock_smtp_dispatch(monkeypatch):
    from app.services.email_service import email_service
    
    class MockSMTP:
        def __init__(self, host, port, timeout=10):
            self.host = host
            self.port = port
        def ehlo(self): pass
        def starttls(self): pass
        def login(self, user, password): pass
        def sendmail(self, from_addr, to_addrs, msg): pass
        def quit(self): pass

    import smtplib
    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)

    mock_creds = {
        "smtp_host": "smtp.mock.com",
        "smtp_port": 587,
        "smtp_user": "alert@mock.com",
        "smtp_password": "mockpassword123",
        "from_email": "alert@mock.com"
    }

    result = email_service.send_email_otp(
        recipient_email="athlete@gym.com",
        otp_code="789012",
        custom_credentials=mock_creds
    )
    assert result["success"] is True
    assert result["mode"] == "smtp_live"
    assert result["simulated"] is False
    assert "athlete@gym.com" in result["status_text"]

