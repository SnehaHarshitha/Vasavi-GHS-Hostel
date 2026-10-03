import random
import string
from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class SickLeaveModel:
    LEAVE_TYPES = [
        'Sick Leave',
        'Emergency Leave',
        'Personal Leave',
        'Family Function',
        'Other'
    ]

    REASONS = [
        'Fever / Flu',
        'Stomach Ache / Food Poisoning',
        'Severe Headache / Migraine',
        'Injury / Body Ache',
        'Viral / Infectious Illness',
        'Medical Doctor Advice',
        'Personal / Family Matter',
        'Other Illness'
    ]

    STATUSES = ['Pending', 'Submitted', 'Approved', 'Approved by Warden', 'Approved by Principal', 'Rejected', 'Completed']

    @staticmethod
    def generate_leave_id():
        date_part = datetime.utcnow().strftime('%Y%m%d')
        rand_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"LV-{date_part}-{rand_part}"

    @staticmethod
    def create_request(student_id, student_name, role_number, room_number, start_date, end_date, reason, leave_type="Sick Leave", department="CSE", semester="5", parent_name="", parent_phone="", address_during_leave="", remarks="", symptoms="", request_sick_diet=False, staying_in_hostel=True, supporting_document=""):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        leave_id = SickLeaveModel.generate_leave_id()

        doc = {
            'leave_id': leave_id,
            'student_id': to_oid(student_id),
            'student_name': student_name,
            'role_number': role_number,
            'room_number': room_number or '101',
            'department': department,
            'semester': str(semester),
            'leave_type': leave_type,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'parent_name': parent_name,
            'parent_phone': parent_phone,
            'address_during_leave': address_during_leave,
            'remarks': remarks,
            'symptoms': symptoms,
            'supporting_document': supporting_document,
            'request_sick_diet': bool(request_sick_diet),
            'staying_in_hostel': bool(staying_in_hostel),
            'status': 'Pending',
            'warden_remarks': '',
            'principal_remarks': '',
            'created_at': now,
            'updated_at': now
        }
        try:
            db.sick_leaves.insert_one(doc)
            return leave_id
        except Exception:
            return leave_id

    @staticmethod
    def get_student_requests(student_id):
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.sick_leaves.find({'student_id': to_oid(student_id)}).sort('created_at', -1))
        except Exception:
            try:
                return list(db.sick_leaves.find({'role_number': student_id}).sort('created_at', -1))
            except Exception:
                return []

    @staticmethod
    def get_active_student_request(student_id, today_str):
        db = get_db()
        if db is None:
            return None
        requests = SickLeaveModel.get_student_requests(student_id)
        for r in requests:
            if r.get('start_date') <= today_str <= r.get('end_date') or r.get('status') == 'Pending':
                return r
        return requests[0] if requests else None

    @staticmethod
    def get_all_requests(status=None, leave_type=None, date_str=None, department=None, room_number=None, search_q=None):
        db = get_db()
        if db is None:
            return []

        query = {}
        if status and status != 'all':
            if status in ['Submitted', 'Pending']:
                query['status'] = {'$in': ['Submitted', 'Pending']}
            elif status in ['Approved', 'Approved by Warden', 'Approved by Principal']:
                query['status'] = {'$in': ['Approved', 'Approved by Warden', 'Approved by Principal']}
            else:
                query['status'] = status

        if leave_type and leave_type != 'all':
            query['leave_type'] = leave_type

        if department:
            query['department'] = department

        if room_number:
            query['room_number'] = room_number

        if date_str:
            query['$and'] = [
                {'start_date': {'$lte': date_str}},
                {'end_date': {'$gte': date_str}}
            ]

        records = list(db.sick_leaves.find(query).sort('created_at', -1))

        if search_q:
            sq = search_q.lower()
            records = [r for r in records if sq in str(r.get('student_name', '')).lower() or sq in str(r.get('role_number', '')).lower() or sq in str(r.get('leave_id', '')).lower()]

        return records

    @staticmethod
    def get_sick_leave_records(status=None, date_str=None):
        return SickLeaveModel.get_all_requests(status=status, leave_type='Sick Leave', date_str=date_str)

    @staticmethod
    def find_by_id(request_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.sick_leaves.find_one({'_id': to_oid(request_id)})
        except Exception:
            try:
                return db.sick_leaves.find_one({'leave_id': request_id})
            except Exception:
                return None

    @staticmethod
    def update_status(request_id, status, remarks="", reviewer_role="Warden", reviewer_name="Warden"):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        update_doc = {
            'status': status,
            'updated_at': now,
            'updated_by': reviewer_name
        }
        if reviewer_role.lower() == 'principal':
            update_doc['principal_remarks'] = remarks
        else:
            update_doc['warden_remarks'] = remarks

        try:
            return db.sick_leaves.update_one({'_id': to_oid(request_id)}, {'$set': update_doc})
        except Exception:
            try:
                return db.sick_leaves.update_one({'leave_id': request_id}, {'$set': update_doc})
            except Exception:
                return None

    @staticmethod
    def get_stats():
        db = get_db()
        if db is None:
            return {'total': 0, 'pending': 0, 'submitted': 0, 'approved': 0, 'rejected': 0, 'sick_total': 0, 'currently_on_sick': 0}

        try:
            today_str = datetime.utcnow().strftime('%Y-%m-%d')
            total = db.sick_leaves.count_documents({})
            pending = db.sick_leaves.count_documents({'status': {'$in': ['Pending', 'Submitted']}})
            approved = db.sick_leaves.count_documents({'status': {'$in': ['Approved', 'Approved by Warden', 'Approved by Principal']}})
            rejected = db.sick_leaves.count_documents({'status': 'Rejected'})

            sick_total = db.sick_leaves.count_documents({'leave_type': 'Sick Leave'})
            currently_on_sick = db.sick_leaves.count_documents({
                'leave_type': 'Sick Leave',
                'status': {'$in': ['Approved', 'Approved by Warden', 'Approved by Principal']},
                'start_date': {'$lte': today_str},
                'end_date': {'$gte': today_str}
            })

            return {
                'total': total,
                'pending': pending,
                'submitted': pending,
                'approved': approved,
                'rejected': rejected,
                'sick_total': sick_total,
                'currently_on_sick': currently_on_sick
            }
        except Exception:
            return {'total': 0, 'pending': 0, 'submitted': 0, 'approved': 0, 'rejected': 0, 'sick_total': 0, 'currently_on_sick': 0}
