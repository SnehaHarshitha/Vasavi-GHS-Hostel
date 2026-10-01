# PG Hostel Mess – Girls Hostel Management System
### Sri Vasavi Engineering College, Tadepalligudem, West Godavari, Andhra Pradesh, India
**Suggested Domain:** `pghostelmess.com`

A complete, production-ready, mobile-responsive girls hostel management web application built with **Flask**, **MongoDB Atlas**, **Bootstrap 5**, and **Streamlit**.


---

## ⚡ Quick Project Startup (How to Start Every Time)

Whenever you reopen the project or open a new terminal:

### Option 1: Double-Click Startup Script (Windows)
Simply double-click **`start.bat`** in the project root directory.

### Option 2: Command Line (One Command)
Run this single command in your terminal:
```bash
python run.py
```

This single command automatically:
1. Detects your Python environment.
2. Automatically frees ports `5000` and `8501` if occupied by stale processes.
3. Verifies and seeds database data if empty.
4. Launches the main website at **`http://localhost:5000`**
5. Launches the Streamlit staff portal at **`http://localhost:8501`**

---

## 🌟 Key Features & Modules


1. **Multi-Role Authentication & Access Control**:
   - **Student**: View profile, mess timetable, submit Thursday/Friday Egg vs Veg choices, view daily room cleaning status, track Sunday Phenyl tasks, file complaints, and view notifications.
   - **Warden**: Manage student approvals, allocate rooms, edit weekly mess menus, log room housekeeping status, schedule Sunday Phenyl cleaning tasks, reply to complaints, broadcast notifications, and export CSV reports.
   - **Principal Portal**: Executive overview of hostel statistics, room occupancy, grievance resolution velocity, warden activity logs, and printable executive summaries.
   - **Admin**: Full system access, manage user roles (Admin, Warden, Principal, Student), website contact form messages, system settings, registration toggle, and database backups.

2. **Mess Management & Egg/Veg Selection**:
   - Weekly menu (Breakfast, Lunch, Snacks, Dinner).
   - Thursday & Friday choice window between **Egg Curry / Boiled Eggs** and **Special Veg Curry (Paneer/Mushroom)**.
   - Real-time aggregated counts for mess cooks to eliminate food waste.
   - CSV Export of daily student food choices.

3. **Room Cleaning & Sunday Phenyl Schedule**:
   - Daily housekeeping tracking per room (Completed, Pending, Not Completed, Student Not Available).
   - Dedicated Sunday Room Phenyl distribution and deep cleaning task tracker.

4. **Complaint & Grievance Portal**:
   - Multi-category complaint submission (Food, Water, Security, Room Cleaning, Maintenance, etc.).
   - Priority levels (Low, Medium, High, Urgent) and anonymous filing option.
   - Warden response tracking, status workflow (`Submitted` -> `Seen` -> `In Progress` -> `Resolved`), and student rating system.

5. **In-App Notification Bell**:
   - Targeted audience notifications (All, Room-specific, Wardens, Individual students).
   - Real-time unread counter badge in top navigation.

6. **Streamlit Analytics Dashboard**:
   - Separate Streamlit application (`streamlit_dashboard/dashboard.py`) connected to the same MongoDB Atlas database for interactive charts, visual pie/bar charts, and CSV report downloads.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask, Flask Blueprints, Flask-Login, Flask-WTF, Werkzeug (Password Hashing)
- **Database**: MongoDB Atlas (PyMongo, dnspython)
- **Frontend**: HTML5, CSS3, Bootstrap 5, FontAwesome 6, Chart.js, Jinja2 Templates
- **Analytics**: Streamlit, Pandas, Plotly Express
- **Server / WSGI**: Gunicorn / Waitress

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
- Python 3.10 or higher installed.
- MongoDB Atlas cluster URI or local MongoDB instance (`mongodb://localhost:27017/pg_hostel_mess`).

### 1. Clone & Environment Setup
```bash
# Navigate to project root
cd "e:/GHS Hostael Mess website"

# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment (Windows PowerShell)
venv\Scripts\activate

# Activate Virtual Environment (Linux / macOS)
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```
Edit `.env` to set your MongoDB Atlas connection string:
```env
SECRET_KEY=pghostelmess_super_secret_key_2026_svec
MONGO_URI=mongodb+srv://admin:password@cluster0.mongodb.net/pg_hostel_mess?retryWrites=true&w=majority
DATABASE_NAME=pg_hostel_mess
ADMIN_EMAIL=admin@pghostelmess.com
ADMIN_PASSWORD=AdminPass123!
```

### 3. Seed Sample Data
Preload sample accounts (Admin, Warden, Principal, Students), rooms, mess menu, cleaning records, and complaints:
```bash
python scripts/seed_sample_data.py
```

### 4. Run the Flask Web Application
```bash
# Development mode
python app.py
```
The public website will be available at: `http://127.0.0.1:5000`

### 5. Run the Streamlit Analytics Dashboard
Open a new terminal window, activate `venv`, and run:
```bash
streamlit run streamlit_dashboard/dashboard.py
```
The Streamlit dashboard will launch at: `http://localhost:8501`

---

## 🔐 Default Login Credentials for Testing

| Role | Login Email / Identifier | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@pghostelmess.com` | `AdminPass123!` | `/admin/dashboard` |
| **Warden** | `warden@pghostelmess.com` | `WardenPass123!` | `/warden/dashboard` |
| **Principal** | `principal@pghostelmess.com` | `PrincipalPass123!` | `/principal/dashboard` |
| **Student (Approved)** | `21A81A0501` or `bhavana@srivasaviengg.ac.in` | `Password123!` | `/student/dashboard` |
| **Student (Pending)** | `21A81A0205` or `deepthi@srivasaviengg.ac.in` | `Password123!` | Awaiting approval |

> **IMPORTANT**: Please change default passwords after logging in for production deployments!

---

## 🌐 Public & Private Routes Sitemap

### Public Pages
- `/` - Home page with hero banner, features, and mess timetable preview
- `/about` - About Sri Vasavi Engineering College & PG Girls Hostel
- `/rules` - Detailed Hostel Rules & Regulations (inspired by top institutional guidelines)
- `/facilities` - Hostel infrastructure (RO Water, Wi-Fi, Security, Housekeeping)
- `/mess` - Full weekly mess timetable and Egg/Veg selection guidelines
- `/contact` - Contact information, emergency numbers, form submission, and Google Maps embed

### User Portals
- `/auth/login` - Secure login for all user roles
- `/auth/register` - Student registration form
- `/student/dashboard` - Student dashboard with mess menu, cleaning status & quick actions
- `/student/food-selection` - Thursday & Friday Egg vs Veg selection form
- `/student/cleaning-status` - Daily room cleaning log & Sunday phenyl task schedule
- `/student/complaints` - Grievance submission, status tracker & rating system
- `/warden/dashboard` - Warden operational control desk
- `/warden/students` - Student registration approval & room assignment
- `/warden/rooms` - Room creation and bed capacity allocation
- `/warden/mess-management` - Mess menu editor & food choice summary
- `/warden/cleaning-management` - Daily room cleaning logger
- `/warden/sunday-tasks` - Sunday room phenyl task scheduler
- `/warden/complaints` - Grievance response & status updater
- `/principal/dashboard` - Executive oversight dashboard
- `/principal/executive-reports` - Printable executive summary reports
- `/admin/dashboard` - System control center
- `/admin/users` - Add staff, wardens, principals, or manage accounts
- `/admin/contact-messages` - Public contact form submissions from MongoDB

---

## 🌐 Production Deployment & Custom Domain Setup

### Option 1: Deploy on Render
1. Create a Web Service on Render and connect your GitHub repository.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn app:app`
4. Set Environment Variables in Render Dashboard (`MONGO_URI`, `SECRET_KEY`, etc.).

### Option 2: Custom Domain (`pghostelmess.com`)
1. In your domain provider DNS settings (e.g. GoDaddy / Namecheap):
   - Add an `A` record pointing `@` to your server IP address.
   - Add a `CNAME` record for `www` pointing to your deployment URL (e.g. `pghostelmess.onrender.com`).
2. Update SSL/TLS certificates (Render / Let's Encrypt automatically issues free SSL for custom domains).

---

## 🧪 Running Automated Tests
```bash
python -m unittest discover tests
```

---

## 📄 License & Attribution
- Project Identity: **PG Hostel Mess – Girls Hostel Management System**
- Institution: **Sri Vasavi Engineering College, Tadepalligudem, West Godavari**
