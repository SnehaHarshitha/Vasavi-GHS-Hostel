from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class NotificationModel:
    @staticmethod
    def create_notification(title, message, target_type='all', target_users=None, created_by='System'):
        db = get_db()
        now = datetime.utcnow()
        doc = {
            'title': title,
            'message': message,
            'target_type': target_type, # 'all', 'room', 'floor', 'wardens', 'specific'
            'target_users': target_users or [], # list of role numbers or user IDs
            'read_by': [], # list of user IDs who have read
            'created_by': created_by,
            'created_at': now
        }
        return db.notifications.insert_one(doc).inserted_id

    @staticmethod
    def get_user_notifications(user):
        db = get_db()
        user_id = str(user.id)
        role_num = user.role_number
        room_num = user.room_number

        query = {
            '$or': [
                {'target_type': 'all'},
                {'target_type': 'wardens', 'target_users': {'$in': [user.role]}},
                {'target_type': 'specific', 'target_users': {'$in': [user_id, role_num]}},
                {'target_type': 'room', 'target_users': {'$in': [room_num]}}
            ]
        }
        notifications = list(db.notifications.find(query).sort('created_at', -1).limit(50))
        
        for n in notifications:
            n['is_read'] = user_id in [str(uid) for uid in n.get('read_by', [])]
            
        return notifications

    @staticmethod
    def mark_as_read(notification_id, user_id):
        db = get_db()
        return db.notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$addToSet': {'read_by': str(user_id)}}
        )

    @staticmethod
    def mark_all_as_read(user):
        db = get_db()
        notifications = NotificationModel.get_user_notifications(user)
        user_id = str(user.id)
        for n in notifications:
            db.notifications.update_one(
                {'_id': n['_id']},
                {'$addToSet': {'read_by': user_id}}
            )
        return True

    @staticmethod
    def count_unread(user):
        notifications = NotificationModel.get_user_notifications(user)
        return sum(1 for n in notifications if not n.get('is_read'))
