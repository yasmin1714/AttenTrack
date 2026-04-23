"""
auth.py  –  AttenTrack authentication routes
POST /api/auth/signup/student  – register student (links to parent via parent_email)
POST /api/auth/signup/parent   – register parent
POST /api/auth/login           – login (student | parent | admin)
POST /api/auth/logout          – mark student offline
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import datetime, hashlib, os

from database import (
    students_collection,
    parents_collection,
    admins_collection,
)

router = APIRouter()

# ── helpers ───────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc

# ── schemas ───────────────────────────────────────────────────────────────────
class StudentSignup(BaseModel):
    name: str
    email: str
    password: str
    parent_email: Optional[str] = None   # links student → parent

class ParentSignup(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str   # "student" | "parent" | "admin"


# ── STUDENT SIGNUP ─────────────────────────────────────────────────────────────
@router.post("/api/auth/signup/student")
def student_signup(data: StudentSignup):
    if students_collection.find_one({"email": data.email}):
        return {"success": False, "message": "Email already registered"}

    # Auto-generate a numeric student_id
    count      = students_collection.count_documents({})
    student_id = str(1000 + count + 1)

    # Try to resolve parent_id from parent_email
    parent_id = None
    if data.parent_email:
        parent = parents_collection.find_one({"email": data.parent_email})
        if parent:
            parent_id = str(parent["_id"])

    doc = {
        "student_id":   student_id,
        "name":         data.name,
        "email":        data.email,
        "password":     _hash(data.password),
        "parent_email": data.parent_email or "",
        "parent_id":    parent_id or "",
        "created_at":   int(datetime.datetime.now().timestamp()),
        "online":       False,
    }
    students_collection.insert_one(doc)

    return {
        "success":    True,
        "student_id": student_id,
        "message":    "Student registered successfully",
    }


# ── PARENT SIGNUP ──────────────────────────────────────────────────────────────
@router.post("/api/auth/signup/parent")
def parent_signup(data: ParentSignup):
    if parents_collection.find_one({"email": data.email}):
        return {"success": False, "message": "Email already registered"}

    doc = {
        "name":       data.name,
        "email":      data.email,
        "password":   _hash(data.password),
        "created_at": int(datetime.datetime.now().timestamp()),
    }
    result    = parents_collection.insert_one(doc)
    parent_id = str(result.inserted_id)

    # Back-link any students who registered with this parent_email
    students_collection.update_many(
        {"parent_email": data.email},
        {"$set": {"parent_id": parent_id}},
    )

    return {"success": True, "parent_id": parent_id, "message": "Parent registered"}


# ── LOGIN ──────────────────────────────────────────────────────────────────────
@router.post("/api/auth/login")
def login(data: LoginRequest):
    pw_hash = _hash(data.password)
    role    = data.role.lower()

    if role == "student":
        user = students_collection.find_one(
            {"email": data.email, "password": pw_hash}
        )
        if not user:
            return {"success": False, "message": "Invalid credentials"}

        # Mark student online
        students_collection.update_one(
            {"email": data.email},
            {"$set": {"online": True, "last_login": int(datetime.datetime.now().timestamp())}},
        )
        return {
            "success":    True,
            "role":       "student",
            "student_id": user["student_id"],
            "name":       user["name"],
            "email":      user["email"],
        }

    elif role == "parent":
        user = parents_collection.find_one(
            {"email": data.email, "password": pw_hash}
        )
        if not user:
            return {"success": False, "message": "Invalid credentials"}

        parent_id = str(user["_id"])

        # Find children linked to this parent
        children = list(
            students_collection.find({"parent_id": parent_id}, {"_id": 0})
        )
        student_ids = [c["student_id"] for c in children]

        return {
            "success":     True,
            "role":        "parent",
            "parent_id":   parent_id,
            "name":        user["name"],
            "email":       user["email"],
            "student_ids": student_ids,   # list of child student_ids
            "children":    children,
        }

    elif role == "admin":
        # Check hardcoded admin OR admins_collection
        ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@attentrack.com")
        ADMIN_PASS  = os.getenv("ADMIN_PASSWORD", "admin123")

        if data.email == ADMIN_EMAIL and data.password == ADMIN_PASS:
            return {"success": True, "role": "admin", "name": "Admin"}

        user = admins_collection.find_one(
            {"email": data.email, "password": pw_hash}
        )
        if not user:
            return {"success": False, "message": "Invalid admin credentials"}
        return {"success": True, "role": "admin", "name": user.get("name", "Admin")}

    return {"success": False, "message": "Unknown role"}


# ── LOGOUT ─────────────────────────────────────────────────────────────────────
@router.post("/api/auth/logout/{student_id}")
def logout(student_id: str):
    students_collection.update_one(
        {"student_id": student_id},
        {"$set": {"online": False}},
    )
    return {"success": True}


# ── STUDENT STATUS (online/offline) ──────────────────────────────────────────
@router.get("/api/student/{student_id}/status")
def get_student_status(student_id: str):
    user = students_collection.find_one({"student_id": student_id})
    if not user:
        return {"online": False}
    return {"online": user.get("online", False), "name": user.get("name", "")}
