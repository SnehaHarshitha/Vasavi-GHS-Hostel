from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import login_required, current_user
import csv
import io
from app.models.user_model import UserModel
from app.models.room_model import RoomModel
from app.models.mess_model import MessModel
from app.models.cleaning_model import CleaningModel
from app.models.complaint_model import ComplaintModel
from app.models.notification_model import NotificationModel
from app.models.sick_leave_model import SickLeaveModel

warden_bp = Blueprint('warden', __name__, url_prefix='/warden')

def warden_only():
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin()):
        if request.method in ['POST', 'PUT', 'DELETE'] or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            abort(403)
        flash('Access restricted to Warden and Admin only.', 'danger')
        return False
    return True


@warden_bp.route('/dashboard')
@login_required
def dashboard():
    if not warden_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Stats
    pending_students = UserModel.count_students(status='pending')
    total_approved_students = UserModel.count_students(status='approved')
    room_stats = RoomModel.get_stats()
    food_stats = MessModel.get_daily_selection_counts(today_str)
    cleaning_stats = CleaningModel.get_daily_cleaning_stats(today_str)
    complaint_stats = ComplaintModel.get_stats()
    sick_leave_stats = SickLeaveModel.get_stats()

    # Recent items
    recent_complaints = ComplaintModel.get_all_complaints()[:5]
    pending_approvals = UserModel.get_all_by_role(role='student', status='pending')
    recent_sick_leaves = SickLeaveModel.get_all_requests()[:5]

    return render_template(
        'warden/dashboard.html',
        today_str=today_str,
        pending_students=pending_students,
        total_approved_students=total_approved_students,
        room_stats=room_stats,
        food_stats=food_stats,
        cleaning_stats=cleaning_stats,
        complaint_stats=complaint_stats,
        sick_leave_stats=sick_leave_stats,
        recent_complaints=recent_complaints,
        pending_approvals=pending_approvals,
        recent_sick_leaves=recent_sick_leaves
    )

@warden_bp.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    if not warden_only():
        return redirect(url_for('public.index'))

    status_filter = request.args.get('status', 'all')
    if status_filter == 'all':
        student_list = UserModel.get_all_by_role(role='student')
    else:
        student_list = UserModel.get_all_by_role(role='student', status=status_filter)

    rooms = RoomModel.get_all_rooms()
    return render_template(
        'warden/students.html',
        students=student_list,
        status_filter=status_filter,
        rooms=rooms
    )

@warden_bp.route('/students/action/<student_id>/<action>', methods=['POST'])
@login_required
def student_action(student_id, action):
    if not warden_only():
        return redirect(url_for('public.index'))

    student = UserModel.find_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('warden.students'))

    if action == 'approve':
        UserModel.update_user(student_id, {'status': 'approved'})
        NotificationModel.create_notification(
            title="Registration Approved",
            message=f"Hello {student.get('full_name')}, your hostel registration has been approved!",
            target_type="specific",
            target_users=[str(student['_id']), student.get('role_number')],
            created_by=current_user.full_name
        )
        flash(f"Registration for {student.get('full_name')} approved.", 'success')

    elif action == 'reject':
        UserModel.update_user(student_id, {'status': 'rejected'})
        flash(f"Registration for {student.get('full_name')} rejected.", 'warning')

    elif action == 'block':
        UserModel.update_user(student_id, {'status': 'blocked'})
        flash(f"Student {student.get('full_name')} blocked.", 'danger')

    elif action == 'unblock':
        UserModel.update_user(student_id, {'status': 'approved'})
        flash(f"Student {student.get('full_name')} unblocked.", 'success')

    elif action == 'assign_room':
        room_number = request.form.get('room_number', '').strip()
        if room_number:
            success, msg = RoomModel.assign_student(
                room_number=room_number,
                student_id=student_id,
                student_name=student.get('full_name'),
                role_number=student.get('role_number')
            )
            if success:
                UserModel.update_user(student_id, {'room_number': room_number})
                flash(f"Assigned {student.get('full_name')} to Room {room_number}.", 'success')
            else:
                flash(f"Room allocation failed: {msg}", 'danger')

    return redirect(url_for('warden.students'))

@warden_bp.route('/rooms', methods=['GET', 'POST'])
@login_required
def rooms():
    if not warden_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        room_number = request.form.get('room_number', '').strip()
        floor = request.form.get('floor', 'Floor 1').strip()
        capacity = int(request.form.get('capacity', 4))

        if RoomModel.find_by_room_number(room_number):
            flash('Room number already exists.', 'danger')
        else:
            RoomModel.create_room({
                'room_number': room_number,
                'floor': floor,
                'capacity': capacity
            })
            flash(f'Room {room_number} created successfully.', 'success')
        return redirect(url_for('warden.rooms'))

    all_rooms = RoomModel.get_all_rooms()
    return render_template('warden/rooms.html', rooms=all_rooms)

@warden_bp.route('/mess-management', methods=['GET', 'POST'])
@login_required
def mess_management():
    if not warden_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        day = request.form.get('day')
        meal_type = request.form.get('meal_type')
        menu_items = request.form.get('menu_items', '').strip()
        special_note = request.form.get('special_note', '').strip()
        is_special = bool(request.form.get('is_special_day'))

        if day and meal_type and menu_items:
            MessModel.set_menu_item(day, meal_type, menu_items, is_special_day=is_special, special_note=special_note)
            
            # Broadcast notification
            NotificationModel.create_notification(
                title=f"Mess Menu Updated ({day})",
                message=f"The mess menu for {day} ({meal_type.title()}) has been updated: {menu_items}",
                target_type="all",
                created_by=current_user.full_name
            )
            flash(f"Menu for {day} ({meal_type.title()}) updated successfully!", 'success')
            return redirect(url_for('warden.mess_management'))

    timetable, notes, is_choice_day = MessModel.get_weekly_timetable()
    today_str = datetime.now().strftime('%Y-%m-%d')
    food_counts = MessModel.get_daily_selection_counts(today_str)

    return render_template(
        'warden/mess_mgmt.html',
        timetable=timetable,
        notes=notes,
        is_choice_day=is_choice_day,
        today_str=today_str,
        food_counts=food_counts
    )

@warden_bp.route('/cleaning-management', methods=['GET', 'POST'])
@login_required
def cleaning_management():
    if not warden_only():
        return redirect(url_for('public.index'))

    today_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    if request.method == 'POST':
        room_number = request.form.get('room_number')
        status = request.form.get('status')
        cleaned_by = request.form.get('cleaned_by', 'Cleaning Staff').strip()
        remarks = request.form.get('remarks', '').strip()

        if room_number and status:
            CleaningModel.record_cleaning(room_number, today_str, status, cleaned_by, remarks)
            flash(f"Cleaning record for Room {room_number} set to {status}.", 'success')
            return redirect(url_for('warden.cleaning_management', date=today_str))

    all_rooms = RoomModel.get_all_rooms()
    cleaning_records = {r.get('room_number'): r for r in CleaningModel.get_cleaning_by_date(today_str)}
    stats = CleaningModel.get_daily_cleaning_stats(today_str)

    return render_template(
        'warden/cleaning_mgmt.html',
        today_str=today_str,
        rooms=all_rooms,
        cleaning_records=cleaning_records,
        stats=stats
    )

@warden_bp.route('/cleaning/checkbook/save', methods=['POST'])
@login_required
def save_cleaning_checkbook():
    if not warden_only():
        return redirect(url_for('public.index'))

    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    room_number = request.form.get('room_number', '').strip()
    room_cleaned = bool(request.form.get('room_cleaned'))
    bathroom_cleaned = bool(request.form.get('bathroom_cleaned'))
    floor_cleaned = bool(request.form.get('floor_cleaned'))
    waste_removed = bool(request.form.get('waste_removed'))
    phenyl_kept = bool(request.form.get('phenyl_kept'))
    cleaned_by = request.form.get('cleaned_by', 'Housekeeping Staff').strip()
    checked_by = request.form.get('checked_by', current_user.full_name).strip()
    check_time = request.form.get('check_time', datetime.now().strftime('%I:%M %p')).strip()
    remarks = request.form.get('remarks', '').strip()

    if not room_number:
        flash('Room number is required.', 'danger')
        return redirect(url_for('warden.cleaning_management', date=date_str))

    CleaningModel.save_checkbook(
        room_number=room_number,
        date_str=date_str,
        room_cleaned=room_cleaned,
        bathroom_cleaned=bathroom_cleaned,
        floor_cleaned=floor_cleaned,
        waste_removed=waste_removed,
        phenyl_kept=phenyl_kept,
        cleaned_by=cleaned_by,
        checked_by=checked_by,
        remarks=remarks,
        check_time=check_time
    )

    flash("Daily Cleaning Checkbook Updated Successfully!", "swal_success")
    return redirect(url_for('warden.cleaning_management', date=date_str))

@warden_bp.route('/sunday-tasks', methods=['GET', 'POST'])
@login_required
def sunday_tasks():
    if not warden_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        task_name = request.form.get('task_name', 'Sunday Room Phenyl Cleaning').strip()
        date_str = request.form.get('date', '').strip()
        rooms_or_floor = request.form.get('rooms_or_floor', 'All Floors').strip()
        assigned_staff = request.form.get('assigned_staff', 'Housekeeping Team').strip()
        instructions = request.form.get('instructions', '').strip()

        if date_str:
            CleaningModel.create_sunday_task(task_name, date_str, rooms_or_floor, assigned_staff, instructions)
            
            # Notify students
            NotificationModel.create_notification(
                title=f"Schedule: {task_name}",
                message=f"A task '{task_name}' is scheduled for {date_str} for {rooms_or_floor}. Instructions: {instructions}",
                target_type="all",
                created_by=current_user.full_name
            )
            flash(f"Task '{task_name}' created for {date_str}.", 'success')
            return redirect(url_for('warden.sunday_tasks'))

    tasks = CleaningModel.get_all_sunday_tasks()
    return render_template('warden/sunday_tasks.html', tasks=tasks)

@warden_bp.route('/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    if not warden_only():
        return redirect(url_for('public.index'))

    category = request.args.get('category')
    priority = request.args.get('priority')
    status = request.args.get('status')

    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')
        new_status = request.form.get('status')
        reply = request.form.get('staff_reply', '').strip()

        if complaint_id and new_status:
            ComplaintModel.update_status(complaint_id, new_status, reply)
            
            c = ComplaintModel.find_by_id(complaint_id)
            if c and not c.get('anonymous'):
                NotificationModel.create_notification(
                    title=f"Complaint Status Update ({new_status})",
                    message=f"Your complaint on '{c.get('category')}' is now {new_status}. Reply: {reply}",
                    target_type="specific",
                    target_users=[str(c.get('student_id')), c.get('role_number')],
                    created_by=current_user.full_name
                )
            flash(f"Complaint status updated to {new_status}.", 'success')
            return redirect(url_for('warden.complaints'))

    complaint_list = ComplaintModel.get_all_complaints(category=category, priority=priority, status=status)
    return render_template(
        'warden/complaints.html',
        complaints=complaint_list,
        categories=ComplaintModel.CATEGORIES,
        priorities=ComplaintModel.PRIORITIES,
        statuses=ComplaintModel.STATUSES,
        sel_cat=category,
        sel_prio=priority,
        sel_stat=status
    )

@warden_bp.route('/complaints/rectify/<complaint_id>', methods=['POST'])
@login_required
def rectify_complaint(complaint_id):
    if not warden_only():
        return redirect(url_for('public.index'))

    rectification_message = request.form.get('rectification_message', '').strip()
    if not rectification_message:
        flash('Please provide rectification details/message.', 'warning')
        return redirect(url_for('warden.complaints'))

    ComplaintModel.rectify_complaint(
        complaint_id=complaint_id,
        rectification_message=rectification_message,
        rectified_by=current_user.full_name
    )

    c = ComplaintModel.find_by_id(complaint_id)
    if c and not c.get('anonymous'):
        NotificationModel.create_notification(
            title="Complaint Rectified",
            message="Your reported problem has been rectified. Please review the update.",
            target_type="specific",
            target_users=[str(c.get('student_id')), c.get('role_number')],
            created_by=current_user.full_name
        )

    flash("Complaint Rectified Successfully!", "swal_success")
    return redirect(url_for('warden.complaints'))

@warden_bp.route('/export-food-selection')
@login_required
def export_food_selection():
    if not warden_only():
        return redirect(url_for('public.index'))

    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selections = MessModel.get_selections_by_date(date_str)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Role Number', 'Date', 'Food Choice', 'Status', 'Updated At'])
    
    for s in selections:
        writer.writerow([
            s.get('role_number', ''),
            s.get('date', ''),
            s.get('food_choice', '').upper(),
            s.get('selection_status', ''),
            s.get('updated_at', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=food_selection_{date_str}.csv"}
    )

@warden_bp.route('/sick-leaves', methods=['GET', 'POST'])
@login_required
def sick_leaves():
    if not warden_only():
        return redirect(url_for('public.index'))

    status_filter = request.args.get('status', 'all')

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        new_status = request.form.get('status')
        remarks = request.form.get('warden_remarks', '').strip()

        if request_id and new_status:
            SickLeaveModel.update_status(request_id, new_status, remarks, reviewer_role="Warden")
            leave = SickLeaveModel.find_by_id(request_id)
            if leave:
                NotificationModel.create_notification(
                    title=f"Sick Leave Request {new_status}",
                    message=f"Your Sick Leave Request ({leave.get('reason')}) has been updated to: {new_status}. Remarks: {remarks}",
                    target_type="specific",
                    target_users=[str(leave.get('student_id')), leave.get('role_number')],
                    created_by=current_user.full_name
                )
            flash(f"Sick Leave status updated to '{new_status}'.", 'success')
            return redirect(url_for('warden.sick_leaves', status=status_filter))

    leave_list = SickLeaveModel.get_all_requests(status=status_filter)
    stats = SickLeaveModel.get_stats()

    return render_template(
        'warden/sick_leaves.html',
        leave_list=leave_list,
        stats=stats,
        status_filter=status_filter,
        statuses=SickLeaveModel.STATUSES
    )
