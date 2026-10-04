from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from app.core.security import hash_password, verify_password, create_access_token
from app.database import db_store
from app.api.dependencies import get_current_user
from app.models.db_models import UserModel
from app.models.events import TenantEvent
from app.engines.tige import tige
from app.engines.sice import sice

router = APIRouter(prefix="/auth", tags=["Authentication & Multi-Tenant Access (JWT)"])

class RegisterUserRequest(BaseModel):
    tenant_id: str
    email: str
    password: str
    full_name: str
    role: str = "member" # 'gym_admin', 'trainer', 'member'

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    role: str
    full_name: str
    created_at: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: RegisterUserRequest):
    # 1. Verify tenant exists
    genome = db_store.get_genome(req.tenant_id)
    if not genome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target tenant '{req.tenant_id}' does not exist."
        )

    # 2. Check email uniqueness
    existing = db_store.get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered."
        )

    # 3. Check role-quota constraint via SICE / TIGE
    if req.role == "member":
        sub = genome.subscription
        if sub.active_members >= sub.max_members:
            # Trigger SICE upgrade check
            sice.evaluate_subscription_convergence(req.tenant_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant '{req.tenant_id}' has reached member tier limit ({sub.active_members}/{sub.max_members}). Upgrade required."
            )

    # 4. Hash password and persist user
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(req.password)
    user = db_store.save_user(
        user_id=user_id,
        tenant_id=req.tenant_id,
        email=req.email,
        hashed_pw=hashed_pw,
        role=req.role,
        full_name=req.full_name
    )

    # 5. If member, propagate event through TIGE
    if req.role == "member":
        evt = TenantEvent(
            tenant_id=req.tenant_id,
            role_context=req.role,
            event_type="member_signup",
            operational_params={"user_id": user_id, "name": req.full_name}
        )
        tige.update_genome_from_event(evt)

    # 6. Generate JWT token
    token = create_access_token({
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "email": user.email
    })

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            created_at=user.created_at
        )
    )

@router.post("/login", response_model=AuthTokenResponse)
def login(req: LoginRequest):
    user = db_store.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "email": user.email
    })

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            created_at=user.created_at
        )
    )

@router.get("/me")
def get_current_user_profile(current_user: UserModel = Depends(get_current_user)):
    genome = db_store.get_genome(current_user.tenant_id)
    return {
        "user_id": current_user.user_id,
        "tenant_id": current_user.tenant_id,
        "gym_name": genome.gym_name if genome else "Unknown Gym",
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at,
        "subscription_tier": genome.subscription.tier if genome else "N/A"
    }
