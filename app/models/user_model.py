from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app.extensions import get_db

class UserModel:
    @staticmethod
    def create_user(user_data):
        db = get_db()
        if 'password' in user_data:
            user_data['password_hash'] = generate_password_hash(user_data.pop('password'))
        
        # Omit empty strings for unique sparse indexed fields
        if 'email' in user_data:
            if user_data['email']:
                user_data['email'] = user_data['email'].strip().lower()
            else:
                user_data.pop('email')

        if 'role_number' in user_data:
            if user_data['role_number']:
                user_data['role_number'] = user_data['role_number'].strip().upper()
                user_data['username'] = user_data['role_number']
            else:
                user_data.pop('role_number')

        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()
        if 'status' not in user_data or not user_data['status']:
            user_data['status'] = 'approved'
        if 'is_active' not in user_data:
            user_data['is_active'] = True

        result = db.users.insert_one(user_data)
        return result.inserted_id

    @staticmethod
    def find_by_email(email_or_username):
        if not email_or_username or not str(email_or_username).strip():
            return None
        db = get_db()
        raw = str(email_or_username).strip()
        lower_val = raw.lower()
        upper_val = raw.upper()

        return db.users.find_one({
            '$or': [
                {'email': lower_val},
                {'email': raw},
                {'role_number': upper_val},
                {'role_number': raw},
                {'username': lower_val},
                {'username': upper_val},
                {'username': raw}
            ]
        })

    @staticmethod
    def find_by_role_number(role_number):
        if not role_number or not str(role_number).strip():
            return None
        db = get_db()
        raw = str(role_number).strip()
        upper_val = raw.upper()
        lower_val = raw.lower()

        return db.users.find_one({
            '$or': [
                {'role_number': upper_val},
                {'role_number': raw},
                {'username': lower_val},
                {'username': upper_val},
                {'username': raw},
                {'email': lower_val}
            ]
        })

    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        try:
            return db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            return None

    @staticmethod
    def verify_password(stored_hash, password):
        if not stored_hash or not password:
            return False
        return check_password_hash(stored_hash, str(password).strip())

    @staticmethod
    def update_user(user_id, update_data):
        db = get_db()
        update_data['updated_at'] = datetime.utcnow()
        if 'password' in update_data:
            update_data['password_hash'] = generate_password_hash(update_data.pop('password'))
        return db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})

    @staticmethod
    def get_all_by_role(role=None, status=None):
        db = get_db()
        query = {}
        if role:
            query['role'] = role
        if status:
            query['status'] = status
        return list(db.users.find(query).sort('created_at', -1))

    @staticmethod
    def count_students(status=None):
        db = get_db()
        query = {'role': 'student'}
        if status:
            query['status'] = status
        return db.users.count_documents(query)

    @staticmethod
    def delete_user(user_id):
        db = get_db()
        return db.users.delete_one({'_id': ObjectId(user_id)})
