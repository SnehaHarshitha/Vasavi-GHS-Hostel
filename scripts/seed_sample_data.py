import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pg_hostel_mess')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'pg_hostel_mess')

def seed_sample_data(target_db=None):
    if target_db is not None:
        db = target_db
    else:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]

    print("Clearing existing sample data...")
    db.users.delete_many({})
    db.rooms.delete_many({})
    db.mess_menu.delete_many({})
    db.food_selections.delete_many({})
    db.cleaning_records.delete_many({})
    db.sunday_tasks.delete_many({})
    db.complaints.delete_many({})
    db.notifications.delete_many({})
    db.contact_messages.delete_many({})

    print("Seeding Users...")
    now = datetime.utcnow()
    pass_hash = generate_password_hash("Password123!")

    # 1. Admin
    admin_id = db.users.insert_one({
        'full_name': 'System Admin',
        'username': 'admin',
        'email': 'admin@pghostelmess.com',
        'password_hash': generate_password_hash('Admin@123'),
        'role': 'admin',
        'phone': '+91 98480 11111',
        'status': 'approved',
        'is_active': True,
        'created_at': now
    }).inserted_id

    # 2. Warden
    warden_id = db.users.insert_one({
        'full_name': 'Hostel Warden',
        'username': 'warden',
        'email': 'warden@pghostelmess.com',
        'password_hash': generate_password_hash('Warden@123'),
        'role': 'warden',
        'phone': '+91 98480 12345',
        'status': 'approved',
        'is_active': True,
        'created_at': now
    }).inserted_id

    # 3. Principal
    principal_id = db.users.insert_one({
        'full_name': 'College Principal',
        'username': 'principal',
        'email': 'principal@pghostelmess.com',
        'password_hash': generate_password_hash('Principal@123'),
        'role': 'principal',
        'phone': '+91 98480 99999',
        'status': 'approved',
        'is_active': True,
        'created_at': now
    }).inserted_id

    # 4. Students
    students_data = [
        {
            'full_name': 'K. Bhavana',
            'role_number': '21A81A0501',
            'email': 'bhavana@srivasaviengg.ac.in',
            'phone': '+91 98765 00001',
            'password_hash': pass_hash,
            'role': 'student',
            'department': 'CSE',
            'year': '3rd Year',
            'parent_name': 'K. Satyanarayana',
            'parent_phone': '+91 94400 00001',
            'room_number': '101',
            'status': 'approved',
            'is_active': True,
            'created_at': now
        },
        {
            'full_name': 'M. Sneha Latha',
            'role_number': '21A81A0502',
            'email': 'sneha@srivasaviengg.ac.in',
            'phone': '+91 98765 00002',
            'password_hash': pass_hash,
            'role': 'student',
            'department': 'ECE',
            'year': '3rd Year',
            'parent_name': 'M. Ramakrishna',
            'parent_phone': '+91 94400 00002',
            'room_number': '101',
            'status': 'approved',
            'is_active': True,
            'created_at': now
        },
        {
            'full_name': 'P. Sreeja',
            'role_number': '22A81A0403',
            'email': 'sreeja@srivasaviengg.ac.in',
            'phone': '+91 98765 00003',
            'password_hash': pass_hash,
            'role': 'student',
            'department': 'ECE',
            'year': '2nd Year',
            'parent_name': 'P. Venkatrao',
            'parent_phone': '+91 94400 00003',
            'room_number': '102',
            'status': 'approved',
            'is_active': True,
            'created_at': now
        },
        {
            'full_name': 'T. Harika',
            'role_number': '23A81A1204',
            'email': 'harika@srivasaviengg.ac.in',
            'phone': '+91 98765 00004',
            'password_hash': pass_hash,
            'role': 'student',
            'department': 'IT',
            'year': '1st Year',
            'parent_name': 'T. Srinivasa Rao',
            'parent_phone': '+91 94400 00004',
            'room_number': '201',
            'status': 'approved',
            'is_active': True,
            'created_at': now
        },
        {
            'full_name': 'V. Deepthi',
            'role_number': '21A81A0205',
            'email': 'deepthi@srivasaviengg.ac.in',
            'phone': '+91 98765 00005',
            'password_hash': pass_hash,
            'role': 'student',
            'department': 'EEE',
            'year': '3rd Year',
            'parent_name': 'V. Nageswara Rao',
            'parent_phone': '+91 94400 00005',
            'room_number': '102',
            'status': 'approved', # All seeded students approved for easy testing
            'is_active': True,
            'created_at': now
        }
    ]

    inserted_students = []
    for s in students_data:
        s_id = db.users.insert_one(s).inserted_id
        inserted_students.append((s_id, s))

    print("Seeding Rooms...")
    rooms_data = [
        {
            'room_number': '101', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 2,
            'assigned_students': [{'student_id': inserted_students[0][0], 'student_name': 'K. Bhavana', 'role_number': '21A81A0501'},
                                  {'student_id': inserted_students[1][0], 'student_name': 'M. Sneha Latha', 'role_number': '21A81A0502'}],
            'status': 'occupied'
        },
        {
            'room_number': '102', 'floor': 'Floor 1', 'capacity': 4, 'occupied_beds': 1,
            'assigned_students': [{'student_id': inserted_students[2][0], 'student_name': 'P. Sreeja', 'role_number': '22A81A0403'}],
            'status': 'occupied'
        },
        {
            'room_number': '201', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 1,
            'assigned_students': [{'student_id': inserted_students[3][0], 'student_name': 'T. Harika', 'role_number': '23A81A1204'}],
            'status': 'occupied'
        },
        {
            'room_number': '202', 'floor': 'Floor 2', 'capacity': 4, 'occupied_beds': 0,
            'assigned_students': [],
            'status': 'available'
        }
    ]
    db.rooms.insert_many(rooms_data)

    print("Seeding Mess Menu...")
    db.mess_menu.delete_many({})
    menu_items = [
        {'day': 'Monday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Idli + Sambar, Coconut Chutney, Tea/Coffee', 'status': 'active'},
        {'day': 'Monday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Rice + Tomato Dal + Potato Fry, Sambar, Curd', 'status': 'active'},
        {'day': 'Monday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Biscuits / Onion Pakoda', 'status': 'active'},
        {'day': 'Monday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Chapathi, Rice + Bottle Gourd Curry, Rasam', 'status': 'active'},

        {'day': 'Tuesday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Puri + Potato Masala Kurma, Tea/Coffee', 'status': 'active'},
        {'day': 'Tuesday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Rice + Majjiga Pulusu + Ladyfinger Fry, Curd', 'status': 'active'},
        {'day': 'Tuesday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Samosa', 'status': 'active'},
        {'day': 'Tuesday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Rice + Ridge Gourd Dal + Curd', 'status': 'active'},

        {'day': 'Wednesday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Mysore Bonda + Peanut Chutney, Tea/Coffee', 'status': 'active'},
        {'day': 'Wednesday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Rice + Sambar + Cabbage Fry + Curd', 'status': 'active'},
        {'day': 'Wednesday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Punugulu', 'status': 'active'},
        {'day': 'Wednesday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Chapathi, Rice + Mixed Veg Curry', 'status': 'active'},

        {'day': 'Thursday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Upma + Chutney / Sev, Tea/Coffee', 'status': 'active'},
        {'day': 'Thursday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Veg Biryani + Raita + Spinach Dal', 'status': 'active'},
        {'day': 'Thursday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Sweet Corn', 'status': 'active'},
        {'day': 'Thursday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Chapathi, Rice + Egg Masala Curry / Paneer Butter Masala (Veg)', 'is_special_day': True, 'special_note': 'Select Egg vs Veg in Student Portal!', 'status': 'active'},

        {'day': 'Friday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Dosa + Ginger Chutney, Tea/Coffee', 'status': 'active'},
        {'day': 'Friday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Rice + Mudda Pappu + Avakaya + Curd', 'status': 'active'},
        {'day': 'Friday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Mirchi Bajji', 'status': 'active'},
        {'day': 'Friday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Rice + Boiled Eggs / Mushroom Veg Fry + Sambar', 'is_special_day': True, 'special_note': 'Select Egg vs Veg in Student Portal!', 'status': 'active'},

        {'day': 'Saturday', 'meal_type': 'breakfast', 'time': '7:30 - 8:45 AM', 'menu_items': 'Rava Dosa + Tomato Chutney, Tea/Coffee', 'status': 'active'},
        {'day': 'Saturday', 'meal_type': 'lunch', 'time': '12:30 - 2:00 PM', 'menu_items': 'Rice + Lemon Rice + Potato Kurma + Curd', 'status': 'active'},
        {'day': 'Saturday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Veg Cutlet', 'status': 'active'},
        {'day': 'Saturday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Chapathi, Rice + Tomato Curry + Rasam', 'status': 'active'},

        {'day': 'Sunday', 'meal_type': 'breakfast', 'time': '8:00 - 9:30 AM', 'menu_items': 'Puri + Chana Masala, Coffee/Tea', 'status': 'active'},
        {'day': 'Sunday', 'meal_type': 'lunch', 'time': '12:30 - 2:30 PM', 'menu_items': 'Special Sunday Meal: Bagara Rice + Paneer Curry / Veg Pulao + Sweet', 'status': 'active'},
        {'day': 'Sunday', 'meal_type': 'snacks', 'time': '4:30 - 5:30 PM', 'menu_items': 'Tea + Biscuits', 'status': 'active'},
        {'day': 'Sunday', 'meal_type': 'dinner', 'time': '7:30 - 9:00 PM', 'menu_items': 'Light Chapathi + Curd Rice + Pickle', 'status': 'active'}
    ]
    db.mess_menu.insert_many(menu_items)

    print("Seeding Food Selections...")
    today_str = datetime.now().strftime('%Y-%m-%d')
    food_selections = [
        {'student_id': inserted_students[0][0], 'role_number': '21A81A0501', 'date': today_str, 'food_choice': 'egg', 'selection_status': 'submitted', 'updated_at': now},
        {'student_id': inserted_students[1][0], 'role_number': '21A81A0502', 'date': today_str, 'food_choice': 'veg', 'selection_status': 'submitted', 'updated_at': now},
        {'student_id': inserted_students[2][0], 'role_number': '22A81A0403', 'date': today_str, 'food_choice': 'egg', 'selection_status': 'submitted', 'updated_at': now}
    ]
    db.food_selections.insert_many(food_selections)

    print("Seeding Cleaning Records...")
    cleaning_records = [
        {'room_number': '101', 'date': today_str, 'status': 'Completed', 'cleaned_by': 'Attendant Lakshmi', 'remarks': 'Deep cleaned and disinfected.', 'updated_at': now},
        {'room_number': '102', 'date': today_str, 'status': 'Completed', 'cleaned_by': 'Attendant Lakshmi', 'remarks': 'Completed floor mop.', 'updated_at': now},
        {'room_number': '201', 'date': today_str, 'status': 'Pending', 'cleaned_by': 'Housekeeping Staff', 'remarks': 'Scheduled for 11:30 AM.', 'updated_at': now}
    ]
    db.cleaning_records.insert_many(cleaning_records)

    print("Seeding Sunday Phenyl Task...")
    sunday_task = {
        'task_name': 'Sunday Room Phenyl Cleaning',
        'date': '2026-09-27',
        'rooms_or_floor': 'All Floors (1st & 2nd Floor)',
        'assigned_staff': 'Housekeeping Sanitation Team',
        'instructions': 'Phenyl and floor cleaner bottles will be distributed to every room at 9:00 AM.',
        'status': 'Scheduled',
        'created_at': now
    }
    db.sunday_tasks.insert_one(sunday_task)

    print("Seeding Complaints...")
    complaints = [
        {
            'student_id': inserted_students[0][0],
            'role_number': '21A81A0501',
            'room_number': '101',
            'category': 'Water',
            'subject': 'RO Purifier cold water line slow on Floor 1',
            'description': 'The mineral RO water dispenser on 1st floor has low water pressure.',
            'priority': 'Medium',
            'status': 'In Progress',
            'staff_reply': 'Plumber assigned to inspect the RO cartridge today.',
            'created_at': now
        },
        {
            'student_id': inserted_students[2][0],
            'role_number': '22A81A0403',
            'room_number': '102',
            'category': 'Food',
            'subject': 'Egg choice selection confirmation error',
            'description': 'Submitted egg selection but wanted to verify if choice was logged.',
            'priority': 'Low',
            'status': 'Resolved',
            'staff_reply': 'Confirmed in mess register for Thursday dinner.',
            'created_at': now
        }
    ]
    db.complaints.insert_many(complaints)

    print("Seeding Notifications...")
    notifications = [
        {
            'title': 'Welcome to PG Hostel Mess Portal',
            'message': 'All residents are advised to update their profile and submit Thursday/Friday food choices on time.',
            'target_type': 'all',
            'read_by': [],
            'created_by': 'Chief Warden',
            'created_at': now
        },
        {
            'title': 'Sunday Room Phenyl Cleaning Scheduled',
            'message': 'Sunday Phenyl cleaning is scheduled for 2026-09-27 across all floors.',
            'target_type': 'all',
            'read_by': [],
            'created_by': 'Chief Warden',
            'created_at': now
        }
    ]
    db.notifications.insert_many(notifications)

    print("Seeding Approved Students List...")
    db.approved_students.delete_many({})
    approved_list = [
        {'roll_number': '21A81A0501', 'full_name': 'K. Bhavana', 'email': 'bhavana@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '5', 'phone': '+91 98765 00001', 'room_number': '101', 'is_registered': True},
        {'roll_number': '21A81A0502', 'full_name': 'M. Sneha Latha', 'email': 'sneha@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '5', 'phone': '+91 98765 00002', 'room_number': '101', 'is_registered': True},
        {'roll_number': '22A81A0403', 'full_name': 'P. Sreeja', 'email': 'sreeja@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '3', 'phone': '+91 98765 00003', 'room_number': '102', 'is_registered': True},
        {'roll_number': '23A81A1204', 'full_name': 'T. Harika', 'email': 'harika@srivasaviengg.ac.in', 'department': 'IT', 'semester': '1', 'phone': '+91 98765 00004', 'room_number': '201', 'is_registered': True},
        {'roll_number': '21A81A0205', 'full_name': 'V. Deepthi', 'email': 'deepthi@srivasaviengg.ac.in', 'department': 'EEE', 'semester': '5', 'phone': '+91 98765 00005', 'room_number': '102', 'is_registered': True},
        {'roll_number': '23A91A0001', 'full_name': 'Student Approved One', 'email': 'student1@srivasaviengg.ac.in', 'department': 'CSE', 'semester': '5', 'phone': '+91 98480 00001', 'room_number': '103', 'is_registered': False},
        {'roll_number': '23A91A0002', 'full_name': 'Student Approved Two', 'email': 'student2@srivasaviengg.ac.in', 'department': 'ECE', 'semester': '3', 'phone': '+91 98480 00002', 'room_number': '104', 'is_registered': False}
    ]
    for app_s in approved_list:
        app_s['created_at'] = now
        db.approved_students.insert_one(app_s)


    print("Seeding Caretakers & Working Staff...")
    db.caretakers.delete_many({})
    db.working_staff.delete_many({})
    db.staff_attendance.delete_many({})


    caretakers_list = [
        {'staff_id': 'CT101', 'full_name': 'M. Lakshmi', 'phone': '+91 98480 20001', 'assigned_work': 'Hostel Maintenance', 'joining_date': '2024-01-15', 'shift': 'Morning', 'status': 'Active', 'category': 'Caretaker', 'created_at': now},
        {'staff_id': 'CT102', 'full_name': 'K. Ramulamma', 'phone': '+91 98480 20002', 'assigned_work': 'Room Cleaning', 'joining_date': '2024-03-01', 'shift': 'Morning', 'status': 'Active', 'category': 'Caretaker', 'created_at': now},
        {'staff_id': 'CT103', 'full_name': 'P. Venkatamma', 'phone': '+91 98480 20003', 'assigned_work': 'Bathroom Cleaning', 'joining_date': '2024-06-10', 'shift': 'Afternoon', 'status': 'Active', 'category': 'Caretaker', 'created_at': now}
    ]
    db.caretakers.insert_many(caretakers_list)

    working_staff_list = [
        {'staff_id': 'WS201', 'full_name': 'K. Nageswara Rao', 'phone': '+91 98480 30001', 'job_role': 'Cook', 'department': 'Mess Kitchen', 'joining_date': '2023-08-01', 'shift': 'Morning', 'status': 'Active', 'category': 'Working Staff', 'created_at': now},
        {'staff_id': 'WS202', 'full_name': 'P. Satish', 'phone': '+91 98480 30002', 'job_role': 'Assistant Cook', 'department': 'Mess Kitchen', 'joining_date': '2024-02-15', 'shift': 'Morning', 'status': 'Active', 'category': 'Working Staff', 'created_at': now},
        {'staff_id': 'WS203', 'full_name': 'M. Apparao', 'phone': '+91 98480 30003', 'job_role': 'Kitchen Helper', 'department': 'Mess Kitchen', 'joining_date': '2024-05-20', 'shift': 'Full Day', 'status': 'Active', 'category': 'Working Staff', 'created_at': now},
        {'staff_id': 'WS204', 'full_name': 'Ch. Srinivasa Rao', 'phone': '+91 98480 30004', 'job_role': 'Security Guard', 'department': 'Hostel Security', 'joining_date': '2023-11-10', 'shift': 'Night', 'status': 'Active', 'category': 'Working Staff', 'created_at': now}
    ]
    db.working_staff.insert_many(working_staff_list)

    today_str = datetime.now().strftime('%Y-%m-%d')
    attendance_list = [
        {'staff_id': 'CT101', 'full_name': 'M. Lakshmi', 'staff_category': 'Caretaker', 'job_role': 'Hostel Maintenance', 'shift': 'Morning', 'attendance_date': today_str, 'attendance_status': 'Present', 'check_in': '07:45 AM', 'check_out': '04:30 PM', 'remarks': 'On time', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'CT102', 'full_name': 'K. Ramulamma', 'staff_category': 'Caretaker', 'job_role': 'Room Cleaning', 'shift': 'Morning', 'attendance_date': today_str, 'attendance_status': 'Present', 'check_in': '08:00 AM', 'check_out': '05:00 PM', 'remarks': 'Completed floor 1', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'CT103', 'full_name': 'P. Venkatamma', 'staff_category': 'Caretaker', 'job_role': 'Bathroom Cleaning', 'shift': 'Afternoon', 'attendance_date': today_str, 'attendance_status': 'Absent', 'check_in': '', 'check_out': '', 'remarks': 'Personal work', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'WS201', 'full_name': 'K. Nageswara Rao', 'staff_category': 'Working Staff', 'job_role': 'Cook', 'shift': 'Morning', 'attendance_date': today_str, 'attendance_status': 'Present', 'check_in': '06:00 AM', 'check_out': '02:30 PM', 'remarks': 'Prepared breakfast & lunch', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'WS202', 'full_name': 'P. Satish', 'staff_category': 'Working Staff', 'job_role': 'Assistant Cook', 'shift': 'Morning', 'attendance_date': today_str, 'attendance_status': 'Present', 'check_in': '06:15 AM', 'check_out': '02:30 PM', 'remarks': 'Assisted cook', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'WS203', 'full_name': 'M. Apparao', 'staff_category': 'Working Staff', 'job_role': 'Kitchen Helper', 'shift': 'Full Day', 'attendance_date': today_str, 'attendance_status': 'On Leave', 'check_in': '', 'check_out': '', 'remarks': 'Sick leave approved', 'marked_by': 'System Admin', 'created_at': now},
        {'staff_id': 'WS204', 'full_name': 'Ch. Srinivasa Rao', 'staff_category': 'Working Staff', 'job_role': 'Security Guard', 'shift': 'Night', 'attendance_date': today_str, 'attendance_status': 'Present', 'check_in': '08:00 PM', 'check_out': '06:00 AM', 'remarks': 'Night duty', 'marked_by': 'System Admin', 'created_at': now}
    ]
    db.staff_attendance.insert_many(attendance_list)

    print("\n=======================================================")
    print("SUCCESS: Sample data & Staff Attendance seeded into MongoDB!")
    print("=======================================================")

if __name__ == '__main__':
    seed_sample_data()


