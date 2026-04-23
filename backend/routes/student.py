from fastapi import APIRouter
from database import attention_collection, alerts_collection, students_collection
from pymongo import DESCENDING

router = APIRouter()


def _clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


@router.get("/api/student/{student_id}/live")
def get_live(student_id: str):
    data = attention_collection.find_one(
        {"student_id": student_id},
        sort=[("timestamp", DESCENDING)],
    )
    return _clean(data) if data else {}


@router.get("/api/student/{student_id}/trend")
def get_trend(student_id: str):
    logs = list(
        attention_collection.find({"student_id": student_id})
        .sort("timestamp", -1)
        .limit(20)
    )
    return {"data": [_clean(l) for l in reversed(logs)]}


@router.get("/api/student/{student_id}/alerts")
def get_alerts(student_id: str):
    alerts = list(
        alerts_collection.find({"student_id": student_id})
        .sort("timestamp", -1)
        .limit(20)
    )
    return [_clean(a) for a in alerts]


@router.get("/api/student/{student_id}/status")
def get_status(student_id: str):
    """Returns online/offline status — driven by login/logout calls."""
    user = students_collection.find_one({"student_id": student_id})
    if not user:
        return {"online": False, "name": ""}
    return {
        "online": user.get("online", False),
        "name":   user.get("name", ""),
    }
