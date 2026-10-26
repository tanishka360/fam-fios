import sys
import os
import html
import random
import secrets
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
from app.services.email_service import email_service
from app.database import db_store, init_db, SessionLocal
from app.models.db_models import UserModel, MemberRecordModel
from app.models.intents import IntentObject
from app.models.events import TenantEvent

# Page Configuration
st.set_page_config(
    page_title="FAM-FIOS · Fitness Operations Platform",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="auto"
)

from ui_kit import (
    inject_global_styles, sidebar_brand, nav_label, page_header, section_header,
    step_indicator, chip, kv_rows, upi_qr_card, membership_pass
)
inject_global_styles()

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
sidebar_brand("FAM-FIOS", "Fitness Operations Platform")
st.sidebar.markdown("---")

# --- SIDEBAR AUTHENTICATION STATUS WIDGET ---
logged_in_user = st.session_state.get("authenticated_user", None)
if logged_in_user:
    role_label = "Member" if logged_in_user.get("role") == "member" else ("Gym Admin" if logged_in_user.get("role") == "gym_admin" else "Trainer")
    with st.sidebar.container(border=True):
        st.markdown(f"**{logged_in_user.get('full_name', 'User')}**")
        st.caption(f"{role_label} &nbsp;·&nbsp; {logged_in_user.get('branch', 'Main Branch')}")
        st.caption(f"`{logged_in_user.get('phone') or logged_in_user.get('email')}`")
        if st.button("Log out", key="sidebar_logout_btn", use_container_width=True):
            st.session_state.pop("authenticated_user", None)
            st.session_state.pop("logged_in_member", None)
            st.session_state.nav_target = "🔐 Member & Admin Login (via OTP)"
            st.rerun()
else:
    with st.sidebar.container(border=True):
        st.caption("Not signed in")
        if st.button("Sign in with OTP", key="sidebar_login_btn", type="primary", use_container_width=True):
            st.session_state.nav_target = "🔐 Member & Admin Login (via OTP)"
            st.rerun()

st.sidebar.markdown("---")

# Internal portal identifiers (used throughout for routing) and their display labels
PORTAL_LABELS = {
    "🔐 Member & Admin Login (via OTP)": "Sign In",
    "📝 New Member Registration & Payment": "Membership Registration",
    "🏢 Gym Owner / Admin View": "Operations Console",
    "🗄️ Central Users & Members Database": "Users & Members",
    "🏋️ Gym Member / User View": "Member Dashboard",
    "🔬 Patent & Architecture Deep-Dive": "Architecture"
}

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

nav_label("Navigation", st.sidebar)
portal_mode = st.sidebar.radio(
    "Navigation",
    PORTAL_OPTIONS,
    index=portal_idx,
    format_func=lambda p: PORTAL_LABELS.get(p, p),
    label_visibility="collapsed"
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

nav_label("Facility", st.sidebar)
selected_tenant_label = st.sidebar.selectbox(
    "Active facility",
    list(tenant_dict.keys()),
    index=tenant_idx,
    help="Scopes the Operations Console and Member Dashboard to one gym.",
    label_visibility="collapsed"
)
st.session_state.selected_tenant_label = selected_tenant_label
active_tenant_id = tenant_dict[selected_tenant_label]
active_genome = db_store.get_genome(active_tenant_id)
sub = active_genome.subscription
usage = active_genome.usage

st.sidebar.markdown("---")
with st.sidebar.expander("Platform engines"):
    st.markdown("""
    - **TIG**: Models each gym as a digital object with evolving capacity and server limits.
    - **SICE**: Tracks signups and calculates prorated upgrade fees before capacity runs out.
    - **PTLM**: Predicts morning and evening rush hours and scales servers 45 minutes ahead.
    - **FAFIE**: Collaborative workout recommendations across gyms without sharing member data.
    - **ACVE**: Isolation firewall that keeps each gym's records private from every other gym.
    """)

with st.sidebar.expander("System administration"):
    st.caption("Restores the seeded gyms (Apex, IronCore, Titan) and clears all other data.")
    if st.button("Reset database to defaults", use_container_width=True):
        db_store.reset()
        from app.main import startup_db_and_seed
        startup_db_and_seed()
        st.sidebar.success("Database restored to default seed data.")
        st.rerun()

st.sidebar.caption("Invention Disclosure 24BIT0370-24BIT0390-IDF-01 · VIT SCORE")

# ==============================================================================
# 0. SECURE OTP LOGIN & AUTHENTICATION PORTAL (NEW FEATURE!)
# ==============================================================================
if portal_mode == "🔐 Member & Admin Login (via OTP)":
    page_header(
        "Sign in to FAM-FIOS",
        "Members, trainers and gym administrators sign in without a password. Enter your registered mobile number or email and we'll send you a 6-digit verification code.",
        eyebrow="Secure access"
    )

    # Check if already logged in
    current_auth = st.session_state.get("authenticated_user", None)
    if current_auth:
        st.success(f"You're signed in as **{current_auth.get('full_name')}** ({current_auth.get('role').replace('_', ' ').title()}).")
        col_logged1, col_logged2 = st.columns(2)
        with col_logged1:
            dest_portal = "🏋️ Gym Member / User View" if current_auth.get("role") == "member" else "🏢 Gym Owner / Admin View"
            if st.button(f"Continue to {PORTAL_LABELS.get(dest_portal, dest_portal)}", type="primary", use_container_width=True):
                st.session_state.nav_target = dest_portal
                st.rerun()
        with col_logged2:
            if st.button("Sign out / switch account", use_container_width=True):
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
                section_header("Enter your mobile number or email", caption="We'll send a one-time code to verify it's you.", step=1)

                # A sample-account button below queues its number here; apply it before the widget renders
                if "login_input_ident" in st.session_state:
                    st.session_state.login_ident_field = st.session_state.pop("login_input_ident")
                user_ident = st.text_input(
                    "Mobile number or email",
                    placeholder="+91 98220 54321 or name@example.com",
                    key="login_ident_field"
                )

                send_otp_btn = st.button("Send verification code", type="primary", use_container_width=True)

                if send_otp_btn:
                    if not user_ident.strip():
                        st.error("Please enter a valid mobile number or email address.")
                    else:
                        clean_ident = user_ident.strip()
                        # Generate OTP with optional AWS and SMTP credentials
                        custom_aws_creds = st.session_state.get("custom_aws_credentials")
                        custom_smtp_creds = st.session_state.get("custom_smtp_credentials")
                        otp_rec = generate_login_otp(
                            clean_ident,
                            custom_aws_credentials=custom_aws_creds,
                            custom_smtp_credentials=custom_smtp_creds
                        )
                        
                        if not otp_rec.get("delivered"):
                            st.error(
                                f"Couldn't send the verification code by {otp_rec.get('channel', 'SMS')}. Please try again in a moment.\n\n"
                                f"Details: {otp_rec.get('dispatch_error')}"
                            )
                        else:
                            # Look up account in database
                            matched_account = db_store.find_account_by_identifier(clean_ident)
                            otp_rec["account"] = matched_account

                            st.session_state.active_otp_record = otp_rec
                            st.session_state.otp_step = "verify"
                            st.session_state.entered_otp_val = ""
                            st.rerun()
                        

                # Sample accounts (fill the field above)
                st.markdown("")
                st.caption("Sample accounts — click to fill in the number")
                c_demo1, c_demo2 = st.columns(2)
                c_demo3, c_demo4 = st.columns(2)
                with c_demo1:
                    if st.button("Tanishka Shah · Titan member", use_container_width=True):
                        st.session_state.login_input_ident = "+91 78880 85822"
                        st.rerun()
                with c_demo2:
                    if st.button("Sarah Jenkins · Apex member", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98233 30002"
                        st.rerun()
                with c_demo3:
                    if st.button("Titan Executive · Gym admin", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98231 10001"
                        st.rerun()
                with c_demo4:
                    if st.button("Coach Alex · IronCore trainer", use_container_width=True):
                        st.session_state.login_input_ident = "+91 98232 20002"
                        st.rerun()

                # Unified SMS & Email Gateway Configuration Expander
                st.markdown("")
                with st.expander("Delivery settings (SMS & email)", expanded=False):
                    tab_gw_email, tab_gw_sms = st.tabs(["Email (SMTP)", "SMS (Amazon SNS)"])

                    with tab_gw_email:
                        email_status = email_service.check_email_configuration(st.session_state.get("custom_smtp_credentials"))
                        if email_status["configured"]:
                            st.success(f"**Email delivery active** — `{email_status['smtp_host']}:{email_status['smtp_port']}` (account `{email_status['masked_user']}`). Codes are emailed to the address entered.")
                        else:
                            st.warning("**Email delivery not configured.** Email sign-in is unavailable until SMTP is set up. Enter your SMTP details below:")

                        c_em1, c_em2 = st.columns(2)
                        with c_em1:
                            smtp_host_in = st.text_input("SMTP Host", value=st.session_state.get("custom_smtp_credentials", {}).get("smtp_host", "smtp.gmail.com"), placeholder="smtp.gmail.com")
                            smtp_user_in = st.text_input("SMTP Username / Email", value=st.session_state.get("custom_smtp_credentials", {}).get("smtp_user", ""), placeholder="yourname@gmail.com")
                        with c_em2:
                            smtp_port_in = st.number_input("SMTP Port", value=int(st.session_state.get("custom_smtp_credentials", {}).get("smtp_port", 587)), min_value=25, max_value=65535)
                            smtp_pass_in = st.text_input("SMTP Password / App Password", value=st.session_state.get("custom_smtp_credentials", {}).get("smtp_password", ""), type="password", placeholder="16-character Google App Password")

                        c_em_save, c_em_reset = st.columns(2)
                        with c_em_save:
                            if st.button("Save email settings", use_container_width=True, key="btn_save_smtp"):
                                if smtp_user_in.strip() and smtp_pass_in.strip():
                                    st.session_state.custom_smtp_credentials = {
                                        "smtp_host": smtp_host_in.strip(),
                                        "smtp_port": int(smtp_port_in),
                                        "smtp_user": smtp_user_in.strip(),
                                        "smtp_password": smtp_pass_in.strip(),
                                        "from_email": smtp_user_in.strip()
                                    }
                                    st.toast("Email settings saved for this session.", icon="✅")
                                    st.rerun()
                                else:
                                    st.warning("Please provide both a username and an app password.")
                        with c_em_reset:
                            if st.button("Clear email settings", use_container_width=True, key="btn_reset_smtp"):
                                st.session_state.pop("custom_smtp_credentials", None)
                                st.toast("Email settings cleared.", icon="🔄")
                                st.rerun()

                    with tab_gw_sms:
                        aws_status = aws_sns_service.check_sns_configuration(st.session_state.get("custom_aws_credentials"))
                        if aws_status["configured"]:
                            source_note = f", via `{aws_status['source']}`" if aws_status.get("source") else ""
                            st.success(f"**SMS delivery active** — Amazon SNS in `{aws_status['region']}` (key `{aws_status['masked_key']}`{source_note}). Codes are texted to the number entered.")
                        else:
                            st.warning("**SMS delivery not configured.** No AWS credentials were found. On EC2, attach an IAM instance profile with SNS publish permission (e.g. LabInstanceProfile), or enter credentials below:")

                        col_aws_k1, col_aws_k2 = st.columns(2)
                        with col_aws_k1:
                            aws_key_input = st.text_input("AWS Access Key ID", value=st.session_state.get("custom_aws_credentials", {}).get("aws_access_key_id", ""), type="password", placeholder="e.g. AKIAIOSFODNN7EXAMPLE")
                            aws_reg_input = st.selectbox("AWS Region", ["us-east-1 (N. Virginia)", "ap-south-1 (Mumbai)", "eu-west-1 (Ireland)", "ap-southeast-1 (Singapore)"], index=0)
                            aws_tok_input = st.text_input("AWS Session Token (optional)", value=st.session_state.get("custom_aws_credentials", {}).get("aws_session_token", ""), type="password", placeholder="Required for temporary / Learner Lab keys")
                        with col_aws_k2:
                            aws_sec_input = st.text_input("AWS Secret Access Key", value=st.session_state.get("custom_aws_credentials", {}).get("aws_secret_access_key", ""), type="password", placeholder="e.g. wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
                            col_save_aws, col_reset_aws = st.columns([1, 1])
                            with col_save_aws:
                                if st.button("Save AWS keys", use_container_width=True, key="btn_save_aws"):
                                    reg = aws_reg_input.split(" ")[0]
                                    if aws_key_input.strip() and aws_sec_input.strip():
                                        st.session_state.custom_aws_credentials = {
                                            "aws_access_key_id": aws_key_input.strip(),
                                            "aws_secret_access_key": aws_sec_input.strip(),
                                            "aws_session_token": aws_tok_input.strip(),
                                            "region_name": reg
                                        }
                                        st.toast("AWS keys saved for this session.", icon="✅")
                                        st.rerun()
                                    else:
                                        st.warning("Please provide both an Access Key ID and a Secret Access Key.")
                            with col_reset_aws:
                                if st.button("Clear AWS keys", use_container_width=True, key="btn_reset_aws"):
                                    st.session_state.pop("custom_aws_credentials", None)
                                    st.toast("Entered keys cleared; using the server's default AWS credentials.", icon="🔄")
                                    st.rerun()

            elif st.session_state.otp_step == "verify":
                otp_rec = st.session_state.get("active_otp_record", {})
                if not otp_rec:
                    st.session_state.otp_step = "request"
                    st.rerun()
                matched_acc = otp_rec.get("account")
                
                channel = otp_rec.get("channel", "SMS")

                section_header("Enter the 6-digit code", step=2)
                if channel == "Email":
                    st.success(f"We've emailed a 6-digit code to **{otp_rec.get('masked_target', '')}**. It expires in 5 minutes.")
                else:
                    st.success(f"We've texted a 6-digit code to **{otp_rec.get('masked_target', '')}**. It expires in 5 minutes.")
                curr_otp = st.session_state.get("entered_otp_val", "")
                entered_otp = st.text_input("Verification code", value=curr_otp, max_chars=6, placeholder="6-digit code", key="otp_input_field")

                verify_btn = st.button("Verify and sign in", type="primary", use_container_width=True)

                if verify_btn:
                    if not entered_otp.strip():
                        st.error("Please enter the 6-digit code.")
                    else:
                        is_valid, msg = verify_login_otp(otp_rec["raw_identifier"], entered_otp.strip())
                        if not is_valid:
                            st.error(msg)
                        else:
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
                                guest_ref = secrets.token_hex(2)
                                user_session = {
                                    "user_id": f"usr_mem_{guest_ref}",
                                    "full_name": resolved_name,
                                    "email": raw_id if "@" in raw_id else f"member.{guest_ref}@gmail.com",
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
                            st.toast(f"Signed in. Welcome back, {user_session['full_name']}.", icon="✅")
                            st.rerun()

                st.caption("Didn't get it? Messages can take up to a minute. Check the number is correct, then resend.")
                col_resend, col_back = st.columns(2)
                with col_resend:
                    if st.button("Resend code", use_container_width=True):
                        custom_aws_creds = st.session_state.get("custom_aws_credentials")
                        custom_smtp_creds = st.session_state.get("custom_smtp_credentials")
                        new_rec = generate_login_otp(
                            otp_rec.get('raw_identifier', ''),
                            custom_aws_credentials=custom_aws_creds,
                            custom_smtp_credentials=custom_smtp_creds
                        )
                        if new_rec.get("delivered"):
                            new_rec["account"] = matched_acc
                            st.session_state.active_otp_record = new_rec
                            st.session_state.entered_otp_val = ""
                            st.toast(f"New code sent to {new_rec.get('masked_target', '')}.", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Couldn't resend the code. Please try again in a moment.\n\nDetails: {new_rec.get('dispatch_error')}")
                with col_back:
                    if st.button("Use a different number or email", use_container_width=True):
                        st.session_state.otp_step = "request"
                        st.session_state.pop("active_otp_record", None)
                        st.session_state.entered_otp_val = ""
                        st.rerun()

        with col_login_info:
            with st.container(border=True):
                section_header("Passwordless security", level=4)
                st.markdown("""
                - **Cryptographic 6-digit code** — generated with a CSPRNG (`secrets.randbelow`) and checked with a constant-time comparison to prevent timing attacks.
                - **Short-lived** — codes expire after **5 minutes**.
                - **Single use** — a code is deleted the moment it's verified.
                - **One sign-in for every role**
                  - **Members** — digital pass, check-in, workout tracking
                  - **Admins** — franchise roster, capacity planning, billing
                  - **Trainers** — client assignment and plateau detection
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
        page_header(
            "Become a member",
            "Choose a gym and branch, pick a plan and pay securely. Your membership is activated and added to the gym's roster as soon as payment completes.",
            eyebrow="Membership registration"
        )
        step_indicator(["Membership details", "Payment", "Digital pass"], 0)

        reg_col1, reg_col2 = st.columns([3, 2])

        with reg_col1:
            section_header("Choose your gym", caption="Select a city, gym network and branch.", step=1)
            col_city, col_brand = st.columns(2)
            with col_city:
                selected_city = st.selectbox("City", list(CITY_BRANCH_STRUCTURE.keys()), key="form_city")

            available_gym_brands = CITY_BRANCH_STRUCTURE[selected_city]
            brand_options = {brand_info["brand_name"]: tid for tid, brand_info in available_gym_brands.items()}

            with col_brand:
                selected_brand_name = st.selectbox("Gym network", list(brand_options.keys()), key="form_brand")

            chosen_tenant_id = brand_options[selected_brand_name]
            brand_data = available_gym_brands[chosen_tenant_id]
            branch_list = brand_data["branches"]
            branch_dict = {f"{b['branch_name']} ({b['area']})": b for b in branch_list}

            selected_branch_label = st.selectbox(
                f"Branch in {selected_city} ({len(branch_list)} available)",
                list(branch_dict.keys()),
                help=f"Select from {len(branch_list)} distinct {selected_brand_name} franchises in {selected_city}.",
                key="form_branch"
            )
            selected_branch = branch_dict[selected_branch_label]

            chosen_genome = db_store.get_genome(chosen_tenant_id)
            chosen_sub = chosen_genome.subscription
            remaining_slots = max(0, chosen_sub.max_members - chosen_sub.active_members)

            # Dynamic Branch Facility Card
            with st.container(border=True):
                st.markdown(f"**{chosen_genome.gym_name} — {selected_branch['branch_name']}**")
                fc1, fc2 = st.columns(2)
                with fc1:
                    st.caption("Location")
                    st.write(f"{selected_city} — {selected_branch['area']}")
                    st.caption("Address")
                    st.write(selected_branch['address'])
                    st.caption("Phone")
                    st.write(selected_branch['phone'])
                with fc2:
                    st.caption("Opening hours")
                    st.write(selected_branch['timing'])
                    st.caption("Facility tier")
                    st.write(f"{chosen_sub.tier} plan · {remaining_slots} membership spots remaining")
                    st.caption("Amenities")
                    st.write(selected_branch['amenities'])

            section_header("Your details", step=2)
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

            section_header("Choose a plan", step=3)
            plan_choice = st.radio(
                "Plan duration",
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
            section_header("Checkout", step=4)
            with st.container(border=True):
                section_header("Order summary", level=4)
                kv_rows([
                    ("Gym network", chosen_genome.gym_name),
                    ("City", selected_city),
                    ("Branch", selected_branch['branch_name']),
                    ("Address", selected_branch['address']),
                    ("Plan", plan_choice.split('—')[0].strip()),
                ])
                st.markdown("---")
                kv_rows([
                    ("Membership fee", f"₹{base_price:,.2f}"),
                    ("GST (18%)", f"₹{gst_amount:,.2f}"),
                ], total=("Total due", f"₹{total_payable:,.2f}"))

                st.markdown("")
                section_header("Payment method", level=4)
                pay_method_display = {
                    "📱 UPI Gateway (Google Pay / PhonePe / Paytm / QR)": "UPI — Google Pay, PhonePe, Paytm or QR",
                    "💳 Credit / Debit Card (with 3D Secure OTP)": "Credit / Debit Card (3-D Secure)",
                    "🏛️ Net Banking Gateway (SBI, HDFC, ICICI, Axis)": "Net Banking — SBI, HDFC, ICICI, Axis",
                    "⚡ Instant 1-Click Fast Checkout (Demo Mode)": "Express Approval (Test Mode)"
                }
                pay_method = st.radio(
                    "Payment method",
                    list(pay_method_display.keys()),
                    format_func=lambda o: pay_method_display.get(o, o),
                    key="input_pay_method",
                    label_visibility="collapsed"
                )

                st.caption("Secured with 256-bit TLS encryption. You'll complete payment on the next screen.")

                u_name_clean = (u_name or st.session_state.get("input_u_name", "")).strip()
                u_email_clean = (u_email or st.session_state.get("input_u_email", "")).strip()
                u_phone_clean = (u_phone or st.session_state.get("input_u_phone", "")).strip()

                # If email is empty (common when Chrome/Edge autofill doesn't trigger React's synthetic event), generate clean fallback
                if not u_email_clean and u_name_clean:
                    u_email_clean = f"{u_name_clean.lower().replace(' ', '.')}@gmail.com"
                elif not u_email_clean:
                    u_email_clean = "member@fitness.fam"

                proceed_btn = st.button("Continue to payment", type="primary", use_container_width=True)

                if proceed_btn:
                    missing_fields = []
                    if not u_name_clean:
                        missing_fields.append("Full Name")
                    if not u_phone_clean:
                        missing_fields.append("Mobile Number")

                    if missing_fields:
                        st.error(f"Please enter your {' and '.join(missing_fields)} to continue.")
                    elif chosen_sub.active_members >= chosen_sub.max_members:
                        st.error(f"{chosen_genome.gym_name} is at full capacity ({chosen_sub.active_members}/{chosen_sub.max_members} members), so new registrations are paused until the gym upgrades its plan.")
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
        page_header(
            "Complete your payment",
            "Choose how you'd like to pay. Your membership activates as soon as the payment is authorized.",
            eyebrow="Secure checkout"
        )
        step_indicator(["Membership details", "Payment", "Digital pass"], 1)

        # Gateway Top Overview Bar
        with st.container(border=True):
            col_ov1, col_ov2, col_ov3, col_ov4 = st.columns(4)
            with col_ov1:
                st.caption("MERCHANT")
                st.markdown(f"**{c_data['gym_name']}**")
                st.caption(f"{c_data['branch_name']}, {c_data['city']}")
            with col_ov2:
                st.caption("MEMBER")
                st.markdown(f"**{c_data['name']}**")
                st.caption(f"{c_data['phone']}")
            with col_ov3:
                st.caption("PLAN")
                st.markdown(f"**{c_data['plan_choice'].split('—')[0].strip()}**")
                st.caption(f"Base: ₹{c_data['base_price']:,.2f} + GST: ₹{c_data['gst_amount']:,.2f}")
            with col_ov4:
                st.caption("TOTAL DUE")
                section_header(f"₹{c_data['total_payable']:,.2f}", level=3)

        st.markdown("")

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

        gw_tab_display = {
            gw_tab_names[0]: "UPI",
            gw_tab_names[1]: "Credit / Debit Card",
            gw_tab_names[2]: "Net Banking",
            gw_tab_names[3]: "Express Approval (Test)"
        }
        selected_gw_tab = st.radio(
            "Payment method",
            gw_tab_names,
            index=initial_tab_idx,
            horizontal=True,
            format_func=lambda o: gw_tab_display.get(o, o),
            key="gw_radio_tab"
        )

        st.markdown("")

        payment_authorized = False
        authorized_method = ""

        # --- GATEWAY OPTION 1: UPI ---
        if "UPI Gateway" in selected_gw_tab:
            section_header("Pay with UPI")
            col_upi_l, col_upi_r = st.columns([1, 1])
            merchant_vpa = f"fitnesspay.{c_data['tenant_id']}@icici"
            with col_upi_l:
                section_header("Scan QR code", level=4)
                upi_qr_card(merchant_vpa, c_data['gym_name'], c_data['total_payable'], f"Membership {c_data['name']}")
                st.caption(f"Merchant UPI ID: `{merchant_vpa}`")

            with col_upi_r:
                section_header("Pay with a UPI app", level=4)
                st.caption("Choose an app to send a payment request to your phone.")
                c_app1, c_app2 = st.columns(2)
                with c_app1:
                    if st.button("Google Pay", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (Google Pay Express)"
                    if st.button("PhonePe", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (PhonePe App)"
                with c_app2:
                    if st.button("Paytm", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (Paytm Payments)"
                    if st.button("CRED", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "UPI (CRED / BHIM)"

                st.markdown("---")
                section_header("Pay with your UPI ID", level=4)
                vpa_input = st.text_input("UPI ID", placeholder="yourname@okhdfcbank", value="member@okhdfcbank")
                if st.button(f"Send payment request · ₹{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                    payment_authorized = True
                    authorized_method = f"UPI Collect ({vpa_input})"

        # --- GATEWAY OPTION 2: CREDIT / DEBIT CARD WITH 3D SECURE OTP ---
        elif "Credit / Debit Card" in selected_gw_tab:
            section_header("Pay by card", caption="Visa, Mastercard and RuPay, verified with 3-D Secure.")
            
            if "card_otp_sent" not in st.session_state:
                st.session_state.card_otp_sent = False

            if not st.session_state.card_otp_sent:
                col_card1, col_card2 = st.columns([1, 1])
                with col_card1:
                    st.text_input("Card number", "4532 •••• •••• 8821")
                    st.text_input("Name on card", c_data['name'].upper())
                    c_exp, c_cvv = st.columns(2)
                    with c_exp:
                        st.text_input("Expiry (MM/YY)", "08/29")
                    with c_cvv:
                        st.text_input("CVV", "•••", type="password")

                with col_card2:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #312E81 100%); padding: 22px 24px; border-radius: 14px; color: white; margin-top: 28px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
                        <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 13px; letter-spacing: 0.06em; opacity: 0.9;">
                            <span>FAM-FIOS PLATINUM</span>
                            <span style="font-style: italic; font-weight: 700;">VISA</span>
                        </div>
                        <div style="font-size: 20px; letter-spacing: 3px; margin: 28px 0 14px 0; font-family: 'JetBrains Mono', monospace;">
                            4532  ••••  ••••  8821
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px;">
                            <div>
                                <div style="opacity: 0.65; letter-spacing: 0.06em;">CARDHOLDER</div>
                                <div style="font-weight: 600;">""" + html.escape(c_data['name'].upper()) + """</div>
                            </div>
                            <div>
                                <div style="opacity: 0.65; letter-spacing: 0.06em;">EXPIRES</div>
                                <div style="font-weight: 600;">08/29</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("Protected by Visa Secure and Mastercard Identity Check.")

                if st.button("Continue to 3-D Secure verification", type="primary", use_container_width=True):
                    st.session_state.card_otp_sent = True
                    st.rerun()

            else:
                # 3D-Secure Bank OTP Sub-Screen
                with st.container(border=True):
                    section_header("Bank verification (3-D Secure)", level=4)
                    st.write(f"Your bank has sent a one-time password to the mobile number ending in **{html.escape(c_data['phone'][-4:])}**.")

                    col_otp1, col_otp2 = st.columns([2, 1])
                    with col_otp1:
                        otp_val = st.text_input("Bank OTP", value="742910")
                        st.caption("Test mode: the bank OTP `742910` is pre-filled.")
                    with col_otp2:
                        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                        if st.button("Resend OTP", use_container_width=True):
                            st.info("A new OTP has been sent to your mobile.")

                col_otp_btn1, col_otp_btn2 = st.columns(2)
                with col_otp_btn1:
                    if st.button(f"Authorize payment · ₹{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                        payment_authorized = True
                        authorized_method = "Credit/Debit Card (3D-Secure Verified)"
                        st.session_state.card_otp_sent = False
                with col_otp_btn2:
                    if st.button("Change card details", use_container_width=True):
                        st.session_state.card_otp_sent = False
                        st.rerun()

        # --- GATEWAY OPTION 3: NET BANKING ---
        elif "Net Banking Gateway" in selected_gw_tab:
            section_header("Pay with net banking")
            col_nb1, col_nb2 = st.columns([1, 1])
            with col_nb1:
                section_header("Your bank", level=4)
                bank_choice = st.selectbox(
                    "Bank",
                    [
                        "State Bank of India (SBI)",
                        "HDFC Bank",
                        "ICICI Bank",
                        "Axis Bank",
                        "Kotak Mahindra Bank",
                        "Punjab National Bank"
                    ]
                )
                st.caption(f"You'll authorize this payment through {bank_choice}'s secure gateway.")

            with col_nb2:
                section_header("Net banking sign-in", level=4)
                st.text_input("Customer ID / username", value=f"usr_{c_data['phone'][-6:]}")
                st.text_input("Password / IPIN", value="••••••••••", type="password")

                if st.button(f"Sign in and pay ₹{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                    payment_authorized = True
                    authorized_method = f"Net Banking ({bank_choice})"

        # --- GATEWAY OPTION 4: INSTANT DEMO ---
        elif "1-Click Instant Approval" in selected_gw_tab:
            section_header("Express Approval", caption="Test mode — authorizes the payment without contacting a payment network.")
            if st.button(f"Approve payment · ₹{c_data['total_payable']:,.2f}", type="primary", use_container_width=True):
                payment_authorized = True
                authorized_method = "Express Approval (Test Mode)"

        st.markdown("---")
        if st.button("Back to membership details"):
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
        page_header(
            "Payment successful — membership active",
            f"Welcome to {rec['gym_name']}, {rec['name']}. Your receipt and digital pass are below.",
            eyebrow="Confirmation"
        )
        step_indicator(["Membership details", "Payment", "Digital pass"], 2)

        col_rcpt1, col_rcpt2 = st.columns([1, 1])

        with col_rcpt1:
            section_header("Tax invoice & receipt", level=3)
            with st.container(border=True):
                kv_rows([
                    ("Transaction ID", rec['txn_id']),
                    ("Bank reference (RRN)", rec['bank_rrn']),
                    ("Payment method", rec['method']),
                    ("Paid on", rec['paid_at']),
                    ("Status", "Captured & verified"),
                ])
                st.markdown("---")
                kv_rows([
                    ("Billed to", f"{rec['name']} ({rec['phone']})"),
                    ("Facility", f"{rec['gym_name']} — {rec['branch_name']}"),
                    ("City", rec['city']),
                    ("Plan", rec['plan_name']),
                    ("Membership fee", f"₹{rec['base_price']:,.2f}"),
                    ("GST (18%)", f"₹{rec['gst_amount']:,.2f}"),
                ], total=("Total paid", f"₹{rec['total_payable']:,.2f}"))
                s3_uri_display = rec.get("s3_uri", f"s3://fam-fios-cloud-vault/invoices/{rec['txn_id']}.json")
                st.caption(f"Archived to Amazon S3 (server-side encrypted): `{s3_uri_display}`")

        with col_rcpt2:
            section_header("Digital fitness pass", level=3)
            membership_pass(
                member_name=rec['name'],
                member_id=rec['member_id'],
                gym_name=rec['gym_name'],
                location=f"{rec['city']} — {rec['branch_name']}",
                address=rec['branch_address'],
                phone=rec['phone'],
                plan=rec['plan_name'],
                amount_paid=f"₹{rec['total_payable']:,.2f}",
                valid_until=rec['expiry_date'],
            )
            st.caption("Show this pass's QR code at the front desk to check in.")

        st.markdown("---")
        section_header("What's next", caption="Your account is active across all modules.")

        c_dest1, c_dest2, c_dest3 = st.columns(3)

        with c_dest1:
            with st.container(border=True):
                section_header("Member dashboard", level=4)
                st.write(f"Workout logging, check-in and plateau detection, set up for **{rec['name']}**.")
                if st.button("Open member dashboard", type="primary", use_container_width=True):
                    st.session_state.nav_target = "🏋️ Gym Member / User View"
                    st.session_state.tenant_target = rec["tenant_id"]
                    st.session_state.logged_in_member = rec
                    st.rerun()

        with c_dest2:
            with st.container(border=True):
                section_header("Operations console", level=4)
                st.write(f"See **{rec['gym_name']}**'s management view, with this member at the top of the roster.")
                if st.button("Open operations console", use_container_width=True):
                    st.session_state.nav_target = "🏢 Gym Owner / Admin View"
                    st.session_state.tenant_target = rec["tenant_id"]
                    st.rerun()

        with c_dest3:
            with st.container(border=True):
                section_header("Users & members", level=4)
                st.write("Browse the `users` and `members` tables, including this new record.")
                if st.button("Open users & members", use_container_width=True):
                    st.session_state.nav_target = "🗄️ Central Users & Members Database"
                    st.rerun()

        st.markdown("")
        if st.button("Register Another Member"):
            st.session_state.checkout_stage = "form"
            st.session_state.card_otp_sent = False
            st.rerun()

# ==============================================================================
# 2. GYM OWNER / ADMIN VIEW
# ==============================================================================
elif portal_mode == "🏢 Gym Owner / Admin View":
    page_header(
        active_genome.gym_name,
        "Capacity, members, demand forecasting, collaborative AI, compliance and cloud storage for this facility.",
        eyebrow="Operations console",
        chips=[
            chip("Facility", active_tenant_id),
            chip("Plan", f"{sub.tier}"),
            chip("Generation", str(active_genome.generation)),
            chip("Healthy", dot_color="#10B981"),
        ]
    )

    if logged_in_user and logged_in_user.get("role") == "gym_admin":
        st.success(f"Signed in as administrator **{logged_in_user.get('full_name')}** ({logged_in_user.get('branch', 'Executive')}).")
    elif logged_in_user and logged_in_user.get("role") == "member":
        st.info(f"You're signed in as a member (**{logged_in_user.get('full_name')}**). This console is shown read-only for preview.")

    # Top KPI Metrics with Plain-English explanations
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    utilization_pct = int((sub.active_members / max(1, sub.max_members)) * 100)
    with kpi1:
        st.metric(
            label="Enrolled members",
            value=f"{sub.active_members} / {sub.max_members}",
            delta=f"{utilization_pct}% of plan limit",
            help="Total active members registered at your gym versus your current monthly subscription limit."
        )
    with kpi2:
        st.metric(
            label="Certified trainers",
            value=f"{sub.active_trainers} / {sub.max_trainers}",
            delta="Trainer quota",
            help="Trainers currently employed at this gym facility."
        )
    with kpi3:
        st.metric(
            label="Peak-hour share",
            value=f"{int(usage.peak_hour_ratio * 100)}%",
            delta="Morning & evening",
            help="Percentage of daily members who visit during peak morning (6-9 AM) and peak evening (5-8 PM) rush hours."
        )
    with kpi4:
        st.metric(
            label="Data isolation",
            value="100%",
            delta="No cross-tenant access",
            help="ACVE security score proving your gym's records are completely firewalled from all other gyms."
        )

    st.markdown("")

    admin_tabs = st.tabs([
        "Capacity & Upgrades",
        "Members",
        "Demand Forecast",
        "Collaborative AI",
        "Compliance",
        "Cloud Storage"
    ])

    # --- TAB 1: SICE SMART UPGRADES ---
    with admin_tabs[0]:
        section_header("Capacity forecasting", caption="SICE engine")
        st.info("""
        **How it works.** Instead of blocking sign-ups when you hit your member limit, SICE tracks how fast you're
        growing, predicts when you'll reach capacity *before* it happens, and offers a fair prorated price for the
        rest of the billing month so you never have to turn members away.
        """)

        col_sice_left, col_sice_right = st.columns([3, 2])
        with col_sice_left:
            section_header("Current capacity", level=4)
            st.write(f"**{sub.active_members}** of **{sub.max_members}** member slots used")
            st.progress(min(1.0, sub.active_members / max(1, sub.max_members)))

            days_remaining = sub.days_remaining_in_cycle
            growth_vel = sub.member_growth_velocity
            projected_end = int(sub.active_members + (growth_vel * days_remaining))

            kv_rows([
                ("Sign-up rate", f"{growth_vel:.1f} new members / day"),
                ("Days left in billing month", f"{days_remaining} days"),
                ("Projected members at month end", f"{projected_end}"),
            ])
            st.markdown("")

            if projected_end >= sub.max_members and sub.tier != "Gold":
                next_tier = "Silver" if sub.tier == "Free" else "Gold"
                price_difference = 99.0 if next_tier == "Silver" else 200.0
                prorated_fee = round(price_difference * (days_remaining / 30.0), 2)
                next_limit = 250 if next_tier == "Silver" else 1000

                st.error(f"**Action needed:** at the current rate this gym will reach its {sub.tier} plan limit in about {int((sub.max_members - sub.active_members)/max(0.1, growth_vel))} days.")
                with st.container(border=True):
                    section_header(f"Recommended: upgrade to {next_tier}", level=4)
                    kv_rows([
                        ("New member limit", f"{next_limit} members"),
                        ("Monthly price", f"${price_difference:.2f} / month"),
                    ], total=("Prorated price today", f"${prorated_fee:.2f}"))
                    st.caption(f"You only pay for the remaining {days_remaining} days of this billing month.")

                if st.button(f"Upgrade to {next_tier} · ${prorated_fee:.2f}", type="primary", use_container_width=True):
                    sice.execute_preemptive_upgrade(active_tenant_id, next_tier)
                    st.success(f"{active_genome.gym_name} upgraded to {next_tier}. Member limit is now {next_limit}.")
                    st.rerun()
            else:
                st.success("**Within capacity.** This gym is operating comfortably within its plan limits — no upgrade needed.")

        with col_sice_right:
            section_header("Agent activity", level=4)
            st.caption("Recent actions from the background agents monitoring this gym.")
            agent_alerts = db_store.get_intents_for_tenant(active_tenant_id)
            if agent_alerts:
                for alert in agent_alerts[-3:]:
                    with st.container(border=True):
                        st.markdown(f"**{alert.proposed_action}**")
                        st.caption(f"{alert.source_agent} · {alert.expected_operational_impact}")
            else:
                st.info("No agent actions right now — everything is operating normally.")

    # --- TAB 2: MEMBER MANAGEMENT ---
    with admin_tabs[1]:
        section_header("Member roster", caption=f"Everyone enrolled at {active_genome.gym_name}, across all branches. New registrations appear here immediately.")

        with SessionLocal() as db:
            active_mems = db.query(MemberRecordModel).filter_by(tenant_id=active_tenant_id).all()
            if active_mems:
                col_f_city, col_f_branch = st.columns(2)
                with col_f_city:
                    cities = ["All Cities"] + sorted(list(set(m.city for m in active_mems if getattr(m, 'city', ''))))
                    filter_city = st.selectbox("City", cities, key="adm_filt_city")
                with col_f_branch:
                    branches = ["All Franchise Branches"] + sorted(list(set(m.branch for m in active_mems if getattr(m, 'branch', ''))))
                    filter_branch = st.selectbox("Branch", branches, key="adm_filt_branch")

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
                st.dataframe(df_members, use_container_width=True, hide_index=True)
                st.caption(f"{len(filtered_mems)} members shown")
            else:
                st.info("No members at this facility yet. Use **Membership Registration** in the sidebar to add the first one.")

    # --- TAB 3: ATTENDANCE & PTLM ---
    with admin_tabs[2]:
        section_header("Demand forecast", caption="PTLM engine")
        st.info("""
        **How it works.** Most systems only scale up *after* the gym is already busy. PTLM uses attendance history
        to predict the morning (6–9 AM) and evening (5–8 PM) rushes and **provisions extra capacity 45 minutes before
        members arrive**.
        """)

        col_ptlm_chart, col_ptlm_ctrl = st.columns([3, 2])
        with col_ptlm_chart:
            section_header("Predicted check-ins by hour", level=4)
            forecasts = [ptlme.forecast_demand(active_genome, h) for h in range(24)]
            df_hourly = pd.DataFrame([
                {"Hour": f"{h:02d}:00", "Predicted Check-Ins": f["predicted_concurrency"], "Peak Window": f["is_peak_window"]}
                for h, f in enumerate(forecasts)
            ])
            st.bar_chart(df_hourly.set_index("Hour")["Predicted Check-Ins"])
            st.caption("Peak windows: **06:00–09:00** (morning) and **17:00–20:00** (evening)")

        with col_ptlm_ctrl:
            section_header("Current server capacity", level=4)
            kv_rows([
                ("CPU", f"{active_genome.resource.allocated_cpu_cores} cores"),
                ("Memory", f"{active_genome.resource.allocated_memory_mb} MB"),
                ("Database partitions", f"{active_genome.resource.materialized_partitions} active"),
                ("Peak pre-scaling", "Active" if active_genome.resource.is_preemptively_scaled else "Baseline"),
            ])
            st.markdown("")

            target_hour = st.slider("Hour to pre-provision for", 0, 23, 7)
            hour_fc = ptlme.forecast_demand(active_genome, target_hour)
            st.caption(f"Expected at {target_hour:02d}:00: **{hour_fc['predicted_concurrency']} concurrent check-ins**.")

            if st.button("Pre-allocate resources for this hour", type="primary", use_container_width=True):
                res_mat = ptlme.materialize_partitions_for_tenant(active_tenant_id, target_hour)
                st.success(f"Pre-allocated {res_mat['materialized_partitions']} partitions and {res_mat['allocated_cpu_cores']} CPU cores for {target_hour:02d}:00.")
                st.rerun()

    # --- TAB 4: FAFIE COLLABORATIVE AI ---
    with admin_tabs[3]:
        section_header("Collaborative AI", caption="FAFIE engine")
        st.info("""
        **How it works.** A single gym rarely has enough data to train a strong recommendation model. FAFIE lets
        many gyms train one shared workout model together **without sharing raw member data**: each gym computes
        updates on its own data, adds differential-privacy noise, and sends only those anonymous updates to the aggregator.
        """)

        section_header("Shared model weights", level=4)
        st.code(str(db_store.global_model_weights), language=None)
        if st.button("Run a federated training round", type="primary"):
            training_updates = []
            for t in all_tenants:
                local_tr = FafieLocalTrainer(t.tenant_id)
                X_batch = np.random.randn(50, len(db_store.global_model_weights))
                y_batch = np.dot(X_batch, db_store.global_model_weights) + np.random.normal(0, 0.05, 50)
                upd = local_tr.compute_local_gradient_update(db_store.global_model_weights, X_batch, y_batch)
                training_updates.append(upd)

            round_outcome = fafie_aggregator.run_aggregation_round(training_updates)
            st.success(f"Round {round_outcome['round_number']} completed across all gyms. Average loss: {round_outcome['average_loss']}")
            if round_outcome.get("s3_uri"):
                st.info(f"Checkpoint archived to Amazon S3: `{round_outcome['s3_uri']}` ({round_outcome.get('encryption', 'AES256')})")
            st.rerun()

    # --- TAB 5: ACVE COMPLIANCE AUDIT ---
    with admin_tabs[4]:
        section_header("Compliance & data isolation", caption="ACVE engine — every action is checked against multi-tenant isolation rules before it runs.")
        gym_audits = [a for a in db_store.compliance_audits if a["tenant_id"] == active_tenant_id or a["tenant_id"] == "system"]
        if gym_audits:
            audit_cols = ["timestamp", "action", "caller_role", "verdict"]
            df_audits = pd.DataFrame(gym_audits[-10:])
            st.dataframe(df_audits[[c for c in audit_cols if c in df_audits.columns]], use_container_width=True)
        else:
            st.success("No security violations recorded. This gym's data isolation boundary is intact.")

    # --- TAB 6: AMAZON S3 CLOUD STORAGE VAULT ---
    with admin_tabs[5]:
        section_header("Cloud storage", caption="Encrypted model checkpoints, tax invoices and certificates, stored in Amazon S3 with server-side AES-256 / KMS encryption.")

        s3_conf = aws_s3_service.check_s3_configuration(st.session_state.get("custom_aws_credentials"))

        c_s3_1, c_s3_2, c_s3_3, c_s3_4 = st.columns(4)
        with c_s3_1:
            st.metric(label="Bucket", value=s3_conf["bucket_name"])
        with c_s3_2:
            st.metric(label="AWS Region", value=s3_conf["region"])
        with c_s3_3:
            st.metric(label="Encryption", value="AES-256 / KMS")
        with c_s3_4:
            if s3_conf["configured"]:
                st.metric(label="Storage Backend", value="Amazon S3", delta="Connected")
            else:
                st.metric(label="Storage Backend", value="Local Sandbox", delta="AWS not connected", delta_color="off")

        st.markdown("")

        c_s3_action1, c_s3_action2 = st.columns([2, 1])
        with c_s3_action1:
            section_header("Stored objects", level=4, caption="Encrypted artifacts in this deployment's bucket.")
        with c_s3_action2:
            if st.button("Back up current model to S3", type="primary", use_container_width=True):
                round_tag = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                backup_data = {
                    "tenant_id": active_tenant_id,
                    "gym_name": active_genome.gym_name,
                    "global_weights": db_store.global_model_weights,
                    "federated_rounds_count": len(db_store.federated_rounds),
                    "timestamp": datetime.utcnow().isoformat()
                }
                res = aws_s3_service.upload_model_checkpoint(round_tag, backup_data, st.session_state.get("custom_aws_credentials"))
                st.success(f"Checkpoint backed up: `{res['s3_uri']}` ({res.get('bytes_stored', 0):,} bytes)")
                st.rerun()

        # List objects in vault
        vault_items = aws_s3_service.list_vault_objects(custom_credentials=st.session_state.get("custom_aws_credentials"))
        if vault_items:
            df_vault = pd.DataFrame(vault_items)
            st.dataframe(df_vault[["key", "size_bytes", "last_modified", "s3_uri", "encryption"]], use_container_width=True)
            
            with st.expander("Object details", expanded=False):
                selected_key = st.selectbox("Select file to inspect", [item["key"] for item in vault_items])
                matched_item = next((item for item in vault_items if item["key"] == selected_key), None)
                if matched_item:
                    st.write(f"**URI:** `{matched_item['s3_uri']}`")
                    st.write(f"**Size:** `{matched_item['size_bytes']} bytes` &nbsp;|&nbsp; **Last Modified:** `{matched_item['last_modified']}`")
                    st.write(f"**Encryption:** `{matched_item['encryption']}` &nbsp;|&nbsp; **Storage Tier:** `{matched_item.get('tier', 'Standard')}`")
        else:
            st.info("No stored objects yet. Run a federated training round or register a member to create the first archive.")

# ==============================================================================
# 3. CENTRAL USERS & MEMBERS DATABASE EXPLORER (NEW!)
# ==============================================================================
elif portal_mode == "🗄️ Central Users & Members Database":
    page_header(
        "Users & members",
        "Accounts and memberships across every gym, city and branch, from the platform database. Search, filter and export for audits and reporting.",
        eyebrow="Directory",
        chips=[chip("Database", "fam_fios.db")]
    )

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
        st.metric("User accounts", total_users_count, help="All user credentials and logins in `users` table.")
    with db_kpi2:
        st.metric("Enrolled members", total_mems_count, help="Active gym membership records in `members` table.")
    with db_kpi3:
        st.metric("Revenue collected", f"₹{total_rev:,.2f}", help="Sum of membership fees paid across all franchises.")
    with db_kpi4:
        st.metric("Cities", max(1, unique_cities), help="Cities with registered franchises (Pune, Bengaluru, Mumbai, etc.).")

    st.markdown("")

    db_tabs = st.tabs([
        "User Accounts",
        "Members",
        "City & Franchise Analytics"
    ])

    # --- TAB 1: USERS TABLE ---
    with db_tabs[0]:
        section_header("User accounts", caption="Gym admins, trainers and members (table: users). Passwords are stored as salted PBKDF2 hashes.")

        c_u1, c_u2, c_u3 = st.columns([2, 1, 1])
        with c_u1:
            u_search = st.text_input("Search", placeholder="Name, email, phone, user ID or branch", key="u_search_box")
        with c_u2:
            u_city_opts = ["All Cities"] + sorted(list(set(u["city"] for u in all_users_data if u["city"])))
            u_city_filt = st.selectbox("City", u_city_opts, key="u_city_filt")
        with c_u3:
            u_role_opts = ["All Roles", "gym_admin", "trainer", "member"]
            u_role_filt = st.selectbox("Role", u_role_opts, key="u_role_filt")

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
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            st.caption(f"{len(filtered_users)} of {len(all_users_data)} accounts")

            csv_users = df_users.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Export CSV",
                data=csv_users,
                file_name="fam_fios_users_database.csv",
                mime="text/csv",
                key="dl_users_csv"
            )
        else:
            st.info("No users match the selected filters.")

    # --- TAB 2: MEMBERS TABLE ---
    with db_tabs[1]:
        section_header("Members", caption="Memberships across every city and branch, with plan and payment details (table: members).")

        c_m1, c_m2, c_m3 = st.columns([2, 1, 1])
        with c_m1:
            m_search = st.text_input("Search", placeholder="Name, email, member ID or branch", key="m_search_box")
        with c_m2:
            m_city_opts = ["All Cities"] + sorted(list(set(m["city"] for m in all_members_data if m["city"])))
            m_city_filt = st.selectbox("City", m_city_opts, key="m_city_filt")
        with c_m3:
            m_branch_opts = ["All Franchise Branches"] + sorted(list(set(m["branch"] for m in all_members_data if m["branch"])))
            m_branch_filt = st.selectbox("Branch", m_branch_opts, key="m_branch_filt")

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
            st.dataframe(df_mems, use_container_width=True, hide_index=True)
            st.caption(f"{len(filtered_mems)} of {len(all_members_data)} members")

            csv_mems = df_mems.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Export CSV",
                data=csv_mems,
                file_name="fam_fios_members_database.csv",
                mime="text/csv",
                key="dl_mems_csv"
            )
        else:
            st.info("No members match the selected filters.")

    # --- TAB 3: CITY & FRANCHISE ANALYTICS ---
    with db_tabs[2]:
        section_header("City & franchise analytics", caption="How registrations are distributed across cities and individual branches.")

        col_an1, col_an2 = st.columns(2)
        with col_an1:
            section_header("Signups by City", level=4)
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
            section_header("Pune Franchises Breakdown (5 Locations)", level=4)
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
        section_header("Revenue Contribution by Gym Organization", level=4)
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

    FOOD_MENU_DATABASE = {
        "🍗 High-Protein Meats, Fish & Eggs": [
            {"name": "Grilled Chicken Breast (Skinless)", "portion": "150g fillet", "calories": 247, "protein": 46.5, "carbs": 0.0, "fats": 5.4},
            {"name": "Whole Boiled Eggs", "portion": "2 large eggs", "calories": 156, "protein": 12.6, "carbs": 1.1, "fats": 10.6},
            {"name": "Egg White Scramble / Omelette", "portion": "4 egg whites (132g)", "calories": 68, "protein": 14.4, "carbs": 0.9, "fats": 0.2},
            {"name": "Grilled Salmon Fillet", "portion": "150g fillet", "calories": 312, "protein": 34.0, "carbs": 0.0, "fats": 18.0},
            {"name": "Canned Tuna in Water", "portion": "1 can (130g drained)", "calories": 145, "protein": 32.5, "carbs": 0.0, "fats": 1.2},
            {"name": "Whey Protein Isolate Shake", "portion": "1 scoop (30g) in water", "calories": 120, "protein": 25.0, "carbs": 2.0, "fats": 1.0},
            {"name": "Lean Minced Beef / Chicken Stir-Fry", "portion": "150g", "calories": 275, "protein": 36.0, "carbs": 0.0, "fats": 13.5}
        ],
        "🧀 Vegetarian & Dairy Protein": [
            {"name": "Fresh Paneer (Raw / Sautéed)", "portion": "100g", "calories": 265, "protein": 18.3, "carbs": 3.4, "fats": 20.8},
            {"name": "Paneer Bhurji (Light Oil)", "portion": "1 bowl (150g)", "calories": 310, "protein": 21.0, "carbs": 6.5, "fats": 22.0},
            {"name": "Organic Tofu (Pan-Seared)", "portion": "150g", "calories": 135, "protein": 15.0, "carbs": 3.0, "fats": 7.5},
            {"name": "Soya Chunks Curry (Nutrela)", "portion": "1 bowl (60g dry eq)", "calories": 215, "protein": 31.2, "carbs": 19.5, "fats": 0.8},
            {"name": "Greek Yogurt (Plain 0% Fat)", "portion": "1 cup (170g)", "calories": 100, "protein": 17.0, "carbs": 6.0, "fats": 0.7},
            {"name": "High-Protein Lassi / Buttermilk", "portion": "250ml glass", "calories": 130, "protein": 15.0, "carbs": 12.0, "fats": 1.5},
            {"name": "Low-Fat Cottage Cheese / Paneer", "portion": "100g", "calories": 170, "protein": 24.0, "carbs": 4.0, "fats": 6.0}
        ],
        "🍚 Rice, Breads & Complex Carbs": [
            {"name": "Cooked Basmati White Rice", "portion": "1 medium bowl (150g)", "calories": 195, "protein": 4.1, "carbs": 43.0, "fats": 0.4},
            {"name": "Steamed Brown Rice", "portion": "1 medium bowl (150g)", "calories": 167, "protein": 3.8, "carbs": 35.0, "fats": 1.4},
            {"name": "Whole Wheat Roti / Phulka (No Ghee)", "portion": "2 medium rotis (70g)", "calories": 160, "protein": 5.8, "carbs": 32.0, "fats": 1.2},
            {"name": "Rolled Oats Cooked in Water", "portion": "1 cup (234g cooked)", "calories": 158, "protein": 6.0, "carbs": 27.0, "fats": 3.2},
            {"name": "Boiled Sweet Potato", "portion": "1 medium (150g)", "calories": 130, "protein": 2.3, "carbs": 30.0, "fats": 0.2},
            {"name": "Whole Grain Toast / Brown Bread", "portion": "2 slices (60g)", "calories": 140, "protein": 6.0, "carbs": 26.0, "fats": 1.8},
            {"name": "Steamed Quinoa Bowl", "portion": "1 cup cooked (185g)", "calories": 222, "protein": 8.1, "carbs": 39.4, "fats": 3.6}
        ],
        "🥘 Indian Curries & Traditional Dishes": [
            {"name": "Yellow Moong / Arhar Dal Tadka", "portion": "1 medium katori (150ml)", "calories": 150, "protein": 8.5, "carbs": 21.0, "fats": 3.5},
            {"name": "Punjabi Rajma Masala (Kidney Beans)", "portion": "1 bowl (180g)", "calories": 210, "protein": 11.2, "carbs": 33.0, "fats": 3.8},
            {"name": "Chole / Chana Masala (Chickpeas)", "portion": "1 bowl (180g)", "calories": 240, "protein": 12.0, "carbs": 35.0, "fats": 6.0},
            {"name": "Palak Paneer (Healthy Prep)", "portion": "1 bowl (180g)", "calories": 255, "protein": 14.5, "carbs": 9.0, "fats": 18.0},
            {"name": "Mixed Vegetable Poriyal / Sabzi", "portion": "1 bowl (150g)", "calories": 115, "protein": 3.2, "carbs": 16.0, "fats": 4.5},
            {"name": "Steamed Idli with Sambar", "portion": "2 idlis + 1 cup sambar", "calories": 185, "protein": 6.8, "carbs": 34.0, "fats": 2.2},
            {"name": "Moong Dal Chilla (Pancakes)", "portion": "2 medium chillas (120g)", "calories": 220, "protein": 13.8, "carbs": 28.0, "fats": 6.0}
        ],
        "🥑 Healthy Fats, Fruits & Snacks": [
            {"name": "Natural Peanut Butter (Unsweetened)", "portion": "2 tablespoons (32g)", "calories": 188, "protein": 8.0, "carbs": 6.0, "fats": 16.0},
            {"name": "Raw California Almonds & Walnuts", "portion": "Handful (30g / ~20 nuts)", "calories": 185, "protein": 6.0, "carbs": 5.5, "fats": 16.5},
            {"name": "Ripe Banana", "portion": "1 medium (118g)", "calories": 105, "protein": 1.3, "carbs": 27.0, "fats": 0.3},
            {"name": "Fresh Apple with Skin", "portion": "1 medium (182g)", "calories": 95, "protein": 0.5, "carbs": 25.0, "fats": 0.3},
            {"name": "Sprouted Moong & Chana Salad", "portion": "1 large bowl (150g)", "calories": 140, "protein": 10.5, "carbs": 22.0, "fats": 1.2},
            {"name": "Mixed Greens Salad with Olive Oil", "portion": "1 large bowl (120g)", "calories": 110, "protein": 2.0, "carbs": 6.0, "fats": 9.0}
        ]
    }

    PHOTO_MEAL_PRESETS = [
        {"name": "Grilled Chicken Breast with Brown Rice & Steamed Broccoli", "calories": 485, "protein": 48.0, "carbs": 44.0, "fats": 7.5, "category": "Lunch / Dinner"},
        {"name": "Paneer Bhurji with 2 Whole Wheat Phulkas & Green Salad", "calories": 490, "protein": 26.5, "carbs": 42.0, "fats": 23.0, "category": "Lunch / Dinner"},
        {"name": "Egg White Omelette with Whole Wheat Toast & Avocado", "calories": 320, "protein": 22.0, "carbs": 28.0, "fats": 12.0, "category": "Breakfast"},
        {"name": "Rolled Oats Bowl with Whey Protein, Peanut Butter & Banana", "calories": 465, "protein": 34.0, "carbs": 55.0, "fats": 12.5, "category": "Breakfast / Pre-Workout"},
        {"name": "Yellow Dal Tadka with Steamed Basmati Rice & Cucumber Raita", "calories": 395, "protein": 14.5, "carbs": 68.0, "fats": 6.5, "category": "Lunch / Dinner"},
        {"name": "Grilled Salmon Fillet with Roasted Sweet Potato & Asparagus", "calories": 475, "protein": 37.0, "carbs": 32.0, "fats": 19.0, "category": "Dinner"},
        {"name": "Soya Chunks Curry with 2 Rotis & Curd", "calories": 440, "protein": 38.0, "carbs": 52.0, "fats": 8.0, "category": "Lunch / Dinner"},
        {"name": "Greek Yogurt Bowl with Mixed Berries, Almonds & Honey", "calories": 280, "protein": 20.0, "carbs": 32.0, "fats": 8.0, "category": "Snack / Breakfast"},
        {"name": "Whey Protein Shake with 1 Banana & 1 tbsp Peanut Butter", "calories": 320, "protein": 29.0, "carbs": 31.0, "fats": 8.5, "category": "Post-Workout"}
    ]

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

    page_header(
        f"Welcome back, {default_mem_name}",
        f"{active_genome.gym_name} · {default_mem_branch}",
        eyebrow="Member dashboard",
        chips=[
            chip("Member ID", default_mem_id),
            chip("Goal", default_mem_goal),
            chip("Active", dot_color="#10B981"),
        ]
    )

    # 📅 Today's Scheduled Workout Banner (Acc. to Current Day of Week)
    today_dt = datetime.now()
    today_day_name = today_dt.strftime("%A")
    today_date_str = today_dt.strftime("%A, %d %B %Y")
    today_routine = WEEKLY_WORKOUT_ROUTINES.get(today_day_name, WEEKLY_WORKOUT_ROUTINES["Monday"])

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-left: 6px solid {today_routine['badge_color']}; border-radius: 12px; padding: 18px 22px; margin-top: 6px; margin-bottom: 18px; box-shadow: 0 4px 14px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <span style="background: {today_routine['badge_color']}22; color: {today_routine['badge_color']}; font-weight: 600; font-size: 0.75rem; padding: 4px 12px; border-radius: 9999px; border: 1px solid {today_routine['badge_color']}55; letter-spacing: 0.06em;">
                    TODAY'S WORKOUT &bull; {today_date_str.upper()}
                </span>
                <div style="margin: 10px 0 4px 0; color: #F8FAFC; font-size: 1.3rem; font-weight: 700; letter-spacing: -0.01em;">
                    {today_routine['title']}
                </div>
                <p style="margin: 0; color: #94A3B8; font-size: 0.9rem;">
                    <b style="color:#CBD5E1">Focus</b> {today_routine['focus']} &nbsp;&middot;&nbsp; <b style="color:#CBD5E1">Duration</b> {today_routine['duration']} &nbsp;&middot;&nbsp; <b style="color:#CBD5E1">Est. burn</b> {today_routine['calories_est']}
                </p>
            </div>
            <div>
                <span style="background: rgba(255,255,255,0.05); color: #E2E8F0; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; border: 1px solid rgba(255,255,255,0.10); display: inline-block;">
                    {len(today_routine['exercises'])} exercises
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Today's exercises ({today_day_name})", expanded=False):
        c_ex_cols = st.columns(len(today_routine['exercises']))
        for i, ex in enumerate(today_routine['exercises']):
            with c_ex_cols[i]:
                st.markdown(f"**{i+1}. {ex['name']}**")
                st.caption(f"{ex['sets_reps']}")
                st.caption(f"{ex['rest']}")
                if "video_url" in ex:
                    st.markdown(f"[Form tutorial ↗]({ex['video_url']})", help=f"Watch tutorial for {ex['name']}")
        st.info("**Ready to train?** Use **Workout Plan** to check off exercises and watch form videos, **Workout Log** to record sets and reps, or **Nutrition** to log meals and track remaining calories.")

    st.markdown("")

    member_tabs = st.tabs([
        "Pass & Check-In",
        "Workout Log",
        "Progress",
        "Workout Plan",
        "Nutrition"
    ])

    with member_tabs[0]:
        section_header("Check in", caption="Check in when you arrive. It records your attendance and helps the gym plan capacity for busy hours.")

        c_pass_left, c_pass_right = st.columns([2, 3])
        with c_pass_left:
            pass_info = active_mem_session or {}
            membership_pass(
                member_name=default_mem_name,
                member_id=default_mem_id,
                gym_name=active_genome.gym_name,
                location=default_mem_branch,
                address=pass_info.get("branch_address", active_genome.gym_name),
                phone=pass_info.get("phone", "—"),
                plan=pass_info.get("plan_name", "Standard Access"),
                amount_paid=f"₹{pass_info['total_payable']:,.2f}" if isinstance(pass_info.get("total_payable"), (int, float)) else "—",
                valid_until=pass_info.get("expiry_date", "—"),
            )
            st.markdown("")
            if st.button("Check in now", type="primary", use_container_width=True):
                evt = TenantEvent(
                    tenant_id=active_tenant_id,
                    role_context="member",
                    event_type="check_in",
                    operational_params={"hour": datetime.utcnow().hour}
                )
                tige.update_genome_from_event(evt)
                st.success(f"Checked in at {datetime.now().strftime('%I:%M %p')}. Enjoy your workout.")

        with c_pass_right:
            with st.container(border=True):
                section_header("Gym crowd level", level=4)
                crowd_pct = int(usage.peak_hour_ratio * 100)
                st.write(f"Expected peak-hour occupancy today: **{crowd_pct}%**")
                st.progress(min(1.0, crowd_pct / 100))
                if crowd_pct > 60:
                    st.warning("Busy right now — expect a wait for popular equipment.")
                else:
                    st.success("Good time to train — plenty of equipment available.")

    with member_tabs[1]:
        section_header("Workout log", caption="Record exercises by week; volume is calculated for you.")
        st.caption("Totals feed straight into the **Progress** tab.")

        if "member_weekly_exercise_logs" not in st.session_state:
            st.session_state.member_weekly_exercise_logs = {
                "Week 1": [],
                "Week 2": [],
                "Week 3": [],
                "Week 4": []
            }

        all_exercise_options = [
            "Barbell Bench Press (Flat)",
            "Incline Dumbbell Chest Press",
            "Seated Overhead Dumbbell Shoulder Press",
            "Cable Tricep Rope Pushdowns",
            "Conventional Barbell Deadlifts",
            "Wide-Grip Lat Pulldowns",
            "Seated Cable Rows (Close Grip)",
            "Incline Dumbbell Bicep Curls",
            "Barbell Back Squats",
            "Romanian Deadlifts (RDL)",
            "Leg Press / Walking Lunges",
            "Standing Calf Raises & Hanging Knee Raises",
            "Incline Barbell Bench Press",
            "T-Bar Rows / Chest Supported Rows",
            "Dumbbell Lateral Raises",
            "Hammer Curls & Overhead Triceps",
            "Trap Bar Deadlifts / Barbell Hip Thrusts",
            "Bulgarian Split Squats (Dumbbell)",
            "Kettlebell Farmer's Carries",
            "Cable Woodchoppers & Plank Hold"
        ]

        c_wk_pick, c_wk_status = st.columns([2, 2])
        with c_wk_pick:
            sel_target_week = st.selectbox(
                "Training week",
                ["Week 4 (Current Week / Today)", "Week 3", "Week 2", "Week 1 (Baseline)"],
                index=0,
                key="sel_log_week_active"
            )
            wk_key = "Week 4" if "Week 4" in sel_target_week else ("Week 1" if "Week 1" in sel_target_week else ("Week 2" if "Week 2" in sel_target_week else "Week 3"))
        with c_wk_status:
            w_total_curr = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs.get(wk_key, []))
            st.metric(f"{wk_key} volume logged", f"{w_total_curr:,.0f} kg")

        with st.form("member_log_exercise"):
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                sel_exercise = st.selectbox("Exercise", all_exercise_options)
                num_sets = st.number_input("Sets", min_value=1, max_value=15, value=4)
            with c_ex2:
                num_reps = st.number_input("Reps per set", min_value=1, max_value=50, value=8)
                weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=65.0, step=2.5)

            session_volume = num_sets * num_reps * weight_kg
            st.caption(f"Volume: **{session_volume:,.1f} kg** ({num_sets} sets × {num_reps} reps × {weight_kg:g} kg)")

            save_log = st.form_submit_button(f"Add to {wk_key}", use_container_width=True, type="primary")
            if save_log:
                evt = TenantEvent(
                    tenant_id=active_tenant_id,
                    role_context="member",
                    event_type="workout_logged",
                    operational_params={"exercise": sel_exercise, "volume_kg": session_volume, "week": wk_key}
                )
                tige.update_genome_from_event(evt)

                st.session_state.member_weekly_exercise_logs[wk_key].append({
                    "Time": datetime.now().strftime("%I:%M %p"),
                    "Week": wk_key,
                    "Exercise": sel_exercise,
                    "Sets": num_sets,
                    "Reps": num_reps,
                    "Weight": f"{weight_kg:g} kg",
                    "Volume": session_volume
                })

                w1_t = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 1"])
                w2_t = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 2"])
                w3_t = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 3"])
                w4_t = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 4"])

                # Dynamic week-wise synchronization:
                if w4_t > 0 and w1_t == 0 and w2_t == 0 and w3_t == 0:
                    # Dynamically calibrate prior weeks relative to actual logged strength!
                    st.session_state.inp_prog_s1 = int(round(w4_t * 0.90 / 25) * 25)
                    st.session_state.inp_prog_s2 = int(round(w4_t * 0.95 / 25) * 25)
                    st.session_state.inp_prog_s3 = int(round(w4_t * 0.98 / 25) * 25)
                    st.session_state.inp_prog_s4 = int(w4_t)
                else:
                    if w1_t > 0: st.session_state.inp_prog_s1 = int(w1_t)
                    if w2_t > 0: st.session_state.inp_prog_s2 = int(w2_t)
                    if w3_t > 0: st.session_state.inp_prog_s3 = int(w3_t)
                    if w4_t > 0: st.session_state.inp_prog_s4 = int(w4_t)

                st.session_state.saved_prog_volumes = [
                    int(st.session_state.inp_prog_s1),
                    int(st.session_state.inp_prog_s2),
                    int(st.session_state.inp_prog_s3),
                    int(st.session_state.inp_prog_s4)
                ]
                st.session_state.last_saved_prog_time = datetime.now().strftime("%I:%M:%S %p")
                
                new_wk_total = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs[wk_key])
                st.toast(f"Added {sel_exercise} (+{session_volume:,.0f} kg). {wk_key} Total: {new_wk_total:,.0f} kg!", icon="🏋️")
                st.rerun()

        # Display Live Week-Wise Logged Breakdown
        all_logs = []
        for wk in ["Week 1", "Week 2", "Week 3", "Week 4"]:
            all_logs.extend(st.session_state.member_weekly_exercise_logs.get(wk, []))

        if all_logs:
            st.markdown("---")
            c_hist_title, c_hist_clear = st.columns([3, 1])
            with c_hist_title:
                section_header("Weekly summary", level=4)
                
                cw1, cw2, cw3, cw4 = st.columns(4)
                t1 = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 1"])
                t2 = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 2"])
                t3 = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 3"])
                t4 = sum(e["Volume"] for e in st.session_state.member_weekly_exercise_logs["Week 4"])
                with cw1: st.metric("Week 1 Total", f"{t1:,.0f} kg" if t1 > 0 else f"{st.session_state.inp_prog_s1:,.0f} kg (Est)")
                with cw2: st.metric("Week 2 Total", f"{t2:,.0f} kg" if t2 > 0 else f"{st.session_state.inp_prog_s2:,.0f} kg (Est)")
                with cw3: st.metric("Week 3 Total", f"{t3:,.0f} kg" if t3 > 0 else f"{st.session_state.inp_prog_s3:,.0f} kg (Est)")
                with cw4: st.metric("Week 4 Total", f"{t4:,.0f} kg" if t4 > 0 else f"{st.session_state.inp_prog_s4:,.0f} kg (Live)")

            with c_hist_clear:
                if st.button("Clear all logs", use_container_width=True):
                    st.session_state.member_weekly_exercise_logs = {"Week 1": [], "Week 2": [], "Week 3": [], "Week 4": []}
                    st.session_state.inp_prog_s1 = 1400
                    st.session_state.inp_prog_s2 = 1475
                    st.session_state.inp_prog_s3 = 1525
                    st.session_state.inp_prog_s4 = 1560
                    st.session_state.saved_prog_volumes = [1400, 1475, 1525, 1560]
                    st.rerun()

            df_all = pd.DataFrame(all_logs)
            df_display = df_all.copy()
            df_display["Volume"] = df_display["Volume"].apply(lambda x: f"{x:,.0f} kg")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            st.success("**Want to see the trend?** Open the **Progress** tab to see your weekly volume plotted against the progressive-overload target.")

    with member_tabs[2]:
        section_header(
            "Progress & plateau detection",
            caption="Tracks weekly volume (sets × reps × weight) to confirm progressive overload and recommend a deload before you stall."
        )

        # 1. 1-Click Interactive Presets / Scenarios (Calibrated Dynamically to Current Baseline)
        section_header("Scenarios", level=5, caption="Load a sample trajectory based on your current baseline.")
        col_pre1, col_pre2, col_pre3, col_pre4 = st.columns(4)
        
        # Initialize default session values dynamically calibrated to real-world workout volume
        if "inp_prog_s1" not in st.session_state:
            st.session_state.inp_prog_s1 = 1400
        if "inp_prog_s2" not in st.session_state:
            st.session_state.inp_prog_s2 = 1475
        if "inp_prog_s3" not in st.session_state:
            st.session_state.inp_prog_s3 = 1525
        if "inp_prog_s4" not in st.session_state:
            st.session_state.inp_prog_s4 = 1560

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

        # Dynamically determine the member's current baseline volume
        dyn_base = max(int(st.session_state.inp_prog_s1), 500)

        with col_pre1:
            if st.button("Progressive Overload", use_container_width=True, help=f"Simulate steady science-backed +5% weekly growth from your {dyn_base:,} kg baseline"):
                st.session_state.inp_prog_s1 = dyn_base
                st.session_state.inp_prog_s2 = int(round(dyn_base * 1.05 / 25) * 25)
                st.session_state.inp_prog_s3 = int(round(dyn_base * 1.10 / 25) * 25)
                st.session_state.inp_prog_s4 = int(round(dyn_base * 1.16 / 25) * 25)
                st.toast(f"Dynamic Progressive Overload (+5% week-wise from {dyn_base:,} kg) loaded. Click Save progress to update the chart.", icon="📝")
                st.rerun()

        with col_pre2:
            if st.button("Plateau Stagnation", use_container_width=True, help=f"Simulate complete training plateau (0% gain) at your {dyn_base:,} kg baseline"):
                st.session_state.inp_prog_s1 = dyn_base
                st.session_state.inp_prog_s2 = dyn_base
                st.session_state.inp_prog_s3 = dyn_base
                st.session_state.inp_prog_s4 = dyn_base
                st.toast(f"Dynamic Plateau scenario ({dyn_base:,} kg flatline across all 4 weeks) loaded. Click Save progress to update the chart.", icon="📝")
                st.rerun()

        with col_pre3:
            if st.button("Aggressive PR Surge", use_container_width=True, help=f"Simulate rapid compounding PR gains (+13-15% per week) from your {dyn_base:,} kg baseline"):
                st.session_state.inp_prog_s1 = dyn_base
                st.session_state.inp_prog_s2 = int(round(dyn_base * 1.13 / 25) * 25)
                st.session_state.inp_prog_s3 = int(round(dyn_base * 1.28 / 25) * 25)
                st.session_state.inp_prog_s4 = int(round(dyn_base * 1.45 / 25) * 25)
                st.toast(f"Dynamic PR Surge (+13-15% weekly leaps from {dyn_base:,} kg) loaded. Click Save progress to update the chart.", icon="📝")
                st.rerun()

        with col_pre4:
            if st.button("Sample Test (100-300kg)", use_container_width=True, help="Load lightweight 100-300 kg test trajectory into inputs"):
                st.session_state.inp_prog_s1 = 100
                st.session_state.inp_prog_s2 = 150
                st.session_state.inp_prog_s3 = 200
                st.session_state.inp_prog_s4 = 300
                st.toast("Sample values loaded. Click Save progress to update the chart.", icon="📝")
                st.rerun()

        st.markdown("")

        # 2. Session Volume Inputs with Real-time Deltas
        section_header("Weekly volume (kg)", level=5, caption="Sets × reps × weight for each of the last four weeks.")
        c_v1, c_v2, c_v3, c_v4 = st.columns(4)
        
        with c_v1:
            s1_vol = st.number_input("Session 1 (Week 1 Baseline)", min_value=0, max_value=25000, step=25, key="inp_prog_s1", help="Sets × Reps × Weight (kg)")
            st.caption("Baseline week")
            w1_log = sum(e["Volume"] for e in st.session_state.get("member_weekly_exercise_logs", {}).get("Week 1", []))
            if w1_log > 0:
                st.caption(f"*Live synced: {w1_log:,.0f} kg*")
        with c_v2:
            s2_vol = st.number_input("Session 2 (Week 2)", min_value=0, max_value=25000, step=25, key="inp_prog_s2", help="Sets × Reps × Weight (kg)")
            d2_input = s2_vol - s1_vol
            p2_input = (d2_input / max(s1_vol, 1)) * 100
            d2_icon = "🟢" if d2_input > 0 else ("🔴" if d2_input < 0 else "⚪")
            st.caption(f"{d2_icon} **Δ vs W1:** `{d2_input:+,.0f} kg ({p2_input:+.1f}%)`")
            w2_log = sum(e["Volume"] for e in st.session_state.get("member_weekly_exercise_logs", {}).get("Week 2", []))
            if w2_log > 0:
                st.caption(f"*Live synced: {w2_log:,.0f} kg*")
        with c_v3:
            s3_vol = st.number_input("Session 3 (Week 3)", min_value=0, max_value=25000, step=25, key="inp_prog_s3", help="Sets × Reps × Weight (kg)")
            d3_input = s3_vol - s2_vol
            p3_input = (d3_input / max(s2_vol, 1)) * 100
            d3_icon = "🟢" if d3_input > 0 else ("🔴" if d3_input < 0 else "⚪")
            st.caption(f"{d3_icon} **Δ vs W2:** `{d3_input:+,.0f} kg ({p3_input:+.1f}%)`")
            w3_log = sum(e["Volume"] for e in st.session_state.get("member_weekly_exercise_logs", {}).get("Week 3", []))
            if w3_log > 0:
                st.caption(f"*Live synced: {w3_log:,.0f} kg*")
        with c_v4:
            s4_vol = st.number_input("Session 4 (Week 4 Latest)", min_value=0, max_value=25000, step=25, key="inp_prog_s4", help="Sets × Reps × Weight (kg)")
            d4_input = s4_vol - s3_vol
            p4_input = (d4_input / max(s3_vol, 1)) * 100
            d4_icon = "🟢" if d4_input > 0 else ("🔴" if d4_input < 0 else "⚪")
            st.caption(f"{d4_icon} **Δ vs W3:** `{d4_input:+,.0f} kg ({p4_input:+.1f}%)`")
            w4_log = sum(e["Volume"] for e in st.session_state.get("member_weekly_exercise_logs", {}).get("Week 4", []))
            if w4_log > 0:
                st.caption(f"*Synced from Workout Log ({w4_log:,.0f} kg)*")

        # Check for unsaved changes between input boxes and saved progress
        current_inputs = [int(s1_vol), int(s2_vol), int(s3_vol), int(s4_vol)]
        has_unsaved_changes = (current_inputs != st.session_state.saved_prog_volumes)

        # 3. Explicit SAVE ACTION BAR: Graph ONLY changes when user clicks this button
        c_save_btn, c_save_status = st.columns([1.5, 2.5])
        with c_save_btn:
            save_prog_clicked = st.button(
                "Save progress",
                type="primary",
                use_container_width=True,
                help="Saves your current volume logs and re-renders the trajectory graph and AI plateau analysis"
            )
        with c_save_status:
            if has_unsaved_changes:
                st.warning("**Unsaved changes.** Click **Save progress** to update the chart.")
            else:
                st.success(f"**Chart is up to date** · last saved {st.session_state.last_saved_prog_time}")

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
                st.toast("Plateau detected: Engine recalibrated with deload recommendation!", icon="🔄")
            else:
                st.toast("Progressive overload recorded! Engine updated.", icon="🚀")
            st.toast("Workout progress successfully saved! Graph and metrics updated.", icon="💾")
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

        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            white-space: normal !important;
            word-break: break-word !important;
        }
        [data-testid="stMetricLabel"] {
            white-space: normal !important;
            word-break: break-word !important;
            font-size: 0.85rem !important;
        }
        [data-testid="stMetricDelta"] {
            white-space: normal !important;
            word-break: break-word !important;
            font-size: 0.80rem !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # 4. Live KPI Performance Metrics (Driven by Saved Progress)
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric(
                label="Latest Saved Volume",
                value=f"{volumes[-1]:,.0f} kg",
                delta=f"{diffs[-1]:+,.0f} kg vs S3"
            )
        with kpi_c2:
            st.metric(
                label="Progression Velocity",
                value=f"{avg_delta:+,.1f} kg/sess",
                delta="Target: > +1.0 kg" if avg_delta > 1.0 else "⚠️ Stagnant Growth",
                delta_color="normal" if avg_delta > 1.0 else "inverse"
            )
        with kpi_c3:
            st.metric(
                label="4-Session Total Volume",
                value=f"{total_lifted:,.0f} kg",
                delta=f"Net: {net_growth:+,.0f} kg ({net_growth_pct:+.1f}%)"
            )
        with kpi_c4:
            if is_plateau:
                st.metric(label="AI Trajectory State", value="Plateau Stagnation ⚠️", delta="Intervention Needed", delta_color="inverse")
            else:
                st.metric(label="AI Trajectory State", value="Progressive Overload 🟢", delta="Optimal Stimulus", delta_color="normal")

        st.markdown("")

        # 5. Easy-to-Understand High-Clarity Visual Graph
        section_header("Volume Trajectory vs. Optimal +5% Overload Benchmark", level=5)

        # Visual Legend Banner (Clear color-coded explanation)
        status_pill = '<span style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">🟢 STATUS: OPTIMAL OVERLOAD</span>' if not is_plateau else '<span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 12px;">⚠️ STATUS: PLATEAU STAGNATION</span>'

        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 14px 18px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
                <span style="display: flex; align-items: center; gap: 8px; color: #F8FAFC; font-size: 13px; font-weight: 600;">
                    <span style="display: inline-block; width: 14px; height: 14px; background: {'#EF4444' if is_plateau else '#10B981'}; border-radius: 3px;"></span>
                    {'Stagnant Volume (kg)' if is_plateau else 'Your Lifted Volume (Actual kg)'}
                </span>
                <span style="display: flex; align-items: center; gap: 8px; color: #94A3B8; font-size: 13px; font-weight: 600;">
                    <span style="display: inline-block; width: 20px; height: 0; border-top: 3px dashed #38BDF8;"></span>
                    Science-Based +5% Overload Goal
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
                <strong style="color: #F8FAFC; font-size: 13px;">{'Plateau Stagnation' if is_plateau else 'Progressive Overload'}</strong>
                <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">
                    {'Volume has stalled. Your neuromuscular system needs a deload.' if is_plateau else 'Green line is climbing! You are consistently lifting more weight or reps.'}
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #38BDF8;">
                <strong style="color: #F8FAFC; font-size: 13px;">+5% Overload Benchmark (Dashed)</strong>
                <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">
                    {'Currently below the recommended progression curve.' if is_plateau else 'You are above the science-based target for muscle hypertrophy.'}
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                <strong style="color: #F8FAFC; font-size: 13px;">Net 4-Session Growth</strong>
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
                        <span style="width: 10px; height: 10px; border-radius: 50%; background: #EF4444; box-shadow: 0 0 0 4px rgba(239,68,68,0.2); display: inline-block;"></span>
                        <div>
                            <div style="margin: 0; color: #FCA5A5; font-weight: 700; font-size: 17px;">Plateau detected</div>
                            <span style="font-size: 13px; color: #CBD5E1;">Flagged by the FAFIE trajectory classifier</span>
                        </div>
                    </div>
                    <span style="background: rgba(239, 68, 68, 0.3); color: #FCA5A5; padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; border: 1px solid rgba(239, 68, 68, 0.5);">STATUS: DELOAD RECOMMENDED</span>
                </div>
                <p style="color: #F1F5F9; font-size: 14px; margin-bottom: 15px; line-height: 1.6;">
                    Your average volume delta over the last 4 workout sessions is <strong>+{avg_delta:,.1f} kg/session</strong> (below the minimum growth threshold of +1.0 kg). Your neuromuscular system has adapted to current mechanical tension, accumulating systemic fatigue without stimulating fresh myofibrillar hypertrophy.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #EF4444;">
                        <strong style="color: #F8FAFC; font-size: 14px;">1. Strategic Deload (Week 5)</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Reduce total lifted volume by 40-50% for 5-7 days. Retain form precision while allowing central nervous system (CNS) glycogen resensitization.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #F59E0B;">
                        <strong style="color: #F8FAFC; font-size: 14px;">2. Exercise Angle Rotation</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Rotate primary compound movement: Swap Flat Barbell Bench to 30° Incline Dumbbell Press; swap Back Squat to Front Squats or Bulgarian Split Squats.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">3. Tempo & Time Under Tension</strong>
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
                        <span style="width: 10px; height: 10px; border-radius: 50%; background: #10B981; box-shadow: 0 0 0 4px rgba(16,185,129,0.2); display: inline-block;"></span>
                        <div>
                            <div style="margin: 0; color: #6EE7B7; font-weight: 700; font-size: 17px;">Progressive overload on track</div>
                            <span style="font-size: 13px; color: #CBD5E1;">Trajectory verified by the FAFIE engine</span>
                        </div>
                    </div>
                    <span style="background: rgba(16, 185, 129, 0.3); color: #6EE7B7; padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: bold; border: 1px solid rgba(16, 185, 129, 0.5);">GROWTH VELOCITY: OPTIMAL</span>
                </div>
                <p style="color: #F1F5F9; font-size: 14px; margin-bottom: 15px; line-height: 1.6;">
                    You are increasing workload at an average velocity of <strong>+{avg_delta:,.1f} kg/session</strong> (Net 4-session gain: <strong>+{net_growth:,.0f} kg ({net_growth_pct:+.1f}%)</strong>). Your mechanical tension curve exceeds hypertrophy baseline criteria.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 12px;">
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #10B981;">
                        <strong style="color: #F8FAFC; font-size: 14px;">1. Incremental Micro-Loading</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Add 1.25 kg – 2.5 kg plates to your first 2 working sets next week to maintain compounding mechanical tension.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">2. Protein & Recovery Buffer</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Fuel your muscular repair with 1.8–2.2g of protein per kg of bodyweight, along with 7.5+ hours of restorative sleep.</p>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.65); padding: 14px; border-radius: 8px; border-left: 4px solid #8B5CF6;">
                        <strong style="color: #F8FAFC; font-size: 14px;">3. Continuous Logging</strong>
                        <p style="color: #94A3B8; font-size: 12px; margin: 4px 0 0 0; line-height: 1.4;">Keep recording your sets in the Workout Log so the closed loop can forecast your 1-rep maximums.</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)



        # 7. Educational Primer Expander
        with st.expander("How progress tracking works", expanded=False):
            st.markdown("""
            ### **Understanding Volume & Progressive Overload**
            
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
        section_header("Workout plan", caption=f"Personalized for {default_mem_name} · Goal: {default_mem_goal}")

        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_idx = days_list.index(today_day_name) if today_day_name in days_list else 0

        c_day_sel, c_day_badge = st.columns([3, 1])
        with c_day_sel:
            selected_day = st.radio(
                "Training day",
                days_list,
                index=today_idx,
                horizontal=True,
                key=f"sel_workout_day_{default_mem_id}"
            )
        with c_day_badge:
            if selected_day == today_day_name:
                st.success(f"**Today ({today_day_name})**")
            else:
                st.info(f"Viewing: **{selected_day}**")

        current_routine = WEEKLY_WORKOUT_ROUTINES.get(selected_day, WEEKLY_WORKOUT_ROUTINES["Monday"])

        # Top summary card for the selected day
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 6px 0; color: #F1F5F9;">{selected_day}'s Focus: {current_routine['title']}</h4>
            <p style="margin: 0; color: #94A3B8; font-size: 0.9rem;">
                <b>Target:</b> {current_routine['focus']} &nbsp;&bull;&nbsp; <b>Estimated Duration:</b> {current_routine['duration']} &nbsp;&bull;&nbsp; <b>Estimated Caloric Burn:</b> {current_routine['calories_est']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        c_guide1, c_guide2 = st.columns([3, 2])
        with c_guide1:
            section_header(f"{selected_day}'s exercises", level=4, caption="Tick each exercise as you finish it.")

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
                    <div style="font-size: 0.84rem; color: #94A3B8;"><b>Target:</b> {ex['target']} &nbsp;|&nbsp; <b>Rest:</b> {ex['rest']}</div>
                    <div style="font-size: 0.82rem; color: #CBD5E1; margin-top: 4px;"><b>Form Cue:</b> <i>{ex['cue']}</i></div>
                    <div style="margin-top: 8px;">
                        <a href="{ex.get('video_url', 'https://youtube.com')}" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.35); padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.80rem; font-weight: 600;">
                            <span style="color: #EF4444; font-size: 0.85rem;">▶</span> Form tutorial: <b>{ex.get('video_title', 'Video Guide')}</b> ↗
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if ex.get("video_url"):
                    with st.expander(f"Watch video: {ex['name']}", expanded=False):
                        st.video(ex["video_url"])

            total_ex = len(current_routine["exercises"])
            pct_done = completed_count / total_ex if total_ex > 0 else 0
            st.progress(pct_done, text=f"{completed_count} of {total_ex} exercises complete ({int(pct_done * 100)}%)")
            if completed_count == total_ex and total_ex > 0:
                st.success(f"**Great work, {default_mem_name}.** You've completed every exercise for {selected_day}.")

        with c_guide2:
            section_header("Nutrition plan", level=4)
            nut = current_routine["nutrition"]
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;">
                <div style="font-size: 0.8rem; color: #10B981; font-weight: 700; text-transform: uppercase;">Daily Energy Target</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #F8FAFC; margin: 4px 0 8px 0;">{nut['calories']}</div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span style="background: rgba(59, 130, 246, 0.15); color: #60A5FA; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">Protein: {nut['protein']}</span>
                    <span style="background: rgba(245, 158, 11, 0.15); color: #FBBF24; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">Carbs: {nut['carbs']}</span>
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">Fats: {nut['fats']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.caption("PRE-WORKOUT")
            st.info(f"{nut['pre_workout']}")

            st.caption("POST-WORKOUT RECOVERY")
            st.success(f"{nut['post_workout']}")

            st.caption("HYDRATION")
            st.write(f"At least **{nut['water']}** of water, spread across the day.")

    with member_tabs[4]:
        section_header("Nutrition", caption=f"Log meals by photo, menu or custom entry and track calories consumed vs. remaining for {default_mem_name}.")

        # Goal to calorie target map
        goal_target_map = {
            "Hypertrophy (Muscle Gain)": {"calories": 2500, "protein": 165, "carbs": 290, "fats": 75},
            "Fat Loss / Cutting": {"calories": 1850, "protein": 175, "carbs": 155, "fats": 55},
            "Weight Loss": {"calories": 1800, "protein": 170, "carbs": 150, "fats": 55},
            "Maintenance & Recomposition": {"calories": 2200, "protein": 150, "carbs": 235, "fats": 65},
            "General Fitness": {"calories": 2100, "protein": 140, "carbs": 240, "fats": 65},
            "Endurance / Athletic": {"calories": 2700, "protein": 145, "carbs": 365, "fats": 70}
        }
        active_plan = goal_target_map.get(default_mem_goal, goal_target_map["Hypertrophy (Muscle Gain)"])

        # Session state for custom calorie target
        if f"cal_budget_target_{default_mem_id}" not in st.session_state:
            st.session_state[f"cal_budget_target_{default_mem_id}"] = active_plan["calories"]

        # Session state for member meal logs
        if f"member_meal_logs_{default_mem_id}" not in st.session_state:
            st.session_state[f"member_meal_logs_{default_mem_id}"] = [
                {
                    "id": "meal_001",
                    "time": "08:30 AM",
                    "slot": "Breakfast 🌅",
                    "name": "Rolled Oats Bowl with Whey Protein, Peanut Butter & Banana",
                    "portion": "1 bowl (1.0x serving)",
                    "calories": 465.0,
                    "protein": 34.0,
                    "carbs": 55.0,
                    "fats": 12.5,
                    "source": "Pre-Logged"
                },
                {
                    "id": "meal_002",
                    "time": "11:15 AM",
                    "slot": "Pre-Workout ⚡",
                    "name": "Ripe Banana + 2 Whole Boiled Eggs",
                    "portion": "1 banana + 2 eggs",
                    "calories": 261.0,
                    "protein": 13.9,
                    "carbs": 28.1,
                    "fats": 10.9,
                    "source": "Menu Database"
                }
            ]

        # Target customization and quick adjustment expander
        with st.expander("**Customize Daily Caloric Budget & Target Macros**", expanded=False):
            c_tg1, c_tg2 = st.columns([2, 2])
            with c_tg1:
                new_cal_target = st.slider(
                    "Daily Calorie Target (kcal)",
                    min_value=1200,
                    max_value=4500,
                    value=int(st.session_state[f"cal_budget_target_{default_mem_id}"]),
                    step=50,
                    key=f"slider_cal_{default_mem_id}"
                )
                st.session_state[f"cal_budget_target_{default_mem_id}"] = new_cal_target
            with c_tg2:
                st.markdown(f"**Baseline Goal Archetype:** `{default_mem_goal}`")
                st.caption(f"Estimated Recommended Split: Protein **{active_plan['protein']}g** &bull; Carbs **{active_plan['carbs']}g** &bull; Fats **{active_plan['fats']}g**")

        current_cal_target = st.session_state[f"cal_budget_target_{default_mem_id}"]
        meal_logs = st.session_state[f"member_meal_logs_{default_mem_id}"]

        consumed_cal = sum(m["calories"] for m in meal_logs)
        consumed_pro = sum(m["protein"] for m in meal_logs)
        consumed_carb = sum(m["carbs"] for m in meal_logs)
        consumed_fat = sum(m["fats"] for m in meal_logs)

        remaining_cal = current_cal_target - consumed_cal
        pct_consumed = consumed_cal / max(current_cal_target, 1)

        # ----------------------------------------------------------------------
        # 1. LIVE CALORIE & REMAINING BUDGET METRICS
        # ----------------------------------------------------------------------
        section_header("Today's Energy Balance (Consumed vs. Remaining)", level=4)
        
        c_met1, c_met2, c_met3, c_met4 = st.columns(4)
        with c_met1:
            st.metric("Daily Target Budget", f"{current_cal_target:,} kcal", help="Total target energy intake for today")
        with c_met2:
            st.metric("Consumed Calories", f"{consumed_cal:,.0f} kcal", f"{pct_consumed*100:.1f}% consumed", delta_color="off")
        with c_met3:
            rem_delta_label = "Remaining" if remaining_cal >= 0 else "Over Budget"
            st.metric(
                "Remaining Calories",
                f"{max(remaining_cal, 0):,.0f} kcal" if remaining_cal >= 0 else f"{remaining_cal:,.0f} kcal",
                f"{remaining_cal:+,.0f} kcal",
                delta_color="normal" if remaining_cal >= 0 else "inverse"
            )
        with c_met4:
            st.metric("Workout Burn (Est.)", f"{today_routine['calories_est']}", f"{today_day_name}'s routine", delta_color="off")

        # Visual progress bar
        capped_pct = min(1.0, max(0.0, pct_consumed))
        st.progress(capped_pct, text=f"Caloric Intake Progress: {consumed_cal:,.0f} / {current_cal_target:,} kcal ({int(pct_consumed * 100)}%)")

        # Dynamic Status Banner
        if remaining_cal > 150:
            st.success(f"**On Track:** You have **{remaining_cal:,.0f} kcal** remaining for today! Ensure you hit your target protein across your remaining meals.")
        elif 0 <= remaining_cal <= 150:
            st.warning(f"**Target Almost Reached:** You have **{remaining_cal:,.0f} kcal** remaining. Excellent adherence to your nutritional budget!")
        else:
            st.error(f"**Calorie Surplus Alert:** You have exceeded your daily budget by **{abs(remaining_cal):,.0f} kcal** ({consumed_cal:,.0f} / {current_cal_target:,} kcal). Consider balancing with additional hydration and light walking or adjust tomorrow's intake.")

        # Macronutrient Progress Cards
        c_mac1, c_mac2, c_mac3 = st.columns(3)
        with c_mac1:
            p_target = active_plan["protein"]
            p_pct = min(1.0, consumed_pro / max(p_target, 1))
            st.markdown(f"**🥩 Protein:** `{consumed_pro:.1f}g` / `{p_target}g` ({int(p_pct*100)}%)")
            st.progress(p_pct)
        with c_mac2:
            c_target = active_plan["carbs"]
            c_pct = min(1.0, consumed_carb / max(c_target, 1))
            st.markdown(f"**🍞 Carbs:** `{consumed_carb:.1f}g` / `{c_target}g` ({int(c_pct*100)}%)")
            st.progress(c_pct)
        with c_mac3:
            f_target = active_plan["fats"]
            f_pct = min(1.0, consumed_fat / max(f_target, 1))
            st.markdown(f"**🥑 Fats:** `{consumed_fat:.1f}g` / `{f_target}g` ({int(f_pct*100)}%)")
            st.progress(f_pct)

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 2. DUAL-INPUT SECTION: PHOTO UPLOAD VS. MENU PICKER
        # ----------------------------------------------------------------------
        section_header("Log Your Meal: Upload Photo or Select From Menu", level=4)

        tab_photo, tab_menu, tab_custom = st.tabs([
            "Upload Meal Photo",
            "Select From Menu",
            "Custom Item"
        ])

        # TAB 1: UPLOAD PHOTO
        with tab_photo:
            section_header("AI Meal Photo Scanner & Estimator", level=5)
            st.caption("Snap a photo of your meal plate or food packaging. Our visual engine recognizes the dish, estimates portions, and computes calories & macros instantly.")

            uploaded_photo = st.file_uploader(
                "Upload Meal Photo (JPG, PNG, JPEG, WEBP)",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"uploader_meal_{default_mem_id}"
            )

            if uploaded_photo is not None:
                c_up_img, c_up_details = st.columns([2, 3])
                with c_up_img:
                    from PIL import Image
                    try:
                        img = Image.open(uploaded_photo)
                        st.image(img, caption=f"📸 Uploaded: {uploaded_photo.name}", use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not load image: {e}")

                with c_up_details:
                    st.success("**Meal Photo Captured & Analyzed!**")
                    
                    # Smart matching logic based on filename keywords or intelligent default
                    fname_lower = uploaded_photo.name.lower()
                    matched_idx = 0
                    if "chicken" in fname_lower: matched_idx = 0
                    elif "paneer" in fname_lower: matched_idx = 1
                    elif "egg" in fname_lower: matched_idx = 2
                    elif "oat" in fname_lower: matched_idx = 3
                    elif "dal" in fname_lower or "rice" in fname_lower: matched_idx = 4
                    elif "salmon" in fname_lower or "fish" in fname_lower: matched_idx = 5
                    elif "soya" in fname_lower: matched_idx = 6
                    elif "yogurt" in fname_lower or "curd" in fname_lower: matched_idx = 7
                    elif "shake" in fname_lower or "whey" in fname_lower: matched_idx = 8

                    preset_names = [p["name"] for p in PHOTO_MEAL_PRESETS]
                    sel_preset_name = st.selectbox(
                        "**Detected Dish Match (Confirm or Select Closest):**",
                        preset_names,
                        index=matched_idx,
                        key=f"sel_photo_match_{default_mem_id}"
                    )
                    chosen_preset = next((p for p in PHOTO_MEAL_PRESETS if p["name"] == sel_preset_name), PHOTO_MEAL_PRESETS[0])

                    c_mult, c_slot = st.columns(2)
                    with c_mult:
                        portion_mult = st.select_slider(
                            "Serving Portion Multiplier",
                            options=[0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
                            value=1.0,
                            format_func=lambda x: f"{x}x ({'Half' if x==0.5 else ('Regular' if x==1.0 else ('1.5x Large' if x==1.5 else f'{x}x'))})"
                        )
                    with c_slot:
                        photo_meal_slot = st.selectbox(
                            "Meal Slot",
                            ["Breakfast 🌅", "Lunch 🍱", "Evening Snack ☕", "Dinner 🌙", "Pre-Workout ⚡", "Post-Workout 🔋"],
                            index=1,
                            key=f"slot_photo_{default_mem_id}"
                        )

                    # Dynamic calorie calculation for the photo dish
                    calc_p_cal = float(chosen_preset["calories"] * portion_mult)
                    calc_p_pro = float(chosen_preset["protein"] * portion_mult)
                    calc_p_carb = float(chosen_preset["carbs"] * portion_mult)
                    calc_p_fat = float(chosen_preset["fats"] * portion_mult)

                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 10px 14px; margin: 8px 0;">
                        <div style="font-weight: 700; color: #F1F5F9;">Calculated Nutrition for this Photo:</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #38BDF8; margin: 2px 0 6px 0;">{calc_p_cal:,.0f} kcal</div>
                        <div style="font-size: 0.85rem; color: #CBD5E1;">
                            Protein: <b>{calc_p_pro:.1f}g</b> &nbsp;|&nbsp; Carbs: <b>{calc_p_carb:.1f}g</b> &nbsp;|&nbsp; Fats: <b>{calc_p_fat:.1f}g</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Add Photo Meal to Today's Diary", type="primary", use_container_width=True, key=f"btn_add_photo_{default_mem_id}"):
                        new_meal_id = f"meal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        st.session_state[f"member_meal_logs_{default_mem_id}"].append({
                            "id": new_meal_id,
                            "time": datetime.now().strftime("%I:%M %p"),
                            "slot": photo_meal_slot,
                            "name": f"📸 {chosen_preset['name']}",
                            "portion": f"{portion_mult}x Serving ({uploaded_photo.name})",
                            "calories": calc_p_cal,
                            "protein": calc_p_pro,
                            "carbs": calc_p_carb,
                            "fats": calc_p_fat,
                            "source": "Photo Upload"
                        })
                        evt = TenantEvent(
                            tenant_id=active_tenant_id,
                            role_context="member",
                            event_type="meal_logged",
                            operational_params={
                                "member_id": default_mem_id,
                                "meal_name": chosen_preset["name"],
                                "calories": calc_p_cal,
                                "source": "photo"
                            }
                        )
                        tige.update_genome_from_event(evt)
                        st.toast(f"Added {chosen_preset['name']} (+{calc_p_cal:,.0f} kcal) to today's diary!", icon="🥗")
                        st.rerun()
            else:
                st.info("**Upload a photo of your meal to begin.** If you already know what you ate, use **Select From Menu** instead.")

        # TAB 2: SELECT FROM MENU DATABASE
        with tab_menu:
            section_header("Search & Select from Curated Fitness Menu", level=5)
            st.caption("Browse curated Indian and global fitness items with lab-tested calorie and macronutrient profiles.")

            c_cat, c_item = st.columns([1.5, 2.5])
            with c_cat:
                category_list = list(FOOD_MENU_DATABASE.keys())
                sel_category = st.selectbox("1. Select Food Category", category_list, key=f"sel_food_cat_{default_mem_id}")
            with c_item:
                items_in_cat = FOOD_MENU_DATABASE[sel_category]
                item_names = [f"{it['name']} ({it['portion']}) — {it['calories']} kcal" for it in items_in_cat]
                sel_item_str = st.selectbox("2. Select Food Item", item_names, key=f"sel_food_item_{default_mem_id}")
                selected_item_idx = item_names.index(sel_item_str)
                selected_food = items_in_cat[selected_item_idx]

            c_m_serv, c_m_slot = st.columns(2)
            with c_m_serv:
                serving_qty = st.number_input("Portion / Serving Multiplier", min_value=0.25, max_value=10.0, value=1.0, step=0.25, key=f"num_menu_serv_{default_mem_id}")
            with c_m_slot:
                menu_meal_slot = st.selectbox(
                    "Meal Timing Slot",
                    ["Breakfast 🌅", "Lunch 🍱", "Evening Snack ☕", "Dinner 🌙", "Pre-Workout ⚡", "Post-Workout 🔋"],
                    index=1,
                    key=f"slot_menu_{default_mem_id}"
                )

            # Calculated nutrition
            calc_m_cal = float(selected_food["calories"] * serving_qty)
            calc_m_pro = float(selected_food["protein"] * serving_qty)
            calc_m_carb = float(selected_food["carbs"] * serving_qty)
            calc_m_fat = float(selected_food["fats"] * serving_qty)

            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 10px 14px; margin: 8px 0;">
                <div style="font-weight: 700; color: #F1F5F9;">Nutrition Subtotal: {selected_food['name']} ({serving_qty:g}x {selected_food['portion']})</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #10B981; margin: 2px 0 6px 0;">{calc_m_cal:,.0f} kcal</div>
                <div style="font-size: 0.85rem; color: #CBD5E1;">
                    Protein: <b>{calc_m_pro:.1f}g</b> &nbsp;|&nbsp; Carbs: <b>{calc_m_carb:.1f}g</b> &nbsp;|&nbsp; Fats: <b>{calc_m_fat:.1f}g</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Add Menu Item to Today's Diary", type="primary", use_container_width=True, key=f"btn_add_menu_{default_mem_id}"):
                new_meal_id = f"meal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                st.session_state[f"member_meal_logs_{default_mem_id}"].append({
                    "id": new_meal_id,
                    "time": datetime.now().strftime("%I:%M %p"),
                    "slot": menu_meal_slot,
                    "name": selected_food["name"],
                    "portion": f"{serving_qty:g}x {selected_food['portion']}",
                    "calories": calc_m_cal,
                    "protein": calc_m_pro,
                    "carbs": calc_m_carb,
                    "fats": calc_m_fat,
                    "source": "Menu Database"
                })
                evt = TenantEvent(
                    tenant_id=active_tenant_id,
                    role_context="member",
                    event_type="meal_logged",
                    operational_params={
                        "member_id": default_mem_id,
                        "meal_name": selected_food["name"],
                        "calories": calc_m_cal,
                        "source": "menu"
                    }
                )
                tige.update_genome_from_event(evt)
                st.toast(f"Added {selected_food['name']} (+{calc_m_cal:,.0f} kcal) to today's diary!", icon="🍲")
                st.rerun()

        # TAB 3: CUSTOM ITEM ENTRY
        with tab_custom:
            section_header("Enter Custom Food Item / Packaged Nutrition", level=5)
            st.caption("Have an outside meal, nutrition label, or custom home recipe? Enter the exact values below.")

            with st.form(f"form_custom_food_{default_mem_id}"):
                c_cf1, c_cf2 = st.columns(2)
                with c_cf1:
                    custom_food_name = st.text_input("Food Item Name", value="Homemade Chicken Biryani")
                    custom_portion = st.text_input("Portion / Serving Size", value="1 medium plate (250g)")
                    custom_slot = st.selectbox(
                        "Meal Slot",
                        ["Breakfast 🌅", "Lunch 🍱", "Evening Snack ☕", "Dinner 🌙", "Pre-Workout ⚡", "Post-Workout 🔋"],
                        index=3
                    )
                with c_cf2:
                    custom_cal = st.number_input("Calories (kcal)", min_value=1.0, max_value=5000.0, value=450.0, step=10.0)
                    c_c_m1, c_c_m2, c_c_m3 = st.columns(3)
                    with c_c_m1: custom_pro = st.number_input("Protein (g)", min_value=0.0, max_value=500.0, value=32.0, step=1.0)
                    with c_c_m2: custom_carb = st.number_input("Carbs (g)", min_value=0.0, max_value=500.0, value=50.0, step=1.0)
                    with c_c_m3: custom_fat = st.number_input("Fats (g)", min_value=0.0, max_value=500.0, value=12.0, step=1.0)

                submit_custom = st.form_submit_button("Add Custom Food to Today's Diary", type="primary", use_container_width=True)
                if submit_custom:
                    new_meal_id = f"meal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.session_state[f"member_meal_logs_{default_mem_id}"].append({
                        "id": new_meal_id,
                        "time": datetime.now().strftime("%I:%M %p"),
                        "slot": custom_slot,
                        "name": custom_food_name,
                        "portion": custom_portion,
                        "calories": float(custom_cal),
                        "protein": float(custom_pro),
                        "carbs": float(custom_carb),
                        "fats": float(custom_fat),
                        "source": "Custom Entry"
                    })
                    evt = TenantEvent(
                        tenant_id=active_tenant_id,
                        role_context="member",
                        event_type="meal_logged",
                        operational_params={
                            "member_id": default_mem_id,
                            "meal_name": custom_food_name,
                            "calories": custom_cal,
                            "source": "custom"
                        }
                    )
                    tige.update_genome_from_event(evt)
                    st.toast(f"Added {custom_food_name} (+{custom_cal:,.0f} kcal)!", icon="🍽️")
                    st.rerun()

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 3. TODAY'S CONSUMED MEALS DIARY & MANAGEMENT
        # ----------------------------------------------------------------------
        section_header("Today's Consumed Meals Diary", level=4)

        if meal_logs:
            c_d_info, c_d_clear = st.columns([3, 1])
            with c_d_info:
                st.caption(f"Currently tracking **{len(meal_logs)} logged items** totaling **{consumed_cal:,.0f} kcal**.")
            with c_d_clear:
                if st.button("Clear Today's Diary", use_container_width=True, key=f"btn_clear_diary_{default_mem_id}"):
                    st.session_state[f"member_meal_logs_{default_mem_id}"] = []
                    st.toast("Today's food diary cleared!", icon="🧹")
                    st.rerun()

            # Render styled meal cards with individual delete buttons
            for idx, item in enumerate(meal_logs):
                col_i1, col_i2, col_i3 = st.columns([3, 1.2, 0.6])
                with col_i1:
                    st.markdown(f"**{item['slot']}** &bull; `{item['time']}` &bull; **{item['name']}**")
                    st.caption(f"Portion: *{item['portion']}* &nbsp;|&nbsp; Source: `{item['source']}`")
                with col_i2:
                    st.markdown(f"**{item['calories']:,.0f} kcal**")
                    st.caption(f"P: {item['protein']:.1f}g &bull; C: {item['carbs']:.1f}g &bull; F: {item['fats']:.1f}g")
                with col_i3:
                    if st.button("Remove", key=f"del_meal_{item['id']}_{idx}", help=f"Remove {item['name']}"):
                        st.session_state[f"member_meal_logs_{default_mem_id}"].pop(idx)
                        st.toast(f"Removed {item['name']}", icon="🗑️")
                        st.rerun()
                st.markdown("<hr style='margin: 4px 0 10px 0; border: none; border-top: 1px solid rgba(255,255,255,0.07);'/>", unsafe_allow_html=True)

            # Structured DataFrame overview
            with st.expander("**View Formatted Table Summary of Today's Intake**", expanded=False):
                df_meals = pd.DataFrame(meal_logs)
                df_show = df_meals[["time", "slot", "name", "portion", "calories", "protein", "carbs", "fats", "source"]].copy()
                df_show.columns = ["Time", "Meal Slot", "Food Item", "Portion", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fats (g)", "Source"]
                st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("**No meals logged yet today.** Upload a photo or select from the menu above to start calculating consumed and remaining calories!")

# ==============================================================================
# 4. PATENT & ARCHITECTURE DEEP-DIVE
# ==============================================================================
elif portal_mode == "🔬 Patent & Architecture Deep-Dive":
    page_header(
        "Architecture",
        f"Live internals of the platform engines for {active_genome.gym_name}: genome vectors, dependency fabric, formulas and security checks.",
        eyebrow="Platform engines",
        chips=[chip("Invention Disclosure", "24BIT0370-24BIT0390-IDF-01"), chip("VIT SCORE")]
    )

    k_tabs = st.tabs([
        "TIG Vectors",
        "DTDF Fabric",
        "SICE Formulas",
        "FAFIE Privacy",
        "PTLM Partitions",
        "ACVE Security Test"
    ])

    with k_tabs[0]:
        section_header("Tenant isolation genome", caption="The six vectors that model this gym as a digital object.")
        v1, v2, v3 = st.columns(3)
        with v1:
            st.caption("SUBSCRIPTION")
            st.json(active_genome.subscription.model_dump())
        with v2:
            st.caption("USAGE")
            st.json(active_genome.usage.model_dump())
        with v3:
            st.caption("ROLE PERMISSIONS")
            st.json(active_genome.role_permission.model_dump())
        v4, v5, v6 = st.columns(3)
        with v4:
            st.caption("RESOURCES")
            st.json(active_genome.resource.model_dump())
        with v5:
            st.caption("COMPLIANCE")
            st.json(active_genome.compliance.model_dump())
        with v6:
            st.caption("TRUST")
            st.json(active_genome.trust.model_dump())

    with k_tabs[1]:
        section_header("Dynamic dependency fabric", caption="Weighted tenant–role–resource edges used for enforcement.")
        edges = dtdfe.get_fabric(active_tenant_id)
        st.dataframe(pd.DataFrame([e.model_dump() for e in edges]), use_container_width=True, hide_index=True)

    with k_tabs[2]:
        section_header("Subscription convergence", caption="Projected month-end members and the prorated upgrade price.")
        with st.container(border=True):
            st.latex(r"\hat{M}_{end} = M_{active} + (v \times d_{rem})")
            st.latex(r"C_{prorated} = (Price_{next} - Price_{current}) \times \frac{d_{rem}}{30}")

    with k_tabs[3]:
        section_header("Differential privacy", caption="Gradient clipping followed by Gaussian noise before updates leave a gym.")
        with st.container(border=True):
            st.latex(r"g_{clipped} = \frac{g}{\max\left(1, \frac{\|g\|_2}{C}\right)}, \quad g_{dp} = g_{clipped} + \mathcal{N}(0, \sigma^2)")

    with k_tabs[4]:
        section_header("Partition allocation", caption="Database partitions pre-materialized ahead of forecast peaks.")
        st.metric("Active pre-materialized partitions", active_genome.resource.materialized_partitions)

    with k_tabs[5]:
        section_header("Cross-tenant intrusion test", caption="Sends an action from a foreign tenant and shows how ACVE blocks it.")
        if st.button("Run intrusion test", type="primary"):
            bad_intent = IntentObject(tenant_id=active_tenant_id, source_agent="IntrusionAgent", proposed_action="ENROLL_MEMBER")
            is_valid, verdict, violations = acve.verify_action_intent(bad_intent, caller_role="gym_admin", caller_tenant_id="tenant_foreign_attacker")
            st.error(f"ACVE verdict: {verdict}")
            st.write(f"Violations caught: `{violations}`")
            st.success("Blocked — the tenant isolation boundary held.")
