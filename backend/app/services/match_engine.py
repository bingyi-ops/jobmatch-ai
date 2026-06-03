import json
import random
from datetime import datetime
from ..database import database

# Skill Jaccard similarity
def jaccard(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


async def run_match():
    """Run match engine for all jobs against the current resume profile."""
    # Get resume
    resume = await database.fetch_one("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1")
    if not resume:
        return

    interest_profile = json.loads(resume["interest_profile"])
    ability_profile = json.loads(resume["ability_profile"])
    user_skills = set(s.lower() for s in ability_profile.get("skills", []))

    # Get all jobs
    jobs = await database.fetch_all("SELECT * FROM jobs")
    random.seed(42)

    # Clear old match records
    await database.execute("DELETE FROM match_records")

    for job in jobs:
        jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
        jd_skill_set = set(s.lower() for s in jd_skills)

        # interest_score: mock LLM semantic match (60-95)
        interest_score = random.uniform(55, 95)

        # ability_score: 0.5*Jaccard + 0.5*random cosine mock
        skill_jaccard = jaccard(user_skills, jd_skill_set)
        cosine_mock = random.uniform(0.3, 0.95)
        ability_score = round((0.5 * skill_jaccard + 0.5 * cosine_mock) * 100)

        # market_score: mock 4-dim match
        market_score = random.randint(50, 95)

        overlap_score = round((interest_score * ability_score * market_score) ** (1 / 3))

        # Only store if above threshold
        if overlap_score >= 60:
            reasons = generate_mock_reasons(interest_score, ability_score, market_score)
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            await database.execute(
                """
                INSERT INTO match_records (job_id, interest_score, ability_score, market_score, overlap_score, match_reasons, is_filtered, created_at)
                VALUES (:jid, :interest, :ability, :market, :overlap, :reasons, 0, :now)
                """,
                values={
                    "jid": job["id"],
                    "interest": round(interest_score),
                    "ability": ability_score,
                    "market": market_score,
                    "overlap": overlap_score,
                    "reasons": reasons,
                    "now": now,
                },
            )


def generate_mock_reasons(interest, ability, market) -> str:
    parts = []
    if interest >= 80:
        parts.append("【兴趣匹配度高】行业方向与您的职业兴趣高度契合")
    elif interest >= 60:
        parts.append("【兴趣适中】岗位方向与您的偏好有一定关联")

    if ability >= 80:
        parts.append("【技能匹配优秀】您的核心技能与岗位要求高度一致")
    elif ability >= 60:
        parts.append("【技能部分匹配】部分技能符合要求，可针对性提升")

    if market >= 80:
        parts.append("【市场需求旺盛】该岗位符合行业发展趋势，前景良好")
    elif market >= 60:
        parts.append("【市场机会适中】岗位在行业中有一定需求")

    return "\n".join(parts) if parts else "综合匹配度达标"
