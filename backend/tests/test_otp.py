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
