from pydantic import BaseModel
from typing import Dict, Any

class PlanTierConfig(BaseModel):
    name: str
    max_members: int
    max_trainers: int
    monthly_price: float
    base_cpu_cores: float
    base_memory_mb: int
    partition_quota: int

TIER_CONFIGS: Dict[str, PlanTierConfig] = {
    "Free": PlanTierConfig(
        name="Free",
        max_members=50,
        max_trainers=2,
        monthly_price=0.0,
        base_cpu_cores=1.0,
        base_memory_mb=512,
        partition_quota=1
    ),
    "Silver": PlanTierConfig(
        name="Silver",
        max_members=250,
        max_trainers=10,
        monthly_price=99.0,
        base_cpu_cores=2.0,
        base_memory_mb=1024,
        partition_quota=3
    ),
    "Gold": PlanTierConfig(
        name="Gold",
        max_members=1000,
        max_trainers=50,
        monthly_price=299.0,
        base_cpu_cores=4.0,
        base_memory_mb=4096,
        partition_quota=8
    )
}

class SystemSettings(BaseModel):
    PROJECT_NAME: str = "FAM-FIOS Runtime"
    VERSION: str = "1.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Persistent Database Configuration (SQLite default, PostgreSQL compatible)
    DATABASE_URL: str = "sqlite:///./fam_fios.db"
    
    # JWT Authentication Parameters
    JWT_SECRET_KEY: str = "fam_fios_jwt_master_secret_key_vit_score_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # Federated Learning Parameters
    FAFIE_DIFF_PRIVACY_EPSILON: float = 1.5
    FAFIE_DIFF_PRIVACY_CLIP_NORM: float = 1.0
    FAFIE_NOISE_SCALE: float = 0.05
    FAFIE_GLOBAL_LEARNING_RATE: float = 0.1
    FAFIE_LOCAL_EPOCHS: int = 5
    
    # Load Materialization Parameters
    PTLM_LEAD_MINUTES: int = 45
    PTLM_MORNING_PEAK: tuple = (6, 9)
    PTLM_EVENING_PEAK: tuple = (17, 20)
    PTLM_CAPACITY_BUFFER: float = 0.25 # 25% safety headroom
    
    # Evolution Parameters
    TEK_EVOLUTION_THRESHOLD: int = 10 # actions per evolution cycle
    TEK_LEARNING_RATE: float = 0.05

settings = SystemSettings()
