from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sqlite3
import json
import os
from datetime import datetime, timedelta
import random

from .config import DB_PATH, SCHEMA_PATH, UPLOAD_DIR, USE_REAL_LLM
from .database import get_db, init_db, dict_row, dict_rows

# ── Mock 数据（保持与原有 server.py 兼容）──────────
COMPANIES = [
    ("字节跳动", "互联网"), ("阿里巴巴", "互联网"), ("腾讯", "互联网"),
    ("百度", "互联网"), ("华为", "互联网"), ("网易", "互联网"),
    ("拼多多", "互联网"), ("宁德时代", "制造业"), ("比亚迪", "制造业"),
    ("大疆", "制造业"), ("格力", "制造业"), ("美的", "制造业"),
    ("三一重工", "制造业"), ("招商银行", "金融"), ("中信证券", "金融"),
    ("平安科技", "金融"), ("蚂蚁集团", "金融"), ("京东科技", "金融"),
    ("微众银行", "金融"), ("好未来", "教育"), ("新东方", "教育"),
    ("高途", "教育"), ("猿辅导", "教育"), ("学而思", "教育"),
    ("迈瑞医疗", "医疗"), ("恒瑞医药", "医疗"), ("药明康德", "医疗"),
    ("联影医疗", "医疗"), ("华大基因", "医疗"), ("麦肯锡", "咨询"),
    ("波士顿咨询", "咨询"), ("贝恩", "咨询"), ("罗兰贝格", "咨询"),
    ("安永", "咨询"), ("宝洁", "快消"), ("联合利华", "快消"),
    ("玛氏", "快消"), ("百事", "快消"), ("可口可乐", "快消"),
    ("欧莱雅", "快消"),
]

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
REC_TYPES = ["daily_intern", "summer_intern", "autumn_recruit", "spring_recruit", "experienced"]
PLATFORMS = ["official", "boss_zhipin", "xiaohongshu", "wechat_public"]
SALARY = ["15k-25k", "20k-35k", "25k-40k", "30k-50k", "18k-28k", "22k-32k", "12k-20k", "35k-55k"]
JOB_TITLES = [
    "数据分析师", "产品经理", "算法工程师", "后端开发工程师", "前端开发工程师",
    "运营专员", "市场推广经理", "HRBP", "软件测试工程师", "UI/UX设计师",
    "机器学习工程师", "数据挖掘工程师", "商业分析师", "战略分析师", "项目经理",
    "销售经理", "品牌经理", "供应链管理", "财务分析师", "投资者关系",
]
JD_SKILLS = [
    "Python", "SQL", "Excel", "Tableau", "机器学习", "深度学习", "PyTorch",
    "TensorFlow", "Spark", "Hadoop", "Docker", "Kubernetes", "AWS", "GCP",
    "React", "Vue", "TypeScript", "Node.js", "Go", "Java", "Spring Boot",
    "数据分析", "AB测试", "统计学", "Power BI", "Figma", "产品设计",
    "项目管理", "敏捷开发", "沟通能力", "团队协作", "英语流利",
    "市场营销", "SEO", "SEM", "内容运营", "用户增长",
]

PLATFORM_LABELS = {
    "official": "企业官网", "boss_zhipin": "Boss直聘",
    "xiaohongshu": "小红书", "wechat_public": "微信公众号",
}

MOCK_USER_SKILLS = {"python", "sql", "机器学习", "数据可视化", "统计学", "excel", "tableau", "a/b测试"}
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
MOCK_BREAKERS = ["纯开发岗", "24小时on-call", "无明确晋升路径"]

COMPANY_INFO = {
    "字节跳动": {"funding": "Pre-IPO (估值$268B)", "scale": "100,000+人", "position": "全球最大独角兽企业之一", "news": "2025年海外TikTok Shop GMV突破$500亿", "culture": ["扁平化管理", "快速迭代", "数据驱动", "技术信仰"]},
    "阿里巴巴": {"funding": "纽交所+港交所上市", "scale": "200,000+人", "position": "中国电商与云计算双巨头", "news": "2025Q1云业务营收同比增长6%", "culture": ["客户第一", "拥抱变化", "团队合作", "激情"]},
    "腾讯": {"funding": "港交所上市", "scale": "100,000+人", "position": "中国社交与游戏领域龙头", "news": "2025年混元大模型全面接入微信生态", "culture": ["用户为本", "科技向善", "开放协作", "创新突破"]},
}

random.seed(42)

def gen_jd(title, company, industry):
    skills = random.sample(JD_SKILLS, random.randint(4, 8))
    jd = f"""【岗位描述】
{company}正在寻找一位优秀的{title}加入我们的团队。

【岗位职责】
1. 负责{title}相关的日常工作，参与核心业务决策
2. 与跨职能团队协作，推动项目落地执行
3. 分析业务数据，提出优化建议和解决方案
4. 跟踪行业动态，持续提升专业能力

【任职要求】
1. 本科及以上学历，计算机/统计/数学等相关专业优先
2. 熟悉{'、'.join(skills[:3])}等技术工具
3. 具备良好的逻辑思维和数据分析能力
4. 优秀的沟通表达和团队协作能力
5. 有相关实习或项目经验者优先

【加分项】
- 有{'/'.join(skills[3:5])}经验
- 了解行业前沿趋势
- 有开源项目或竞赛经历"""
    return jd, skills

def gen_jd_profile(skills):
    return {
        "knowledge": [s for s in skills if s in ["Python", "SQL", "统计学", "机器学习"]],
        "skills": skills,
        "abilities": [s for s in skills if s in ["项目管理", "沟通能力", "团队协作"]],
        "values": ["数据驱动", "结果导向", "快速迭代", "团队合作"],
    }

def seed_database(db: sqlite3.Connection):
    """向数据库写入 40 条 mock 岗位（幂等：先清空再写入）"""
    for t in ["feedback", "match_records", "applications", "resume", "jobs"]:
        db.execute(f"DELETE FROM {t}")
    db.commit()

    now = datetime.now()
    post_dates = (
        [(now - timedelta(hours=random.randint(1, 23))).strftime("%Y-%m-%dT%H:%M:%S") for _ in range(6)] +
        [(now - timedelta(days=1, hours=random.randint(1, 23))).strftime("%Y-%m-%dT%H:%M:%S") for _ in range(8)] +
        [(now - timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%dT%H:%M:%S") for _ in range(12)] +
        [(now - timedelta(days=random.randint(8, 30))).strftime("%Y-%m-%dT%H:%M:%S") for _ in range(14)]
    )
    random.shuffle(post_dates)

    for i in range(40):
        company, industry = COMPANIES[i % len(COMPANIES)]
        title = random.choice(JOB_TITLES)
        city = random.choice(CITIES)
        rectype = random.choice(REC_TYPES)
        platform = random.choice(PLATFORMS)
        salary = random.choice(SALARY)
        posted_str = post_dates[i]
        posted_dt = datetime.strptime(posted_str, "%Y-%m-%dT%H:%M:%S")
        dl = (posted_dt + timedelta(days=random.choice([3, 7, 14, 21, 30]))).strftime("%Y-%m-%d")
        jd_text, skills = gen_jd(title, company, industry)
        jd_profile = gen_jd_profile(skills)

        db.execute(
            """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
               recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
               application_deadline, posted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, ?)""",
            (title, company, jd_text, json.dumps(skills, ensure_ascii=False),
             json.dumps(jd_profile, ensure_ascii=False), city, salary,
             rectype, industry, platform,
             f"https://www.example.com/jobs/{company}/{i+1}", dl, posted),
        )
    db.commit()
    return 40

def run_match_for_all(db: sqlite3.Connection):
    """对所有岗位运行三圈匹配（基于规则的真实计算版，零成本，可解释）"""
    db.execute("DELETE FROM match_records")
    jobs = db.execute("SELECT * FROM jobs").fetchall()

    # 用户兴趣维度向量（关键词 + 权重）
    interest_keywords = {
        "互联网": 1.0, "金融科技": 0.9, "人工智能": 0.95,
        "数据": 0.9, "产品": 0.85, "算法": 0.85, "分析": 0.9,
        "电商": 0.7, "游戏": 0.7, "教育": 0.6, "医疗": 0.55,
    }
    # 用户技能集合（来自简历画像）
    user_skills = {s.lower() for s in MOCK_ABILITY["skills"]}  # 8个技能
    preferred_industries = set(i.lower() for i in MOCK_INTEREST["preferred_industries"])
    preferred_roles = set(r.lower() for r in MOCK_INTEREST["preferred_roles"])

    for job in jobs:
        jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
        jd_set = set(s.lower() for s in jd_skills)
        job_industry = (job["industry"] or "").lower()
        job_title = (job["title"] or "").lower()
        job_city = (job["city"] or "").lower()
        job_salary = job["salary_range"] or ""

        # ── 1. 兴趣圈：行业 + 角色 + 公司文化偏好 ──
        interest_base = 40.0
        # 行业匹配
        industry_hit = sum(w for k, w in interest_keywords.items() if k in job_industry)
        if any(ind in job_industry for ind in preferred_industries):
            industry_hit += 0.3
        interest_base += industry_hit * 30  # 最高 +30
        # 角色匹配
        role_hit = sum(w for k, w in interest_keywords.items() if k in job_title)
        if any(role in job_title for role in preferred_roles):
            role_hit += 0.25
        interest_base += role_hit * 20  # 最高 +20
        # 城市偏好（一线城市加成）
        city_bonus = 5 if job_city in ("北京", "上海", "深圳", "杭州") else 2 if job_city in ("广州", "成都", "武汉") else 0
        interest_score = min(round(interest_base + city_bonus), 98)

        # ── 2. 能力圈：纯 Jaccard 技能相似度（去随机化）──
        sj = jaccard(user_skills, jd_set)
        # 若技能有交叉，加分；无交叉但有相近领域，给基础分
        if sj > 0:
            ability_score = round(sj * 95 + 5)  # Jaccard→[5, 100]
        else:
            # 无直接技能交集时，用行业关键词模糊匹配给基础分
            fuzzy_hit = sum(0.08 for k in interest_keywords if k in job_title or k in job_industry)
            ability_score = round(15 + fuzzy_hit * 40)  # [15, ~50]

        # ── 3. 市场圈：基于岗位客观数据的市场价值评估 ──
        market_base = 45.0
        # 薪资档位（提取数字范围估算）
        salary_level = 0
        try:
            nums = [int(n.replace("k", "").replace("K", "")) for n in job_salary.split("-") if n.replace("k","").replace("K","").strip().isdigit()]
            if nums: salary_level = sum(nums) / len(nums)  # 平均k数
        except: pass
        if salary_level >= 30: market_base += 20
        elif salary_level >= 20: market_base += 15
        elif salary_level >= 10: market_base += 8
        # 公司规模加成
        if job["company"] in COMPANY_INFO: market_base += 10
        # 招聘类型加成（社招>秋招>春招>实习）
        type_weights = {"experienced": 18, "autumn_recruit": 12, "spring_recruit": 8, "daily_intern": 5, "summer_intern": 6}
        market_base += type_weights.get(job["recruitment_type"], 5)
        # 一线城市加成
        if city_bonus >= 5: market_base += 5
        market_score = min(round(market_base), 98)

        # ── 4. 综合分：加权平均（能力50% + 兴趣25% + 市场25%）──
        overlap_score = round(ability_score * 0.50 + interest_score * 0.25 + market_score * 0.25)

        # ── 5. 可解释匹配理由 ──
        reasons = []
        matched_skills = user_skills & jd_set
        if matched_skills:
            reasons.append("【技能匹配】" + "、".join(sorted(matched_skills)[:4]) + "等" + str(len(matched_skills)) + "项技能与岗位要求吻合")
        missing_skills = jd_set - user_skills
        if missing_skills and len(missing_skills) <= 4:
            reasons.append("【能力差距】建议补充" + "、".join(sorted(missing_skills)[:3]) + "等技能以提升竞争力")
        if industry_hit > 0.5:
            reasons.append("【兴趣匹配】该岗位所在行业与您的职业兴趣高度契合")
        elif industry_hit > 0.1:
            reasons.append("【兴趣相关】岗位方向与您的偏好有一定关联")
        if market_score >= 75:
            reasons.append("【市场看好】该岗位薪资与行业前景表现优秀")
        elif market_score >= 60:
            reasons.append("【市场适中】岗位在行业中有稳定需求")
        if not reasons:
            reasons.append("综合匹配度达标")

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        db.execute(
            """INSERT INTO match_records (job_id, interest_score, ability_score, market_score,
               overlap_score, match_reasons, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (job["id"], interest_score, ability_score, market_score, overlap_score,
             "\n".join(reasons), now),
        )
    db.commit()

def jaccard(a: set, b: set) -> float:
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

# ── FastAPI 应用 ────────────────────────────────────────
app = FastAPI(title="JobMatch AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    db = get_db()
    job_count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    db.close()
    if job_count == 0:
        print("[Init] Seeding database...")
        db2 = get_db()
        seed_database(db2)
        run_match_for_all(db2)
        db2.close()
        print("[Init] 40 mock jobs seeded and matched")

# ── Health ──────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "db": Path(DB_PATH).exists()}

# ── Seed ────────────────────────────────────────────────
@app.post("/api/seed")
def seed():
    db = get_db()
    cnt = seed_database(db)
    run_match_for_all(db)
    db.close()
    return {"success": True, "jobs_seeded": cnt, "resume": MOCK_ABILITY["skills"]}

# ── 求职日报 API ──────────────────────────────────────
@app.get("/api/daily-report")
def daily_report():
    """零成本求职日报：基于本地数据聚合生成，无需LLM"""
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # 今日新增岗位
    today_jobs = db.execute(
        "SELECT COUNT(*) FROM jobs WHERE date(posted_at) = ?", (today,)
    ).fetchone()[0]

    # 匹配分数分布
    dist_rows = db.execute(
        """SELECT CASE
            WHEN overlap_score >= 80 THEN '80-100'
            WHEN overlap_score >= 60 THEN '60-79'
            ELSE '0-59'
        END as tier, COUNT(*) as cnt
        FROM match_records GROUP BY tier ORDER BY tier"""
    ).fetchall()

    # 本周投递统计
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    app_stats = db.execute(
        "SELECT status, COUNT(*) as cnt FROM applications WHERE date(created_at) >= ? GROUP BY status",
        (week_start,)
    ).fetchall()

    # 技能缺口Top5（找出JD中最多出现但用户不拥有的技能）
    resume_row = db.execute("SELECT ability_profile FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
    user_skills_set = set()
    if resume_row:
        ability = json.loads(resume_row["ability_profile"])
        user_skills_set = set(s.lower() for s in ability.get("skills", []))

    skill_gaps = db.execute("SELECT jd_skills FROM jobs").fetchall()
    gap_count: dict[str, int] = {}
    for row in skill_gaps:
        skills = json.loads(row["jd_skills"]) if isinstance(row["jd_skills"], str) else (row["jd_skills"] or [])
        for s in skills:
            sl = s.lower()
            if sl not in user_skills_set:
                gap_count[s] = gap_count.get(s, 0) + 1

    top_gaps = sorted(gap_count.items(), key=lambda x: x[1], reverse=True)[:5]

    # 本周推荐行动
    actions = []
    total_match = db.execute("SELECT COUNT(*) FROM match_records WHERE overlap_score >= 60").fetchone()[0]
    if total_match > 0:
        top_match = db.execute(
            "SELECT j.title, j.company, m.overlap_score FROM match_records m JOIN jobs j ON m.job_id = j.id WHERE m.overlap_score >= 75 ORDER BY m.overlap_score DESC LIMIT 1"
        ).fetchone()
        if top_match:
            actions.append("🔥 最佳匹配：「" + top_match["title"] + "」(" + top_match["company"] + ")，综合分 " + str(top_match["overlap_score"]) + "，建议优先投递")
    if top_gaps:
        actions.append("📚 技能提升建议：学习 " + top_gaps[0][0] + "（" + str(top_gaps[0][1]) + " 个岗位要求）")
    recent_apps = db.execute("SELECT COUNT(*) FROM applications WHERE date(created_at) >= ?", (week_start,)).fetchone()[0]
    if recent_apps == 0:
        actions.append("📋 本周尚未投递，建议从精选推荐中选出 Top3 投递")
    elif recent_apps < 3:
        actions.append("📋 本周投递 " + str(recent_apps) + " 次，建议保持每天 1-2 个投递节奏")
    if not actions:
        actions.append("✅ 整体进展良好，继续保持")

    db.close()
    return {
        "date": today,
        "today_new_jobs": today_jobs,
        "score_distribution": dict_rows(dist_rows),
        "weekly_applications": dict_rows(app_stats),
        "top_skill_gaps": [{"skill": s, "demand_count": c} for s, c in top_gaps],
        "recommended_actions": actions,
        "total_matched": total_match,
    }

# ── Jobs: 全部岗位（含去重逻辑）────────────────────
@app.get("/api/jobs/all")
def get_all_jobs(
    page: int = Query(1),
    page_size: int = Query(20),
    platform: str = Query(""),
    type: str = Query(""),
    search: str = Query(""),
):
    """
    全部岗位列表，按 (company, title) 去重（同一公司同一岗位只展示最新的一条）
    使用子查询兼容所有 SQLite 版本（不依赖 window function）
    """
    conditions = []
    vals = []

    if platform:
        conditions.append("source_platform = ?")
        vals.append(platform)
    if type:
        conditions.append("recruitment_type = ?")
        vals.append(type)
    if search:
        conditions.append("(title LIKE ? OR company LIKE ? OR jd_text LIKE ?)")
        s = f"%{search}%"
        vals.extend([s, s, s])

    where = " AND ".join(conditions) if conditions else "1=1"

    db = get_db()
    # 去重：同一 (company, title) 只保留 posted_at 最新的一条
    # 兼容旧版 SQLite：用子查询 + GROUP BY
    dedup_sql = f"""
        SELECT t.id FROM jobs t
        INNER JOIN (
            SELECT company, title, MAX(posted_at) as max_posted
            FROM jobs
            WHERE {where}
            GROUP BY company, title
        ) dup ON t.company = dup.company AND t.title = dup.title AND t.posted_at = dup.max_posted
    """

    all_ids_rows = db.execute(dedup_sql, vals).fetchall()
    all_ids = [r["id"] for r in all_ids_rows]
    total = len(all_ids)

    offset = (page - 1) * page_size
    page_ids = all_ids[offset:offset + page_size]

    rows = []
    if page_ids:
        placeholders = ",".join(["?"] * len(page_ids))
        rows = db.execute(
            f"SELECT * FROM jobs WHERE id IN ({placeholders}) ORDER BY posted_at DESC",
            page_ids
        ).fetchall()

    db.close()
    return {
        "items": dict_rows(rows),
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": offset + page_size < total,
    }

# ── Jobs: 搜索 ────────────────────────────────────────
@app.get("/api/jobs/search")
def search_jobs(q: str = Query(""), page: int = Query(1)):
    db = get_db()
    s = f"%{q}%"
    total_row = db.execute(
        "SELECT COUNT(*) FROM jobs WHERE title LIKE ? OR company LIKE ? OR jd_text LIKE ?",
        (s, s, s)
    ).fetchone()
    total = total_row[0] if total_row else 0
    offset = (page - 1) * 20
    rows = db.execute(
        "SELECT * FROM jobs WHERE title LIKE ? OR company LIKE ? OR jd_text LIKE ? ORDER BY posted_at DESC LIMIT 20 OFFSET ?",
        (s, s, s, offset)
    ).fetchall()
    db.close()
    return {"items": dict_rows(rows), "total": total}

# ── Job Detail ─────────────────────────────────────────
@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: int):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        db.close()
        raise HTTPException(status_code=404, detail="not found")
    result = dict(job)
    match = db.execute(
        "SELECT * FROM match_records WHERE job_id = ? ORDER BY created_at DESC LIMIT 1", (job_id,)
    ).fetchone()
    result["match_record"] = dict(match) if match else None
    db.close()
    return result

# ── Similar Jobs ──────────────────────────────────────
@app.get("/api/jobs/{job_id}/similar")
def get_similar_jobs(job_id: int, limit: int = Query(5)):
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        db.close()
        return {"items": []}
    rows = db.execute(
        """SELECT j.*, COALESCE(mr.overlap_score, -1) as overlap
           FROM jobs j LEFT JOIN match_records mr ON j.id = mr.job_id
           WHERE j.id != ?
           ORDER BY CASE WHEN j.company = ? THEN 0 ELSE 1 END,
                    CASE WHEN j.industry = ? THEN 0 ELSE 1 END,
                    CASE WHEN j.city = ? THEN 0 ELSE 1 END,
                    j.posted_at DESC LIMIT ?""",
        (job_id, job["company"], job["industry"], job["city"], limit),
    ).fetchall()
    db.close()
    return {"items": dict_rows(rows)}

# ── Company Info ───────────────────────────────────────
@app.get("/api/jobs/{job_id}/company-info")
def get_company_info(job_id: int):
    db = get_db()
    job = db.execute("SELECT company FROM jobs WHERE id = ?", (job_id,)).fetchone()
    db.close()
    if not job:
        raise HTTPException(status_code=404, detail="not found")
    default_info = {
        "funding": "信息暂缺", "scale": "信息暂缺",
        "position": "信息暂缺", "news": "暂无近期动态", "culture": ["信息暂缺"],
    }
    info = COMPANY_INFO.get(job["company"], default_info)
    return {
        "company": job["company"],
        "funding_stage": info["funding"],
        "employee_scale": info["scale"],
        "industry_position": info["position"],
        "recent_news": info["news"],
        "culture_keywords": info["culture"],
        "disclaimer": "基于公开信息推断，仅供参考",
    }

# ── Featured: 精选推荐（多层过滤漏斗）────────────────
@app.get("/api/featured")
def get_featured(
    page: int = Query(1),
    page_size: int = Query(10),
    min_score: int = Query(60),
    type: str = Query(""),
    industry: str = Query(""),
    city: str = Query(""),
):
    """
    精选推荐 API —— 多层过滤漏斗：
    1. 硬过滤：overlap_score >= min_score
    2. 条件过滤：招聘类型 / 行业 / 城市
    3. 排序：overlap_score DESC（纯交集分，不做新鲜度加权）
    4. 今日新增统计
    """
    conditions = ["mr.overlap_score >= ?"]
    vals = [min_score]

    if type:
        conditions.append("j.recruitment_type = ?")
        vals.append(type)
    if industry:
        conditions.append("j.industry = ?")
        vals.append(industry)
    if city:
        conditions.append("j.city = ?")
        vals.append(city)

    where = " AND ".join(conditions)
    db = get_db()

    total = db.execute(
        f"SELECT COUNT(*) FROM match_records mr JOIN jobs j ON mr.job_id = j.id WHERE {where}", vals
    ).fetchone()[0]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT mr.*, j.title, j.company, j.city, j.salary_range, j.recruitment_type,
                j.industry, j.source_platform, j.source_url, j.posted_at,
                j.application_deadline, j.jd_skills
            FROM match_records mr JOIN jobs j ON mr.job_id = j.id
            WHERE {where} ORDER BY mr.overlap_score DESC LIMIT ? OFFSET ?""",
        vals + [page_size, offset],
    ).fetchall()

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = db.execute(
        f"SELECT COUNT(*) FROM match_records mr JOIN jobs j ON mr.job_id = j.id WHERE {where} AND j.posted_at >= ?",
        vals + [today],
    ).fetchone()[0]

    items = []
    for row in rows:
        d = dict(row)
        fb = db.execute(
            "SELECT * FROM feedback WHERE match_record_id = ? ORDER BY created_at DESC LIMIT 1",
            (d["id"],),
        ).fetchone()
        d["feedback"] = dict(fb) if fb else None
        items.append(d)

    db.close()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "today_new": today_count,
    }

# ── Applications ───────────────────────────────────────
@app.get("/api/applications")
def get_applications(
    status: str = Query(""),
    page: int = Query(1),
    page_size: int = Query(20),
):
    conditions = []
    vals = []
    if status:
        conditions.append("a.status = ?")
        vals.append(status)
    where = " AND ".join(conditions) if conditions else "1=1"

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM applications a WHERE {where}", vals).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
            FROM applications a LEFT JOIN jobs j ON a.job_id = j.id
            WHERE {where} ORDER BY a.applied_at DESC LIMIT ? OFFSET ?""",
        vals + [page_size, offset],
    ).fetchall()
    db.close()
    return {"items": dict_rows(rows), "total": total, "page": page, "page_size": page_size}

@app.post("/api/applications")
def create_application(body: dict):
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    notes = json.dumps(body.get("notes") or {}, ensure_ascii=False)
    db.execute(
        """INSERT INTO applications (job_id, match_record_id, status, notes, applied_at, updated_at)
           VALUES (?, ?, 'applied', ?, ?, ?)""",
        (body["job_id"], body.get("match_record_id"), notes, now, now),
    )
    db.commit()
    app_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    row = db.execute(
        """SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
           FROM applications a LEFT JOIN jobs j ON a.job_id = j.id WHERE a.id = ?""",
        (app_id,),
    ).fetchone()
    db.close()
    return dict(row)

@app.put("/api/applications/{app_id}")
def update_application(app_id: int, body: dict):
    db = get_db()
    updates = []
    vals = []
    if "status" in body:
        updates.append("status = ?")
        vals.append(body["status"])
    if "notes" in body:
        updates.append("notes = ?")
        vals.append(json.dumps(body["notes"], ensure_ascii=False))
    if updates:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        updates.append("updated_at = ?")
        vals.append(now)
        vals.append(app_id)
        db.execute(f"UPDATE applications SET {', '.join(updates)} WHERE id = ?", vals)
        db.commit()
    row = db.execute(
        """SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
           FROM applications a LEFT JOIN jobs j ON a.job_id = j.id WHERE a.id = ?""",
        (app_id,),
    ).fetchone()
    db.close()
    return dict(row) if row else {"error": "not found"}

@app.get("/api/applications/stats")
def get_app_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0] or 0
    by_status_rows = db.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status").fetchall()
    by_status = {r["status"]: r["cnt"] for r in by_status_rows}
    dist_rows = db.execute(
        """SELECT CASE
               WHEN mr.overlap_score < 70 THEN '60-70' WHEN mr.overlap_score < 80 THEN '70-80'
               WHEN mr.overlap_score < 90 THEN '80-90' ELSE '90-100' END as range,
               COUNT(*) as cnt
           FROM applications a LEFT JOIN match_records mr ON a.match_record_id = mr.id
           WHERE mr.overlap_score IS NOT NULL GROUP BY range ORDER BY range"""
    ).fetchall()
    db.close()
    return {
        "total": total, "by_status": by_status,
        "score_distribution": dict_rows(dist_rows),
        "weekly_trend": [
            {"week": "2026-W20", "applied": 5, "offer": 1},
            {"week": "2026-W21", "applied": 8, "offer": 2},
            {"week": "2026-W22", "applied": 3, "offer": 0},
        ],
    }

# ── Resume ─────────────────────────────────────────────
@app.get("/api/resume/profile")
def get_resume_profile():
    db = get_db()
    row = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
    db.close()
    if not row:
        return {"has_resume": False}
    return {
        "has_resume": True,
        "interest_profile": json.loads(row["interest_profile"]),
        "ability_profile": json.loads(row["ability_profile"]),
        "deal_breakers": json.loads(row["deal_breakers"]),
    }

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(None)):
    """简历上传：接收文件并生成三圈画像。零成本模式下使用智能mock（根据文件名微调画像）"""
    # 读取文件内容（用于未来接入真实解析）
    raw_text = ""
    if file:
        try:
            content = await file.read()
            raw_text = content.decode("utf-8", errors="ignore")[:5000]
        except Exception:
            raw_text = f"[二进制文件: {file.filename}, {len(content)} bytes]"

    # 根据文件名微调画像，让不同简历产生不同匹配结果
    interest = dict(MOCK_INTEREST)
    ability = dict(MOCK_ABILITY)
    breakers = list(MOCK_BREAKERS)

    if file and file.filename:
        fname_lower = file.filename.lower()
        # 根据文件名推断方向
        if "前端" in fname_lower or "frontend" in fname_lower:
            ability["skills"] = ["JavaScript", "React", "TypeScript", "CSS", "Vue", "Node.js", "Webpack", "性能优化"]
            interest["preferred_roles"] = ["前端开发", "全栈工程师"]
        elif "后端" in fname_lower or "backend" in fname_lower:
            ability["skills"] = ["Java", "Python", "Go", "MySQL", "Redis", "微服务", "Docker", "Kubernetes"]
            interest["preferred_roles"] = ["后端开发", "架构师"]
        elif "产品" in fname_lower or "pm" in fname_lower:
            ability["skills"] = ["需求分析", "PRD", "数据分析", "SQL", "用户研究", "Axure", "项目管理", "A/B测试"]
            interest["preferred_roles"] = ["产品经理"]
        elif "算法" in fname_lower or "algo" in fname_lower or "ai" in fname_lower:
            ability["skills"] = ["Python", "PyTorch", "TensorFlow", "深度学习", "NLP", "CV", "推荐系统", "统计学"]
            interest["preferred_roles"] = ["算法工程师", "AI研究员"]
        elif "测试" in fname_lower or "qa" in fname_lower or "test" in fname_lower:
            ability["skills"] = ["Selenium", "自动化测试", "Python", "JMeter", "接口测试", "性能测试", "SQL", "CI/CD"]
            interest["preferred_roles"] = ["测试工程师", "QA"]

    db = get_db()
    db.execute("DELETE FROM resume")
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at) VALUES (?, ?, ?, ?, ?)",
        (json.dumps(interest, ensure_ascii=False),
         json.dumps(ability, ensure_ascii=False),
         json.dumps(breakers, ensure_ascii=False),
         raw_text[:200] if raw_text else "暂无解析内容",
         now),
    )
    db.commit()
    run_match_for_all(db)
    db.close()

    return {
        "success": True,
        "interest_profile": interest,
        "ability_profile": ability,
        "deal_breakers": breakers,
        "filename": file.filename if file else None,
        "message": "简历上传成功！已生成三圈画像并完成全量岗位匹配",
    }

# ── Feedback ───────────────────────────────────────────
@app.post("/api/feedback")
def submit_feedback(body: dict):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db = get_db()
    db.execute(
        "INSERT INTO feedback (match_record_id, action, ignore_reason, created_at) VALUES (?, ?, ?, ?)",
        (body["match_record_id"], body["action"], body.get("ignore_reason"), now),
    )
    db.commit()
    db.close()

    changes = []
    reason = body.get("ignore_reason", "")
    action = body["action"]
    if action == "ignored" and reason:
        if reason == "salary_too_low":
            changes.append({"field": "min_salary", "old_value": "原始", "new_value": "× 1.1", "note": "连续3次触发后调整"})
        elif reason == "location_mismatch":
            changes.append({"field": "city_weight", "old_value": "1.0", "new_value": "0.7", "note": "已降低该城市权重"})
        elif reason == "skill_mismatch":
            changes.append({"field": "skill_cluster_weight", "old_value": "1.0", "new_value": "0.8", "note": "已降低该技能簇权重"})
        elif reason == "not_interested":
            changes.append({"field": "interest_score", "old_value": "1.0", "new_value": "0.75", "note": "已降低该行业+类型权重"})
    elif action == "saved":
        changes.append({"field": "interest_score", "old_value": "1.0", "new_value": "1.1", "note": "正向反馈：同公司/同行业加分"})
    return {"success": True, "preference_changes": changes}

@app.get("/api/feedback")
def get_feedback_history(limit: int = Query(20)):
    db = get_db()
    rows = db.execute(
        """SELECT f.*, j.title as job_title, j.company as job_company
           FROM feedback f LEFT JOIN match_records mr ON f.match_record_id = mr.id
           LEFT JOIN jobs j ON mr.job_id = j.id
           ORDER BY f.created_at DESC LIMIT ?""", (limit,)
    ).fetchall()
    db.close()
    return dict_rows(rows)

# ── Sources ────────────────────────────────────────────
@app.get("/api/jobs/sources")
def get_job_sources():
    db = get_db()
    rows = db.execute(
        "SELECT source_platform, COUNT(*) as cnt FROM jobs GROUP BY source_platform ORDER BY cnt DESC"
    ).fetchall()
    sources = []
    for r in rows:
        sources.append({
            "platform": r["source_platform"],
            "count": r["cnt"],
            "label": PLATFORM_LABELS.get(r["source_platform"], r["source_platform"]),
        })
    db.close()
    return {"sources": sources, "all_platforms": list(PLATFORM_LABELS.keys())}

# ── Custom Source ──────────────────────────────────────
@app.post("/api/custom-source")
def add_custom_source(body: dict):
    if not body.get("title") or not body.get("company"):
        raise HTTPException(status_code=400, detail="岗位名称和公司为必填项")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    skills = body.get("skills", [])
    jd_profile = gen_jd_profile(skills) if skills else {"knowledge":[],"skills":[],"abilities":[],"values":[]}

    db = get_db()
    db.execute(
        """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
           recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
           application_deadline, posted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'custom', ?, ?, ?, ?, ?)""",
        (body["title"], body["company"], body.get("jd_text", ""),
         json.dumps(skills, ensure_ascii=False),
         json.dumps(jd_profile, ensure_ascii=False),
         body.get("city", ""), body.get("salary_range", ""),
         body.get("recruitment_type", "experienced"), body.get("industry", "互联网"),
         body.get("source_url", ""), body.get("source_name", "自定义来源"),
         body.get("source_url", ""), dl, now),
    )
    db.commit()
    new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 单岗位匹配
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
    jd_skills_list = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
    jd_set = set(s.lower() for s in jd_skills_list)
    interest_score = random.uniform(55, 95)
    sj = jaccard(MOCK_USER_SKILLS, jd_set)
    ability_score = round((0.5 * sj + 0.5 * random.uniform(0.3, 0.95)) * 100)
    market_score = random.randint(50, 95)
    overlap_score = round((interest_score * ability_score * market_score) ** (1 / 3))
    match_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "INSERT INTO match_records (job_id, interest_score, ability_score, market_score, overlap_score, match_reasons, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (new_id, round(interest_score), ability_score, market_score, overlap_score, "【自定义来源岗位】已纳入匹配系统", match_now),
    )
    db.commit()
    db.close()
    return {"success": True, "job_id": new_id, "message": f"岗位「{body['title']}」已添加并完成匹配"}

# ── Resume Advise & Generate ──────────────────────────
@app.post("/api/resume/advise")
def get_resume_advise(body: dict):
    job_id = body.get("job_id", 0)
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    resume = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
    db.close()
    if not resume:
        raise HTTPException(status_code=400, detail="请先上传简历")

    ability = json.loads(resume["ability_profile"])
    jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
    user_skills = [s.lower() for s in (ability.get("skills") or [])]
    matched = [s for s in jd_skills if any(us == s.lower() or s.lower() in us or us in s.lower() for us in user_skills)]
    missing = [s for s in jd_skills if s not in matched]

    matched_str = "，".join(matched) if matched else ""
    missing_str = "，".join(missing) if missing else ""
    jd_top = "，".join(jd_skills[:5]) if jd_skills else ""
    advices = []
    if matched:
        advices.append({"type": "strength", "title": "已有匹配技能需突出", "content": "你的" + matched_str + "等技能与岗位要求匹配，建议在简历中将这些技能放在显眼位置，并用具体项目数据佐证。", "skills": matched})
    if missing:
        advices.append({"type": "gap", "title": "技能差距需弥补或转化", "content": "岗位要求但你的简历中未体现的技能：" + missing_str + "。建议：1) 如有相关学习经历，补充到简历中；2) 用相近技能进行替代表述；3) 短期内可以通过在线课程快速入门。", "skills": missing})
    advices.append({"type": "project", "title": "项目经历优化建议", "content": "用STAR法则重构项目描述，每个项目突出：业务背景→你的角色→技术方案→量化成果。确保至少有2个项目与岗位行业相关。"})
    advices.append({"type": "keyword", "title": "ATS关键词优化", "content": "确保简历JD中以下关键词自然出现：" + jd_top + "。避免堆砌，在每个项目经历中自然融入2-3个关键词。"})
    advices.append({"type": "format", "title": "简历版式与结构建议", "content": "建议采用「个人信息→求职意向→核心技能→工作/项目经历→教育背景」的结构，一页A4为佳。使用量化数字（如'提升效率30%'）增强说服力。"})

    return {
        "job_title": job["title"], "job_company": job["company"],
        "matched_skills": matched, "missing_skills": missing,
        "match_rate": round(len(matched) / max(len(jd_skills), 1) * 100),
        "advices": advices,
    }

@app.post("/api/resume/generate")
def generate_resume(body: dict):
    job_id = body.get("job_id", 0)
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    resume = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
    db.close()
    if not resume:
        raise HTTPException(status_code=400, detail="请先上传简历")

    ability = json.loads(resume["ability_profile"])
    jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
    user_skills = ability.get("skills") or []
    projects = ability.get("projects") or []
    matched_jd_skills = [s for s in jd_skills if any(us.lower() == s.lower() or s.lower() in us.lower() for us in user_skills)]

    user_skills_str = "，".join(user_skills[:4]) if user_skills else ""
    projects_str = "，".join(projects[:2]) if projects else ""
    matched_jd_str = "，".join(matched_jd_skills[:3]) if matched_jd_skills else ""
    summary = ("拥有" + user_skills_str + "等核心技能的" + job["title"] + "候选人，有"
                + projects_str + "等项目经验，具备扎实的" + matched_jd_str + "能力。")

    related_projects = []
    for p in (projects[:3] if projects else []):
        desc = "在" + str(p) + "中，应用" + "，".join(user_skills[:3]) + "技术，实现了从需求分析到落地的完整链路。"
        related_projects.append({"name": p, "description": desc, "skills_used": user_skills[:3], "result": "项目目标达成率提升XX%，获得团队认可"})

    jd_matched_points = []
    if matched_jd_skills:
        jd_matched_points.append("突出的" + "，".join(matched_jd_skills[:3]) + "技能与岗位要求高度匹配")
    total_jd = max(len(jd_skills), 1)
    pct = round(len(matched_jd_skills) / total_jd * 100)
    jd_matched_points.append(str(len(matched_jd_skills)) + "/" + str(len(jd_skills)) + "项JD技能要求被覆盖，覆盖率" + str(pct) + "%")

    generated_resume = {
        "personal_info": {"name": "[你的姓名]", "phone": "[手机号]", "email": "[邮箱]", "city": job["city"] if job["city"] else "[城市]"},
        "summary": summary,
        "core_skills": list(set(matched_jd_skills + user_skills[:5])),
        "target_job": job["title"],
        "target_company": job["company"],
        "related_projects": related_projects,
        "jd_matched_points": jd_matched_points,
        "optimization_notes": ["已在简历中前置JD匹配最高的技能", "项目描述采用了STAR法则重构", "所有量化指标已加粗突出"],
    }

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db2 = get_db()
    max_ver = db2.execute("SELECT COALESCE(MAX(version), 0) FROM resume_versions WHERE resume_id = ?", (resume["id"],)).fetchone()[0]
    title_str = "针对" + job["company"] + job["title"] + "岗位优化"
    pct = round(len(matched_jd_skills) / max(len(jd_skills), 1) * 100)
    note_str = "基于差距分析自动优化，匹配率" + str(pct) + "%"
    db2.execute(
        """INSERT INTO resume_versions (resume_id, version, content_json, title, target_job_title,
           improvement_notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (resume["id"], max_ver + 1, json.dumps(generated_resume, ensure_ascii=False),
         title_str, job["title"],
         note_str, now),
    )
    db2.commit()
    db2.close()

    return {"success": True, "version": max_ver + 1, "resume": generated_resume,
            "matched_count": len(matched_jd_skills), "total_jd_skills": len(jd_skills),
            "message": "已生成针对" + job["company"] + job["title"] + "的优化简历"}

@app.get("/api/resume/versions")
def get_resume_versions():
    db = get_db()
    rows = db.execute("SELECT * FROM resume_versions ORDER BY created_at DESC LIMIT 10").fetchall()
    db.close()
    return {"versions": dict_rows(rows)}

# ── Interview Prep ─────────────────────────────────────
@app.get("/api/jobs/{job_id}/interview-prep")
def get_interview_prep(job_id: int):
    db = get_db()
    job = db.execute("SELECT title, jd_text FROM jobs WHERE id = ?", (job_id,)).fetchone()
    db.close()
    if not job:
        raise HTTPException(status_code=404, detail="not found")

    jd_text = job["jd_text"] or ""
    title = job["title"]
    directions = []
    if any(kw in jd_text for kw in ["Python", "SQL", "Java", "算法", "开发", "工程"]):
        directions.append({"dimension": "技术栈深入", "label": "技术", "color": "#3B82F6",
            "sample_questions": [f"请描述你在{title}相关项目中使用Python/SQL解决的一个复杂问题", "针对大规模数据处理，你会如何优化查询性能？"],
            "prep_tips": "回顾核心算法和数据结构，准备一个技术深度展示的项目案例"})
    if any(kw in jd_text for kw in ["分析", "数据", "统计"]):
        directions.append({"dimension": "数据分析思维", "label": "分析", "color": "#10B981",
            "sample_questions": ["给我们一个你通过数据分析推动业务决策的例子", "如果产品的关键指标突然下降30%，你如何排查？"],
            "prep_tips": "准备AB测试框架、指标体系搭建的案例，熟悉因果推断基本概念"})
    directions.append({"dimension": "行为面试", "label": "行为", "color": "#8B5CF6",
        "sample_questions": ["请描述一次你与团队成员意见分歧时如何处理的经历", "讲讲你最有成就感的一个项目，你的角色和贡献"],
        "prep_tips": "用STAR法则准备3个核心故事"})
    directions.append({"dimension": "行业认知", "label": "行业", "color": "#F59E0B",
        "sample_questions": ["你对当前行业趋势有什么看法？", "你认为AI技术会如何改变这个行业？"],
        "prep_tips": "阅读最新行业报告，准备2-3个行业见解"})
    if any(kw in jd_text for kw in ["产品", "设计", "系统", "架构"]):
        directions.append({"dimension": "系统设计", "label": "设计", "color": "#06B6D4",
            "sample_questions": ["如何设计一个支持百万用户的产品功能？", "当系统面临高并发压力时，你会如何设计？"],
            "prep_tips": "熟悉系统设计框架：需求澄清→容量估算→API设计→数据模型→架构图"})
    return {"job_id": job_id, "directions": directions[:5]}

# ── Mock Interview ─────────────────────────────────────
@app.post("/api/interview/start")
def start_mock_interview(body: dict):
    job_id = body.get("job_id", 0)
    db = get_db()
    job = db.execute("SELECT title FROM jobs WHERE id = ?", (job_id,)).fetchone()
    db.close()
    questions = [
        {"id": 1, "question": f"请做一个简单的自我介绍，重点突出与{job['title'] if job else '该岗位'}相关的经历。"},
        {"id": 2, "question": f"在{job['title'] if job else '该岗位'}的工作中，你如何处理压力和紧急任务？"},
        {"id": 3, "question": "如果团队中有人不同意你的方案，你会怎么做？"},
        {"id": 4, "question": "你如何保持自己在专业领域的持续学习和成长？"},
        {"id": 5, "question": "你对我们公司和这个岗位有什么了解？为什么想来？"},
    ]
    return {"session_id": random.randint(1000, 9999), "job_title": job["title"] if job else "未知岗位",
            "questions": questions, "total_questions": len(questions)}

@app.post("/api/interview/evaluate")
def evaluate_answer(body: dict):
    score = random.randint(3, 5)
    feedbacks = {3: "回答结构清晰，但可以补充更多具体例子来增强说服力",
                 4: "很好的回答！建议加入量化成果，让面试官更直观地感受你的贡献",
                 5: "优秀！回答全面且有深度，展现了扎实的专业功底和沟通能力"}
    return {"question_id": body.get("question_id", 0), "score": score, "max_score": 5,
            "feedback": feedbacks[score], "completed": body.get("question_id", 0) >= 5}

# ── Interview Review ──────────────────────────────────
@app.post("/api/interview/review")
def submit_interview_review(body: dict):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    ai_analysis = {
        "overall_score": min((body.get("score_self", 0) or 0) * 0.9 + random.uniform(0, 15), 100),
        "score_breakdown": {"technical": random.randint(60, 90), "communication": random.randint(65, 95),
                           "problem_solving": random.randint(60, 90), "culture_fit": random.randint(70, 95)},
        "strengths": ["对技术栈有较好理解，能清晰表达项目经验", "对行业有一定认知，展现了求职诚意"],
        "weaknesses": ["部分技术问题的深度可以进一步提升", "回答时可以更多引用量化数据增强说服力", "对公司的了解可以更深入一些"],
        "key_takeaways": "整体表现良好，体现了较强的学习能力和沟通能力。建议在技术深度和对公司业务理解上继续加强。"
    }
    improvement_advices = [
        {"category": "技术提升", "priority": "high", "action": "深入掌握岗位相关的核心技术框架，准备3个技术深度展示案例", "timeline": "2周内", "resources": "官方文档、技术博客、开源项目贡献"},
        {"category": "项目表达", "priority": "high", "action": "用STAR法则重构每个项目描述，确保3分钟内讲清：背景→挑战→方案→量化成果", "timeline": "1周内", "resources": "录制模拟回答视频自我复盘"},
    ]

    db = get_db()
    db.execute(
        """INSERT INTO interview_reviews (application_id, job_id, review_text, score_self,
           questions_asked, difficult_questions, ai_analysis, improvement_advices,
           strengths, weaknesses, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.get("application_id"), body.get("job_id"), body.get("review_text", ""),
         body.get("score_self", 0),
         json.dumps(body.get("questions_asked", []), ensure_ascii=False),
         body.get("difficult_questions", ""),
         json.dumps(ai_analysis, ensure_ascii=False),
         json.dumps(improvement_advices, ensure_ascii=False),
         json.dumps(ai_analysis["strengths"], ensure_ascii=False),
         json.dumps(ai_analysis["weaknesses"], ensure_ascii=False),
         now),
    )
    db.commit()
    review_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    if body.get("application_id"):
        existing = db.execute("SELECT notes FROM applications WHERE id = ?", (body["application_id"],)).fetchone()
        if existing:
            try: notes = json.loads(existing["notes"]) if isinstance(existing["notes"], str) else (existing["notes"] or {})
            except: notes = {}
            notes["last_interview_review_id"] = review_id
            notes["last_interview_score"] = body.get("score_self", 0)
            db.execute("UPDATE applications SET notes = ?, updated_at = ? WHERE id = ?",
                       (json.dumps(notes, ensure_ascii=False), now, body["application_id"]))
            db.commit()
    db.close()
    return {"success": True, "review_id": review_id, "analysis": ai_analysis, "improvement_advices": improvement_advices}

@app.get("/api/interview/review")
def get_interview_reviews(job_id: int = Query(0)):
    db = get_db()
    if job_id:
        rows = db.execute("SELECT * FROM interview_reviews WHERE job_id = ? ORDER BY created_at DESC LIMIT 5", (job_id,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM interview_reviews ORDER BY created_at DESC LIMIT 10").fetchall()
    db.close()
    return {"reviews": dict_rows(rows)}

@app.post("/api/interview/improvement")
def get_improvement_advice(body: dict):
    db = get_db()
    review = None
    if body.get("review_id"):
        review = db.execute("SELECT * FROM interview_reviews WHERE id = ?", (body["review_id"],)).fetchone()
    elif body.get("job_id"):
        review = db.execute("SELECT * FROM interview_reviews WHERE job_id = ? ORDER BY created_at DESC LIMIT 1", (body["job_id"],)).fetchone()
    if not review:
        db.close()
        raise HTTPException(status_code=404, detail="未找到面试复盘记录")

    ai_analysis = json.loads(review["ai_analysis"]) if isinstance(review["ai_analysis"], str) else review["ai_analysis"]
    weaknesses = json.loads(review["weaknesses"]) if isinstance(review["weaknesses"], str) else review["weaknesses"]
    improvement_advices = json.loads(review["improvement_advices"]) if isinstance(review["improvement_advices"], str) else review["improvement_advices"]
    job = db.execute("SELECT title, company FROM jobs WHERE id = ?", (review["job_id"],)).fetchone() if review["job_id"] else None
    db.close()

    next_steps = {
        "before_next_interview": [
            {"step": 1, "action": "针对薄弱项进行专项训练", "detail": f"重点提升：{', '.join(weaknesses[:2])}", "duration": "3-5天"},
            {"step": 2, "action": "更新简历突出新学习内容", "detail": "将面试中学到的反馈转化为简历关键词", "duration": "1天"},
            {"step": 3, "action": "再次模拟面试", "detail": "针对上次不足的问题类型进行专项模拟", "duration": "2天"},
        ],
        "long_term_growth": ["建立个人技术博客/GitHub项目展示技术深度", "参与行业meetup或线上社区，拓展人脉", "定期复盘每次面试，建立个人面试题库"],
        "resume_update_suggestions": ["在简历中补充面试中暴露的技能短板相关学习经历", "优化项目描述中的量化数据", "添加面试中面试官关注的关键词"],
        "priority_advices": [a for a in improvement_advices if a.get("priority") == "high"],
    }
    return {"review_id": review["id"], "review_score": review["score_self"], "ai_score": ai_analysis.get("overall_score", 0),
            "strengths": json.loads(review["strengths"]) if isinstance(review["strengths"], str) else review["strengths"],
            "weaknesses": weaknesses, "improvement_advices": improvement_advices,
            "next_steps": next_steps, "job_title": job["title"] if job else "", "job_company": job["company"] if job else ""}
