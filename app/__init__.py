import os
from flask import Flask
from config import config_by_name
from app.extensions import login_manager, init_mongo

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name.get('production', config_by_name['default']))
    app.config.from_object(config_class)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    login_manager.init_app(app)
    init_mongo(app)

    # Register Blueprints
    from app.routes.public_routes import public_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import student_bp
    from app.routes.warden_routes import warden_bp
    from app.routes.principal_routes import principal_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.mess_routes import mess_bp
    from app.routes.cleaning_routes import cleaning_bp
    from app.routes.complaint_routes import complaint_bp
    from app.routes.notification_routes import notification_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(warden_bp)
    app.register_blueprint(principal_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mess_bp)
    app.register_blueprint(cleaning_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(notification_bp)

    # Global context processors (e.g. unread notifications count)
    @app.context_processor
    def inject_global_vars():
        unread_count = 0
        try:
            from flask_login import current_user
            from app.models.notification_model import NotificationModel
            if current_user and current_user.is_authenticated:
                notifs = NotificationModel.get_user_notifications(current_user)
                unread_count = len([n for n in notifs if not n.get('is_read')])
        except Exception as e:
            app.logger.warning(f"Context processor notification fetch warning: {e}")
            unread_count = 0

        return dict(
            unread_notif_count=unread_count,
            current_year=2026,
            hostel_name="GHS Hostel",
            college_name="Sri Vasavi Engineering College"
        )

    @app.errorhandler(500)
    def handle_500_error(e):
        app.logger.error(f"Internal Server Error 500: {e}")
        return render_template('public/500.html', error=str(e)), 500

    return app
