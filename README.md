# GHShostel Management System

![GHS Hostel Portal](app/static/images/vasavi_logo.png)

A comprehensive, modern, mobile-responsive web application for managing student registration, room allocation, daily snacks attendance, leave letters, housekeeping room cleaning, grievances, and executive administrative audit reports for **Sri Vasavi Engineering College Girls Hostel (GHS Hostel)**.

---

## 🌟 Key Features

### 1. 👁️ Password Visibility Control (Eye Toggle)
- Interactive eye icon (`fa-eye` / `fa-eye-slash`) inside password and confirm password fields across Student Registration, Student Login, Admin Login, Warden Login, and Principal Login.
- Prevents accidental form submissions or input resets. Passwords are securely hashed using `werkzeug.security` before database persistence.

### 2. 🆔 Auto Student Name Retrieval & Role Verification
- **Pattern Matching (First 2 & Last 3 Digits)**: Verifies student roll numbers (e.g., `23A81A1487` or `23-1487`) against the pre-approved database roster.
- **Auto-Fill**: Automatically populates the student's official **Full Name**, **Email**, **Department**, **Semester**, and **Assigned Room Number**.
- **Tamper Prevention**: Pre-approved details are locked during registration to guarantee data accuracy.

### 3. 🛏️ Dynamic Room Allocation & Warden Sorting
- **Admin Approved Student List**: Displays dedicated Room Number, Department, Semester, and Registration Status columns with inline editing.
- **Grouped Room Roster**: Displays hostel rooms with real-time capacity and bed occupancy.
- **Multi-Criteria Sorting**: Sort room roster by **Room Number (Ascending & Descending)**, **Student Name**, or **Role Number**.
- **Filtering**: Filter roster by **Floor** and **Department**.
- **Audit Tracking**: Every room reallocation is recorded in `db.room_history`.

### 4. 🍿 Daily Snacks Attendance Checkbox System
- Interactive checkbox roster for Admin and Warden to mark daily snacks distribution.
- Includes `[Save Attendance]`, `[Select All]`, `[Clear Selection]`, date picker, room filter, and department filter.
- **Dynamic Database Cards**: Calculates live counts for **Total Registered Students**, **Snacks Taken**, **Snacks Not Taken**, and **Not Yet Marked**.

### 5. ✉️ Student Leave Letter Submission System
- Enables students to submit digital leave applications with auto-retrieved credentials.
- Supports leave types: **Sick Leave**, **Emergency Leave**, **Personal Leave**, **Family Function**, and **Other**.
- Collects parent/guardian contact, address during leave, text explanation, and optional supporting document upload (`static/uploads/leaves/`).
- Generates a unique **Leave Application ID** (e.g. `LV-20261002-8419`) and pushes real-time notifications to staff dashboards.

### 6. 🩺 Leave Management Dashboard & Sick Leave Records
- Filterable leave management table for Admin, Warden, and Principal.
- Dedicated **Sick Leave Records** tab with live DB counters: **Total Sick Applications**, **Pending**, **Approved**, **Rejected**, and **Currently on Approved Sick Leave**.
- Allows staff to review applications, enter inspection remarks, and approve/reject leave.

### 7. 🧹 Housekeeping & Daily Room Cleaning Checkbook
- **Student View**: Displays room cleaning status (`Completed`, `Pending`, `Problem Reported`) and task breakdown (**Room Surface**, **Bathroom Cleaned**, **Floor Mopped**, **Waste Disposed**, **Phenyl Provided**).
- **Student Confirmation**: Includes a `[Confirm My Room is Cleaned Today]` button for students.
- **Warden Checkbook**: Modal inspection dialog per room to record attendant name, check time, task checkboxes, and comments.

### 8. 📊 Historical Audit System & Reports
- Dedicated **Daily & Monthly History Reports** section (`/admin/history-reports`).
- Supports **Single Day History**, **Monthly Summary Breakdown**, **Custom Date Range**, and **PDF Export**.
- Preserves all historical records in MongoDB Atlas across server restarts.

### 9. 📱 Mobile-First Responsive Design & Navigation
- Optimised for desktop, tablet, and smartphones ($\le 768\text{px}$).
- Includes a fixed **Mobile Bottom Navigation Bar** for 1-tap touch navigation:
  - **Student**: Home $\cdot$ Dashboard $\cdot$ Leave $\cdot$ Cleaning $\cdot$ Alerts
  - **Warden / Admin**: Home $\cdot$ Dashboard $\cdot$ Snacks $\cdot$ Cleaning $\cdot$ Alerts
  - **Principal**: Home $\cdot$ Dashboard $\cdot$ Leaves $\cdot$ Reports $\cdot$ Alerts

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Vanilla & Bootstrap 5.3), JavaScript (ES6+), FontAwesome 6, SweetAlert2.
- **Backend**: Python 3.10+, Flask, Werkzeug, Jinja2 template engine.
- **Analytics Dashboard**: Streamlit.
- **Database**: MongoDB Atlas (Cloud NoSQL DB) via `pymongo`.

---

## 🔐 Portal Roles & Permissions Matrix

| Feature / Action | Student | Warden | Admin | Principal |
| :--- | :---: | :---: | :---: | :---: |
| Show/Hide Password Toggle | Yes | Yes | Yes | Yes |
| Role Auto-Verification & Details | Self | No | Manage Roster | View |
| Room Allocation & Re-sorting | View Own | Full Manage | Full Manage | View |
| Daily Snacks Attendance | No | Mark & Save | Mark & Save | View & Monitor |
| Leave Letter Submission | Apply / View Own | Review / Approve | Review / Approve | Review / Approve |
| Sick Leave Records Tab | No | View & Manage | View & Manage | Audit & Approve |
| Room Cleaning Checkbook | Confirm / Feedback | Record & Inspect | Record & Inspect | Audit Roster |
| Historical & Monthly Reports | No | No | Access & Export | Access & Export |

---

## ⚙️ Local Installation & Setup Guide

### 1. Prerequisites
- Python 3.10 or higher installed.
- Git installed.
- MongoDB Atlas account (or local MongoDB server).

### 2. Clone the Repository
```bash
git clone https://github.com/SnehaHarshitha/Vasavi-GHS--Hostel.git
cd Vasavi-GHS--Hostel
```

### 3. Set Up Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your credentials:
```ini
SECRET_KEY=your_super_secret_key_2026
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/pg_hostel_mess?retryWrites=true&w=majority
DATABASE_NAME=pg_hostel_mess
PORT=5000
STREAMLIT_SERVER_PORT=8501
```

### 6. Run the Application
Launch both the Flask server and Streamlit dashboard using `run.py`:
```bash
python run.py
```

- **Computer Browser Access**: `http://localhost:5000`
- **Mobile Wi-Fi Access**: `http://<YOUR_COMPUTER_LOCAL_IP>:5000`
- **Streamlit Analytics Dashboard**: `http://localhost:8501`

---

## 🚀 Deployment Guidelines

1. **Production Deployment (Render / Heroku / AWS)**:
   - Set `MONGO_URI` environment variable in your production host settings.
   - Use `gunicorn app:app` as the web application process runner.
2. **MongoDB Atlas Security**:
   - Ensure Network Access whitelist includes your deployment IP or `0.0.0.0/0`.
   - Never commit `.env` or sensitive connection strings to Git repository.

---

## 📄 License & Attribution
Designed for **Sri Vasavi Engineering College Girls Hostel (GHS Hostel)**. All rights reserved.
