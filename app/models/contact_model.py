from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class ContactModel:
    @staticmethod
    def save_message(name, email, phone, subject, message):
        db = get_db()
        doc = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message,
            'status': 'Unread', # 'Unread', 'Read', 'Replied'
            'created_at': datetime.utcnow()
        }
        return db.contact_messages.insert_one(doc).inserted_id

    @staticmethod
    def get_all_messages():
        db = get_db()
        return list(db.contact_messages.find().sort('created_at', -1))

    @staticmethod
    def mark_as_read(msg_id):
        db = get_db()
        return db.contact_messages.update_one(
            {'_id': ObjectId(msg_id)},
            {'$set': {'status': 'Read'}}
        )

    @staticmethod
    def count_unread():
        db = get_db()
        return db.contact_messages.count_documents({'status': 'Unread'})
