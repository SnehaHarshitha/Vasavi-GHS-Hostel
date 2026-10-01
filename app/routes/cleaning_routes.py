from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models.cleaning_model import CleaningModel

cleaning_bp = Blueprint('cleaning', __name__, url_prefix='/api/cleaning')

@cleaning_bp.route('/stats')
def get_cleaning_stats():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    stats = CleaningModel.get_daily_cleaning_stats(date_str)
    return jsonify(stats)
