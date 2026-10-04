from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime
from app.core.config import settings
from app.core.security import decode_access_token
from app.database import db_store
from app.models.db_models import UserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserModel:
    """Extracts, verifies, and decodes the JWT bearer token, fetching the user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or corrupted token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identity.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db_store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_role(allowed_roles: List[str]):
    """Enforces Role-Based Access Control (RBAC) on the endpoint."""
    def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in allowed_roles:
            # Log ACVE RBAC violation
            db_store.log_compliance({
                "tenant_id": current_user.tenant_id,
                "action": "RBAC_CHECK",
                "caller_role": current_user.role,
                "verdict": "REJECTED_RBAC_VIOLATION",
                "violations": [f"Role '{current_user.role}' not permitted. Required: {allowed_roles}"],
                "timestamp": datetime.utcnow().isoformat()
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{current_user.role}' lacks required permissions ({allowed_roles})."
            )
        return current_user
    return role_checker

def verify_tenant_boundary_access(target_tenant_id: str, current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Enforces strict Multi-Tenant Isolation:
    Guarantees that a user belonging to tenant A cannot view or mutate tenant B's resources.
    """
    if current_user.tenant_id != target_tenant_id:
        # Log critical ACVE cross-tenant security breach attempt
        db_store.log_compliance({
            "tenant_id": target_tenant_id,
            "action": "CROSS_TENANT_ACCESS_ATTEMPT",
            "caller_role": current_user.role,
            "verdict": "REJECTED_ISOLATION_BREACH",
            "violations": [f"User '{current_user.email}' from tenant '{current_user.tenant_id}' attempted access to tenant '{target_tenant_id}'."],
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant isolation policy violation: You do not have permission to access resources in tenant '{target_tenant_id}'."
        )
    return current_user
