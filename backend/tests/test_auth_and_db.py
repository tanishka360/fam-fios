import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.database import db_store, init_db
from app.engines.tige import tige
from app.api.dependencies import require_role, verify_tenant_boundary_access
from app.models.db_models import UserModel
from fastapi import HTTPException

def test_password_hashing_and_verification():
    raw_pass = "SuperSecretPassword123!"
    hashed = hash_password(raw_pass)
    
    assert hashed != raw_pass
    assert "$" in hashed
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_creation_and_decoding():
    payload = {
        "sub": "usr_test_123",
        "tenant_id": "tenant_apex",
        "role": "gym_admin",
        "email": "admin@apexfitness.com"
    }
    token = create_access_token(payload)
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "usr_test_123"
    assert decoded["tenant_id"] == "tenant_apex"
    assert decoded["role"] == "gym_admin"

def test_persistent_db_and_user_creation():
    db_store.reset()
    tige.initialize_tenant_genome("tenant_db_test", "DB Test Gym", "Free")

    # Save user to SQLite
    user = db_store.save_user(
        user_id="usr_db_001",
        tenant_id="tenant_db_test",
        email="testuser@dbtest.com",
        hashed_pw=hash_password("Pass1234!"),
        role="gym_admin",
        full_name="Database Test User"
    )
    assert user.user_id == "usr_db_001"

    # Query back from SQLite
    fetched_user = db_store.get_user_by_email("testuser@dbtest.com")
    assert fetched_user is not None
    assert fetched_user.email == "testuser@dbtest.com"
    assert fetched_user.role == "gym_admin"
    assert verify_password("Pass1234!", fetched_user.hashed_password) is True

def test_cross_tenant_isolation_boundary_enforcement():
    db_store.reset()
    user_apex = UserModel(
        user_id="usr_apex_01",
        tenant_id="tenant_apex",
        email="user@apex.com",
        hashed_password=hash_password("Pass!"),
        role="gym_admin",
        full_name="Apex Admin",
        created_at="2026-09-06T12:00:00"
    )

    # 1. Allowed: accessing own tenant
    passed_user = verify_tenant_boundary_access("tenant_apex", user_apex)
    assert passed_user.tenant_id == "tenant_apex"

    # 2. Blocked: attempting cross-tenant access to tenant_iron
    with pytest.raises(HTTPException) as exc_info:
        verify_tenant_boundary_access("tenant_iron", user_apex)
    
    assert exc_info.value.status_code == 403
    assert "Tenant isolation policy violation" in exc_info.value.detail

    # Verify ACVE logged the breach attempt in the persistent audits
    audits = db_store.compliance_audits
    assert any(a["action"] == "CROSS_TENANT_ACCESS_ATTEMPT" for a in audits)

def test_rbac_role_enforcement():
    member_user = UserModel(
        user_id="usr_mem_01",
        tenant_id="tenant_apex",
        email="mem@apex.com",
        hashed_password=hash_password("Pass!"),
        role="member",
        full_name="Member Only",
        created_at="2026-09-06T12:00:00"
    )

    admin_checker = require_role(["gym_admin"])

    with pytest.raises(HTTPException) as exc_info:
        admin_checker(member_user)

    assert exc_info.value.status_code == 403
    assert "lacks required permissions" in exc_info.value.detail
