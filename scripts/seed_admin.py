import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pg_hostel_mess')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'pg_hostel_mess')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@pghostelmess.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'AdminPass123!')

def seed_admin():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    existing = db.users.find_one({'email': ADMIN_EMAIL.lower()})
    if existing:
        print(f"Admin account already exists: {ADMIN_EMAIL}")
        return

    admin_doc = {
        'full_name': 'Super Administrator',
        'email': ADMIN_EMAIL.lower(),
        'password_hash': generate_password_hash(ADMIN_PASSWORD),
        'role': 'admin',
        'phone': '+91 98480 00000',
        'status': 'approved',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    db.users.insert_one(admin_doc)
    print(f"Successfully created Super Admin user!")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")

if __name__ == '__main__':
    seed_admin()
