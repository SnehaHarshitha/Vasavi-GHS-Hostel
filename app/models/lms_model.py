import re
from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class LMSModel:
    # ----------------------------------------------------
    # ANNOUNCEMENTS
    # ----------------------------------------------------
    @staticmethod
    def get_announcements(target_role=None):
        db = get_db()
        if db is None:
            return []
        query = {}
        if target_role:
            query['target_role'] = {'$in': [target_role, 'all']}
        try:
            return list(db.announcements.find(query).sort('created_at', -1))
        except Exception:
            return []

    @staticmethod
    def get_announcement_by_id(anc_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.announcements.find_one({'_id': to_oid(anc_id)})
        except Exception:
            return None

    @staticmethod
    def create_announcement(data):
        db = get_db()
        if db is None:
            return None
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.announcements.insert_one(data).inserted_id
        except Exception:
            return None

    @staticmethod
    def update_announcement(anc_id, data):
        db = get_db()
        if db is None:
            return None
        data['updated_at'] = datetime.utcnow()
        try:
            return db.announcements.update_one({'_id': to_oid(anc_id)}, {'$set': data})
        except Exception:
            return None

    @staticmethod
    def delete_announcement(anc_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.announcements.delete_one({'_id': to_oid(anc_id)})
        except Exception:
            return None


    # ----------------------------------------------------
    # APPROVED STUDENT LIST & ACCESS CONTROL
    # ----------------------------------------------------
    @staticmethod
    def is_matching_student(approved, user):
        app_roll = str(approved.get('roll_number', '')).strip().upper()
        app_email = str(approved.get('email', '')).strip().lower()
        app_name = re.sub(r'[^a-zA-Z]', '', str(approved.get('full_name', ''))).lower()

        user_roll = str(user.get('role_number', '')).strip().upper()
        user_email = str(user.get('email', '')).strip().lower()
        user_name = re.sub(r'[^a-zA-Z]', '', str(user.get('full_name', ''))).lower()

        # 1. Exact match on roll number, username, or email
        if app_roll and (app_roll == user_roll or app_roll == str(user.get('username', '')).upper()):
            return True
        if app_email and app_email == user_email:
            return True

        # 2. Email prefix match (e.g. "23109@srivasaviengg.ac.in" vs "23a81a109@srivasaviengg.ac.in")
        app_email_prefix = app_email.split('@')[0] if app_email else ''
        user_email_prefix = user_email.split('@')[0] if user_email else ''
        if app_email_prefix and len(app_email_prefix) >= 3 and (app_email_prefix in user_roll.lower() or app_email_prefix == user_email_prefix):
            return True

        # 3. Suffix / Digits match + Name match
        app_digits = re.sub(r'\D', '', app_roll)
        user_digits = re.sub(r'\D', '', user_roll)
        if app_digits and user_digits and (app_digits == user_digits or app_digits in user_digits or user_digits in app_digits):
            if app_name and user_name and (app_name == user_name or app_name in user_name or user_name in app_name):
                return True

        # 4. Same normalized name
        if len(app_name) >= 5 and app_name == user_name:
            return True

        return False

    @staticmethod
    def get_approved_students():
        default_approved = [
            {'_id': 'app_101', 'roll_number': '21A81A0501', 'full_name': 'K. Bhavana', 'email': 'bhavana@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '5', 'phone': '+91 98765 00001', 'room_number': '101', 'is_registered': True},
            {'_id': 'app_102', 'roll_number': '21A81A0502', 'full_name': 'M. Sneha Latha', 'email': 'sneha@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '5', 'phone': '+91 98765 00002', 'room_number': '101', 'is_registered': True},
            {'_id': 'app_103', 'roll_number': '22A81A0403', 'full_name': 'P. Sreeja', 'email': 'sreeja@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '3', 'phone': '+91 98765 00003', 'room_number': '102', 'is_registered': True},
            {'_id': 'app_104', 'roll_number': '23A81A1204', 'full_name': 'T. Harika', 'email': 'harika@srivasaviengg.ac.in', 'department': 'IT', 'semester': '1', 'phone': '+91 98765 00004', 'room_number': '201', 'is_registered': True},
            {'_id': 'app_105', 'roll_number': '21A81A0205', 'full_name': 'V. Deepthi', 'email': 'deepthi@srivasaviengg.ac.in', 'department': 'EEE', 'semester': '5', 'phone': '+91 98765 00005', 'room_number': '102', 'is_registered': True},
            {'_id': 'app_106', 'roll_number': '23A81A109', 'full_name': 'G. Harini', 'email': 'harini23a81a109@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '3', 'phone': '+91 98480 12345', 'room_number': '101', 'is_registered': True}
        ]
        db = get_db()
        if db is None:
            return default_approved

        try:
            approved_list = list(db.approved_students.find().sort('roll_number', 1))
            if not approved_list:
                return default_approved
            user_students = list(db.users.find({'role': 'student'}))

            for s in approved_list:
                if not s.get('is_registered'):
                    for u in user_students:
                        if LMSModel.is_matching_student(s, u):
                            s['is_registered'] = True
                            s['registered_user_id'] = str(u['_id'])
                            try:
                                db.approved_students.update_one({'_id': s['_id']}, {'$set': {'is_registered': True, 'registered_user_id': str(u['_id'])}})
                            except Exception:
                                pass
                            break
            return approved_list
        except Exception:
            return default_approved

    @staticmethod
    def find_approved_student(roll_number=None, email=None):
        db = get_db()
        if db is None:
            return None

        r_upper = str(roll_number).strip().upper() if roll_number else ''
        e_lower = str(email).strip().lower() if email else ''
        r_digits = re.sub(r'\D', '', r_upper)

        approved_list = list(db.approved_students.find())
        for s in approved_list:
            s_roll = str(s.get('roll_number', '')).strip().upper()
            s_email = str(s.get('email', '')).strip().lower()
            s_digits = re.sub(r'\D', '', s_roll)

            if r_upper and (r_upper == s_roll or (r_digits and r_digits == s_digits)):
                return s
            if e_lower and (e_lower == s_email or e_lower.split('@')[0] == s_email.split('@')[0]):
                return s

        return None

    @staticmethod
    def match_approved_student_by_role_number(entered_role):
        from app.models.user_model import UserModel
        db = get_db()
        if db is None or not entered_role or not str(entered_role).strip():
            return {
                'status': 'error',
                'code': 'MISSING_FIELDS',
                'message': 'Required Fields Missing'
            }

        raw_entered = str(entered_role).strip().upper()
        if len(raw_entered) < 4:
            return {
                'status': 'error',
                'code': 'INVALID_LENGTH',
                'message': 'Role Number is too short.'
            }

        first_2 = raw_entered[:2]
        last_3 = raw_entered[-3:]
        entered_digits = re.sub(r'\D', '', raw_entered)

        approved_list = list(db.approved_students.find())
        candidates = []

        for s in approved_list:
            s_roll = str(s.get('roll_number', '')).strip().upper()
            if len(s_roll) < 4:
                continue

            s_first_2 = s_roll[:2]
            s_last_3 = s_roll[-3:]
            s_digits = re.sub(r'\D', '', s_roll)

            # 1. Match first 2 digits AND last 3 digits/chars
            if (s_first_2 == first_2 and s_last_3 == last_3) or (
                len(entered_digits) >= 4 and len(s_digits) >= 4 and
                s_digits[:2] == entered_digits[:2] and s_digits[-3:] == entered_digits[-3:]
            ):
                candidates.append(s)

        if len(candidates) == 0:
            return {
                'status': 'error',
                'code': 'NOT_FOUND',
                'message': 'Your Role Number is not available in the Admin Approved Students List. Please contact the Admin.'
            }

        # Deduplicate candidates by student name & roll number (e.g. if duplicate records exist in db.approved_students)
        unique_candidates = []
        seen_names = set()
        for c in candidates:
            c_name = str(c.get('full_name', '')).strip().lower()
            c_roll = str(c.get('roll_number', '')).strip().upper()
            key = (c_name, c_roll)
            if key not in seen_names:
                seen_names.add(key)
                unique_candidates.append(c)

        if len(unique_candidates) == 1:
            candidate = unique_candidates[0]
        else:
            # Check for exact full roll match or exact digit match
            exact_matches = [c for c in unique_candidates if str(c.get('roll_number', '')).strip().upper() == raw_entered]
            if len(exact_matches) >= 1:
                candidate = exact_matches[0]
            else:
                exact_digits_matches = [
                    c for c in unique_candidates
                    if re.sub(r'\D', '', str(c.get('roll_number', ''))) == entered_digits
                ]
                if len(exact_digits_matches) >= 1:
                    candidate = exact_digits_matches[0]
                else:
                    candidate = unique_candidates[0]

        # Check if candidate is ALREADY REGISTERED
        cand_roll = str(candidate.get('roll_number', '')).strip().upper()
        cand_email = str(candidate.get('email', '')).strip().lower()

        existing_user = (
            UserModel.find_by_role_number(cand_roll) or
            UserModel.find_by_role_number(raw_entered) or
            (UserModel.find_by_email(cand_email) if cand_email else None)
        )

        if candidate.get('is_registered') or existing_user:
            return {
                'status': 'error',
                'code': 'ALREADY_REGISTERED',
                'message': 'This Role Number is already registered. Please log in to your account.'
            }

        is_exact = (cand_roll == raw_entered)
        return {
            'status': 'success',
            'match_type': 'exact' if is_exact else 'partial',
            'candidate': {
                'id': str(candidate['_id']),
                'roll_number': cand_roll,
                'full_name': candidate.get('full_name', ''),
                'email': cand_email,
                'department': candidate.get('department', 'CSE'),
                'semester': str(candidate.get('semester', '5')),
                'phone': candidate.get('phone', ''),
                'room_number': candidate.get('room_number', '101')
            }
        }

    @staticmethod
    def get_approved_student_by_id(app_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.approved_students.find_one({'_id': to_oid(app_id)})
        except Exception:
            return None

    @staticmethod
    def create_approved_student(data):
        db = get_db()
        if db is None:
            return None
        data['roll_number'] = str(data.get('roll_number', '')).strip().upper()
        data['email'] = str(data.get('email', '')).strip().lower()
        data['created_at'] = datetime.utcnow()
        data['is_registered'] = data.get('is_registered', False)
        try:
            return db.approved_students.insert_one(data).inserted_id
        except Exception:
            return None

    @staticmethod
    def update_approved_student(app_id, data):
        db = get_db()
        if db is None:
            return None
        if 'roll_number' in data:
            data['roll_number'] = str(data['roll_number']).strip().upper()
        if 'email' in data:
            data['email'] = str(data['email']).strip().lower()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.approved_students.update_one({'_id': to_oid(app_id)}, {'$set': data})
        except Exception:
            return None

    @staticmethod
    def delete_approved_student(app_id):
        db = get_db()
        if db is None:
            return None
        student = LMSModel.get_approved_student_by_id(app_id)
        if student:
            # Delete corresponding user account if exists
            try:
                db.users.delete_one({'role_number': student.get('roll_number')})
            except Exception:
                pass
        try:
            return db.approved_students.delete_one({'_id': to_oid(app_id)})
        except Exception:
            return None

    @staticmethod
    def bulk_import_approved_students(students_list):
        db = get_db()
        count = 0
        for item in students_list:
            roll_no = str(item.get('roll_number', '')).strip().upper()
            email = str(item.get('email', '')).strip().lower()
            if not roll_no:
                continue
            existing = db.approved_students.find_one({'roll_number': roll_no})
            if not existing:
                item['roll_number'] = roll_no
                item['email'] = email
                item['created_at'] = datetime.utcnow()
                item['is_registered'] = False
                db.approved_students.insert_one(item)
                count += 1
        return count
