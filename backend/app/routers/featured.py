from fastapi import APIRouter, Query
from ..database import database

router = APIRouter()


@router.get("/featured")
async def get_featured(
    page: int = 1,
    page_size: int = 10,
    min_score: int = 60,
    type: str = "",
    industry: str = "",
    city: str = "",
):
    conditions = ["mr.overlap_score >= :min_score"]
    params = {"min_score": min_score}

    if type:
        conditions.append("j.recruitment_type = :type")
        params["type"] = type
    if industry:
        conditions.append("j.industry = :industry")
        params["industry"] = industry
    if city:
        conditions.append("j.city = :city")
        params["city"] = city

    where = " AND ".join(conditions)

    count = await database.fetch_val(
        f"SELECT COUNT(*) FROM match_records mr JOIN jobs j ON mr.job_id = j.id WHERE {where}",
        values=params,
    )

    offset = (page - 1) * page_size
    rows = await database.fetch_all(
        f"""
        SELECT mr.*, j.title, j.company, j.city, j.salary_range, j.recruitment_type,
               j.industry, j.source_platform, j.source_url, j.posted_at,
               j.application_deadline, j.jd_skills
        FROM match_records mr JOIN jobs j ON mr.job_id = j.id
        WHERE {where}
        ORDER BY mr.overlap_score DESC
        LIMIT :limit OFFSET :offset
        """,
        values={**params, "limit": page_size, "offset": offset},
    )

    # Count today's new
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = await database.fetch_val(
        f"SELECT COUNT(*) FROM match_records mr JOIN jobs j ON mr.job_id = j.id WHERE {where} AND j.posted_at >= :today",
        values={**params, "today": today},
    )

    jobs = []
    for row in rows:
        d = dict(row)
        # Check if saved or ignored
        fb = await database.fetch_one(
            "SELECT * FROM feedback WHERE match_record_id = :mid ORDER BY created_at DESC LIMIT 1",
            values={"mid": d["id"]},
        )
        d["feedback"] = dict(fb) if fb else None
        jobs.append(d)

    return {
        "items": jobs,
        "total": count,
        "page": page,
        "page_size": page_size,
        "today_new": today_count,
    }
