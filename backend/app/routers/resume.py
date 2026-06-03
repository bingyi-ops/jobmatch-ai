from fastapi import APIRouter, UploadFile, File, Form
from ..database import database
import json
import os
from ..config import UPLOAD_DIR

router = APIRouter()

# Mock resume data (in production, parse with LLM)
MOCK_INTEREST = {
    "preferred_industries": ["互联网", "金融科技", "人工智能"],
    "preferred_roles": ["数据分析", "产品经理", "算法工程师"],
    "work_style": ["快节奏", "数据驱动", "结果导向"],
}

MOCK_ABILITY = {
    "skills": ["Python", "SQL", "机器学习", "数据可视化", "统计学", "Excel", "Tableau", "A/B测试"],
    "education": "硕士 | 计算机科学",
    "experience": "2段数据分析实习",
    "projects": ["用户画像建模", "推荐系统优化", "AB实验分析"],
}

MOCK_DEALBREAKERS = ["纯开发岗", "24小时on-call", "无明确晋升路径"]

@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(None)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if file and file.filename:
        content = await file.read()
        fpath = os.path.join(UPLOAD_DIR, file.filename)
        with open(fpath, "wb") as f:
            f.write(content)

    # Delete old resume
    await database.execute("DELETE FROM resume")

    interest_json = json.dumps(MOCK_INTEREST, ensure_ascii=False)
    ability_json = json.dumps(MOCK_ABILITY, ensure_ascii=False)
    breakers_json = json.dumps(MOCK_DEALBREAKERS, ensure_ascii=False)

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    await database.execute(
        "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, embedding_json, raw_parsed, created_at) VALUES (:ip, :ap, :db, '[]', 'mock', :now)",
        values={"ip": interest_json, "ap": ability_json, "db": breakers_json, "now": now},
    )

    # Trigger match engine for all jobs
    from ..services.match_engine import run_match
    await run_match()

    return {
        "success": True,
        "interest_profile": MOCK_INTEREST,
        "ability_profile": MOCK_ABILITY,
        "deal_breakers": MOCK_DEALBREAKERS,
        "message": "简历解析成功！已生成三圈画像并完成40个岗位匹配",
    }


@router.get("/resume/profile")
async def get_profile():
    row = await database.fetch_one("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1")
    if not row:
        return {"has_resume": False}
    interest = json.loads(row["interest_profile"])
    ability = json.loads(row["ability_profile"])
    breakers = json.loads(row["deal_breakers"])
    return {"has_resume": True, "interest_profile": interest, "ability_profile": ability, "deal_breakers": breakers}

