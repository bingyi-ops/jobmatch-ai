"""
JobMatch AI - 纯 Python 标准库后端 (零外部依赖)
启动: python server.py
"""
import json
import sqlite3
import os
import re
import random
import math
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "jobmatch.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

random.seed(42)

# ─────────────────── Database ───────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            db.execute(stmt)
    db.commit()
    db.close()

def dict_row(row) -> dict:
    if row is None:
        return None
    return dict(row)

def dict_rows(rows) -> list:
    return [dict(r) for r in rows]

# ─────────────────── Seed Data ───────────────────

COMPANIES = [
    ("字节跳动", "互联网"), ("阿里巴巴", "互联网"), ("腾讯", "互联网"),
    ("百度", "互联网"), ("华为", "互联网"), ("网易", "互联网"),
    ("拼多多", "互联网"), ("宁德时代", "制造业"), ("比亚迪", "制造业"),
    ("大疆", "制造业"), ("格力", "制造业"), ("美的", "制造业"),
    ("三一重工", "制造业"), ("招商银行", "金融"), ("中信证券", "金融"),
    ("平安科技", "金融"), ("蚂蚁集团", "金融"), ("京东金融", "金融"),
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
PLATFORMS = ["official", "boss_zhipin", "xiaohongshu", "wechat_public", "liepin", "lagou", "zhilian", "51job", "shixiseng", "zhihu", "referral", "school_career"]

PLATFORM_LABELS = {
    "official": "企业官网",
    "boss_zhipin": "Boss直聘",
    "xiaohongshu": "小红书",
    "wechat_public": "微信公众号",
    "liepin": "猎聘",
    "lagou": "拉勾",
    "zhilian": "智联招聘",
    "51job": "前程无忧",
    "shixiseng": "实习僧",
    "zhihu": "知乎",
    "referral": "内推/师兄师姐推荐",
    "school_career": "学校就业网",
    "bilibili": "B站",
    "douyin": "抖音",
    "weibo": "微博",
    "custom": "自定义来源",
}
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

def seed_database():
    db = get_db()
    # Clear
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
        posted = post_dates[i]
        posted_dt = datetime.strptime(posted, "%Y-%m-%dT%H:%M:%S")
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
    db.close()
    return 40

# ─────────────────── Match Engine ───────────────────

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

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def run_match_for_all(db):
    """Match all jobs against mock resume profile."""
    db.execute("DELETE FROM match_records")
    jobs = db.execute("SELECT * FROM jobs").fetchall()

    for job in jobs:
        jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
        jd_set = set(s.lower() for s in jd_skills)

        interest_score = random.uniform(55, 95)
        sj = jaccard(MOCK_USER_SKILLS, jd_set)
        ability_score = round((0.5 * sj + 0.5 * random.uniform(0.3, 0.95)) * 100)
        market_score = random.randint(50, 95)
        overlap_score = round((interest_score * ability_score * market_score) ** (1 / 3))

        if overlap_score >= 60:
            reasons = []
            if interest_score >= 80: reasons.append("【兴趣匹配度高】行业方向与您的职业兴趣高度契合")
            elif interest_score >= 60: reasons.append("【兴趣适中】岗位方向与您的偏好有一定关联")
            if ability_score >= 80: reasons.append("【技能匹配优秀】您的核心技能与岗位要求高度一致")
            elif ability_score >= 60: reasons.append("【技能部分匹配】部分技能符合要求，可针对性提升")
            if market_score >= 80: reasons.append("【市场需求旺盛】该岗位符合行业发展趋势，前景良好")
            elif market_score >= 60: reasons.append("【市场机会适中】岗位在行业中有一定需求")
            if not reasons: reasons.append("综合匹配度达标")

            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            db.execute(
                """INSERT INTO match_records (job_id, interest_score, ability_score, market_score,
                   overlap_score, match_reasons, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (job["id"], round(interest_score), ability_score, market_score, overlap_score,
                 "\n".join(reasons), now),
            )
    db.commit()

# ─────────────────── Company Info (Mock) ───────────────────

COMPANY_INFO = {
    "字节跳动": {"funding": "Pre-IPO (估值$268B)", "scale": "100,000+人", "position": "全球最大独角兽，短视频/推荐系统领先", "news": "2025年海外TikTok Shop GMV突破$500亿", "culture": ["扁平化管理", "快速迭代", "数据驱动", "技术信仰"]},
    "阿里巴巴": {"funding": "纽交所+港交所上市 (NYSE:BABA)", "scale": "200,000+人", "position": "中国最大电商平台，云计算领先", "news": "2025Q1云业务营收同比增长6%", "culture": ["客户第一", "拥抱变化", "团队合作", "激情"]},
    "腾讯": {"funding": "港交所上市 (00700.HK)", "scale": "100,000+人", "position": "中国最大社交+游戏公司", "news": "2025年混元大模型全面接入微信生态", "culture": ["用户为本", "科技向善", "开放协作", "创新突破"]},
    "百度": {"funding": "纳斯达克上市 (NASDAQ:BIDU)", "scale": "40,000+人", "position": "中国AI先行者，自动驾驶领先", "news": "文心一言4.0发布，萝卜快跑覆盖20城", "culture": ["简单可依赖", "技术驱动", "创新突破"]},
    "华为": {"funding": "未上市 (员工持股)", "scale": "200,000+人", "position": "全球通信设备+手机巨头", "news": "鸿蒙生态设备超10亿台，昇腾AI芯片量产", "culture": ["以奋斗者为本", "狼性文化", "技术立身", "长期投入"]},
    "网易": {"funding": "纳斯达克+港交所上市", "scale": "30,000+人", "position": "头部游戏+在线教育公司", "news": "2025年多款新游全球上线", "culture": ["创新", "匠心", "和用户在一起"]},
    "拼多多": {"funding": "纳斯达克上市 (NASDAQ:PDD)", "scale": "15,000+人", "position": "中国增长最快电商，Temu全球化", "news": "Temu覆盖70+国家，2025年营收翻倍", "culture": ["本分", "极致效率", "消费者导向"]},
}

DEFAULT_COMPANY = {"funding": "信息暂缺", "scale": "信息暂缺", "position": "信息暂缺", "news": "暂无近期动态", "culture": ["信息暂缺"]}

# ─────────────────── Interview Prep Generator ───────────────────

def generate_interview_prep(jd_text: str, title: str) -> list:
    directions = []
    if any(kw in jd_text for kw in ["Python", "SQL", "Java", "算法", "开发", "工程"]):
        directions.append({
            "dimension": "技术栈深入",
            "label": "技术",
            "color": "#3B82F6",
            "sample_questions": [
                f"请描述你在{title}相关项目中使用Python/SQL解决的一个复杂问题",
                "针对大规模数据处理，你会如何优化查询性能？",
            ],
            "prep_tips": "回顾核心算法和数据结构，准备一个技术深度展示的项目案例",
        })
    if any(kw in jd_text for kw in ["分析", "数据", "统计", "分析"]):
        directions.append({
            "dimension": "数据分析思维",
            "label": "分析",
            "color": "#10B981",
            "sample_questions": [
                "给我们一个你通过数据分析推动业务决策的例子",
                "如果产品的关键指标突然下降30%，你如何排查？",
            ],
            "prep_tips": "准备AB测试框架、指标体系搭建的案例，熟悉因果推断基本概念",
        })
    directions.append({
        "dimension": "行为面试",
        "label": "行为",
        "color": "#8B5CF6",
        "sample_questions": [
            "请描述一次你与团队成员意见分歧时如何处理的经历",
            "讲讲你最有成就感的一个项目，你的角色和贡献",
        ],
        "prep_tips": "用STAR法则(Situation-Task-Action-Result)准备3个核心故事",
    })
    directions.append({
        "dimension": "行业认知",
        "label": "行业",
        "color": "#F59E0B",
        "sample_questions": [
            "你对当前行业趋势有什么看法？",
            "你认为AI技术会如何改变这个行业？",
        ],
        "prep_tips": "阅读最新行业报告，准备2-3个行业见解",
    })
    if any(kw in jd_text for kw in ["产品", "设计", "系统", "架构"]):
        directions.append({
            "dimension": "系统设计",
            "label": "设计",
            "color": "#06B6D4",
            "sample_questions": [
                "如何设计一个支持百万用户的产品功能？",
                "当系统面临高并发压力时，你会如何设计？",
            ],
            "prep_tips": "熟悉系统设计框架：需求澄清→容量估算→API设计→数据模型→架构图",
        })
    return directions[:5]

# ─────────────────── HTTP Server ───────────────────

class JobMatchHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw)
        except:
            return {}

    def _get_param(self, key, default=""):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return params.get(key, [default])[0]

    def route(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        method = self.command

        # ── Health ──
        if path == "/api/health":
            return self.json_response({"status": "ok", "db": os.path.exists(DB_PATH)})

        # ── Seed ──
        if path == "/api/seed" and method == "POST":
            cnt = seed_database()
            db = get_db()
            run_match_for_all(db)
            db.close()
            return self.json_response({"success": True, "jobs_seeded": cnt, "resume": MOCK_ABILITY["skills"]})

        # ── Jobs ──
        if path == "/api/jobs/all" or path == "/api/jobs/search":
            page = int(params.get("page", ["1"])[0])
            page_size = int(params.get("page_size", ["20"])[0])
            platform = params.get("platform", [""])[0]
            rtype = params.get("type", [""])[0]
            search = params.get("search", [""])[0] or params.get("q", [""])[0]

            conditions = []
            vals = []
            if platform:
                conditions.append("source_platform = ?")
                vals.append(platform)
            if rtype:
                conditions.append("recruitment_type = ?")
                vals.append(rtype)
            if search:
                conditions.append("(title LIKE ? OR company LIKE ? OR jd_text LIKE ?)")
                s = f"%{search}%"
                vals.extend([s, s, s])

            where = " AND ".join(conditions) if conditions else "1=1"
            db = get_db()
            total = db.execute(f"SELECT COUNT(*) FROM jobs WHERE {where}", vals).fetchone()[0]
            offset = (page - 1) * page_size
            rows = db.execute(
                f"SELECT * FROM jobs WHERE {where} ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                vals + [page_size, offset],
            ).fetchall()
            db.close()
            return self.json_response({
                "items": dict_rows(rows), "total": total, "page": page,
                "page_size": page_size, "has_more": offset + page_size < total,
            })

        # ── Job Detail ──
        m = re.match(r"/api/jobs/(\d+)$", path)
        if m:
            job_id = int(m.group(1))
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not job:
                db.close()
                return self.json_response({"error": "not found"}, 404)
            result = dict(job)
            match = db.execute(
                "SELECT * FROM match_records WHERE job_id = ? ORDER BY created_at DESC LIMIT 1", (job_id,)
            ).fetchone()
            result["match_record"] = dict(match) if match else None
            db.close()
            return self.json_response(result)

        # ── Similar Jobs ──
        m = re.match(r"/api/jobs/(\d+)/similar", path)
        if m:
            job_id = int(m.group(1))
            limit = int(params.get("limit", ["5"])[0])
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not job:
                db.close()
                return self.json_response({"items": []})
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
            return self.json_response({"items": dict_rows(rows)})

        # ── Company Info ──
        m = re.match(r"/api/jobs/(\d+)/company-info", path)
        if m:
            job_id = int(m.group(1))
            db = get_db()
            job = db.execute("SELECT company FROM jobs WHERE id = ?", (job_id,)).fetchone()
            db.close()
            if not job:
                return self.json_response({"error": "not found"}, 404)
            info = COMPANY_INFO.get(job["company"], DEFAULT_COMPANY)
            return self.json_response({
                "company": job["company"],
                "funding_stage": info["funding"],
                "employee_scale": info["scale"],
                "industry_position": info["position"],
                "recent_news": info["news"],
                "culture_keywords": info["culture"],
                "disclaimer": "基于公开信息推断，仅供参考",
            })

        # ── Interview Prep ──
        m = re.match(r"/api/jobs/(\d+)/interview-prep", path)
        if m:
            job_id = int(m.group(1))
            db = get_db()
            job = db.execute("SELECT title, jd_text FROM jobs WHERE id = ?", (job_id,)).fetchone()
            db.close()
            if not job:
                return self.json_response({"error": "not found"}, 404)
            directions = generate_interview_prep(job["jd_text"] or "", job["title"])
            return self.json_response({"job_id": job_id, "directions": directions})

        # ── Mock Interview ──
        if path == "/api/interview/start" and method == "POST":
            body = self.read_body()
            job_id = body.get("job_id", 0)
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            db.close()
            jd = job["jd_text"] if job else ""
            questions = [
                {"id": 1, "question": f"请做一个简单的自我介绍，重点突出与{job['title'] if job else '该岗位'}相关的经历。"},
                {"id": 2, "question": f"在{job['title'] if job else '该岗位'}的工作中，你如何处理压力和紧急任务？"},
                {"id": 3, "question": "如果团队中有人不同意你的方案，你会怎么做？"},
                {"id": 4, "question": "你如何保持自己在专业领域的持续学习和成长？"},
                {"id": 5, "question": "你对我们公司和这个岗位有什么了解？为什么想来？"},
            ]
            return self.json_response({
                "session_id": random.randint(1000, 9999),
                "job_title": job["title"] if job else "未知岗位",
                "questions": questions,
                "total_questions": len(questions),
            })

        if path == "/api/interview/evaluate" and method == "POST":
            body = self.read_body()
            answer = body.get("answer", "")
            qid = body.get("question_id", 0)
            # Mock evaluation
            score = random.randint(3, 5)
            feedbacks = {
                3: "回答结构清晰，但可以补充更多具体例子来增强说服力",
                4: "很好的回答！建议加入量化成果，让面试官更直观地感受你的贡献",
                5: "优秀！回答全面且有深度，展现了扎实的专业功底和沟通能力",
            }
            return self.json_response({
                "question_id": qid,
                "score": score,
                "max_score": 5,
                "feedback": feedbacks[score],
                "completed": qid >= 5,
            })

        # ── Featured ──
        if path == "/api/featured":
            page = int(params.get("page", ["1"])[0])
            page_size = int(params.get("page_size", ["10"])[0])
            minscore = int(params.get("min_score", ["60"])[0])
            rtype = params.get("type", [""])[0]
            industry = params.get("industry", [""])[0]
            city = params.get("city", [""])[0]

            conditions = ["mr.overlap_score >= ?"]
            vals = [minscore]
            if rtype:
                conditions.append("j.recruitment_type = ?")
                vals.append(rtype)
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
            return self.json_response({
                "items": items, "total": total, "page": page,
                "page_size": page_size, "today_new": today_count,
            })

        # ── Applications ──
        if path == "/api/applications":
            if method == "GET":
                status = params.get("status", [""])[0]
                page = int(params.get("page", ["1"])[0])
                page_size = int(params.get("page_size", ["20"])[0])

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
                return self.json_response({
                    "items": dict_rows(rows), "total": total, "page": page, "page_size": page_size,
                })

            elif method == "POST":
                body = self.read_body()
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
                return self.json_response(dict(row))

        # ── Application detail ──
        m = re.match(r"/api/applications/(\d+)$", path)
        if m:
            app_id = int(m.group(1))
            if method == "PUT":
                body = self.read_body()
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
                return self.json_response(dict(row) if row else {"error": "not found"})

        # ── Application Stats ──
        if path == "/api/applications/stats":
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
            return self.json_response({
                "total": total, "by_status": by_status,
                "score_distribution": dict_rows(dist_rows),
                "weekly_trend": [
                    {"week": "2026-W20", "applied": 5, "offer": 1},
                    {"week": "2026-W21", "applied": 8, "offer": 2},
                    {"week": "2026-W22", "applied": 3, "offer": 0},
                ],
            })

        # ── Resume ──
        if path == "/api/resume/upload" and method == "POST":
            body = self.read_body()
            db = get_db()
            db.execute("DELETE FROM resume")
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            db.execute(
                "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at) VALUES (?, ?, ?, 'mock', ?)",
                (json.dumps(MOCK_INTEREST, ensure_ascii=False),
                 json.dumps(MOCK_ABILITY, ensure_ascii=False),
                 json.dumps(MOCK_BREAKERS, ensure_ascii=False), now),
            )
            db.commit()
            run_match_for_all(db)
            db.close()
            return self.json_response({
                "success": True,
                "interest_profile": MOCK_INTEREST,
                "ability_profile": MOCK_ABILITY,
                "deal_breakers": MOCK_BREAKERS,
                "message": "简历上传成功！已生成三圈画像并完成40个岗位匹配",
            })

        if path == "/api/resume/profile":
            db = get_db()
            row = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
            db.close()
            if not row:
                return self.json_response({"has_resume": False})
            return self.json_response({
                "has_resume": True,
                "interest_profile": json.loads(row["interest_profile"]),
                "ability_profile": json.loads(row["ability_profile"]),
                "deal_breakers": json.loads(row["deal_breakers"]),
            })

        # ── Feedback ──
        if path == "/api/feedback":
            if method == "POST":
                body = self.read_body()
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
                return self.json_response({"success": True, "preference_changes": changes})

            elif method == "GET":
                limit = int(params.get("limit", ["20"])[0])
                db = get_db()
                rows = db.execute(
                    """SELECT f.*, j.title as job_title, j.company as job_company
                       FROM feedback f LEFT JOIN match_records mr ON f.match_record_id = mr.id
                       LEFT JOIN jobs j ON mr.job_id = j.id
                       ORDER BY f.created_at DESC LIMIT ?""", (limit,),
                ).fetchall()
                db.close()
                return self.json_response(dict_rows(rows))

        # ── Source Platforms ──
        if path == "/api/jobs/sources":
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
            # Add custom source count
            custom_cnt = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE source_platform = 'custom'"
            ).fetchone()[0]
            if custom_cnt > 0:
                sources.append({"platform": "custom", "count": custom_cnt, "label": "自定义来源"})
            db.close()
            return self.json_response({"sources": sources, "all_platforms": list(PLATFORM_LABELS.keys())})

        # ── Custom Source ──
        if path == "/api/custom-source" and method == "POST":
            body = self.read_body()
            title = body.get("title", "")
            company = body.get("company", "")
            custom_source_name = body.get("source_name", "自定义来源")
            custom_source_url = body.get("source_url", "")
            city = body.get("city", "")
            salary_range = body.get("salary_range", "")
            recruitment_type = body.get("recruitment_type", "experienced")
            industry = body.get("industry", "互联网")
            jd_text = body.get("jd_text", "")
            skills = body.get("skills", [])

            if not title or not company:
                return self.json_response({"error": "岗位名称和公司为必填项"}, 400)

            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            jd_profile = gen_jd_profile(skills) if skills else {"knowledge":[],"skills":[],"abilities":[],"values":[]}

            db = get_db()
            db.execute(
                """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                   recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
                   application_deadline, posted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'custom', ?, ?, ?, ?, ?)""",
                (title, company, jd_text, json.dumps(skills, ensure_ascii=False),
                 json.dumps(jd_profile, ensure_ascii=False), city, salary_range,
                 recruitment_type, industry, custom_source_url, custom_source_name, custom_source_url, dl, now),
            )
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            # Run match for new job
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
            db.close()

            # Match this single job
            db2 = get_db()
            jd_skills_list = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
            jd_set = set(s.lower() for s in jd_skills_list)
            interest_score = random.uniform(55, 95)
            sj = jaccard(MOCK_USER_SKILLS, jd_set)
            ability_score = round((0.5 * sj + 0.5 * random.uniform(0.3, 0.95)) * 100)
            market_score = random.randint(50, 95)
            overlap_score = round((interest_score * ability_score * market_score) ** (1 / 3))
            reasons = ["【自定义来源岗位】已纳入匹配系统"]
            match_now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            db2.execute(
                "INSERT INTO match_records (job_id, interest_score, ability_score, market_score, overlap_score, match_reasons, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id, round(interest_score), ability_score, market_score, overlap_score, "\n".join(reasons), match_now),
            )
            db2.commit()
            db2.close()
            return self.json_response({"success": True, "job_id": new_id, "message": f"岗位「{title}」已添加并完成匹配"})

        # ── Resume Advise ──
        if path == "/api/resume/advise" and method == "POST":
            body = self.read_body()
            job_id = body.get("job_id", 0)
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            resume = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
            db.close()

            if not resume:
                return self.json_response({"error": "请先上传简历"}, 400)

            ability = json.loads(resume["ability_profile"]) if isinstance(resume["ability_profile"], str) else resume["ability_profile"]
            jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
            user_skills = [s.lower() for s in (ability.get("skills") or [])]
            jd_set = set(s.lower() for s in jd_skills)

            # Gap analysis
            matched = [s for s in jd_skills if any(us == s.lower() or s.lower() in us or us in s.lower() for us in user_skills)]
            missing = [s for s in jd_skills if s not in matched]

            # Generate advices
            advices = []
            if matched:
                advices.append({
                    "type": "strength",
                    "title": "已有匹配技能需突出",
                    "content": f"你的{', '.join(matched)}等技能与岗位要求匹配，建议在简历中将这些技能放在显眼位置，并用具体项目数据佐证。",
                    "skills": matched,
                })
            if missing:
                advices.append({
                    "type": "gap",
                    "title": "技能差距需弥补或转化",
                    "content": f"岗位要求但你的简历中未体现的技能：{', '.join(missing)}。建议：1) 如有相关学习经历，补充到简历中；2) 用相近技能进行替代表述；3) 短期内可以通过在线课程快速入门。",
                    "skills": missing,
                })
            advices.append({
                "type": "project",
                "title": "项目经历优化建议",
                "content": "用STAR法则重构项目描述，每个项目突出：业务背景→你的角色→技术方案→量化成果。确保至少有2个项目与岗位行业相关。",
            })
            advices.append({
                "type": "keyword",
                "title": "ATS关键词优化",
                "content": f"确保简历JD中以下关键词自然出现：{', '.join(jd_skills[:5])}。避免堆砌，在每个项目经历中自然融入2-3个关键词。",
            })
            advices.append({
                "type": "format",
                "title": "简历版式与结构建议",
                "content": "建议采用「个人信息→求职意向→核心技能→工作/项目经历→教育背景」的结构，一页A4为佳。使用量化数字（如'提升效率30%'）增强说服力。",
            })

            return self.json_response({
                "job_title": job["title"],
                "job_company": job["company"],
                "matched_skills": matched,
                "missing_skills": missing,
                "match_rate": round(len(matched) / max(len(jd_skills), 1) * 100),
                "advices": advices,
            })

        # ── Resume Generate ──
        if path == "/api/resume/generate" and method == "POST":
            body = self.read_body()
            job_id = body.get("job_id", 0)
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            resume = db.execute("SELECT * FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
            db.close()

            if not resume:
                return self.json_response({"error": "请先上传简历"}, 400)

            ability = json.loads(resume["ability_profile"]) if isinstance(resume["ability_profile"], str) else resume["ability_profile"]
            interest = json.loads(resume["interest_profile"]) if isinstance(resume["interest_profile"], str) else resume["interest_profile"]
            jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])

            # Generate optimized resume content
            user_skills = ability.get("skills") or []
            projects = ability.get("projects") or []
            matched_jd_skills = [s for s in jd_skills if any(us.lower() == s.lower() or s.lower() in us.lower() for us in user_skills)]

            generated_resume = {
                "personal_info": {
                    "name": "[你的姓名]",
                    "phone": "[手机号]",
                    "email": "[邮箱]",
                    "city": job["city"] if job["city"] else "[城市]",
                },
                "summary": f"拥有{', '.join(user_skills[:4])}等核心技能的{job['title']}候选人，" +
                          f"有{', '.join(projects[:2])}等项目经验，具备扎实的{', '.join(matched_jd_skills[:3])}能力。",
                "core_skills": list(set(matched_jd_skills + user_skills[:5])),
                "target_job": job["title"],
                "target_company": job["company"],
                "related_projects": [
                    {
                        "name": p,
                        "description": f"在{p}中，应用{', '.join(user_skills[:3])}技术，实现了从需求分析到落地的完整链路。",
                        "skills_used": user_skills[:3],
                        "result": "项目目标达成率提升XX%，获得团队认可",
                    } for p in projects[:3]
                ],
                "jd_matched_points": [
                    f"突出的{', '.join(matched_jd_skills[:3])}技能与岗位要求高度匹配",
                    f"{len(matched_jd_skills)}/{len(jd_skills)}项JD技能要求被覆盖，覆盖率{round(len(matched_jd_skills)/max(len(jd_skills),1)*100)}%",
                ],
                "optimization_notes": [
                    "已在简历中前置JD匹配最高的技能",
                    "项目描述采用了STAR法则重构",
                    "所有量化指标已加粗突出",
                ],
            }

            # Save version
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            db2 = get_db()
            # Get max version
            max_ver = db2.execute(
                "SELECT COALESCE(MAX(version), 0) FROM resume_versions WHERE resume_id = ?",
                (resume["id"],)
            ).fetchone()[0]
            db2.execute(
                """INSERT INTO resume_versions (resume_id, version, content_json, title, target_job_title,
                   improvement_notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (resume["id"], max_ver + 1, json.dumps(generated_resume, ensure_ascii=False),
                 f"针对{job['company']}{job['title']}岗位优化", job["title"],
                 f"基于差距分析自动优化，匹配率{round(len(matched_jd_skills)/max(len(jd_skills),1)*100)}%", now),
            )
            db2.commit()
            db2.close()

            return self.json_response({
                "success": True,
                "version": max_ver + 1,
                "resume": generated_resume,
                "matched_count": len(matched_jd_skills),
                "total_jd_skills": len(jd_skills),
                "message": f"已生成针对{job['company']}{job['title']}的优化简历",
            })

        # ── Resume Versions ──
        if path == "/api/resume/versions":
            db = get_db()
            rows = db.execute(
                "SELECT * FROM resume_versions ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            db.close()
            return self.json_response({"versions": dict_rows(rows)})

        # ── Interview Review ──
        if path == "/api/interview/review":
            if method == "POST":
                body = self.read_body()
                job_id = body.get("job_id", 0)
                application_id = body.get("application_id", 0)
                review_text = body.get("review_text", "")
                score_self = body.get("score_self", 0)
                questions_asked = json.dumps(body.get("questions_asked", []), ensure_ascii=False)
                difficult_questions = body.get("difficult_questions", "")

                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                # AI Analysis (mock)
                ai_analysis = {
                    "overall_score": min(score_self * 0.9 + random.uniform(0, 15), 100),
                    "score_breakdown": {
                        "technical": random.randint(60, 90),
                        "communication": random.randint(65, 95),
                        "problem_solving": random.randint(60, 90),
                        "culture_fit": random.randint(70, 95),
                    },
                    "strengths": [
                        "对技术栈有较好理解，能清晰表达项目经验",
                        "对行业有一定认知，展现了求职诚意",
                    ],
                    "weaknesses": [
                        "部分技术问题的深度可以进一步提升",
                        "回答时可以更多引用量化数据增强说服力",
                        "对公司的了解可以更深入一些",
                    ],
                    "key_takeaways": "整体表现良好，体现了较强的学习能力和沟通能力。建议在技术深度和对公司业务理解上继续加强。",
                }

                improvement_advices = [
                    {
                        "category": "技术提升",
                        "priority": "high",
                        "action": "深入掌握岗位相关的核心技术框架，准备3个技术深度展示案例",
                        "timeline": "2周内",
                        "resources": "官方文档、技术博客、开源项目贡献",
                    },
                    {
                        "category": "项目表达",
                        "priority": "high",
                        "action": "用STAR法则重构每个项目描述，确保3分钟内讲清：背景→挑战→方案→量化成果",
                        "timeline": "1周内",
                        "resources": "录制模拟回答视频自我复盘",
                    },
                    {
                        "category": "公司研究",
                        "priority": "medium",
                        "action": "深度研究目标公司业务模式、竞品动态、最新财报/新闻",
                        "timeline": "面试前3天",
                        "resources": "公司年报、36氪、虎嗅研报",
                    },
                    {
                        "category": "软技能",
                        "priority": "medium",
                        "action": "练习行为面试常见问题，准备5个个人故事覆盖不同能力维度",
                        "timeline": "持续进行",
                        "resources": "模拟面试练习、录音回听",
                    },
                ]

                db = get_db()
                db.execute(
                    """INSERT INTO interview_reviews (application_id, job_id, review_text, score_self,
                       questions_asked, difficult_questions, ai_analysis, improvement_advices,
                       strengths, weaknesses, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (application_id, job_id, review_text, score_self,
                     questions_asked, difficult_questions,
                     json.dumps(ai_analysis, ensure_ascii=False),
                     json.dumps(improvement_advices, ensure_ascii=False),
                     json.dumps(ai_analysis["strengths"], ensure_ascii=False),
                     json.dumps(ai_analysis["weaknesses"], ensure_ascii=False),
                     now),
                )
                db.commit()
                review_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

                # If there's an application, update its notes
                if application_id:
                    existing = db.execute("SELECT notes FROM applications WHERE id = ?", (application_id,)).fetchone()
                    if existing:
                        try:
                            notes = json.loads(existing["notes"]) if isinstance(existing["notes"], str) else (existing["notes"] or {})
                        except:
                            notes = {}
                        notes["last_interview_review_id"] = review_id
                        notes["last_interview_score"] = score_self
                        db.execute("UPDATE applications SET notes = ?, updated_at = ? WHERE id = ?",
                                   (json.dumps(notes, ensure_ascii=False), now, application_id))
                        db.commit()
                db.close()

                return self.json_response({
                    "success": True,
                    "review_id": review_id,
                    "analysis": ai_analysis,
                    "improvement_advices": improvement_advices,
                })

            elif method == "GET":
                job_id = int(self._get_param("job_id", "0"))
                db = get_db()
                if job_id:
                    rows = db.execute(
                        "SELECT * FROM interview_reviews WHERE job_id = ? ORDER BY created_at DESC LIMIT 5",
                        (job_id,)
                    ).fetchall()
                else:
                    rows = db.execute(
                        "SELECT * FROM interview_reviews ORDER BY created_at DESC LIMIT 10"
                    ).fetchall()
                db.close()
                return self.json_response({"reviews": dict_rows(rows)})

        # ── Improvement Advisor ──
        if path == "/api/interview/improvement" and method == "POST":
            body = self.read_body()
            review_id = body.get("review_id", 0)
            job_id = body.get("job_id", 0)

            db = get_db()
            if review_id:
                review = db.execute("SELECT * FROM interview_reviews WHERE id = ?", (review_id,)).fetchone()
            elif job_id:
                review = db.execute(
                    "SELECT * FROM interview_reviews WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                    (job_id,)
                ).fetchone()
            else:
                review = None

            if not review:
                db.close()
                return self.json_response({"error": "未找到面试复盘记录"}, 404)

            ai_analysis = json.loads(review["ai_analysis"]) if isinstance(review["ai_analysis"], str) else review["ai_analysis"]
            improvement_advices = json.loads(review["improvement_advices"]) if isinstance(review["improvement_advices"], str) else review["improvement_advices"]
            weaknesses = json.loads(review["weaknesses"]) if isinstance(review["weaknesses"], str) else review["weaknesses"]

            # Get job info for targeted advice
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (review["job_id"],)).fetchone() if review["job_id"] else None
            db.close()

            # Generate next-step plan
            next_steps = {
                "before_next_interview": [
                    {"step": 1, "action": "针对薄弱项进行专项训练", "detail": f"重点提升：{', '.join(weaknesses[:2])}", "duration": "3-5天"},
                    {"step": 2, "action": "更新简历突出新学习内容", "detail": "将面试中学到的反馈转化为简历关键词", "duration": "1天"},
                    {"step": 3, "action": "再次模拟面试", "detail": "针对上次不足的问题类型进行专项模拟", "duration": "2天"},
                ],
                "long_term_growth": [
                    "建立个人技术博客/GitHub项目展示技术深度",
                    "参与行业meetup或线上社区，拓展人脉",
                    "定期复盘每次面试，建立个人面试题库",
                ],
                "resume_update_suggestions": [
                    "在简历中补充面试中暴露的技能短板相关学习经历",
                    "优化项目描述中的量化数据",
                    "添加面试中面试官关注的关键词",
                ],
                "priority_advices": [a for a in improvement_advices if a.get("priority") == "high"],
            }

            return self.json_response({
                "review_id": review["id"],
                "review_score": review["score_self"],
                "ai_score": ai_analysis.get("overall_score", 0),
                "strengths": json.loads(review["strengths"]) if isinstance(review["strengths"], str) else review["strengths"],
                "weaknesses": weaknesses,
                "improvement_advices": improvement_advices,
                "next_steps": next_steps,
                "job_title": job["title"] if job else "",
                "job_company": job["company"] if job else "",
            })

        # ── 404 ──
        self.json_response({"error": "not found", "path": path}, 404)

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route()

    def do_PUT(self):
        self.route()

    def do_DELETE(self):
        self.route()

    def log_message(self, format, *args):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {args[0] if args else format}")


if __name__ == "__main__":
    # Init
    init_db()
    db = get_db()
    job_count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    db.close()

    if job_count == 0:
        print("[Init] Seeding database...")
        seed_database()
        db = get_db()
        run_match_for_all(db)
        db.close()
        print("[Init] 40 mock jobs seeded and matched")

    port = 8000
    server = HTTPServer(("0.0.0.0", port), JobMatchHandler)
    print(f"\n[Server] JobMatch AI running at http://localhost:{port}")
    print(f"  Health:   http://localhost:{port}/api/health")
    print(f"  All Jobs: http://localhost:{port}/api/jobs/all")
    print(f"  Featured: http://localhost:{port}/api/featured")
    print(f"  Apply:    http://localhost:{port}/api/applications")
    print(f"  Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Stopped")
        server.server_close()
