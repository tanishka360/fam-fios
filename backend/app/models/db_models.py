from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TenantModel(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, index=True)
    gym_name = Column(String, nullable=False)
    tier = Column(String, default="Free")
    generation = Column(Integer, default=1)
    integrity_hash = Column(String, default="")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

class GenomeVectorModel(Base):
    __tablename__ = "genome_vectors"

    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), primary_key=True, index=True)
    subscription_json = Column(Text, nullable=False)
    usage_json = Column(Text, nullable=False)
    role_permission_json = Column(Text, nullable=False)
    resource_json = Column(Text, nullable=False)
    compliance_json = Column(Text, nullable=False)
    trust_json = Column(Text, nullable=False)

class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'gym_admin', 'trainer', 'member'
    full_name = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    phone = Column(String, default="")
    city = Column(String, default="")
    branch = Column(String, default="")
    status = Column(String, default="Active")

class MemberRecordModel(Base):
    __tablename__ = "members"

    member_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    goal = Column(String, default="hypertrophy")
    phone = Column(String, default="")
    city = Column(String, default="")
    branch = Column(String, default="")
    area = Column(String, default="")
    plan = Column(String, default="")
    amount_paid = Column(Float, default=0.0)
    enrolled_at = Column(String, nullable=False)
    status = Column(String, default="Active")

class EventRecordModel(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    role_context = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    params_json = Column(Text, default="{}")
    signature = Column(String, nullable=True)

class IntentRecordModel(Base):
    __tablename__ = "intents"

    intent_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    source_agent = Column(String, nullable=False)
    proposed_action = Column(String, nullable=False)
    impact = Column(Text, default="")
    priority = Column(Integer, default=5)
    status = Column(String, default="PENDING")
    payload_json = Column(Text, default="{}")
    created_at = Column(String, nullable=False)

class FragmentRecordModel(Base):
    __tablename__ = "execution_fragments"

    fragment_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    triggering_intent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    pre_hash = Column(String, nullable=False)
    post_hash = Column(String, nullable=False)
    duration_ms = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    verdict = Column(String, default="APPROVED")
    timestamp = Column(String, nullable=False)

class ComplianceAuditRecordModel(Base):
    __tablename__ = "compliance_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    caller_role = Column(String, nullable=False)
    verdict = Column(String, nullable=False)
    violations_json = Column(Text, default="[]")
    timestamp = Column(String, nullable=False)

class LoadPartitionRecordModel(Base):
    __tablename__ = "load_partitions"

    tenant_id = Column(String, primary_key=True, index=True)
    target_hour = Column(Integer, default=0)
    materialized_partitions = Column(Integer, default=1)
    allocated_cpu = Column(Float, default=1.0)
    is_peak = Column(Boolean, default=False)
    status = Column(String, default="INITIALIZED")
    provisioned_at = Column(String, nullable=False)

class FederatedRoundRecordModel(Base):
    __tablename__ = "federated_rounds"

    round_number = Column(Integer, primary_key=True)
    participating_tenants_json = Column(Text, nullable=False)
    global_weights_json = Column(Text, nullable=False)
    average_loss = Column(Float, default=0.0)
    privacy_guarantee = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
