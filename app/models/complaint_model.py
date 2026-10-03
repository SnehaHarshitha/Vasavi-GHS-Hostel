from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class ComplaintModel:
    CATEGORIES = [
        'Food', 'Room cleaning', 'Water', 'Electricity',
        'Security', 'Maintenance', 'Health', 'Warden support', 'Other'
    ]

    PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']

    STATUSES = ['Submitted', 'Under Review', 'In Progress', 'Rectified', 'Closed', 'Reopened', 'Rejected']

    @staticmethod
    def rectify_complaint(complaint_id, rectification_message, rectified_by="Warden"):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        history_entry = {
            'status': 'Rectified',
            'action': 'Marked as Rectified',
            'message': rectification_message,
            'updated_by': rectified_by,
            'timestamp': now
        }
        try:
            return db.complaints.update_one(
                {'_id': to_oid(complaint_id)},
                {
                    '$set': {
                        'status': 'Rectified',
                        'rectification_message': rectification_message,
                        'rectified_by': rectified_by,
                        'rectified_at': now,
                        'updated_at': now
                    },
                    '$push': {'history': history_entry}
                }
            )
        except Exception:
            return None

    @staticmethod
    def record_student_feedback(complaint_id, feedback_action, student_name="Student"):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        if feedback_action == 'still_exists':
            new_status = 'Reopened'
            action_title = 'Problem Still Exists'
        else:
            new_status = 'Closed'
            action_title = 'Problem Resolved'

        history_entry = {
            'status': new_status,
            'action': action_title,
            'message': f"Student {student_name} selected '{action_title}'",
            'updated_by': student_name,
            'timestamp': now
        }

        try:
            return db.complaints.update_one(
                {'_id': to_oid(complaint_id)},
                {
                    '$set': {
                        'status': new_status,
                        'student_feedback': feedback_action,
                        'updated_at': now
                    },
                    '$push': {'history': history_entry}
                }
            )
        except Exception:
            return None

    @staticmethod
    def get_stats():
        db = get_db()
        if db is None:
            return {
                'total': 0, 'submitted': 0, 'in_progress': 0,
                'rectified': 0, 'resolved': 0, 'rejected': 0
            }
        try:
            total = db.complaints.count_documents({})
            submitted = db.complaints.count_documents({'status': 'Submitted'})
            in_progress = db.complaints.count_documents({'status': {'$in': ['In Progress', 'Under Review', 'Reopened']}})
            rectified = db.complaints.count_documents({'status': 'Rectified'})
            resolved = db.complaints.count_documents({'status': 'Closed'})
            rejected = db.complaints.count_documents({'status': 'Rejected'})
            return {
                'total': total,
                'submitted': submitted,
                'in_progress': in_progress,
                'rectified': rectified,
                'resolved': resolved,
                'rejected': rejected
            }
        except Exception:
            return {
                'total': 0, 'submitted': 0, 'in_progress': 0,
                'rectified': 0, 'resolved': 0, 'rejected': 0
            }

    @staticmethod
    def create_complaint(student_id, role_number, room_number, category, subject, description, priority='Medium', attachment='', anonymous=False):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        complaint = {
            'student_id': to_oid(student_id),
            'role_number': 'Anonymous' if anonymous else role_number,
            'room_number': room_number,
            'category': category,
            'subject': subject,
            'description': description,
            'priority': priority,
            'attachment': attachment,
            'anonymous': anonymous,
            'status': 'Submitted',
            'staff_reply': '',
            'rating': None,
            'feedback_comments': [],
            'created_at': now,
            'updated_at': now
        }
        try:
            return db.complaints.insert_one(complaint).inserted_id
        except Exception:
            return None

    @staticmethod
    def get_student_complaints(student_id):
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.complaints.find({'student_id': to_oid(student_id)}).sort('created_at', -1))
        except Exception:
            return []

    @staticmethod
    def get_all_complaints(category=None, priority=None, status=None, room_number=None):
        db = get_db()
        if db is None:
            return []
        query = {}
        if category:
            query['category'] = category
        if priority:
            query['priority'] = priority
        if status:
            query['status'] = status
        if room_number:
            query['room_number'] = room_number
        try:
            return list(db.complaints.find(query).sort('created_at', -1))
        except Exception:
            return []

    @staticmethod
    def find_by_id(complaint_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.complaints.find_one({'_id': to_oid(complaint_id)})
        except Exception:
            return None

    @staticmethod
    def update_status(complaint_id, status, staff_reply=""):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        update_doc = {
            'status': status,
            'updated_at': now
        }
        if staff_reply:
            update_doc['staff_reply'] = staff_reply

        try:
            return db.complaints.update_one(
                {'_id': to_oid(complaint_id)},
                {'$set': update_doc}
            )
        except Exception:
            return None

    @staticmethod
    def add_comment(complaint_id, author_role, author_name, comment_text):
        db = get_db()
        if db is None:
            return None
        now = datetime.utcnow()
        comment = {
            'author_role': author_role,
            'author_name': author_name,
            'comment_text': comment_text,
            'created_at': now
        }
        try:
            return db.complaints.update_one(
                {'_id': to_oid(complaint_id)},
                {
                    '$push': {'feedback_comments': comment},
                    '$set': {'updated_at': now}
                }
            )
        except Exception:
            return None

    @staticmethod
    def rate_complaint(complaint_id, rating):
        db = get_db()
        if db is None:
            return None
        try:
            return db.complaints.update_one(
                {'_id': to_oid(complaint_id)},
                {'$set': {'rating': int(rating), 'updated_at': datetime.utcnow()}}
            )
        except Exception:
            return None

