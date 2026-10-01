from flask import Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.complaint_model import ComplaintModel

complaint_bp = Blueprint('complaint_api', __name__, url_prefix='/api/complaint')

@complaint_bp.route('/rate/<complaint_id>', methods=['POST'])
@login_required
def rate_complaint(complaint_id):
    rating = request.form.get('rating')
    if rating:
        ComplaintModel.rate_complaint(complaint_id, rating)
        flash('Thank you for rating the resolution!', 'success')
    return redirect(url_for('student.complaints'))

@complaint_bp.route('/comment/<complaint_id>', methods=['POST'])
@login_required
def add_comment(complaint_id):
    comment_text = request.form.get('comment_text', '').strip()
    if comment_text:
        ComplaintModel.add_comment(
            complaint_id=complaint_id,
            author_role=current_user.role,
            author_name=current_user.full_name,
            comment_text=comment_text
        )
        flash('Comment added.', 'success')
        
    if current_user.is_student():
        return redirect(url_for('student.complaints'))
    else:
        return redirect(url_for('warden.complaints'))
