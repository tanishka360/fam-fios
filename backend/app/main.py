import sys
import os

# Ensure backend directory is always in sys.path regardless of execution root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import hash_password
from app.api.routes_auth import router as auth_router
from app.api.routes_tenants import router as tenants_router
from app.api.routes_gym import router as gym_router
from app.api.routes_federated import router as federated_router
from app.api.routes_load import router as load_router
from app.api.routes_compliance import router as compliance_router
from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.database import db_store, init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Federated Adaptive Multi-Tenant Fitness Infrastructure Operating System (FAM-FIOS) with Persistent SQLite & JWT Auth"
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(tenants_router, prefix=settings.API_V1_PREFIX)
app.include_router(gym_router, prefix=settings.API_V1_PREFIX)
app.include_router(federated_router, prefix=settings.API_V1_PREFIX)
app.include_router(load_router, prefix=settings.API_V1_PREFIX)
app.include_router(compliance_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
def startup_db_and_seed():
    """Initializes persistent database and seeds default tenants and users."""
    init_db()

    if not db_store.get_genome("tenant_apex"):
        # Tenant 1: Apex Fitness (Free tier, near limits)
        g1 = tige.initialize_tenant_genome("tenant_apex", "Apex Elite Fitness", "Free")
        g1.subscription.active_members = 43 # 43/50 - near breach threshold for SICE
        g1.subscription.member_growth_velocity = 1.2
        g1.usage.hourly_histogram["7"] = 28
        g1.usage.hourly_histogram["8"] = 35
        g1.usage.hourly_histogram["18"] = 42
        g1.usage.hourly_histogram["19"] = 38
        g1.usage.peak_hour_ratio = 0.68
        g1.update_integrity()
        db_store.save_genome(g1)
        dtdfe.construct_fabric(g1)

        # Seed Apex Users
        db_store.save_user(
            user_id="usr_apex_admin",
            tenant_id="tenant_apex",
            email="admin@apexfitness.com",
            hashed_pw=hash_password("ApexAdmin123!"),
            role="gym_admin",
            full_name="Apex Administrator",
            phone="+91 98233 30001",
            city="Pune",
            branch="Camp / MG Road Branch"
        )
        db_store.save_user(
            user_id="usr_apex_member",
            tenant_id="tenant_apex",
            email="member@apexfitness.com",
            hashed_pw=hash_password("ApexMember123!"),
            role="member",
            full_name="Sarah Jenkins",
            phone="+91 98233 30002",
            city="Pune",
            branch="Kalyani Nagar Branch"
        )

        # Tenant 2: IronCore Club (Silver tier)
        g2 = tige.initialize_tenant_genome("tenant_iron", "IronCore Athletic Club", "Silver")
        g2.subscription.active_members = 145
        g2.subscription.active_trainers = 6
        g2.subscription.member_growth_velocity = 2.4
        g2.usage.hourly_histogram["6"] = 55
        g2.usage.hourly_histogram["7"] = 62
        g2.usage.hourly_histogram["17"] = 70
        g2.usage.hourly_histogram["18"] = 75
        g2.usage.peak_hour_ratio = 0.61
        g2.update_integrity()
        db_store.save_genome(g2)
        dtdfe.construct_fabric(g2)

        # Seed IronCore Users
        db_store.save_user(
            user_id="usr_iron_admin",
            tenant_id="tenant_iron",
            email="admin@ironcore.com",
            hashed_pw=hash_password("IronAdmin123!"),
            role="gym_admin",
            full_name="IronCore Manager",
            phone="+91 98232 20001",
            city="Pune",
            branch="Wakad Franchise"
        )
        db_store.save_user(
            user_id="usr_iron_trainer",
            tenant_id="tenant_iron",
            email="trainer@ironcore.com",
            hashed_pw=hash_password("IronTrainer123!"),
            role="trainer",
            full_name="Coach Alex",
            phone="+91 98232 20002",
            city="Pune",
            branch="Senapati Bapat Road Franchise"
        )

        # Tenant 3: Titan Network (Gold tier enterprise)
        g3 = tige.initialize_tenant_genome("tenant_titan", "Titan Fitness Network", "Gold")
        g3.subscription.active_members = 680
        g3.subscription.active_trainers = 28
        g3.subscription.member_growth_velocity = 5.0
        g3.update_integrity()
        db_store.save_genome(g3)
        dtdfe.construct_fabric(g3)

        # Seed Titan User
        db_store.save_user(
            user_id="usr_titan_admin",
            tenant_id="tenant_titan",
            email="admin@titan.com",
            hashed_pw=hash_password("TitanAdmin123!"),
            role="gym_admin",
            full_name="Titan Executive Admin",
            phone="+91 98231 10001",
            city="Pune",
            branch="Baner High Street Franchise"
        )

        # Seed Multi-Franchise City Members
        sample_members = [
            ("MEM-2026-001", "tenant_titan", "Rohit Deshmukh", "rohit.deshmukh@gmail.com", "+91 98220 11001", "Pune", "Kothrud (Paud Road) Franchise", "Kothrud", "3 Months Quarterly", 4482.82),
            ("MEM-2026-002", "tenant_titan", "Ananya Sharma", "ananya.sharma@gmail.com", "+91 98220 11002", "Pune", "Viman Nagar Franchise", "Viman Nagar", "12 Months VIP", 14158.82),
            ("MEM-2026-003", "tenant_titan", "Vikram Patil", "vikram.patil@gmail.com", "+91 98220 11003", "Pune", "Hinjewadi Phase 1 (IT Hub) Franchise", "Hinjewadi", "1 Month Standard", 1768.82),
            ("MEM-2026-004", "tenant_titan", "Priya Kulkarni", "priya.kulkarni@gmail.com", "+91 98220 11004", "Pune", "Koregaon Park VIP Franchise", "Koregaon Park", "12 Months VIP", 14158.82),
            ("MEM-2026-005", "tenant_titan", "Aditya Joshi", "aditya.joshi@gmail.com", "+91 98220 11005", "Pune", "Baner High Street Franchise", "Baner", "3 Months Quarterly", 4482.82),
            ("MEM-2026-006", "tenant_titan", "Arjun Mehta", "arjun.mehta@gmail.com", "+91 80 9811 0001", "Bengaluru", "Indiranagar 100ft Road Franchise", "Indiranagar", "12 Months VIP", 14158.82),
            ("MEM-2026-007", "tenant_titan", "Neha Kapoor", "neha.kapoor@gmail.com", "+91 22 9822 0002", "Mumbai", "Bandra West Linking Road Franchise", "Bandra West", "3 Months Quarterly", 4482.82),
            ("MEM-2026-008", "tenant_iron", "Kabir Sen", "kabir.sen@gmail.com", "+91 98232 20111", "Pune", "Wakad Franchise", "Wakad", "1 Month Standard", 1768.82),
            ("MEM-2026-009", "tenant_apex", "Sarah Jenkins", "member@apexfitness.com", "+91 98233 30002", "Pune", "Kalyani Nagar Branch", "Kalyani Nagar", "1 Month Standard", 1768.82),
        ]
        for mid, tid, name, email, phone, city, branch, area, plan, amount in sample_members:
            db_store.save_member(
                member_id=mid,
                tenant_id=tid,
                name=name,
                email=email,
                goal="Hypertrophy (Muscle Gain & Bodybuilding)",
                phone=phone,
                city=city,
                branch=branch,
                area=area,
                plan=plan,
                amount_paid=amount,
                status="Active"
            )
            # Create user account for login
            if not db_store.get_user_by_email(email):
                db_store.save_user(
                    user_id=f"usr_{mid.lower()}",
                    tenant_id=tid,
                    email=email,
                    hashed_pw=hash_password("MemberPass123!"),
                    role="member",
                    full_name=name,
                    phone=phone,
                    city=city,
                    branch=branch,
                    status="Active"
                )

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "Persistent SQLite (SQLAlchemy)",
        "security": "JWT Bearer Authentication & Multi-Tenant Boundary Enforcement",
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "modules": [
            "Tenant Data Acquisition Layer",
            "Tenant Isolation Genome Engine (TIGE)",
            "Dynamic Tenant Dependency Fabric Engine (DTDFE)",
            "Specialized Autonomous Fitness Agents",
            "Subscription Intent Convergence Engine (SICE)",
            "Federated Adaptive Fitness Intelligence Engine (FAFIE)",
            "Predictive Tenant Load Materialization Engine (PTLME)",
            "Autonomous Compliance Verification Engine (ACVE)",
            "Tenant Execution Fragment Repository (TEFR)",
            "Tenant Evolution Kernel (TEK)"
        ]
    }
