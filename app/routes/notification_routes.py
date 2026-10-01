from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models.notification_model import NotificationModel

notification_bp = Blueprint('notification_api', __name__, url_prefix='/api/notifications')

@notification_bp.route('/unread-count')
@login_required
def unread_count():
    notifications = NotificationModel.get_user_notifications(current_user)
    unread = [n for n in notifications if not n.get('is_read')]
    return jsonify({'unread_count': len(unread)})

@notification_bp.route('/read/<notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    NotificationModel.mark_as_read(notif_id, current_user.id)
    return jsonify({'success': True})

@notification_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    NotificationModel.mark_all_as_read(current_user)
    return jsonify({'success': True})
