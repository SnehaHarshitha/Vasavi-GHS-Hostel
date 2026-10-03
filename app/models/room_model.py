from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import get_db

class RoomModel:
    @staticmethod
    def create_room(room_data):
        db = get_db()
        room_data['occupied_beds'] = room_data.get('occupied_beds', 0)
        room_data['assigned_students'] = room_data.get('assigned_students', [])
        room_data['status'] = room_data.get('status', 'available')
        room_data['created_at'] = datetime.utcnow()
        return db.rooms.insert_one(room_data).inserted_id

    @staticmethod
    def get_all_rooms():
        db = get_db()
        if db is None:
            return []
        try:
            return list(db.rooms.find().sort('room_number', 1))
        except Exception:
            return []

    @staticmethod
    def find_by_room_number(room_number):
        db = get_db()
        if db is None:
            return None
        return db.rooms.find_one({'room_number': room_number})

    @staticmethod
    def find_by_id(room_id):
        db = get_db()
        if db is None:
            return None
        try:
            return db.rooms.find_one({'_id': ObjectId(room_id)})
        except Exception:
            return None

    @staticmethod
    def update_room(room_id, update_data):
        db = get_db()
        if db is None:
            return None
        return db.rooms.update_one({'_id': ObjectId(room_id)}, {'$set': update_data})

    @staticmethod
    def assign_student(room_number, student_id, student_name, role_number):
        db = get_db()
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
            'student_id': ObjectId(student_id),
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
