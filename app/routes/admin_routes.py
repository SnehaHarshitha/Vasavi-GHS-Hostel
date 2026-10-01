import csv
import io
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app, Response
from flask_login import login_required, current_user
from app.models.user_model import UserModel
from app.models.room_model import RoomModel
from app.models.contact_model import ContactModel
from app.models.complaint_model import ComplaintModel
from app.models.mess_model import MessModel
from app.models.cleaning_model import CleaningModel
from app.models.notification_model import NotificationModel
from app.models.lms_model import LMSModel
from app.utils.pdf_parser import extract_students_from_pdf
from app.utils.staff_pdf_parser import extract_staff_from_pdf

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_only():
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.method in ['POST', 'PUT', 'DELETE'] or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            abort(403)
        flash('Access restricted to System Administrators only.', 'danger')
        return False
    return True


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not admin_only():
        return redirect(url_for('public.index'))

    today_str = datetime.now().strftime('%Y-%m-%d')
    total_students = UserModel.count_students()
    pending_registrations = UserModel.count_students(status='pending')
    total_wardens = len(UserModel.get_all_by_role('warden'))
    total_principals = len(UserModel.get_all_by_role('principal'))

    room_stats = RoomModel.get_stats()
    food_stats = MessModel.get_daily_selection_counts(today_str)
    cleaning_stats = CleaningModel.get_daily_cleaning_stats(today_str)
    complaint_stats = ComplaintModel.get_stats()
    unread_messages = ContactModel.count_unread()

    # LMS statistics
    announcements = LMSModel.get_announcements()
    approved_students = LMSModel.get_approved_students()

    return render_template(
        'admin/dashboard.html',
        today_str=today_str,
        total_students=total_students,
        pending_registrations=pending_registrations,
        total_wardens=total_wardens,
        total_principals=total_principals,
        room_stats=room_stats,
        food_stats=food_stats,
        cleaning_stats=cleaning_stats,
        complaint_stats=complaint_stats,
        unread_messages=unread_messages,
        total_announcements=len(announcements),
        total_approved_students=len(approved_students)
    )

@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if not admin_only():
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'student').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        role_number = (request.form.get('role_number') or request.form.get('roll_no') or request.form.get('role_no') or '').strip().upper()
        room_number = (request.form.get('room_number') or request.form.get('room_no') or '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        status = request.form.get('status', 'approved').strip().lower()

        if not full_name or not password or (role == 'student' and not role_number):
            flash('Please fill in all required fields.', 'danger')
        elif confirm_password and password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif role == 'student' and role_number and UserModel.find_by_role_number(role_number):
            flash('Role number already exists.', 'danger')
        elif email and UserModel.find_by_email(email):
            flash('Email already registered.', 'danger')
        elif role == 'student' and room_number and RoomModel.get_stats().get('total_rooms', 0) > 0 and not RoomModel.find_by_room_number(room_number):
            flash('Invalid room number.', 'danger')
        else:
            user_data = {
                'full_name': full_name,
                'email': email,
                'role': role,
                'phone': phone,
                'password': password,
                'status': status or 'approved',
                'is_active': True
            }
            if role == 'student':
                user_data['role_number'] = role_number
                user_data['room_number'] = room_number or '101'
                user_data['department'] = department or 'CSE'
                user_data['year'] = year or '3rd Year'
                user_data['username'] = role_number.lower() if role_number else (email.split('@')[0] if email else full_name.lower().replace(' ', ''))
                
                # Auto add to approved list as well
                if role_number:
                    approved_student = LMSModel.find_approved_student(role_number, email)
                    if approved_student:
                        LMSModel.update_approved_student(approved_student['_id'], {
                            'full_name': full_name,
                            'email': email,
                            'phone': phone,
                            'room_number': room_number or '101',
                            'is_registered': True
                        })
                    else:
                        LMSModel.create_approved_student({
                            'roll_number': role_number,
                            'full_name': full_name,
                            'email': email,
                            'department': department or 'CSE',
                            'semester': '5',
                            'phone': phone,
                            'room_number': room_number or '101',
                            'is_registered': True
                        })

            new_user_id = UserModel.create_user(user_data)

            if role == 'student' and room_number:
                RoomModel.assign_student(
                    room_number=room_number,
                    student_id=str(new_user_id),
                    student_name=full_name,
                    role_number=role_number
                )

            flash("Student Successfully Registered!" if role == 'student' else f"New {role.title()} account created successfully.", 'swal_success' if role == 'student' else 'success')
        return redirect(url_for('admin.users'))


    all_users = (
        UserModel.get_all_by_role('admin') +
        UserModel.get_all_by_role('principal') +
        UserModel.get_all_by_role('warden') +
        UserModel.get_all_by_role('student')
    )

    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/edit/<user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    role_number = request.form.get('role_number', '').strip().upper()
    department = request.form.get('department', '').strip()
    year = request.form.get('year', '').strip()
    room_number = request.form.get('room_number', '').strip()
    status = request.form.get('status', 'approved').strip()

    update_data = {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'role_number': role_number,
        'department': department,
        'year': year,
        'room_number': room_number,
        'status': status
    }
    
    password = request.form.get('password', '').strip()
    if password:
        update_data['password'] = password

    UserModel.update_user(user_id, update_data)
    flash('User details updated successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    user = UserModel.find_by_id(user_id)
    if user and user.get('email') == current_user.email:
        flash('You cannot delete your own admin account!', 'danger')
    else:
        UserModel.delete_user(user_id)
        flash('User account deleted successfully.', 'success')

    return redirect(url_for('admin.users'))

from app.models.staff_model import StaffModel

# ----------------------------------------------------
# LMS CONTENT MANAGEMENT DASHBOARD & ROUTES
# ----------------------------------------------------
@admin_bp.route('/lms')
@login_required
def lms_dashboard():
    if not admin_only():
        return redirect(url_for('public.index'))

    active_tab = request.args.get('active_tab', 'mess')
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    announcements = LMSModel.get_announcements()
    approved_students = LMSModel.get_approved_students()
    mess_items = MessModel.get_all_menu_items()

    # Staff Attendance Management Data
    caretakers = StaffModel.get_all_caretakers()
    working_staff = StaffModel.get_all_working_staff()
    attendance_stats = StaffModel.get_dashboard_counters(selected_date)
    categorized_staff_names = StaffModel.get_categorized_staff_names(selected_date)
    daily_attendance_records = StaffModel.get_daily_attendance(selected_date)

    return render_template(
        'admin/lms.html',
        announcements=announcements,
        approved_students=approved_students,
        mess_items=mess_items,
        caretakers=caretakers,
        working_staff=working_staff,
        attendance_stats=attendance_stats,
        categorized_staff_names=categorized_staff_names,
        daily_attendance_records=daily_attendance_records,
        selected_date=selected_date,
        active_tab=active_tab
    )

# ----------------------------------------------------
# CARETAKER & WORKING STAFF MANAGEMENT ROUTES
# ----------------------------------------------------
@admin_bp.route('/caretakers/add', methods=['POST'])
@admin_bp.route('/caretaker/add', methods=['POST'])
@login_required
def add_caretaker():
    if not admin_only():
        return redirect(url_for('public.index'))

    staff_id = request.form.get('staff_id', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    assigned_work = request.form.get('assigned_work', 'Hostel Maintenance').strip()
    joining_date = request.form.get('joining_date', datetime.now().strftime('%Y-%m-%d')).strip()
    shift = request.form.get('shift', 'Morning').strip()
    status = request.form.get('status', 'Active').strip()

    if not staff_id or not full_name:
        flash('Staff ID and Full Name are required.', 'danger')
        return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

    if StaffModel.find_caretaker_by_staff_id(staff_id) or StaffModel.find_working_staff_by_staff_id(staff_id):
        flash(f'Staff ID {staff_id} already exists. Please use a unique Staff ID.', 'warning')
        return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

    StaffModel.create_caretaker({
        'staff_id': staff_id,
        'full_name': full_name,
        'phone': phone,
        'assigned_work': assigned_work,
        'joining_date': joining_date,
        'shift': shift,
        'status': status
    })
    flash('Caretaker Added Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

@admin_bp.route('/caretakers/edit/<ct_id>', methods=['POST'])
@login_required
def edit_caretaker(ct_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    data = {
        'staff_id': request.form.get('staff_id', '').strip().upper(),
        'full_name': request.form.get('full_name', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'assigned_work': request.form.get('assigned_work', 'Hostel Maintenance').strip(),
        'joining_date': request.form.get('joining_date', '').strip(),
        'shift': request.form.get('shift', 'Morning').strip(),
        'status': request.form.get('status', 'Active').strip()
    }
    StaffModel.update_caretaker(ct_id, data)
    flash('Caretaker Details Updated Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

@admin_bp.route('/caretakers/delete/<ct_id>', methods=['POST'])
@login_required
def delete_caretaker(ct_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    StaffModel.delete_caretaker(ct_id)
    flash('Caretaker removed successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

@admin_bp.route('/working-staff/add', methods=['POST'])
@login_required
def add_working_staff():
    if not admin_only():
        return redirect(url_for('public.index'))

    staff_id = request.form.get('staff_id', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    job_role = request.form.get('job_role', 'Maintenance Staff').strip()
    department = request.form.get('department', 'Hostel Operations').strip()
    joining_date = request.form.get('joining_date', datetime.now().strftime('%Y-%m-%d')).strip()
    shift = request.form.get('shift', 'Morning').strip()
    status = request.form.get('status', 'Active').strip()

    if not staff_id or not full_name:
        flash('Staff ID and Full Name are required.', 'danger')
        return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

    if StaffModel.find_working_staff_by_staff_id(staff_id) or StaffModel.find_caretaker_by_staff_id(staff_id):
        flash(f'Staff ID {staff_id} already exists. Please use a unique Staff ID.', 'warning')
        return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

    StaffModel.create_working_staff({
        'staff_id': staff_id,
        'full_name': full_name,
        'phone': phone,
        'job_role': job_role,
        'department': department,
        'joining_date': joining_date,
        'shift': shift,
        'status': status
    })
    flash('Working Staff Added Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

@admin_bp.route('/working-staff/edit/<ws_id>', methods=['POST'])
@login_required
def edit_working_staff(ws_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    data = {
        'staff_id': request.form.get('staff_id', '').strip().upper(),
        'full_name': request.form.get('full_name', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'job_role': request.form.get('job_role', 'Maintenance Staff').strip(),
        'department': request.form.get('department', 'Hostel Operations').strip(),
        'joining_date': request.form.get('joining_date', '').strip(),
        'shift': request.form.get('shift', 'Morning').strip(),
        'status': request.form.get('status', 'Active').strip()
    }
    StaffModel.update_working_staff(ws_id, data)
    flash('Working Staff Details Updated Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

@admin_bp.route('/working-staff/delete/<ws_id>', methods=['POST'])
@login_required
def delete_working_staff(ws_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    StaffModel.delete_working_staff(ws_id)
    flash('Working staff removed successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff'))

# ----------------------------------------------------
# DAILY ATTENDANCE MARKING & EDITING ROUTES
# ----------------------------------------------------
@admin_bp.route('/staff-attendance/save', methods=['POST'])
@login_required
def save_staff_attendance():
    if not admin_only():
        return redirect(url_for('public.index'))

    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    staff_ids = request.form.getlist('staff_ids')

    saved_count = 0
    for s_id in staff_ids:
        status = request.form.get(f'status_{s_id}', 'Present').strip()
        check_in = request.form.get(f'check_in_{s_id}', '').strip()
        check_out = request.form.get(f'check_out_{s_id}', '').strip()
        remarks = request.form.get(f'remarks_{s_id}', '').strip()

        # Find staff info
        staff_info = StaffModel.find_caretaker_by_staff_id(s_id)
        if not staff_info:
            staff_info = StaffModel.find_working_staff_by_staff_id(s_id)

        if staff_info:
            StaffModel.save_single_attendance(
                date_str=date_str,
                staff_info=staff_info,
                status=status,
                check_in=check_in,
                check_out=check_out,
                remarks=remarks,
                user_name=current_user.full_name
            )
            saved_count += 1

    flash('Daily Attendance Saved Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff', date=date_str))

@admin_bp.route('/staff-attendance/edit/<att_id>', methods=['POST'])
@login_required
def edit_single_staff_attendance(att_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    date_str = request.form.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    status = request.form.get('status', 'Present').strip()
    check_in = request.form.get('check_in', '').strip()
    check_out = request.form.get('check_out', '').strip()
    remarks = request.form.get('remarks', '').strip()

    StaffModel.update_attendance_by_id(att_id, {
        'attendance_status': status,
        'check_in': check_in,
        'check_out': check_out,
        'remarks': remarks
    }, user_name=current_user.full_name)

    flash('Attendance Updated Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='staff', date=date_str))

@admin_bp.route('/staff-attendance/download-csv', methods=['GET'])
@login_required
def download_attendance_csv():
    if not admin_only():
        return redirect(url_for('public.index'))

    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    category = request.args.get('category', 'All').strip()

    records = StaffModel.get_daily_attendance(date_str, category=category)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Staff ID', 'Full Name', 'Category', 'Job Role / Work', 'Shift', 'Attendance Date', 'Status', 'Check-In', 'Check-Out', 'Remarks', 'Marked By'])

    for r in records:
        writer.writerow([
            r.get('staff_id', ''),
            r.get('full_name', ''),
            r.get('staff_category', ''),
            r.get('job_role', ''),
            r.get('shift', ''),
            r.get('attendance_date', ''),
            r.get('attendance_status', ''),
            r.get('check_in', ''),
            r.get('check_out', ''),
            r.get('remarks', ''),
            r.get('marked_by', '')
        ])

    output.seek(0)
    return current_app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=Staff_Attendance_Report_{date_str}.csv'}
    )


# --- APPROVED STUDENTS MANAGEMENT ---
@admin_bp.route('/approved-students/add', methods=['POST'])
@login_required
def add_approved_student():
    if not admin_only():
        return redirect(url_for('public.index'))

    roll_number = request.form.get('roll_number', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    department = request.form.get('department', 'CSE').strip()
    semester = request.form.get('semester', '5').strip()
    phone = request.form.get('phone', '').strip()
    room_number = request.form.get('room_number', '101').strip()

    if not roll_number or not full_name:
        flash('Roll Number and Full Name are required.', 'danger')
        return redirect(url_for('admin.lms_dashboard', active_tab='students'))

    existing_roll = LMSModel.get_approved_students()
    for s in existing_roll:
        if s.get('roll_number', '').upper() == roll_number:
            flash('Role Number Already Exists', 'danger')
            return redirect(url_for('admin.lms_dashboard', active_tab='students'))
        if email and s.get('email', '').lower() == email:
            flash('Email Already Registered', 'danger')
            return redirect(url_for('admin.lms_dashboard', active_tab='students'))

    LMSModel.create_approved_student({
        'roll_number': roll_number,
        'full_name': full_name,
        'email': email,
        'department': department,
        'semester': semester,
        'phone': phone,
        'room_number': room_number
    })
    flash('Student Successfully Added!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='students'))

@admin_bp.route('/approved-students/edit/<student_id>', methods=['POST'])
@login_required
def edit_approved_student(student_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    data = {
        'roll_number': request.form.get('roll_number', '').strip().upper(),
        'full_name': request.form.get('full_name', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'department': request.form.get('department', 'CSE').strip(),
        'semester': request.form.get('semester', '5').strip(),
        'phone': request.form.get('phone', '').strip(),
        'room_number': request.form.get('room_number', '101').strip()
    }
    LMSModel.update_approved_student(student_id, data)
    
    # Update active user account if already registered
    registered_user = UserModel.find_by_role_number(data['roll_number'])
    if registered_user:
        UserModel.update_user(registered_user['_id'], {
            'full_name': data['full_name'],
            'email': data['email'],
            'department': data['department'],
            'semester': data['semester'],
            'phone': data['phone'],
            'room_number': data['room_number']
        })

    flash('Student Details Updated Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='students'))

@admin_bp.route('/approved-students/delete/<student_id>', methods=['POST'])
@login_required
def delete_approved_student(student_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    LMSModel.delete_approved_student(student_id)
    flash('Student Deleted Successfully!', 'swal_success')
    return redirect(url_for('admin.lms_dashboard', active_tab='students'))

@admin_bp.route('/approved-students/preview-pdf', methods=['POST'])
@login_required
def preview_pdf_students():
    if not admin_only():
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'error': 'Please select a PDF file.'}), 400

    pdf_file = request.files['pdf_file']
    if not pdf_file or not pdf_file.filename or not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Please upload a valid PDF file.'}), 400

    try:
        pdf_bytes = pdf_file.read()
        if not pdf_bytes:
            return jsonify({'success': False, 'error': 'The uploaded PDF file is empty.'}), 400

        extracted_students = extract_students_from_pdf(pdf_bytes)
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception:
        return jsonify({'success': False, 'error': 'Unable to process this PDF. Please check the file and try again.'}), 400

    if not extracted_students:
        return jsonify({'success': False, 'error': 'The PDF does not contain readable student data.'}), 400

    existing_students = LMSModel.get_approved_students()
    existing_rolls = {s.get('roll_number', '').upper() for s in existing_students if s.get('roll_number')}
    existing_emails = {s.get('email', '').lower() for s in existing_students if s.get('email')}

    processed_records = []
    valid_count = 0
    duplicate_count = 0
    invalid_count = 0

    for s in extracted_students:
        roll = (s.get('roll_number') or '').strip().upper()
        name = (s.get('full_name') or '').strip()
        email = (s.get('email') or '').strip().lower()
        dept = (s.get('department') or 'CSE').strip()
        sem = str(s.get('semester') or '5').strip()

        is_valid_roll = bool(roll and len(roll) >= 4)
        is_valid_name = bool(name and len(name) >= 2)
        is_valid_email = bool(email and '@' in email)

        if not (is_valid_roll and is_valid_name and is_valid_email):
            status = 'invalid'
            reason = 'Missing roll number / name or invalid email format'
            invalid_count += 1
        elif roll in existing_rolls or email in existing_emails:
            status = 'duplicate'
            reason = 'Already exists in approved list'
            duplicate_count += 1
        else:
            status = 'valid'
            reason = 'New student ready to import'
            valid_count += 1

        processed_records.append({
            'roll_number': roll,
            'full_name': name,
            'email': email,
            'department': dept,
            'semester': sem,
            'status': status,
            'reason': reason
        })

    return jsonify({
        'success': True,
        'total_count': len(processed_records),
        'valid_count': valid_count,
        'duplicate_count': duplicate_count,
        'invalid_count': invalid_count,
        'records': processed_records
    })

@admin_bp.route('/approved-students/confirm-import-pdf', methods=['POST'])
@login_required
def confirm_import_pdf():
    if not admin_only():
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    payload = request.get_json() or {}
    students_to_import = payload.get('students', [])

    if not students_to_import:
        return jsonify({'success': False, 'error': 'No valid students selected for import.'}), 400

    clean_students = []
    for s in students_to_import:
        clean_students.append({
            'roll_number': s.get('roll_number', '').strip().upper(),
            'full_name': s.get('full_name', '').strip(),
            'email': s.get('email', '').strip().lower(),
            'department': s.get('department', 'CSE').strip(),
            'semester': str(s.get('semester', '5')).strip(),
            'phone': s.get('phone', '').strip(),
            'room_number': s.get('room_number', '101').strip()
        })

    added_count = LMSModel.bulk_import_approved_students(clean_students)
    flash(f'✓ {added_count} students imported successfully from PDF.', 'success')

    return jsonify({
        'success': True,
        'imported_count': added_count,
        'message': f'{added_count} students imported successfully.'
    })

# --- ANNOUNCEMENTS ---
@admin_bp.route('/announcements/add', methods=['POST'])
@login_required
def add_announcement():
    if not admin_only():
        return redirect(url_for('public.index'))

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'Medium').strip()
    target_role = request.form.get('target_role', 'student').strip()

    if not title or not content:
        flash('Title and Announcement Content are required.', 'danger')
        return redirect(url_for('admin.lms_dashboard'))

    LMSModel.create_announcement({
        'title': title,
        'content': content,
        'priority': priority,
        'target_role': target_role
    })
    flash('Announcement published successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard'))

@admin_bp.route('/announcements/edit/<anc_id>', methods=['POST'])
@login_required
def edit_announcement(anc_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    data = {
        'title': request.form.get('title', '').strip(),
        'content': request.form.get('content', '').strip(),
        'priority': request.form.get('priority', 'Medium').strip(),
        'target_role': request.form.get('target_role', 'student').strip()
    }
    LMSModel.update_announcement(anc_id, data)
    flash('Announcement updated successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard'))

@admin_bp.route('/announcements/delete/<anc_id>', methods=['POST'])
@login_required
def delete_announcement(anc_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    LMSModel.delete_announcement(anc_id)
    flash('Announcement deleted successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard'))

@admin_bp.route('/contact-messages')
@login_required
def contact_messages():
    if not admin_only():
        return redirect(url_for('public.index'))

    messages = ContactModel.get_all_messages()
    return render_template('admin/contact_messages.html', messages=messages)

@admin_bp.route('/contact-messages/read/<msg_id>', methods=['POST'])
@login_required
def mark_contact_read(msg_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    ContactModel.mark_as_read(msg_id)
    flash('Message marked as read.', 'success')
    return redirect(url_for('admin.contact_messages'))

@admin_bp.route('/settings')
@login_required
def settings():
    if not admin_only():
        return redirect(url_for('public.index'))

    return render_template('admin/settings.html')

# ----------------------------------------------------
# FOOD TIMETABLE / MESS MENU MANAGEMENT
# ----------------------------------------------------
@admin_bp.route('/mess-timetable/add', methods=['POST'])
@login_required
def add_mess_item():
    if not admin_only():
        return redirect(url_for('public.index'))

    day = request.form.get('day', 'Monday').strip()
    meal_type = request.form.get('meal_type', 'breakfast').strip().lower()
    time_slot = request.form.get('time', '').strip()
    menu_items = request.form.get('menu_items', '').strip()
    special_note = request.form.get('special_note', '').strip()
    is_special_day = bool(request.form.get('is_special_day'))

    if not day or not meal_type or not menu_items:
        flash('Day, Meal Type, and Food Menu Items are required.', 'danger')
        return redirect(url_for('admin.lms_dashboard', active_tab='mess'))

    MessModel.add_menu_item({
        'day': day,
        'meal_type': meal_type,
        'time': time_slot,
        'menu_items': menu_items,
        'special_note': special_note,
        'is_special_day': is_special_day
    })

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash(f'Food timetable entry for {day} {meal_type.title()} saved successfully!', 'success')
    return redirect(url_for('admin.lms_dashboard', active_tab='mess'))

@admin_bp.route('/mess-timetable/edit/<item_id>', methods=['POST'])
@login_required
def edit_mess_item(item_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    day = request.form.get('day', 'Monday').strip()
    meal_type = request.form.get('meal_type', 'breakfast').strip().lower()
    time_slot = request.form.get('time', '').strip()
    menu_items = request.form.get('menu_items', '').strip()
    special_note = request.form.get('special_note', '').strip()
    is_special_day = bool(request.form.get('is_special_day'))

    if not menu_items:
        flash('Food menu items cannot be empty.', 'danger')
        return redirect(url_for('admin.lms_dashboard', active_tab='mess'))

    MessModel.update_menu_item(item_id, {
        'day': day,
        'meal_type': meal_type,
        'time': time_slot,
        'menu_items': menu_items,
        'special_note': special_note,
        'is_special_day': is_special_day
    })

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash('Mess timetable updated successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard', active_tab='mess'))

@admin_bp.route('/mess-timetable/delete/<item_id>', methods=['POST'])
@login_required
def delete_mess_item(item_id):
    if not admin_only():
        return redirect(url_for('public.index'))

    MessModel.delete_menu_item(item_id)

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash('Mess timetable entry deleted successfully.', 'success')
    return redirect(url_for('admin.lms_dashboard', active_tab='mess'))

# --- STAFF PDF IMPORT ROUTES ---
@admin_bp.route('/staff/preview-pdf', methods=['POST'])
@login_required
def preview_pdf_staff():
    if not admin_only():
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'error': 'Please select a PDF file.'}), 400

    pdf_file = request.files['pdf_file']
    if not pdf_file or not pdf_file.filename or not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Please upload a valid PDF file.'}), 400

    try:
        pdf_bytes = pdf_file.read()
        if not pdf_bytes:
            return jsonify({'success': False, 'error': 'The uploaded PDF file is empty.'}), 400

        extracted_staff = extract_staff_from_pdf(pdf_bytes)
    except Exception:
        return jsonify({'success': False, 'error': 'Unable to process this PDF. Please verify that the PDF is readable.'}), 400

    if not extracted_staff:
        return jsonify({'success': False, 'error': 'The PDF does not contain readable staff data.'}), 400

    existing_cts = {c.get('staff_id', '').upper() for c in StaffModel.get_all_caretakers()}
    existing_wss = {w.get('staff_id', '').upper() for w in StaffModel.get_all_working_staff()}
    all_existing = existing_cts.union(existing_wss)

    processed = []
    valid_count = 0
    duplicate_count = 0
    invalid_count = 0

    for s in extracted_staff:
        s_id = s.get('staff_id', '').upper().strip()
        name = s.get('full_name', '').strip()
        phone = s.get('phone', '').strip()

        if not s_id or not name:
            status = 'invalid'
            reason = 'Missing Staff ID or Name'
            invalid_count += 1
        elif s_id in all_existing:
            status = 'duplicate'
            reason = 'Staff ID already exists'
            duplicate_count += 1
        else:
            status = 'valid'
            reason = 'Ready to import'
            valid_count += 1

        processed.append({
            'staff_id': s_id,
            'full_name': name,
            'phone': phone,
            'job_role': s.get('job_role', 'Staff'),
            'department': s.get('department', 'Hostel Operations'),
            'shift': s.get('shift', 'Morning'),
            'category': s.get('category', 'Working Staff'),
            'status': status,
            'reason': reason
        })

    return jsonify({
        'success': True,
        'total_count': len(processed),
        'valid_count': valid_count,
        'duplicate_count': duplicate_count,
        'invalid_count': invalid_count,
        'records': processed
    })

@admin_bp.route('/staff/confirm-import-pdf', methods=['POST'])
@login_required
def confirm_import_staff_pdf():
    if not admin_only():
        return jsonify({'success': False, 'error': 'Unauthorized access.'}), 403

    payload = request.get_json() or {}
    staff_to_import = payload.get('staff', [])

    if not staff_to_import:
        return jsonify({'success': False, 'error': 'No valid staff records selected for import.'}), 400

    imported_count = 0
    for s in staff_to_import:
        cat = s.get('category', 'Working Staff')
        if cat == 'Caretaker':
            StaffModel.create_caretaker({
                'staff_id': s.get('staff_id'),
                'full_name': s.get('full_name'),
                'phone': s.get('phone', ''),
                'assigned_work': s.get('job_role', 'Hostel Maintenance'),
                'shift': s.get('shift', 'Morning'),
                'status': 'Active'
            })
        else:
            StaffModel.create_working_staff({
                'staff_id': s.get('staff_id'),
                'full_name': s.get('full_name'),
                'phone': s.get('phone', ''),
                'job_role': s.get('job_role', 'Maintenance Staff'),
                'department': s.get('department', 'Hostel Operations'),
                'shift': s.get('shift', 'Morning'),
                'status': 'Active'
            })
        imported_count += 1

    flash('Staff Details Imported Successfully!', 'swal_success')
    return jsonify({
        'success': True,
        'imported_count': imported_count,
        'message': f'{imported_count} staff details imported successfully.'
    })

