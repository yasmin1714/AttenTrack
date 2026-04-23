from fastapi import APIRouter, Request
from database import attention_collection, alerts_collection
from schemas import AttentionData

router = APIRouter()

_violation_counter = {}
VIOLATION_THRESHOLD = 3


@router.post("/api/attention")
async def receive_attention(data: AttentionData, request: Request):

    payload = data.dict()

    # Save log
    attention_collection.insert_one(payload)

    # Get manager safely
    manager = getattr(request.app.state, "manager", None)

    # Push real-time update
    if manager:
        await manager.push(data.student_id, {
            "type": "attention_update",
            **payload
        })

    # Check violation
    sid = data.student_id
    is_violation = data.phone_detected or data.status == "NOT PAYING ATTENTION"

    if is_violation:
        _violation_counter[sid] = _violation_counter.get(sid, 0) + 1
    else:
        _violation_counter[sid] = 0

    # Trigger alert
    if _violation_counter.get(sid, 0) == VIOLATION_THRESHOLD:

        alert_data = {
            "student_id": sid,
            "type": "Phone Detected" if data.phone_detected else "Low Attention",
            "score": data.attention_score,
            "timestamp": data.timestamp,
            "screenshot": data.screenshot,
            "resolved": False,
        }

        alerts_collection.insert_one(alert_data)

        if manager:
            await manager.push(sid, {
                "type": "alert",
                "alert_type": alert_data["type"],
                "score": alert_data["score"],
                "timestamp": alert_data["timestamp"],
            })

    return {"message": "OK"}