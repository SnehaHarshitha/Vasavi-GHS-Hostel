from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from app.extensions import get_db

class UserModel:
    @staticmethod
    def create_user(user_data):
        db = get_db()
        if db is None:
            return None
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

        try:
            result = db.users.insert_one(user_data)
            return result.inserted_id
        except Exception:
            # Fallback for existing user or duplicate key
            query = []
            if user_data.get('email'):
                query.append({'email': user_data['email']})
            if user_data.get('role_number'):
                query.append({'role_number': user_data['role_number']})
            if user_data.get('role'):
                query.append({'role': user_data['role']})
            if query:
                existing = db.users.find_one({'$or': query})
                if existing:
                    return existing['_id']
            return None

    @staticmethod
    def find_by_email(email_or_username):
        if not email_or_username or not str(email_or_username).strip():
            return None
        db = get_db()
        if db is None:
            return None
        raw = str(email_or_username).strip()
        lower_val = raw.lower()
        upper_val = raw.upper()

        try:
            # Role alias matching for caretaker / warden / admin / principal
            if lower_val in ['caretaker', 'warden', 'warden@pghostelmess.com', 'caretaker@pghostelmess.com']:
                found = db.users.find_one({'$or': [{'role': {'$in': ['warden', 'caretaker']}}, {'username': {'$in': ['warden', 'caretaker']}}, {'email': lower_val}]})
                if found:
                    return found
            elif lower_val in ['admin', 'admin@pghostelmess.com']:
                found = db.users.find_one({'$or': [{'role': 'admin'}, {'username': 'admin'}, {'email': lower_val}]})
                if found:
                    return found
            elif lower_val in ['principal', 'principal@pghostelmess.com']:
                found = db.users.find_one({'$or': [{'role': 'principal'}, {'username': 'principal'}, {'email': lower_val}]})
                if found:
                    return found

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
        except Exception:
            return None

    @staticmethod
    def find_by_role_number(role_number):
        if not role_number or not str(role_number).strip():
            return None
        db = get_db()
        if db is None:
            return None
        raw = str(role_number).strip()
        upper_val = raw.upper()
        lower_val = raw.lower()

        try:
            res = db.users.find_one({
                '$or': [
                    {'role_number': upper_val},
                    {'role_number': raw},
                    {'username': lower_val},
                    {'username': upper_val},
                    {'username': raw},
                    {'email': lower_val}
                ]
            })
            if res:
                return res

            import re
            entered_digits = re.sub(r'\D', '', upper_val)
            if len(entered_digits) >= 4:
                e_first_2 = entered_digits[:2]
                e_last_3 = entered_digits[-3:]
                all_users = list(db.users.find({'role': 'student'}))
                for u in all_users:
                    u_roll = str(u.get('role_number', '')).strip().upper()
                    u_digits = re.sub(r'\D', '', u_roll)
                    if len(u_digits) >= 4 and u_digits[:2] == e_first_2 and u_digits[-3:] == e_last_3:
                        return u
        except Exception:
            return None
        return None

    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        if db is None:
            return None
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
        if db is None:
            return None
        update_data['updated_at'] = datetime.utcnow()
        if 'password' in update_data:
            update_data['password_hash'] = generate_password_hash(update_data.pop('password'))
        return db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})

    @staticmethod
    def get_all_by_role(role=None, status=None):
        db = get_db()
        if db is None:
            return []
        query = {}
        if role:
            query['role'] = role
        if status:
            query['status'] = status
        try:
            return list(db.users.find(query).sort('created_at', -1))
        except Exception:
            return []

    @staticmethod
    def count_students(status=None):
        db = get_db()
        if db is None:
            return 0
        query = {'role': 'student'}
        if status:
            query['status'] = status
        try:
            return db.users.count_documents(query)
        except Exception:
            return 0

    @staticmethod
    def delete_user(user_id):
        db = get_db()
        if db is None:
            return None
        return db.users.delete_one({'_id': ObjectId(user_id)})
