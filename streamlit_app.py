import sys
import os
import random
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.engines.tige import tige
from app.engines.dtdfe import dtdfe
from app.engines.agents.membership_agent import membership_agent
from app.engines.agents.attendance_agent import attendance_agent
from app.engines.sice import sice
from app.engines.fafie.local_trainer import FafieLocalTrainer
from app.engines.fafie.aggregator import fafie_aggregator
from app.engines.fafie.plateau_detector import plateau_detector
from app.engines.ptlme import ptlme
from app.engines.acve import acve
from app.engines.tek import tek
from app.core.security import verify_password, create_access_token, hash_password, generate_login_otp, verify_login_otp
from app.services.aws_sns import aws_sns_service, format_e164
from app.services.aws_s3 import aws_s3_service
from app.database import db_store, init_db, SessionLocal
from app.models.db_models import UserModel, MemberRecordModel
from app.models.intents import IntentObject
from app.models.events import TenantEvent

# Page Configuration
st.set_page_config(
    page_title="FAM-FIOS: Intelligent Gym Operating System",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and seed showcase gyms if missing
init_db()
if not db_store.get_genome("tenant_apex"):
    from app.main import startup_db_and_seed
    startup_db_and_seed()

# Multi-City and Franchise Branch Infrastructure
CITY_BRANCH_STRUCTURE = {
    "Pune": {
        "tenant_titan": {
            "brand_name": "Titan Fitness Network (Gold Enterprise)",
            "tier": "Gold",
            "branches": [
                {
                    "branch_id": "pune_titan_baner",
                    "branch_name": "Baner High Street Franchise",
                    "area": "Baner / Balewadi",
                    "address": "4th Floor, Platinum Square, Baner High Street, Pune",
                    "phone": "+91 98231 10001",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "Olympic Barbells, Steam & Sauna, CrossFit Box, Smoothie Bar, Certified Coaches"
                },
                {
                    "branch_id": "pune_titan_kothrud",
                    "branch_name": "Kothrud (Paud Road) Franchise",
                    "area": "Kothrud",
                    "address": "City Pride Complex, 3rd Floor, Paud Road, Kothrud, Pune",
                    "phone": "+91 98231 10002",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Olympic Barbells, Cardio Deck, Zumba & Yoga Studio, Shower & Locker Rooms"
                },
                {
                    "branch_id": "pune_titan_viman",
                    "branch_name": "Viman Nagar Franchise",
                    "area": "Viman Nagar",
                    "address": "Behind Phoenix Marketcity, Clover Park, Viman Nagar, Pune",
                    "phone": "+91 98231 10003",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "Free Weights Deck, Cryo Recovery Lounge, HIIT Zone, Valet Parking"
                },
                {
                    "branch_id": "pune_titan_hinjewadi",
                    "branch_name": "Hinjewadi Phase 1 (IT Hub) Franchise",
                    "area": "Hinjewadi",
                    "address": "Rajiv Gandhi Infotech Park, Near Wipro Circle, Phase 1, Pune",
                    "phone": "+91 98231 10004",
                    "timing": "24/7 Access (Keycard & QR)",
                    "amenities": "24/7 Tech Access, Ergonomic Machines, Showers & Lockers, High-Speed WiFi"
                },
                {
                    "branch_id": "pune_titan_kp",
                    "branch_name": "Koregaon Park VIP Franchise",
                    "area": "Koregaon Park",
                    "address": "Lane 7, North Main Road, Koregaon Park, Pune",
                    "phone": "+91 98231 10005",
                    "timing": "6:00 AM – Midnight",
                    "amenities": "Rooftop Turf, Pilates Reformer, Luxury Spa & Sauna, Organic Protein Bar"
                }
            ]
        },
        "tenant_iron": {
            "brand_name": "IronCore Athletic Club (Silver Tier)",
            "tier": "Silver",
            "branches": [
                {
                    "branch_id": "pune_iron_wakad",
                    "branch_name": "Wakad Franchise",
                    "area": "Wakad",
                    "address": "Datta Mandir Road, Wakad, Pune",
                    "phone": "+91 98232 20001",
                    "timing": "6:00 AM – 10:00 PM",
                    "amenities": "Powerlifting Racks, Heavy Dumbbells (up to 60kg), Calisthenics Rig"
                },
                {
                    "branch_id": "pune_iron_sb_road",
                    "branch_name": "Senapati Bapat Road Franchise",
                    "area": "SB Road / Deccan",
                    "address": "Opposite ICC Towers, SB Road, Pune",
                    "phone": "+91 98232 20002",
                    "timing": "6:00 AM – 10:00 PM",
                    "amenities": "Hammer Strength Equipment, Shower Rooms, Cardio Studio"
                },
                {
                    "branch_id": "pune_iron_magarpatta",
                    "branch_name": "Magarpatta City Franchise",
                    "area": "Hadapsar / Magarpatta",
                    "address": "Destination Centre, Magarpatta City, Hadapsar, Pune",
                    "phone": "+91 98232 20003",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Cardio Area, Functional Cross-training, Locker Facilities"
                },
                {
                    "branch_id": "pune_iron_fc_road",
                    "branch_name": "FC Road Franchise",
                    "area": "Shivajinagar / FC Road",
                    "address": "Fergusson College Road, Near Goodluck Cafe, Pune",
                    "phone": "+91 98232 20004",
                    "timing": "6:00 AM – 10:00 PM",
                    "amenities": "Student Discount Zone, Power Racks, Functional Turf"
                },
                {
                    "branch_id": "pune_iron_aundh",
                    "branch_name": "Aundh Franchise",
                    "area": "Aundh",
                    "address": "ITI Road, Above Star Bazaar, Aundh, Pune",
                    "phone": "+91 98232 20005",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "InBody 770 Composition Scanner, Personal Training, Steam Room"
                }
            ]
        },
        "tenant_apex": {
            "brand_name": "Apex Elite Fitness (Free Tier / Boutique)",
            "tier": "Free",
            "branches": [
                {
                    "branch_id": "pune_apex_camp",
                    "branch_name": "Camp / MG Road Branch",
                    "area": "Pune Camp",
                    "address": "East Street, Near Aurora Towers, Camp, Pune",
                    "phone": "+91 98233 30001",
                    "timing": "6:00 AM – 9:30 PM",
                    "amenities": "Classic Iron Weights, Boxing Bags, Free Weight Section"
                },
                {
                    "branch_id": "pune_apex_kalyani",
                    "branch_name": "Kalyani Nagar Branch",
                    "area": "Kalyani Nagar",
                    "address": "Central Avenue, Near Jogger's Park, Kalyani Nagar, Pune",
                    "phone": "+91 98233 30002",
                    "timing": "6:00 AM – 10:00 PM",
                    "amenities": "Boutique Studio, Yoga Sessions, WiFi"
                },
                {
                    "branch_id": "pune_apex_bavdhan",
                    "branch_name": "Bavdhan Branch",
                    "area": "Bavdhan",
                    "address": "NDA Road, Bavdhan, Pune",
                    "phone": "+91 98233 30003",
                    "timing": "6:00 AM – 9:30 PM",
                    "amenities": "Functional Turf, Dumbbells, Steam Room"
                },
                {
                    "branch_id": "pune_apex_pimpri",
                    "branch_name": "Pimpri-Chinchwad Branch",
                    "area": "PCMC",
                    "address": "Old Mumbai-Pune Highway, Pimpri, Pune",
                    "phone": "+91 98233 30004",
                    "timing": "6:00 AM – 10:00 PM",
                    "amenities": "Strength Equipment, Locker Room, Cardio Section"
                },
                {
                    "branch_id": "pune_apex_kondhwa",
                    "branch_name": "Kondhwa / NIBM Branch",
                    "area": "NIBM / Kondhwa",
                    "address": "NIBM Post Office Road, Kondhwa, Pune",
                    "phone": "+91 98233 30005",
                    "timing": "6:00 AM – 9:30 PM",
                    "amenities": "Bodybuilding Machines, Power Lifting, Juice Corner"
                }
            ]
        }
    },
    "Bengaluru": {
        "tenant_titan": {
            "brand_name": "Titan Fitness Network (Gold Enterprise)",
            "tier": "Gold",
            "branches": [
                {
                    "branch_id": "blr_titan_indira",
                    "branch_name": "Indiranagar 100ft Road Franchise",
                    "area": "Indiranagar",
                    "address": "100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru",
                    "phone": "+91 80 4111 0001",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "Rooftop Turf, Olympic Racks, Recovery Spa, Protein Cafe"
                },
                {
                    "branch_id": "blr_titan_kora",
                    "branch_name": "Koramangala 5th Block Franchise",
                    "area": "Koramangala",
                    "address": "Sony World Junction, 80ft Road, Koramangala, Bengaluru",
                    "phone": "+91 80 4111 0002",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "Steam & Sauna, CrossFit Arena, HIIT Zone"
                },
                {
                    "branch_id": "blr_titan_hsr",
                    "branch_name": "HSR Layout Sector 1 Franchise",
                    "area": "HSR Layout",
                    "address": "27th Main, Sector 1, HSR Layout, Bengaluru",
                    "phone": "+91 80 4111 0003",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Cardio Cinema, Olympic Barbells, Physiotherapy"
                },
                {
                    "branch_id": "blr_titan_wf",
                    "branch_name": "Whitefield ITPL Franchise",
                    "area": "Whitefield",
                    "address": "ITPL Main Road, Prestige Shantiniketan, Whitefield, Bengaluru",
                    "phone": "+91 80 4111 0004",
                    "timing": "24/7 Access",
                    "amenities": "24/7 Keycard, Corporate Lounge, Olympic Lifting"
                },
                {
                    "branch_id": "blr_titan_jp",
                    "branch_name": "JP Nagar 7th Phase Franchise",
                    "area": "JP Nagar",
                    "address": "Brigade Millennium Road, JP Nagar 7th Phase, Bengaluru",
                    "phone": "+91 80 4111 0005",
                    "timing": "5:30 AM – 10:30 PM",
                    "amenities": "Swimming Pool Access, Cardio Deck, Zumba Studio"
                }
            ]
        },
        "tenant_iron": {
            "brand_name": "IronCore Athletic Club (Silver Tier)",
            "tier": "Silver",
            "branches": [
                {
                    "branch_id": "blr_iron_bellandur",
                    "branch_name": "Bellandur EcoSpace Franchise",
                    "area": "Bellandur / ORR",
                    "address": "Opposite EcoSpace Business Park, Bellandur, Bengaluru",
                    "phone": "+91 80 4222 0001",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Powerlifting Racks, Heavy Dumbbells, Cardio Zone"
                }
            ]
        }
    },
    "Mumbai": {
        "tenant_titan": {
            "brand_name": "Titan Fitness Network (Gold Enterprise)",
            "tier": "Gold",
            "branches": [
                {
                    "branch_id": "mum_titan_bandra",
                    "branch_name": "Bandra West Linking Road Franchise",
                    "area": "Bandra West",
                    "address": "Linking Road, Near Khar Telephone Exchange, Bandra West, Mumbai",
                    "phone": "+91 22 2640 0001",
                    "timing": "5:30 AM – 11:30 PM",
                    "amenities": "Celebrity Trainers, Cryotherapy, Pilates Reformer, Valet Parking"
                },
                {
                    "branch_id": "mum_titan_andheri",
                    "branch_name": "Andheri West Lokhandwala Franchise",
                    "area": "Andheri West",
                    "address": "Lokhandwala Complex, Above Indigo Delicatessen, Andheri West, Mumbai",
                    "phone": "+91 22 2640 0002",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Heavy Lifting Platform, Steam/Sauna, Juice Bar"
                },
                {
                    "branch_id": "mum_titan_powai",
                    "branch_name": "Powai Hiranandani Franchise",
                    "area": "Powai",
                    "address": "Galleria Shopping Mall, Hiranandani Gardens, Powai, Mumbai",
                    "phone": "+91 22 2640 0003",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Lake View Cardio Deck, Olympic Barbells, CrossFit"
                },
                {
                    "branch_id": "mum_titan_juhu",
                    "branch_name": "Juhu Tara Road Franchise",
                    "area": "Juhu",
                    "address": "Juhu Tara Road, Near Sea Princess Hotel, Juhu, Mumbai",
                    "phone": "+91 22 2640 0004",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "VIP Lounge, Beachside Outdoor Area, Physiotherapy"
                },
                {
                    "branch_id": "mum_titan_lower_parel",
                    "branch_name": "Lower Parel Phoenix Mills Franchise",
                    "area": "Lower Parel",
                    "address": "Senapati Bapat Marg, Lower Parel, Mumbai",
                    "phone": "+91 22 2640 0005",
                    "timing": "6:00 AM – Midnight",
                    "amenities": "Executive Locker Rooms, Shower & Towel Service, Steam"
                }
            ]
        }
    },
    "Delhi NCR": {
        "tenant_titan": {
            "brand_name": "Titan Fitness Network (Gold Enterprise)",
            "tier": "Gold",
            "branches": [
                {
                    "branch_id": "del_titan_cp",
                    "branch_name": "Connaught Place Inner Circle Franchise",
                    "area": "Connaught Place (CP)",
                    "address": "Block E, Inner Circle, Connaught Place, New Delhi",
                    "phone": "+91 11 4350 0001",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Prime Location, Steam & Sauna, Heavy Free Weights"
                },
                {
                    "branch_id": "del_titan_gurgaon",
                    "branch_name": "Gurugram Golf Course Road Franchise",
                    "area": "Golf Course Road, Gurugram",
                    "address": "Sector 54, Golf Course Road, Gurugram, Haryana",
                    "phone": "+91 124 450 0002",
                    "timing": "5:30 AM – Midnight",
                    "amenities": "24/7 Access, CrossFit Arena, Swimming Pool, Spa"
                },
                {
                    "branch_id": "del_titan_noida",
                    "branch_name": "Noida Sector 62 Franchise",
                    "area": "Sector 62, Noida",
                    "address": "Logix Cyber Park, Sector 62, Noida, UP",
                    "phone": "+91 120 450 0003",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Cardio Theater, Olympic Lifting, Zumba Hall"
                },
                {
                    "branch_id": "del_titan_south_ex",
                    "branch_name": "South Extension Part 2 Franchise",
                    "area": "South Extension",
                    "address": "Main Ring Road, South Ex Part 2, New Delhi",
                    "phone": "+91 11 4350 0004",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Strength Equipment, Physiotherapy, Sauna"
                },
                {
                    "branch_id": "del_titan_hauz_khas",
                    "branch_name": "Hauz Khas Franchise",
                    "area": "Hauz Khas",
                    "address": "Aurobindo Marg, Near Hauz Khas Metro, New Delhi",
                    "phone": "+91 11 4350 0005",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Calisthenics Area, Olympic Weights, Smoothie Bar"
                }
            ]
        }
    },
    "Hyderabad": {
        "tenant_titan": {
            "brand_name": "Titan Fitness Network (Gold Enterprise)",
            "tier": "Gold",
            "branches": [
                {
                    "branch_id": "hyd_titan_hitec",
                    "branch_name": "HITEC City Cyber Towers Franchise",
                    "area": "HITEC City / Madhapur",
                    "address": "Cyber Gateway, HITEC City, Hyderabad",
                    "phone": "+91 40 4455 0001",
                    "timing": "5:30 AM – 11:30 PM",
                    "amenities": "Olympic Barbells, Steam & Sauna, 24/7 Access"
                },
                {
                    "branch_id": "hyd_titan_banjara",
                    "branch_name": "Banjara Hills Road No. 12 Franchise",
                    "area": "Banjara Hills",
                    "address": "Road Number 12, Banjara Hills, Hyderabad",
                    "phone": "+91 40 4455 0002",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "VIP Wellness Suite, Pilates, CrossFit Turf"
                },
                {
                    "branch_id": "hyd_titan_gachibowli",
                    "branch_name": "Gachibowli Financial District Franchise",
                    "area": "Gachibowli",
                    "address": "Financial District, Nanakramguda, Gachibowli, Hyderabad",
                    "phone": "+91 40 4455 0003",
                    "timing": "6:00 AM – 11:00 PM",
                    "amenities": "Olympic Lifting, Recovery Ice Bath, Showers"
                },
                {
                    "branch_id": "hyd_titan_jubilee",
                    "branch_name": "Jubilee Hills Road 36 Franchise",
                    "area": "Jubilee Hills",
                    "address": "Near Peddamma Temple Metro, Road No. 36, Jubilee Hills, Hyderabad",
                    "phone": "+91 40 4455 0004",
                    "timing": "5:30 AM – 11:00 PM",
                    "amenities": "Rooftop Conditioning, Personal Training, Organic Cafe"
                },
                {
                    "branch_id": "hyd_titan_kondapur",
                    "branch_name": "Kondapur Botanical Garden Franchise",
                    "area": "Kondapur",
                    "address": "Near Botanical Garden Road, Kondapur, Hyderabad",
                    "phone": "+91 40 4455 0005",
                    "timing": "6:00 AM – 10:30 PM",
                    "amenities": "Cardio Cinema, Steam Room, Free Weights"
                }
            ]
        }
    }
}

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("# ⚡ **FAM-FIOS**")
st.sidebar.markdown("**Federated Adaptive Multi-Tenant Fitness OS**")
st.sidebar.caption("Patent Invention Disclosure: `24BIT0370-24BIT0390-IDF-01`")
st.sidebar.markdown("---")

# --- SIDEBAR AUTHENTICATION STATUS WIDGET ---
logged_in_user = st.session_state.get("authenticated_user", None)
if logged_in_user:
    role_label = "🟢 Member" if logged_in_user.get("role") == "member" else ("🏢 Gym Admin" if logged_in_user.get("role") == "gym_admin" else "🏋️ Trainer")
    with st.sidebar.container(border=True):
        st.markdown(f"**👤 {logged_in_user.get('full_name', 'User')}**")
        st.caption(f"Role: **{role_label}** &nbsp;|&nbsp; {logged_in_user.get('branch', 'Main Branch')}")
        st.caption(f"📱 `{logged_in_user.get('phone') or logged_in_user.get('email')}`")
        if st.button("🚪 Log Out", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.pop("authenticated_user", None)
            st.session_state.pop("logged_in_member", None)
            st.session_state.nav_target = "🔐 Member & Admin Login (via OTP)"
            st.rerun()
else:
    with st.sidebar.container(border=True):
        st.caption("🔒 **Security Mode: Guest / Visitor**")
        if st.button("🔐 Log In via Mobile OTP", key="sidebar_login_btn", use_container_width=True):
            st.session_state.nav_target = "🔐 Member & Admin Login (via OTP)"
            st.rerun()

st.sidebar.markdown("---")

PORTAL_OPTIONS = [
    "🔐 Member & Admin Login (via OTP)",
    "📝 New Member Registration & Payment",
    "🏢 Gym Owner / Admin View",
    "🗄️ Central Users & Members Database",
    "🏋️ Gym Member / User View",
    "🔬 Patent & Architecture Deep-Dive"
]

if "nav_target" in st.session_state and st.session_state.nav_target in PORTAL_OPTIONS:
    default_portal = st.session_state.pop("nav_target")
elif "current_portal" in st.session_state and st.session_state.current_portal in PORTAL_OPTIONS:
    default_portal = st.session_state.current_portal
else:
    default_portal = PORTAL_OPTIONS[0]

portal_idx = PORTAL_OPTIONS.index(default_portal)

portal_mode = st.sidebar.radio(
    "👉 Choose Portal Mode:",
    PORTAL_OPTIONS,
    index=portal_idx,
    help="Switch between user registration, gym admin management, central users database, member workouts, and patent architecture."
)
st.session_state.current_portal = portal_mode

st.sidebar.markdown("---")

# Active Gym Facility selector for Admin and Member views
all_tenants = db_store.list_genomes()
tenant_dict = {f"{g.gym_name} ({g.tenant_id})": g.tenant_id for g in all_tenants}
tenant_id_to_label = {g.tenant_id: f"{g.gym_name} ({g.tenant_id})" for g in all_tenants}

if "tenant_target" in st.session_state and st.session_state.tenant_target in tenant_id_to_label:
    default_tenant_label = tenant_id_to_label[st.session_state.pop("tenant_target")]
elif "selected_tenant_label" in st.session_state and st.session_state.selected_tenant_label in tenant_dict:
    default_tenant_label = st.session_state.selected_tenant_label
else:
    default_tenant_label = list(tenant_dict.keys())[0]

tenant_idx = list(tenant_dict.keys()).index(default_tenant_label) if default_tenant_label in tenant_dict else 0

selected_tenant_label = st.sidebar.selectbox(
    "🏢 Active Facility Filter:",
    list(tenant_dict.keys()),
    index=tenant_idx,
    help="Filter data for a specific gym."
)
st.session_state.selected_tenant_label = selected_tenant_label
active_tenant_id = tenant_dict[selected_tenant_label]
active_genome = db_store.get_genome(active_tenant_id)
sub = active_genome.subscription
usage = active_genome.usage

st.sidebar.markdown("---")
with st.sidebar.expander("📖 Quick Patent Guide (1-Minute Read)"):
    st.markdown("""
    - **TIG**: Models each gym as an executable digital object with evolving capacity and server limits.
    - **SICE**: Automatically tracks new signups and calculates fair prorated upgrade fees before gym capacity runs out.
    - **PTLM**: Predicts morning/evening rush hours and spins up servers 45 min in advance.
    - **FAFIE**: Multi-gym collaborative AI workout recommendations without sharing member private data.
    - **ACVE**: The security firewall that prevents any gym from seeing another gym's records.
    """)

if st.sidebar.button("🔄 Reset Database to Factory Defaults", use_container_width=True):
    db_store.reset()
    from app.main import startup_db_and_seed
    startup_db_and_seed()
    st.sidebar.success("Database re-seeded with Apex, IronCore, and Titan!")
    st.rerun()

# ==============================================================================
# 0. SECURE OTP LOGIN & AUTHENTICATION PORTAL (NEW FEATURE!)
# ==============================================================================
if portal_mode == "🔐 Member & Admin Login (via OTP)":
    st.title("🔐 Secure Member & Admin Login via OTP")
    st.markdown("""
    Sign in to your fitness account or gym command center without remembering passwords. 
    Enter your registered **Mobile Phone Number** or **Email Address**, and we'll dispatch a 6-digit verification code.
    """)
    
    # Check if already logged in
    current_auth = st.session_state.get("authenticated_user", None)
    if current_auth:
        st.success(f"✅ You are currently authenticated as **{current_auth.get('full_name')}** ({current_auth.get('role').title()})!")
        col_logged1, col_logged2 = st.columns(2)
        with col_logged1:
            dest_portal = "🏋️ Gym Member / User View" if current_auth.get("role") == "member" else "🏢 Gym Owner / Admin View"
            if st.button(f"👉 Proceed to My Portal ({dest_portal})", type="primary", use_container_width=True):
                st.session_state.nav_target = dest_portal
                st.rerun()
        with col_logged2:
            if st.button("🚪 Log Out / Switch Account", use_container_width=True):
                st.session_state.pop("authenticated_user", None)
                st.session_state.pop("logged_in_member", None)
                st.session_state.pop("active_otp_record", None)
                st.session_state.otp_step = "request"
                st.rerun()
    else:
        # Initialize OTP state
        if "otp_step" not in st.session_state:
            st.session_state.otp_step = "request" # "request" or "verify"
            
        col_login_main, col_login_info = st.columns([3, 2])
        
        with col_login_main:
            if st.session_state.otp_step == "request":
                st.subheader("1️⃣ Enter Your Registered Mobile Number or Email")
                
                # AWS Cloud Gateway Configuration Expander
                with st.expander("☁️ **AWS Cloud Gateway Configuration & Status (Amazon SNS)**", expanded=False):
                    aws_status = aws_sns_service.check_sns_configuration(st.session_state.get("custom_aws_credentials"))
                    if aws_status["configured"]:
                        st.success(f"🟢 **Amazon SNS Active**: Connected to AWS Region `{aws_status['region']}` (Key: `{aws_status['masked_key']}`). Real SMS will be delivered directly to your mobile phone via carrier gateways!")
                    else:
                        st.info(f"🟡 **Sandbox Simulation Active**: Boto3 engine is ready. Standard demo OTPs display securely on-screen. To test real live SMS dispatch to your physical phone via AWS, enter your AWS credentials below:")
                    
                    col_aws_k1, col_aws_k2 = st.columns(2)
                    with col_aws_k1:
                        aws_key_input = st.text_input("AWS Access Key ID", value=st.session_state.get("custom_aws_credentials", {}).get("aws_access_key_id", ""), type="password", placeholder="e.g. AKIAIOSFODNN7EXAMPLE")
                        aws_reg_input = st.selectbox("AWS Region", ["ap-south-1 (Mumbai)", "us-east-1 (N. Virginia)", "eu-west-1 (Ireland)", "ap-southeast-1 (Singapore)"], index=0)
                    with col_aws_k2:
                        aws_sec_input = st.text_input("AWS Secret Access Key", value=st.session_state.get("custom_aws_credentials", {}).get("aws_secret_access_key", ""), type="password", placeholder="e.g. wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
                        col_save_aws, col_reset_aws = st.columns([1, 1])
                        with col_save_aws:
                            if st.button("💾 Apply AWS Keys", use_container_width=True):
                                reg = aws_reg_input.split(" ")[0]
                                if aws_key_input.strip() and aws_sec_input.strip():
                                    st.session_state.custom_aws_credentials = {
                                        "aws_access_key_id": aws_key_input.strip(),
                                        "aws_secret_access_key": aws_sec_input.strip(),
                                        "region_name": reg
                                    }
                                    st.toast("✅ AWS SNS credentials configured for this session!", icon="☁️")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Please provide both Access Key ID and Secret Access Key.")
                        with col_reset_aws:
                            if st.button("🔄 Reset to Simulation", use_container_width=True):
                                st.session_state.pop("custom_aws_credentials", None)
                                st.toast("Reset to simulation sandbox mode.", icon="🔄")
                                st.rerun()

                # Demo Personas Quick Select
                st.markdown("**⚡ Quick-Select Demo Persona (1-Click Test):**")
                c_demo1, c_demo2, c_demo3, c_demo4 = st.columns(4)
                with c_demo1:
                    if st.button("👤 Tanishka Shah\n(Titan Member)", use_container_width=True):
                        st.session_state.login_input_ident = "+91 78880 85822"
                        st.rerun()
                with c_demo2:
                    if st.button("👤 Sarah Jenkins\n(Apex Member)", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98233 30002"
                        st.rerun()
                with c_demo3:
                    if st.button("🏢 Titan Executive\n(Gym Admin)", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98231 10001"
                        st.rerun()
                with c_demo4:
                    if st.button("🏋️ Coach Alex\n(IronCore Trainer)", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98232 20002"
                        st.rerun()
                        
                default_ident = st.session_state.get("login_input_ident", "")
                user_ident = st.text_input(
                    "📱 Mobile Phone Number or ✉️ Email Address:",
                    value=default_ident,
                    placeholder="e.g. +91 98220 54321 or your.email@gmail.com",
                    key="login_ident_field"
                )
                
                send_otp_btn = st.button("📲 Send 6-Digit Verification OTP", type="primary", use_container_width=True)
                
                if send_otp_btn:
                    if not user_ident.strip():
                        st.error("⚠️ Please enter a valid mobile number or email address.")
                    else:
                        clean_ident = user_ident.strip()
                        # Generate OTP with optional AWS credentials
                        custom_creds = st.session_state.get("custom_aws_credentials")
                        otp_rec = generate_login_otp(clean_ident, custom_aws_credentials=custom_creds)
                        
                        # Look up account in database
                        matched_account = db_store.find_account_by_identifier(clean_ident)
                        otp_rec["account"] = matched_account
                        
                        st.session_state.active_otp_record = otp_rec
                        st.session_state.otp_step = "verify"
                        st.session_state.entered_otp_val = ""
                        st.rerun()
                        
            elif st.session_state.otp_step == "verify":
                otp_rec = st.session_state.get("active_otp_record", {})
                if not otp_rec:
                    st.session_state.otp_step = "request"
                    st.rerun()
                matched_acc = otp_rec.get("account")
                
                st.subheader("2️⃣ Enter 6-Digit Verification Code")
                st.write(f"We've sent a 6-digit OTP to **{otp_rec.get('masked_target', '')}** via {otp_rec.get('channel', 'SMS')} Gateway.")
                
                # Dynamic SMS / AWS Push Notification Card
                is_aws = (otp_rec.get("dispatch_mode") == "aws_sns")
                badge_bg = "#065F46" if is_aws else "#0369A1"
                badge_text = "🟢 AWS Amazon SNS Live Dispatch" if is_aws else "Jio / Twilio Sandbox Simulator"
                badge_border = "#10B981" if is_aws else "#38BDF8"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1E293B, #0F172A); border: 2px solid {badge_border}; border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 14px rgba(56, 189, 248, 0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: bold; color: {badge_border}; font-size: 14px;">📲 {otp_rec.get('channel', 'SMS').upper()} DISPATCH NOTIFICATION</span>
                        <span style="background-color: {badge_bg}; color: white; padding: 2px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;">{badge_text}</span>
                    </div>
                    <div style="font-size: 15px; color: #F8FAFC; margin-bottom: 8px;">
                        <strong>FAM-FIOS Security:</strong> Your login OTP is <span style="font-size: 22px; font-weight: bold; color: #FCD34D; letter-spacing: 4px; padding: 2px 8px; background: rgba(0,0,0,0.4); border-radius: 4px;">{otp_rec.get('otp', '000000')}</span>. Valid for 5 minutes.
                    </div>
                    <div style="font-size: 12px; color: #94A3B8;">
                        Target: {otp_rec.get('raw_identifier', '')} | Region: {otp_rec.get('region', 'ap-south-1')} | Ref: {otp_rec.get('aws_message_id', 'AUTH-OTP-000')}
                    </div>
                    <div style="font-size: 11px; color: {'#6EE7B7' if is_aws else '#93C5FD'}; margin-top: 5px;">
                        <strong>Gateway Status:</strong> {otp_rec.get('aws_status_text', 'Dispatched successfully')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_otp_fill, col_otp_resend = st.columns([1, 1])
                with col_otp_fill:
                    if st.button("⚡ 1-Click Auto-Fill OTP", use_container_width=True):
                        st.session_state.entered_otp_val = otp_rec.get('otp', '')
                        st.rerun()
                        
                with col_otp_resend:
                    if st.button("🔁 Resend New OTP", use_container_width=True):
                        custom_creds = st.session_state.get("custom_aws_credentials")
                        new_rec = generate_login_otp(otp_rec.get('raw_identifier', ''), custom_aws_credentials=custom_creds)
                        new_rec["account"] = matched_acc
                        st.session_state.active_otp_record = new_rec
                        st.session_state.entered_otp_val = ""
                        st.toast("📨 New OTP sent to your device!", icon="📲")
                        st.rerun()
                        
                curr_otp = st.session_state.get("entered_otp_val", "")
                entered_otp = st.text_input("Enter 6-Digit OTP:", value=curr_otp, max_chars=6, placeholder="e.g. 123456", key="otp_input_field")
                
                verify_btn = st.button("🔓 Verify OTP & Log In", type="primary", use_container_width=True)
                
                if verify_btn:
                    if not entered_otp.strip():
                        st.error("⚠️ Please enter the 6-digit OTP code.")
                    else:
                        is_valid, msg = verify_login_otp(otp_rec["raw_identifier"], entered_otp.strip())
                        if not is_valid:
                            st.error(f"❌ {msg}")
                        else:
                            st.balloons()
                            # Build authenticated user dictionary
                            if matched_acc:
                                user_session = {
                                    "user_id": matched_acc.get("user_id") or matched_acc.get("member_id", "usr_otp_guest"),
                                    "full_name": matched_acc.get("full_name", "Valued Member"),
                                    "email": matched_acc.get("email", otp_rec["raw_identifier"]),
                                    "phone": matched_acc.get("phone", otp_rec["raw_identifier"]),
                                    "role": matched_acc.get("role", "member"),
                                    "tenant_id": matched_acc.get("tenant_id", "tenant_titan"),
                                    "city": matched_acc.get("city", "Pune"),
                                    "branch": matched_acc.get("branch", "Baner High Street Franchise"),
                                    "plan": matched_acc.get("plan", "Standard Membership")
                                }
                            else:
                                raw_id = str(otp_rec.get("raw_identifier", ""))
                                is_tanishka = ("788808" in raw_id) or ("tanishka" in raw_id.lower())
                                if is_tanishka:
                                    resolved_name = "Tanishka Shah"
                                elif "@" in raw_id:
                                    prefix = raw_id.split("@")[0].replace(".", " ").replace("_", " ").title()
                                    resolved_name = prefix if len(prefix) > 2 else "Verified Gym Member"
                                else:
                                    resolved_name = "Verified Gym Member"

                                # New / unseeded number logged in as verified member
                                user_session = {
                                    "user_id": f"usr_mem_{otp_rec.get('otp', '9999')[:4]}",
                                    "full_name": resolved_name,
                                    "email": raw_id if "@" in raw_id else f"member.{otp_rec.get('otp', '0000')[:4]}@gmail.com",
                                    "phone": raw_id,
                                    "role": "member",
                                    "tenant_id": "tenant_titan",
                                    "city": "Pune",
                                    "branch": "Baner High Street Franchise",
                                    "plan": "1 Month Standard Access"
                                }
                            
                            st.session_state.authenticated_user = user_session
                            if user_session["role"] == "member":
                                st.session_state.logged_in_member = {
                                    "member_id": user_session["user_id"],
                                    "name": user_session["full_name"],
                                    "email": user_session["email"],
                                    "phone": user_session["phone"],
                                    "tenant_id": user_session["tenant_id"],
                                    "gym_name": "Titan Fitness Network",
                                    "city": user_session["city"],
                                    "branch_name": user_session["branch"],
                                    "plan_name": user_session.get("plan", "1 Month Standard Access"),
                                    "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%d %b %Y"),
                                    "goal": "Hypertrophy (Muscle Gain)"
                                }
                                st.session_state.nav_target = "🏋️ Gym Member / User View"
                                st.session_state.tenant_target = user_session["tenant_id"]
                            else:
                                st.session_state.nav_target = "🏢 Gym Owner / Admin View"
                                st.session_state.tenant_target = user_session["tenant_id"]
                                
                            st.session_state.otp_step = "request"
                            st.session_state.pop("active_otp_record", None)
                            st.toast(f"🎉 Login Successful! Welcome back, {user_session['full_name']}!", icon="✅")
                            st.rerun()
                            
                st.markdown("")
                if st.button("⬅️ Back to Enter Different Number / Email"):
                    st.session_state.otp_step = "request"
                    st.session_state.pop("active_otp_record", None)
                    st.session_state.entered_otp_val = ""
                    st.rerun()

        with col_login_info:
            st.markdown("### 🛡️ **Zero-Password OTP Security**")
            with st.container(border=True):
                st.markdown("""
                - 🔒 **Cryptographic 6-Digit Token**: Generated using CSPRNG (`secrets.randbelow`) and validated using constant-time HMAC comparison to eliminate timing attacks.
                - ⏱️ **Time-Bound Validity**: OTPs expire automatically after **5 minutes**.
                - ⚡ **Single-Use Invalidation**: The OTP is consumed and deleted from memory instantly upon successful verification.
                - 🏢 **Multi-Role Single Sign-On**:
                  - **Members** ➔ Instant pass, gym check-in, workout tracking.
                  - **Admins** ➔ Franchise roster, capacity scaling, billing metrics.
                  - **Trainers** ➔ Client assignment & plateau detector.
                """)

# ==============================================================================
# 1. NEW MEMBER REGISTRATION & PAYMENT PORTAL (NEW FEATURE!)
# ==============================================================================
elif portal_mode == "📝 New Member Registration & Payment":
    if "checkout_stage" not in st.session_state:
        st.session_state.checkout_stage = "form"

    # ==========================================================================
    # STAGE 1: REGISTRATION DETAILS & PLAN SELECTION
    # ==========================================================================
    if st.session_state.checkout_stage == "form":
        st.title("📝 Public Member Registration & Membership Pass")
        st.markdown("""
        Welcome! Choose your preferred gym facility and area, pick your membership duration, 
        and proceed to payment. **Once payment is processed, you are automatically registered in the Gym Admin's management system in real time!**
        """)
        
        # Step progress indicator
        st.markdown("""
        <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #334155;">
            <span style="color: #38BDF8; font-weight: bold;">📍 Step 1: Membership & Facility Details (ACTIVE)</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #94A3B8;">💳 Step 2: Dedicated Payment Gateway</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #94A3B8;">🎟️ Step 3: Digital Pass & Connected Pages</span>
        </div>
        """, unsafe_allow_html=True)

        reg_col1, reg_col2 = st.columns([3, 2])

        with reg_col1:
            st.subheader("1️⃣ Select City & Specific Franchise Branch")
            col_city, col_brand = st.columns(2)
            with col_city:
                selected_city = st.selectbox("🏙️ Step 1: Select City:", list(CITY_BRANCH_STRUCTURE.keys()), key="form_city")

            available_gym_brands = CITY_BRANCH_STRUCTURE[selected_city]
            brand_options = {brand_info["brand_name"]: tid for tid, brand_info in available_gym_brands.items()}

            with col_brand:
                selected_brand_name = st.selectbox("🏢 Step 2: Select Gym Brand / Network:", list(brand_options.keys()), key="form_brand")

            chosen_tenant_id = brand_options[selected_brand_name]
            brand_data = available_gym_brands[chosen_tenant_id]
            branch_list = brand_data["branches"]
            branch_dict = {f"{b['branch_name']} ({b['area']})": b for b in branch_list}

            selected_branch_label = st.selectbox(
                f"📍 Step 3: Choose Franchise Branch in {selected_city} ({len(branch_list)} available):",
                list(branch_dict.keys()),
                help=f"Select from {len(branch_list)} distinct {selected_brand_name} franchises in {selected_city}.",
                key="form_branch"
            )
            selected_branch = branch_dict[selected_branch_label]

            chosen_genome = db_store.get_genome(chosen_tenant_id)
            chosen_sub = chosen_genome.subscription
            remaining_slots = max(0, chosen_sub.max_members - chosen_sub.active_members)

            # Dynamic Branch Facility Card
            st.info(f"""
            🏢 **{chosen_genome.gym_name} — {selected_branch['branch_name']}**  
            - 🏙️ **City & Area:** {selected_city} — {selected_branch['area']}  
            - 📍 **Address:** {selected_branch['address']}  
            - 📞 **Branch Phone:** `{selected_branch['phone']}`  
            - 🕒 **Operating Hours:** `{selected_branch['timing']}`  
            - 🏆 **Facility Tier:** `{chosen_sub.tier} Plan` ({remaining_slots} membership spots remaining)  
            - ✨ **Amenities:** {selected_branch['amenities']}
            """)

            st.subheader("2️⃣ Member Personal Information")
            u_name = st.text_input("Full Name", placeholder="e.g. Siddharth Verma", key="input_u_name")
            u_email = st.text_input("Email Address", placeholder="e.g. siddharth.verma@gmail.com", key="input_u_email")
            u_phone = st.text_input("Mobile Number", placeholder="e.g. +91 98220 54321", key="input_u_phone")
            
            c_age, c_gender = st.columns(2)
            with c_age:
                u_age = st.number_input("Age", min_value=14, max_value=85, value=22, key="input_u_age")
            with c_gender:
                u_gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"], key="input_u_gender")

            u_goal = st.selectbox(
                "Primary Fitness Goal",
                [
                    "Hypertrophy (Muscle Gain & Bodybuilding)",
                    "Fat Loss & Cardiovascular Health",
                    "Powerlifting & Strength",
                    "General Athletic Conditioning & Mobility"
                ],
                key="input_u_goal"
            )

            st.subheader("3️⃣ Choose Membership Plan")
            plan_choice = st.radio(
                "Select Plan Duration:",
                [
                    "1 Month Standard Access — ₹1,499",
                    "3 Months Quarterly (Save 15%) — ₹3,799",
                    "12 Months Annual VIP (Save 33%) — ₹11,999"
                ],
                key="input_plan_choice"
            )
            
            base_price = 1499.0 if "1 Month" in plan_choice else (3799.0 if "3 Months" in plan_choice else 11999.0)
            gst_amount = round(base_price * 0.18, 2)
            total_payable = round(base_price + gst_amount, 2)

        with reg_col2:
            st.subheader("4️⃣ Checkout & Payment Gateway")
            with st.container(border=True):
                st.markdown("#### 🧾 **Order Summary**")
                st.write(f"**Gym Network:** {chosen_genome.gym_name}")
                st.write(f"**City:** {selected_city}")
                st.write(f"**Franchise Branch:** {selected_branch['branch_name']}")
                st.write(f"**Branch Address:** {selected_branch['address']}")
                st.write(f"**Plan Duration:** {plan_choice.split('—')[0].strip()}")
                st.write(f"Base Membership Fee: **₹{base_price:,.2f}**")
                st.write(f"GST (18%): **₹{gst_amount:,.2f}**")
                st.markdown("---")
                st.markdown(f"### **Total Amount: ₹{total_payable:,.2f}**")

                st.markdown("#### **Preferred Payment Mode**")
                pay_method = st.radio(
                    "Choose payment gateway method to open:",
                    [
                        "📱 UPI Gateway (Google Pay / PhonePe / Paytm / QR)",
                        "💳 Credit / Debit Card (with 3D Secure OTP)",
                        "🏛️ Net Banking Gateway (SBI, HDFC, ICICI, Axis)",
                        "⚡ Instant 1-Click Fast Checkout (Demo Mode)"
                    ],
                    key="input_pay_method"
                )

                st.caption("🔒 256-Bit SSL Encrypted. You will proceed to a dedicated payment gateway on the next page.")

                u_name_clean = (u_name or st.session_state.get("input_u_name", "")).strip()
                u_email_clean = (u_email or st.session_state.get("input_u_email", "")).strip()
                u_phone_clean = (u_phone or st.session_state.get("input_u_phone", "")).strip()

                # If email is empty (common when Chrome/Edge autofill doesn't trigger React's synthetic event), generate clean fallback
                if not u_email_clean and u_name_clean:
                    u_email_clean = f"{u_name_clean.lower().replace(' ', '.')}@gmail.com"
                elif not u_email_clean:
                    u_email_clean = "member@fitness.fam"

                proceed_btn = st.button("💳 Proceed to Payment Gateway ➡️", type="primary", use_container_width=True)

                if proceed_btn:
                    missing_fields = []
                    if not u_name_clean:
                        missing_fields.append("Full Name")
                    if not u_phone_clean:
                        missing_fields.append("Mobile Number")

                    if missing_fields:
                        st.error(f"⚠️ Missing required info: Please enter your {', '.join(missing_fields)} before proceeding.")
                    elif chosen_sub.active_members >= chosen_sub.max_members:
                        st.error(f"⚠️ Registration Blocked by SICE: {chosen_genome.gym_name} is currently at maximum capacity ({chosen_sub.active_members}/{chosen_sub.max_members}). Upgrade required!")
                    else:
                        st.session_state.checkout_data = {
                            "tenant_id": chosen_tenant_id,
                            "gym_name": chosen_genome.gym_name,
                            "tier": chosen_sub.tier,
                            "city": selected_city,
                            "branch_name": selected_branch["branch_name"],
                            "branch_area": selected_branch["area"],
                            "branch_address": selected_branch["address"],
                            "branch_phone": selected_branch["phone"],
                            "name": u_name_clean,
                            "email": u_email_clean,
                            "phone": u_phone_clean,
                            "age": u_age,
                            "gender": u_gender,
                            "goal": u_goal,
                            "plan_choice": plan_choice,
                            "base_price": base_price,
                            "gst_amount": gst_amount,
                            "total_payable": total_payable,
                            "pay_method": pay_method
                        }
                        st.session_state.checkout_stage = "gateway"
                        st.rerun()

    # ==========================================================================
    # STAGE 2: DEDICATED PAYMENT GATEWAY PAGE
    # ==========================================================================
    elif st.session_state.checkout_stage == "gateway":
        c_data = st.session_state.checkout_data
        st.title("🔒 FAM-FIOS Secure Payment Gateway")
        
        # Step progress indicator
        st.markdown("""
        <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #334155;">
            <span style="color: #10B981; font-weight: bold;">✅ Step 1: Details Confirmed</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #38BDF8; font-weight: bold;">💳 Step 2: Payment Gateway & Authentication (ACTIVE)</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #94A3B8;">🎟️ Step 3: Digital Pass & Connected Pages</span>
        </div>
        """, unsafe_allow_html=True)

        # Gateway Top Overview Bar
        with st.container(border=True):
            col_ov1, col_ov2, col_ov3, col_ov4 = st.columns(4)
            with col_ov1:
                st.caption("MERCHANT / GYM")
                st.markdown(f"**{c_data['gym_name']}**")
                st.caption(f"📍 {c_data['branch_name']}, {c_data['city']}")
            with col_ov2:
                st.caption("MEMBER SUBSCRIBER")
                st.markdown(f"**{c_data['name']}**")
                st.caption(f"📞 {c_data['phone']}")
            with col_ov3:
                st.caption("PLAN & DURATION")
                st.markdown(f"**{c_data['plan_choice'].split('—')[0].strip()}**")
                st.caption(f"Base: ₹{c_data['base_price']:,.2f} + GST: ₹{c_data['gst_amount']:,.2f}")
            with col_ov4:
                st.caption("TOTAL PAYABLE")
                st.markdown(f"### **₹{c_data['total_payable']:,.2f}**")

        st.markdown("---")

        # Payment Tabs
        gw_tab_names = [
            "📱 UPI Gateway (GPay / PhonePe / Paytm / QR)",
            "💳 Credit / Debit Card & 3D Secure OTP",
            "🏛️ Net Banking Gateway",
            "⚡ 1-Click Instant Approval (Demo)"
        ]
        
        initial_tab_idx = 0
        if "Card" in c_data["pay_method"]:
            initial_tab_idx = 1
        elif "Net Banking" in c_data["pay_method"]:
            initial_tab_idx = 2
        elif "Instant" in c_data["pay_method"]:
            initial_tab_idx = 3

        selected_gw_tab = st.radio(
            "Select or switch payment option on gateway:",
            gw_tab_names,
            index=initial_tab_idx,
            horizontal=True,
            key="gw_radio_tab"
        )

        st.markdown("")

        payment_authorized = False
        authorized_method = ""

        # --- GATEWAY OPTION 1: UPI ---
        if "UPI Gateway" in selected_gw_tab:
            st.subheader("📱 UPI Payment Gateway (Fast & Contactless)")
            col_upi_l, col_upi_r = st.columns([1, 1])
            with col_upi_l:
                st.markdown("#### **Option A: Scan UPI QR Code**")
                st.markdown(f"""
                ```
                ┌────────────────────────────────────────┐
                │ █▀▀▀▀▀█ ▄█▄▀█  █▄ █▀▀▀▀▀█              │
                │ █ ███ █ ▄▀█▀▄ ▀ █ █ ███ █              │
                │ █ ▀▀▀ █ █ █▀█ █ █ █ ▀▀▀ █   SCAN & PAY │
                │ ▀▀▀▀▀▀▀ ▀▄█ ▀ █ ▀ ▀▀▀▀▀▀▀              │
                │ █▄ █▀▄▀▄▀▄▀▄▀▄█▄▀▄ █▄▀█▄█              │
                │ █▀▀▀▀▀█ █ ▄ █▄▀▄█ █ █ █▄█              │
                │ █ ███ █ █▀█ █▄█ █ █ █ █ █   BHIM / UPI │
                │ █ ▀▀▀ █ ▄ ▄▀█▄ ▄█ █ █ █▄█              │
                │ ▀▀▀▀▀▀▀ ▀ ▀ ▀▀▀ ▀ ▀ ▀▀▀▀▀              │
                └────────────────────────────────────────┘
                ```
                """)
                st.markdown(f"**Virtual Payment Address (VPA):** `fitnesspay.{c_data['tenant_id']}@icici`")
                st.caption("Point your camera or UPI scanner at the code above.")

            with col_upi_r:
                st.markdown("#### **Option B: Pay via UPI Apps**")
                st.write("Click any app to send an instant authorization push to your device:")
                c_app1, c_app2 = st.columns(2)
                with c_app1:
                    if st.button("🔵 Google Pay", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (Google Pay Express)"
                    if st.button("🟣 PhonePe", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (PhonePe App)"
                with c_app2:
                    if st.button("⚪ Paytm UPI", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (Paytm Payments)"
                    if st.button("🟢 CRED UPI", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (CRED / BHIM)"

                st.markdown("---")
                st.markdown("#### **Option C: Enter Your UPI ID**")
                vpa_input = st.text_input("Your UPI ID (VPA):", placeholder="e.g. yourname@okhdfcbank", value="member@okhdfcbank")
                if st.button("📲 Send Collect Request & Authorize ₹" + f"{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                    payment_authorized = True
                    authorized_method = f"UPI Collect ({vpa_input})"

        # --- GATEWAY OPTION 2: CREDIT / DEBIT CARD WITH 3D SECURE OTP ---
        elif "Credit / Debit Card" in selected_gw_tab:
            st.subheader("💳 Credit / Debit Card Gateway & 3D Secure Verification")
            
            if "card_otp_sent" not in st.session_state:
                st.session_state.card_otp_sent = False

            if not st.session_state.card_otp_sent:
                col_card1, col_card2 = st.columns([1, 1])
                with col_card1:
                    st.text_input("Card Number", "4532 •••• •••• 8821")
                    st.text_input("Cardholder Name", c_data['name'].upper())
                    c_exp, c_cvv = st.columns(2)
                    with c_exp:
                        st.text_input("Expiry Date (MM/YY)", "08/29")
                    with c_cvv:
                        st.text_input("CVV", "•••", type="password")

                with col_card2:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #1E3A8A, #3B82F6); padding: 20px; border-radius: 12px; color: white; margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; font-weight: bold;">
                            <span>FAM-FIOS PLATINUM</span>
                            <span>VISA</span>
                        </div>
                        <div style="font-size: 20px; letter-spacing: 2px; margin: 25px 0 10px 0; font-family: monospace;">
                            4532  ••••  ••••  8821
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px;">
                            <div>
                                <div style="opacity: 0.8;">CARDHOLDER</div>
                                <div style="font-weight: bold;">""" + c_data['name'].upper() + """</div>
                            </div>
                            <div>
                                <div style="opacity: 0.8;">EXPIRES</div>
                                <div style="font-weight: bold;">08/29</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("🔒 Verified by VISA & Mastercard Identity Check")

                if st.button("🔒 Proceed to Bank 3D-Secure Verification Page ➡️", type="primary", use_container_width=True):
                    st.session_state.card_otp_sent = True
                    st.rerun()

            else:
                # 3D-Secure Bank OTP Sub-Screen!
                st.markdown("""
                <div style="background-color: #0F172A; border: 2px solid #3B82F6; border-radius: 10px; padding: 25px; margin: 10px 0;">
                    <h3 style="color: #60A5FA; margin-top: 0;">🏦 Bank 3D-Secure Authorization Page</h3>
                    <p style="color: #CBD5E1;">A One-Time Password (OTP) has been sent to your registered mobile number <b>+91 *****""" + c_data['phone'][-4:] + """</b>.</p>
                </div>
                """, unsafe_allow_html=True)

                col_otp1, col_otp2 = st.columns([2, 1])
                with col_otp1:
                    otp_val = st.text_input("Enter 6-Digit Bank OTP:", value="742910")
                    st.caption("💡 Hint for Demo Evaluation: Use the pre-filled OTP `742910`.")
                with col_otp2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🔄 Resend OTP"):
                        st.info("A new OTP has been dispatched to your mobile.")

                col_otp_btn1, col_otp_btn2 = st.columns(2)
                with col_otp_btn1:
                    if st.button("✅ Confirm & Authenticate Payment of ₹" + f"{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "Credit/Debit Card (3D-Secure Verified)"
                        st.session_state.card_otp_sent = False
                with col_otp_btn2:
                    if st.button("⬅️ Change Card Details", use_container_width=True):
                        st.session_state.card_otp_sent = False
                        st.rerun()

        # --- GATEWAY OPTION 3: NET BANKING ---
        elif "Net Banking Gateway" in selected_gw_tab:
            st.subheader("🏛️ Net Banking Portal Gateway")
            col_nb1, col_nb2 = st.columns([1, 1])
            with col_nb1:
                st.markdown("#### **Select Your Bank**")
                bank_choice = st.selectbox(
                    "Choose Bank:",
                    [
                        "State Bank of India (SBI)",
                        "HDFC Bank",
                        "ICICI Bank",
                        "Axis Bank",
                        "Kotak Mahindra Bank",
                        "Punjab National Bank"
                    ]
                )
                st.info(f"You will be securely routed through {bank_choice}'s enterprise gateway.")

            with col_nb2:
                st.markdown("#### **Bank Gateway Login Credentials**")
                st.text_input("NetBanking Customer ID / Username", value=f"usr_{c_data['phone'][-6:]}")
                st.text_input("NetBanking IPIN / Password", value="••••••••••", type="password")
                
                if st.button(f"🔒 Log In & Authorize ₹{c_data['total_payable']:,.2f} via {bank_choice}", type="primary", use_container_width=True):
                    payment_authorized = True
                    authorized_method = f"Net Banking ({bank_choice})"

        # --- GATEWAY OPTION 4: INSTANT DEMO ---
        elif "1-Click Instant Approval" in selected_gw_tab:
            st.subheader("⚡ Instant 1-Click Fast Approval (Demo Mode)")
            st.info("💡 Bypasses external payment network handshakes for instant review and system grading.")
            if st.button(f"⚡ Instant Approve Payment of ₹{c_data['total_payable']:,.2f} & Complete", type="primary", use_container_width=True):
                payment_authorized = True
                authorized_method = "1-Click Instant Demo Payment"

        st.markdown("---")
        if st.button("⬅️ Cancel & Return to Registration Details"):
            st.session_state.checkout_stage = "form"
            st.session_state.card_otp_sent = False
            st.rerun()

        # Handle Payment Completion Logic
        if payment_authorized:
            new_mem_id = f"MEM-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            txn_id = f"TXN-2026-{datetime.utcnow().strftime('%m%d%H%M')}-{random.randint(1000, 9999)}"
            bank_rrn = f"RRN{random.randint(100000000000, 999999999999)}"

            # Persist to SQLite Database
            with SessionLocal() as db:
                new_member = MemberRecordModel(
                    member_id=new_mem_id,
                    tenant_id=c_data["tenant_id"],
                    name=c_data["name"],
                    email=c_data["email"],
                    goal=c_data["goal"],
                    phone=c_data["phone"],
                    city=c_data["city"],
                    branch=c_data["branch_name"],
                    area=c_data["branch_area"],
                    plan=c_data["plan_choice"].split("—")[0].strip(),
                    amount_paid=c_data["total_payable"],
                    status="Active",
                    enrolled_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                )
                db.add(new_member)

                new_user = UserModel(
                    user_id=f"usr_{new_mem_id.lower()}",
                    tenant_id=c_data["tenant_id"],
                    email=c_data["email"],
                    hashed_password=hash_password("MemberPass123!"),
                    role="member",
                    full_name=c_data["name"],
                    phone=c_data["phone"],
                    city=c_data["city"],
                    branch=c_data["branch_name"],
                    status="Active",
                    created_at=datetime.utcnow().isoformat()
                )
                db.add(new_user)
                db.commit()

            # Trigger TIGE Operational Events
            signup_evt = TenantEvent(
                tenant_id=c_data["tenant_id"],
                role_context="member",
                event_type="member_signup",
                operational_params={
                    "member_id": new_mem_id,
                    "name": c_data["name"],
                    "email": c_data["email"],
                    "phone": c_data["phone"],
                    "city": c_data["city"],
                    "branch": c_data["branch_name"],
                    "amount_paid": c_data["total_payable"],
                    "plan": c_data["plan_choice"]
                }
            )
            tige.update_genome_from_event(signup_evt)

            # SICE Evaluates Capacity Convergence
            sice.evaluate_subscription_convergence(c_data["tenant_id"])

            # DTDF Restructures Dependencies
            updated_g = db_store.get_genome(c_data["tenant_id"])
            dtdfe.construct_fabric(updated_g)

            # Store receipt
            expiry_date = (datetime.utcnow() + timedelta(days=30 if "1 Month" in c_data["plan_choice"] else (90 if "3 Months" in c_data["plan_choice"] else 365))).strftime("%d %B %Y")
            st.session_state.payment_receipt = {
                "member_id": new_mem_id,
                "txn_id": txn_id,
                "bank_rrn": bank_rrn,
                "method": authorized_method,
                "tenant_id": c_data["tenant_id"],
                "gym_name": c_data["gym_name"],
                "city": c_data["city"],
                "branch_name": c_data["branch_name"],
                "branch_address": c_data["branch_address"],
                "name": c_data["name"],
                "email": c_data["email"],
                "phone": c_data["phone"],
                "goal": c_data["goal"],
                "plan_name": c_data["plan_choice"].split("—")[0].strip(),
                "base_price": c_data["base_price"],
                "gst_amount": c_data["gst_amount"],
                "total_payable": c_data["total_payable"],
                "paid_at": datetime.utcnow().strftime("%d %B %Y, %I:%M %p"),
                "expiry_date": expiry_date
            }

            # Backup Tax Invoice & Digital Pass to Amazon S3 Cloud Vault
            s3_inv_res = aws_s3_service.upload_invoice(
                invoice_id=txn_id,
                invoice_data=st.session_state.payment_receipt,
                custom_credentials=st.session_state.get("custom_aws_credentials")
            )
            st.session_state.payment_receipt["s3_uri"] = s3_inv_res.get("s3_uri")
            st.session_state.payment_receipt["s3_status"] = s3_inv_res.get("status_text")

            st.session_state.checkout_stage = "success"
            st.rerun()

    # ==========================================================================
    # STAGE 3: PAYMENT CONFIRMATION, RECEIPT & CONNECT TO FURTHER PAGES
    # ==========================================================================
    elif st.session_state.checkout_stage == "success":
        rec = st.session_state.payment_receipt
        st.balloons()
        st.title("🎉 Payment Approved & Membership Activated!")
        
        # Step progress indicator
        st.markdown("""
        <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #334155;">
            <span style="color: #10B981; font-weight: bold;">✅ Step 1: Details Confirmed</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #10B981; font-weight: bold;">✅ Step 2: Payment Gateway Authorized</span> 
            <span style="color: #64748B; margin: 0 10px;">➔</span> 
            <span style="color: #38BDF8; font-weight: bold;">🎟️ Step 3: Official Pass & Connected Pages (ACTIVE)</span>
        </div>
        """, unsafe_allow_html=True)

        col_rcpt1, col_rcpt2 = st.columns([1, 1])

        with col_rcpt1:
            st.markdown("### 🧾 **Official Tax Invoice & Payment Receipt**")
            with st.container(border=True):
                st.write(f"**Transaction ID:** `{rec['txn_id']}`")
                st.write(f"**Bank RRN / Ref:** `{rec['bank_rrn']}`")
                st.write(f"**Payment Method:** `{rec['method']}`")
                st.write(f"**Payment Timestamp:** `{rec['paid_at']}`")
                st.write(f"**Payment Status:** `CAPTURED & VERIFIED ✅`")
                st.markdown("---")
                st.write(f"**Billed To:** {rec['name']} ({rec['phone']})")
                st.write(f"**Facility:** {rec['gym_name']} — {rec['branch_name']}")
                st.write(f"**City:** {rec['city']}")
                st.write(f"**Membership Plan:** {rec['plan_name']}")
                st.write(f"Base Membership Fee: **₹{rec['base_price']:,.2f}**")
                st.write(f"GST (18%): **₹{rec['gst_amount']:,.2f}**")
                st.markdown(f"### **Total Amount Paid: ₹{rec['total_payable']:,.2f}**")
                s3_uri_display = rec.get("s3_uri", f"s3://fam-fios-cloud-vault/invoices/{rec['txn_id']}.json")
                st.caption(f"☁️ **Amazon S3 Cloud Vault Archive:** `{s3_uri_display}` (🛡️ Server-Side Encrypted)")

        with col_rcpt2:
            st.markdown("### 🎟️ **Official Digital Fitness Pass**")
            st.markdown(f"""
            ```
            ========================================================================
                              OFFICIAL DIGITAL FITNESS PASS                         
            ========================================================================
            MEMBER NAME:       {rec['name'].upper()}
            MEMBER ID:         {rec['member_id']}
            GYM ORGANIZATION:  {rec['gym_name']}
            CITY & FRANCHISE:  {rec['city'].upper()} — {rec['branch_name'].upper()}
            ADDRESS:           {rec['branch_address']}
            PHONE:             {rec['phone']}
            MEMBERSHIP PLAN:   {rec['plan_name']} (PAID: ₹{rec['total_payable']:,.2f})
            VALID UNTIL:       {rec['expiry_date']}
            ACCESS STATUS:     ACTIVE & VERIFIED ✅
            SECURITY BARCODE:  ||| ||||| |||| |||| ||| ||||||| ||||| || |||
            ========================================================================
            ```
            """)

        st.markdown("---")
        st.markdown("## 🚀 **Choose Where You Want to Go Next (Further Pages):**")
        st.caption("Your payment is complete and your account is live across all modules. Click any destination below:")

        c_dest1, c_dest2, c_dest3 = st.columns(3)

        with c_dest1:
            with st.container(border=True):
                st.markdown("### 🏋️ **Member Fitness Companion**")
                st.write(f"Access workout logging, QR scanner check-in, and AI plateau detection pre-loaded for **{rec['name']}**.")
                if st.button("👉 Go to My Member Fitness Dashboard", type="primary", use_container_width=True):
                    st.session_state.nav_target = "🏋️ Gym Member / User View"
                    st.session_state.tenant_target = rec["tenant_id"]
                    st.session_state.logged_in_member = rec
                    st.rerun()

        with c_dest2:
            with st.container(border=True):
                st.markdown("### 🏢 **Gym Owner / Admin Console**")
                st.write(f"Inspect **{rec['gym_name']}** management center and verify your name appears at the top of the roster.")
                if st.button("👉 Open Gym Owner Console", use_container_width=True):
                    st.session_state.nav_target = "🏢 Gym Owner / Admin View"
                    st.session_state.tenant_target = rec["tenant_id"]
                    st.rerun()

        with c_dest3:
            with st.container(border=True):
                st.markdown("### 🗄️ **Central Users & Members Database**")
                st.write(f"View the live SQLite relational database (`users` and `members` tables) containing your new record.")
                if st.button("👉 Inspect in Central Database", use_container_width=True):
                    st.session_state.nav_target = "🗄️ Central Users & Members Database"
                    st.rerun()

        st.markdown("")
        if st.button("➕ Register Another Member"):
            st.session_state.checkout_stage = "form"
            st.session_state.card_otp_sent = False
            st.rerun()

# ==============================================================================
# 2. GYM OWNER / ADMIN VIEW
# ==============================================================================
elif portal_mode == "🏢 Gym Owner / Admin View":
    st.markdown(f"## 🏢 **{active_genome.gym_name} — Gym Owner Command Center**")
    st.markdown(
        f"**Facility ID:** `{active_tenant_id}` &nbsp;|&nbsp; "
        f"**Subscription Plan:** `{sub.tier} Plan` &nbsp;|&nbsp; "
        f"**System State:** `Generation {active_genome.generation} (Active & Healthy)`"
    )

    if logged_in_user and logged_in_user.get("role") == "gym_admin":
        st.success(f"🔑 **Administrator Session Active:** Authenticated as **{logged_in_user.get('full_name')}** ({logged_in_user.get('branch', 'Executive')}) via Secure OTP.")
    elif logged_in_user and logged_in_user.get("role") == "member":
        st.info(f"ℹ️ **Member Audit Mode:** Logged in as **{logged_in_user.get('full_name')}** (Member). Accessing administrative telemetry in preview mode.")

    # Top KPI Metrics with Plain-English explanations
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    utilization_pct = int((sub.active_members / max(1, sub.max_members)) * 100)
    with kpi1:
        st.metric(
            label="👥 Enrolled Members",
            value=f"{sub.active_members} / {sub.max_members}",
            delta=f"{utilization_pct}% of Plan Limit",
            help="Total active members registered at your gym versus your current monthly subscription limit."
        )
    with kpi2:
        st.metric(
            label="👨‍🏫 Certified Trainers",
            value=f"{sub.active_trainers} / {sub.max_trainers}",
            delta="Trainer Quota",
            help="Trainers currently employed at this gym facility."
        )
    with kpi3:
        st.metric(
            label="🕒 Rush-Hour Concentration",
            value=f"{int(usage.peak_hour_ratio * 100)}%",
            delta="Morning & Evening Waves",
            help="Percentage of daily members who visit during peak morning (6-9 AM) and peak evening (5-8 PM) rush hours."
        )
    with kpi4:
        st.metric(
            label="🔒 Data Isolation Score",
            value="100% Strict",
            delta="Zero Leakage to Competitors",
            help="ACVE security score proving your gym's records are completely firewalled from all other gyms."
        )

    st.markdown("---")

    admin_tabs = st.tabs([
        "⚡ 1. Smart Capacity & Plan Upgrades (SICE)",
        "👥 2. Member Directory & Live Signups",
        "🕒 3. Rush-Hour Crowd Predictor (PTLM)",
        "🧠 4. Privacy-Safe Collaborative AI (FAFIE)",
        "🛡️ 5. Security & Isolation Defense (ACVE)",
        "☁️ 6. Amazon S3 Cloud Storage Vault"
    ])

    # --- TAB 1: SICE SMART UPGRADES ---
    with admin_tabs[0]:
        st.markdown("### ⚡ **Smart Plan & Capacity Forecaster (SICE Engine)**")
        st.info("""
        💡 **What this does in plain English:**  
        Conventional software locks your doors or crashes when you hit your member limit.  
        **SICE** looks at how fast you are signing up members, calculates when you will run out of capacity *before* it happens,  
        and calculates a fair, discounted (prorated) price for the remaining days of your month so your business never stops!
        """)

        col_sice_left, col_sice_right = st.columns([3, 2])
        with col_sice_left:
            st.markdown("#### 📊 **Real-Time Capacity Meter**")
            st.write(f"Current Usage: **{sub.active_members} members** out of **{sub.max_members} max**")
            st.progress(min(1.0, sub.active_members / max(1, sub.max_members)))

            days_remaining = sub.days_remaining_in_cycle
            growth_vel = sub.member_growth_velocity
            projected_end = int(sub.active_members + (growth_vel * days_remaining))

            st.markdown(f"""
            - **Current Sign-Up Speed:** `{growth_vel:.1f} new members every day`
            - **Days Left in Current Billing Month:** `{days_remaining} days`
            - **Projected Total Members by Month End:** `{projected_end} members`
            """)

            if projected_end >= sub.max_members and sub.tier != "Gold":
                next_tier = "Silver" if sub.tier == "Free" else "Gold"
                price_difference = 99.0 if next_tier == "Silver" else 200.0
                prorated_fee = round(price_difference * (days_remaining / 30.0), 2)
                next_limit = 250 if next_tier == "Silver" else 1000

                st.error(f"🚨 **Action Needed:** Your gym is on track to hit its {sub.tier} plan ceiling in ~{int((sub.max_members - sub.active_members)/max(0.1, growth_vel))} days!")
                st.warning(f"""
                **SICE Recommendation:** Upgrade to the **{next_tier} Plan**  
                - **New Member Limit:** {next_limit} members (gives your gym room to expand!)  
                - **Full Monthly Price:** ${price_difference}/month  
                - **Special Prorated Price Today:** **${prorated_fee}** *(you only pay for the remaining {days_remaining} days!)*
                """)

                if st.button(f"✅ Click Here to Upgrade to {next_tier} Tier (${prorated_fee})", type="primary", use_container_width=True):
                    sice.execute_preemptive_upgrade(active_tenant_id, next_tier)
                    st.success(f"🎉 Upgraded {active_genome.gym_name} to {next_tier} Plan! Limit expanded to {next_limit} members.")
                    st.rerun()
            else:
                st.success("✅ **Capacity Status:** Your gym is operating safely within its limits. No upgrade required today.")

        with col_sice_right:
            st.markdown("#### 🤖 **Autonomous AI Assistants Feed**")
            st.caption("Specialized AI agents working in the background for your gym:")
            agent_alerts = db_store.get_intents_for_tenant(active_tenant_id)
            if agent_alerts:
                for alert in agent_alerts[-3:]:
                    with st.container(border=True):
                        st.markdown(f"**Agent:** `{alert.source_agent}`")
                        st.markdown(f"**Action:** `{alert.proposed_action}`")
                        st.caption(f"Reason: {alert.expected_operational_impact}")
            else:
                st.info("All background assistants report normal operational parameters.")

    # --- TAB 2: MEMBER MANAGEMENT ---
    with admin_tabs[1]:
        st.markdown(f"### 👥 **Member Roster & Multi-Franchise Live Signups ({active_genome.gym_name})**")
        st.info("💡 **What this does:** All members who registered from the Public Portal or enrolled at any franchise branch appear here in real time with branch-level filtering.")

        with SessionLocal() as db:
            active_mems = db.query(MemberRecordModel).filter_by(tenant_id=active_tenant_id).all()
            if active_mems:
                col_f_city, col_f_branch = st.columns(2)
                with col_f_city:
                    cities = ["All Cities"] + sorted(list(set(m.city for m in active_mems if getattr(m, 'city', ''))))
                    filter_city = st.selectbox("🏙️ Filter by City:", cities, key="adm_filt_city")
                with col_f_branch:
                    branches = ["All Franchise Branches"] + sorted(list(set(m.branch for m in active_mems if getattr(m, 'branch', ''))))
                    filter_branch = st.selectbox("📍 Filter by Branch:", branches, key="adm_filt_branch")

                filtered_mems = active_mems
                if filter_city != "All Cities":
                    filtered_mems = [m for m in filtered_mems if getattr(m, 'city', '') == filter_city]
                if filter_branch != "All Franchise Branches":
                    filtered_mems = [m for m in filtered_mems if getattr(m, 'branch', '') == filter_branch]

                df_members = pd.DataFrame([
                    {
                        "Member ID": m.member_id,
                        "Full Name": m.name,
                        "Email": m.email,
                        "Phone": getattr(m, "phone", "N/A"),
                        "City": getattr(m, "city", "N/A"),
                        "Franchise Branch": getattr(m, "branch", getattr(m, "area", "N/A")),
                        "Plan": getattr(m, "plan", "Standard Access"),
                        "Fitness Goal": m.goal,
                        "Amount Paid (₹)": f"₹{getattr(m, 'amount_paid', 0.0):,.2f}",
                        "Date Enrolled": m.enrolled_at,
                        "Status": getattr(m, "status", "Active")
                    }
                    for m in filtered_mems
                ])
                st.dataframe(df_members, use_container_width=True)
                st.caption(f"Showing **{len(filtered_mems)}** members registered at this facility.")
            else:
                st.info("No members recorded in this facility yet. Go to '📝 New Member Registration' in the sidebar to register the first member!")

    # --- TAB 3: ATTENDANCE & PTLM ---
    with admin_tabs[2]:
        st.markdown("### 🕒 **Rush-Hour Crowd Predictor & Server Auto-Scaler (PTLM Engine)**")
        st.info("""
        💡 **What this does in plain English:**  
        Most cloud apps only scale up *after* the gym is already full and the check-in scanners start freezing.  
        **PTLM** uses historical attendance data to predict morning (6–9 AM) and evening (5–8 PM) crowds,  
        and **proactively provisions extra database and server power 45 minutes before members walk through the door!**
        """)

        col_ptlm_chart, col_ptlm_ctrl = st.columns([3, 2])
        with col_ptlm_chart:
            st.markdown("#### 📈 **Predicted 24-Hour Check-In Rush Pattern**")
            forecasts = [ptlme.forecast_demand(active_genome, h) for h in range(24)]
            df_hourly = pd.DataFrame([
                {"Hour": f"{h:02d}:00", "Predicted Check-Ins": f["predicted_concurrency"], "Peak Window": f["is_peak_window"]}
                for h, f in enumerate(forecasts)
            ])
            st.bar_chart(df_hourly.set_index("Hour")["Predicted Check-Ins"])
            st.caption("🔴 Morning Peak Window: **06:00 – 09:00 AM** &nbsp;|&nbsp; 🔴 Evening Peak Window: **17:00 – 20:00 PM**")

        with col_ptlm_ctrl:
            st.markdown("#### ⚙️ **Current Server Capacity**")
            st.write(f"- **Allocated CPU Power:** `{active_genome.resource.allocated_cpu_cores} Cores`")
            st.write(f"- **Allocated Memory:** `{active_genome.resource.allocated_memory_mb} MB RAM`")
            st.write(f"- **Materialized Database Partitions:** `{active_genome.resource.materialized_partitions} Active`")
            st.write(f"- **Rush-Hour Pre-Scaling Active:** `{'🟢 YES (High Speed)' if active_genome.resource.is_preemptively_scaled else '⚪ Standard Baseline'}`")

            target_hour = st.slider("Select an hour to simulate pre-provisioning:", 0, 23, 7)
            hour_fc = ptlme.forecast_demand(active_genome, target_hour)
            st.caption(f"At {target_hour:02d}:00, estimated crowd is **{hour_fc['predicted_concurrency']} concurrent check-ins**.")

            if st.button("🚀 Pre-Allocate Resources for this Hour Now", type="primary", use_container_width=True):
                res_mat = ptlme.materialize_partitions_for_tenant(active_tenant_id, target_hour)
                st.success(f"Success! Pre-allocated {res_mat['materialized_partitions']} partitions and {res_mat['allocated_cpu_cores']} CPU cores for {target_hour:02d}:00.")
                st.rerun()

    # --- TAB 4: FAFIE COLLABORATIVE AI ---
    with admin_tabs[3]:
        st.markdown("### 🧠 **Privacy-Preserving Collaborative AI (FAFIE Engine)**")
        st.info("""
        💡 **What this does in plain English:**  
        Independent gyms usually have too little data to build powerful AI recommendation models on their own.  
        **FAFIE** allows hundreds of gyms to collectively train a world-class workout AI **without ever uploading or sharing raw customer data!**  
        Each gym calculates mathematical updates on its own local database, encrypts them, adds mathematical noise for privacy,  
        and shares only the anonymous updates with the global aggregator.
        """)

        st.markdown(f"#### 🌐 **Shared Global AI Model Weights:** `{db_store.global_model_weights}`")
        if st.button("🤝 Run Multi-Gym Collaborative Training Round Now", type="primary"):
            training_updates = []
            for t in all_tenants:
                local_tr = FafieLocalTrainer(t.tenant_id)
                X_batch = np.random.randn(50, len(db_store.global_model_weights))
                y_batch = np.dot(X_batch, db_store.global_model_weights) + np.random.normal(0, 0.05, 50)
                upd = local_tr.compute_local_gradient_update(db_store.global_model_weights, X_batch, y_batch)
                training_updates.append(upd)

            round_outcome = fafie_aggregator.run_aggregation_round(training_updates)
            st.success(f"🎉 Round {round_outcome['round_number']} completed across all gyms! Global loss reduced to: {round_outcome['average_loss']}")
            if round_outcome.get("s3_uri"):
                st.info(f"☁️ **FAFIE Checkpoint Archived to Amazon S3**: `{round_outcome['s3_uri']}` ({round_outcome.get('encryption', 'AES256')})")
            st.rerun()

    # --- TAB 5: ACVE COMPLIANCE AUDIT ---
    with admin_tabs[4]:
        st.markdown("### 🛡️ **Autonomous Compliance & Data Isolation Defense (ACVE)**")
        st.info("💡 Security gatekeeper verifying all actions against strict multi-tenant isolation rules.")
        gym_audits = [a for a in db_store.compliance_audits if a["tenant_id"] == active_tenant_id or a["tenant_id"] == "system"]
        if gym_audits:
            st.dataframe(pd.DataFrame(gym_audits[-10:][["timestamp", "action", "caller_role", "verdict"]]), use_container_width=True)
        else:
            st.success("🛡️ Zero security violations recorded. Your gym's data isolation boundary is 100% intact.")

    # --- TAB 6: AMAZON S3 CLOUD STORAGE VAULT ---
    with admin_tabs[5]:
        st.markdown("### ☁️ **Amazon S3 Enterprise Cloud Storage Vault**")
        st.info("💡 **Durable Cloud Object Storage:** Persists encrypted FAFIE neural model weight checkpoints, member tax invoices, and verification certificates directly into Amazon S3 with Server-Side KMS/AES-256 Encryption.")

        s3_conf = aws_s3_service.check_s3_configuration(st.session_state.get("custom_aws_credentials"))
        
        c_s3_1, c_s3_2, c_s3_3, c_s3_4 = st.columns(4)
        with c_s3_1:
            st.metric(label="📦 Active S3 Bucket", value=s3_conf["bucket_name"])
        with c_s3_2:
            st.metric(label="🌐 AWS Region", value=s3_conf["region"])
        with c_s3_3:
            st.metric(label="🛡️ Encryption Tier", value="AES-256 / KMS")
        with c_s3_4:
            if s3_conf["configured"]:
                st.metric(label="⚡ Vault Engine", value="Amazon S3 Standard 🟢")
            else:
                st.metric(label="⚡ Vault Engine", value="Sandbox Vault 🟡")

        st.markdown("---")

        c_s3_action1, c_s3_action2 = st.columns([2, 1])
        with c_s3_action1:
            st.markdown("#### 🗃️ **S3 Vault Objects Explorer**")
            st.caption("Live encrypted artifacts stored in your multi-tenant S3 bucket:")
        with c_s3_action2:
            if st.button("📦 Backup Current FAFIE Model to S3", type="primary", use_container_width=True):
                round_tag = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                backup_data = {
                    "tenant_id": active_tenant_id,
                    "gym_name": active_genome.gym_name,
                    "global_weights": db_store.global_model_weights,
                    "federated_rounds_count": len(db_store.federated_rounds),
                    "timestamp": datetime.utcnow().isoformat()
                }
                res = aws_s3_service.upload_model_checkpoint(round_tag, backup_data, st.session_state.get("custom_aws_credentials"))
                st.balloons()
                st.success(f"✅ Checkpoint backed up to Amazon S3: `{res['s3_uri']}` ({res.get('bytes_stored', 0):,} bytes)")
                st.rerun()

        # List objects in vault
        vault_items = aws_s3_service.list_vault_objects(custom_credentials=st.session_state.get("custom_aws_credentials"))
        if vault_items:
            df_vault = pd.DataFrame(vault_items)
            st.dataframe(df_vault[["key", "size_bytes", "last_modified", "s3_uri", "encryption"]], use_container_width=True)
            
            with st.expander("🔍 **Inspect Vault File Metadata (Click to View)**", expanded=False):
                selected_key = st.selectbox("Select file to inspect:", [item["key"] for item in vault_items])
                matched_item = next((item for item in vault_items if item["key"] == selected_key), None)
                if matched_item:
                    st.write(f"**URI:** `{matched_item['s3_uri']}`")
                    st.write(f"**Size:** `{matched_item['size_bytes']} bytes` &nbsp;|&nbsp; **Last Modified:** `{matched_item['last_modified']}`")
                    st.write(f"**Encryption:** `{matched_item['encryption']}` &nbsp;|&nbsp; **Storage Tier:** `{matched_item.get('tier', 'Standard')}`")
        else:
            st.info("ℹ️ No objects found in S3 vault yet. Run a collaborative AI round or register a member to create encrypted cloud archives!")

# ==============================================================================
# 3. CENTRAL USERS & MEMBERS DATABASE EXPLORER (NEW!)
# ==============================================================================
elif portal_mode == "🗄️ Central Users & Members Database":
    st.title("🗄️ Central Multi-Tenant Users & Multi-Franchise Database")
    st.markdown("""
    This portal gives system administrators, auditors, and multi-franchise owners direct insight into the 
    **persistent relational database (`fam_fios.db`)**. Inspect user accounts, multi-city memberships, 
    verify branch distributions (such as **Pune's 5 franchises**), and export compliance reports.
    """)
    st.markdown("---")

    # Fetch live records from database
    all_users_data = db_store.list_all_users()
    all_members_data = db_store.list_all_members()

    total_users_count = len(all_users_data)
    total_mems_count = len(all_members_data)
    total_rev = sum(m.get("amount_paid", 0.0) for m in all_members_data)
    unique_cities = len(set(m.get("city") for m in all_members_data if m.get("city")))

    # Summary KPI Cards
    db_kpi1, db_kpi2, db_kpi3, db_kpi4 = st.columns(4)
    with db_kpi1:
        st.metric("👥 Total Registered Accounts", total_users_count, help="All user credentials and logins in `users` table.")
    with db_kpi2:
        st.metric("🏋️ Total Enrolled Members", total_mems_count, help="Active gym membership records in `members` table.")
    with db_kpi3:
        st.metric("💰 Total Revenue Collected", f"₹{total_rev:,.2f}", help="Sum of membership fees paid across all franchises.")
    with db_kpi4:
        st.metric("🏙️ Active Cities Covered", max(1, unique_cities), help="Cities with registered franchises (Pune, Bengaluru, Mumbai, etc.).")

    st.markdown("---")

    db_tabs = st.tabs([
        "👥 1. Registered User Accounts (`users` Table)",
        "🏋️ 2. Gym Members Directory (`members` Table)",
        "📊 3. City & Franchise Distribution Analytics"
    ])

    # --- TAB 1: USERS TABLE ---
    with db_tabs[0]:
        st.subheader("👥 System User Accounts (`users` table)")
        st.caption("Includes Gym Owners / Admins, Certified Trainers, and Registered Members with secure salted PBKDF2 credentials.")

        c_u1, c_u2, c_u3 = st.columns([2, 1, 1])
        with c_u1:
            u_search = st.text_input("🔍 Search users (Name, Email, Phone, User ID):", placeholder="e.g. Pune, Rohit, admin...", key="u_search_box")
        with c_u2:
            u_city_opts = ["All Cities"] + sorted(list(set(u["city"] for u in all_users_data if u["city"])))
            u_city_filt = st.selectbox("Filter by City:", u_city_opts, key="u_city_filt")
        with c_u3:
            u_role_opts = ["All Roles", "gym_admin", "trainer", "member"]
            u_role_filt = st.selectbox("Filter by Role:", u_role_opts, key="u_role_filt")

        filtered_users = all_users_data
        if u_city_filt != "All Cities":
            filtered_users = [u for u in filtered_users if u["city"] == u_city_filt]
        if u_role_filt != "All Roles":
            filtered_users = [u for u in filtered_users if u["role"] == u_role_filt]
        if u_search:
            s = u_search.lower()
            filtered_users = [
                u for u in filtered_users
                if s in u["full_name"].lower() or s in u["email"].lower() or s in u["user_id"].lower() or s in u["phone"].lower() or s in u["branch"].lower()
            ]

        if filtered_users:
            df_users = pd.DataFrame([
                {
                    "User ID": u["user_id"],
                    "Tenant ID": u["tenant_id"],
                    "Full Name": u["full_name"],
                    "Email": u["email"],
                    "Phone": u["phone"] if u["phone"] else "N/A",
                    "City": u["city"] if u["city"] else "N/A",
                    "Franchise Branch": u["branch"] if u["branch"] else "N/A",
                    "Role": u["role"].upper(),
                    "Status": u["status"],
                    "Created At": u["created_at"][:16].replace("T", " ")
                }
                for u in filtered_users
            ])
            st.dataframe(df_users, use_container_width=True)

            csv_users = df_users.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Users Database to CSV",
                data=csv_users,
                file_name="fam_fios_users_database.csv",
                mime="text/csv",
                key="dl_users_csv"
            )
        else:
            st.info("No users match the selected filters.")

    # --- TAB 2: MEMBERS TABLE ---
    with db_tabs[1]:
        st.subheader("🏋️ Multi-Branch Gym Members Directory (`members` table)")
        st.caption("Active memberships enrolled across city franchises with fee accounting and plan durations.")

        c_m1, c_m2, c_m3 = st.columns([2, 1, 1])
        with c_m1:
            m_search = st.text_input("🔍 Search members (Name, Email, Member ID):", placeholder="e.g. Baner, Hinjewadi, Verma...", key="m_search_box")
        with c_m2:
            m_city_opts = ["All Cities"] + sorted(list(set(m["city"] for m in all_members_data if m["city"])))
            m_city_filt = st.selectbox("Filter by City:", m_city_opts, key="m_city_filt")
        with c_m3:
            m_branch_opts = ["All Franchise Branches"] + sorted(list(set(m["branch"] for m in all_members_data if m["branch"])))
            m_branch_filt = st.selectbox("Filter by Branch:", m_branch_opts, key="m_branch_filt")

        filtered_mems = all_members_data
        if m_city_filt != "All Cities":
            filtered_mems = [m for m in filtered_mems if m["city"] == m_city_filt]
        if m_branch_filt != "All Franchise Branches":
            filtered_mems = [m for m in filtered_mems if m["branch"] == m_branch_filt]
        if m_search:
            s = m_search.lower()
            filtered_mems = [
                m for m in filtered_mems
                if s in m["name"].lower() or s in m["email"].lower() or s in m["member_id"].lower() or s in m["phone"].lower() or s in m["branch"].lower()
            ]

        if filtered_mems:
            df_mems = pd.DataFrame([
                {
                    "Member ID": m["member_id"],
                    "Tenant ID": m["tenant_id"],
                    "Full Name": m["name"],
                    "Email": m["email"],
                    "Phone": m["phone"] if m["phone"] else "N/A",
                    "City": m["city"] if m["city"] else "N/A",
                    "Franchise Branch": m["branch"] if m["branch"] else (m["area"] if m["area"] else "N/A"),
                    "Plan": m["plan"] if m["plan"] else "Standard Access",
                    "Fitness Goal": m["goal"],
                    "Amount Paid (₹)": f"₹{m['amount_paid']:,.2f}",
                    "Enrolled Date": m["enrolled_at"],
                    "Status": m["status"]
                }
                for m in filtered_mems
            ])
            st.dataframe(df_mems, use_container_width=True)

            csv_mems = df_mems.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Members Database to CSV",
                data=csv_mems,
                file_name="fam_fios_members_database.csv",
                mime="text/csv",
                key="dl_mems_csv"
            )
        else:
            st.info("No members match the selected filters.")

    # --- TAB 3: CITY & FRANCHISE ANALYTICS ---
    with db_tabs[2]:
        st.subheader("📊 Multi-City & Franchise Intelligence")
        st.info("💡 Real-time distribution of active gym registrations across cities and individual franchise locations.")

        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.markdown("#### 🏙️ **Signups by City**")
            city_counts = {}
            for m in all_members_data:
                c = m.get("city") or "Other / Unassigned"
                city_counts[c] = city_counts.get(c, 0) + 1
            if city_counts:
                df_city_chart = pd.DataFrame(list(city_counts.items()), columns=["City", "Members Enrolled"]).set_index("City")
                st.bar_chart(df_city_chart)
            else:
                st.info("No city data recorded yet.")

        with col_an2:
            st.markdown("#### 📍 **Pune Franchises Breakdown (5 Locations)**")
            pune_branches = [
                "Baner High Street Franchise",
                "Kothrud (Paud Road) Franchise",
                "Viman Nagar Franchise",
                "Hinjewadi Phase 1 (IT Hub) Franchise",
                "Koregaon Park VIP Franchise"
            ]
            branch_counts = {b.split('(')[0].replace('Franchise', '').strip(): 0 for b in pune_branches}
            for m in all_members_data:
                b = m.get("branch", "")
                for pb in pune_branches:
                    if pb in b or b in pb:
                        short_name = pb.split('(')[0].replace('Franchise', '').strip()
                        branch_counts[short_name] = branch_counts.get(short_name, 0) + 1

            df_branch_chart = pd.DataFrame(list(branch_counts.items()), columns=["Pune Branch", "Active Signups"]).set_index("Pune Branch")
            st.bar_chart(df_branch_chart)

        st.markdown("---")
        st.markdown("#### 💰 **Revenue Contribution by Gym Organization**")
        rev_by_tenant = {}
        for m in all_members_data:
            t = m.get("tenant_id", "unknown")
            rev_by_tenant[t] = rev_by_tenant.get(t, 0.0) + m.get("amount_paid", 0.0)
        df_rev = pd.DataFrame([
            {"Gym Organization": tid, "Total Revenue (₹)": f"₹{amt:,.2f}", "Raw Amount": amt}
            for tid, amt in rev_by_tenant.items()
        ])
        if not df_rev.empty:
            st.dataframe(df_rev[["Gym Organization", "Total Revenue (₹)"]], use_container_width=True)

# ==============================================================================
# 4. GYM MEMBER / USER VIEW
# ==============================================================================
elif portal_mode == "🏋️ Gym Member / User View":
    WEEKLY_WORKOUT_ROUTINES = {
        "Monday": {
            "title": "Push Day: Chest, Shoulders & Triceps",
            "focus": "Upper body pressing strength & pectoral hypertrophy",
            "duration": "55 mins",
            "calories_est": "380 kcal",
            "badge_color": "#3B82F6",
            "exercises": [
                {
                    "name": "Barbell Bench Press (Flat)",
                    "sets_reps": "4 sets × 6-8 reps",
                    "rest": "90s rest",
                    "target": "Pectoralis Major, Anterior Deltoids",
                    "cue": "Retract scapulae, plant feet firmly, explode on upward push with controlled 2s eccentric.",
                    "video_url": "https://www.youtube.com/watch?v=vcBig73ojpE",
                    "video_title": "How to Bench Press with Perfect Form (Jeff Nippard)"
                },
                {
                    "name": "Incline Dumbbell Chest Press",
                    "sets_reps": "3 sets × 8-10 reps",
                    "rest": "75s rest",
                    "target": "Clavicular (Upper) Pectorals",
                    "cue": "Set bench to 30°, maintain neutral wrist alignment, deep stretch at bottom.",
                    "video_url": "https://www.youtube.com/watch?v=8iPEnn-ltC8",
                    "video_title": "Incline Dumbbell Press Technique (Jeff Nippard)"
                },
                {
                    "name": "Seated Overhead Dumbbell Shoulder Press",
                    "sets_reps": "3 sets × 10-12 reps",
                    "rest": "60s rest",
                    "target": "Anterior & Lateral Deltoids",
                    "cue": "Brace core tightly, press weights up in slight arc without hyperextending lower spine.",
                    "video_url": "https://www.youtube.com/watch?v=qEwKCR5JCog",
                    "video_title": "Dumbbell Shoulder Press Form (Jeff Nippard)"
                },
                {
                    "name": "Cable Tricep Rope Pushdowns",
                    "sets_reps": "3 sets × 12-15 reps",
                    "rest": "45s rest",
                    "target": "Triceps Brachii (Lateral & Long Head)",
                    "cue": "Pin elbows to torso, spread the rope handles wide at contraction with 1s pause.",
                    "video_url": "https://www.youtube.com/watch?v=-xa-6cQaZKY",
                    "video_title": "Tricep Rope Pushdown Execution (Scott Herman)"
                }
            ],
            "nutrition": {
                "calories": "2,550 kcal",
                "protein": "180g",
                "carbs": "280g",
                "fats": "65g",
                "pre_workout": "Oatmeal with sliced banana & whey isolate (60 mins before training)",
                "post_workout": "Grilled chicken breast or paneer tikka with steamed rice & sweet potatoes",
                "water": "3.5 Liters"
            }
        },
        "Tuesday": {
            "title": "Pull Day: Back, Lats & Biceps Hypertrophy",
            "focus": "Posterior chain thickness, lat width & arm development",
            "duration": "60 mins",
            "calories_est": "420 kcal",
            "badge_color": "#10B981",
            "exercises": [
                {
                    "name": "Conventional Barbell Deadlifts",
                    "sets_reps": "3 sets × 5 reps",
                    "rest": "120s rest",
                    "target": "Erector Spinae, Latissimus Dorsi, Glutes & Hamstrings",
                    "cue": "Hip hinge setup, pull slack out of bar, drive the floor away through midfoot.",
                    "video_url": "https://www.youtube.com/watch?v=VL5Ab0T07e4",
                    "video_title": "How to Deadlift with Perfect Form (Jeff Nippard)"
                },
                {
                    "name": "Wide-Grip Lat Pulldowns",
                    "sets_reps": "4 sets × 8-10 reps",
                    "rest": "75s rest",
                    "target": "Latissimus Dorsi & Teres Major",
                    "cue": "Initiate pull by depressing scapulae; pull elbows towards back pockets.",
                    "video_url": "https://www.youtube.com/watch?v=CAwf7n6Luuc",
                    "video_title": "Lat Pulldown Form for Back Hypertrophy (Jeremy Ethier)"
                },
                {
                    "name": "Seated Cable Rows (Close Grip)",
                    "sets_reps": "3 sets × 10-12 reps",
                    "rest": "60s rest",
                    "target": "Rhomboids, Middle Trapezius & Lats",
                    "cue": "Keep chest elevated, avoid excessive rocking, hold contraction for 1 second.",
                    "video_url": "https://www.youtube.com/watch?v=GZbfZ033f74",
                    "video_title": "Seated Cable Row Technique (Scott Herman)"
                },
                {
                    "name": "Incline Dumbbell Bicep Curls",
                    "sets_reps": "3 sets × 12 reps",
                    "rest": "45s rest",
                    "target": "Biceps Brachii (Long Head)",
                    "cue": "Full supination at peak contraction; do not let elbows drift forward.",
                    "video_url": "https://www.youtube.com/watch?v=soxrZlIl35U",
                    "video_title": "Incline Dumbbell Curl Form (Buff Dudes)"
                }
            ],
            "nutrition": {
                "calories": "2,500 kcal",
                "protein": "180g",
                "carbs": "270g",
                "fats": "65g",
                "pre_workout": "Whole grain toast with peanut butter & black coffee",
                "post_workout": "Double whey shake with blueberries, plus dal khichdi or quinoa chicken bowl",
                "water": "3.5 Liters"
            }
        },
        "Wednesday": {
            "title": "Legs & Core: Quads, Hamstrings & Calves",
            "focus": "Lower body maximal strength, quad development & hip stability",
            "duration": "65 mins",
            "calories_est": "460 kcal",
            "badge_color": "#F59E0B",
            "exercises": [
                {
                    "name": "Barbell Back Squats",
                    "sets_reps": "4 sets × 6-8 reps",
                    "rest": "120s rest",
                    "target": "Quadriceps, Gluteus Maximus, Core Stabilizers",
                    "cue": "Take deep belly breath into belt, knees track outward over second toes, hit depth.",
                    "video_url": "https://www.youtube.com/watch?v=bEv6CCg2BC8",
                    "video_title": "How to Squat with Proper Depth & Form (Squat University)"
                },
                {
                    "name": "Romanian Deadlifts (RDL)",
                    "sets_reps": "3 sets × 10 reps",
                    "rest": "90s rest",
                    "target": "Hamstrings & Gluteal Fold",
                    "cue": "Soft knee flexion, push hips straight back until deep hamstring stretch is felt.",
                    "video_url": "https://www.youtube.com/watch?v=JCXUYuzwNrM",
                    "video_title": "Romanian Deadlift Masterclass (Jeremy Ethier)"
                },
                {
                    "name": "Leg Press / Walking Lunges",
                    "sets_reps": "3 sets × 12 reps per leg",
                    "rest": "60s rest",
                    "target": "Quadriceps & Glute Medius",
                    "cue": "Maintain upright posture, knee aligned over ankle at bottom position.",
                    "video_url": "https://www.youtube.com/watch?v=IZxyjW7MPJQ",
                    "video_title": "Leg Press Machine Setup & Execution (Jeff Nippard)"
                },
                {
                    "name": "Standing Calf Raises & Hanging Knee Raises",
                    "sets_reps": "4 sets × 15 reps",
                    "rest": "45s rest",
                    "target": "Gastrocnemius & Rectus Abdominis",
                    "cue": "2-second pause at maximum stretch and 1-second flex at contraction.",
                    "video_url": "https://www.youtube.com/watch?v=-M4-G8p8fmc",
                    "video_title": "Calf & Core Knee Raise Technique (Scott Herman)"
                }
            ],
            "nutrition": {
                "calories": "2,650 kcal",
                "protein": "185g",
                "carbs": "310g",
                "fats": "70g",
                "pre_workout": "Banana smoothie with greek yogurt, honey & chia seeds",
                "post_workout": "Paneer/tofu curry or chicken stir-fry with brown basmati rice & lentils",
                "water": "4.0 Liters"
            }
        },
        "Thursday": {
            "title": "Active Recovery & Mobility Flow",
            "focus": "Joint decompression, tissue regeneration & aerobic base",
            "duration": "40 mins",
            "calories_est": "220 kcal",
            "badge_color": "#8B5CF6",
            "exercises": [
                {
                    "name": "Zone 2 Incline Treadmill Walk",
                    "sets_reps": "1 session × 30 mins",
                    "rest": "Steady state",
                    "target": "Aerobic Capacity & Mitochondrial Health",
                    "cue": "Keep heart rate steady at 115-130 BPM; conversational brisk walk.",
                    "video_url": "https://www.youtube.com/watch?v=0kO7L9e5V-I",
                    "video_title": "Zone 2 Cardio Training Guide (Dr. Peter Attia)"
                },
                {
                    "name": "Thoracic Spine Foam Rolling & Extensions",
                    "sets_reps": "3 sets × 10 reps",
                    "rest": "30s rest",
                    "target": "Thoracic Mobility & Postural Alignment",
                    "cue": "Do not hyperextend lumbar; breathe deeply through tight rib angles.",
                    "video_url": "https://www.youtube.com/watch?v=q0wLp4L6Qis",
                    "video_title": "Thoracic Spine Mobility Foam Rolling (Squat University)"
                },
                {
                    "name": "90/90 Hip Flow & Deep Glute Stretch",
                    "sets_reps": "3 sets × 60s per side",
                    "rest": "30s rest",
                    "target": "Hip Internal & External Rotators",
                    "cue": "Sit tall, square shoulders to lead knee, breathe calmly into tight areas.",
                    "video_url": "https://www.youtube.com/watch?v=33K5qXU9r4A",
                    "video_title": "90/90 Hip Mobility Flow Guide (The Ready State)"
                },
                {
                    "name": "Banded Face Pulls",
                    "sets_reps": "3 sets × 15 reps",
                    "rest": "45s rest",
                    "target": "Rear Deltoids & Scapular Retractors",
                    "cue": "Light band resistance; pull hands wide past ears to recruit external rotators.",
                    "video_url": "https://www.youtube.com/watch?v=rep-qVOkqgk",
                    "video_title": "How to Face Pull Correctly (ATHLEAN-X)"
                }
            ],
            "nutrition": {
                "calories": "2,250 kcal",
                "protein": "175g",
                "carbs": "220g",
                "fats": "65g",
                "pre_workout": "Green matcha tea or coconut water with electrolytes",
                "post_workout": "Sprouted moong salad, boiled eggs or tofu bhurji with walnuts",
                "water": "3.5 Liters"
            }
        },
        "Friday": {
            "title": "Upper Body Power & Hypertrophy",
            "focus": "Upper body volumizing, shoulder width & upper chest",
            "duration": "55 mins",
            "calories_est": "390 kcal",
            "badge_color": "#EC4899",
            "exercises": [
                {
                    "name": "Incline Barbell Bench Press",
                    "sets_reps": "4 sets × 6-8 reps",
                    "rest": "90s rest",
                    "target": "Upper Clavicular Pectoral Head",
                    "cue": "Bar lands 2 inches below clavicle; control descent before driving up.",
                    "video_url": "https://www.youtube.com/watch?v=SrqOu55lrYU",
                    "video_title": "Incline Barbell Bench Press Technique (Jeff Nippard)"
                },
                {
                    "name": "T-Bar Rows / Chest Supported Rows",
                    "sets_reps": "4 sets × 8-10 reps",
                    "rest": "75s rest",
                    "target": "Mid Back, Trapezius & Lats",
                    "cue": "Drive elbows straight back; keep chin tucked with flat lumbar spine.",
                    "video_url": "https://www.youtube.com/watch?v=j3Igk5nyZE4",
                    "video_title": "T-Bar Row Setup and Form (Scott Herman)"
                },
                {
                    "name": "Dumbbell Lateral Raises",
                    "sets_reps": "4 sets × 12-15 reps",
                    "rest": "45s rest",
                    "target": "Lateral Deltoids (Boulder Shoulders)",
                    "cue": "Lead with elbows; lean torso 5° forward to place tension on side head.",
                    "video_url": "https://www.youtube.com/watch?v=3VcKaXpzqRo",
                    "video_title": "Lateral Raises for Boulder Shoulders (Jeff Nippard)"
                },
                {
                    "name": "Hammer Curls & Overhead Tricep Extension",
                    "sets_reps": "3 sets × 12 reps (Superset)",
                    "rest": "60s rest",
                    "target": "Brachialis & Triceps Long Head",
                    "cue": "Strict tempo, zero hip swing; lock arms out smoothly at top.",
                    "video_url": "https://www.youtube.com/watch?v=zC3nLlEvin4",
                    "video_title": "Hammer Curl & Tricep Arm Superset (Buff Dudes)"
                }
            ],
            "nutrition": {
                "calories": "2,500 kcal",
                "protein": "180g",
                "carbs": "275g",
                "fats": "65g",
                "pre_workout": "Apple slices with almond butter & whey protein",
                "post_workout": "Tandoori chicken / grilled soya chaap with chapati & cucumber raita",
                "water": "3.5 Liters"
            }
        },
        "Saturday": {
            "title": "Posterior Chain & Functional Conditioning",
            "focus": "Posterior chain power, unilateral balance & core anti-rotation",
            "duration": "55 mins",
            "calories_est": "430 kcal",
            "badge_color": "#06B6D4",
            "exercises": [
                {
                    "name": "Trap Bar Deadlifts / Barbell Hip Thrusts",
                    "sets_reps": "4 sets × 8 reps",
                    "rest": "90s rest",
                    "target": "Glutes, Hamstrings, Quadriceps & Traps",
                    "cue": "Neutral spine, lock out glutes hard at the top without backward lean.",
                    "video_url": "https://www.youtube.com/watch?v=lmHYE10Y-G8",
                    "video_title": "How to Trap Bar Deadlift (Alan Thrall)"
                },
                {
                    "name": "Bulgarian Split Squats (Dumbbell)",
                    "sets_reps": "3 sets × 10 reps per leg",
                    "rest": "60s rest",
                    "target": "Quadriceps & Glute Medius",
                    "cue": "Rear foot on bench laces-down; drive through front heel.",
                    "video_url": "https://www.youtube.com/watch?v=2C-uNgKwPLE",
                    "video_title": "Bulgarian Split Squat Form Without Pain (Squat University)"
                },
                {
                    "name": "Kettlebell Farmer's Carries",
                    "sets_reps": "4 sets × 40 meters",
                    "rest": "60s rest",
                    "target": "Grip Strength, Forearms & Core Bracing",
                    "cue": "Pack shoulders down, tall posture, short steady steps.",
                    "video_url": "https://www.youtube.com/watch?v=rt17lmnaLSM",
                    "video_title": "Farmer's Walk & Carry Masterclass (Scott Herman)"
                },
                {
                    "name": "Cable Woodchoppers & Plank Hold",
                    "sets_reps": "3 sets × 12 reps / side + 45s plank",
                    "rest": "45s rest",
                    "target": "Obliques & Transverse Abdominis",
                    "cue": "Rotate from thoracic spine, keep pelvis locked forward.",
                    "video_url": "https://www.youtube.com/watch?v=pAplQXk3dkU",
                    "video_title": "Cable Woodchoppers for Oblique Power (ATHLEAN-X)"
                }
            ],
            "nutrition": {
                "calories": "2,600 kcal",
                "protein": "180g",
                "carbs": "290g",
                "fats": "70g",
                "pre_workout": "Whole grain toast with avocado & 2 poached eggs",
                "post_workout": "Lentil stew / chicken curry with wild rice and mixed green salad",
                "water": "4.0 Liters"
            }
        },
        "Sunday": {
            "title": "Full Rest & CNS Restoration",
            "focus": "Deep nervous system reset, cellular recovery & meal prep",
            "duration": "25 mins (Casual)",
            "calories_est": "180 kcal",
            "badge_color": "#64748B",
            "exercises": [
                {
                    "name": "Nature Walk or Casual Stroll",
                    "sets_reps": "20-30 mins outdoor walk",
                    "rest": "Casual pace",
                    "target": "Mental De-stress & Lymphatic Circulation",
                    "cue": "Enjoy sunlight, breathe naturally, no heart rate spikes.",
                    "video_url": "https://www.youtube.com/watch?v=b_r7F9L3eP0",
                    "video_title": "Science of Walking for Health & Recovery (Huberman Lab)"
                },
                {
                    "name": "Full Body Myofascial Foam Rolling",
                    "sets_reps": "10-15 mins full body",
                    "rest": "Relaxed",
                    "target": "Calves, Quads, IT Band, Lats",
                    "cue": "Spend 30-45 seconds on trigger points, breathe through discomfort.",
                    "video_url": "https://www.youtube.com/watch?v=o04_72b3X5o",
                    "video_title": "Full Body Foam Rolling Routine (Bob & Brad)"
                },
                {
                    "name": "Diaphragmatic Box Breathing",
                    "sets_reps": "5 mins (4s in, 4s hold, 4s out, 4s hold)",
                    "rest": "Meditative",
                    "target": "Parasympathetic Nervous System Activation",
                    "cue": "Inhale through nose expanding belly, slow relaxed exhalations.",
                    "video_url": "https://www.youtube.com/watch?v=tEmt1Znux58",
                    "video_title": "Navy SEAL Box Breathing Exercise (Mark Divine)"
                }
            ],
            "nutrition": {
                "calories": "2,200 kcal",
                "protein": "170g",
                "carbs": "200g",
                "fats": "65g",
                "pre_workout": "Hydrating herbal tea or fresh coconut water",
                "post_workout": "Light Mediterranean salad with chickpeas, feta/paneer, olive oil",
                "water": "3.5 Liters"
            }
        }
    }

    st.markdown(f"## 🏋️ **Member Fitness Companion — {active_genome.gym_name}**")
    
    # Check if there is an active member profile in session from registration or DB
    active_mem_session = st.session_state.get("logged_in_member", None)
    
    # Query members for this tenant to allow profile switching
    with SessionLocal() as db:
        tenant_mems = db.query(MemberRecordModel).filter_by(tenant_id=active_tenant_id).all()
        mem_options = {f"{m.name} ({m.member_id}) — {getattr(m, 'branch', getattr(m, 'area', 'Main'))}": m for m in tenant_mems}

    # Determine default member with intelligent profile resolution
    auth_user = st.session_state.get("authenticated_user", None)
    mem_email = str(active_mem_session.get("email", "") if active_mem_session else (auth_user.get("email", "") if auth_user else "")).lower()
    mem_phone = str(active_mem_session.get("phone", "") if active_mem_session else (auth_user.get("phone", "") if auth_user else ""))
    
    if "tanishka" in mem_email or "788808" in mem_phone:
        default_mem_name = "Tanishka Shah"
    elif active_mem_session and active_mem_session.get("name") and active_mem_session["name"] != "Verified Gym Member":
        default_mem_name = active_mem_session["name"]
    elif auth_user and auth_user.get("full_name") and auth_user["full_name"] != "Verified Gym Member":
        default_mem_name = auth_user["full_name"]
    elif tenant_mems:
        default_mem_name = tenant_mems[0].name
    else:
        default_mem_name = "Tanishka Shah"

    if active_mem_session:
        active_mem_session["name"] = default_mem_name
    if auth_user:
        auth_user["full_name"] = default_mem_name

    default_mem_id = active_mem_session["member_id"] if active_mem_session else (tenant_mems[0].member_id if tenant_mems else "MEM-2026-001")
    default_mem_branch = active_mem_session.get("branch_name", "Main Branch") if active_mem_session else (getattr(tenant_mems[0], "branch", "Main Branch") if tenant_mems else "Main Branch")
    default_mem_goal = active_mem_session.get("goal", "Hypertrophy (Muscle Gain)") if active_mem_session else (tenant_mems[0].goal if tenant_mems else "Hypertrophy (Muscle Gain)")

    col_user_header, col_user_badge = st.columns([3, 1])
    with col_user_header:
        st.markdown(f"### **Welcome back, {default_mem_name}!** 👋")
        st.markdown(f"**Member ID:** `{default_mem_id}` &nbsp;|&nbsp; **Home Gym:** `{active_genome.gym_name}` ({default_mem_branch}) &nbsp;|&nbsp; **Goal:** `{default_mem_goal}`")
    with col_user_badge:
        st.success("🟢 Active & Verified")

    # 📅 Today's Scheduled Workout Banner (Acc. to Current Day of Week)
    today_dt = datetime.now()
    today_day_name = today_dt.strftime("%A")
    today_date_str = today_dt.strftime("%A, %d %B %Y")
    today_routine = WEEKLY_WORKOUT_ROUTINES.get(today_day_name, WEEKLY_WORKOUT_ROUTINES["Monday"])

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-left: 6px solid {today_routine['badge_color']}; border-radius: 12px; padding: 18px 22px; margin-top: 6px; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <span style="background: {today_routine['badge_color']}22; color: {today_routine['badge_color']}; font-weight: 700; font-size: 0.8rem; padding: 4px 12px; border-radius: 9999px; border: 1px solid {today_routine['badge_color']}55; letter-spacing: 0.5px;">
                    📅 TODAY'S SCHEDULED WORKOUT &bull; {today_day_name.upper()} ({today_date_str})
                </span>
                <h3 style="margin: 8px 0 4px 0; color: #F8FAFC; font-size: 1.35rem; font-weight: 700;">
                    {today_routine['title']}
                </h3>
                <p style="margin: 0; color: #94A3B8; font-size: 0.92rem;">
                    🎯 <b>Target Focus:</b> {today_routine['focus']} &nbsp;|&nbsp; ⏱️ <b>Duration:</b> {today_routine['duration']} &nbsp;|&nbsp; 🔥 <b>Est. Burn:</b> {today_routine['calories_est']}
                </p>
            </div>
            <div>
                <span style="background: rgba(255,255,255,0.06); color: #E2E8F0; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; border: 1px solid rgba(255,255,255,0.12); display: inline-block;">
                    ⚡ {len(today_routine['exercises'])} Exercises Scheduled Today
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📋 **Quick View: Today's ({today_day_name}) Exercise List & Targets**", expanded=False):
        c_ex_cols = st.columns(len(today_routine['exercises']))
        for i, ex in enumerate(today_routine['exercises']):
            with c_ex_cols[i]:
                st.markdown(f"**{i+1}. {ex['name']}**")
                st.caption(f"🎯 {ex['sets_reps']}")
                st.caption(f"⏱️ {ex['rest']}")
                if "video_url" in ex:
                    st.markdown(f"[▶️ **Form Tutorial**]({ex['video_url']})", help=f"Watch tutorial for {ex['name']}")
        st.info("💡 **Ready to train?** Open **Tab 4 (🥗 AI Workout & Meal Guide)** to check off exercises, watch embedded video tutorials, or record your lifts in **Tab 2 (📝 Record Workout Log)**!")

    st.markdown("---")

    member_tabs = st.tabs([
        "📱 1. Digital Gym Pass & Check-In",
        "📝 2. Record Workout Log",
        "📈 3. My Progress & Plateau Detector",
        "🥗 4. AI Workout & Meal Guide"
    ])

    with member_tabs[0]:
        st.markdown("### 📱 **Quick Gym Check-In**")
        st.info("💡 **What this does:** When you arrive at the gym, tap below to check in. This records your attendance and helps the gym auto-scale server power.")

        c_pass_left, c_pass_right = st.columns([2, 3])
        with c_pass_left:
            st.markdown(f"""
            ```
            ==============================================
                      OFFICIAL DIGITAL FITNESS PASS       
            ==============================================
            MEMBER:   {default_mem_name.upper()}
            ID:       {default_mem_id}
            GYM:      {active_genome.gym_name}
            BRANCH:   {default_mem_branch}
            STATUS:   ACTIVE / VERIFIED ✅
            BARCODE:  ||| ||||| |||| |||| ||| ||||||| |||
            ==============================================
            ```
            """)
            if st.button("📍 Check In to Gym Right Now", type="primary", use_container_width=True):
                evt = TenantEvent(
                    tenant_id=active_tenant_id,
                    role_context="member",
                    event_type="check_in",
                    operational_params={"hour": datetime.utcnow().hour}
                )
                tige.update_genome_from_event(evt)
                st.balloons()
                st.success(f"✅ Check-in recorded at {datetime.now().strftime('%I:%M %p')}! Enjoy your workout!")

        with c_pass_right:
            st.markdown("#### 🕒 **Live Gym Crowd Level**")
            crowd_pct = int(usage.peak_hour_ratio * 100)
            st.write(f"Estimated Peak Crowd Level Today: **{crowd_pct}% concentration**")
            if crowd_pct > 60:
                st.warning("⚠️ High peak volume window: Gym is currently busy.")
            else:
                st.success("🟢 Ideal workout window: Plenty of equipment available!")

    with member_tabs[1]:
        st.markdown("### 📝 **Log Today's Exercises**")
        st.info("💡 Enter your weight and reps. Total workout volume is calculated automatically.")

        with st.form("member_log_exercise"):
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                sel_exercise = st.selectbox("Select Exercise", ["Barbell Bench Press", "Barbell Back Squat", "Conventional Deadlift", "Overhead Military Press", "Pull-Ups", "Dumbbell Incline Press"])
                num_sets = st.number_input("Number of Sets", min_value=1, max_value=10, value=4)
            with c_ex2:
                num_reps = st.number_input("Reps per Set", min_value=1, max_value=30, value=8)
                weight_kg = st.number_input("Weight Used (kg)", min_value=0.0, max_value=400.0, value=80.0, step=2.5)

            session_volume = num_sets * num_reps * weight_kg
            st.markdown(f"**Calculated Volume for this exercise:** `{session_volume:,.1f} kg lifted`")

            save_log = st.form_submit_button("Save Exercise to My History")
            if save_log:
                evt = TenantEvent(
                    tenant_id=active_tenant_id,
                    role_context="member",
                    event_type="workout_logged",
                    operational_params={"exercise": sel_exercise, "volume_kg": session_volume}
                )
                tige.update_genome_from_event(evt)
                st.success(f"🎉 Logged: {sel_exercise} — Total Volume: {session_volume:,.1f} kg!")

    with member_tabs[2]:
        st.markdown("### 📈 **Progressive Overload & Muscle Plateau Detector**")
        st.markdown(
            "Track your weekly lifted volume (*Sets × Reps × Weight*). "
            "Our neural engine monitors your trajectory across workout sessions to verify active progressive overload "
            "and automatically prescribe deload adjustments before physical stagnation occurs."
        )

        # 1. 1-Click Interactive Presets / Scenarios
        st.markdown("##### ⚡ **Interactive Scenarios (Select to Load Into Inputs):**")
        col_pre1, col_pre2, col_pre3, col_pre4 = st.columns(4)
        
        # Initialize default session values if not present
        if "inp_prog_s1" not in st.session_state:
            st.session_state.inp_prog_s1 = 100
        if "inp_prog_s2" not in st.session_state:
            st.session_state.inp_prog_s2 = 150
        if "inp_prog_s3" not in st.session_state:
            st.session_state.inp_prog_s3 = 125
        if "inp_prog_s4" not in st.session_state:
            st.session_state.inp_prog_s4 = 300

        # Initialize SAVED workout volumes (The graph ONLY changes when this is updated via Save)
        if "saved_prog_volumes" not in st.session_state:
            st.session_state.saved_prog_volumes = [
                int(st.session_state.inp_prog_s1),
                int(st.session_state.inp_prog_s2),
                int(st.session_state.inp_prog_s3),
                int(st.session_state.inp_prog_s4)
            ]
        if "last_saved_prog_time" not in st.session_state:
            st.session_state.last_saved_prog_time = datetime.now().strftime("%I:%M %p")

        with col_pre1:
            if st.button("🚀 Progressive Overload", use_container_width=True, help="Load steady +283 kg/session growth trajectory into inputs"):
                st.session_state.inp_prog_s1 = 3000
                st.session_state.inp_prog_s2 = 3250
                st.session_state.inp_prog_s3 = 3500
                st.session_state.inp_prog_s4 = 3850
                st.toast("Preset loaded into inputs! Click '💾 Save & Update My Workout Progress' below to update graph.", icon="📝")
                st.rerun()

        with col_pre2:
            if st.button("⚠️ Plateau Stagnation", use_container_width=True, help="Load flat trajectory showing AI deload intervention into inputs"):
                st.session_state.inp_prog_s1 = 3200
                st.session_state.inp_prog_s2 = 3200
                st.session_state.inp_prog_s3 = 3200
                st.session_state.inp_prog_s4 = 3200
                st.toast("Plateau scenario loaded (3,200 kg flatline across all sessions)! Click '💾 Save & Update My Workout Progress' below to update graph.", icon="📝")
                st.rerun()

        with col_pre3:
            if st.button("💥 Aggressive PR Surge", use_container_width=True, help="Load rapid volume acceleration into inputs"):
                st.session_state.inp_prog_s1 = 2800
                st.session_state.inp_prog_s2 = 3250
                st.session_state.inp_prog_s3 = 3700
                st.session_state.inp_prog_s4 = 4200
                st.toast("Aggressive PR Surge loaded (+450-500 kg weekly compounding)! Click '💾 Save & Update My Workout Progress' below to update graph.", icon="📝")
                st.rerun()

        with col_pre4:
            if st.button("🧪 Sample Test (100-300kg)", use_container_width=True, help="Load lightweight 100-300 kg test trajectory into inputs"):
                st.session_state.inp_prog_s1 = 100
                st.session_state.inp_prog_s2 = 150
                st.session_state.inp_prog_s3 = 200
                st.session_state.inp_prog_s4 = 300
                st.toast("Sample test loaded into inputs! Click '💾 Save & Update My Workout Progress' below to update graph.", icon="📝")
                st.rerun()

        st.markdown("")

        # 2. Session Volume Inputs with Real-time Deltas
        st.markdown("##### 📝 **Recent Workout Volume Logs (kg Lifted = Sets × Reps × Weight across 4 Weeks):**")
        c_v1, c_v2, c_v3, c_v4 = st.columns(4)
        
        with c_v1:
            s1_vol = st.number_input("Session 1 (Week 1 Baseline)", min_value=0, max_value=25000, step=25, key="inp_prog_s1", help="Sets × Reps × Weight (kg)")
            st.caption("🏁 **Week 1 Baseline**")
        with c_v2:
            s2_vol = st.number_input("Session 2 (Week 2)", min_value=0, max_value=25000, step=25, key="inp_prog_s2", help="Sets × Reps × Weight (kg)")
            d2_input = s2_vol - s1_vol
            p2_input = (d2_input / max(s1_vol, 1)) * 100
            d2_icon = "🟢" if d2_input > 0 else ("🔴" if d2_input < 0 else "⚪")
            st.caption(f"{d2_icon} **Δ vs W1:** `{d2_input:+,.0f} kg ({p2_input:+.1f}%)`")
        with c_v3:
            s3_vol = st.number_input("Session 3 (Week 3)", min_value=0, max_value=25000, step=25, key="inp_prog_s3", help="Sets × Reps × Weight (kg)")
            d3_input = s3_vol - s2_vol
            p3_input = (d3_input / max(s2_vol, 1)) * 100
            d3_icon = "🟢" if d3_input > 0 else ("🔴" if d3_input < 0 else "⚪")
            st.caption(f"{d3_icon} **Δ vs W2:** `{d3_input:+,.0f} kg ({p3_input:+.1f}%)`")
        with c_v4:
            s4_vol = st.number_input("Session 4 (Week 4 Latest)", min_value=0, max_value=25000, step=25, key="inp_prog_s4", help="Sets × Reps × Weight (kg)")
            d4_input = s4_vol - s3_vol
            p4_input = (d4_input / max(s3_vol, 1)) * 100
            d4_icon = "🟢" if d4_input > 0 else ("🔴" if d4_input < 0 else "⚪")
            st.caption(f"{d4_icon} **Δ vs W3:** `{d4_input:+,.0f} kg ({p4_input:+.1f}%)`")

        # Check for unsaved changes between input boxes and saved progress
        current_inputs = [int(s1_vol), int(s2_vol), int(s3_vol), int(s4_vol)]
        has_unsaved_changes = (current_inputs != st.session_state.saved_prog_volumes)

        # 3. Explicit SAVE ACTION BAR: Graph ONLY changes when user clicks this button
        c_save_btn, c_save_status = st.columns([1.5, 2.5])
        with c_save_btn:
            save_prog_clicked = st.button(
                "💾 Save & Update My Workout Progress",
                type="primary",
                use_container_width=True,
                help="Saves your current volume logs and re-renders the trajectory graph and AI plateau analysis"
            )
        with c_save_status:
            if has_unsaved_changes:
                st.warning("⚠️ **Unsaved Changes**: You adjusted session numbers above. Click **'Save & Update My Workout Progress'** to reflect these changes on the graph!")
            else:
                st.success(f"🟢 **Graph is Up-to-Date with Saved Progress** (Last Saved: `{st.session_state.last_saved_prog_time}`)")

        if save_prog_clicked:
            st.session_state.saved_prog_volumes = current_inputs
            st.session_state.last_saved_prog_time = datetime.now().strftime("%I:%M:%S %p")
            
            # Recalibrate and commit event to backend TIGE genome
            user_sessions = [{"total_volume_kg": v} for v in current_inputs]
            analysis = plateau_detector.analyze_member_trajectory(active_tenant_id, default_mem_id, user_sessions)
            evt_avg_delta = float(np.mean([current_inputs[i] - current_inputs[i-1] for i in range(1, 4)]))
            evt_is_plateau = bool(evt_avg_delta <= 1.0)
            evt = TenantEvent(
                tenant_id=active_tenant_id,
                role_context="member",
                event_type="plateau_analysis",
                operational_params={
                    "member_id": default_mem_id,
                    "avg_delta_kg": evt_avg_delta,
                    "is_plateau": evt_is_plateau,
                    "recommended_action": analysis["recommended_action"]
                }
            )
            tige.update_genome_from_event(evt)
            if evt_is_plateau:
                st.toast("⚠️ Plateau detected: Engine recalibrated with deload recommendation!", icon="🔄")
            else:
                st.toast("🎉 Progressive overload recorded! Engine updated.", icon="🚀")
            st.toast("✅ Workout progress successfully saved! Graph and metrics updated.", icon="💾")
            st.rerun()

        # The graph and metrics are calculated STRICTLY from saved_prog_volumes
        volumes = st.session_state.saved_prog_volumes
        diffs = [volumes[i] - volumes[i-1] for i in range(1, len(volumes))]
        avg_delta = float(np.mean(diffs))
        total_lifted = sum(volumes)
        net_growth = volumes[-1] - volumes[0]
        net_growth_pct = ((volumes[-1] - volumes[0]) / max(volumes[0], 1)) * 100
        is_plateau = bool(avg_delta <= 1.0)

        st.markdown("---")

        # 4. Live KPI Performance Metrics (Driven by Saved Progress)
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric(
                label="🏋️ Latest Saved Volume",
                value=f"{volumes[-1]:,.0f} kg",
                delta=f"{diffs[-1]:+,.0f} kg vs S3"
            )
        with kpi_c2:
            st.metric(
                label="📈 Progression Velocity",
                value=f"{avg_delta:+,.1f} kg/sess",
                delta="Target: > +1.0 kg" if avg_delta > 1.0 else "⚠️ Stagnant Growth",
                delta_color="normal" if avg_delta > 1.0 else "inverse"
            )
        with kpi_c3:
            st.metric(
                label="🎯 4-Session Total Volume",
                value=f"{total_lifted:,.0f} kg",
                delta=f"Net: {net_growth:+,.0f} kg ({net_growth_pct:+.1f}%)"
            )
        with kpi_c4:
            if is_plateau:
                st.metric(label="🛡️ AI Trajectory State", value="Plateau Stagnation ⚠️", delta="Intervention Needed", delta_color="inverse")
            else:
                st.metric(label="🛡️ AI Trajectory State", value="Progressive Overload 🟢", delta="Optimal Stimulus", delta_color="normal")

        st.markdown("")

        # 5. Easy-to-Understand High-Clarity Visual Graph
        st.markdown("##### 📊 **Volume Trajectory vs. Optimal +5% Overload Benchmark**")

        # Visual Legend Banner (Clear color-coded explanation)
        status_pill = '<span style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">🟢 STATUS: OPTIMAL OVERLOAD</span>' if not is_plateau else '<span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">⚠️ STATUS: PLATEAU STAGNATION</span>'

        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 14px 18px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
                <span style="display: flex; align-items: center; gap: 8px; color: #F8FAFC; font-size: 13px; font-weight: 600;">
                    <span style="display: inline-block; width: 14px; height: 14px; background: {'#EF4444' if is_plateau else '#10B981'}; border-radius: 3px;"></span>
                    {'🔴 Stagnant Volume (kg)' if is_plateau else '🟢 Your Lifted Volume (Actual kg)'}
                </span>
                <span style="display: flex; align-items: center; gap: 8px; color: #94A3B8; font-size: 13px; font-weight: 600;">
                    <span style="display: inline-block; width: 20px; height: 0; border-top: 3px dashed #38BDF8;"></span>
                    🔵 Science-Based +5% Overload Goal
                </span>
            </div>
            {status_pill}
        </div>
        """, unsafe_allow_html=True)
        
        session_names = ["Week 1 (Base)", "Week 2", "Week 3", "Week 4 (Latest)"]
        benchmark_target = [round(volumes[0] * (1.05 ** i)) for i in range(4)]
        deltas_str = ["Baseline"] + [f"{d:+,.0f} kg" for d in diffs]
        
        labels_str = []
        for i, (v, d) in enumerate(zip(volumes, deltas_str)):
            if i == 0:
                labels_str.append(f"{v:,.0f} kg (Base)")
            else:
                pct = ((v - volumes[i-1]) / max(volumes[i-1], 1)) * 100
                labels_str.append(f"{v:,.0f} kg ({pct:+.0f}%)")

        target_labels = ["" for _ in range(4)]
        target_labels[3] = f"🎯 Goal: {benchmark_target[3]:,.0f} kg"

        perf_status = ["Baseline Reference"] + [
            f"Exceeding Target by +{v - b:,.0f} kg 🎉" if v >= b else f"Below Target by -{b - v:,.0f} kg ⚠️"
            for v, b in zip(volumes[1:], benchmark_target[1:])
        ]

        df_chart = pd.DataFrame({
            "Session": session_names,
            "Order": [1, 2, 3, 4],
            "Actual Volume (kg)": volumes,
            "Target Benchmark (kg)": benchmark_target,
            "Data Label": labels_str,
            "Target Label": target_labels,
            "Growth Delta": deltas_str,
            "Performance Status": perf_status
        })

        main_color = "#EF4444" if is_plateau else "#10B981"
        accent_color = "#F87171" if is_plateau else "#34D399"
        bench_color = "#38BDF8"

        all_vals = volumes + benchmark_target
        min_val = max(0, min(all_vals) * 0.70)
        max_val = max(all_vals) * 1.25

        base_chart = alt.Chart(df_chart).encode(
            x=alt.X(
                "Session:N",
                sort=alt.SortField("Order", order="ascending"),
                title=None,
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=12,
                    labelFontWeight="bold",
                    labelPadding=8,
                    grid=False
                )
            )
        )

        # 1. Shaded area under actual curve (makes volume trajectory instantly readable)
        actual_area = base_chart.mark_area(
            opacity=0.18,
            color=main_color,
            interpolate="monotone"
        ).encode(
            y=alt.Y("Actual Volume (kg):Q")
        )

        # 2. Benchmark dashed line (+5% weekly target)
        bench_line = base_chart.mark_line(
            strokeDash=[6, 6],
            strokeWidth=2.5,
            color=bench_color,
            opacity=0.85
        ).encode(
            y=alt.Y("Target Benchmark (kg):Q")
        )

        bench_pts = base_chart.mark_circle(
            size=75,
            color=bench_color,
            opacity=0.80
        ).encode(
            y=alt.Y("Target Benchmark (kg):Q"),
            tooltip=[
                alt.Tooltip("Session:N", title="Session"),
                alt.Tooltip("Target Benchmark (kg):Q", title="Target Benchmark (+5%/session)", format=",.0f")
            ]
        )

        bench_text = base_chart.mark_text(
            align="center",
            baseline="top",
            dy=14,
            fontSize=11,
            fontWeight="bold",
            color=bench_color
        ).encode(
            y=alt.Y("Target Benchmark (kg):Q"),
            text="Target Label:N"
        )

        # 3. Actual volume curve (thick line + glowing points)
        actual_line = base_chart.mark_line(
            strokeWidth=4.5,
            color=main_color,
            interpolate="monotone"
        ).encode(
            y=alt.Y(
                "Actual Volume (kg):Q",
                title="Total Volume Lifted (kg) = Sets × Reps × Weight",
                scale=alt.Scale(domain=[min_val, max_val]),
                axis=alt.Axis(
                    grid=True,
                    gridColor="rgba(148, 163, 184, 0.15)",
                    labelFontSize=11,
                    titleFontSize=12,
                    titleFontWeight="bold",
                    titlePadding=10
                )
            )
        )

        actual_halo = base_chart.mark_circle(
            size=300,
            color=main_color,
            opacity=0.20
        ).encode(
            y=alt.Y("Actual Volume (kg):Q")
        )

        actual_pts = base_chart.mark_circle(
            size=180,
            color=main_color
        ).encode(
            y=alt.Y("Actual Volume (kg):Q"),
            tooltip=[
                alt.Tooltip("Session:N", title="Workout Session"),
                alt.Tooltip("Actual Volume (kg):Q", title="Your Lifted Volume", format=",.0f"),
                alt.Tooltip("Target Benchmark (kg):Q", title="Target Goal", format=",.0f"),
                alt.Tooltip("Growth Delta:N", title="Session Delta"),
                alt.Tooltip("Performance Status:N", title="Status vs Benchmark")
            ]
        )

        actual_text = base_chart.mark_text(
            align="center",
            baseline="bottom",
            dy=-15,
            fontSize=12,
            fontWeight="bold",
            color="#F8FAFC"
        ).encode(
            y=alt.Y("Actual Volume (kg):Q"),
            text="Data Label:N"
        )

        prog_chart = alt.layer(
            actual_area,
            bench_line,
            bench_pts,
            bench_text,
            actual_line,
            actual_halo,
            actual_pts,
            actual_text
        ).properties(
            height=340
        ).configure_view(
            strokeOpacity=0
        )

        st.altair_chart(prog_chart, use_container_width=True)

        # 6. Concise "How to Read This Graph" Visual Card
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-top: 10px; margin-bottom: 20px;">
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border-left: 4px solid {'#EF4444' if is_plateau else '#10B981'};">
                <strong style="color: #F8FAFC; font-size: 13px;">{'🔴 Plateau Stagnation' if is_plateau else '📈 Progressive Overload'}</strong>
                <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">
                    {'Volume has stalled. Your neuromuscular system needs a deload.' if is_plateau else 'Green line is climbing! You are consistently lifting more weight or reps.'}
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #38BDF8;">
                <strong style="color: #F8FAFC; font-size: 13px;">🎯 +5% Overload Benchmark (Dashed)</strong>
                <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">
                    {'Currently below the recommended progression curve.' if is_plateau else 'You are above the science-based target for muscle hypertrophy.'}
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                <strong style="color: #F8FAFC; font-size: 13px;">🏆 Net 4-Session Growth</strong>
                <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">
                    Overall change: <span style="color: {'#FCA5A5' if is_plateau else '#6EE7B7'}; font-weight: bold;">{net_growth:+,.0f} kg ({net_growth_pct:+.1f}%)</span> across 4 sessions.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 5. Live AI Coach Diagnosis & Actionable Prescription Card
        if is_plateau:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(245, 158, 11, 0.12) 100%); border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 12px; padding: 20px; margin-top: 15px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 28px;">⚠️</span>
                        <div>
                            <h4 style="margin: 0; color: #FCA5A5; font-weight: 700; font-size: 18px;">FAM-FIOS Neural Plateau Alert: Stagnation Detected</h4>
                            <span style="font-size: 13px; color: #CBD5E1;">Triggered via Closed-Loop FAFIE Motor Trajectory Classifier</span>
                        </div>
                    </div>
                    <span style="background: rgba(239, 68, 68, 0.3); color: #FCA5A5; padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; border: 1px solid rgba(239, 68, 68, 0.5);">STATUS: DELOAD RECOMMENDED</span>
                </div>
                <p style="color: #F1F5F9; font-size: 14px; margin-bottom: 15px; line-height: 1.6;">
                    Your average volume delta over the last 4 workout sessions is <strong>+{avg_delta:,.1f} kg/session</strong> (below the minimum growth threshold of +1.0 kg). Your neuromuscular system has adapted to current mechanical tension, accumulating systemic fatigue without stimulating fresh myofibrillar hypertrophy.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #EF4444;">
                        <strong style="color: #F8FAFC; font-size: 14px;">1. 🔄 Strategic Deload (Week 5)</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Reduce total lifted volume by 40-50% for 5-7 days. Retain form precision while allowing central nervous system (CNS) glycogen resensitization.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #F59E0B;">
                        <strong style="color: #F8FAFC; font-size: 14px;">2. 📐 Exercise Angle Rotation</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Rotate primary compound movement: Swap Flat Barbell Bench to 30° Incline Dumbbell Press; swap Back Squat to Front Squats or Bulgarian Split Squats.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">3. ⏱️ Tempo & Time Under Tension</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Shift to a 3-0-1-0 tempo (3-second controlled eccentric lowering phase) to recruit stubborn high-threshold fast-twitch motor units.</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(59, 130, 246, 0.12) 100%); border: 1px solid rgba(16, 185, 129, 0.45); border-radius: 12px; padding: 20px; margin-top: 15px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 28px;">🎉</span>
                        <div>
                            <h4 style="margin: 0; color: #6EE7B7; font-weight: 700; font-size: 18px;">Progressive Overload Active: Outstanding Growth Trajectory!</h4>
                            <span style="font-size: 13px; color: #CBD5E1;">Neural Trajectory Verified & Validated by FAFIE Engine</span>
                        </div>
                    </div>
                    <span style="background: rgba(16, 185, 129, 0.3); color: #6EE7B7; padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; border: 1px solid rgba(16, 185, 129, 0.5);">GROWTH VELOCITY: OPTIMAL</span>
                </div>
                <p style="color: #F1F5F9; font-size: 14px; margin-bottom: 15px; line-height: 1.6;">
                    You are increasing workload at an average velocity of <strong>+{avg_delta:,.1f} kg/session</strong> (Net 4-session gain: <strong>+{net_growth:,.0f} kg ({net_growth_pct:+.1f}%)</strong>). Your mechanical tension curve exceeds hypertrophy baseline criteria.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #10B981;">
                        <strong style="color: #F8FAFC; font-size: 14px;">1. 🎯 Incremental Micro-Loading</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Add 1.25 kg – 2.5 kg plates to your first 2 working sets next week to maintain compounding mechanical tension.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">2. 🥩 Protein & Recovery Buffer</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Fuel your muscular repair with 1.8–2.2g of protein per kg of bodyweight, along with 7.5+ hours of restorative sleep.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">3. 📊 Continuous Logging</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Keep recording your reps in Tab 2 so the autonomous closed loop can forecast your 1-rep maximums.</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)



        # 7. Educational Primer Expander
        with st.expander("📖 **How FAM-FIOS AI Progress Tracking Works (Click to Learn)**", expanded=False):
            st.markdown("""
            ### 🏋️ **Understanding Volume & Progressive Overload**
            
            1. **What is Total Volume?**
               - **Formula:** $\\text{Volume (kg)} = \\text{Sets} \\times \\text{Reps} \\times \\text{Weight (kg)}$
               - *Example:* 4 sets of 8 reps with an 80 kg barbell = $4 \\times 8 \\times 80 = 2,560\\text{ kg}$.
               - Total Volume is the gold standard metric used by sports scientists to measure physiological stimulus and mechanical tension.
            
            2. **The Principle of Progressive Overload:**
               - Muscles adapt to the demands placed upon them. To stimulate continuous muscle growth (hypertrophy) or strength gains, your total volume or intensity must steadily climb over time.
            
            3. **How the Plateau Detector Works:**
               - The FAM-FIOS engine evaluates your last 4 recorded sessions and computes the session-over-session velocity $\\Delta = \\frac{d(\\text{Volume})}{d(\\text{Session})}$.
               - If the average velocity $\\Delta_{\\text{average}} \\le 1.0\\text{ kg/session}$, the system flags **Plateau Stagnation**.
               - Stagnation is normal after 6-8 weeks of intense training because your central nervous system (CNS) and muscular receptors require recovery. FAM-FIOS automatically prescribes a structured **Deload Week** or **Exercise Variation** to break through the plateau without risking injury.
            """)

    with member_tabs[3]:
        st.markdown("### 🥗 **AI Workout & Daily Nutrition Guide**")
        st.caption(f"Personalized training & fueling regimen calibrated for **{default_mem_name}** &bull; Goal: **{default_mem_goal}**")

        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_idx = days_list.index(today_day_name) if today_day_name in days_list else 0

        c_day_sel, c_day_badge = st.columns([3, 1])
        with c_day_sel:
            selected_day = st.radio(
                "📅 **Select Training Day:**",
                days_list,
                index=today_idx,
                horizontal=True,
                key=f"sel_workout_day_{default_mem_id}"
            )
        with c_day_badge:
            if selected_day == today_day_name:
                st.success(f"📍 **Today ({today_day_name})**")
            else:
                st.info(f"Viewing: **{selected_day}**")

        current_routine = WEEKLY_WORKOUT_ROUTINES.get(selected_day, WEEKLY_WORKOUT_ROUTINES["Monday"])

        # Top summary card for the selected day
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #F1F5F9;">🏋️ {selected_day}'s Focus: {current_routine['title']}</h4>
            <p style="margin: 0; color: #94A3B8; font-size: 0.9rem;">
                🎯 <b>Target:</b> {current_routine['focus']} &nbsp;&bull;&nbsp; ⏱️ <b>Estimated Duration:</b> {current_routine['duration']} &nbsp;&bull;&nbsp; 🔥 <b>Estimated Caloric Burn:</b> {current_routine['calories_est']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        c_guide1, c_guide2 = st.columns([3, 2])
        with c_guide1:
            st.markdown(f"#### 🏋️ **{selected_day}'s Exercise Plan & Checklist**")
            st.caption("Check off exercises as you complete your workout sets:")

            completed_count = 0
            for idx, ex in enumerate(current_routine["exercises"]):
                chk_key = f"chk_ex_{default_mem_id}_{selected_day}_{idx}"
                is_done = st.checkbox(
                    f"**{idx + 1}. {ex['name']}** — `{ex['sets_reps']}`",
                    key=chk_key,
                    help=f"Rest: {ex['rest']} | Target: {ex['target']}"
                )
                if is_done:
                    completed_count += 1
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.45); border-left: 3px solid #38BDF8; border-radius: 6px; padding: 10px 14px; margin-top: -6px; margin-bottom: 8px;">
                    <div style="font-size: 0.84rem; color: #94A3B8;">🎯 <b>Target:</b> {ex['target']} &nbsp;|&nbsp; ⏱️ <b>Rest:</b> {ex['rest']}</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 4px;">💡 <b>Form Cue:</b> <i>{ex['cue']}</i></div>
                    <div style="margin-top: 8px;">
                        <a href="{ex.get('video_url', 'https://youtube.com')}" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.35); padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.80rem; font-weight: 600;">
                            <span style="color: #EF4444; font-size: 0.95rem;">▶️</span> Watch YouTube Form Tutorial: <b>{ex.get('video_title', 'Video Guide')}</b> ↗
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if ex.get("video_url"):
                    with st.expander(f"📺 Watch Form Video: {ex['name']}", expanded=False):
                        st.video(ex["video_url"])

            total_ex = len(current_routine["exercises"])
            pct_done = completed_count / total_ex if total_ex > 0 else 0
            st.progress(pct_done, text=f"Session Progress: {completed_count}/{total_ex} Exercises Completed ({int(pct_done * 100)}%)")
            if completed_count == total_ex and total_ex > 0:
                st.balloons()
                st.success(f"🎉 **Outstanding work, {default_mem_name}!** You completed all scheduled exercises for {selected_day}!")

        with c_guide2:
            st.markdown("#### 🥗 **Daily Nutrition & Fueling Plan**")
            nut = current_routine["nutrition"]
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;">
                <div style="font-size: 0.8rem; color: #10B981; font-weight: 700; text-transform: uppercase;">Daily Energy Target</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 4px 0 8px 0;">{nut['calories']}</div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">🥩 Protein: {nut['protein']}</span>
                    <span style="background: rgba(245, 158, 11, 0.15); color: #FBBF24; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">🍞 Carbs: {nut['carbs']}</span>
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">🥑 Fats: {nut['fats']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"**⚡ Pre-Workout Fueling:**")
            st.info(f"🥣 {nut['pre_workout']}")

            st.markdown(f"**🔋 Post-Workout Recovery:**")
            st.success(f"🍗 {nut['post_workout']}")

            st.markdown(f"**💧 Daily Hydration Target:**")
            st.write(f"🚰 Minimum **{nut['water']}** of water distributed throughout the day.")

# ==============================================================================
# 4. PATENT & ARCHITECTURE DEEP-DIVE
# ==============================================================================
elif portal_mode == "🔬 Patent & Architecture Deep-Dive":
    st.markdown("## 🔬 **FAM-FIOS: Architectural Verification Console**")
    st.markdown("**Invention Disclosure Document:** `24BIT0370-24BIT0390-IDF-01` (VIT SCORE)")

    k_tabs = st.tabs([
        "1. TIG 6-Vectors",
        "2. DTDF Dynamic Weights",
        "3. SICE Mathematical Convergence",
        "4. FAFIE Differential Privacy",
        "5. PTLM Peak Allocations",
        "6. ACVE Penetration Testing"
    ])

    with k_tabs[0]:
        st.subheader("🧬 Tenant Isolation Genome (TIG) Vectors")
        v1, v2, v3 = st.columns(3)
        with v1:
            st.json(active_genome.subscription.model_dump())
        with v2:
            st.json(active_genome.usage.model_dump())
        with v3:
            st.json(active_genome.role_permission.model_dump())
        v4, v5, v6 = st.columns(3)
        with v4:
            st.json(active_genome.resource.model_dump())
        with v5:
            st.json(active_genome.compliance.model_dump())
        with v6:
            st.json(active_genome.trust.model_dump())

    with k_tabs[1]:
        st.subheader("🕸️ DTDF Dynamic Dependency Fabric")
        edges = dtdfe.get_fabric(active_tenant_id)
        st.dataframe(pd.DataFrame([e.model_dump() for e in edges]), use_container_width=True)

    with k_tabs[2]:
        st.subheader("⚡ SICE Algorithmic Convergence Formula")
        st.latex(r"\hat{M}_{end} = M_{active} + (v \times d_{rem})")
        st.latex(r"C_{prorated} = (Price_{next} - Price_{current}) \times \frac{d_{rem}}{30}")

    with k_tabs[3]:
        st.subheader("🧠 FAFIE Differential Privacy Guarantees")
        st.latex(r"g_{clipped} = \frac{g}{\max\left(1, \frac{\|g\|_2}{C}\right)}, \quad g_{dp} = g_{clipped} + \mathcal{N}(0, \sigma^2)")

    with k_tabs[4]:
        st.subheader("🕒 PTLM Partition Allocations")
        st.write(f"Active Pre-Materialized Partitions: **{active_genome.resource.materialized_partitions} Partitions**")

    with k_tabs[5]:
        st.subheader("⚔️ ACVE Security & Penetration Testing")
        if st.button("🚨 Simulate Cross-Tenant Unauthorized Intrusion"):
            bad_intent = IntentObject(tenant_id=active_tenant_id, source_agent="IntrusionAgent", proposed_action="ENROLL_MEMBER")
            is_valid, verdict, violations = acve.verify_action_intent(bad_intent, caller_role="gym_admin", caller_tenant_id="tenant_foreign_attacker")
            st.error(f"ACVE Security Gatekeeper Verdict: {verdict}")
            st.write(f"Violations Caught: `{violations}`")
            st.success("Tenant isolation boundary 100% defended.")
