from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class NotificationModel:
    @staticmethod
    def create_notification(title, message, target_type='all', target_users=None, created_by='System'):
        db = get_db()
        if db is None:
            return None
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
        try:
            return db.notifications.insert_one(doc).inserted_id
        except Exception:
            return None

    @staticmethod
    def get_user_notifications(user):
        db = get_db()
        if db is None or not user:
            return []
        try:
            user_id = str(user.id)
            role_num = getattr(user, 'role_number', '')
            room_num = getattr(user, 'room_number', '')

            query = {
                '$or': [
                    {'target_type': 'all'},
                    {'target_type': 'wardens', 'target_users': {'$in': [getattr(user, 'role', '')]}},
                    {'target_type': 'specific', 'target_users': {'$in': [user_id, role_num]}},
                    {'target_type': 'room', 'target_users': {'$in': [room_num]}}
                ]
            }
            notifications = list(db.notifications.find(query).sort('created_at', -1).limit(50))
            
            for n in notifications:
                n['is_read'] = user_id in [str(uid) for uid in n.get('read_by', [])]
                
            return notifications
        except Exception:
            return []

    @staticmethod
    def mark_as_read(notification_id, user_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.notifications.update_one(
                {'_id': to_oid(notification_id)},
                {'$addToSet': {'read_by': str(user_id)}}
            )
        except Exception:
            return None

    @staticmethod
    def mark_all_as_read(user):
        db = get_db()
        if db is None:
            return True
        notifications = NotificationModel.get_user_notifications(user)
        user_id = str(user.id)
        for n in notifications:
            try:
                db.notifications.update_one(
                    {'_id': to_oid(n['_id'])},
                    {'$addToSet': {'read_by': user_id}}
                )
            except Exception:
                pass
        return True

    @staticmethod
    def count_unread(user):
        notifications = NotificationModel.get_user_notifications(user)
        return sum(1 for n in notifications if not n.get('is_read'))
