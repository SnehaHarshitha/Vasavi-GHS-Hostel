from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user_model import UserModel
from app.models.mess_model import MessModel
from app.models.cleaning_model import CleaningModel
from app.models.complaint_model import ComplaintModel
from app.models.notification_model import NotificationModel
from app.models.sick_leave_model import SickLeaveModel
from app.models.lms_model import LMSModel

student_bp = Blueprint('student', __name__, url_prefix='/student')

def student_only():
    if not current_user.is_authenticated or not current_user.is_student():
        flash('Access restricted to Students only.', 'danger')
        return False
    return True

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if not student_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    day_name = datetime.now().strftime('%A')

    # Get mess info for today
    timetable, notes, _, _ = MessModel.get_weekly_timetable()
    today_menu = timetable.get(day_name, {})

    # Food choice selection status
    food_choice = MessModel.get_student_selection(current_user.id, today_str)

    # Cleaning status
    cleaning_record = CleaningModel.get_room_cleaning(current_user.room_number, today_str)

    # Latest Sunday task
    sunday_task = CleaningModel.get_latest_sunday_task()

    # Complaints
    complaints = ComplaintModel.get_student_complaints(current_user.id)
    pending_complaints = [c for c in complaints if c.get('status') in ['Submitted', 'Seen', 'In Progress']]

    # Sick Leaves
    active_sick_leave = SickLeaveModel.get_active_student_request(current_user.id, today_str)

    # Notifications
    notifications = NotificationModel.get_user_notifications(current_user)
    unread_notifications = [n for n in notifications if not n.get('is_read')]

    return render_template(
        'student/dashboard.html',
        today_str=today_str,
        day_name=day_name,
        today_menu=today_menu,
        food_choice=food_choice,
        cleaning_record=cleaning_record,
        sunday_task=sunday_task,
        pending_complaints_count=len(pending_complaints),
        active_sick_leave=active_sick_leave,
        unread_notifications_count=len(unread_notifications),
        recent_notifications=notifications[:5]
    )

@student_bp.route('/food-selection', methods=['GET', 'POST'])
@login_required
def food_selection():
    if not student_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    day_name = datetime.now().strftime('%A')
    is_applicable_day = day_name in ['Thursday', 'Friday']

    if request.method == 'POST':
        if not is_applicable_day:
            flash('Food selection is only available on Thursdays and Fridays.', 'warning')
            return redirect(url_for('student.food_selection'))

        choice = request.form.get('food_choice')
        if choice in ['egg', 'veg']:
            MessModel.save_food_selection(current_user.id, current_user.role_number, today_str, choice)
            flash(f'Your choice ({choice.upper()}) has been saved for {today_str}.', 'success')
        else:
            flash('Invalid food option selected.', 'danger')

        return redirect(url_for('student.food_selection'))

    today_choice = MessModel.get_student_selection(current_user.id, today_str)
    history = MessModel.get_student_selection_history(current_user.id)

    return render_template(
        'student/food_selection.html',
        today_str=today_str,
        day_name=day_name,
        is_applicable_day=is_applicable_day,
        today_choice=today_choice,
        history=history
    )

@student_bp.route('/cleaning-status', methods=['GET', 'POST'])
@login_required
def cleaning_status():
    if not student_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    room_no = current_user.room_number or '101'

    if request.method == 'POST':
        category = request.form.get('category', 'Room Not Cleaned').strip()
        description = request.form.get('description', '').strip()

        # Photo upload if provided
        attachment = ""
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"clean_{current_user.role_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'cleaning')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                attachment = f"/static/uploads/cleaning/{filename}"

        if description:
            ComplaintModel.create_complaint(
                student_id=current_user.id,
                role_number=current_user.role_number,
                room_number=room_no,
                category='Room cleaning',
                subject=f"Cleaning Issue: {category}",
                description=description,
                priority='High',
                attachment=attachment
            )
            # Update room cleaning status to 'Problem Reported'
            db = get_db()
            if db is not None:
                db.cleaning_records.update_one(
                    {'room_number': room_no, 'date': today_str},
                    {'$set': {'status': 'Problem Reported', 'remarks': f"Problem Reported: {description}"}},
                    upsert=True
                )

            # Notify Warden
            NotificationModel.create_notification(
                title="Cleaning Complaint Submitted",
                message=f"Student {current_user.full_name} (Room {room_no}) submitted a cleaning complaint: {description}",
                target_type="warden",
                created_by=current_user.full_name
            )

            flash("Your Cleaning Complaint Has Been Submitted Successfully!", "swal_success")
            return redirect(url_for('student.cleaning_status'))
        else:
            flash("Please enter a description for the cleaning complaint.", "danger")

    today_record = CleaningModel.get_room_cleaning(room_no, today_str)
    history = CleaningModel.get_room_cleaning_history(room_no)
    sunday_tasks = CleaningModel.get_all_sunday_tasks()

    db = get_db()
    cleaning_complaints = []
    if db is not None:
        cleaning_complaints = list(db.complaints.find({
            'role_number': current_user.role_number,
            'category': 'Room cleaning'
        }).sort('created_at', -1))

    return render_template(
        'student/cleaning.html',
        today_str=today_str,
        today_record=today_record,
        history=history,
        sunday_tasks=sunday_tasks,
        cleaning_complaints=cleaning_complaints
    )

@student_bp.route('/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    if not student_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        category = request.form.get('category')
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'Medium')
        anonymous = bool(request.form.get('anonymous'))

        if category and subject and description:
            ComplaintModel.create_complaint(
                student_id=current_user.id,
                role_number=current_user.role_number,
                room_number=current_user.room_number,
                category=category,
                subject=subject,
                description=description,
                priority=priority,
                anonymous=anonymous
            )
            flash('Your complaint has been submitted successfully!', 'swal_success')
            return redirect(url_for('student.complaints'))
        else:
            flash('Please complete all required fields.', 'danger')

    my_complaints = ComplaintModel.get_student_complaints(current_user.id)
    return render_template(
        'student/complaints.html',
        complaints=my_complaints,
        categories=ComplaintModel.CATEGORIES,
        priorities=ComplaintModel.PRIORITIES
    )

@student_bp.route('/complaint/feedback/<complaint_id>', methods=['POST'])
@login_required
def complaint_feedback(complaint_id):
    if not student_only():
        return redirect(url_for('public.index'))

    action = request.form.get('action') # 'resolved' or 'still_exists'
    if action not in ['resolved', 'still_exists']:
        flash('Invalid feedback option.', 'danger')
        return redirect(url_for('student.complaints'))

    ComplaintModel.record_student_feedback(complaint_id, action, student_name=current_user.full_name)

    complaint = ComplaintModel.find_by_id(complaint_id)
    if action == 'still_exists':
        NotificationModel.create_notification(
            title="Complaint Reopened",
            message=f"Student {current_user.full_name} reported that problem for Complaint #{str(complaint_id)[-6:]} STILL EXISTS.",
            target_type="wardens",
            created_by=current_user.full_name
        )
        flash('Complaint reopened for further review.', 'swal_success')
    else:
        flash('Thank you! Complaint marked as resolved.', 'swal_success')

    return redirect(url_for('student.complaints'))

@student_bp.route('/notifications')
@login_required
def notifications():
    if not student_only():
        return redirect(url_for('public.index'))

    NotificationModel.mark_all_as_read(current_user)
    user_notifications = NotificationModel.get_user_notifications(current_user)
    return render_template('student/notifications.html', notifications=user_notifications)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not student_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()

        UserModel.update_user(current_user.id, {
            'phone': phone,
            'parent_name': parent_name,
            'parent_phone': parent_phone
        })
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))

    user_data = UserModel.find_by_id(current_user.id)
    return render_template('student/profile.html', user=user_data)

@student_bp.route('/sick-leave', methods=['GET', 'POST'])
@login_required
def sick_leave():
    if not student_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        leave_type = request.form.get('leave_type', 'Sick Leave').strip()
        start_date = request.form.get('start_date', today_str).strip()
        end_date = request.form.get('end_date', start_date).strip()
        reason = request.form.get('reason', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        address_during_leave = request.form.get('address_during_leave', '').strip()
        remarks = request.form.get('remarks', '').strip()
        symptoms = request.form.get('symptoms', '').strip()
        request_sick_diet = bool(request.form.get('request_sick_diet'))
        staying_in_hostel = bool(request.form.get('staying_in_hostel'))

        # File upload
        supporting_document = ""
        if 'supporting_document' in request.files:
            file = request.files['supporting_document']
            if file and file.filename:
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"{current_user.role_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'leaves')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                supporting_document = f"/static/uploads/leaves/{filename}"

        if start_date and end_date and reason:
            leave_id = SickLeaveModel.create_request(
                student_id=current_user.id,
                student_name=current_user.full_name,
                role_number=current_user.role_number,
                room_number=current_user.room_number or '101',
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                leave_type=leave_type,
                department=current_user.department or 'CSE',
                semester=getattr(current_user, 'semester', '5'),
                parent_name=parent_name or current_user.parent_name,
                parent_phone=parent_phone or current_user.parent_phone,
                address_during_leave=address_during_leave,
                remarks=remarks,
                symptoms=symptoms,
                request_sick_diet=request_sick_diet,
                staying_in_hostel=staying_in_hostel,
                supporting_document=supporting_document
            )

            # Create notification for Warden, Admin, Principal
            notif_msg = f"New {leave_type} Application ({leave_id}) submitted by {current_user.full_name} ({current_user.role_number}) Room {current_user.room_number or '101'}."
            NotificationModel.create_notification(
                title=f"New {leave_type} Application",
                message=notif_msg,
                target_type="all",
                created_by=current_user.full_name
            )

            flash(f'Your Leave Application ({leave_id}) Has Been Submitted Successfully!', 'swal_success')
            return redirect(url_for('student.sick_leave'))
        else:
            flash('Please fill in all required fields (Dates and Reason).', 'danger')

    leave_requests = SickLeaveModel.get_student_requests(current_user.id)
    return render_template(
        'student/sick_leave.html',
        today_str=today_str,
        leave_types=SickLeaveModel.LEAVE_TYPES,
        reasons=SickLeaveModel.REASONS,
        leave_requests=leave_requests
    )

@student_bp.route('/lms')
@login_required
def lms():
    if not student_only():
        return redirect(url_for('public.index'))

    announcements = LMSModel.get_announcements(target_role='student')

    return render_template(
        'student/lms.html',
        announcements=announcements
    )

@student_bp.route('/lms/subject/<sub_id>')
@login_required
def lms_subject_detail(sub_id):
    return redirect(url_for('student.lms'))

@student_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if not student_only():
        return redirect(url_for('public.index'))

    current_pass = request.form.get('current_password', '').strip()
    new_pass = request.form.get('new_password', '').strip()
    confirm_pass = request.form.get('confirm_password', '').strip()

    if not current_pass or not new_pass or not confirm_pass:
        flash('Please fill in all password fields.', 'danger')
        return redirect(url_for('student.profile'))

    user_data = UserModel.find_by_id(current_user.id)
    # Validate current password (match hash or default Vasavi@1234)
    if not UserModel.verify_password(user_data.get('password_hash'), current_pass) and current_pass != 'Vasavi@1234':
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('student.profile'))

    if new_pass != confirm_pass:
        flash('New password and confirm password do not match.', 'danger')
        return redirect(url_for('student.profile'))

    if len(new_pass) < 4:
        flash('New password must be at least 4 characters long.', 'warning')
        return redirect(url_for('student.profile'))

    UserModel.update_user(current_user.id, {'password': new_pass})
    flash('Password Updated Successfully!', 'swal_success')
    return redirect(url_for('student.profile'))


