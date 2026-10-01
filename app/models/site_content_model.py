from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class SiteContentModel:
    # --- HOME CONTENT ---
    @staticmethod
    def get_home_content():
        db = get_db()
        content = db.site_content.find_one({'type': 'home_hero'})
        if not content:
            # Default Home Hero Content
            content = {
                'type': 'home_hero',
                'title': 'Modern, Safe & Hygienic Girls Hostel Management',
                'subtext': 'Sri Vasavi Engineering College Girls Hostel',
                'description': 'Providing state-of-the-art living facilities, nutritious mess meals with egg/veg selection, daily room cleaning verification, and 24/7 dedicated security for female engineering students.',
                'banner_image': 'images/svec_campus.jpg'
            }
            db.site_content.insert_one(content)
        return content

    @staticmethod
    def update_home_content(title, subtext, description):
        db = get_db()
        return db.site_content.update_one(
            {'type': 'home_hero'},
            {'$set': {
                'title': title,
                'subtext': subtext,
                'description': description,
                'updated_at': datetime.utcnow()
            }},
            upsert=True
        )

    @staticmethod
    def get_home_sections():
        db = get_db()
        sections = list(db.home_sections.find().sort('order', 1))
        if not sections:
            # Default initial sections
            default_sections = [
                {
                    'title': 'Egg / Veg Choice System',
                    'icon': 'fa-egg',
                    'color': 'warning',
                    'description': 'Students can select Egg or Veg preferences for special meal days (Thursdays & Fridays) via their student dashboard.',
                    'order': 1
                },
                {
                    'title': 'Housekeeping Verification',
                    'icon': 'fa-broom',
                    'color': 'primary',
                    'description': 'Daily room cleaning tracking with status logs (Cleaned / Pending / Not Cleaned) and Sunday phenyl tasks.',
                    'order': 2
                },
                {
                    'title': '24/7 Grievance Portal',
                    'icon': 'fa-comments',
                    'color': 'danger',
                    'description': 'Online complaint registration for maintenance, mess, and room issues with direct resolution tracking by Wardens.',
                    'order': 3
                }
            ]
            db.home_sections.insert_many(default_sections)
            sections = list(db.home_sections.find().sort('order', 1))
        return sections

    @staticmethod
    def add_home_section(title, icon, color, description):
        db = get_db()
        count = db.home_sections.count_documents({})
        doc = {
            'title': title,
            'icon': icon or 'fa-star',
            'color': color or 'primary',
            'description': description,
            'order': count + 1,
            'created_at': datetime.utcnow()
        }
        return db.home_sections.insert_one(doc).inserted_id

    @staticmethod
    def delete_home_section(section_id):
        db = get_db()
        return db.home_sections.delete_one({'_id': ObjectId(section_id)})

    # --- HOSTEL RULES ---
    @staticmethod
    def get_rules():
        db = get_db()
        rules = list(db.hostel_rules.find().sort('order', 1))
        if not rules:
            default_rules = [
                {
                    'section_num': 1,
                    'title': 'Entry, Timings & Gate Rules',
                    'icon': 'fa-clock',
                    'rule_points': [
                        'All hostellers must return to the hostel premises by 6:30 PM strictly on all working days.',
                        'Late entry is allowed up to 7:00 PM only with prior written permission or approval from the Resident Warden.',
                        'Biometric/Register attendance is mandatory every evening at 8:00 PM.',
                        'Students leaving campus for weekend home visits must submit an approved Gate Pass countersigned by the Warden and Guardian.'
                    ],
                    'order': 1
                },
                {
                    'section_num': 2,
                    'title': 'Mess Etiquette & Food Selection Rules',
                    'icon': 'fa-utensils',
                    'rule_points': [
                        'Mess timings: Breakfast: 7:30 AM – 8:45 AM | Lunch: 12:30 PM – 2:00 PM | Snacks: 4:30 PM – 5:30 PM | Dinner: 7:30 PM – 9:00 PM.',
                        'Thursday & Friday Special Selection: Students must log into their portal and select their food preference (Egg vs. Vegetarian) before 9:00 PM on Wednesday/Thursday respectively.',
                        'Food items or mess utensils are not permitted to be carried out of the dining hall except for sick students with warden approval.',
                        'Wastage of food is strictly discouraged.'
                    ],
                    'order': 2
                },
                {
                    'section_num': 3,
                    'title': 'Room Maintenance & Sunday Phenyl Cleaning',
                    'icon': 'fa-broom',
                    'rule_points': [
                        'Rooms must be kept clean, orderly, and hygienic at all times. Daily housekeeping staff will clean rooms between 9:00 AM and 12:00 PM.',
                        'Sunday Phenyl & Deep Cleaning: Every Sunday, phenyl and cleaning materials are supplied to rooms. Students must ensure their room floor is cleared for deep cleaning.',
                        'Electrical appliances like high-wattage room heaters or heavy cooking coils are strictly prohibited.'
                    ],
                    'order': 3
                },
                {
                    'section_num': 4,
                    'title': 'Discipline, Visitors & Safety',
                    'icon': 'fa-user-lock',
                    'rule_points': [
                        'Visitors/Parents are allowed to meet residents only at the designated Reception Visitor Room between 4:00 PM and 6:30 PM on weekends.',
                        'Male visitors or non-residents are strictly prohibited from entering student room corridors.',
                        'Strict anti-ragging policies apply. Ragging or harassment of any form attracts immediate suspension and legal action.'
                    ],
                    'order': 4
                }
            ]
            db.hostel_rules.insert_many(default_rules)
            rules = list(db.hostel_rules.find().sort('order', 1))
        
        # Ensure fallback for rule_points vs items
        for r in rules:
            if 'rule_points' not in r:
                r['rule_points'] = r.get('items', [])
        return rules

    @staticmethod
    def add_rule(title, icon, items_text):
        db = get_db()
        items = [i.strip() for i in items_text.split('\n') if i.strip()]
        count = db.hostel_rules.count_documents({})
        doc = {
            'section_num': count + 1,
            'title': title,
            'icon': icon or 'fa-book-bookmark',
            'rule_points': items,
            'order': count + 1,
            'created_at': datetime.utcnow()
        }
        return db.hostel_rules.insert_one(doc).inserted_id

    @staticmethod
    def update_rule(rule_id, title, icon, items_text):
        db = get_db()
        items = [i.strip() for i in items_text.split('\n') if i.strip()]
        return db.hostel_rules.update_one(
            {'_id': ObjectId(rule_id)},
            {'$set': {
                'title': title,
                'icon': icon,
                'rule_points': items,
                'updated_at': datetime.utcnow()
            }}
        )

    @staticmethod
    def delete_rule(rule_id):
        db = get_db()
        return db.hostel_rules.delete_one({'_id': ObjectId(rule_id)})

    # --- FACILITIES ---
    @staticmethod
    def get_facilities():
        db = get_db()
        facilities = list(db.facilities.find().sort('order', 1))
        if not facilities:
            default_facilities = [
                {
                    'title': 'Furnished Clean Rooms',
                    'icon': 'fa-bed',
                    'color': 'text-primary',
                    'description': 'Well-ventilated rooms with study desks, ergonomic chairs, individual cupboards, and comfortable beds.',
                    'order': 1
                },
                {
                    'title': '24/7 RO Purified Water',
                    'icon': 'fa-bottle-water',
                    'color': 'text-info',
                    'description': 'Commercial RO water purification plants on every floor providing cold and hot mineral drinking water.',
                    'order': 2
                },
                {
                    'title': 'High-Speed Wi-Fi',
                    'icon': 'fa-wifi',
                    'color': 'text-warning',
                    'description': 'Seamless campus Wi-Fi network coverage for online learning, research, and technical project work.',
                    'order': 3
                },
                {
                    'title': 'Security & CCTV',
                    'icon': 'fa-shield-halved',
                    'color': 'text-danger',
                    'description': '24/7 female security guards, biometric access control, and comprehensive CCTV monitoring in common areas.',
                    'order': 4
                },
                {
                    'title': 'Daily Housekeeping',
                    'icon': 'fa-broom',
                    'color': 'text-success',
                    'description': 'Dedicated cleaning staff with automated daily room cleaning verification and Sunday deep cleaning tasks.',
                    'order': 5
                },
                {
                    'title': 'Medical Support',
                    'icon': 'fa-kit-medical',
                    'color': 'text-purple',
                    'description': 'On-campus dispensary with a resident doctor and emergency ambulance service on standby 24/7.',
                    'order': 6
                }
            ]
            db.facilities.insert_many(default_facilities)
            facilities = list(db.facilities.find().sort('order', 1))
        return facilities

    @staticmethod
    def add_facility(title, icon, color, description):
        db = get_db()
        count = db.facilities.count_documents({})
        doc = {
            'title': title,
            'icon': icon or 'fa-building',
            'color': color or 'text-primary',
            'description': description,
            'order': count + 1,
            'created_at': datetime.utcnow()
        }
        return db.facilities.insert_one(doc).inserted_id

    @staticmethod
    def update_facility(fac_id, title, icon, color, description):
        db = get_db()
        return db.facilities.update_one(
            {'_id': ObjectId(fac_id)},
            {'$set': {
                'title': title,
                'icon': icon,
                'color': color,
                'description': description,
                'updated_at': datetime.utcnow()
            }}
        )

    @staticmethod
    def delete_facility(fac_id):
        db = get_db()
        return db.facilities.delete_one({'_id': ObjectId(fac_id)})

    # --- CONTACT INFO ---
    @staticmethod
    def get_contact_info():
        db = get_db()
        info = db.contact_info.find_one({'type': 'contact_details'})
        if not info:
            info = {
                'type': 'contact_details',
                'address': 'PG Girls Hostel & Mess Office\nSri Vasavi Engineering College Campus,\nPedatadepalli, Tadepalligudem – 534101,\nWest Godavari District, Andhra Pradesh, India.',
                'chief_warden_phone': '+91 98480 12345',
                'assistant_warden_phone': '+91 98480 54321',
                'mess_supervisor_phone': '+91 98480 98765',
                'security_desk_phone': '08818-284355',
                'office_timings': 'Monday – Saturday: 8:00 AM – 8:00 PM\nSunday & Holidays: 9:00 AM – 5:00 PM (Emergency Desk 24/7)',
                'email': 'ghshostel@srivasaviengg.ac.in'
            }
            db.contact_info.insert_one(info)
        return info

    @staticmethod
    def update_contact_info(address, chief_phone, asst_phone, mess_phone, security_phone, timings, email):
        db = get_db()
        return db.contact_info.update_one(
            {'type': 'contact_details'},
            {'$set': {
                'address': address,
                'chief_warden_phone': chief_phone,
                'assistant_warden_phone': asst_phone,
                'mess_supervisor_phone': mess_phone,
                'security_desk_phone': security_phone,
                'office_timings': timings,
                'email': email,
                'updated_at': datetime.utcnow()
            }},
            upsert=True
        )

    # --- FEEDBACK ---
    @staticmethod
    def submit_feedback(student_id, student_name, role_number, category, rating, comment):
        db = get_db()
        doc = {
            'student_id': ObjectId(student_id) if student_id else None,
            'student_name': student_name,
            'role_number': role_number,
            'category': category,
            'rating': int(rating),
            'comment': comment,
            'created_at': datetime.utcnow()
        }
        return db.feedbacks.insert_one(doc).inserted_id

    @staticmethod
    def get_all_feedback():
        db = get_db()
        return list(db.feedbacks.find().sort('created_at', -1))

    @staticmethod
    def get_student_feedback(student_id):
        db = get_db()
        return list(db.feedbacks.find({'student_id': ObjectId(student_id)}).sort('created_at', -1))

    @staticmethod
    def delete_feedback(feedback_id):
        db = get_db()
        return db.feedbacks.delete_one({'_id': ObjectId(feedback_id)})
