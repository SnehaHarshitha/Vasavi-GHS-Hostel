"""
run.py — Independent Launcher for GHS Hostel Mess Management System
Starts Flask backend (app.py) & Streamlit dashboard (streamlit_dashboard/dashboard.py),
verifies health check endpoint (/health), and auto-opens default web browser.
"""
import sys
import os
import io
import socket
import subprocess
import time
import urllib.request
import webbrowser
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, '.env')
ENV_EXAMPLE = os.path.join(BASE_DIR, '.env.example')

# Ensure .env exists
if not os.path.exists(ENV_FILE):
    if os.path.exists(ENV_EXAMPLE):
        print("ℹ️ .env missing. Copying default configuration from .env.example...")
        with open(ENV_EXAMPLE, 'r', encoding='utf-8') as src, open(ENV_FILE, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    else:
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write("SECRET_KEY=ghs-hostel-secret-key-2026\n")
            f.write("MONGO_URI=mongodb://localhost:27017/pg_hostel_mess\n")
            f.write("DATABASE_NAME=pg_hostel_mess\n")

load_dotenv(ENV_FILE)

BACKEND_PORT = int(os.getenv('PORT', 5000))
FRONTEND_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', 8501))


def get_local_ip():
    """Returns local network IP address for mobile phone Wi-Fi access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def free_port(port):
    """Frees specified port if occupied by an orphaned process."""
    if sys.platform == 'win32':
        try:
            cmd = f'netstat -ano | findstr LISTENING | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            lines = output.strip().splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid and pid != '0' and pid != str(os.getpid()):
                        print(f"🧹 Clearing port {port} (releasing orphaned process PID {pid})...")
                        subprocess.run(['taskkill', '/F', '/PID', pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def check_and_seed_db():
    """Ensure database has basic seed data before startup."""
    try:
        from pymongo import MongoClient
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pg_hostel_mess')
        db_name = os.getenv('DATABASE_NAME', 'pg_hostel_mess')
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]
        if db.users.count_documents({}) == 0:
            print("🌱 Empty database detected! Seeding initial sample data...")
            seed_script = os.path.join(BASE_DIR, 'scripts', 'seed_sample_data.py')
            subprocess.run([sys.executable, seed_script], cwd=BASE_DIR, check=False)
        else:
            print("✅ MongoDB Atlas connection established successfully.")
    except Exception as e:
        print(f"⚠️ Database connection notice: {e}")


def start_backend():
    print(f"🚀 Starting Flask backend on 0.0.0.0:{BACKEND_PORT} ...")
    free_port(BACKEND_PORT)
    env = os.environ.copy()
    env['PYTHONPATH'] = BASE_DIR
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=BASE_DIR,
        env=env
    )
    return proc


def start_frontend():
    time.sleep(1)
    print(f"🎨 Starting Streamlit analytics dashboard on port {FRONTEND_PORT} ...")
    free_port(FRONTEND_PORT)
    proc = subprocess.Popen(
        [sys.executable, '-m', 'streamlit', 'run', 'streamlit_dashboard/dashboard.py',
         '--server.port', str(FRONTEND_PORT),
         '--server.headless', 'true',
         '--browser.gatherUsageStats', 'false'],
        cwd=BASE_DIR
    )
    return proc


def verify_backend(port, retries=15, delay=0.8):
    url = f"http://localhost:{port}/health"
    fallback_url = f"http://localhost:{port}/"
    for _ in range(retries):
        for test_url in (url, fallback_url):
            try:
                req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.status in (200, 302, 301):
                        return True
            except Exception:
                pass
        time.sleep(delay)
    return False


def main():
    local_ip = get_local_ip()
    print("=" * 68)
    print("  GHS Hostel Mess Management System — Server Active")
    print("=" * 68)
    print(f"  💻 Computer Web Access:   http://localhost:{BACKEND_PORT}")
    print(f"  📱 Mobile Phone Wi-Fi:    http://{local_ip}:{BACKEND_PORT}")
    print(f"  🔍 Server Health Endpoint: http://localhost:{BACKEND_PORT}/health")
    print(f"  📊 Streamlit Staff Portal: http://localhost:{FRONTEND_PORT}")
    print("=" * 68)

    check_and_seed_db()

    backend_proc = start_backend()
    frontend_proc = start_frontend()

    print("\n⏳ Verifying server connection...")
    if verify_backend(BACKEND_PORT):
        print(f"\n✅ Website is online and running successfully at http://localhost:{BACKEND_PORT}")
        print(f"📱 Mobile network link: http://{local_ip}:{BACKEND_PORT}")
        print(f"🌐 Auto-opening http://localhost:{BACKEND_PORT} in your default browser...")
        try:
            webbrowser.open(f"http://localhost:{BACKEND_PORT}")
        except Exception as err:
            print(f"⚠️ Could not open browser automatically: {err}")
    else:
        print(f"\n⚠️ Server started. Access at http://localhost:{BACKEND_PORT}")

    print("\n💡 Press Ctrl+C in this terminal window to stop the server.")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()
        print("✅ Servers stopped successfully.")


if __name__ == '__main__':
    main()

