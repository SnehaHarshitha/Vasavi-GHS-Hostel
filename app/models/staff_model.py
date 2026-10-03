from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

FALLBACK_CARETAKERS = [
    {
        '_id': 'ct_1',
        'staff_id': 'CT101',
        'full_name': 'K. Lakshmi',
        'phone': '+91 98765 11111',
        'assigned_work': 'Block A Caretaker',
        'joining_date': '2023-01-15',
        'shift': 'Morning',
        'status': 'Active',
        'category': 'Caretaker'
    },
    {
        '_id': 'ct_2',
        'staff_id': 'CT102',
        'full_name': 'P. Sunitha',
        'phone': '+91 98765 22222',
        'assigned_work': 'Block B Caretaker',
        'joining_date': '2023-03-20',
        'shift': 'Evening',
        'status': 'Active',
        'category': 'Caretaker'
    }
]

FALLBACK_WORKING_STAFF = [
    {
        '_id': 'ws_1',
        'staff_id': 'WS201',
        'full_name': 'R. Rajesh',
        'phone': '+91 98765 33333',
        'job_role': 'Maintenance Staff',
        'department': 'Hostel Maintenance',
        'joining_date': '2022-06-10',
        'shift': 'Morning',
        'status': 'Active',
        'category': 'Working Staff'
    },
    {
        '_id': 'ws_2',
        'staff_id': 'WS202',
        'full_name': 'S. Kumar',
        'phone': '+91 98765 44444',
        'job_role': 'Security Staff',
        'department': 'Hostel Security',
        'joining_date': '2022-09-01',
        'shift': 'Night',
        'status': 'Active',
        'category': 'Working Staff'
    }
]

FALLBACK_STAFF_ATTENDANCE = []

class StaffModel:
    # ----------------------------------------------------
    # CARETAKERS MANAGEMENT
    # ----------------------------------------------------
    @staticmethod
    def get_all_caretakers(status=None):
        db = get_db()
        if db is None:
            res = list(FALLBACK_CARETAKERS)
            if status:
                res = [c for c in res if c.get('status') == status]
            return res
        query = {}
        if status:
            query['status'] = status
        try:
            items = list(db.caretakers.find(query).sort('staff_id', 1))
            if not items:
                for c in FALLBACK_CARETAKERS:
                    c_copy = dict(c)
                    c_copy.pop('_id', None)
                    try:
                        db.caretakers.insert_one(c_copy)
                    except Exception:
                        pass
                items = list(db.caretakers.find(query).sort('staff_id', 1))

            db_ids = {str(c.get('staff_id')).upper() for c in items}
            for fb_c in FALLBACK_CARETAKERS:
                fb_sid = str(fb_c.get('staff_id')).upper()
                if fb_sid not in db_ids:
                    if not status or fb_c.get('status') == status:
                        fb_copy = dict(fb_c)
                        fb_copy.pop('_id', None)
                        try:
                            res_id = db.caretakers.insert_one(fb_copy).inserted_id
                            fb_copy['_id'] = res_id
                            items.append(fb_copy)
                        except Exception:
                            items.append(fb_c)
            return items if items else list(FALLBACK_CARETAKERS)
        except Exception:
            res = list(FALLBACK_CARETAKERS)
            if status:
                res = [c for c in res if c.get('status') == status]
            return res

    @staticmethod
    def find_caretaker_by_staff_id(staff_id):
        if not staff_id:
            return None
        sid = str(staff_id).strip().upper()
        for c in StaffModel.get_all_caretakers():
            if str(c.get('staff_id')).strip().upper() == sid:
                return c
        return None

    @staticmethod
    def find_caretaker_by_id(ct_id):
        for c in FALLBACK_CARETAKERS:
            if str(c.get('_id')) == str(ct_id):
                return c
        db = get_db()
        if db is None:
            return None
        try:
            return db.caretakers.find_one({'_id': to_oid(ct_id)})
        except Exception:
            return None

    @staticmethod
    def create_caretaker(data):
        staff_id = str(data.get('staff_id', '')).strip().upper()
        full_name = str(data.get('full_name', '')).strip()
        phone = str(data.get('phone', '')).strip()
        assigned_work = str(data.get('assigned_work', 'General Maintenance')).strip()
        joining_date = str(data.get('joining_date', datetime.utcnow().strftime('%Y-%m-%d'))).strip()
        shift = str(data.get('shift', 'Morning')).strip()
        status = str(data.get('status', 'Active')).strip()

        fb_doc = {
            '_id': f"ct_{datetime.utcnow().timestamp()}",
            'staff_id': staff_id,
            'full_name': full_name,
            'phone': phone,
            'assigned_work': assigned_work,
            'joining_date': joining_date,
            'shift': shift,
            'status': status,
            'category': 'Caretaker',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        existing = [c for c in FALLBACK_CARETAKERS if str(c.get('staff_id')).upper() == staff_id]
        if not existing:
            FALLBACK_CARETAKERS.append(fb_doc)
        else:
            existing[0].update(fb_doc)

        db = get_db()
        if db is not None:
            db_doc = dict(fb_doc)
            db_doc.pop('_id', None)
            try:
                return db.caretakers.insert_one(db_doc).inserted_id
            except Exception:
                return fb_doc['_id']
        return fb_doc['_id']

    @staticmethod
    def update_caretaker(ct_id, data):
        if 'staff_id' in data:
            data['staff_id'] = str(data['staff_id']).strip().upper()
        data['updated_at'] = datetime.utcnow()

        for c in FALLBACK_CARETAKERS:
            if str(c.get('_id')) == str(ct_id):
                c.update(data)
                break

        db = get_db()
        if db is None:
            return True
        try:
            return db.caretakers.update_one({'_id': to_oid(ct_id)}, {'$set': data})
        except Exception:
            return True

    @staticmethod
    def delete_caretaker(ct_id):
        global FALLBACK_CARETAKERS
        ct = StaffModel.find_caretaker_by_id(ct_id)
        if ct:
            sid = ct.get('staff_id')
            FALLBACK_CARETAKERS = [c for c in FALLBACK_CARETAKERS if str(c.get('_id')) != str(ct_id) and c.get('staff_id') != sid]

        db = get_db()
        if db is None:
            return True

        if ct and ct.get('staff_id'):
            try:
                db.staff_attendance.delete_many({'staff_id': ct.get('staff_id')})
            except Exception:
                pass
        try:
            return db.caretakers.delete_one({'_id': to_oid(ct_id)})
        except Exception:
            return True

    # ----------------------------------------------------
    # WORKING STAFF MANAGEMENT
    # ----------------------------------------------------
    @staticmethod
    def get_all_working_staff(status=None):
        db = get_db()
        if db is None:
            res = list(FALLBACK_WORKING_STAFF)
            if status:
                res = [w for w in res if w.get('status') == status]
            return res
        query = {}
        if status:
            query['status'] = status
        try:
            items = list(db.working_staff.find(query).sort('staff_id', 1))
            if not items:
                for w in FALLBACK_WORKING_STAFF:
                    w_copy = dict(w)
                    w_copy.pop('_id', None)
                    try:
                        db.working_staff.insert_one(w_copy)
                    except Exception:
                        pass
                items = list(db.working_staff.find(query).sort('staff_id', 1))

            db_ids = {str(w.get('staff_id')).upper() for w in items}
            for fb_w in FALLBACK_WORKING_STAFF:
                fb_sid = str(fb_w.get('staff_id')).upper()
                if fb_sid not in db_ids:
                    if not status or fb_w.get('status') == status:
                        fb_copy = dict(fb_w)
                        fb_copy.pop('_id', None)
                        try:
                            res_id = db.working_staff.insert_one(fb_copy).inserted_id
                            fb_copy['_id'] = res_id
                            items.append(fb_copy)
                        except Exception:
                            items.append(fb_w)
            return items if items else list(FALLBACK_WORKING_STAFF)
        except Exception:
            res = list(FALLBACK_WORKING_STAFF)
            if status:
                res = [w for w in res if w.get('status') == status]
            return res

    @staticmethod
    def find_working_staff_by_staff_id(staff_id):
        if not staff_id:
            return None
        sid = str(staff_id).strip().upper()
        for w in StaffModel.get_all_working_staff():
            if str(w.get('staff_id')).strip().upper() == sid:
                return w
        return None

    @staticmethod
    def find_working_staff_by_id(ws_id):
        for w in FALLBACK_WORKING_STAFF:
            if str(w.get('_id')) == str(ws_id):
                return w
        db = get_db()
        if db is None:
            return None
        try:
            return db.working_staff.find_one({'_id': to_oid(ws_id)})
        except Exception:
            return None

    @staticmethod
    def create_working_staff(data):
        staff_id = str(data.get('staff_id', '')).strip().upper()
        full_name = str(data.get('full_name', '')).strip()
        phone = str(data.get('phone', '')).strip()
        job_role = str(data.get('job_role', 'Maintenance Staff')).strip()
        department = str(data.get('department', 'Hostel Operations')).strip()
        joining_date = str(data.get('joining_date', datetime.utcnow().strftime('%Y-%m-%d'))).strip()
        shift = str(data.get('shift', 'Morning')).strip()
        status = str(data.get('status', 'Active')).strip()

        fb_doc = {
            '_id': f"ws_{datetime.utcnow().timestamp()}",
            'staff_id': staff_id,
            'full_name': full_name,
            'phone': phone,
            'job_role': job_role,
            'department': department,
            'joining_date': joining_date,
            'shift': shift,
            'status': status,
            'category': 'Working Staff',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        existing = [w for w in FALLBACK_WORKING_STAFF if str(w.get('staff_id')).upper() == staff_id]
        if not existing:
            FALLBACK_WORKING_STAFF.append(fb_doc)
        else:
            existing[0].update(fb_doc)

        db = get_db()
        if db is not None:
            db_doc = dict(fb_doc)
            db_doc.pop('_id', None)
            try:
                return db.working_staff.insert_one(db_doc).inserted_id
            except Exception:
                return fb_doc['_id']
        return fb_doc['_id']

    @staticmethod
    def update_working_staff(ws_id, data):
        if 'staff_id' in data:
            data['staff_id'] = str(data['staff_id']).strip().upper()
        data['updated_at'] = datetime.utcnow()

        for w in FALLBACK_WORKING_STAFF:
            if str(w.get('_id')) == str(ws_id):
                w.update(data)
                break

        db = get_db()
        if db is None:
            return True
        try:
            return db.working_staff.update_one({'_id': to_oid(ws_id)}, {'$set': data})
        except Exception:
            return True

    @staticmethod
    def delete_working_staff(ws_id):
        global FALLBACK_WORKING_STAFF
        ws = StaffModel.find_working_staff_by_id(ws_id)
        if ws:
            sid = ws.get('staff_id')
            FALLBACK_WORKING_STAFF = [w for w in FALLBACK_WORKING_STAFF if str(w.get('_id')) != str(ws_id) and w.get('staff_id') != sid]

        db = get_db()
        if db is None:
            return True

        if ws and ws.get('staff_id'):
            try:
                db.staff_attendance.delete_many({'staff_id': ws.get('staff_id')})
            except Exception:
                pass
        try:
            return db.working_staff.delete_one({'_id': to_oid(ws_id)})
        except Exception:
            return True

    # ----------------------------------------------------
    # STAFF ATTENDANCE OPERATIONS & DASHBOARD
    # ----------------------------------------------------
    @staticmethod
    def get_daily_attendance(date_str, category=None):
        db = get_db()
        fb_records = [r for r in FALLBACK_STAFF_ATTENDANCE if r.get('attendance_date') == date_str]
        if category and category != 'All':
            fb_records = [r for r in fb_records if r.get('staff_category') == category]

        if db is None:
            return fb_records

        query = {'attendance_date': date_str}
        if category and category != 'All':
            query['staff_category'] = category

        try:
            db_records = list(db.staff_attendance.find(query).sort('staff_id', 1))
            db_sids = {r.get('staff_id') for r in db_records}
            for fb_r in fb_records:
                if fb_r.get('staff_id') not in db_sids:
                    db_records.append(fb_r)
            return db_records if db_records else fb_records
        except Exception:
            return fb_records

    @staticmethod
    def save_single_attendance(date_str, staff_info, status, check_in='', check_out='', remarks='', user_name='System Admin'):
        staff_id = str(staff_info.get('staff_id', '')).strip().upper()
        record_data = {
            '_id': f"att_{staff_id}_{date_str}",
            'staff_id': staff_id,
            'full_name': staff_info.get('full_name', ''),
            'staff_category': staff_info.get('category', 'Working Staff'),
            'job_role': staff_info.get('job_role') or staff_info.get('assigned_work', 'Staff'),
            'shift': staff_info.get('shift', 'Morning'),
            'attendance_date': date_str,
            'attendance_status': status,
            'check_in': check_in or '',
            'check_out': check_out or '',
            'remarks': remarks or '',
            'updated_by': user_name,
            'updated_at': datetime.utcnow()
        }

        # Update FALLBACK_STAFF_ATTENDANCE
        existing_fb = [r for r in FALLBACK_STAFF_ATTENDANCE if r.get('staff_id') == staff_id and r.get('attendance_date') == date_str]
        if existing_fb:
            existing_fb[0].update(record_data)
        else:
            record_data['marked_by'] = user_name
            record_data['created_at'] = datetime.utcnow()
            FALLBACK_STAFF_ATTENDANCE.append(record_data)

        db = get_db()
        if db is None:
            return record_data['_id']

        try:
            existing = db.staff_attendance.find_one({'staff_id': staff_id, 'attendance_date': date_str})
            if existing:
                db_data = dict(record_data)
                db_data.pop('_id', None)
                db.staff_attendance.update_one({'_id': existing['_id']}, {'$set': db_data})
                return existing['_id']
            else:
                db_data = dict(record_data)
                db_data.pop('_id', None)
                return db.staff_attendance.insert_one(db_data).inserted_id
        except Exception:
            return record_data['_id']

    @staticmethod
    def update_attendance_by_id(att_id, update_data, user_name='System Admin'):
        update_data['updated_by'] = user_name
        update_data['updated_at'] = datetime.utcnow()

        for r in FALLBACK_STAFF_ATTENDANCE:
            if str(r.get('_id')) == str(att_id):
                r.update(update_data)
                break

        db = get_db()
        if db is None:
            return True
        try:
            return db.staff_attendance.update_one({'_id': to_oid(att_id)}, {'$set': update_data})
        except Exception:
            return True

    @staticmethod
    def get_dashboard_counters(date_str):
        caretakers = StaffModel.get_all_caretakers(status='Active')
        working_staff = StaffModel.get_all_working_staff(status='Active')

        caretakers_map = {c['staff_id']: c for c in caretakers}
        working_staff_map = {w['staff_id']: w for w in working_staff}

        daily_records = StaffModel.get_daily_attendance(date_str)
        daily_map = {r['staff_id']: r for r in daily_records}

        ct_present = 0
        ct_absent = 0
        ct_leave = 0

        for c_id in caretakers_map:
            rec = daily_map.get(c_id)
            if rec:
                st = rec.get('attendance_status')
                if st == 'Present': ct_present += 1
                elif st == 'Absent': ct_absent += 1
                elif st == 'On Leave': ct_leave += 1

        ws_present = 0
        ws_absent = 0
        ws_leave = 0

        for w_id in working_staff_map:
            rec = daily_map.get(w_id)
            if rec:
                st = rec.get('attendance_status')
                if st == 'Present': ws_present += 1
                elif st == 'Absent': ws_absent += 1
                elif st == 'On Leave': ws_leave += 1

        total_staff = len(caretakers) + len(working_staff)
        total_present = ct_present + ws_present
        total_absent = ct_absent + ws_absent
        total_leave = ct_leave + ws_leave
        not_marked = total_staff - (total_present + total_absent + total_leave)

        return {
            'total_caretakers': len(caretakers),
            'caretakers_present': ct_present,
            'caretakers_absent': ct_absent,
            'caretakers_leave': ct_leave,
            'total_working_staff': len(working_staff),
            'working_staff_present': ws_present,
            'working_staff_absent': ws_absent,
            'working_staff_leave': ws_leave,
            'total_staff': total_staff,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_leave': total_leave,
            'not_marked': not_marked if not_marked >= 0 else 0
        }

    @staticmethod
    def get_categorized_staff_names(date_str):
        caretakers = StaffModel.get_all_caretakers(status='Active')
        working_staff = StaffModel.get_all_working_staff(status='Active')

        all_active_staff = []
        for c in caretakers:
            all_active_staff.append({
                'staff_id': c['staff_id'],
                'full_name': c['full_name'],
                'category': 'Caretaker',
                'job_role': c.get('assigned_work', 'Hostel Maintenance'),
                'shift': c.get('shift', 'Morning'),
                'phone': c.get('phone', '')
            })

        for w in working_staff:
            all_active_staff.append({
                'staff_id': w['staff_id'],
                'full_name': w['full_name'],
                'category': 'Working Staff',
                'job_role': w.get('job_role', 'Staff'),
                'shift': w.get('shift', 'Morning'),
                'phone': w.get('phone', '')
            })

        daily_records = StaffModel.get_daily_attendance(date_str)
        daily_map = {r['staff_id']: r for r in daily_records}

        present_list = []
        absent_list = []
        on_leave_list = []
        not_marked_list = []

        for staff in all_active_staff:
            s_id = staff['staff_id']
            rec = daily_map.get(s_id)
            staff_info = {
                'staff_id': s_id,
                'full_name': staff['full_name'],
                'category': staff['category'],
                'job_role': staff['job_role'],
                'shift': staff['shift'],
                'phone': staff['phone'],
                'check_in': rec.get('check_in', '08:00 AM') if rec else '',
                'check_out': rec.get('check_out', '05:00 PM') if rec else '',
                'remarks': rec.get('remarks', '') if rec else '',
                'attendance_date': date_str,
                'att_id': str(rec['_id']) if rec else None
            }

            if not rec:
                not_marked_list.append(staff_info)
            else:
                st = rec.get('attendance_status')
                if st == 'Present':
                    present_list.append(staff_info)
                elif st == 'Absent':
                    absent_list.append(staff_info)
                elif st == 'On Leave':
                    on_leave_list.append(staff_info)
                else:
                    not_marked_list.append(staff_info)

        return {
            'present': present_list,
            'absent': absent_list,
            'on_leave': on_leave_list,
            'not_marked': not_marked_list
        }


