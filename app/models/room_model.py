from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db, to_oid

class RoomModel:
    @staticmethod
    def create_room(room_data):
        db = get_db()
        if db is None:
            return None
        room_data['occupied_beds'] = room_data.get('occupied_beds', 0)
        room_data['assigned_students'] = room_data.get('assigned_students', [])
        room_data['status'] = room_data.get('status', 'available')
        room_data['created_at'] = datetime.utcnow()
        try:
            return db.rooms.insert_one(room_data).inserted_id
        except Exception:
            return None

    @staticmethod
    def get_all_rooms():
        default_rooms = [
            {'room_number': '101', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 2, 'status': 'occupied', 'assigned_students': [{'student_name': 'K. Bhavana', 'role_number': '21A81A0501'}, {'student_name': 'M. Sneha Latha', 'role_number': '21A81A0502'}]},
            {'room_number': '102', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 1, 'status': 'occupied', 'assigned_students': [{'student_name': 'P. Sreeja', 'role_number': '22A81A0403'}]},
            {'room_number': '201', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 1, 'status': 'occupied', 'assigned_students': [{'student_name': 'T. Harika', 'role_number': '23A81A1204'}]},
            {'room_number': '202', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 0, 'status': 'available', 'assigned_students': []}
        ]
        db = get_db()
        if db is None:
            return default_rooms
        try:
            rooms = list(db.rooms.find().sort('room_number', 1))
            return rooms if rooms else default_rooms
        except Exception:
            return default_rooms

    @staticmethod
    def find_by_room_number(room_number):
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.find_one({'room_number': room_number})
        except Exception:
            return None

    @staticmethod
    def find_by_id(room_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.find_one({'_id': to_oid(room_id)})
        except Exception:
            return None

    @staticmethod
    def update_room(room_id, update_data):
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.update_one({'_id': to_oid(room_id)}, {'$set': update_data})
        except Exception:
            return None

    @staticmethod
    def assign_student(room_number, student_id, student_name, role_number):
        db = get_db()
        if db is None:
            return False, "Database unavailable"
        try:
            room = db.rooms.find_one({'room_number': room_number})
            if not room:
                return False, "Room not found"
            
            # Check capacity
            assigned = room.get('assigned_students', [])
            if len(assigned) >= int(room.get('capacity', 4)):
                return False, "Room is full"
            
            # Check if already assigned
            for s in assigned:
                if str(s.get('student_id')) == str(student_id):
                    return True, "Already assigned"
                    
            assigned.append({
                'student_id': to_oid(student_id),
                'student_name': student_name,
                'role_number': role_number
            })
            new_occupied = len(assigned)
            new_status = 'full' if new_occupied >= int(room.get('capacity', 4)) else 'occupied'

            db.rooms.update_one(
                {'_id': room['_id']},
                {'$set': {
                    'assigned_students': assigned,
                    'occupied_beds': new_occupied,
                    'status': new_status
                }}
            )
            return True, "Assigned successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_stats():
        db = get_db()
        if db is None:
            return {'total_rooms': 0, 'occupied_rooms': 0, 'available_rooms': 0}
        try:
            total_rooms = db.rooms.count_documents({})
            occupied_rooms = db.rooms.count_documents({'status': {'$in': ['occupied', 'full']}})
            available_rooms = db.rooms.count_documents({'status': 'available'})
            return {
                'total_rooms': total_rooms,
                'occupied_rooms': occupied_rooms,
                'available_rooms': available_rooms
            }
        except Exception:
            return {'total_rooms': 0, 'occupied_rooms': 0, 'available_rooms': 0}

