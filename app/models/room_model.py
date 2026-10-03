from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

FALLBACK_ROOMS = [
    {'_id': '101', 'room_number': '101', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 2, 'status': 'occupied', 'assigned_students': [{'student_name': 'K. Bhavana', 'role_number': '21A81A0501'}, {'student_name': 'M. Sneha Latha', 'role_number': '21A81A0502'}]},
    {'_id': '102', 'room_number': '102', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 1, 'status': 'occupied', 'assigned_students': [{'student_name': 'P. Sreeja', 'role_number': '22A81A0403'}]},
    {'_id': '201', 'room_number': '201', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 1, 'status': 'occupied', 'assigned_students': [{'student_name': 'T. Harika', 'role_number': '23A81A1204'}]},
    {'_id': '202', 'room_number': '202', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 0, 'status': 'available', 'assigned_students': []}
]

class RoomModel:
    @staticmethod
    def create_room(room_data):
        room_number = str(room_data.get('room_number', '')).strip()
        floor = str(room_data.get('floor', 'Floor 1')).strip()
        capacity = int(room_data.get('capacity', 4))
        occupied_beds = int(room_data.get('occupied_beds', 0))
        assigned_students = room_data.get('assigned_students', [])
        status = room_data.get('status', 'available')

        fb_doc = {
            '_id': f"room_{datetime.utcnow().timestamp()}",
            'room_number': room_number,
            'floor': floor,
            'capacity': capacity,
            'occupied_beds': occupied_beds,
            'assigned_students': assigned_students,
            'status': status,
            'created_at': datetime.utcnow()
        }

        existing_fb = [r for r in FALLBACK_ROOMS if str(r.get('room_number')).strip() == room_number]
        if not existing_fb:
            FALLBACK_ROOMS.append(fb_doc)
        else:
            existing_fb[0].update({
                'floor': floor,
                'capacity': capacity,
                'occupied_beds': occupied_beds,
                'assigned_students': assigned_students,
                'status': status
            })

        db = get_db()
        if db is not None:
            db_doc = dict(fb_doc)
            db_doc.pop('_id', None)
            try:
                return db.rooms.insert_one(db_doc).inserted_id
            except Exception:
                return fb_doc['_id']
        return fb_doc['_id']

    @staticmethod
    def get_all_rooms():
        db = get_db()
        if db is None:
            return list(FALLBACK_ROOMS)
        try:
            rooms = list(db.rooms.find().sort('room_number', 1))
            if not rooms:
                for r in FALLBACK_ROOMS:
                    r_copy = dict(r)
                    r_copy.pop('_id', None)
                    r_copy['created_at'] = datetime.utcnow()
                    try:
                        db.rooms.insert_one(r_copy)
                    except Exception:
                        pass
                rooms = list(db.rooms.find().sort('room_number', 1))

            db_room_numbers = {str(r.get('room_number')).strip() for r in rooms}
            for fb_r in FALLBACK_ROOMS:
                fb_num = str(fb_r.get('room_number')).strip()
                if fb_num not in db_room_numbers:
                    fb_copy = dict(fb_r)
                    fb_copy.pop('_id', None)
                    try:
                        res = db.rooms.insert_one(fb_copy)
                        fb_copy['_id'] = res.inserted_id
                        rooms.append(fb_copy)
                        db_room_numbers.add(fb_num)
                    except Exception:
                        rooms.append(fb_r)
            return rooms if rooms else list(FALLBACK_ROOMS)
        except Exception:
            return list(FALLBACK_ROOMS)

    @staticmethod
    def find_by_room_number(room_number):
        if not room_number:
            return None
        r_str = str(room_number).strip()
        all_r = RoomModel.get_all_rooms()
        for r in all_r:
            if str(r.get('room_number')).strip() == r_str:
                return r
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.find_one({'room_number': r_str})
        except Exception:
            return None

    @staticmethod
    def find_by_id(room_id):
        for r in FALLBACK_ROOMS:
            if str(r.get('_id')) == str(room_id):
                return r
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.find_one({'_id': to_oid(room_id)})
        except Exception:
            return None

    @staticmethod
    def update_room(room_id, update_data):
        for r in FALLBACK_ROOMS:
            if str(r.get('_id')) == str(room_id):
                r.update(update_data)
                break
        db = get_db()
        if db is None:
            return True
        try:
            return db.rooms.update_one({'_id': to_oid(room_id)}, {'$set': update_data})
        except Exception:
            return True

    @staticmethod
    def assign_student(room_number, student_id, student_name, role_number):
        room = RoomModel.find_by_room_number(room_number)
        if not room:
            return False, "Room not found"

        assigned = room.get('assigned_students', [])
        if len(assigned) >= int(room.get('capacity', 4)):
            return False, "Room is full"

        for s in assigned:
            if str(s.get('student_id')) == str(student_id) or str(s.get('role_number')) == str(role_number):
                return True, "Already assigned"

        new_entry = {
            'student_id': str(student_id),
            'student_name': student_name,
            'role_number': role_number
        }
        assigned.append(new_entry)
        new_occupied = len(assigned)
        new_status = 'full' if new_occupied >= int(room.get('capacity', 4)) else 'occupied'

        for r in FALLBACK_ROOMS:
            if str(r.get('room_number')).strip() == str(room_number).strip():
                r['assigned_students'] = assigned
                r['occupied_beds'] = new_occupied
                r['status'] = new_status
                break

        db = get_db()
        if db is not None:
            try:
                db.rooms.update_one(
                    {'room_number': str(room_number).strip()},
                    {'$set': {
                        'assigned_students': assigned,
                        'occupied_beds': new_occupied,
                        'status': new_status
                    }}
                )
            except Exception:
                pass
        return True, "Assigned successfully"

    @staticmethod
    def get_stats():
        rooms = RoomModel.get_all_rooms()
        total_rooms = len(rooms)
        occupied_rooms = sum(1 for r in rooms if r.get('status') in ['occupied', 'full'])
        available_rooms = sum(1 for r in rooms if r.get('status') == 'available')
        return {
            'total_rooms': total_rooms,
            'occupied_rooms': occupied_rooms,
            'available_rooms': available_rooms
        }


