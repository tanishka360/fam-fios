from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.db_models import (
    Base, TenantModel, GenomeVectorModel, UserModel, MemberRecordModel,
    EventRecordModel, IntentRecordModel, FragmentRecordModel,
    ComplianceAuditRecordModel, LoadPartitionRecordModel, FederatedRoundRecordModel
)
from app.models.genome import (
    TenantGenome, SubscriptionVector, UsageVector,
    RolePermissionVector, ResourceVector, ComplianceVector, TrustVector
)
from app.models.events import TenantEvent
from app.models.intents import IntentObject
from app.models.fragments import TenantExecutionFragment

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def _apply_sqlite_migrations():
    """Dynamically adds missing columns to SQLite tables if they do not exist."""
    try:
        with engine.connect() as conn:
            # Check users table columns
            res_user = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            existing_user_cols = {row[1] for row in res_user}
            user_cols_to_add = [
                ("phone", "VARCHAR DEFAULT ''"),
                ("city", "VARCHAR DEFAULT ''"),
                ("branch", "VARCHAR DEFAULT ''"),
                ("status", "VARCHAR DEFAULT 'Active'")
            ]
            for col_name, col_type in user_cols_to_add:
                if col_name not in existing_user_cols:
                    conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    conn.commit()

            # Check members table columns
            res_mem = conn.exec_driver_sql("PRAGMA table_info(members)").fetchall()
            existing_mem_cols = {row[1] for row in res_mem}
            mem_cols_to_add = [
                ("phone", "VARCHAR DEFAULT ''"),
                ("area", "VARCHAR DEFAULT ''"),
                ("city", "VARCHAR DEFAULT ''"),
                ("branch", "VARCHAR DEFAULT ''"),
                ("plan", "VARCHAR DEFAULT ''"),
                ("amount_paid", "FLOAT DEFAULT 0.0"),
                ("status", "VARCHAR DEFAULT 'Active'")
            ]
            for col_name, col_type in mem_cols_to_add:
                if col_name not in existing_mem_cols:
                    conn.exec_driver_sql(f"ALTER TABLE members ADD COLUMN {col_name} {col_type}")
                    conn.commit()
    except Exception as e:
        print(f"Migration error or non-sqlite engine: {e}")

def init_db():
    """Initializes the database schemas and tables."""
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()

def get_db():
    """Dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseFAMFIOSStore:
    """
    Persistent Multi-Tenant Storage Layer:
    Provides thread-safe access to persistent SQLite/PostgreSQL storage
    while maintaining strict per-tenant data scoping.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseFAMFIOSStore, cls).__new__(cls)
                cls._instance._init_cache()
        return cls._instance

    def _init_cache(self):
        init_db()
        self.global_model_weights: List[float] = [0.25, 0.45, 0.30, 0.50, 0.15]
        self.load_partitions: Dict[str, Dict[str, Any]] = {}
        self.federated_rounds: List[Dict[str, Any]] = []

    def reset(self):
        with self._lock:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            self._init_cache()

    # --- Tenant & Genome Operations ---
    def save_genome(self, genome: TenantGenome):
        with self._lock:
            genome.update_integrity()
            with SessionLocal() as db:
                tenant_record = db.query(TenantModel).filter_by(tenant_id=genome.tenant_id).first()
                if not tenant_record:
                    tenant_record = TenantModel(
                        tenant_id=genome.tenant_id,
                        gym_name=genome.gym_name,
                        tier=genome.subscription.tier,
                        generation=genome.generation,
                        integrity_hash=genome.genome_integrity_hash,
                        created_at=genome.created_at,
                        updated_at=genome.updated_at
                    )
                    db.add(tenant_record)
                else:
                    tenant_record.gym_name = genome.gym_name
                    tenant_record.tier = genome.subscription.tier
                    tenant_record.generation = genome.generation
                    tenant_record.integrity_hash = genome.genome_integrity_hash
                    tenant_record.updated_at = genome.updated_at

                vector_record = db.query(GenomeVectorModel).filter_by(tenant_id=genome.tenant_id).first()
                if not vector_record:
                    vector_record = GenomeVectorModel(
                        tenant_id=genome.tenant_id,
                        subscription_json=json.dumps(genome.subscription.model_dump()),
                        usage_json=json.dumps(genome.usage.model_dump()),
                        role_permission_json=json.dumps(genome.role_permission.model_dump()),
                        resource_json=json.dumps(genome.resource.model_dump()),
                        compliance_json=json.dumps(genome.compliance.model_dump()),
                        trust_json=json.dumps(genome.trust.model_dump())
                    )
                    db.add(vector_record)
                else:
                    vector_record.subscription_json = json.dumps(genome.subscription.model_dump())
                    vector_record.usage_json = json.dumps(genome.usage.model_dump())
                    vector_record.role_permission_json = json.dumps(genome.role_permission.model_dump())
                    vector_record.resource_json = json.dumps(genome.resource.model_dump())
                    vector_record.compliance_json = json.dumps(genome.compliance.model_dump())
                    vector_record.trust_json = json.dumps(genome.trust.model_dump())

                db.commit()

    def get_genome(self, tenant_id: str) -> Optional[TenantGenome]:
        with SessionLocal() as db:
            tenant_record = db.query(TenantModel).filter_by(tenant_id=tenant_id).first()
            if not tenant_record:
                return None
            vector_record = db.query(GenomeVectorModel).filter_by(tenant_id=tenant_id).first()
            if not vector_record:
                return None

            return TenantGenome(
                tenant_id=tenant_record.tenant_id,
                gym_name=tenant_record.gym_name,
                created_at=tenant_record.created_at,
                updated_at=tenant_record.updated_at,
                generation=tenant_record.generation,
                subscription=SubscriptionVector(**json.loads(vector_record.subscription_json)),
                usage=UsageVector(**json.loads(vector_record.usage_json)),
                role_permission=RolePermissionVector(**json.loads(vector_record.role_permission_json)),
                resource=ResourceVector(**json.loads(vector_record.resource_json)),
                compliance=ComplianceVector(**json.loads(vector_record.compliance_json)),
                trust=TrustVector(**json.loads(vector_record.trust_json)),
                genome_integrity_hash=tenant_record.integrity_hash
            )

    def list_genomes(self) -> List[TenantGenome]:
        with SessionLocal() as db:
            tenants = db.query(TenantModel).all()
            genomes = []
            for t in tenants:
                g = self.get_genome(t.tenant_id)
                if g:
                    genomes.append(g)
            return genomes

    # --- User Operations (Option B) ---
    def save_user(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        hashed_pw: str,
        role: str,
        full_name: str,
        phone: str = "",
        city: str = "",
        branch: str = "",
        status: str = "Active"
    ) -> UserModel:
        with SessionLocal() as db:
            user = UserModel(
                user_id=user_id,
                tenant_id=tenant_id,
                email=email,
                hashed_password=hashed_pw,
                role=role,
                full_name=full_name,
                phone=phone,
                city=city,
                branch=branch,
                status=status,
                created_at=datetime.utcnow().isoformat()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        with SessionLocal() as db:
            return db.query(UserModel).filter_by(email=email).first()

    def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        with SessionLocal() as db:
            return db.query(UserModel).filter_by(user_id=user_id).first()

    def list_all_users(self, tenant_id: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            query = db.query(UserModel)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            if city:
                query = query.filter_by(city=city)
            users = query.order_by(UserModel.created_at.desc()).all()
            return [
                {
                    "user_id": u.user_id,
                    "tenant_id": u.tenant_id,
                    "email": u.email,
                    "role": u.role,
                    "full_name": u.full_name,
                    "phone": getattr(u, "phone", "") or "",
                    "city": getattr(u, "city", "") or "",
                    "branch": getattr(u, "branch", "") or "",
                    "status": getattr(u, "status", "Active") or "Active",
                    "created_at": u.created_at
                }
                for u in users
            ]

    # --- Member Operations ---
    def save_member(
        self,
        member_id: str,
        tenant_id: str,
        name: str,
        email: str,
        goal: str = "hypertrophy",
        phone: str = "",
        city: str = "",
        branch: str = "",
        area: str = "",
        plan: str = "",
        amount_paid: float = 0.0,
        status: str = "Active",
        enrolled_at: Optional[str] = None
    ) -> MemberRecordModel:
        with SessionLocal() as db:
            mem = MemberRecordModel(
                member_id=member_id,
                tenant_id=tenant_id,
                name=name,
                email=email,
                goal=goal,
                phone=phone,
                city=city,
                branch=branch,
                area=area,
                plan=plan,
                amount_paid=amount_paid,
                status=status,
                enrolled_at=enrolled_at or datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            )
            db.add(mem)
            db.commit()
            db.refresh(mem)
            return mem

    def list_all_members(
        self,
        tenant_id: Optional[str] = None,
        city: Optional[str] = None,
        branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            query = db.query(MemberRecordModel)
            if tenant_id:
                query = query.filter_by(tenant_id=tenant_id)
            if city:
                query = query.filter_by(city=city)
            if branch:
                query = query.filter_by(branch=branch)
            members = query.order_by(MemberRecordModel.enrolled_at.desc()).all()
            return [
                {
                    "member_id": m.member_id,
                    "tenant_id": m.tenant_id,
                    "name": m.name,
                    "email": m.email,
                    "goal": m.goal,
                    "phone": getattr(m, "phone", "") or "",
                    "city": getattr(m, "city", "") or "",
                    "branch": getattr(m, "branch", "") or "",
                    "area": getattr(m, "area", "") or "",
                    "plan": getattr(m, "plan", "") or "",
                    "amount_paid": float(getattr(m, "amount_paid", 0.0) or 0.0),
                    "status": getattr(m, "status", "Active") or "Active",
                    "enrolled_at": m.enrolled_at
                }
                for m in members
            ]

    def find_account_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Looks up an account across UserModel and MemberRecordModel by phone, email, or user/member ID.
        Matches with normalized digits for phone numbers or case-insensitive emails.
        """
        clean_ident = identifier.strip().lower()
        digits = "".join(c for c in clean_ident if c.isdigit())
        
        with SessionLocal() as db:
            # 1. Search in UserModel
            users = db.query(UserModel).all()
            for u in users:
                u_email = (u.email or "").strip().lower()
                u_id = (u.user_id or "").strip().lower()
                u_phone = (getattr(u, "phone", "") or "").strip().lower()
                u_digits = "".join(c for c in u_phone if c.isdigit())
                
                if (clean_ident and clean_ident in (u_email, u_id)) or (digits and len(digits) >= 6 and (digits in u_digits or u_digits.endswith(digits[-10:]))):
                    return {
                        "account_type": "user",
                        "user_id": u.user_id,
                        "tenant_id": u.tenant_id,
                        "full_name": u.full_name,
                        "email": u.email,
                        "phone": getattr(u, "phone", ""),
                        "role": u.role,
                        "city": getattr(u, "city", "") or "Pune",
                        "branch": getattr(u, "branch", "") or "Main Branch"
                    }
                    
            # 2. Search in MemberRecordModel
            members = db.query(MemberRecordModel).all()
            for m in members:
                m_email = (m.email or "").strip().lower()
                m_id = (m.member_id or "").strip().lower()
                m_phone = (getattr(m, "phone", "") or "").strip().lower()
                m_digits = "".join(c for c in m_phone if c.isdigit())
                
                if (clean_ident and clean_ident in (m_email, m_id)) or (digits and len(digits) >= 6 and (digits in m_digits or m_digits.endswith(digits[-10:]))):
                    return {
                        "account_type": "member",
                        "member_id": m.member_id,
                        "tenant_id": m.tenant_id,
                        "full_name": m.name,
                        "email": m.email,
                        "phone": getattr(m, "phone", ""),
                        "role": "member",
                        "city": getattr(m, "city", "") or "Pune",
                        "branch": getattr(m, "branch", "") or getattr(m, "area", "Main Branch"),
                        "plan": getattr(m, "plan", "Standard Plan")
                    }
            return None

    # --- Events ---
    def log_event(self, event: TenantEvent):
        with SessionLocal() as db:
            evt_record = EventRecordModel(
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                event_type=event.event_type,
                role_context=event.role_context,
                timestamp=event.timestamp,
                params_json=json.dumps(event.operational_params),
                signature=event.isolation_signature
            )
            db.add(evt_record)
            db.commit()

    # --- Intents ---
    def save_intent(self, intent: IntentObject):
        with SessionLocal() as db:
            rec = IntentRecordModel(
                intent_id=intent.intent_id,
                tenant_id=intent.tenant_id,
                source_agent=intent.source_agent,
                proposed_action=intent.proposed_action,
                impact=intent.expected_operational_impact,
                priority=intent.execution_priority,
                status=intent.status,
                payload_json=json.dumps(intent.payload),
                created_at=intent.created_at
            )
            db.add(rec)
            db.commit()

    def get_intents_for_tenant(self, tenant_id: str) -> List[IntentObject]:
        with SessionLocal() as db:
            records = db.query(IntentRecordModel).filter_by(tenant_id=tenant_id).all()
            results = []
            for r in records:
                results.append(IntentObject(
                    intent_id=r.intent_id,
                    tenant_id=r.tenant_id,
                    source_agent=r.source_agent,
                    proposed_action=r.proposed_action,
                    expected_operational_impact=r.impact,
                    execution_priority=r.priority,
                    status=r.status,
                    payload=json.loads(r.payload_json),
                    created_at=r.created_at
                ))
            return results

    # --- Fragments (TEFR) ---
    def log_fragment(self, fragment: TenantExecutionFragment):
        with SessionLocal() as db:
            rec = FragmentRecordModel(
                fragment_id=fragment.fragment_id,
                tenant_id=fragment.tenant_id,
                triggering_intent_id=fragment.triggering_intent_id,
                action_type=fragment.action_type,
                pre_hash=fragment.pre_execution_state_hash,
                post_hash=fragment.post_execution_state_hash,
                duration_ms=fragment.execution_duration_ms,
                success=fragment.success,
                verdict=fragment.validation_verdict,
                timestamp=fragment.timestamp
            )
            db.add(rec)
            db.commit()

    def get_fragments_for_tenant(self, tenant_id: str) -> List[TenantExecutionFragment]:
        with SessionLocal() as db:
            records = db.query(FragmentRecordModel).filter_by(tenant_id=tenant_id).all()
            return [
                TenantExecutionFragment(
                    fragment_id=r.fragment_id,
                    tenant_id=r.tenant_id,
                    timestamp=r.timestamp,
                    triggering_intent_id=r.triggering_intent_id,
                    action_type=r.action_type,
                    pre_execution_state_hash=r.pre_hash,
                    post_execution_state_hash=r.post_hash,
                    execution_duration_ms=r.duration_ms,
                    success=r.success,
                    validation_verdict=r.verdict
                )
                for r in records
            ]

    # --- Compliance Audits ---
    def log_compliance(self, record: Dict[str, Any]):
        with SessionLocal() as db:
            rec = ComplianceAuditRecordModel(
                tenant_id=record.get("tenant_id", "system"),
                action=record.get("action", "UNKNOWN"),
                caller_role=record.get("caller_role", "UNKNOWN"),
                verdict=record.get("verdict", "UNKNOWN"),
                violations_json=json.dumps(record.get("violations", [])),
                timestamp=record.get("timestamp", datetime.utcnow().isoformat())
            )
            db.add(rec)
            db.commit()

    @property
    def compliance_audits(self) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            records = db.query(ComplianceAuditRecordModel).all()
            return [
                {
                    "id": r.id,
                    "tenant_id": r.tenant_id,
                    "action": r.action,
                    "caller_role": r.caller_role,
                    "verdict": r.verdict,
                    "violations": json.loads(r.violations_json),
                    "timestamp": r.timestamp
                }
                for r in records
            ]

db_store = DatabaseFAMFIOSStore()
