from fastapi import APIRouter
from ..database import database
from datetime import datetime

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(body: dict):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    await database.execute(
        "INSERT INTO feedback (match_record_id, action, ignore_reason, created_at) VALUES (:mid, :action, :reason, :now)",
        values={
            "mid": body["match_record_id"],
            "action": body["action"],
            "reason": body.get("ignore_reason"),
            "now": now,
        },
    )

    changes = []
    reason = body.get("ignore_reason", "")
    action = body["action"]

    if action == "ignored" and reason:
        if reason == "salary_too_low":
            changes.append({"field": "min_salary", "old_value": "原始", "new_value": "× 1.1", "note": "连续3次同类型触发"})
        elif reason == "location_mismatch":
            changes.append({"field": "city_weight", "old_value": "1.0", "new_value": "0.7", "note": "已降低该城市权重"})
        elif reason == "skill_mismatch":
            changes.append({"field": "skill_cluster_weight", "old_value": "1.0", "new_value": "0.8", "note": "已降低该技能簇权重"})
        elif reason == "not_interested":
            changes.append({"field": "interest_score", "old_value": "1.0", "new_value": "0.75", "note": "已降低该行业+招聘类型权重"})
    elif action == "saved":
        changes.append({"field": "interest_score", "old_value": "1.0", "new_value": "1.1", "note": "正向反馈：同公司/同行业加分"})

    return {"success": True, "preference_changes": changes}


@router.get("/feedback/history")
async def feedback_history(limit: int = 20):
    rows = await database.fetch_all(
        """
        SELECT f.*, j.title as job_title, j.company as job_company
        FROM feedback f
        LEFT JOIN match_records mr ON f.match_record_id = mr.id
        LEFT JOIN jobs j ON mr.job_id = j.id
        ORDER BY f.created_at DESC LIMIT :limit
        """,
        values={"limit": limit},
    )
    return [dict(r) for r in rows]
