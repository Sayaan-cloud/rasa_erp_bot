# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# Custom actions to interacti with a MongoDB backend.

# actions/actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from pymongo import MongoClient
import os

# MongoDB connection (replace placeholders)
# MONGO_URI = "mongodb://<username>:<password>@localhost:27017/erp_db"
MONGO_URI = "mongodb://localhost:27017/erp_db"
client = MongoClient(MONGO_URI)
db = client['erp_db']
students = db['students']

# Utility: Fetch student by ID
def fetch_student(student_id):
    return students.find_one({"student_id": student_id})

# Utility: Role-based access
def is_allowed(role, target_student_id, requesting_student_id=None):
    if role == "admin":
        return True
    elif role == "teacher":
        return True  # teachers can access all students
    elif role == "student":
        return target_student_id == requesting_student_id
    return False

# =========================
# Student Information Actions
# =========================
class ActionStudentFee(Action):
    def name(self) -> Text:
        return "action_student_fee"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')  # self-access

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text=f"❌ No record found for ID {student_id}")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 You don't have permission to view this student's fee info.")
                return []

            fee = student.get("fee_structure", {})
            paid_sem = fee.get("paid_till_semester", 0)
            per_sem = fee.get("per_semester_fee", 0)
            hostel_fee = fee.get("hostel_fee", 0)
            total_due = max((student.get("semesters",0) * per_sem + hostel_fee) - (paid_sem*per_sem + hostel_fee if paid_sem>0 else 0),0)

            dispatcher.utter_message(text=f"💰 {student['name']}'s fee status:\n"
                                          f"Paid till semester: {paid_sem}\n"
                                          f"Per Semester Fee: {per_sem}\n"
                                          f"Hostel Fee: {hostel_fee}\n"
                                          f"Total Due: {total_due}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching fee: {str(e)}")
        return []

class ActionStudentAttendance(Action):
    def name(self) -> Text:
        return "action_student_attendance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text=f"❌ No record found for ID {student_id}")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied to view attendance.")
                return []

            attendance = student.get("attendance", {})
            if not attendance:
                dispatcher.utter_message(text="ℹ️ Attendance data not available yet.")
                return []

            message = f"📊 Attendance for {student['name']}:\n"
            for sem, perc in attendance.items():
                message += f"{sem}: {perc}\n"
            dispatcher.utter_message(text=message)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching attendance: {str(e)}")
        return []

class ActionStudentResults(Action):
    def name(self) -> Text:
        return "action_student_results"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text=f"❌ No record found for ID {student_id}")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 You don't have permission to view results.")
                return []

            results = student.get("results", {})
            if not results:
                dispatcher.utter_message(text="ℹ️ Results not available yet.")
                return []

            message = f"📝 Results for {student['name']}:\n"
            for sem, gpa in results.items():
                message += f"{sem}: {gpa}\n"
            dispatcher.utter_message(text=message)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching results: {str(e)}")
        return []

class ActionHostelInfo(Action):
    def name(self) -> Text:
        return "action_hostel_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text="❌ Student not found.")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            hostel = student.get("hostel_allocation", "Not Allocated")
            dispatcher.utter_message(text=f"🏨 {student['name']}'s hostel: {hostel}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching hostel info: {str(e)}")
        return []

class ActionLibraryInfo(Action):
    def name(self) -> Text:
        return "action_library_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text="❌ Student not found.")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            library = student.get("library_access", "Inactive")
            dispatcher.utter_message(text=f"📚 {student['name']}'s library access: {library}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching library info: {str(e)}")
        return []

class ActionCourseInfo(Action):
    def name(self) -> Text:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text="❌ Student not found.")
                return []
            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            message = f"🎓 {student['name']} is enrolled in {student['course_name']} ({student['level']})\n"
            message += f"Duration: {student.get('duration_years',0)} years | Semesters: {student.get('semesters',0)}\n"
            message += f"Current Semester: {student.get('current_semester',0)} | Credits Completed: {student.get('credits_completed',0)}\n"
            message += f"Electives: {', '.join(student.get('electives',[]))}"
            dispatcher.utter_message(text=message)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching course info: {str(e)}")
        return []

class ActionPersonalInfo(Action):
    def name(self) -> Text:
        return "action_personal_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text="❌ Student not found.")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            dispatcher.utter_message(text=f"👤 {student['name']} | DOB: {student['dob']} | Email: {student['email']} | Phone: {student['phone']} | Address: {student['address']}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching personal info: {str(e)}")
        return []

class ActionFacultyAdvisorInfo(Action):
    def name(self) -> Text:
        return "action_faculty_advisor_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student:
                dispatcher.utter_message(text="❌ Student not found.")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            dispatcher.utter_message(text=f"👨‍🏫 {student['name']}'s faculty advisor: {student.get('faculty_advisor','N/A')}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching advisor info: {str(e)}")
        return []

class ActionThesisStatus(Action):
    def name(self) -> Text:
        return "action_thesis_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        student_id = tracker.get_slot('student_id')
        role = tracker.get_slot('role')
        requesting_id = tracker.get_slot('student_id')

        try:
            student = fetch_student(student_id)
            if not student or 'thesis' not in student:
                dispatcher.utter_message(text="ℹ️ Thesis information not available.")
                return []

            if not is_allowed(role, student_id, requesting_id):
                dispatcher.utter_message(text="🚫 Permission denied.")
                return []

            thesis = student.get('thesis', {})
            dispatcher.utter_message(text=f"📌 Thesis Title: {thesis.get('title','N/A')} | Status: {thesis.get('status','Not Started')}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching thesis info: {str(e)}")
        return []

# =========================
# Admin Actions
# =========================
class ActionAdminOverview(Action):
    def name(self) -> Text:
        return "action_admin_overview"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        role = tracker.get_slot('role')
        if role != "admin":
            dispatcher.utter_message(text="🚫 Only admins can access overview.")
            return []

        try:
            total_students = students.count_documents({})
            bachelors = students.count_documents({"level":"Bachelor"})
            masters = students.count_documents({"level":"Master"})
            dispatcher.utter_message(text=f"📊 Admin Dashboard:\nTotal Students: {total_students}\nBachelor Students: {bachelors}\nMaster Students: {masters}")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching admin overview: {str(e)}")
        return []

class ActionStudentList(Action):
    def name(self) -> Text:
        return "action_student_list"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        role = tracker.get_slot('role')
        if role not in ["admin","teacher"]:
            dispatcher.utter_message(text="🚫 Only teachers/admins can view student lists.")
            return []

        try:
            student_docs = students.find({}, {"student_id":1,"name":1,"course_name":1})
            message = "📋 Student List:\n"
            for s in student_docs:
                message += f"{s['student_id']} - {s['name']} ({s['course_name']})\n"
            dispatcher.utter_message(text=message)
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error fetching student list: {str(e)}")
        return []

# =========================
# CRUD Actions for Admin
# =========================
class ActionAddStudent(Action):
    def name(self) -> Text:
        return "action_add_student"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        role = tracker.get_slot('role')
        if role != "admin":
            dispatcher.utter_message(text="🚫 Only admins can add students.")
            return []

        try:
            new_student = {
                "student_id": tracker.get_slot("student_id"),
                "name": tracker.get_slot("name"),
                "dob": tracker.get_slot("dob"),
                "gender": tracker.get_slot("gender"),
                "email": tracker.get_slot("email"),
                "phone": tracker.get_slot("phone"),
                "address": tracker.get_slot("address"),
                "admission_year": tracker.get_slot("admission_year"),
                "course_id": tracker.get_slot("course_id"),
                "course_name": tracker.get_slot("course_name"),
                "level": tracker.get_slot("level"),
                "duration_years": tracker.get_slot("duration_years"),
                "semesters": tracker.get_slot("semesters"),
                "current_semester": tracker.get_slot("current_semester"),
                "credits_completed": tracker.get_slot("credits_completed"),
                "electives": tracker.get_slot("electives") or [],
                "fee_structure": tracker.get_slot("fee_structure") or {},
                "attendance": {},
                "results": {},
                "faculty_advisor": tracker.get_slot("faculty_advisor") or "",
                "library_access": "Active",
                "hostel_allocation": tracker.get_slot("hostel_allocation") or ""
            }
            students.insert_one(new_student)
            dispatcher.utter_message(text=f"✅ Student {new_student['name']} added successfully!")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error adding student: {str(e)}")
        return []

class ActionUpdateStudent(Action):
    def name(self) -> Text:
        return "action_update_student"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        role = tracker.get_slot('role')
        if role != "admin":
            dispatcher.utter_message(text="🚫 Only admins can update students.")
            return []

        student_id = tracker.get_slot("student_id")
        updates = {}
        for key in ["name","email","phone","address","current_semester","credits_completed"]:
            val = tracker.get_slot(key)
            if val:
                updates[key] = val

        try:
            result = students.update_one({"student_id":student_id},{"$set":updates})
            if result.matched_count == 0:
                dispatcher.utter_message(text="❌ Student not found.")
            else:
                dispatcher.utter_message(text=f"✅ Student {student_id} updated successfully!")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error updating student: {str(e)}")
        return []

class ActionDeleteStudent(Action):
    def name(self) -> Text:
        return "action_delete_student"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict]:
        role = tracker.get_slot('role')
        if role != "admin":
            dispatcher.utter_message(text="🚫 Only admins can delete students.")
            return []

        student_id = tracker.get_slot("student_id")
        try:
            result = students.delete_one({"student_id":student_id})
            if result.deleted_count == 0:
                dispatcher.utter_message(text="❌ Student not found.")
            else:
                dispatcher.utter_message(text=f"✅ Student {student_id} deleted successfully!")
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error deleting student: {str(e)}")
        return []
