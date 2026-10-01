from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.mess_model import MessModel

mess_bp = Blueprint('mess', __name__, url_prefix='/api/mess')

@mess_bp.route('/counts')
def get_food_counts():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    counts = MessModel.get_daily_selection_counts(date_str)
    return jsonify(counts)

@mess_bp.route('/select', methods=['POST'])
@login_required
def select_food_api():
    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    choice = request.form.get('choice')

    if choice not in ['egg', 'veg']:
        return jsonify({'success': False, 'message': 'Invalid choice'}), 400

    MessModel.save_food_selection(current_user.id, current_user.role_number, date_str, choice)
    return jsonify({'success': True, 'message': f'Saved choice as {choice.upper()}'})
