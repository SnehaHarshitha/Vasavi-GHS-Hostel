import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from datetime import datetime

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/pg_hostel_mess")
DATABASE_NAME = os.getenv("DATABASE_NAME", "pg_hostel_mess")

@st.cache_resource
def get_db():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        return client[DATABASE_NAME]
    except Exception:
        fallback_uri = "mongodb://localhost:27017/pg_hostel_mess"
        client = MongoClient(fallback_uri, serverSelectionTimeoutMS=3000)
        return client[DATABASE_NAME]


# Page configuration
st.set_page_config(
    page_title="GHS Hostel Mess - Staff & Employee Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Outfit:wght@600;700;800&display=swap');

body { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-family: 'Outfit', sans-serif; }

.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stMetric"] {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.2rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

db = get_db()

# ─── Sidebar Authentication & Navigation ──────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align: center; padding-bottom: 1rem;">
    <div style="
        width: 60px; height: 60px;
        background: linear-gradient(135deg, #4f46e5, #06b6d4);
        border-radius: 18px;
        margin: 0 auto 0.6rem;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; color: white;
    ">💼</div>
    <h3 style="margin: 0; font-size: 1.2rem; font-weight: 800; color: #0f172a;">GHS Hostel Portal</h3>
    <p style="margin: 0; font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase;">Staff & Employee Login</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.sidebar.subheader("🔒 Employee & Staff Sign In")
    
    # Instant Quick Login Pills
    st.sidebar.markdown("<p style='font-size: 11px; font-weight: 700; color: #64748b; margin-bottom: 4px;'>⚡ QUICK DEMO AUTOFILL</p>", unsafe_allow_html=True)
    q1, q2 = st.sidebar.columns(2)
    if q1.button("👮 Warden", use_container_width=True, key="demo_warden_btn"):
        st.session_state.demo_email = "warden@pghostelmess.com"
        st.session_state.demo_pw = "WardenPass123!"
    if q2.button("👔 Principal", use_container_width=True, key="demo_principal_btn"):
        st.session_state.demo_email = "principal@pghostelmess.com"
        st.session_state.demo_pw = "PrincipalPass123!"
        
    q3, q4 = st.sidebar.columns(2)
    if q3.button("🛡️ Admin", use_container_width=True, key="demo_admin_btn"):
        st.session_state.demo_email = "admin@pghostelmess.com"
        st.session_state.demo_pw = "AdminPass123!"
    if q4.button("🎓 Student", use_container_width=True, key="demo_student_btn"):
        st.session_state.demo_email = "bhavana@srivasaviengg.ac.in"
        st.session_state.demo_pw = "Password123!"

    email_input = st.sidebar.text_input(
        "Email Address / ID",
        value=st.session_state.get('demo_email', ''),
        placeholder="e.g. warden@pghostelmess.com",
        key="login_email_field"
    )
    password_input = st.sidebar.text_input(
        "Password",
        value=st.session_state.get('demo_pw', ''),
        type="password",
        placeholder="••••••••",
        key="login_pw_field"
    )

    if st.sidebar.button("Sign In →", use_container_width=True, key="submit_login_btn"):
        if not email_input or not password_input:
            st.sidebar.error("Please enter both email and password")
        else:
            user = db.users.find_one({'email': email_input.strip().lower()})
            if user and check_password_hash(user.get('password_hash', ''), password_input):
                st.session_state.logged_in = True
                st.session_state.user = {
                    'id': str(user['_id']),
                    'name': user.get('full_name', 'Employee'),
                    'email': user.get('email'),
                    'role': user.get('role', 'staff').lower(),
                    'phone': user.get('phone', 'N/A')
                }
                st.sidebar.success(f"Welcome back, {user.get('full_name')}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials. Try demo buttons above!")

else:
    # Logged In User Card
    u = st.session_state.user
    role_label = u['role'].upper()
    role_badge_color = {'ADMIN': '#ef4444', 'WARDEN': '#f59e0b', 'PRINCIPAL': '#3b82f6', 'STUDENT': '#10b981'}.get(role_label, '#6366f1')

    st.sidebar.markdown(f"""
    <div style="
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <p style="color: #64748b; font-size: 11px; font-weight: 700; margin: 0; text-transform: uppercase;">Logged In Employee</p>
        <h4 style="color: #0f172a; margin: 2px 0 4px 0; font-size: 1rem; font-weight: 700;">{u['name']}</h4>
        <span style="background: {role_badge_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700;">{role_label} STAFF</span>
        <p style="color: #94a3b8; font-size: 12px; margin: 6px 0 0 0;">✉️ {u['email']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Sign Out", use_container_width=True, key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# ─── Main Content ─────────────────────────────────────────────────────────────
st.title("💼 GHS Hostel - Staff & Employee Management Dashboard")
st.markdown("**Sri Vasavi Engineering College • Tadepalligudem, West Godavari**")

if not st.session_state.logged_in:
    st.info("👋 Welcome! Use the **Staff & Employee Sign In** box in the left sidebar (or click any quick demo button) to access the staff portal.")
    
    # Overview metrics for public view
    col1, col2, col3, col4 = st.columns(4)
    total_students = db.users.count_documents({"role": "student"})
    approved_students = db.users.count_documents({"role": "student", "status": "approved"})
    total_rooms = db.rooms.count_documents({})
    total_complaints = db.complaints.count_documents({})
    resolved_complaints = db.complaints.count_documents({"status": "Resolved"})

    col1.metric("Registered Students", f"{approved_students} Approved", f"{total_students} Total")
    col2.metric("Total Rooms", f"{total_rooms} Rooms Allocated")
    col3.metric("Complaints Logged", f"{total_complaints}", f"{resolved_complaints} Resolved")
    res_rate = round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 100.0
    col4.metric("Resolution Rate", f"{res_rate}%")
    st.markdown("---")

else:
    u = st.session_state.user
    st.success(f"Connected as **{u['name']}** ({u['role'].title()} Staff Portal)")

    # Key Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    total_students = db.users.count_documents({"role": "student"})
    pending_approval = db.users.count_documents({"role": "student", "status": "pending"})
    total_rooms = db.rooms.count_documents({})
    open_complaints = db.complaints.count_documents({"status": "Pending"})

    col1.metric("Total Students", f"{total_students}", f"{pending_approval} Pending Approval")
    col2.metric("Total Rooms", f"{total_rooms} Rooms")
    col3.metric("Open Grievances", f"{open_complaints} Urgent", delta_color="inverse")
    col4.metric("Mess Active", "Operational ✅")

    st.markdown("---")

    # Staff Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Staff & Student Roster",
        "🍳 Food Selection Reports",
        "🧹 Housekeeping & Cleaning",
        "🚨 Grievances & Complaints",
        "📑 Export CSV Reports"
    ])

    # Tab 1: Staff & Student Roster
    with tab1:
        st.subheader("👥 Hostel User Roster & Student Approvals")
        users = list(db.users.find({}, {'password_hash': 0}))
        if users:
            df_users = pd.DataFrame(users)
            df_users['_id'] = df_users['_id'].astype(str)
            
            st.dataframe(df_users[['full_name', 'email', 'role', 'phone', 'room_number', 'status']], use_container_width=True)

            # Pending Student Approvals
            pending_list = [u for u in users if u.get('status') == 'pending']
            if pending_list:
                st.warning(f"⚠️ You have {len(pending_list)} pending student registration(s) requiring approval.")
                for p in pending_list:
                    pcol1, pcol2 = st.columns([3, 1])
                    with pcol1:
                        st.write(f"**{p.get('full_name')}** ({p.get('email')}) — Roll No: `{p.get('role_number', 'N/A')}`")
                    with pcol2:
                        if st.button(f"Approve Account ✅", key=f"approve_{p['_id']}"):
                            db.users.update_one({'_id': p['_id']}, {'$set': {'status': 'approved'}})
                            st.success(f"Approved account for {p.get('full_name')}!")
                            st.rerun()
            else:
                st.info("✅ All registered students are currently approved.")

    # Tab 2: Food Selection Reports
    with tab2:
        st.subheader("🍳 Thursday & Friday Food Selection Audit")
        selections = list(db.food_selections.find())
        if selections:
            df_food = pd.DataFrame(selections)
            food_counts = df_food['food_choice'].value_counts().reset_index()
            food_counts.columns = ['Food Choice', 'Count']

            fcol1, fcol2 = st.columns([1, 2])
            with fcol1:
                st.dataframe(food_counts, use_container_width=True)
            with fcol2:
                fig_food = px.pie(
                    food_counts, names='Food Choice', values='Count',
                    title="Staff Mess Preference Audit (Egg vs Veg)",
                    color_discrete_map={'egg': '#f59e0b', 'veg': '#10b981'}
                )
                st.plotly_chart(fig_food, use_container_width=True)
        else:
            st.info("No food selections logged yet.")

    # Tab 3: Housekeeping & Cleaning
    with tab3:
        st.subheader("🧹 Room Cleaning & Sunday Phenyl Task Compliance")
        cleaning_records = list(db.cleaning_records.find())
        if cleaning_records:
            df_clean = pd.DataFrame(cleaning_records)
            fig_clean = px.bar(
                df_clean['status'].value_counts().reset_index(),
                x='status', y='count',
                title="Cleaning Task Completion Status",
                color='status'
            )
            st.plotly_chart(fig_clean, use_container_width=True)
            st.dataframe(df_clean[['room_number', 'date', 'status', 'inspected_by']], use_container_width=True)
        else:
            st.info("No room cleaning records logged yet.")

    # Tab 4: Grievances & Complaints
    with tab4:
        st.subheader("🚨 Complaint Resolution & Action Center")
        complaints = list(db.complaints.find())
        if complaints:
            df_comp = pd.DataFrame(complaints)
            for comp in complaints:
                with st.expander(f"📌 [{comp.get('status', 'Pending')}] {comp.get('title', 'Complaint')} — Room {comp.get('room_number', 'N/A')}"):
                    st.write(f"**Student:** {comp.get('student_name', 'Student')}")
                    st.write(f"**Category:** {comp.get('category')} | **Priority:** {comp.get('priority')}")
                    st.write(f"**Description:** {comp.get('description')}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Mark as Resolved ✅", key=f"resolve_{comp['_id']}"):
                            db.complaints.update_one({'_id': comp['_id']}, {'$set': {'status': 'Resolved', 'resolved_at': datetime.utcnow()}})
                            st.success("Complaint updated to Resolved!")
                            st.rerun()
                    with c2:
                        if st.button("Mark as In Progress ⏳", key=f"progress_{comp['_id']}"):
                            db.complaints.update_one({'_id': comp['_id']}, {'$set': {'status': 'In Progress'}})
                            st.info("Complaint updated to In Progress!")
                            st.rerun()
        else:
            st.info("No complaints registered.")

    # Tab 5: Export CSV Reports
    with tab5:
        st.subheader("📑 Administrative Data Export")
        st.write("Download administrative reports for auditing and records.")
        users_list = list(db.users.find({}, {'password_hash': 0}))
        if users_list:
            df_export = pd.DataFrame(users_list)
            st.download_button(
                label="📥 Download Full User Roster CSV",
                data=df_export.to_csv(index=False).encode('utf-8'),
                file_name="ghs_hostel_user_roster.csv",
                mime="text/csv"
            )
