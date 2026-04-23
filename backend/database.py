from pymongo import MongoClient, ASCENDING, DESCENDING
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────
# CONNECT
# ─────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["attentrack"]

# Collections
students_collection  = db["students"]
sessions_collection  = db["sessions"]
attention_collection = db["attention_logs"]
alerts_collection    = db["alerts"]
parents_collection   = db["parents"]
admins_collection    = db["admins"]       # ← NEW: admin accounts


# ─────────────────────────────────────
# INDEXES
# ─────────────────────────────────────
def create_indexes():
    attention_collection.create_index([("student_id", ASCENDING)])
    attention_collection.create_index([("timestamp",  DESCENDING)])

    alerts_collection.create_index([("student_id", ASCENDING)])
    alerts_collection.create_index([("timestamp",  DESCENDING)])

    sessions_collection.create_index([("student_id", ASCENDING)])

    students_collection.create_index([("email",     ASCENDING)], unique=True, sparse=True)
    parents_collection.create_index( [("email",     ASCENDING)], unique=True, sparse=True)
    admins_collection.create_index(  [("email",     ASCENDING)], unique=True, sparse=True)

create_indexes()


# ─────────────────────────────────────
# STUDENT FUNCTIONS
# ─────────────────────────────────────
def create_student(student_id, name, parent_id, email):
    students_collection.insert_one({
        "_id":        student_id,
        "name":       name,
        "parent_id":  parent_id,
        "email":      email,
        "created_at": int(datetime.datetime.now().timestamp()),
    })


def get_student(student_id):
    return students_collection.find_one({"_id": student_id})


# ─────────────────────────────────────
# SESSION FUNCTIONS
# ─────────────────────────────────────
def start_session(student_id):
    session = {
        "student_id": student_id,
        "start_time": int(datetime.datetime.now().timestamp()),
        "end_time":   None,
        "status":     "ACTIVE",
    }
    result = sessions_collection.insert_one(session)
    return str(result.inserted_id)


def end_session(student_id):
    sessions_collection.update_one(
        {"student_id": student_id, "status": "ACTIVE"},
        {"$set": {
            "status":   "ENDED",
            "end_time": int(datetime.datetime.now().timestamp()),
        }},
    )


# ─────────────────────────────────────
# ATTENTION LOG FUNCTIONS
# ─────────────────────────────────────
def log_attention(data):
    attention_collection.insert_one(data)


def get_latest_attention(student_id):
    return attention_collection.find_one(
        {"student_id": student_id},
        sort=[("timestamp", DESCENDING)],
    )


def get_attention_trend(student_id, limit=20):
    return list(
        attention_collection.find({"student_id": student_id})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )


# ─────────────────────────────────────
# ALERT FUNCTIONS
# ─────────────────────────────────────
def create_alert(student_id, score, screenshot):
    alerts_collection.insert_one({
        "student_id": student_id,
        "type":       "Low Attention",
        "score":      score,
        "timestamp":  int(datetime.datetime.now().timestamp()),
        "screenshot": screenshot,
        "resolved":   False,
    })


def get_alerts(student_id):
    return list(alerts_collection.find({"student_id": student_id}))


# ─────────────────────────────────────
# ADMIN METRICS
# ─────────────────────────────────────
def get_admin_metrics():
    total_students = students_collection.count_documents({})
    total_alerts   = alerts_collection.count_documents({})
    logs           = list(attention_collection.find())
    avg_attention  = (
        sum(l["attention_score"] for l in logs) / len(logs) if logs else 0
    )
    return {
        "total_students": total_students,
        "alerts_today":   total_alerts,
        "avg_attention":  avg_attention,
    }
