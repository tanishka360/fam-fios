# FAM-FIOS: Federated Adaptive Multi-Tenant Fitness Infrastructure Operating System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/tests-24%2F24%20passing-brightgreen.svg)]()
[![Patent](https://img.shields.io/badge/Invention%20Disclosure-24BIT0370--24BIT0390--IDF--01-orange.svg)]()

**FAM-FIOS** is an autonomous, privacy-preserving, AI-driven multi-tenant operating system designed for fitness facilities, franchise networks, and enterprise gym chains. Developed based on Invention Disclosure **24BIT0370-24BIT0390-IDF-01** (VIT SCORE), the platform coordinates tenant isolation, preemptive capacity scaling, federated machine learning, cryptographic verification, and end-to-end member enrollment with zero-password OTP authentication.

---

## 🚀 Key System Portals & Features

The complete interactive operating system is delivered via **Streamlit** on http://localhost:8501, featuring 6 dedicated operational portals:

### 1. 🔐 Zero-Password OTP Authentication Portal
- **Passwordless Mobile & Email Login**: Members, trainers, and gym administrators authenticate without passwords using their registered Mobile Number (e.g., +91 78880 85822) or Email.
- **Cryptographic OTP Generation**: 6-digit numeric OTPs generated via CSPRNG (secrets.randbelow) and verified using constant-time HMAC digest comparisons (hmac.compare_digest) to eliminate side-channel timing attacks.
- **Realistic SMS Push Alert Card**: Displays an interactive mobile push alert card simulating carrier dispatch via Twilio / Jio SMS Gateway with reference tracking and a 5-minute expiry timer.
- **1-Click Auto-Fill OTP**: Instant test fill button (⚡ 1-Click Auto-Fill OTP) alongside quick demo personas (**Tanishka Shah**, **Sarah Jenkins**, **Titan Executive Admin**, **Coach Alex**).
- **Role-Based Dynamic Redirection**:
  - **Members** ➔ Seamlessly routed to **Member Fitness Dashboard** with their personalized pass and attendance records.
  - **Admins** ➔ Routed to **Gym Owner Command Center** with full facility controls unlocked.
- **Persistent Sidebar Session Widget**: Real-time authentication status badge in the sidebar showing active user avatar, role badge (🟢 Member or 🏢 Gym Admin), contact info, home branch, and a 1-click **🚪 Log Out** button.

---

### 2. 📝 Member Registration & Multi-Stage Payment Gateway
- **Hierarchical City & Franchise Branch Architecture**:
  - **City-First Selection**: Prospective members select their city (**Pune**, **Bengaluru**, **Mumbai**, **Delhi NCR**, **Hyderabad**).
  - **Multi-Franchise Chains (e.g. Pune)**: Choose from 5 distinct franchise branches for the same brand:
    1. Baner High Street Franchise (Platinum Square, Baner)
    2. Kothrud (Paud Road) Franchise (City Pride Complex, Paud Road)
    3. Viman Nagar Franchise (Behind Phoenix Marketcity)
    4. Hinjewadi Phase 1 (IT Hub) Franchise (Rajiv Gandhi Infotech Park)
    5. Koregaon Park VIP Franchise (Lane 7, North Main Road)
  - **Live Facility Information Card**: Real-time address, contact number, operating hours, amenities, and available membership slots.
- **Member Profile & Plan Selection**: Captures name, phone, email, age, gender, fitness goals, and membership duration (1 Month Standard, 3 Months Quarterly, 12 Months VIP) with itemized 18% GST calculation.
- **Dedicated Multi-Screen Payment Gateway**:
  - **📱 UPI Gateway**: Direct app push intents (**Google Pay**, **PhonePe**, **Paytm**, **CRED**, **BHIM**), high-resolution UPI QR code (pay.fitness.{tenant_id}@icici), and manual VPA collect request.
  - **💳 Card Gateway & 3D Secure OTP**: Credit/debit card form transitioning to an authentic **Bank 3D Secure OTP Verification Screen** (demo OTP: 742910).
  - **🏛️ Net Banking Gateway**: Instant authorization across major banks (SBI, HDFC, ICICI, Axis, Kotak, PNB).
  - **⚡ 1-Click Fast Approval**: Quick-pass demo approval.
- **Tax Invoice & Digital Pass**: Itemized Tax Invoice (TXN-2026-XXXX), Bank RRN, and Official Digital Fitness Pass with security barcode.
- **Connected Post-Payment Routing**: Immediate navigation buttons to **👉 Go to My Member Fitness Dashboard**, **👉 Open Gym Owner Console**, and **👉 Inspect Central Database**.

---

### 3. 🏢 Gym Owner / Admin Command Center
- **Dynamic Capacity Tracking**: Real-time telemetry monitoring member counts vs. subscription tier limits (Free, Silver, Gold).
- **Live Member Roster**: Newly enrolled members appear at the top of the roster immediately upon payment completion.
- **Preemptive SICE Synthesis**: Automated generation of fair prorated tier upgrade orders before facility capacity breaches.
- **Peak Load Prediction (PTLME)**: Hourly attendance histograms predicting morning (6–9 AM) and evening (5–8 PM) rushes, spinning up server headroom 45 minutes in advance.
- **Tenant Isolation Genome (TIGE)**: Evolving tenant generation state, resource utilization, and health score.

---

### 4. 🗄️ Central Users & Members Database Explorer
- **Relational SQLite Database Viewer**: Inspects live tables (`users` and `members`) stored in `fam_fios.db`.
- **User Accounts (`users`)**: Manages PBKDF2 salted credentials, roles (`gym_admin`, `trainer`, `member`), phone numbers, cities, and branches.
- **Gym Members (members)**: Tracks member IDs, membership durations, base fees, GST, total amounts paid (₹), and enrollment timestamps.
- **Live Search & Filter**: Real-time filtering by City, Franchise Branch, and Account Role.
- **One-Click CSV Export**: Downloadable datasets via Export Users CSV and Export Members CSV.
- **Franchise Intelligence Analytics**:
  - Signups by City distribution chart.
  - Pune 5-Franchise breakdown chart (Baner, Kothrud, Viman Nagar, Hinjewadi, Koregaon Park).
  - Revenue contribution table by gym network.

---

### 5. 🏋️ Member Fitness Companion
- **Digital Gym Pass & QR Check-In**: Instant barcode check-in triggering attendance agent event logging.
- **Interactive Workout Logger**: Logs exercise sets, reps, load (kg), and RPE ratings.
- **FAFIE Plateau Detector**: Flags performance stagnations and generates privacy-preserving adaptive suggestions.
- **AI Workout & Meal Guide**: Dynamic fitness plans tailored to member goals (Hypertrophy, Fat Loss, Powerlifting, Conditioning).

---

### 6. 🔬 Patent & Architecture Deep-Dive
- Visual interactive breakdown of the 10 patent-pending engines from Invention Disclosure 24BIT0370-24BIT0390-IDF-01.
- Interactive simulation of cross-tenant unauthorized intrusion attempts and ACVE security firewall interception.

---

## 🧠 Core Architectural Modules (Invention Disclosure)

| Engine | Name | Primary Function |
| :--- | :--- | :--- |
| **TIGE** | Tenant Isolation Genome Engine | Models each gym as an executable digital object with evolving Subscription, Usage, RBAC, Resource, Compliance, and Trust vectors. |
| **DTDFE** | Dynamic Tenant Dependency Fabric Engine | Dynamic graph modeling tenant-role-resource dependencies with adaptive enforcement weights. |
| **SICE** | Subscription Intent Convergence Engine | Pre-emptive capacity monitoring and automated prorated upgrade synthesis ahead of limit breaches. |
| **FAFIE** | Federated Adaptive Fitness Intelligence Engine | Privacy-preserving cross-gym collaborative AI (FedAvg + Differential Privacy $\epsilon=1.5$) with local plateau detection. |
| **PTLME** | Predictive Tenant Load Materialization Engine | Demand-driven pre-emptive compute/partition provisioning 45 minutes before morning and evening rush hours. |
| **ACVE** | Autonomous Compliance Verification Engine | Pre-execution firewall enforcing multi-tenant isolation, RBAC, quotas, and cross-facility boundaries. |
| **TEFR / TEK** | Execution Fragment Repository & Evolution Kernel | Closed-loop operational telemetry ledger and parameter adaptation engine. |

---

## 🗃️ Database Architecture

FAM-FIOS uses an ACID-compliant relational SQLite database (am_fios.db) with dynamic PRAGMA schema migrations:

- **users Table**:
  - user_id (PK, VARCHAR)
  - 	enant_id (VARCHAR)
  - email (VARCHAR, UNIQUE)
  - hashed_password (VARCHAR — PBKDF2-HMAC-SHA256)
  - 
ole (VARCHAR — gym_admin, 	rainer, member)
  - ull_name (VARCHAR)
  - phone (VARCHAR)
  - city (VARCHAR)
  - ranch (VARCHAR)
  - status (VARCHAR)
  - created_at (DATETIME)

- **members Table**:
  - member_id (PK, VARCHAR — MEM-2026-XXXX)
  - 	enant_id (VARCHAR)
  - 
ame (VARCHAR)
  - email (VARCHAR)
  - phone (VARCHAR)
  - city (VARCHAR)
  - ranch (VARCHAR)
  - rea (VARCHAR)
  - goal (VARCHAR)
  - plan (VARCHAR)
  - mount_paid (FLOAT)
  - status (VARCHAR)
  - enrolled_at (DATETIME)

---

## 📂 Directory Layout

`
fam-fios/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI REST endpoints (tenants, gym, federated, load)
│   │   ├── core/
│   │   │   ├── config.py        # System configuration & tier limits
│   │   │   └── security.py      # PBKDF2 hashing, JWT tokens, Cryptographic OTP generator/verifier
│   │   ├── database.py          # SQLAlchemy SessionLocal, DatabaseStore, PRAGMA migrations, account lookup
│   │   ├── engines/
│   │   │   ├── tige.py          # Tenant Isolation Genome Engine
│   │   │   ├── dtdfe.py         # Dynamic Tenant Dependency Fabric Engine
│   │   │   ├── sice.py          # Subscription Intent Convergence Engine
│   │   │   ├── ptlme.py         # Predictive Tenant Load Materialization Engine
│   │   │   ├── acve.py          # Autonomous Compliance Verification Engine
│   │   │   ├── tek.py           # Tenant Evolution Kernel
│   │   │   ├── agents/          # Autonomous agents (membership, attendance)
│   │   │   └── fafie/           # Federated learning (local trainer, aggregator, plateau detector)
│   │   ├── models/              # Pydantic schemas, Genome models, SQLAlchemy DB models
│   │   └── main.py              # FastAPI application entrypoint & startup seeder
│   └── tests/                   # 24 automated unit and integration tests (100% pass rate)
│       ├── test_acve.py
│       ├── test_auth_and_db.py
│       ├── test_closed_loop.py
│       ├── test_closed_loop_failure.py # Failure-path test verifying ACVE loop halts & TEK penalty
│       ├── test_dtdfe.py
│       ├── test_fafie.py
│       ├── test_fafie_privacy_magnitude.py # Mathematical DP noise magnitude & L2-clipping verification
│       ├── test_otp.py          # Cryptographic OTP generation, expiry, and single-use verification
│       ├── test_ptlm.py
│       ├── test_sice.py
│       └── test_tig.py
├── fam_fios.db                  # Persistent SQLite relational database
├── simulation/                  # Multi-tenant execution simulation scripts
├── streamlit_app.py             # Complete interactive Streamlit web dashboard
├── requirements.txt             # Project dependencies
└── README.md                    # System documentation
`

---

## 🛠️ Quickstart & Execution Guide

### 1. Prerequisites
- Python 3.10 or higher
- Virtual environment recommended

### 2. Run the Interactive Dashboard
Launch the unified web operating system:
`ash
streamlit run streamlit_app.py
`
Open your browser at **http://localhost:8501**.

### 3. Run the Backend API (FastAPI)
` ash
uvicorn backend.app.main:app --reload --port 8000
`
Interactive Swagger API documentation is available at **http://localhost:8000/docs**.

### 4. Run the Automated Test Suite
Execute the full 24-test suite with detailed output:
```bash
pytest backend/tests -v
```

---

## 👥 Demo Personas for Instant Testing

| Persona | Role | Facility & Branch | Demo Mobile / Email |
| :--- | :--- | :--- | :--- |
| **Tanishka Shah** | Member | Titan Fitness — Baner High Street Franchise | +91 78880 85822 / 	anishkashahpune@gmail.com |
| **Sarah Jenkins** | Member | Apex Elite — Kalyani Nagar Branch | +91 98233 30002 / member@apexfitness.com |
| **Titan Executive** | Gym Admin | Titan Fitness Network (Gold Enterprise) | +91 98231 10001 / dmin@titan.com |
| **IronCore Manager** | Gym Admin | IronCore Athletic Club (Silver Tier) | +91 98232 20001 / dmin@ironcore.com |
| **Coach Alex** | Trainer | IronCore — Senapati Bapat Road Franchise | +91 98232 20002 / 	rainer@ironcore.com |

---

## 📜 Patent Citation
> **Invention Disclosure:** *Federated Adaptive Multi-Tenant Fitness Infrastructure Operating System (FAM-FIOS)*  
> **Reference ID:** 24BIT0370-24BIT0390-IDF-01  
> **Institution:** Vellore Institute of Technology (VIT SCORE)
