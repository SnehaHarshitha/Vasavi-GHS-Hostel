from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class SickLeaveModel:
    REASONS = [
        'Fever / Flu',
        'Stomach Ache / Food Poisoning',
        'Severe Headache / Migraine',
        'Injury / Body Ache',
        'Viral / Infectious Illness',
        'Medical Doctor Advice',
        'Other Illness'
    ]

    STATUSES = ['Submitted', 'Approved by Warden', 'Approved by Principal', 'Rejected']

    @staticmethod
    def create_request(student_id, student_name, role_number, room_number, start_date, end_date, reason, symptoms="", request_sick_diet=False, staying_in_hostel=True):
        db = get_db()
        now = datetime.utcnow()
        doc = {
            'student_id': ObjectId(student_id),
            'student_name': student_name,
            'role_number': role_number,
            'room_number': room_number,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'symptoms': symptoms,
            'request_sick_diet': bool(request_sick_diet),
            'staying_in_hostel': bool(staying_in_hostel),
            'status': 'Submitted',
            'warden_remarks': '',
            'principal_remarks': '',
            'created_at': now,
            'updated_at': now
        }
        return db.sick_leaves.insert_one(doc).inserted_id

    @staticmethod
    def get_student_requests(student_id):
        db = get_db()
        return list(db.sick_leaves.find({'student_id': ObjectId(student_id)}).sort('created_at', -1))

    @staticmethod
    def get_active_student_request(student_id, today_str):
        db = get_db()
        # Find any request where start_date <= today_str <= end_date or created recently
        requests = list(db.sick_leaves.find({'student_id': ObjectId(student_id)}).sort('created_at', -1))
        for r in requests:
            if r.get('start_date') <= today_str <= r.get('end_date') or r.get('status') == 'Submitted':
                return r
        return requests[0] if requests else None

    @staticmethod
    def get_all_requests(status=None, date_str=None):
        db = get_db()
        query = {}
        if status and status != 'all':
            query['status'] = status
        if date_str:
            query['$and'] = [
                {'start_date': {'$lte': date_str}},
                {'end_date': {'$gte': date_str}}
            ]
        return list(db.sick_leaves.find(query).sort('created_at', -1))

    @staticmethod
    def find_by_id(request_id):
        db = get_db()
        try:
            return db.sick_leaves.find_one({'_id': ObjectId(request_id)})
        except Exception:
            return None

    @staticmethod
    def update_status(request_id, status, remarks="", reviewer_role="Warden"):
        db = get_db()
        now = datetime.utcnow()
        update_doc = {
            'status': status,
            'updated_at': now
        }
        if reviewer_role.lower() == 'principal':
            update_doc['principal_remarks'] = remarks
        else:
            update_doc['warden_remarks'] = remarks

        return db.sick_leaves.update_one(
            {'_id': ObjectId(request_id)},
            {'$set': update_doc}
        )

    @staticmethod
    def get_stats():
        db = get_db()
        total = db.sick_leaves.count_documents({})
        submitted = db.sick_leaves.count_documents({'status': 'Submitted'})
        approved_warden = db.sick_leaves.count_documents({'status': 'Approved by Warden'})
        approved_principal = db.sick_leaves.count_documents({'status': 'Approved by Principal'})
        rejected = db.sick_leaves.count_documents({'status': 'Rejected'})
        return {
            'total': total,
            'submitted': submitted,
            'approved_warden': approved_warden,
            'approved_principal': approved_principal,
            'approved_total': approved_warden + approved_principal,
            'rejected': rejected
        }
