from fastapi import APIRouter, Query
from database import students_collection, attention_collection, alerts_collection
from pymongo import DESCENDING

router = APIRouter()


# ─────────────────────────────────────────
# Existing endpoints (unchanged)
# ─────────────────────────────────────────

@router.get("/api/admin/metrics")
def get_metrics():
    total_students = students_collection.count_documents({})
    alerts_today   = alerts_collection.count_documents({})
    logs           = list(attention_collection.find())

    avg_attention = (
        sum(l["attention_score"] for l in logs) / len(logs) if logs else 0
    )

    return {
        "total_students": total_students,
        "avg_attention":  round(avg_attention, 2),
        "alerts_today":   alerts_today,
    }


@router.get("/api/admin/alerts")
def get_alerts():
    return list(alerts_collection.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(10))


@router.get("/api/admin/students")
def get_students():
    return list(students_collection.find({}, {"_id": 0}))


# ─────────────────────────────────────────
# NEW: system-level attention trend
#
# Returns the rolling average attention score
# across ALL students, bucketed by minute.
#
# Query params:
#   limit  – how many most-recent log entries to
#            include before bucketing (default 300)
#
# Response:
#   { "data": [{ "avg_score": float, "timestamp": int }, ...] }
# ─────────────────────────────────────────

@router.get("/api/admin/attention-trend")
def get_attention_trend(limit: int = Query(default=300, ge=10, le=2000)):
    """
    Compute a per-minute class-wide average attention score.

    Algorithm
    ---------
    1. Pull the <limit> most-recent attention logs from *all* students.
    2. Bucket each log into its minute-level timestamp
       (floor to the nearest 60 000 ms).
    3. Return buckets sorted ascending so the chart reads left → right.
    """
    logs = list(
        attention_collection
        .find({}, {"attention_score": 1, "timestamp": 1, "_id": 0})
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )

    if not logs:
        return {"data": []}

    # ── bucket by minute ──────────────────────────────
    buckets: dict[int, list[float]] = {}
    for log in logs:
        ts    = log.get("timestamp", 0)
        score = log.get("attention_score", 0)

        # timestamps may be in seconds or milliseconds
        # normalise to milliseconds
        if ts < 1_000_000_000_000:   # looks like seconds
            ts = ts * 1000

        minute_bucket = (ts // 60_000) * 60_000   # floor to minute
        buckets.setdefault(minute_bucket, []).append(score)

    # ── compute averages and sort chronologically ─────
    result = [
        {
            "timestamp": bucket_ts,
            "avg_score": round(sum(scores) / len(scores), 2),
        }
        for bucket_ts, scores in sorted(buckets.items())
    ]

    return {"data": result}
