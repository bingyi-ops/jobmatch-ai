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
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程 HTTP 服务器，每个请求独立线程，不会因为匹配计算阻塞其他请求"""
    daemon_threads = True
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from app.llm import parse_jd_text
from app.resume_parser import parse_resume
import cgi
import io

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
            try: db.execute(stmt)
            except Exception as e: print(f"[DB] Skip: {e}")
    # 清理旧 RSS/通知表
    for t in ["notification_logs", "rss_fetch_logs", "subscriptions"]:
        try: db.execute(f"DROP TABLE IF EXISTS {t}")
        except: pass
    db.commit()
    db.close()

def dict_row(row) -> dict:
    if row is None:
        return None
    d = dict(row)
    return _parse_json_fields(d)

def dict_rows(rows) -> list:
    return [dict_row(r) for r in rows]

# JSON 字段列表：数据库中存储为 JSON 字符串，需解析为原生对象给前端
_JSON_FIELDS = {"jd_skills", "jd_profile", "quality_flags", "match_reasons",
                "interest_profile", "ability_profile", "deal_breakers",
                "notes", "ai_analysis", "improvement_advices", "strengths",
                "weaknesses", "questions_asked", "difficult_questions",
                "companies", "industries", "cities", "keywords", "channels",
                "content_json", "feedback", "score_breakdown", "channels"}

def _parse_json_fields(d: dict) -> dict:
    """将字典中已知的 JSON 字符串字段解析为原生对象"""
    for key in _JSON_FIELDS:
        val = d.get(key)
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass  # 保留原始字符串
    return d

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
PLATFORMS = ["official", "boss_zhipin", "xiaohongshu", "wechat_public", "liepin", "lagou", "zhilian", "51job", "shixiseng", "zhihu", "referral", "school_career", "url_import", "custom"]

# 用户导入岗位时选择的「数据来源渠道」→ 映射到标准的 source_platform
# 这样筛选器中点击「企业官网」时就能正确显示所有选「官网直投」的岗位
SOURCE_CHANNEL_TO_PLATFORM = {
    '官网直投':      'official',
    'Boss直聘转发':  'boss_zhipin',
    '就业网':        'school_career',
    '学长内推':      'referral',
    '招聘平台':      'custom',
    '小红书':        'xiaohongshu',
    '公众号':        'wechat_public',
    '其他渠道':      'custom',
}

def map_channel_to_platform(source_channel: str) -> str:
    """将用户选择的渠道名称映射为 source_platform 值"""
    return SOURCE_CHANNEL_TO_PLATFORM.get(source_channel, 'custom')

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

def add_random_jobs(count=1):
    """Add random jobs without clearing existing data."""
    db = get_db()
    now = datetime.now()
    added = 0
    for i in range(count):
        company, industry = COMPANIES[i % len(COMPANIES)]
        title = random.choice(JOB_TITLES)
        city = random.choice(CITIES)
        rectype = random.choice(REC_TYPES)
        platform = random.choice(PLATFORMS)
        salary = random.choice(SALARY)
        posted = now.strftime("%Y-%m-%dT%H:%M:%S")
        dl = (now + timedelta(days=random.choice([7, 14, 21, 30]))).strftime("%Y-%m-%d")
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
             f"https://www.example.com/jobs/{company}/{random.randint(1000,9999)}", dl, posted),
        )
        added += 1
    db.commit()
    db.close()
    return added

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

# ═══════════════════════════════════════════════════════════════
# 人岗匹配评分引擎 — 0-10分制二级指标体系
# ═══════════════════════════════════════════════════════════════
# 我擅长(45%): 学历层次(A1) + 技能掌握度(A2) + 项目经验(A3)  —— 📄简历
# 公司需要(30%): 学历达标(B1) + 专业对口(B2) + 经验年限(B3)
#                + 职责覆盖(B4) + 工作稳定性(B5)  —— 📋JD vs 📄简历
# 我喜欢(25%): 城市(C1) + 行业(C2) + 薪资(C3) + 岗位方向(C4)  —— 👤偏好 vs 📋岗位
# ================================================================

DEFAULT_INTEREST = {
    "preferred_industries": ["互联网"],
    "preferred_roles": ["数据分析"],
    "work_style": [],
}
DEFAULT_ABILITY = {
    "skills": ["Python", "SQL", "Excel"],
    "education": "本科",
    "experience": "1-3年经验",
    "projects": [],
}
DEFAULT_BREAKERS = []

def jaccard(a: set, b: set) -> float:
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def _json_field(val):
    """安全解析 JSON 字符串字段"""
    if isinstance(val, str):
        try: return json.loads(val)
        except: return val
    return val

def _get_user_profile(db, user_key="default"):
    """从数据库读取指定用户的简历画像，若无则返回默认值"""
    row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    if not row:
        return DEFAULT_INTEREST, DEFAULT_ABILITY, DEFAULT_BREAKERS
    interest = _json_field(row["interest_profile"]) or DEFAULT_INTEREST
    ability = _json_field(row["ability_profile"]) or DEFAULT_ABILITY
    breakers = _json_field(row["deal_breakers"]) or DEFAULT_BREAKERS
    return interest, ability, breakers

# ═══════════════════ 一票否决 ═══════════════════

def _check_deal_breakers(job: dict, breakers: list) -> tuple[bool, str]:
    """检查岗位是否命中用户不可接受项。返回(命中, 命中原因)"""
    if not breakers:
        return False, ""
    jd_text = (job["jd_text"] or "").lower()
    title = (job["title"] or "").lower()
    jd_skills = [s.lower() for s in (_json_field(job["jd_skills"]) or [])]
    search_text = jd_text + " " + " ".join(jd_skills) + " " + title
    hits = [b for b in breakers if b.lower() in search_text]
    if hits:
        return True, "命中不可接受项：" + "、".join(hits)
    return False, ""

# ═══════════════════ Multipart 解析（替代 cgi.FieldStorage）═══════════════════

def _parse_multipart(body_bytes: bytes, content_type: str):
    """简易 multipart/form-data 解析器，返回 (file_bytes, filename) 或 (None, '')"""
    # 提取 boundary
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[len("boundary="):].strip(' "')
            break
    if not boundary:
        return None, ""

    boundary_bytes = boundary.encode("utf-8")
    # 分割各部分
    parts = body_bytes.split(b"--" + boundary_bytes)
    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        # 提取 name 和 filename
        header_end = part.find(b"\r\n\r\n")
        if header_end < 0:
            continue
        headers_raw = part[:header_end].decode("utf-8", errors="ignore")
        if 'name="file"' not in headers_raw:
            continue
        # 提取文件名
        fn_match = re.search(r'filename="([^"]*)"', headers_raw)
        filename = fn_match.group(1) if fn_match else "resume.pdf"
        # 提取文件内容（headers 之后，去掉末尾 \r\n）
        content = part[header_end + 4:]
        if content.endswith(b"\r\n"):
            content = content[:-2]
        if content.endswith(b"--"):
            content = content[:-2]
        if len(content) > 10:
            return content, filename
    return None, ""

# ═══════════════════ JD 需求推断辅助 ═══════════════════

def _infer_jd_education_req(jd_text: str):
    """从 JD 文本推断学历要求。返回 '博士'/'硕士'/'本科' 或 None"""
    if not jd_text: return None
    t = jd_text.lower()
    if re.search(r'博士', t): return "博士"
    if re.search(r'硕士|研究生', t): return "硕士"
    if re.search(r'本科及以上|本科以上|本科', t): return "本科"
    if re.search(r'大专|专科', t): return "大专"
    return None

def _infer_jd_major_req(jd_text: str):
    """从 JD 文本推断专业要求。返回专业关键词 或 None"""
    if not jd_text: return None
    t = jd_text
    majors = ["计算机", "软件工程", "数学", "统计", "金融", "会计", "市场营销",
              "通信", "电子", "自动化", "人工智能", "数据科学", "设计", "新闻",
              "医学", "药学", "生物", "化学", "机械", "电气", "土木", "法学"]
    for m in majors:
        if m in t:
            return m
    return None

def _infer_jd_exp_years(jd_text: str):
    """从 JD 文本推断经验年限要求。返回年数 或 None"""
    if not jd_text: return None
    m = re.search(r'(\d+)\s*[年\-].*?[以]?[上内].*?[经工]', jd_text)
    if m: return int(m.group(1))
    m = re.search(r'[经工].*?[经工].*?(\d+)\s*年', jd_text)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)\s*年.*?[以]?[上内].*?[经工]', jd_text)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)[年-].*经验', jd_text)
    if m: return int(m.group(1))
    return None

def _extract_jd_duties(jd_text: str) -> list:
    """从 JD 文本提取岗位职责关键词列表"""
    if not jd_text: return []
    # 提取「负责/参与/主导/协助...」后面的短语
    duties = re.findall(r'(?:负责|参与|主导|协助|承担|推动|完成)\s*[：:]?\s*([^。；;，,\n]{4,30})', jd_text)
    return [d.strip() for d in duties if len(d.strip()) >= 4]

# ═══════════════════ 我擅长 (A1-A3) ═══════════════════

def _score_education_level(ability: dict) -> float:
    """A1: 学历层次 0-10。博士10/硕士8/本科6/大专4/其他2"""
    edu = (ability.get("education") or "").lower() if ability else ""
    if any(kw in edu for kw in ["博士"]): return 10
    if any(kw in edu for kw in ["硕士", "研究生"]): return 8
    if any(kw in edu for kw in ["本科", "学士"]): return 6
    if any(kw in edu for kw in ["大专", "专科"]): return 4
    return 2

def _score_skills_mastery(ability: dict) -> float:
    """A2: 技能掌握度 0-10。基于技能数量和覆盖面"""
    skills = ability.get("skills", []) if ability else []
    n = len(skills)
    if n >= 8: return 10
    if n >= 5: return 8
    if n >= 3: return 6
    if n >= 1: return 4
    return 2

def _score_project_experience(ability: dict) -> float:
    """A3: 实习/项目经验 0-10。基于项目数量和相关性"""
    projects = ability.get("projects", []) if ability else []
    if not projects: return 1
    n = len(projects)
    if n >= 3: return 10
    if n >= 2: return 7
    return 4

# ═══════════════════ 公司需要 (B1-B5) ═══════════════════

def _score_edu_requirement(job: dict, ability: dict) -> float:
    """B1: 学历达标 0-10。JD要求 vs 用户学历"""
    edu_req = _infer_jd_education_req(job["jd_text"] or "")
    if edu_req is None:
        return 7  # JD无明确要求
    user_edu_score = _score_education_level(ability)
    req_scores = {"博士": 10, "硕士": 8, "本科": 6, "大专": 4}
    req_score = req_scores.get(edu_req, 6)
    if user_edu_score >= req_score: return 10  # 达标/超出
    if user_edu_score >= req_score - 2: return 6  # 略低
    return 2  # 明显不达标

def _score_major_match(job: dict, ability: dict) -> float:
    """B2: 专业对口 0-10。JD专业偏好 vs 用户专业"""
    major_req = _infer_jd_major_req(job["jd_text"] or "")
    if major_req is None:
        return 7  # JD无明确要求
    edu = (ability.get("education") or "").lower() if ability else ""
    major = (ability.get("major") or "").lower() if ability else ""
    user_text = edu + " " + major
    if major_req.lower() in user_text: return 10
    # 相近专业组
    cs_group = {"计算机", "软件工程", "人工智能", "数据科学", "通信", "电子", "自动化"}
    fin_group = {"金融", "会计", "经济", "统计"}
    if major_req in cs_group and any(g in user_text for g in cs_group): return 7
    if major_req in fin_group and any(g in user_text for g in fin_group): return 7
    return 4

def _score_exp_years_match(job: dict, ability: dict) -> float:
    """B3: 工作经验年限 0-10。JD要求 vs 用户年限"""
    req_years = _infer_jd_exp_years(job["jd_text"] or "")
    if req_years is None:
        return 7  # JD无明确要求
    exp_text = (ability.get("experience") or "").lower() if ability else ""
    m = re.search(r'(\d+)', exp_text)
    user_years = int(m.group(1)) if m else 1
    if user_years >= req_years: return 10
    if user_years >= req_years * 0.5: return 6
    return 2

def _score_duty_coverage(job: dict, ability: dict) -> float:
    """B4: 岗位职责覆盖 0-10。JD职责 vs 用户项目/技能"""
    duties = _extract_jd_duties(job["jd_text"] or "")
    if not duties:
        return 5  # 无法提取职责
    projects = ability.get("projects", []) if ability else []
    skills = [s.lower() for s in (ability.get("skills", []) or [])]
    projects_text = " ".join(projects).lower()
    skills_text = " ".join(skills)
    user_text = projects_text + " " + skills_text

    covered = 0
    for duty in duties:
        duty_words = set(duty.lower().split())
        if any(w in user_text for w in duty_words if len(w) >= 3):
            covered += 1

    ratio = covered / len(duties)
    if ratio >= 0.8: return 10
    if ratio >= 0.5: return 7
    if ratio >= 0.3: return 4
    return 2

def _score_work_stability(ability: dict) -> float:
    """B5: 工作经历稳定性 0-10。基于实习/工作时长"""
    exp_text = (ability.get("experience") or "").lower() if ability else ""
    # 提取多段时间信息
    durations = re.findall(r'(\d+)\s*[个]?\s*月', exp_text)
    years_list = re.findall(r'(\d+)\s*年', exp_text)
    # 如果有 "X年" 经验，视为稳定性好
    if years_list:
        max_years = max(int(y) for y in years_list)
        if max_years >= 2: return 10
        if max_years >= 1: return 7
    if durations:
        max_months = max(int(d) for d in durations)
        if max_months >= 6: return 7
        if max_months >= 3: return 4
        return 2
    # 无法提取时间信息 → 默认5分
    return 5

# ═══════════════════ 我喜欢 (C1-C4) ═══════════════════

def _score_city_match(job: dict, interest: dict) -> float:
    """C1: 城市匹配 0-10"""
    preferred = [c.lower() for c in (interest.get("preferred_cities", []) or [])]
    job_city = (job["city"] or "").lower()
    if not preferred or not job_city:
        return 5  # 无偏好或无城市信息
    if any(job_city == c for c in preferred): return 10
    if any(c in job_city or job_city in c for c in preferred): return 7
    return 3

def _score_industry_match(job: dict, interest: dict) -> float:
    """C2: 行业匹配 0-10"""
    preferred = [i.lower() for i in (interest.get("preferred_industries", []) or [])]
    job_industry = (job["industry"] or "").lower()
    if not preferred or not job_industry:
        return 5
    if any(job_industry == i for i in preferred): return 10
    if any(i in job_industry or job_industry in i for i in preferred): return 7
    return 4

def _score_salary_match(job: dict, interest: dict) -> float:
    """C3: 薪资匹配 0-10"""
    salary_min = interest.get("salary_min", 0) if interest else 0
    if not salary_min:
        return 5  # 未设置期望薪资
    salary_text = (job["salary_range"] or "").lower()
    nums = re.findall(r'(\d+)', salary_text.replace('k', '000').replace('K', '000').replace('万', '0000'))
    if not nums:
        return 5  # 面议→默认
    job_min = min(int(n) for n in nums)
    if job_min >= salary_min * 1.2: return 10  # 超出预期
    if job_min >= salary_min: return 8       # 在预期范围内
    if job_min >= salary_min * 0.7: return 5  # 略低于预期
    return 2                                    # 明显低于

def _score_role_match(job: dict, interest: dict) -> float:
    """C4: 岗位内容方向 0-10"""
    preferred = [r.lower() for r in (interest.get("preferred_roles", []) or [])]
    job_title = (job["title"] or "").lower()
    jd_text = (job["jd_text"] or "").lower()
    if not preferred:
        return 5
    # 精确匹配岗位标题
    if any(job_title == r for r in preferred): return 10
    if any(r in job_title or job_title in r for r in preferred): return 7
    # 模糊匹配 JD 文本
    if any(r in jd_text for r in preferred): return 4
    return 1

# ═══════════════════ 综合评分汇总 ═══════════════════

def compute_match(job: dict, ability: dict, interest: dict, breakers: list,
                  w1: int = 45, w2: int = 30, w3: int = 25) -> dict:
    """完整评分流程：一票否决 → 12子指标打分 → 加权汇总 → 诊断建议

    Args:
        w1, w2, w3: 三维度权重（总和应为100）
    Returns:
        完整评分卡 dict（含子指标明细和诊断建议）
    """
    # 0. 一票否决
    filtered, filter_reason = _check_deal_breakers(job, breakers)
    if filtered:
        return {
            "job_id": job["id"], "total_score": 0, "total_score_pct": 0,
            "ability": {"total": 0, "subs": {}, "verdict": filter_reason},
            "market":  {"total": 0, "subs": {}, "verdict": ""},
            "interest":{"total": 0, "subs": {}, "verdict": ""},
            "suggestion": "该岗位命中您的不可接受项（" + filter_reason + "），已自动过滤",
            "is_filtered": True
        }

    # 1. 我擅长 (0-10)
    a1 = _score_education_level(ability)
    a2 = _score_skills_mastery(ability)
    a3 = _score_project_experience(ability)
    ability_total = round(a1 * 0.35 + a2 * 0.35 + a3 * 0.30, 1)
    ability_verdict = _ability_verdict(ability_total, a1, a2, a3)

    # 2. 公司需要 (0-10)
    b1 = _score_edu_requirement(job, ability)
    b2 = _score_major_match(job, ability)
    b3 = _score_exp_years_match(job, ability)
    b4 = _score_duty_coverage(job, ability)
    b5 = _score_work_stability(ability)
    market_total = round(b1 * 0.20 + b2 * 0.20 + b3 * 0.20 + b4 * 0.25 + b5 * 0.15, 1)
    market_verdict = _market_verdict(market_total, b1, b2, b3, b4, b5)

    # 3. 我喜欢 (0-10)
    c1 = _score_city_match(job, interest)
    c2 = _score_industry_match(job, interest)
    c3 = _score_salary_match(job, interest)
    c4 = _score_role_match(job, interest)
    interest_total = round(c1 * 0.25 + c2 * 0.25 + c3 * 0.20 + c4 * 0.30, 1)
    interest_verdict = _interest_verdict(interest_total, c1, c2, c3, c4)

    # 4. 综合加权
    total = round(ability_total * w1 / 100 + market_total * w2 / 100 + interest_total * w3 / 100, 1)
    total_pct = round(total * 10)
    suggestion = _generate_suggestion(ability_total, market_total, interest_total, total)

    return {
        "job_id": job["id"],
        "total_score": total,
        "total_score_pct": total_pct,
        "ability": {
            "total": ability_total,
            "subs": {"education": a1, "skills": a2, "projects": a3},
            "verdict": ability_verdict
        },
        "market": {
            "total": market_total,
            "subs": {"edu_req": b1, "major_match": b2, "exp_years": b3, "duty_coverage": b4, "stability": b5},
            "verdict": market_verdict
        },
        "interest": {
            "total": interest_total,
            "subs": {"city": c1, "industry": c2, "salary": c3, "role": c4},
            "verdict": interest_verdict
        },
        "suggestion": suggestion,
        "is_filtered": False
    }

def _ability_verdict(total, a1, a2, a3):
    parts = []
    edu_map = {10:"博士", 8:"硕士", 6:"本科", 4:"大专", 2:"其他"}
    parts.append(f"学历{edu_map.get(a1,'未知')}({a1}/10)")
    parts.append(f"技能{a2}/10分")
    parts.append(f"项目经验{a3}/10分")
    if total >= 8: parts.append("→ 硬实力优秀")
    elif total >= 5: parts.append("→ 硬实力中等")
    else: parts.append("→ 硬实力需提升")
    return "，".join(parts)

def _market_verdict(total, b1, b2, b3, b4, b5):
    parts = []
    if b1 < 6: parts.append("学历略低于JD要求")
    if b2 < 6: parts.append("专业不完全对口")
    if b3 < 6: parts.append("经验年限略低于JD要求")
    if b4 < 5: parts.append("岗位职责覆盖不足")
    if b5 >= 8: parts.append("工作稳定性良好")
    if not parts: parts.append("各方面均满足JD要求")
    if total >= 8: parts.append("→ 高度匹配")
    elif total >= 5: parts.append("→ 中等匹配")
    else: parts.append("→ 差距较大")
    return "，".join(parts)

def _interest_verdict(total, c1, c2, c3, c4):
    parts = []
    if c1 >= 10: parts.append("城市首选")
    elif c1 >= 7: parts.append("城市可接受")
    if c2 >= 10: parts.append("行业精确匹配")
    elif c2 >= 7: parts.append("行业相关")
    if c3 >= 10: parts.append("薪资超出预期")
    elif c3 >= 8: parts.append("薪资符合预期")
    if c4 >= 10: parts.append("岗位精确命中")
    elif c4 >= 7: parts.append("岗位方向相关")
    if not parts: parts.append("偏好匹配度一般")
    if total >= 8: parts.append("→ 高度契合")
    elif total >= 5: parts.append("→ 基本满意")
    else: parts.append("→ 需放宽偏好")
    return "，".join(parts)

def _generate_suggestion(ability, market, interest, total):
    tips = []
    if total >= 8.0:
        tips.append("综合匹配度优秀，建议优先投递并认真准备面试")
    elif total >= 6.5:
        tips.append("综合匹配度良好，可投递，针对弱项做面试准备")
    elif total >= 5.0:
        tips.append("综合匹配度尚可，建议优化简历后投递")
    else:
        tips.append("综合匹配度偏低，建议提升相关技能或拓宽岗位选择范围")

    # 找最弱维度给具体建议
    scores = [("硬实力", ability), ("JD匹配", market), ("偏好契合", interest)]
    scores.sort(key=lambda x: x[1])
    weakest = scores[0]
    if weakest[1] < 5:
        if weakest[0] == "硬实力":
            tips.append(f"短板在「我擅长」({ability}/10)：建议补充相关技能、积累项目经验")
        elif weakest[0] == "JD匹配":
            tips.append(f"短板在「公司需要」({market}/10)：建议筛选学历/经验要求更匹配的岗位")
        else:
            tips.append(f"短板在「我喜欢」({interest}/10)：建议拓宽行业/城市/岗位选择范围")
    return "。".join(tips)

# ═══════════════════ 匹配执行 ═══════════════════

def _match_single_job(db, job, ability, interest, breakers, user_key="default",
                      w1=45, w2=30, w3=25) -> dict | None:
    """对单个岗位执行完整评分并写入 match_records"""
    result = compute_match(job, ability, interest, breakers, w1, w2, w3)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    a_total = result["ability"]["total"]
    m_total = result["market"]["total"]
    i_total = result["interest"]["total"]
    overlap_pct = result["total_score_pct"]

    if result["is_filtered"]:
        db.execute(
            """INSERT INTO match_records (job_id, interest_score, ability_score, market_score,
               overlap_score, match_reasons, is_filtered, filter_reason, created_at, user_key)
               VALUES (?, 0, 0, 0, 0, ?, 1, ?, ?, ?)""",
            (job["id"], result["suggestion"], result["ability"]["verdict"], now, user_key),
        )
    else:
        db.execute(
            """INSERT INTO match_records (job_id, interest_score, ability_score, market_score,
               overlap_score, match_reasons, is_filtered, filter_reason, created_at, user_key)
               VALUES (?, ?, ?, ?, ?, ?, 0, '', ?, ?)""",
            (job["id"], round(i_total * 10), round(a_total * 10),
             round(m_total * 10), overlap_pct, result["suggestion"], now, user_key),
        )

    # 在返回结果中附加评分卡
    return {
        "job_id": job["id"],
        "interest_score": round(i_total * 10),
        "ability_score": round(a_total * 10),
        "market_score": round(m_total * 10),
        "overlap_score": overlap_pct,
        "match_reasons": result["suggestion"],
        "is_filtered": 1 if result["is_filtered"] else 0,
        "score_card": result
    }

def run_match_for_all(db, user_key="default", w1=45, w2=30, w3=25):
    """对所有岗位执行匹配评分（同步版本，可能较慢）"""
    db.execute("PRAGMA foreign_keys = OFF")
    db.execute("DELETE FROM match_records WHERE user_key = ?", (user_key,))
    db.execute("PRAGMA foreign_keys = ON")

    interest, ability, breakers = _get_user_profile(db, user_key)
    jobs = db.execute("SELECT * FROM jobs").fetchall()

    for job in jobs:
        _match_single_job(db, job, ability, interest, breakers, user_key, w1, w2, w3)
    db.commit()

def bg_run_match(user_key="default"):
    """后台线程执行匹配评分，不阻塞请求响应"""
    def _run():
        try:
            db = get_db()
            run_match_for_all(db, user_key)
            db.close()
            print(f"[BG] Matching completed for user {user_key}")
        except Exception as e:
            print(f"[BG] Match error: {e}")
    Thread(target=_run, daemon=True).start()

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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Key")

    def get_user_key(self) -> str:
        """从请求头提取用户标识，默认 'default' 兼容旧数据"""
        return self.headers.get("X-User-Key", "default")

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
                # fallback: read up to 1MB
                raw = self.rfile.read(1024 * 1024)
                if not raw:
                    return {}
            else:
                raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except:
            return {}

    def _get_param(self, key, default=""):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return params.get(key, [default])[0]

    def route(self):
        try:
            self._route_impl()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.json_response({"error": str(e)}, 500)

    def _route_impl(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        method = self.command

        # ── Health ──
        if path == "/api/health":
            return self.json_response({"status": "ok", "db": os.path.exists(DB_PATH)})

        # ── Seed ──
        if path == "/api/seed" and method == "POST":
            init_db()
            cnt = seed_database()
            db = get_db()
            run_match_for_all(db, "default")
            db.close()
            return self.json_response({"success": True, "jobs_seeded": cnt, "resume": DEFAULT_ABILITY["skills"]})

        # ── Dashboard ──
        if path == "/api/dashboard":
            db = get_db()
            today = datetime.now().strftime("%Y-%m-%d")

            total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] or 0
            today_new = db.execute("SELECT COUNT(*) FROM jobs WHERE date(posted_at) = ?", (today,)).fetchone()[0] or 0

            dist = db.execute(
                """SELECT CASE
                    WHEN overlap_score >= 80 THEN 'high'
                    WHEN overlap_score >= 60 THEN 'mid'
                    ELSE 'low'
                END as tier, COUNT(*) as cnt
                FROM match_records GROUP BY tier"""
            ).fetchall()
            match_dist = {r["tier"]: r["cnt"] for r in dist}

            source_dist = db.execute(
                "SELECT source_platform, COUNT(*) as cnt FROM jobs GROUP BY source_platform ORDER BY cnt DESC"
            ).fetchall()
            sources = [{"platform": r["source_platform"], "count": r["cnt"],
                        "label": r["source_platform"]}
                       for r in source_dist]

            industry_dist = db.execute(
                "SELECT industry, COUNT(*) as cnt FROM jobs GROUP BY industry ORDER BY cnt DESC LIMIT 8"
            ).fetchall()

            app_total = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0] or 0
            app_by_status = db.execute(
                "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
            ).fetchall()

            db.close()
            return self.json_response({
                "total_jobs": total_jobs,
                "today_new": today_new,
                "match_distribution": match_dist,
                "high_match_count": match_dist.get("high", 0),
                "mid_match_count": match_dist.get("mid", 0),
                "sources": sources,
                "industries": dict_rows(industry_dist),
                "applications": {
                    "total": app_total,
                    "by_status": {r["status"]: r["cnt"] for r in app_by_status},
                },
            })

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
                # 同时支持 source_platform 直接匹配，以及 custom_source_name 中渠道前缀匹配
                # （用户导入时填写的渠道统一通过 map_channel_to_platform 映射到 source_platform，
                #  老数据若为 url_import 也以 custom_source_name 前缀兜底匹配）
                platform_to_channel = {
                    'official':       ['官网直投', '企业官网'],
                    'boss_zhipin':    ['Boss直聘转发', 'Boss直聘'],
                    'xiaohongshu':    ['小红书'],
                    'wechat_public':  ['公众号', '微信公众号'],
                    'referral':       ['学长内推', '内推', '企业内推'],
                    'school_career':  ['就业网'],
                    'custom':         ['招聘平台', '其他渠道'],
                }
                channels = platform_to_channel.get(platform, [])
                if channels:
                    # 构造 (source_platform = ? OR custom_source_name LIKE ch1% OR ... LIKE chN%)
                    or_parts = ["source_platform = ?"]
                    or_vals = [platform]
                    like_parts = []
                    for ch in channels:
                        like_parts.append("custom_source_name LIKE ?")
                        or_vals.append(f"{ch}%")
                    conditions.append("(" + " OR ".join(or_parts + like_parts) + ")")
                    vals.extend(or_vals)
                else:
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

        # ── Job Detail / Edit / Delete ──
        m = re.match(r"/api/jobs/(\d+)$", path)
        if m:
            job_id = int(m.group(1))

            # ── PUT: 编辑岗位（仅限 custom / url_import 来源）──
            if method == "PUT":
                db = get_db()
                job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
                if not job:
                    db.close()
                    return self.json_response({"error": "岗位不存在"}, 404)
                # 用户导入的岗位（有 custom_source_name）都可以编辑
                csn = (job["custom_source_name"] or "") if "custom_source_name" in job.keys() else ""
                is_user_imported = job["source_platform"] in ("custom", "url_import") or bool(csn.strip())
                if not is_user_imported:
                    db.close()
                    return self.json_response({"error": "只有手动录入或URL导入的岗位可以编辑"}, 403)

                body = self.read_body()
                updates = []
                vals = []

                editable = {
                    "title": "title", "company": "company", "city": "city",
                    "salary_range": "salary_range", "industry": "industry",
                    "recruitment_type": "recruitment_type",
                }
                for db_field, key in editable.items():
                    if key in body and body[key] is not None:
                        updates.append(f"{db_field} = ?")
                        vals.append(body[key])

                if "source_name" in body and body["source_name"] is not None:
                    updates.append("custom_source_name = ?")
                    vals.append(body["source_name"])
                if "source_channel" in body and body["source_channel"] is not None:
                    mapped_platform = map_channel_to_platform(body["source_channel"])
                    updates.append("source_platform = ?")
                    vals.append(mapped_platform)
                if "source_url" in body and body["source_url"] is not None:
                    updates.append("source_url = ?")
                    vals.append(body["source_url"])
                if "jd_text" in body and body["jd_text"] is not None:
                    updates.append("jd_text = ?")
                    vals.append(body["jd_text"])
                if "skills" in body and body["skills"] is not None:
                    skills_list = body["skills"]
                    updates.append("jd_skills = ?")
                    vals.append(json.dumps(skills_list, ensure_ascii=False))
                    jd_profile = gen_jd_profile(skills_list)
                    updates.append("jd_profile = ?")
                    vals.append(json.dumps(jd_profile, ensure_ascii=False))

                if updates:
                    vals.append(job_id)
                    db.execute(f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?", vals)
                    db.commit()

                job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
                db.close()

                # 重新匹配（使用真实用户画像）
                db2 = get_db()
                db2.execute("DELETE FROM match_records WHERE job_id = ?", (job_id,))
                job = db2.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
                if job:
                    interest, ability, breakers = _get_user_profile(db2, user_key)
                    _match_single_job(db2, job, ability, interest, breakers, user_key)
                db2.commit()
                db2.close()
                return self.json_response({"success": True, "job": dict_row(job), "message": "岗位已更新并重新匹配"})

            # ── DELETE: 删除岗位（仅限 custom / url_import 来源）──
            if method == "DELETE":
                db = get_db()
                job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
                if not job:
                    db.close()
                    return self.json_response({"error": "岗位不存在"}, 404)
                csn = (job["custom_source_name"] or "") if "custom_source_name" in job.keys() else ""
                is_user_imported = job["source_platform"] in ("custom", "url_import") or bool(csn.strip())
                if not is_user_imported:
                    db.close()
                    return self.json_response({"error": "只有手动录入或URL导入的岗位可以删除"}, 403)

                db.execute("DELETE FROM feedback WHERE match_record_id IN (SELECT id FROM match_records WHERE job_id = ?)", (job_id,))
                db.execute("DELETE FROM match_records WHERE job_id = ?", (job_id,))
                db.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
                db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                db.commit()
                db.close()
                return self.json_response({"success": True, "message": "岗位已删除"})

            # ── GET: 岗位详情 ──
            user_key = self.get_user_key()
            db = get_db()
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not job:
                db.close()
                return self.json_response({"error": "not found"}, 404)
            result = dict_row(job)
            match = db.execute(
                "SELECT * FROM match_records WHERE job_id = ? AND user_key = ? ORDER BY created_at DESC LIMIT 1",
                (job_id, user_key),
            ).fetchone()
            result["match_record"] = dict_row(match) if match else None
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
            # 可配置权重（前端滑块传入）
            w1 = int(params.get("w1", ["45"])[0])
            w2 = int(params.get("w2", ["30"])[0])
            w3 = int(params.get("w3", ["25"])[0])
            # 标准化权重确保总和100
            wsum = w1 + w2 + w3
            if wsum != 100:
                w1 = round(w1 / wsum * 100)
                w2 = round(w2 / wsum * 100)
                w3 = 100 - w1 - w2

            user_key = self.get_user_key()
            conditions = ["mr.is_filtered = 0", "mr.user_key = ?"]
            vals = [user_key]
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

            # 先获取当前用户的画像用于动态重算
            interest, ability, breakers = _get_user_profile(db, user_key)

            # 获取所有匹配记录（不做 score 过滤，前端按阈值筛选）
            all_rows = db.execute(
                f"""SELECT mr.*, j.title, j.company, j.city, j.salary_range, j.recruitment_type,
                    j.industry, j.source_platform, j.source_url, j.posted_at,
                    j.application_deadline, j.jd_skills, j.jd_text, j.quality_score, j.quality_flags
                    FROM match_records mr JOIN jobs j ON mr.job_id = j.id
                    WHERE {where} ORDER BY mr.overlap_score DESC""",
                vals,
            ).fetchall()

            today = datetime.now().strftime("%Y-%m-%d")
            today_count = db.execute(
                f"SELECT COUNT(*) FROM match_records mr JOIN jobs j ON mr.job_id = j.id WHERE {where} AND j.posted_at >= ?",
                vals + [today],
            ).fetchone()[0]

            # 动态重算综合分（按用户设置的权重）
            scored_items = []
            for row in all_rows:
                d = dict_row(row)
                # 用存储的三圈原始分 × 新权重重算 overlap
                raw_ability = d.get("ability_score", 0)
                raw_market = d.get("market_score", 0)
                raw_interest = d.get("interest_score", 0)
                new_overlap = round(raw_ability * w1 / 100 + raw_market * w2 / 100 + raw_interest * w3 / 100)

                d["overlap_score"] = new_overlap
                d["w1"] = w1; d["w2"] = w2; d["w3"] = w3
                scored_items.append(d)

            # 按新综合分排序 + 阈值过滤
            scored_items = [it for it in scored_items if it["overlap_score"] >= minscore]
            scored_items.sort(key=lambda x: x["overlap_score"], reverse=True)

            total = len(scored_items)
            offset = (page - 1) * page_size
            page_items = scored_items[offset:offset + page_size]

            # 附加反馈信息
            for item in page_items:
                fb = db.execute(
                    "SELECT * FROM feedback WHERE match_record_id = ? ORDER BY created_at DESC LIMIT 1",
                    (item["id"],),
                ).fetchone()
                item["feedback"] = dict_row(fb) if fb else None

            db.close()
            return self.json_response({
                "items": page_items, "total": total, "page": page,
                "page_size": page_size, "today_new": today_count,
                "weights": {"w1": w1, "w2": w2, "w3": w3},
            })

        # ── Applications ──
        if path == "/api/applications":
            if method == "GET":
                user_key = self.get_user_key()
                status = params.get("status", [""])[0]
                page = int(params.get("page", ["1"])[0])
                page_size = int(params.get("page_size", ["20"])[0])

                conditions = ["a.user_key = ?"]
                vals = [user_key]
                if status:
                    conditions.append("a.status = ?")
                    vals.append(status)
                where = " AND ".join(conditions)

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
                user_key = self.get_user_key()
                db = get_db()
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                notes = json.dumps(body.get("notes") or {}, ensure_ascii=False)
                db.execute(
                    """INSERT INTO applications (job_id, match_record_id, status, notes, applied_at, updated_at, user_key)
                       VALUES (?, ?, 'applied', ?, ?, ?, ?)""",
                    (body["job_id"], body.get("match_record_id"), notes, now, now, user_key),
                )
                db.commit()
                app_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                row = db.execute(
                    """SELECT a.*, j.title as job_title, j.company as job_company, j.source_url as job_source_url
                       FROM applications a LEFT JOIN jobs j ON a.job_id = j.id WHERE a.id = ?""",
                    (app_id,),
                ).fetchone()
                db.close()
                return self.json_response(dict_row(row))

        # ── Application detail ──
        m = re.match(r"/api/applications/(\d+)$", path)
        if m:
            app_id = int(m.group(1))
            if method == "PUT":
                user_key = self.get_user_key()
                body = self.read_body()
                db = get_db()
                # 验证所有权
                app = db.execute("SELECT id FROM applications WHERE id = ? AND user_key = ?", (app_id, user_key)).fetchone()
                if not app:
                    db.close()
                    return self.json_response({"error": "投递记录不存在"}, 404)
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
                return self.json_response(dict_row(row) if row else {"error": "not found"})

        # ── Application Stats ──
        if path == "/api/applications/stats":
            user_key = self.get_user_key()
            db = get_db()
            total = db.execute("SELECT COUNT(*) FROM applications WHERE user_key = ?", (user_key,)).fetchone()[0] or 0
            by_status_rows = db.execute("SELECT status, COUNT(*) as cnt FROM applications WHERE user_key = ? GROUP BY status", (user_key,)).fetchall()
            by_status = {r["status"]: r["cnt"] for r in by_status_rows}
            dist_rows = db.execute(
                """SELECT CASE
                       WHEN mr.overlap_score < 70 THEN '60-70' WHEN mr.overlap_score < 80 THEN '70-80'
                       WHEN mr.overlap_score < 90 THEN '80-90' ELSE '90-100' END as range,
                       COUNT(*) as cnt
                   FROM applications a LEFT JOIN match_records mr ON a.match_record_id = mr.id
                   WHERE mr.overlap_score IS NOT NULL AND a.user_key = ? GROUP BY range ORDER BY range""",
                (user_key,),
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
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            user_key = self.get_user_key()
            raw_body = None
            filename = "resume.pdf"

            # 只读字节，不做任何解析
            if content_length > 0:
                raw_body = self.rfile.read(content_length)
            if not raw_body:
                return self.json_response({"error": "请上传有效的简历文件"}, 400)

            # 全部放后台：解析 + 入库 + 匹配
            def _bg_full_pipeline(body_bytes, ct, cl, uk):
                try:
                    fb = None
                    fn = "resume.pdf"
                    # 1) 尝试 multipart/form-data（浏览器上传）
                    if ct and "multipart/form-data" in ct:
                        fb, fn = _parse_multipart(body_bytes, ct)
                    # 2) 回退 JSON base64
                    if fb is None:
                        try:
                            body_json = json.loads(body_bytes.decode("utf-8", errors="ignore"))
                            if body_json.get("content"):
                                import base64
                                fb = base64.b64decode(body_json["content"])
                                fn = body_json.get("filename", "resume.pdf")
                        except: pass

                    if fb is None or len(fb) < 10:
                        print(f"[Resume] Failed to extract file bytes")
                        return

                    print(f"[Resume] Parsing {fn} ({len(fb)} bytes)...")
                    parsed = parse_resume(fb, fn)
                    if parsed is None:
                        print(f"[Resume] parse_resume returned None for {fn}")
                        return

                    skills_count = len(parsed.get("extracted_skills", []))
                    print(f"[Resume] Parsed: {skills_count} skills, edu={parsed.get('extracted_education','?')}")

                    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    db2 = get_db()
                    db2.execute("DELETE FROM resume WHERE user_key = ?", (uk,))
                    db2.execute(
                        "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
                        (json.dumps(parsed.get("interest_profile", {"preferred_industries": parsed.get("extracted_industries",["互联网"]), "preferred_roles": parsed.get("extracted_roles",["数据分析"])}), ensure_ascii=False),
                         json.dumps(parsed.get("ability_profile", {"skills": parsed.get("extracted_skills",[]), "education": parsed.get("extracted_education",""), "experience": parsed.get("extracted_experience",""), "projects": parsed.get("projects",[])}), ensure_ascii=False),
                         json.dumps(parsed.get("deal_breakers",[]), ensure_ascii=False),
                         json.dumps(parsed, ensure_ascii=False), now, uk),
                    )
                    db2.commit()
                    # 直接在当前线程跑匹配（已在后台线程中，不阻塞请求）
                    run_match_for_all(db2, uk)
                    db2.close()
                    print(f"[Resume] Done: {skills_count} skills, matched for user {uk}")
                except Exception as e:
                    print(f"[Resume] BG error: {e}")
                    import traceback; traceback.print_exc()

            Thread(target=_bg_full_pipeline, args=(raw_body, content_type, content_length, user_key), daemon=True).start()
            return self.json_response({
                "success": True,
                "message": "简历已收到，正在后台解析中，请稍后刷新页面查看结果",
                "processing": True,
            })

        if path == "/api/resume/profile":
            user_key = self.get_user_key()
            db = get_db()
            row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
            db.close()
            if not row:
                return self.json_response({"has_resume": False})
            return self.json_response({
                "has_resume": True,
                "interest_profile": json.loads(row["interest_profile"]),
                "ability_profile": json.loads(row["ability_profile"]),
                "deal_breakers": json.loads(row["deal_breakers"]),
            })

        if path == "/api/resume/deal-breakers" and method == "PUT":
            user_key = self.get_user_key()
            body = self.read_body()
            breakers = body.get("deal_breakers", [])
            db = get_db()
            row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
            if not row:
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                db.execute(
                    "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, 'mock', ?, ?)",
                    (json.dumps(DEFAULT_INTEREST, ensure_ascii=False),
                     json.dumps(DEFAULT_ABILITY, ensure_ascii=False),
                     json.dumps(breakers, ensure_ascii=False), now, user_key),
                )
            else:
                db.execute("UPDATE resume SET deal_breakers = ? WHERE id = ?",
                           (json.dumps(breakers, ensure_ascii=False), row["id"]))
            db.commit()
            db.close()
            bg_run_match(user_key)
            return self.json_response({"success": True, "message": "不可接受项已更新"})

        if path == "/api/resume/interest-profile" and method == "PUT":
            user_key = self.get_user_key()
            body = self.read_body()
            db = get_db()
            row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
            # 读取现有画像，支持增量更新
            if row:
                existing = json.loads(row["interest_profile"]) if isinstance(row["interest_profile"], str) else (row["interest_profile"] or {})
            else:
                existing = dict(DEFAULT_INTEREST)
            # 按字段更新（只更新前端传了的字段）
            if "preferred_industries" in body:
                existing["preferred_industries"] = body["preferred_industries"]
            if "preferred_roles" in body:
                existing["preferred_roles"] = body["preferred_roles"]
            if "preferred_cities" in body:
                existing["preferred_cities"] = body["preferred_cities"]
            if "salary_min" in body:
                existing["salary_min"] = body["salary_min"]
            # 兼容旧版 flattened 格式
            if "interests" in body and "preferred_industries" not in body:
                existing["preferred_industries"] = body["interests"]

            if not row:
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                db.execute(
                    "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
                    (json.dumps(existing, ensure_ascii=False),
                     json.dumps(DEFAULT_ABILITY, ensure_ascii=False),
                     json.dumps(DEFAULT_BREAKERS, ensure_ascii=False), now, user_key),
                )
            else:
                db.execute("UPDATE resume SET interest_profile = ? WHERE id = ?",
                           (json.dumps(existing, ensure_ascii=False), row["id"]))
            db.commit()
            db.close()
            bg_run_match(user_key)
            return self.json_response({"success": True, "message": "偏好画像已更新", "profile": existing})

        if path == "/api/resume/ability-profile" and method == "PUT":
            user_key = self.get_user_key()
            body = self.read_body()
            db = get_db()
            row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
            if row:
                existing = json.loads(row["ability_profile"]) if isinstance(row["ability_profile"], str) else (row["ability_profile"] or {})
            else:
                existing = dict(DEFAULT_ABILITY)
            # 按字段增量更新
            if "skills" in body:
                existing["skills"] = body["skills"]
            if "education" in body:
                existing["education"] = body["education"]
            if "major" in body:
                existing["major"] = body["major"]
            if "experience" in body:
                existing["experience"] = body["experience"]
            if "projects" in body:
                existing["projects"] = body["projects"]

            if not row:
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                db.execute(
                    "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
                    (json.dumps(DEFAULT_INTEREST, ensure_ascii=False),
                     json.dumps(existing, ensure_ascii=False),
                     json.dumps(DEFAULT_BREAKERS, ensure_ascii=False), now, user_key),
                )
            else:
                db.execute("UPDATE resume SET ability_profile = ? WHERE id = ?",
                           (json.dumps(existing, ensure_ascii=False), row["id"]))
            db.commit()
            db.close()
            bg_run_match(user_key)
            return self.json_response({"success": True, "message": "能力画像已更新", "profile": existing})
            return self.json_response({"success": True, "message": "能力画像已更新"})

        # ── Feedback ──
        if path == "/api/feedback":
            if method == "POST":
                body = self.read_body()
                if not body or "match_record_id" not in body:
                    return self.json_response({"error": "missing match_record_id"}, 400)
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
            source_channel = body.get("source_channel", "其他渠道")

            if not title or not company:
                return self.json_response({"error": "岗位名称和公司为必填项"}, 400)

            # 将用户选择的渠道映射为标准 source_platform
            source_platform = map_channel_to_platform(source_channel)

            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            jd_profile = gen_jd_profile(skills) if skills else {"knowledge":[],"skills":[],"abilities":[],"values":[]}

            user_key = self.get_user_key()
            db = get_db()
            db.execute(
                """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                   recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
                   application_deadline, posted_at, user_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, company, jd_text, json.dumps(skills, ensure_ascii=False),
                 json.dumps(jd_profile, ensure_ascii=False), city, salary_range,
                 recruitment_type, industry, source_platform, custom_source_url, custom_source_name, custom_source_url, dl, now, user_key),
            )
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            job = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
            db.close()

            # Match this single job
            db2 = get_db()
            interest, ability, breakers = _get_user_profile(db2, user_key)
            _match_single_job(db2, job, ability, interest, breakers, user_key)
            db2.commit()
            db2.close()
            return self.json_response({"success": True, "job_id": new_id, "message": f"岗位「{title}」已添加并完成匹配"})

        # ── JD Text AI 解析：从粘贴的JD文本智能提取信息 ──
        if path == "/api/jobs/parse-jd-text" and method == "POST":
            body = self.read_body()
            jd_text = body.get("jd_text", "").strip()
            if not jd_text or len(jd_text) < 20:
                return self.json_response({"error": "请粘贴至少20字的岗位描述文本"}, 400)

            try:
                result = asyncio.run(parse_jd_text(jd_text))
                if result:
                    return self.json_response({
                        "success": True,
                        "data": result,
                    })
                else:
                    return self.json_response({
                        "success": False,
                        "error": "AI 解析失败，请检查 API 配置或手动填写",
                    })
            except Exception as e:
                return self.json_response({
                    "success": False,
                    "error": f"AI 解析异常: {str(e)}",
                })

        # ── URL Import: 手动填写 + 链接参考导入 ──
        if path == "/api/jobs/import-from-url" and method == "POST":
            body = self.read_body()
            url = body.get("url", "").strip()
            title = body.get("title", "").strip()
            company = body.get("company", "").strip()

            if not title or not company:
                return self.json_response({
                    "error": "岗位名称和公司为必填项。请先粘贴JD文本并使用AI智能解析，或手动填写。",
                    "need_manual_input": True,
                }, 400)

            source_channel = body.get("source_channel", "其他渠道")
            source_name = body.get("source_name", source_channel)
            city = body.get("city", "")
            salary_range = body.get("salary_range", "")
            recruitment_type = body.get("recruitment_type", "experienced")
            industry = body.get("industry", "")
            jd_text = body.get("jd_text", "")
            skills = body.get("skills", [])

            # 将用户选择的渠道映射为标准 source_platform
            source_platform = map_channel_to_platform(source_channel)
            user_key = self.get_user_key()

            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            jd_profile = gen_jd_profile(skills) if skills else {"knowledge":[],"skills":[],"abilities":[],"values":[]}

            db = get_db()
            db.execute(
                """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                   recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
                   application_deadline, posted_at, user_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, company, jd_text, json.dumps(skills, ensure_ascii=False),
                 json.dumps(jd_profile, ensure_ascii=False), city, salary_range,
                 recruitment_type, industry, source_platform, url, source_name, url, dl, now, user_key),
            )
            db.commit()
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            db.close()

            db2 = get_db()
            db2.execute("DELETE FROM match_records WHERE job_id = ?", (new_id,))
            job = db2.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
            if job:
                interest, ability, breakers = _get_user_profile(db2, user_key)
                _match_single_job(db2, job, ability, interest, breakers, user_key)
            db2.commit()
            db2.close()

            return self.json_response({
                "success": True, "job_id": new_id,
                "message": f"已导入岗位「{title} - {company}」并完成匹配",
                "source_platform": source_platform,
                "source_channel": source_channel,
                "extracted_skills": skills,
            })

        # ── Batch Import: 批量确认导入 ──
        if path == "/api/jobs/import-batch" and method == "POST":
            body = self.read_body()
            jobs_input = body.get("jobs", [])
            if not isinstance(jobs_input, list) or len(jobs_input) == 0:
                return self.json_response({"error": "没有可导入的岗位"}, 400)

            user_key = self.get_user_key()
            imported = 0
            skipped = 0
            job_ids = []
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

            for j in jobs_input:
                if not isinstance(j, dict):
                    skipped += 1
                    continue
                title = j.get("title", "").strip()
                company = j.get("company", "").strip()
                if not title or not company:
                    skipped += 1
                    continue
                city = j.get("city", "")
                salary_range = j.get("salary_range", "")
                industry = j.get("industry", "")
                jd_text = j.get("jd_text", "")
                skills = j.get("skills", [])
                source_channel = j.get("source_channel", "批量导入")
                source_platform = map_channel_to_platform(source_channel)
                jd_profile = j.get("jd_profile") or gen_jd_profile(skills)
                if isinstance(jd_profile, str):
                    try:
                        jd_profile = json.loads(jd_profile)
                    except:
                        jd_profile = gen_jd_profile(skills)

                db = get_db()
                recruitment_type = j.get("recruitment_type", "experienced")
                db.execute(
                    """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                       recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
                       application_deadline, posted_at, user_key)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (title, company, jd_text,
                     json.dumps(skills, ensure_ascii=False),
                     json.dumps(jd_profile, ensure_ascii=False),
                     city, salary_range, recruitment_type, industry, source_platform,
                     j.get("source_url", ""), source_channel, j.get("source_url", ""),
                     dl, now, user_key),
                )
                db.commit()
                new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                job_ids.append(new_id)

                # 使用真实用户画像匹配
                job = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
                if job:
                    interest, ability, breakers = _get_user_profile(db, user_key)
                    _match_single_job(db, job, ability, interest, breakers, user_key)
                db.commit()
                db.close()
                imported += 1

            return self.json_response({
                "success": True, "imported": imported, "duplicates": 0,
                "failed": skipped, "job_ids": job_ids,
                "message": f"成功导入 {imported} 个岗位，跳过 {skipped} 个",
            })

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
                dq = body.get("difficult_questions", "")
                if isinstance(dq, list):
                    dq = json.dumps(dq, ensure_ascii=False)
                difficult_questions = dq

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

        # ── User Feedback ──
        if path == "/api/user-feedback" and method == "POST":
            body = self.read_body()
            feedback_type = body.get("type", "").strip()
            title = body.get("title", "").strip()
            description = body.get("description", "").strip()
            contact = body.get("contact", "").strip()

            if feedback_type not in ("bug", "feature"):
                return self.json_response({"error": "请选择反馈类型: bug 或 feature"}, 400)
            if not title or len(title) < 2:
                return self.json_response({"error": "请填写标题（至少2个字）"}, 400)
            if not description or len(description) < 10:
                return self.json_response({"error": "请填写描述（至少10个字）"}, 400)

            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            db = get_db()
            db.execute(
                "INSERT INTO user_feedback (feedback_type, title, description, contact, created_at) VALUES (?, ?, ?, ?, ?)",
                (feedback_type, title, description, contact, now),
            )
            db.commit()
            db.close()
            return self.json_response({"success": True, "message": "感谢你的反馈！我们会尽快处理。"})

        # ── 404 ──
        self.json_response({"error": "not found", "path": path}, 404)

    # ── 静态文件服务（生产部署用）──
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

    def _serve_static(self, path: str):
        """返回前端静态文件，非 /api/ 路径走这里"""
        if path.startswith("/api/"):
            return False  # API 请求不处理
        # 安全：防止路径穿越
        safe_path = os.path.normpath(path.lstrip("/"))
        if safe_path == "" or safe_path == ".":
            safe_path = "index.html"
        file_path = os.path.join(self.STATIC_DIR, safe_path)
        # SPA 回退：无此文件则返回 index.html
        if not os.path.isfile(file_path):
            file_path = os.path.join(self.STATIC_DIR, "index.html")
        if not os.path.isfile(file_path):
            self.send_error(404, "Not Found")
            return True
        # MIME 类型
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".html": "text/html", ".js": "application/javascript", ".css": "text/css",
            ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg",
            ".svg": "image/svg+xml", ".ico": "image/x-icon", ".woff2": "font/woff2",
        }
        content_type = mime_map.get(ext, "application/octet-stream")
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except:
            self.send_error(404, "Not Found")
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            if self._serve_static(parsed.path):
                return
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
        run_match_for_all(db, "default")
        db.close()
        print("[Init] 40 mock jobs seeded and matched")

    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), JobMatchHandler)
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
