from pydantic import BaseModel, EmailStr
from typing import Optional


# ─────────────────────────────────────────
# Attention data (unchanged)
# ─────────────────────────────────────────
class AttentionData(BaseModel):
    student_id: str
    attention_score: float
    status: str                    # ATTENTIVE | DISTRACTED | NOT PAYING ATTENTION
    eyes_closed: bool
    sleeping: bool
    looking_away: bool
    phone_detected: bool
    timestamp: int                 # Unix ms
    screenshot: Optional[str] = None  # base64 or file path


# ─────────────────────────────────────────
# Auth schemas
# ─────────────────────────────────────────
class StudentSignup(BaseModel):
    name: str
    email: str
    password: str
    parent_email: Optional[str] = None   # links student → parent account


class ParentSignup(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str   # "student" | "parent" | "admin"
