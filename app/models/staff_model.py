from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class StaffModel:
    # ----------------------------------------------------
    # CARETAKERS MANAGEMENT
    # ----------------------------------------------------
    @staticmethod
    def get_all_caretakers(status=None):
        db = get_db()
        if db is None:
            return []
        query = {}
        if status:
            query['status'] = status
        try:
            return list(db.caretakers.find(query).sort('staff_id', 1))
        except Exception:
            return []

    @staticmethod
    def find_caretaker_by_staff_id(staff_id):
        db = get_db()
        if db is None or not staff_id:
            return None
        try:
            return db.caretakers.find_one({'staff_id': str(staff_id).strip().upper()})
        except Exception:
            return None

    @staticmethod
    def find_caretaker_by_id(ct_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.caretakers.find_one({'_id': to_oid(ct_id)})
        except Exception:
            return None

    @staticmethod
    def create_caretaker(data):
        db = get_db()
        if db is None:
            return None
        data['staff_id'] = str(data.get('staff_id', '')).strip().upper()
        data['full_name'] = str(data.get('full_name', '')).strip()
        data['phone'] = str(data.get('phone', '')).strip()
        data['assigned_work'] = str(data.get('assigned_work', 'General Maintenance')).strip()
        data['joining_date'] = str(data.get('joining_date', datetime.utcnow().strftime('%Y-%m-%d'))).strip()
        data['shift'] = str(data.get('shift', 'Morning')).strip()
        data['status'] = str(data.get('status', 'Active')).strip()
        data['category'] = 'Caretaker'
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.caretakers.insert_one(data).inserted_id
        except Exception:
            return None

    @staticmethod
    def update_caretaker(ct_id, data):
        db = get_db()
        if db is None:
            return None
        if 'staff_id' in data:
            data['staff_id'] = str(data['staff_id']).strip().upper()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.caretakers.update_one({'_id': to_oid(ct_id)}, {'$set': data})
        except Exception:
            return None

    @staticmethod
    def delete_caretaker(ct_id):
        db = get_db()
        if db is None:
            return None
        ct = StaffModel.find_caretaker_by_id(ct_id)
        if ct:
            # Also clean up attendance records
            try:
                db.staff_attendance.delete_many({'staff_id': ct.get('staff_id')})
            except Exception:
                pass
        try:
            return db.caretakers.delete_one({'_id': to_oid(ct_id)})
        except Exception:
            return None

    # ----------------------------------------------------
    # WORKING STAFF MANAGEMENT
    # ----------------------------------------------------
    @staticmethod
    def get_all_working_staff(status=None):
        db = get_db()
        if db is None:
            return []
        query = {}
        if status:
            query['status'] = status
        try:
            return list(db.working_staff.find(query).sort('staff_id', 1))
        except Exception:
            return []

    @staticmethod
    def find_working_staff_by_staff_id(staff_id):
        db = get_db()
        if db is None or not staff_id:
            return None
        try:
            return db.working_staff.find_one({'staff_id': str(staff_id).strip().upper()})
        except Exception:
            return None

    @staticmethod
    def find_working_staff_by_id(ws_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.working_staff.find_one({'_id': to_oid(ws_id)})
        except Exception:
            return None

    @staticmethod
    def create_working_staff(data):
        db = get_db()
        if db is None:
            return None
        data['staff_id'] = str(data.get('staff_id', '')).strip().upper()
        data['full_name'] = str(data.get('full_name', '')).strip()
        data['phone'] = str(data.get('phone', '')).strip()
        data['job_role'] = str(data.get('job_role', 'Maintenance Staff')).strip()
        data['department'] = str(data.get('department', 'Hostel Operations')).strip()
        data['joining_date'] = str(data.get('joining_date', datetime.utcnow().strftime('%Y-%m-%d'))).strip()
        data['shift'] = str(data.get('shift', 'Morning')).strip()
        data['status'] = str(data.get('status', 'Active')).strip()
        data['category'] = 'Working Staff'
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.working_staff.insert_one(data).inserted_id
        except Exception:
            return None

    @staticmethod
    def update_working_staff(ws_id, data):
        db = get_db()
        if db is None:
            return None
        if 'staff_id' in data:
            data['staff_id'] = str(data['staff_id']).strip().upper()
        data['updated_at'] = datetime.utcnow()
        try:
            return db.working_staff.update_one({'_id': to_oid(ws_id)}, {'$set': data})
        except Exception:
            return None

    @staticmethod
    def delete_working_staff(ws_id):
        db = get_db()
        if db is None:
            return None
        ws = StaffModel.find_working_staff_by_id(ws_id)
        if ws:
            try:
                db.staff_attendance.delete_many({'staff_id': ws.get('staff_id')})
            except Exception:
                pass
        try:
            return db.working_staff.delete_one({'_id': to_oid(ws_id)})
        except Exception:
            return None

    # ----------------------------------------------------
    # STAFF ATTENDANCE OPERATIONS & DASHBOARD
    # ----------------------------------------------------
    @staticmethod
    def get_daily_attendance(date_str, category=None):
        db = get_db()
        if db is None:
            return []
        query = {'attendance_date': date_str}
        if category and category != 'All':
            query['staff_category'] = category
        return list(db.staff_attendance.find(query).sort('staff_id', 1))

    @staticmethod
    def save_single_attendance(date_str, staff_info, status, check_in='', check_out='', remarks='', user_name='System Admin'):
        db = get_db()
        if db is None:
            return None

        staff_id = str(staff_info.get('staff_id', '')).strip().upper()
        existing = db.staff_attendance.find_one({'staff_id': staff_id, 'attendance_date': date_str})

        record_data = {
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

        if existing:
            db.staff_attendance.update_one({'_id': existing['_id']}, {'$set': record_data})
            return existing['_id']
        else:
            record_data['marked_by'] = user_name
            record_data['created_at'] = datetime.utcnow()
            return db.staff_attendance.insert_one(record_data).inserted_id

    @staticmethod
    def update_attendance_by_id(att_id, update_data, user_name='System Admin'):
        db = get_db()
        update_data['updated_by'] = user_name
        update_data['updated_at'] = datetime.utcnow()
        return db.staff_attendance.update_one({'_id': ObjectId(att_id)}, {'$set': update_data})

    @staticmethod
    def get_dashboard_counters(date_str):
        db = get_db()
        caretakers = list(db.caretakers.find({'status': 'Active'}))
        working_staff = list(db.working_staff.find({'status': 'Active'}))

        caretakers_map = {c['staff_id']: c for c in caretakers}
        working_staff_map = {w['staff_id']: w for w in working_staff}

        daily_records = list(db.staff_attendance.find({'attendance_date': date_str}))
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
        db = get_db()
        caretakers = list(db.caretakers.find({'status': 'Active'}))
        working_staff = list(db.working_staff.find({'status': 'Active'}))

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

        daily_records = list(db.staff_attendance.find({'attendance_date': date_str}))
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
