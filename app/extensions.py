import os
from pymongo import MongoClient, ASCENDING
from flask_login import LoginManager, UserMixin
from bson.objectid import ObjectId

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

mongo_client = None
db = None

def to_oid(val):
    if not val:
        return None
    if isinstance(val, ObjectId):
        return val
    try:
        return ObjectId(val)
    except Exception:
        return str(val)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self._id = user_data.get('_id')
        self.full_name = user_data.get('full_name', '')
        self.role_number = user_data.get('role_number', '')
        self.email = user_data.get('email', '')
        self.phone = user_data.get('phone', '')
        self.password_hash = user_data.get('password_hash', '')
        self.role = user_data.get('role', 'student') # student, warden, admin, principal
        self.department = user_data.get('department', '')
        self.year = user_data.get('year', '')
        self.parent_name = user_data.get('parent_name', '')
        self.parent_phone = user_data.get('parent_phone', '')
        self.room_number = user_data.get('room_number', '')
        self.status = user_data.get('status', 'approved') # pending, approved, rejected, blocked
        self._is_active = user_data.get('is_active', True)
        self.created_at = user_data.get('created_at')

    @property
    def is_active(self):
        return self._is_active

    def is_student(self):
        return self.role == 'student'

    def is_warden(self):
        return self.role == 'warden'

    def is_admin(self):
        return self.role == 'admin'

    def is_principal(self):
        return self.role == 'principal'

def init_mongo(app):
    global mongo_client, db
    mongo_uri = app.config.get('MONGO_URI')
    db_name = app.config.get('DATABASE_NAME', 'pg_hostel_mess')
    
    try:
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ping')
        db = mongo_client[db_name]
        app.logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        app.logger.warning(f"Primary MONGO_URI connection failed ({e}). Attempting local fallback...")
        try:
            fallback_uri = 'mongodb://localhost:27017/pg_hostel_mess'
            mongo_client = MongoClient(fallback_uri, serverSelectionTimeoutMS=3000)
            mongo_client.admin.command('ping')
            db = mongo_client[db_name]
            app.logger.info("Successfully connected to local MongoDB fallback!")
        except Exception as fallback_err:
            app.logger.error(f"Error connecting to MongoDB: {fallback_err}")
            db = None
            return

    if db is not None:
        try:
            db.users.create_index([("role_number", ASCENDING)], unique=True, sparse=True)
            db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
            db.rooms.create_index([("room_number", ASCENDING)], unique=True)
            db.food_selections.create_index([("student_id", ASCENDING), ("date", ASCENDING)], unique=True)
            
            # Auto-seed database if empty on Render / cloud MongoDB Atlas
            if db.users.count_documents({}) == 0:
                try:
                    from scripts.seed_sample_data import seed_sample_data
                    seed_sample_data()
                    app.logger.info("Successfully auto-seeded MongoDB Atlas database!")
                except Exception as seed_err:
                    app.logger.warning(f"Auto-seeding note: {seed_err}")
        except Exception as idx_err:
            app.logger.warning(f"Error setting up MongoDB indexes: {idx_err}")


def get_db():
    global db
    return db

FALLBACK_USERS = {}

@login_manager.user_loader
def load_user(user_id):
    database = get_db()
    if database is not None:
        try:
            user_data = database.users.find_one({"_id": to_oid(user_id)})
            if user_data:
                return User(user_data)
        except Exception:
            pass
            
    if user_id in FALLBACK_USERS:
        return User(FALLBACK_USERS[user_id])

    return None
