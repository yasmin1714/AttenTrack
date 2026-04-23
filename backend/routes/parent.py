from fastapi import APIRouter
from database import students_collection, attention_collection

router = APIRouter()


def _clean(doc):
    if doc:
        doc.pop("_id", None)
    return doc


@router.get("/api/parent/{parent_id}/children")
def get_children(parent_id: str):
    students = list(students_collection.find({"parent_id": parent_id}))
    return [_clean(s) for s in students]


@router.get("/api/parent/{parent_id}/student/{student_id}/report")
def get_report(parent_id: str, student_id: str):
    pipeline = [
        {"$match": {"student_id": student_id}},
        {"$group": {
            "_id": None,
            "avg":  {"$avg": "$attention_score"},
            "peak": {"$max": "$attention_score"},
            "low":  {"$min": "$attention_score"},
        }}
    ]
    result = list(attention_collection.aggregate(pipeline))
    if not result:
        return {"avg_score": 0, "peak_score": 0, "lowest_score": 0}

    r = result[0]
    return {
        "avg_score":    round(r["avg"],  1),
        "peak_score":   round(r["peak"], 1),
        "lowest_score": round(r["low"],  1),
    }
