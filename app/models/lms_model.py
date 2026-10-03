import re
from datetime import datetime
from app.extensions import get_db, to_oid

FALLBACK_APPROVED_STUDENTS = [
    {'_id': 'app_101', 'roll_number': '21A81A0501', 'full_name': 'K. Bhavana', 'email': 'bhavana@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '5', 'phone': '+91 98765 00001', 'room_number': '101', 'is_registered': True},
    {'_id': 'app_102', 'roll_number': '21A81A0502', 'full_name': 'M. Sneha Latha', 'email': 'sneha@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '5', 'phone': '+91 98765 00002', 'room_number': '101', 'is_registered': True},
    {'_id': 'app_103', 'roll_number': '22A81A0403', 'full_name': 'P. Sreeja', 'email': 'sreeja@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '3', 'phone': '+91 98765 00003', 'room_number': '102', 'is_registered': True},
    {'_id': 'app_104', 'roll_number': '23A81A1204', 'full_name': 'T. Harika', 'email': 'harika@srivasaviengg.ac.in', 'department': 'IT', 'semester': '1', 'phone': '+91 98765 00004', 'room_number': '201', 'is_registered': True},
    {'_id': 'app_105', 'roll_number': '21A81A0205', 'full_name': 'V. Deepthi', 'email': 'deepthi@srivasaviengg.ac.in', 'department': 'EEE', 'semester': '5', 'phone': '+91 98765 00005', 'room_number': '102', 'is_registered': True},
    {'_id': 'app_106', 'roll_number': '23A81A109', 'full_name': 'G. Harini', 'email': 'harini23a81a109@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '3', 'phone': '+91 98480 12345', 'room_number': '101', 'is_registered': True}
]

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

        if app_roll and (app_roll == user_roll or app_roll == str(user.get('username', '')).upper()):
            return True
        if app_email and app_email == user_email:
            return True

        app_email_prefix = app_email.split('@')[0] if app_email else ''
        user_email_prefix = user_email.split('@')[0] if user_email else ''
        if app_email_prefix and len(app_email_prefix) >= 3 and (app_email_prefix in user_roll.lower() or app_email_prefix == user_email_prefix):
            return True

        app_digits = re.sub(r'\D', '', app_roll)
        user_digits = re.sub(r'\D', '', user_roll)
        if app_digits and user_digits and (app_digits == user_digits or app_digits in user_digits or user_digits in app_digits):
            if app_name and user_name and (app_name == user_name or app_name in user_name or user_name in app_name):
                return True

        if len(app_name) >= 5 and app_name == user_name:
            return True

        return False

    @staticmethod
    def get_approved_students():
        db = get_db()
        if db is None:
            return list(FALLBACK_APPROVED_STUDENTS)

        try:
            approved_list = list(db.approved_students.find().sort('roll_number', 1))
            if not approved_list:
                now = datetime.utcnow()
                for s in FALLBACK_APPROVED_STUDENTS:
                    s_copy = dict(s)
                    s_copy.pop('_id', None)
                    s_copy['created_at'] = now
                    try:
                        db.approved_students.insert_one(s_copy)
                    except Exception:
                        pass
                approved_list = list(db.approved_students.find().sort('roll_number', 1))

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
            return approved_list if approved_list else list(FALLBACK_APPROVED_STUDENTS)
        except Exception:
            return list(FALLBACK_APPROVED_STUDENTS)

    @staticmethod
    def find_approved_student(roll_number=None, email=None):
        db = get_db()
        r_upper = str(roll_number).strip().upper() if roll_number else ''
        e_lower = str(email).strip().lower() if email else ''
        r_digits = re.sub(r'\D', '', r_upper)

        approved_list = LMSModel.get_approved_students()
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
        if not entered_role or not str(entered_role).strip():
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

        approved_list = LMSModel.get_approved_students()
        candidates = []

        for s in approved_list:
            s_roll = str(s.get('roll_number', '')).strip().upper()
            if len(s_roll) < 4:
                continue

            s_first_2 = s_roll[:2]
            s_last_3 = s_roll[-3:]
            s_digits = re.sub(r'\D', '', s_roll)

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
        students = LMSModel.get_approved_students()
        for s in students:
            if str(s.get('_id')) == str(app_id):
                return s
        db = get_db()
        if db is None:
            return None
        try:
            return db.approved_students.find_one({'_id': to_oid(app_id)})
        except Exception:
            return None

    @staticmethod
    def create_approved_student(data):
        roll_no = str(data.get('roll_number', '')).strip().upper()
        email = str(data.get('email', '')).strip().lower()
        full_name = str(data.get('full_name', '')).strip()
        dept = str(data.get('department', 'CSE')).strip()
        sem = str(data.get('semester', '5')).strip()
        phone = str(data.get('phone', '')).strip()
        room = str(data.get('room_number', '101')).strip()

        clean_id = f"app_{int(datetime.utcnow().timestamp())}_{re.sub(r'[^a-zA-Z0-9]', '_', roll_no)}"
        doc = {
            '_id': clean_id,
            'roll_number': roll_no,
            'full_name': full_name or roll_no,
            'email': email or f"{roll_no.lower()}@srivasaviengg.ac.in",
            'department': dept or 'CSE',
            'semester': sem or '5',
            'phone': phone,
            'room_number': room or '101',
            'is_registered': data.get('is_registered', False),
            'created_at': datetime.utcnow()
        }

        FALLBACK_APPROVED_STUDENTS.insert(0, doc)

        db = get_db()
        if db is not None:
            db_doc = dict(doc)
            db_doc.pop('_id', None)
            try:
                return db.approved_students.insert_one(db_doc).inserted_id
            except Exception:
                return doc['_id']
        return doc['_id']

    @staticmethod
    def update_approved_student(app_id, data):
        r_upper = str(data.get('roll_number', '')).strip().upper()
        for s in FALLBACK_APPROVED_STUDENTS:
            if str(s.get('_id')) == str(app_id) or (r_upper and str(s.get('roll_number')).upper() == r_upper):
                s.update({k: v for k, v in data.items() if v is not None})
                break

        db = get_db()
        if db is None:
            return True

        if 'roll_number' in data:
            data['roll_number'] = str(data['roll_number']).strip().upper()
        if 'email' in data:
            data['email'] = str(data['email']).strip().lower()
        data['updated_at'] = datetime.utcnow()
        try:
            res = db.approved_students.update_one({'_id': to_oid(app_id)}, {'$set': data})
            if res.matched_count == 0 and r_upper:
                db.approved_students.update_one({'roll_number': r_upper}, {'$set': data})
            return True
        except Exception:
            return True

    @staticmethod
    def delete_approved_student(app_id):
        global FALLBACK_APPROVED_STUDENTS
        student = LMSModel.get_approved_student_by_id(app_id)
        roll = student.get('roll_number') if student else None

        FALLBACK_APPROVED_STUDENTS = [s for s in FALLBACK_APPROVED_STUDENTS if str(s.get('_id')) != str(app_id) and s.get('roll_number') != roll]

        db = get_db()
        if db is None:
            return True

        if student:
            try:
                db.users.delete_one({'role_number': student.get('roll_number')})
            except Exception:
                pass
        try:
            res = db.approved_students.delete_one({'_id': to_oid(app_id)})
            if res.deleted_count == 0 and roll:
                db.approved_students.delete_one({'roll_number': roll})
            return True
        except Exception:
            return True

    @staticmethod
    def bulk_import_approved_students(students_list):
        db = get_db()
        count = 0
        if not students_list:
            return 0

        existing_rolls_fb = {str(s.get('roll_number', '')).strip().upper() for s in FALLBACK_APPROVED_STUDENTS}
        existing_emails_fb = {str(s.get('email', '')).strip().lower() for s in FALLBACK_APPROVED_STUDENTS}

        for item in students_list:
            roll_no = str(item.get('roll_number', '')).strip().upper()
            email = str(item.get('email', '')).strip().lower()
            name = str(item.get('full_name', '')).strip()
            dept = str(item.get('department', 'CSE')).strip()
            sem = str(item.get('semester', '5')).strip()
            phone = str(item.get('phone', '')).strip()
            room = str(item.get('room_number', '101')).strip()

            if not roll_no and not name:
                continue

            if not roll_no:
                roll_no = re.sub(r'[^A-Z0-9]', '', name.upper())[:10]

            if not email:
                clean_r = roll_no.lower().replace('-', '').replace('.', '')
                email = f"{clean_r}@srivasaviengg.ac.in"

            clean_id = f"app_imp_{int(datetime.utcnow().timestamp())}_{count}_{re.sub(r'[^a-zA-Z0-9]', '_', roll_no)}"
            fb_doc = {
                '_id': clean_id,
                'roll_number': roll_no,
                'full_name': name or roll_no,
                'email': email,
                'department': dept or 'CSE',
                'semester': sem or '5',
                'phone': phone,
                'room_number': room or '101',
                'is_registered': False,
                'created_at': datetime.utcnow()
            }

            if roll_no not in existing_rolls_fb and email not in existing_emails_fb:
                FALLBACK_APPROVED_STUDENTS.append(fb_doc)
                existing_rolls_fb.add(roll_no)
                existing_emails_fb.add(email)

            if db is not None:
                try:
                    query = {'$or': [{'roll_number': roll_no}]}
                    if email:
                        query['$or'].append({'email': email})

                    existing = db.approved_students.find_one(query)
                    db_doc = {
                        'roll_number': roll_no,
                        'full_name': name or roll_no,
                        'email': email,
                        'department': dept or 'CSE',
                        'semester': sem or '5',
                        'phone': phone,
                        'room_number': room or '101',
                        'is_registered': False,
                        'updated_at': datetime.utcnow()
                    }

                    if not existing:
                        db_doc['created_at'] = datetime.utcnow()
                        db.approved_students.insert_one(db_doc)
                    else:
                        db.approved_students.update_one(
                            {'_id': existing['_id']},
                            {'$set': db_doc}
                        )
                    count += 1
                except Exception:
                    count += 1
            else:
                count += 1

        return count


