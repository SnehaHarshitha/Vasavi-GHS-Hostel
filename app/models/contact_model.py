from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class ContactModel:
    @staticmethod
    def save_message(name, email, phone, subject, message):
        db = get_db()
        if db is None:
            return None
        doc = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'status': 'Unread', # 'Unread', 'Read', 'Replied'
            'created_at': datetime.utcnow()
        }
        try:
            return db.contact_messages.insert_one(doc).inserted_id
        except Exception:
            return None

    @staticmethod
    def get_all_messages():
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.contact_messages.find().sort('created_at', -1))
        except Exception:
            return []

    @staticmethod
    def mark_as_read(msg_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.contact_messages.update_one(
                {'_id': to_oid(msg_id)},
                {'$set': {'status': 'Read'}}
            )
        except Exception:
            return None

    @staticmethod
    def count_unread():
        db = get_db()
        if db is None:
            return 0
        try:
            return db.contact_messages.count_documents({'status': 'Unread'})
        except Exception:
            return 0

