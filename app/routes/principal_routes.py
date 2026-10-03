from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user_model import UserModel
from app.models.room_model import RoomModel
from app.models.mess_model import MessModel
from app.models.cleaning_model import CleaningModel
from app.models.complaint_model import ComplaintModel
from app.models.sick_leave_model import SickLeaveModel
from app.models.notification_model import NotificationModel

principal_bp = Blueprint('principal', __name__, url_prefix='/principal')

def principal_or_admin_only():
    if not current_user.is_authenticated or (not current_user.is_principal() and not current_user.is_admin()):
        flash('Access restricted to Principal and Admin portal.', 'danger')
        return False
    return True

@principal_bp.route('/dashboard')
@login_required
def dashboard():
    if not principal_or_admin_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        total_students = UserModel.count_students()
        approved_students = UserModel.count_students(status='approved')
        pending_registrations = UserModel.count_students(status='pending')
    except Exception:
        total_students, approved_students, pending_registrations = 0, 0, 0

    try:
        room_stats = RoomModel.get_stats() or {}
    except Exception:
        room_stats = {'total_rooms': 0, 'occupied_rooms': 0, 'available_rooms': 0}

    try:
        food_stats = MessModel.get_daily_selection_counts(today_str) or {}
    except Exception:
        food_stats = {'date': today_str, 'egg_count': 0, 'veg_count': 0, 'total_selected': 0, 'total_students': 0, 'pending_count': 0}

    try:
        cleaning_stats = CleaningModel.get_daily_cleaning_stats(today_str) or {}
    except Exception:
        cleaning_stats = {'date': today_str, 'completed': 0, 'pending': 0, 'total_rooms': 0}

    try:
        complaint_stats = ComplaintModel.get_stats() or {}
    except Exception:
        complaint_stats = {'total': 0, 'submitted': 0, 'pending': 0, 'in_progress': 0, 'rectified': 0, 'resolved': 0, 'rejected': 0}

    try:
        sick_leave_stats = SickLeaveModel.get_stats() or {}
    except Exception:
        sick_leave_stats = {'total': 0, 'pending': 0, 'submitted': 0, 'approved': 0, 'rejected': 0, 'sick_total': 0, 'currently_on_sick': 0}

    resolved_count = complaint_stats.get('resolved', 0) if isinstance(complaint_stats, dict) else 0
    total_complaints = complaint_stats.get('total', 0) if isinstance(complaint_stats, dict) else 0
    resolution_rate = round((resolved_count / total_complaints * 100), 1) if total_complaints > 0 else 100.0

    try:
        recent_complaints = ComplaintModel.get_all_complaints()[:8]
    except Exception:
        recent_complaints = []

    try:
        sunday_tasks = CleaningModel.get_all_sunday_tasks()[:5]
    except Exception:
        sunday_tasks = []

    try:
        recent_sick_leaves = SickLeaveModel.get_all_requests()[:5]
    except Exception:
        recent_sick_leaves = []

    try:
        all_rooms = RoomModel.get_all_rooms()
    except Exception:
        all_rooms = []

    try:
        cleaning_records = {r.get('room_number'): r for r in CleaningModel.get_cleaning_by_date(today_str)}
    except Exception:
        cleaning_records = {}

    return render_template(
        'principal/dashboard.html',
        today_str=today_str,
        total_students=total_students,
        approved_students=approved_students,
        pending_registrations=pending_registrations,
        room_stats=room_stats,
        food_stats=food_stats,
        cleaning_stats=cleaning_stats,
        complaint_stats=complaint_stats,
        sick_leave_stats=sick_leave_stats,
        resolution_rate=resolution_rate,
        recent_complaints=recent_complaints,
        sunday_tasks=sunday_tasks,
        recent_sick_leaves=recent_sick_leaves,
        rooms=all_rooms,
        cleaning_records=cleaning_records
    )

@principal_bp.route('/executive-reports')
@login_required
def executive_reports():
    if not principal_or_admin_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    student_list = UserModel.get_all_by_role(role='student')
    room_list = RoomModel.get_all_rooms()
    complaints = ComplaintModel.get_all_complaints()
    food_counts = MessModel.get_daily_selection_counts(today_str)
    sick_leaves = SickLeaveModel.get_all_requests()

    return render_template(
        'principal/executive_reports.html',
        today_str=today_str,
        students=student_list,
        rooms=room_list,
        complaints=complaints,
        food_counts=food_counts,
        sick_leaves=sick_leaves
    )

@principal_bp.route('/sick-leaves', methods=['GET', 'POST'])
@login_required
def sick_leaves():
    if not principal_or_admin_only():
        return redirect(url_for('public.index'))

    status_filter = request.args.get('status', 'all')
    leave_type_filter = request.args.get('leave_type', 'all')
    filter_dept = request.args.get('dept', '')
    search_q = request.args.get('search', '').strip().lower()

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        new_status = request.form.get('status')
        remarks = request.form.get('principal_remarks', '').strip()

        if request_id and new_status:
            SickLeaveModel.update_status(request_id, new_status, remarks, reviewer_role="Principal", reviewer_name=current_user.full_name)
            leave = SickLeaveModel.find_by_id(request_id)
            if leave:
                l_type = leave.get('leave_type', 'Sick Leave')
                s_date = leave.get('start_date', '')
                e_date = leave.get('end_date', '')
                notif_msg = f"Your {l_type} Application from {s_date} to {e_date} has been updated to '{new_status}' by Principal."
                if remarks:
                    notif_msg += f" Remarks: {remarks}"
                
                NotificationModel.create_notification(
                    title=f"Principal Review: {l_type} ({new_status})",
                    message=notif_msg,
                    target_type="specific",
                    target_users=[str(leave.get('student_id')), leave.get('role_number')],
                    created_by=current_user.full_name
                )
            flash(f"Leave Application status updated to '{new_status}' with Principal remarks.", 'swal_success')
            return redirect(url_for('principal.sick_leaves', status=status_filter, leave_type=leave_type_filter))

    leave_list = SickLeaveModel.get_all_requests(status=status_filter, leave_type=leave_type_filter, department=filter_dept, search_q=search_q)
    sick_leave_records = SickLeaveModel.get_sick_leave_records()
    stats = SickLeaveModel.get_stats()

    return render_template(
        'principal/sick_leaves.html',
        leave_list=leave_list,
        sick_leave_records=sick_leave_records,
        stats=stats,
        status_filter=status_filter,
        leave_type_filter=leave_type_filter,
        filter_dept=filter_dept,
        search_q=search_q,
        show_sick_only=(leave_type_filter == 'Sick Leave'),
        statuses=SickLeaveModel.STATUSES
    )

@principal_bp.route('/cleaning-management')
@login_required
def cleaning_management():
    if not principal_or_admin_only():
        return redirect(url_for('public.index'))
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    return redirect(url_for('warden.cleaning_management', date=date_str))
