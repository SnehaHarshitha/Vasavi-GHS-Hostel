from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class MessModel:
    DAY_ORDER = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    MEAL_ORDER = {'breakfast': 1, 'lunch': 2, 'snacks': 3, 'dinner': 4}

    @staticmethod
    def get_all_menu_items():
        db = get_db()
        if db is None:
            return []
        records = list(db.mess_menu.find())
        # Sort by day order then meal order
        records.sort(key=lambda r: (
            MessModel.DAY_ORDER.get(str(r.get('day', '')).capitalize(), 99),
            MessModel.MEAL_ORDER.get(str(r.get('meal_type', '')).lower(), 99)
        ))
        return records

    @staticmethod
    def get_menu_item_by_id(item_id):
        db = get_db()
        try:
            return db.mess_menu.find_one({'_id': ObjectId(item_id)})
        except Exception:
            return None

    @staticmethod
    def add_menu_item(data):
        db = get_db()
        data['day'] = str(data.get('day', 'Monday')).capitalize()
        data['meal_type'] = str(data.get('meal_type', 'breakfast')).lower()
        data['time'] = str(data.get('time', '')).strip()
        data['menu_items'] = str(data.get('menu_items', '')).strip()
        data['special_note'] = str(data.get('special_note', '')).strip()
        data['is_special_day'] = bool(data.get('is_special_day'))
        data['status'] = str(data.get('status', 'active')).strip()
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        return db.mess_menu.insert_one(data).inserted_id

    @staticmethod
    def update_menu_item(item_id, data):
        db = get_db()
        update_data = {
            'day': str(data.get('day', 'Monday')).capitalize(),
            'meal_type': str(data.get('meal_type', 'breakfast')).lower(),
            'menu_items': str(data.get('menu_items', '')).strip(),
            'time': str(data.get('time', '')).strip(),
            'special_note': str(data.get('special_note', '')).strip(),
            'is_special_day': bool(data.get('is_special_day')),
            'status': str(data.get('status', 'active')).strip(),
            'updated_at': datetime.utcnow()
        }
        return db.mess_menu.update_one({'_id': ObjectId(item_id)}, {'$set': update_data})

    @staticmethod
    def delete_menu_item(item_id):
        db = get_db()
        return db.mess_menu.delete_one({'_id': ObjectId(item_id)})

    @staticmethod
    def set_menu_item(day, meal_type, menu_items, time="", is_special_day=False, food_type="veg", special_note=""):
        db = get_db()
        db.mess_menu.update_one(
            {'day': day.capitalize(), 'meal_type': meal_type.lower()},
            {'$set': {
                'day': day.capitalize(),
                'meal_type': meal_type.lower(),
                'time': time,
                'menu_items': menu_items,
                'is_special_day': is_special_day,
                'food_type': food_type,
                'special_note': special_note,
                'updated_at': datetime.utcnow()
            }},
            upsert=True
        )

    @staticmethod
    def get_weekly_timetable():
        db = get_db()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        meals = ['breakfast', 'lunch', 'snacks', 'dinner']
        
        timetable = {day: {meal: "" for meal in meals} for day in days}
        times = {day: {meal: "" for meal in meals} for day in days}
        notes = {day: "" for day in days}
        is_choice_day = {'Thursday': True, 'Friday': True}

        if db is not None:
            records = list(db.mess_menu.find({'status': {'$ne': 'inactive'}}))
            for r in records:
                d = r.get('day')
                m = r.get('meal_type')
                if d in timetable and m in timetable[d]:
                    timetable[d][m] = r.get('menu_items', '')
                    if r.get('time'):
                        times[d][m] = r.get('time', '')
                    if r.get('special_note'):
                        notes[d] = r.get('special_note')

        return timetable, notes, is_choice_day, times

    @staticmethod
    def save_food_selection(student_id, role_number, date_str, food_choice):
        db = get_db()
        now = datetime.utcnow()
        db.food_selections.update_one(
            {'student_id': ObjectId(student_id), 'date': date_str},
            {'$set': {
                'student_id': ObjectId(student_id),
                'role_number': role_number,
                'date': date_str,
                'food_choice': food_choice, # 'egg' or 'veg'
                'selection_status': 'submitted',
                'updated_at': now
            }},
            upsert=True
        )

    @staticmethod
    def get_student_selection(student_id, date_str):
        db = get_db()
        if db is None:
            return None
        return db.food_selections.find_one({'student_id': ObjectId(student_id), 'date': date_str})

    @staticmethod
    def get_student_selection_history(student_id):
        db = get_db()
        if db is None:
            return []
        return list(db.food_selections.find({'student_id': ObjectId(student_id)}).sort('date', -1))

    @staticmethod
    def get_daily_selection_counts(date_str):
        db = get_db()
        if db is None:
            return {'date': date_str, 'egg_count': 0, 'veg_count': 0, 'total_selected': 0, 'total_students': 0, 'pending_count': 0}
        egg_count = db.food_selections.count_documents({'date': date_str, 'food_choice': 'egg'})
        veg_count = db.food_selections.count_documents({'date': date_str, 'food_choice': 'veg'})
        total_selected = egg_count + veg_count
        
        total_students = db.users.count_documents({'role': 'student', 'status': 'approved'})
        pending_count = max(0, total_students - total_selected)

        return {
            'date': date_str,
            'egg_count': egg_count,
            'veg_count': veg_count,
            'total_selected': total_selected,
            'total_students': total_students,
            'pending_count': pending_count
        }

    @staticmethod
    def get_selections_by_date(date_str):
        db = get_db()
        if db is None:
            return []
        return list(db.food_selections.find({'date': date_str}))


class SnacksAttendanceModel:
    @staticmethod
    def save_attendance(date_str, attendance_list, recorded_by="Admin"):
        db = get_db()
        if db is None:
            return 0
        now = datetime.utcnow()
        count = 0
        for item in attendance_list:
            role_number = str(item.get('role_number', '')).strip().upper()
            if not role_number:
                continue
            status = item.get('status', 'Not Taken')
            full_name = item.get('full_name', '')
            room_number = item.get('room_number', '101')
            department = item.get('department', 'CSE')

            db.snacks_attendance.update_one(
                {'date': date_str, 'role_number': role_number},
                {'$set': {
                    'date': date_str,
                    'role_number': role_number,
                    'full_name': full_name,
                    'room_number': room_number,
                    'department': department,
                    'status': status, # 'Taken' or 'Not Taken'
                    'recorded_by': recorded_by,
                    'updated_at': now
                }},
                upsert=True
            )
            count += 1
        return count

    @staticmethod
    def get_attendance_by_date(date_str):
        db = get_db()
        if db is None:
            return []
        return list(db.snacks_attendance.find({'date': date_str}))

    @staticmethod
    def get_attendance_stats(date_str):
        from app.models.lms_model import LMSModel
        db = get_db()
        approved_students = LMSModel.get_approved_students()
        total_students = len(approved_students)

        if db is None:
            return {
                'date': date_str,
                'total_students': total_students,
                'taken': 0,
                'not_taken': 0,
                'not_marked': total_students
            }

        taken_count = db.snacks_attendance.count_documents({'date': date_str, 'status': 'Taken'})
        not_taken_count = db.snacks_attendance.count_documents({'date': date_str, 'status': 'Not Taken'})
        marked_count = taken_count + not_taken_count
        not_marked_count = max(0, total_students - marked_count)

        return {
            'date': date_str,
            'total_students': total_students,
            'taken': taken_count,
            'not_taken': not_taken_count,
            'not_marked': not_marked_count
        }

    @staticmethod
    def get_student_history(role_number, limit=30):
        db = get_db()
        if db is None:
            return []
        return list(db.snacks_attendance.find({'role_number': str(role_number).strip().upper()}).sort('date', -1).limit(limit))

