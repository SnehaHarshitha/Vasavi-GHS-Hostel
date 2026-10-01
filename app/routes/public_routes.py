from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, jsonify
from flask_login import current_user, login_required
from app.models.contact_model import ContactModel
from app.models.mess_model import MessModel
from app.models.room_model import RoomModel
from app.models.notification_model import NotificationModel
from app.models.site_content_model import SiteContentModel

public_bp = Blueprint('public', __name__)

# --- HEALTH CHECK ---
@public_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@public_bp.route('/api/unread-notifications-count')
def unread_notifications_count():
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    count = NotificationModel.count_unread(current_user)
    return jsonify({'count': count})

# --- HOME PAGE ---
@public_bp.route('/')
def index():
    home_hero = SiteContentModel.get_home_content()
    home_sections = SiteContentModel.get_home_sections()
    timetable, notes, is_choice_day, times = MessModel.get_weekly_timetable()
    room_stats = RoomModel.get_stats()
    return render_template('public/index.html', home_hero=home_hero, home_sections=home_sections, timetable=timetable, room_stats=room_stats)

@public_bp.route('/site/home/edit', methods=['POST'])
def edit_home_content():
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only Warden and Admin can edit home content.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    subtext = request.form.get('subtext', '').strip()
    description = request.form.get('description', '').strip()

    if not title:
        flash('Home Banner Title is required.', 'danger')
        return redirect(url_for('public.index'))

    SiteContentModel.update_home_content(title, subtext, description)
    NotificationModel.create_notification(
        title="Home Content Updated",
        message="The home page content has been updated.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('Home page content updated successfully.', 'success')
    return redirect(url_for('public.index'))

@public_bp.route('/site/home/add-section', methods=['POST'])
def add_home_section():
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can add home sections.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    icon = request.form.get('icon', 'fa-star').strip()
    color = request.form.get('color', 'primary').strip()
    description = request.form.get('description', '').strip()

    if not title or not description:
        flash('Section Title and Description are required.', 'danger')
        return redirect(url_for('public.index'))

    SiteContentModel.add_home_section(title, icon, color, description)
    flash('New home section added successfully.', 'success')
    return redirect(url_for('public.index'))

@public_bp.route('/site/home/delete-section/<section_id>', methods=['POST'])
def delete_home_section(section_id):
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can delete home sections.'}), 403
        abort(403)

    SiteContentModel.delete_home_section(section_id)
    flash('Home section deleted successfully.', 'success')
    return redirect(url_for('public.index'))

# --- ABOUT PAGE ---
@public_bp.route('/about')
def about():
    return render_template('public/about.html')

# --- HOSTEL RULES ---
@public_bp.route('/rules')
def rules():
    rules_list = SiteContentModel.get_rules()
    return render_template('public/rules.html', rules_list=rules_list)

@public_bp.route('/site/rules/edit/<rule_id>', methods=['POST'])
def edit_rule(rule_id):
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin() and not current_user.is_principal()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Students are not authorized to edit rules.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    icon = request.form.get('icon', 'fa-book-bookmark').strip()
    items_text = request.form.get('items_text', '').strip()

    if not title:
        flash('Rule title is required.', 'danger')
        return redirect(url_for('public.rules'))

    SiteContentModel.update_rule(rule_id, title, icon, items_text)
    NotificationModel.create_notification(
        title="Hostel Rules Updated",
        message=f"Hostel rule section '{title}' has been updated.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('Hostel rule section updated successfully.', 'success')
    return redirect(url_for('public.rules'))

@public_bp.route('/site/rules/add', methods=['POST'])
def add_rule():
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can add new rules.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    icon = request.form.get('icon', 'fa-book-bookmark').strip()
    items_text = request.form.get('items_text', '').strip()

    if not title:
        flash('Rule title is required.', 'danger')
        return redirect(url_for('public.rules'))

    SiteContentModel.add_rule(title, icon, items_text)
    NotificationModel.create_notification(
        title="New Hostel Rule Added",
        message=f"A new hostel rule section '{title}' has been published.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('New rule section added successfully.', 'success')
    return redirect(url_for('public.rules'))

@public_bp.route('/site/rules/delete/<rule_id>', methods=['POST'])
def delete_rule(rule_id):
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can delete rules.'}), 403
        abort(403)

    SiteContentModel.delete_rule(rule_id)
    flash('Rule section deleted successfully.', 'success')
    return redirect(url_for('public.rules'))

# --- FACILITIES ---
@public_bp.route('/facilities')
def facilities():
    facilities_list = SiteContentModel.get_facilities()
    return render_template('public/facilities.html', facilities_list=facilities_list)

@public_bp.route('/site/facilities/edit/<fac_id>', methods=['POST'])
def edit_facility(fac_id):
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Students are not authorized to edit facilities.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    icon = request.form.get('icon', 'fa-building').strip()
    color = request.form.get('color', 'text-primary').strip()
    description = request.form.get('description', '').strip()

    if not title or not description:
        flash('Facility Title and Description are required.', 'danger')
        return redirect(url_for('public.facilities'))

    SiteContentModel.update_facility(fac_id, title, icon, color, description)
    NotificationModel.create_notification(
        title="Hostel Facilities Updated",
        message=f"Hostel facility '{title}' details have been updated.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('Facility updated successfully.', 'success')
    return redirect(url_for('public.facilities'))

@public_bp.route('/site/facilities/add', methods=['POST'])
def add_facility():
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can add new facilities.'}), 403
        abort(403)

    title = request.form.get('title', '').strip()
    icon = request.form.get('icon', 'fa-building').strip()
    color = request.form.get('color', 'text-primary').strip()
    description = request.form.get('description', '').strip()

    if not title or not description:
        flash('Facility Title and Description are required.', 'danger')
        return redirect(url_for('public.facilities'))

    SiteContentModel.add_facility(title, icon, color, description)
    NotificationModel.create_notification(
        title="New Facility Added",
        message=f"A new facility '{title}' has been added to the hostel.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('New facility added successfully.', 'success')
    return redirect(url_for('public.facilities'))

@public_bp.route('/site/facilities/delete/<fac_id>', methods=['POST'])
def delete_facility(fac_id):
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can delete facilities.'}), 403
        abort(403)

    SiteContentModel.delete_facility(fac_id)
    flash('Facility deleted successfully.', 'success')
    return redirect(url_for('public.facilities'))

# --- MESS TIMETABLE ---
@public_bp.route('/mess')
def mess():
    timetable, notes, is_choice_day, times = MessModel.get_weekly_timetable()
    mess_items = MessModel.get_all_menu_items()
    return render_template('public/mess.html', timetable=timetable, notes=notes, is_choice_day=is_choice_day, times=times, mess_items=mess_items)

@public_bp.route('/mess/update-item', methods=['POST'])
def update_mess_item_public():
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Students are not authorized to modify the mess timetable.'}), 403
        abort(403)

    day = request.form.get('day', '').strip()
    meal_type = request.form.get('meal_type', '').strip().lower()
    time_slot = request.form.get('time', '').strip()
    menu_items = request.form.get('menu_items', '').strip()
    special_note = request.form.get('special_note', '').strip()

    if not day or not meal_type or not menu_items:
        flash('Day, Meal Type, and Food Menu Items are required.', 'danger')
        return redirect(url_for('public.mess'))

    MessModel.set_menu_item(
        day=day,
        meal_type=meal_type,
        menu_items=menu_items,
        time=time_slot,
        special_note=special_note
    )

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash('Mess timetable updated successfully.', 'success')
    return redirect(url_for('public.mess'))

@public_bp.route('/mess/add-item', methods=['POST'])
def add_mess_item_public():
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can add new mess entries.'}), 403
        abort(403)

    day = request.form.get('day', 'Monday').strip()
    meal_type = request.form.get('meal_type', 'breakfast').strip().lower()
    time_slot = request.form.get('time', '').strip()
    menu_items = request.form.get('menu_items', '').strip()
    special_note = request.form.get('special_note', '').strip()

    if not day or not meal_type or not menu_items:
        flash('Day, Meal Type, and Food Menu Items are required.', 'danger')
        return redirect(url_for('public.mess'))

    MessModel.add_menu_item({
        'day': day,
        'meal_type': meal_type,
        'time': time_slot,
        'menu_items': menu_items,
        'special_note': special_note
    })

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash('Mess timetable updated successfully.', 'success')
    return redirect(url_for('public.mess'))

@public_bp.route('/mess/delete-item/<item_id>', methods=['POST'])
def delete_mess_item_public(item_id):
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can delete mess entries.'}), 403
        abort(403)

    MessModel.delete_menu_item(item_id)

    NotificationModel.create_notification(
        title="Mess Timetable Updated",
        message="Mess timetable has been updated. Please check the latest timetable.",
        target_type="all",
        created_by=current_user.full_name
    )

    flash('Mess timetable updated successfully.', 'success')
    return redirect(url_for('public.mess'))

# --- CONTACT US ---
@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    contact_details = SiteContentModel.get_contact_info()
    maps_url = current_app.config.get('GOOGLE_MAPS_EMBED_URL')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if name and email and message:
            ContactModel.save_message(name, email, phone, subject, message)
            flash('Thank you for reaching out! Your message has been submitted to the Warden & Admin office.', 'success')
            return redirect(url_for('public.contact'))
        else:
            flash('Please fill in all required fields.', 'danger')

    return render_template('public/contact.html', contact_details=contact_details, maps_url=maps_url)

@public_bp.route('/site/contact/edit', methods=['POST'])
def edit_contact_info():
    if not current_user.is_authenticated or (not current_user.is_warden() and not current_user.is_admin()):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Students are not authorized to edit contact information.'}), 403
        abort(403)

    address = request.form.get('address', '').strip()
    chief_phone = request.form.get('chief_phone', '').strip()
    asst_phone = request.form.get('asst_phone', '').strip()
    mess_phone = request.form.get('mess_phone', '').strip()
    security_phone = request.form.get('security_phone', '').strip()
    timings = request.form.get('timings', '').strip()
    email = request.form.get('email', '').strip()

    SiteContentModel.update_contact_info(address, chief_phone, asst_phone, mess_phone, security_phone, timings, email)
    NotificationModel.create_notification(
        title="Contact Information Updated",
        message="Hostel office contact details have been updated.",
        target_type="all",
        created_by=current_user.full_name
    )
    flash('Contact details updated successfully.', 'success')
    return redirect(url_for('public.contact'))

# --- FEEDBACK ---
@public_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please log in to submit feedback.', 'warning')
            return redirect(url_for('auth.login'))

        category = request.form.get('category', 'General').strip()
        rating = request.form.get('rating', 5)
        comment = request.form.get('comment', '').strip()

        if comment:
            SiteContentModel.submit_feedback(
                student_id=current_user.id if hasattr(current_user, 'id') else None,
                student_name=getattr(current_user, 'full_name', 'Anonymous'),
                role_number=getattr(current_user, 'role_number', 'N/A'),
                category=category,
                rating=rating,
                comment=comment
            )
            flash('Thank you! Your feedback has been submitted successfully.', 'success')
            return redirect(url_for('public.feedback'))
        else:
            flash('Please provide your feedback comments.', 'danger')

    all_feedback = []
    my_feedback = []
    if current_user.is_authenticated:
        if current_user.is_student():
            my_feedback = SiteContentModel.get_student_feedback(current_user.id)
        else:
            all_feedback = SiteContentModel.get_all_feedback()
    
    return render_template('public/feedback.html', all_feedback=all_feedback, my_feedback=my_feedback)

@public_bp.route('/site/feedback/delete/<feedback_id>', methods=['POST'])
def delete_feedback(feedback_id):
    if not current_user.is_authenticated or not current_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'error': '403 Forbidden. Only System Administrators can delete feedback entries.'}), 403
        abort(403)

    SiteContentModel.delete_feedback(feedback_id)
    flash('Feedback entry deleted successfully.', 'success')
    return redirect(url_for('public.feedback'))
