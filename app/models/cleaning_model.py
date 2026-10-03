from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class CleaningModel:
    @staticmethod
    def save_checkbook(room_number, date_str, room_cleaned=False, bathroom_cleaned=False, floor_cleaned=False, waste_removed=False, phenyl_kept=False, cleaned_by="Housekeeping Staff", checked_by="Warden", remarks="", check_time=None):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        if not check_time:
            check_time = now.strftime('%I:%M %p')

        if room_cleaned and bathroom_cleaned and floor_cleaned and waste_removed:
            status = 'Completed'
        elif not room_cleaned and not bathroom_cleaned and not floor_cleaned:
            status = 'Not Completed'
        else:
            status = 'Pending'

        update_doc = {
            'room_number': room_number,
            'date': date_str,
            'room_cleaned': bool(room_cleaned),
            'bathroom_cleaned': bool(bathroom_cleaned),
            'floor_cleaned': bool(floor_cleaned),
            'waste_removed': bool(waste_removed),
            'phenyl_kept': bool(phenyl_kept),
            'cleaned_by': cleaned_by,
            'checked_by': checked_by,
            'check_time': check_time,
            'remarks': remarks,
            'status': status,
            'updated_at': now
        }

        try:
            return db.cleaning_records.update_one(
                {'room_number': room_number, 'date': date_str},
                {'$set': update_doc},
                upsert=True
            )
        except Exception:
            return None

    @staticmethod
    def record_cleaning(room_number, date_str, status, cleaned_by="Staff", remarks="", photo_url=""):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        try:
            db.cleaning_records.update_one(
                {'room_number': room_number, 'date': date_str},
                {'$set': {
                    'room_number': room_number,
                    'date': date_str,
                    'status': status,
                    'cleaned_by': cleaned_by,
                    'remarks': remarks,
                    'photo_url': photo_url,
                    'updated_at': now
                }},
                upsert=True
            )
        except Exception:
            pass

    @staticmethod
    def get_cleaning_by_date(date_str):
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.cleaning_records.find({'date': date_str}))
        except Exception:
            return []

    @staticmethod
    def get_room_cleaning(room_number, date_str):
        db = get_db()
        if db is None:
            return None
        try:
            return db.cleaning_records.find_one({'room_number': room_number, 'date': date_str})
        except Exception:
            return None

    @staticmethod
    def get_room_cleaning_history(room_number, limit=30):
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.cleaning_records.find({'room_number': room_number}).sort('date', -1).limit(limit))
        except Exception:
            return []

    @staticmethod
    def get_daily_cleaning_stats(date_str):
        db = get_db()
        if db is None:
            return {
                'date': date_str,
                'completed': 0,
                'pending': 0,
                'total_rooms': 0
            }
        try:
            completed = db.cleaning_records.count_documents({'date': date_str, 'status': 'Completed'})
            pending = db.cleaning_records.count_documents({'date': date_str, 'status': {'$ne': 'Completed'}})
            total_rooms = db.rooms.count_documents({})
            return {
                'date': date_str,
                'completed': completed,
                'pending': max(0, total_rooms - completed),
                'total_rooms': total_rooms
            }
        except Exception:
            return {
                'date': date_str,
                'completed': 0,
                'pending': 0,
                'total_rooms': 0
            }

    # Sunday Phenyl / Cleaning Tasks
    @staticmethod
    def create_sunday_task(task_name, date_str, rooms_or_floor, assigned_staff, instructions=""):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        task = {
            'task_name': task_name, # Default: "Sunday Room Phenyl Cleaning"
            'date': date_str,
            'rooms_or_floor': rooms_or_floor,
            'assigned_staff': assigned_staff,
            'instructions': instructions,
            'status': 'Scheduled', # 'Scheduled', 'In Progress', 'Completed'
            'created_at': now,
            'updated_at': now
        }
        try:
            return db.sunday_tasks.insert_one(task).inserted_id
        except Exception:
            return None

    @staticmethod
    def get_all_sunday_tasks():
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.sunday_tasks.find().sort('date', -1))
        except Exception:
            return []

    @staticmethod
    def update_sunday_task_status(task_id, status, remarks=""):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        try:
            return db.sunday_tasks.update_one(
                {'_id': to_oid(task_id)},
                {'$set': {'status': status, 'remarks': remarks, 'updated_at': now}}
            )
        except Exception:
            return None

    @staticmethod
    def get_latest_sunday_task():
        db = get_db()
        if db is None:
            return None
        try:
            return db.sunday_tasks.find_one(sort=[('date', -1)])
        except Exception:
            return None
