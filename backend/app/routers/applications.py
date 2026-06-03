from fastapi import APIRouter, Query
from ..database import database

router = APIRouter()


@router.get("/applications")
async def list_applications(
    status: str = "",
    page: int = 1,
    page_size: int = 20,
):
    conditions = []
    params = {}
    if status:
        conditions.append("a.status = :status")
        params["status"] = status
    where = " AND ".join(conditions) if conditions else "1=1"

    count = await database.fetch_val(
        f"SELECT COUNT(*) FROM applications a WHERE {where}", values=params
    )
    offset = (page - 1) * page_size
    rows = await database.fetch_all(
        f"""
        SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
        FROM applications a LEFT JOIN jobs j ON a.job_id = j.id
        WHERE {where}
        ORDER BY a.applied_at DESC LIMIT :limit OFFSET :offset
        """,
        values={**params, "limit": page_size, "offset": offset},
    )
    return {
        "items": [dict(r) for r in rows],
        "total": count,
        "page": page,
        "page_size": page_size,
    }


@router.post("/applications")
async def create_application(body: dict):
    import json
    from datetime import datetime

    notes = json.dumps(body.get("notes") or {})
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    await database.execute(
        """
        INSERT INTO applications (job_id, match_record_id, status, notes, applied_at, updated_at)
        VALUES (:job_id, :mr_id, 'applied', :notes, :now, :now)
        """,
        values={
            "job_id": body["job_id"],
            "mr_id": body.get("match_record_id"),
            "notes": notes,
            "now": now,
        },
    )
    app_id = await database.fetch_val("SELECT last_insert_rowid()")
    row = await database.fetch_one(
        """
        SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
        FROM applications a LEFT JOIN jobs j ON a.job_id = j.id WHERE a.id = :id
        """,
        values={"id": app_id},
    )
    return dict(row)


@router.put("/applications/{app_id}")
async def update_application(app_id: int, body: dict):
    import json
    from datetime import datetime

    updates = []
    params = {"id": app_id}

    if "status" in body:
        updates.append("status = :status")
        params["status"] = body["status"]
    if "notes" in body:
        updates.append("notes = :notes")
        params["notes"] = json.dumps(body["notes"])
    if updates:
        params["now"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        updates.append("updated_at = :now")
        await database.execute(
            f"UPDATE applications SET {', '.join(updates)} WHERE id = :id", values=params
        )
    row = await database.fetch_one(
        """
        SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
        FROM applications a LEFT JOIN jobs j ON a.job_id = j.id WHERE a.id = :id
        """,
        values={"id": app_id},
    )
    return dict(row) if row else {"error": "not found"}


@router.get("/applications/stats")
async def application_stats():
    total = await database.fetch_val("SELECT COUNT(*) FROM applications") or 0

    by_status_rows = await database.fetch_all(
        "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
    )
    by_status = {r["status"]: r["cnt"] for r in by_status_rows}

    # Score distribution
    dist_rows = await database.fetch_all(
        """
        SELECT
            CASE
                WHEN mr.overlap_score < 70 THEN '60-70'
                WHEN mr.overlap_score < 80 THEN '70-80'
                WHEN mr.overlap_score < 90 THEN '80-90'
                ELSE '90-100'
            END as range,
            COUNT(*) as cnt
        FROM applications a
        LEFT JOIN match_records mr ON a.match_record_id = mr.id
        WHERE mr.overlap_score IS NOT NULL
        GROUP BY range ORDER BY range
        """
    )
    score_distribution = [dict(r) for r in dist_rows] if dist_rows else []

    weekly_trend = [
        {"week": "2026-W20", "applied": 5, "offer": 1},
        {"week": "2026-W21", "applied": 8, "offer": 2},
        {"week": "2026-W22", "applied": 3, "offer": 0},
    ]

    return {"total": total, "by_status": by_status, "score_distribution": score_distribution, "weekly_trend": weekly_trend}
