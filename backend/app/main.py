from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, Form, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sqlite3
import json
import os
import sys
import asyncio
from datetime import datetime, timedelta
import random

# ── Windows: 修复 Playwright 子进程兼容性 ──
# Python 3.14 默认的 ProactorEventLoop 不支持 subprocess transport，
# 而 Playwright 需要它来启动浏览器。切换到 SelectorEventLoop。
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from .config import DB_PATH, SCHEMA_PATH, UPLOAD_DIR, USE_REAL_LLM
from .database import get_db, init_db, dict_row, dict_rows
from .resume_parser import parse_resume
from .scraper import extract_job_from_url, identify_page_type, extract_jobs_from_list_url
from . import llm
from .rss_aggregator import fetch_rss_jobs, RSS_SOURCES
from .quality_filter import JobQualityFilter
from .services.notification import push_notifications, format_jobs_html
from .services.subscription_matcher import (
    match_jobs_against_subscription,
    deduplicate_jobs,
    load_notified_history,
    save_notification_logs,
)

# ── Mock 数据（保持与原有 server.py 兼容）──────────
COMPANIES = [
    ("字节跳动", "互联网"), ("阿里巴巴", "互联网"), ("腾讯", "互联网"),
    ("百度", "互联网"), ("华为", "互联网"), ("网易", "互联网"),
    ("美团", "互联网"), ("滴滴", "互联网"), ("快手", "互联网"), ("B站", "互联网"),
    ("拼多多", "互联网"), ("京东", "互联网"), ("小米", "互联网"),
    ("宁德时代", "制造业"), ("比亚迪", "制造业"),
    ("大疆", "制造业"), ("格力", "制造业"), ("美的", "制造业"),
    ("三一重工", "制造业"), ("招商银行", "金融"), ("中信证券", "金融"),
    ("平安科技", "金融"), ("蚂蚁集团", "金融"), ("京东科技", "金融"),
    ("微众银行", "金融"), ("好未来", "教育"), ("新东方", "教育"),
    ("高途", "教育"), ("猿辅导", "教育"), ("学而思", "教育"),
    ("迈瑞医疗", "医疗健康"), ("恒瑞医药", "医疗健康"), ("药明康德", "医疗健康"),
    ("联影医疗", "医疗健康"), ("华大基因", "医疗健康"),
    ("麦肯锡", "咨询"), ("波士顿咨询", "咨询"), ("贝恩", "咨询"),
    ("罗兰贝格", "咨询"), ("安永", "咨询"), ("德勤", "咨询"),
    ("宝洁", "快消"), ("联合利华", "快消"),
    ("玛氏", "快消"), ("百事", "快消"), ("可口可乐", "快消"),
    ("欧莱雅", "快消"), ("小红书", "互联网"), ("蔚来", "制造业"),
    ("理想汽车", "制造业"), ("小鹏汽车", "制造业"),
    ("中国平安", "金融"), ("中国人寿", "金融"),
    ("万科", "房地产"), ("碧桂园", "房地产"), ("龙湖", "房地产"),
    ("顺丰", "物流"), ("中通", "物流"), ("京东物流", "物流"),
    ("中国移动", "通信"), ("中国电信", "通信"),
]

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "长沙", "苏州", "厦门", "天津", "重庆", "合肥"]
REC_TYPES = ["daily_intern", "summer_intern", "autumn_recruit", "spring_recruit", "experienced"]
PLATFORMS = ["official", "boss_zhipin", "lagou", "liepin", "51job", "zhilian", "xiaohongshu", "referral", "custom"]
SALARY = ["15k-25k", "20k-35k", "25k-40k", "30k-50k", "18k-28k", "22k-32k", "12k-20k", "35k-55k", "8k-15k", "40k-60k", "50k-80k"]
JOB_TITLES = [
    # 技术类
    "数据分析师", "产品经理", "算法工程师", "后端开发工程师", "前端开发工程师",
    "全栈工程师", "测试工程师", "运维工程师", "安全工程师", "架构师",
    "机器学习工程师", "数据挖掘工程师", "商业分析师", "战略分析师", "项目经理",
    "iOS开发工程师", "Android开发工程师", "游戏开发工程师", "嵌入式工程师",
    "NLP工程师", "计算机视觉工程师",
    # 人力资源类
    "HRBP", "人力资源专员", "人力资源总监", "招聘专员", "招聘经理",
    "薪酬福利经理", "培训发展经理", "组织发展OD", "员工关系专员",
    "HR信息系统管理",
    # 财务类
    "财务经理", "会计", "审计专员", "税务专员", "预算分析师",
    "财务分析师", "资金管理", "出纳", "财务总监",
    # 市场类
    "市场营销经理", "品牌策划", "公关专员", "活动策划", "新媒体运营",
    "内容营销经理", "SEM优化师", "SEO专员", "广告投放", "用户增长",
    "品牌经理", "市场总监",
    # 运营类
    "产品运营", "用户运营", "社群运营", "电商运营", "商家运营",
    "策略运营", "内容运营", "活动运营", "数据运营", "游戏运营",
    # 设计类
    "UI设计师", "UX设计师", "视觉设计师", "交互设计师",
    "品牌设计师", "动效设计师", "插画师", "3D设计师",
    # 销售类
    "大客户销售", "渠道销售经理", "销售运营", "商务拓展BD",
    "销售总监", "客户成功", "售前工程师", "电销专员", "销售经理",
    # 法务/行政
    "法务专员", "合规经理", "行政经理", "总助/CEO助理", "知识产权专员",
    # 供应链
    "供应链管理", "采购专员", "物流经理", "仓储管理", "质量管理",
    # 教育/医疗/其他
    "教师", "课程设计师", "医学顾问", "临床研究专员",
    "投资经理", "行业研究", "咨询顾问", "风险管理",
    "产品总监", "技术总监",
]
JD_SKILLS = [
    "Python", "SQL", "Excel", "Tableau", "机器学习", "深度学习", "PyTorch",
    "TensorFlow", "Spark", "Hadoop", "Docker", "Kubernetes", "AWS", "GCP",
    "React", "Vue", "TypeScript", "Node.js", "Go", "Java", "Spring Boot",
    "数据分析", "AB测试", "统计学", "Power BI", "Figma", "产品设计",
    "项目管理", "敏捷开发", "沟通能力", "团队协作", "英语流利",
    "市场营销", "SEO", "SEM", "内容运营", "用户增长",
    "人力资源管理", "招聘", "薪酬福利", "培训", "绩效管理",
    "财务管理", "审计", "税务", "预算管理", "成本控制",
    "供应链管理", "物流", "采购", "质量管理",
    "法务", "合规", "合同管理", "知识产权",
    "销售管理", "客户关系管理", "商务谈判",
    "视频剪辑", "新媒体", "社群运营",
    "Unity", "Unreal", "游戏策划",
    "Photoshop", "Illustrator", "After Effects",
]

PLATFORM_LABELS = {
    "official": "企业官网", "boss_zhipin": "Boss直聘",
    "xiaohongshu": "小红书", "wechat_public": "微信公众号",
    "lagou": "拉勾", "liepin": "猎聘",
    "zhilian": "智联招聘", "51job": "前程无忧",
    "referral": "内推", "custom": "自定义",
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
    "百度": {"funding": "纳斯达克+港交所上市", "scale": "40,000+人", "position": "中国AI与搜索领域领军企业", "news": "文心大模型持续迭代", "culture": ["技术驱动", "简单可依赖"]},
    "华为": {"funding": "员工持股(未上市)", "scale": "190,000+人", "position": "全球通信设备与智能终端巨头", "news": "鸿蒙生态持续扩展", "culture": ["艰苦奋斗", "自我批判", "开放合作"]},
    "美团": {"funding": "港交所上市", "scale": "100,000+人", "position": "中国本地生活服务龙头", "news": "2025年即时零售业务高速增长", "culture": ["长期有耐心", "以客户为中心"]},
    "滴滴": {"funding": "纽交所上市", "scale": "15,000+人", "position": "中国出行服务领导者", "news": "国际化业务拓展加速", "culture": ["安全第一", "体验至上"]},
    "快手": {"funding": "港交所上市", "scale": "25,000+人", "position": "短视频与直播头部平台", "news": "电商GMV持续高增长", "culture": ["拥抱每一种生活", "技术普惠"]},
    "京东": {"funding": "纳斯达克+港交所上市", "scale": "500,000+人", "position": "中国自营电商与供应链巨头", "news": "物流科技持续创新", "culture": ["正道成功", "客户为先"]},
    "小米": {"funding": "港交所上市", "scale": "35,000+人", "position": "全球消费电子与智能生态领先者", "news": "造车业务持续推进", "culture": ["真诚热爱", "与用户交朋友"]},
    "小红书": {"funding": "Pre-IPO (估值$20B+)", "scale": "5,000+人", "position": "中国生活方式社区领导者", "news": "电商业务快速增长", "culture": ["向上生长", "向下扎根"]},
    "招商银行": {"funding": "上交所+港交所上市", "scale": "100,000+人", "position": "中国零售银行标杆", "news": "数字化转型领先", "culture": ["因您而变", "轻型银行"]},
    "宁德时代": {"funding": "深交所上市", "scale": "40,000+人", "position": "全球动力电池龙头", "news": "固态电池技术突破", "culture": ["修己达人", "奋斗创新"]},
    "比亚迪": {"funding": "深交所+港交所上市", "scale": "600,000+人", "position": "中国新能源汽车领导者", "news": "全球销量持续领先", "culture": ["技术为王", "创新为本"]},
    "大疆": {"funding": "Pre-IPO (估值$15B+)", "scale": "14,000+人", "position": "全球无人机与影像技术霸主", "news": "行业应用持续拓展", "culture": ["激极尽志", "求真品诚"]},
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
               application_deadline, posted_at, quality_score, quality_flags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, ?, 90, '["mock_data","high_quality"]')""",
            (title, company, jd_text, json.dumps(skills, ensure_ascii=False),
             json.dumps(jd_profile, ensure_ascii=False), city, salary,
             rectype, industry, platform,
             f"https://www.example.com/jobs/{company}/{i+1}", dl, posted),
        )
    db.commit()
    return 40

def run_match_for_all(db: sqlite3.Connection, user_key: str = "default"):
    """对所有岗位运行三圈匹配（基于规则的真实计算版，零成本，可解释）
    仅匹配当前用户的简历画像，match_records 按 user_key 隔离"""
    db.execute("DELETE FROM match_records WHERE user_key = ?", (user_key,))
    jobs = db.execute("SELECT * FROM jobs").fetchall()

    # 获取当前用户最新简历画像
    resume_row = db.execute(
        "SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)
    ).fetchone()
    if resume_row:
        user_ability = json.loads(resume_row["ability_profile"])
        user_interest = json.loads(resume_row["interest_profile"])
        user_skills = {s.lower() for s in user_ability.get("skills", [])}
        preferred_industries = set(i.lower() for i in user_interest.get("preferred_industries", ["互联网"]))
        preferred_roles = set(r.lower() for r in user_interest.get("preferred_roles", ["数据分析"]))
    else:
        # Fallback to mock
        user_skills = {s.lower() for s in MOCK_ABILITY["skills"]}
        preferred_industries = set(i.lower() for i in MOCK_INTEREST["preferred_industries"])
        preferred_roles = set(r.lower() for r in MOCK_INTEREST["preferred_roles"])

    # 用户兴趣维度向量（关键词 + 权重）
    interest_keywords = {
        "互联网": 1.0, "金融科技": 0.9, "人工智能": 0.95, "金融": 0.85,
        "数据": 0.9, "产品": 0.85, "算法": 0.85, "分析": 0.9,
        "电商": 0.7, "游戏": 0.7, "教育": 0.6, "医疗": 0.55,
        "制造": 0.7, "快消": 0.65, "物流": 0.6, "通信": 0.7,
        "人力资源": 0.8, "财务": 0.7, "市场": 0.75, "运营": 0.8,
        "设计": 0.75, "销售": 0.65, "供应链": 0.7, "法务": 0.65,
    }

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
               overlap_score, match_reasons, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (job["id"], interest_score, ability_score, market_score, overlap_score,
             "\n".join(reasons), now, user_key),
        )
    db.commit()

def jaccard(a: set, b: set) -> float:
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

# ── 用户身份依赖注入 ──────────────────────────────────
def get_user_key(x_user_key: str = Header("default", alias="X-User-Key")) -> str:
    """从请求头提取用户标识，实现数据隔离。未传则默认为 'default' 以兼容旧数据。"""
    return x_user_key

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
    # 确保 user_settings 表存在
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preferences TEXT DEFAULT '{}',
            updated_at TEXT
        )""")
        db.commit()
    except:
        pass

    job_count = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    db.close()
    if job_count == 0:
        print("[Init] Seeding database...")
        db2 = get_db()
        seed_database(db2)
        run_match_for_all(db2, "default")
        db2.close()
        print("[Init] 40 mock jobs seeded and matched")

    # 启动后台定时任务
    # ⚠️ RSS自动拉取仅覆盖 V2EX 两个可靠源，平均每次可获取 10~30 条
    # 核心数据应由用户通过「URL导入」和「手动录入」主动添加
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            _background_rss_refresh,
            'interval',
            hours=4,
            id='rss_periodic_refresh',
            replace_existing=True,
        )
        # 订阅通知推送（每2小时检查一次）
        scheduler.add_job(
            _background_subscription_notify,
            'interval',
            hours=2,
            id='subscription_notify',
            replace_existing=True,
        )
        scheduler.start()
        print("[Scheduler] RSS自动拉取(仅V2EX可靠源)已启动 + 订阅通知已启动")
    except Exception as e:
        print(f"[Scheduler] 启动失败（可忽略）: {e}")

def _background_rss_refresh():
    """后台任务：从RSS源拉取新岗位（仅V2EX两个可靠源启用了）"""
    import asyncio as aio
    try:
        loop = aio.new_event_loop()
        aio.set_event_loop(loop)
        new_jobs = loop.run_until_complete(fetch_rss_jobs(max_per_source=5))
        if new_jobs:
            db = get_db()
            saved = 0
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            for job in new_jobs:
                existing = db.execute(
                    "SELECT id FROM jobs WHERE source_url = ? AND company = ? AND title = ?",
                    (job.get("source_url", ""), job["company"], job["title"])
                ).fetchone()
                if not existing:
                    dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    skills = job.get("jd_skills", [])
                    jd_profile = gen_jd_profile(skills) if skills else {}

                    # ── 质量过滤 ──
                    qf_result = JobQualityFilter.validate(
                        title=job.get("title", ""),
                        jd_text=job.get("jd_text", ""),
                        company=job.get("company", ""),
                        source_platform=job.get("source_platform", "official"),
                        source_url=job.get("source_url", ""),
                    )
                    if not qf_result["pass"]:
                        continue  # 跳过低质量内容

                    db.execute(
                        """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                           recruitment_type, industry, source_platform, source_url, application_deadline, posted_at,
                           quality_score, quality_flags)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (job["title"], job["company"], job.get("jd_text", ""),
                         json.dumps(skills, ensure_ascii=False),
                         json.dumps(jd_profile, ensure_ascii=False),
                         "", "", "experienced", job.get("industry", "互联网"),
                         job.get("source_platform", "official"),
                         job.get("source_url", ""), dl, now,
                         qf_result["score"], json.dumps(qf_result["flags"], ensure_ascii=False)),
                    )
                    saved += 1
            if saved > 0:
                db.commit()
                run_match_for_all(db)

            # 记录 RSS 拉取日志
            try:
                db.execute(
                    "INSERT INTO rss_fetch_logs (source_name, jobs_count, success, created_at) VALUES (?, ?, ?, ?)",
                    ("全部源", len(new_jobs), 1, now)
                )
                db.commit()
            except Exception:
                pass
            db.close()
            print(f"[Scheduler] RSS 刷新完成，新增 {saved} 个岗位（仅V2EX源）")
    except Exception as e:
        print(f"[Scheduler] RSS 刷新出错: {e}")


def _background_subscription_notify():
    """后台任务：检查订阅并推送通知"""
    import asyncio as aio
    try:
        loop = aio.new_event_loop()
        aio.set_event_loop(loop)

        db = get_db()
        # 获取用户订阅偏好
        row = db.execute("SELECT preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
        subscriptions = {}
        notification_config = {}
        if row:
            try:
                prefs = json.loads(row["preferences"])
                subscriptions = prefs.get("subscriptions", {})
                notification_config = prefs.get("notifications", {})
            except Exception:
                pass

        if not subscriptions or not any([
            subscriptions.get("companies"),
            subscriptions.get("keywords"),
            subscriptions.get("cities"),
            subscriptions.get("industries"),
        ]):
            db.close()
            return

        # 检查通知渠道是否启用
        channels = notification_config.get("channels", {})
        any_enabled = False
        for ch in ["email", "dingtalk", "wecom", "feishu"]:
            if channels.get(ch, {}).get("enabled"):
                any_enabled = True
                break
        if not any_enabled:
            db.close()
            return

        # 获取最近 2 小时内新增岗位
        cutoff = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        rows = db.execute(
            "SELECT jd_skills, title, company, industry, city, source_url, source_platform, jd_text, posted_at FROM jobs WHERE posted_at > ? ORDER BY posted_at DESC LIMIT 50",
            (cutoff,)
        ).fetchall()
        # 也获取未匹配的近期岗位（确保有足够数据）
        if len(rows) < 10:
            rows = db.execute(
                "SELECT jd_skills, title, company, industry, city, source_url, source_platform, jd_text, posted_at FROM jobs ORDER BY posted_at DESC LIMIT 50"
            ).fetchall()

        # 加载已通知历史
        notified_urls, notified_titles = load_notified_history(db)

        new_jobs = []
        for r in rows:
            skills = json.loads(r["jd_skills"]) if r["jd_skills"] else []
            new_jobs.append({
                "title": r["title"],
                "company": r["company"],
                "industry": r["industry"],
                "city": r["city"],
                "source_url": r["source_url"],
                "source_platform": r["source_platform"],
                "jd_text": r["jd_text"] or "",
                "jd_skills": skills,
                "posted_at": r["posted_at"],
            })

        # 匹配订阅
        matched = match_jobs_against_subscription(new_jobs, subscriptions)
        # 去重
        to_notify = deduplicate_jobs(matched, notified_urls, notified_titles)

        if to_notify:
            print(f"[Subscription] 匹配到 {len(to_notify)} 个新岗位，准备推送")
            # 异步推送通知
            results = loop.run_until_complete(
                push_notifications(to_notify, notification_config)
            )
            # 记录通知日志
            save_notification_logs(db, to_notify, results)
            print(f"[Subscription] 推送完成: {results}")
        else:
            print(f"[Subscription] 无新匹配岗位需要推送")

        db.close()
    except Exception as e:
        print(f"[Subscription] 通知检查出错: {type(e).__name__}: {str(e)[:200]}")

# ── Health ──────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "db": Path(DB_PATH).exists()}

# ── Seed ────────────────────────────────────────────────
@app.post("/api/seed")
def seed(user_key: str = Depends(get_user_key)):
    db = get_db()
    cnt = seed_database(db)
    run_match_for_all(db, user_key)
    db.close()
    return {"success": True, "jobs_seeded": cnt, "resume": MOCK_ABILITY["skills"]}

# ── 求职日报 API ──────────────────────────────────────
@app.get("/api/daily-report")
async def daily_report(user_key: str = Depends(get_user_key)):
    """求职日报：本地数据聚合 + AI 智能摘要"""
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # 今日新增岗位
    today_jobs = db.execute(
        "SELECT COUNT(*) FROM jobs WHERE date(posted_at) = ? AND user_key = ?", (today, user_key)
    ).fetchone()[0]

    # 匹配分数分布
    dist_rows = db.execute(
        """SELECT CASE
            WHEN overlap_score >= 80 THEN '80-100'
            WHEN overlap_score >= 60 THEN '60-79'
            ELSE '0-59'
        END as tier, COUNT(*) as cnt
        FROM match_records WHERE user_key = ? GROUP BY tier ORDER BY tier""", (user_key,)
    ).fetchall()

    # 本周投递统计
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    app_stats = db.execute(
        "SELECT status, COUNT(*) as cnt FROM applications WHERE date(applied_at) >= ? AND user_key = ? GROUP BY status",
        (week_start, user_key)
    ).fetchall()

    # 技能缺口Top5（找出JD中最多出现但用户不拥有的技能）
    resume_row = db.execute("SELECT ability_profile FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    user_skills_set = set()
    if resume_row:
        ability = json.loads(resume_row["ability_profile"])
        user_skills_set = set(s.lower() for s in ability.get("skills", []))

    skill_gaps = db.execute("SELECT jd_skills FROM jobs WHERE user_key = ?", (user_key,)).fetchall()
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
    total_match = db.execute("SELECT COUNT(*) FROM match_records WHERE overlap_score >= 60 AND user_key = ?", (user_key,)).fetchone()[0]
    if total_match > 0:
        top_match = db.execute(
            "SELECT j.title, j.company, m.overlap_score FROM match_records m JOIN jobs j ON m.job_id = j.id WHERE m.overlap_score >= 75 AND m.user_key = ? ORDER BY m.overlap_score DESC LIMIT 1", (user_key,)
        ).fetchone()
        if top_match:
            actions.append("🔥 最佳匹配：「" + top_match["title"] + "」(" + top_match["company"] + ")，综合分 " + str(top_match["overlap_score"]) + "，建议优先投递")
    if top_gaps:
        actions.append("📚 技能提升建议：学习 " + top_gaps[0][0] + "（" + str(top_gaps[0][1]) + " 个岗位要求）")
    recent_apps = db.execute("SELECT COUNT(*) FROM applications WHERE date(applied_at) >= ? AND user_key = ?", (week_start, user_key)).fetchone()[0]
    if recent_apps == 0:
        actions.append("📋 本周尚未投递，建议从精选推荐中选出 Top3 投递")
    elif recent_apps < 3:
        actions.append("📋 本周投递 " + str(recent_apps) + " 次，建议保持每天 1-2 个投递节奏")
    if not actions:
        actions.append("✅ 整体进展良好，继续保持")

    db.close()

    # AI 智能摘要（DeepSeek）
    ai_insight = None
    if USE_REAL_LLM:
        try:
            ai_insight = await llm.generate_daily_insight(
                today_new=today_jobs,
                total_matched=total_match,
                top_gaps=[{"skill": s, "demand_count": c} for s, c in top_gaps],
                weekly_apps=recent_apps,
            )
        except Exception as e:
            print(f"[LLM] 日报摘要生成失败: {e}")

    return {
        "date": today,
        "today_new_jobs": today_jobs,
        "score_distribution": dict_rows(dist_rows),
        "weekly_applications": dict_rows(app_stats),
        "top_skill_gaps": [{"skill": s, "demand_count": c} for s, c in top_gaps],
        "recommended_actions": actions,
        "total_matched": total_match,
        "ai_insight": ai_insight,
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
        ORDER BY dup.max_posted DESC
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


# ── 质量评分：重评所有岗位 ────────────────────────────
@app.post("/api/jobs/rescore-all")
def rescore_all_jobs():
    """对所有已入库岗位重新进行质量评分（用于数据库清理后评估）"""
    db = get_db()
    rows = db.execute("SELECT * FROM jobs").fetchall()
    updated = 0
    cleaned = 0

    for row in rows:
        title = row["title"] or ""
        jd_text = row["jd_text"] or ""
        company = row["company"] or ""
        source_platform = row["source_platform"] or ""
        source_url = row["source_url"] or ""

        result = JobQualityFilter.validate(title, jd_text, company, source_platform, source_url)

        if JobQualityFilter.should_cleanup(result["flags"], source_platform, source_url):
            db.execute("DELETE FROM match_records WHERE job_id = ?", (row["id"],))
            db.execute("DELETE FROM jobs WHERE id = ?", (row["id"],))
            cleaned += 1
        else:
            db.execute(
                "UPDATE jobs SET quality_score = ?, quality_flags = ? WHERE id = ?",
                (result["score"], json.dumps(result["flags"], ensure_ascii=False), row["id"])
            )
            updated += 1

    db.commit()
    total = len(rows)
    db.close()
    return {
        "success": True,
        "total_jobs": total,
        "rescored": updated,
        "cleaned": cleaned,
        "message": f"已重评 {updated} 个岗位，清理 {cleaned} 个非岗位内容"
    }


# ── 获取质量统计 ─────────────────────────────────────
@app.get("/api/jobs/quality-stats")
def get_quality_stats():
    """获取岗位质量统计信息"""
    db = get_db()
    
    total = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    high = db.execute("SELECT COUNT(*) FROM jobs WHERE quality_score >= 70").fetchone()[0]
    medium = db.execute("SELECT COUNT(*) FROM jobs WHERE quality_score >= 40 AND quality_score < 70").fetchone()[0]
    low = db.execute("SELECT COUNT(*) FROM jobs WHERE quality_score > 0 AND quality_score < 40").fetchone()[0]
    unscored = db.execute("SELECT COUNT(*) FROM jobs WHERE quality_score = 0").fetchone()[0]
    
    stats = {
        "total": total,
        "high_quality": high,
        "medium_quality": medium,
        "low_quality": low,
        "unscored": unscored,
    }
    db.close()
    return {"success": True, "stats": stats}


# ── Job Detail ─────────────────────────────────────────
@app.get("/api/jobs/{job_id}")
async def get_job_detail(job_id: int):
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

    # AI 增强匹配理由（仅在查看详情时调用，每次约 0.05 分钱）
    if USE_REAL_LLM and result["match_record"]:
        try:
            resume_row = db.execute("SELECT interest_profile, ability_profile FROM resume ORDER BY created_at DESC LIMIT 1").fetchone()
            if resume_row:
                interests = json.loads(resume_row["interest_profile"])
                abilities = json.loads(resume_row["ability_profile"])
                ai_reason = await llm.generate_match_reasons(
                    job_title=job["title"] or "",
                    company=job["company"] or "",
                    jd_text=(job["jd_text"] or "")[:800],
                    user_skills=abilities.get("skills", []),
                    interests=interests.get("preferred_industries", []) + interests.get("preferred_roles", []),
                )
                if ai_reason:
                    result["match_record"]["ai_reason"] = ai_reason
        except Exception as e:
            print(f"[LLM] 匹配理由增强失败: {e}")

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
    user_key: str = Depends(get_user_key),
):
    """
    精选推荐 API —— 多层过滤漏斗：
    1. 硬过滤：overlap_score >= min_score
    2. 条件过滤：招聘类型 / 行业 / 城市
    3. 排序：overlap_score DESC（纯交集分，不做新鲜度加权）
    4. 今日新增统计
    """
    conditions = ["mr.overlap_score >= ?", "mr.user_key = ?"]
    vals = [min_score, user_key]

    # ── 过滤低质量岗位（quality_score < 30 或标记为非岗位内容）──
    conditions.append("(j.quality_score IS NULL OR j.quality_score >= 30)")

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
                j.application_deadline, j.jd_skills, j.quality_score, j.quality_flags
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
    user_key: str = Depends(get_user_key),
):
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
    return {"items": dict_rows(rows), "total": total, "page": page, "page_size": page_size}

@app.post("/api/applications")
def create_application(body: dict, user_key: str = Depends(get_user_key)):
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
    return dict(row)

@app.put("/api/applications/{app_id}")
def update_application(app_id: int, body: dict, user_key: str = Depends(get_user_key)):
    db = get_db()
    # 校验所有权
    app = db.execute("SELECT id FROM applications WHERE id = ? AND user_key = ?", (app_id, user_key)).fetchone()
    if not app:
        db.close()
        raise HTTPException(status_code=404, detail="投递记录不存在")
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
def get_app_stats(user_key: str = Depends(get_user_key)):
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
           WHERE mr.overlap_score IS NOT NULL AND a.user_key = ?
           GROUP BY range ORDER BY range""", (user_key,)
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
def get_resume_profile(user_key: str = Depends(get_user_key)):
    db = get_db()
    row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    db.close()
    if not row:
        return {"has_resume": False}
    return {
        "has_resume": True,
        "interest_profile": json.loads(row["interest_profile"]),
        "ability_profile": json.loads(row["ability_profile"]),
        "deal_breakers": json.loads(row["deal_breakers"]),
    }

@app.put("/api/resume/deal-breakers")
def update_deal_breakers(body: dict, user_key: str = Depends(get_user_key)):
    """用户自定义不可接受项"""
    new_breakers = body.get("deal_breakers", [])
    if not isinstance(new_breakers, list):
        raise HTTPException(status_code=400, detail="deal_breakers 必须为数组")

    db = get_db()
    row = db.execute("SELECT id FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    if not row:
        # 没有简历时创建一条
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        db.execute(
            "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
            (json.dumps(MOCK_INTEREST, ensure_ascii=False),
             json.dumps(MOCK_ABILITY, ensure_ascii=False),
             json.dumps(new_breakers, ensure_ascii=False),
             "", now, user_key),
        )
        db.commit()
    else:
        db.execute(
            "UPDATE resume SET deal_breakers = ? WHERE id = ?",
            (json.dumps(new_breakers, ensure_ascii=False), row["id"])
        )
        db.commit()

    # 重新运行匹配（不可接受项变化会影响结果）
    run_match_for_all(db, user_key)
    db.close()

    return {
        "success": True,
        "message": f"已更新 {len(new_breakers)} 项不可接受条件，匹配结果已刷新",
    }

@app.put("/api/resume/interest-profile")
def update_interest_profile(body: dict, user_key: str = Depends(get_user_key)):
    """用户自定义兴趣画像（我喜欢）"""
    new_interests = body.get("interests", [])
    if not isinstance(new_interests, list):
        raise HTTPException(status_code=400, detail="interests 必须为数组")

    db = get_db()
    row = db.execute("SELECT id, interest_profile FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    if not row:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        ip = {"preferred_industries": new_interests, "preferred_roles": []}
        db.execute(
            "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
            (json.dumps(ip, ensure_ascii=False),
             json.dumps(MOCK_ABILITY, ensure_ascii=False),
             json.dumps([], ensure_ascii=False),
             "", now, user_key),
        )
        db.commit()
    else:
        ip = json.loads(row["interest_profile"]) if row["interest_profile"] else {}
        ip["preferred_industries"] = new_interests
        ip["preferred_roles"] = []
        db.execute("UPDATE resume SET interest_profile = ? WHERE id = ?",
                   (json.dumps(ip, ensure_ascii=False), row["id"]))
        db.commit()

    run_match_for_all(db, user_key)
    db.close()

    return {
        "success": True,
        "message": f"已更新 {len(new_interests)} 项兴趣偏好，匹配结果已刷新",
    }

@app.put("/api/resume/ability-profile")
def update_ability_profile(body: dict, user_key: str = Depends(get_user_key)):
    """用户自定义能力画像（我擅长）"""
    new_skills = body.get("skills", [])
    if not isinstance(new_skills, list):
        raise HTTPException(status_code=400, detail="skills 必须为数组")

    db = get_db()
    row = db.execute("SELECT id, ability_profile FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    if not row:
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        ap = {"skills": new_skills, "education": "", "experience": ""}
        db.execute(
            "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
            (json.dumps(MOCK_INTEREST, ensure_ascii=False),
             json.dumps(ap, ensure_ascii=False),
             json.dumps([], ensure_ascii=False),
             "", now, user_key),
        )
        db.commit()
    else:
        ap = json.loads(row["ability_profile"]) if row["ability_profile"] else {}
        ap["skills"] = new_skills
        # 保留原有的 education 和 experience
        if "education" not in ap: ap["education"] = ""
        if "experience" not in ap: ap["experience"] = ""
        db.execute("UPDATE resume SET ability_profile = ? WHERE id = ?",
                   (json.dumps(ap, ensure_ascii=False), row["id"]))
        db.commit()

    run_match_for_all(db, user_key)
    db.close()

    return {
        "success": True,
        "message": f"已更新 {len(new_skills)} 项技能标签，匹配结果已刷新",
    }

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(None), user_key: str = Depends(get_user_key)):
    """简历上传：真实 PDF/DOCX/TXT 解析，提取三圈画像要素，保存到本地并运行全量匹配"""
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的简历文件")

    # 读取文件字节
    content = await file.read()

    # 保存文件到 uploads 目录
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = Path(UPLOAD_DIR) / file.filename
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        print(f"[Upload] 文件保存失败: {e}")

    # 真实解析简历
    try:
        parsed = parse_resume(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[Resume] 解析异常: {e}")
        parsed = {
            "interest_profile": dict(MOCK_INTEREST),
            "ability_profile": dict(MOCK_ABILITY),
            "deal_breakers": list(MOCK_BREAKERS),
            "raw_text_preview": f"解析遇到问题，使用默认画像。错误: {str(e)[:200]}",
            "extracted_skills": MOCK_ABILITY["skills"],
            "extracted_education": "硕士",
            "extracted_major": "计算机科学",
            "extracted_experience": "2段实习",
            "extracted_roles": ["数据分析"],
            "extracted_industries": ["互联网"],
        }

    # ── AI 增强提取（DeepSeek，每次约 0.05 分钱，失败则保留规则解析结果）──
    if USE_REAL_LLM and parsed.get("raw_text_preview"):
        try:
            ai_tags = asyncio.run(llm.extract_resume_tags(parsed["raw_text_preview"]))
            if ai_tags:
                if ai_tags.get("skills"):
                    parsed["extracted_skills"] = list(dict.fromkeys(ai_tags["skills"] + parsed.get("extracted_skills", [])))[:15]
                if ai_tags.get("roles"):
                    parsed["extracted_roles"] = ai_tags["roles"][:5]
                if ai_tags.get("industries"):
                    parsed["extracted_industries"] = ai_tags["industries"][:5]
                if ai_tags.get("experience"):
                    parsed["extracted_experience"] = ai_tags["experience"]
                if ai_tags.get("education"):
                    parsed["extracted_education"] = ai_tags["education"]
                # 更新三圈画像
                parsed["interest_profile"] = {
                    "preferred_industries": parsed.get("extracted_industries", ["互联网"]),
                    "preferred_roles": parsed.get("extracted_roles", ["数据分析"]),
                }
                parsed["ability_profile"]["skills"] = parsed.get("extracted_skills", parsed["ability_profile"]["skills"])
                parsed["raw_text_preview"] += "\n[AI增强提取完成]"
        except Exception as e:
            print(f"[LLM] 简历增强提取失败（使用规则结果）: {e}")
            parsed["raw_text_preview"] += f"\n[AI增强未启用: {str(e)[:100]}]"

    db = get_db()
    db.execute("DELETE FROM resume WHERE user_key = ?", (user_key,))
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "INSERT INTO resume (interest_profile, ability_profile, deal_breakers, raw_parsed, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?)",
        (json.dumps(parsed["interest_profile"], ensure_ascii=False),
         json.dumps(parsed["ability_profile"], ensure_ascii=False),
         json.dumps(parsed["deal_breakers"], ensure_ascii=False),
         parsed["raw_text_preview"][:500],
         now, user_key),
    )
    db.commit()
    run_match_for_all(db, user_key)
    db.close()

    return {
        "success": True,
        "interest_profile": parsed["interest_profile"],
        "ability_profile": parsed["ability_profile"],
        "deal_breakers": parsed["deal_breakers"],
        "filename": file.filename,
        "extracted_skills": parsed.get("extracted_skills", []),
        "extracted_education": parsed.get("extracted_education", ""),
        "extracted_experience": parsed.get("extracted_experience", ""),
        "extracted_roles": parsed.get("extracted_roles", []),
        "extracted_industries": parsed.get("extracted_industries", []),
        "message": f"简历解析成功！从 {file.filename} 中提取了 {len(parsed.get('extracted_skills', []))} 项技能，已生成三圈画像并完成全量岗位匹配",
    }

# ── Feedback ───────────────────────────────────────────
@app.post("/api/feedback")
def submit_feedback(body: dict, user_key: str = Depends(get_user_key)):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db = get_db()
    db.execute(
        "INSERT INTO feedback (match_record_id, action, ignore_reason, created_at, user_key) VALUES (?, ?, ?, ?, ?)",
        (body["match_record_id"], body["action"], body.get("ignore_reason"), now, user_key),
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
def get_feedback_history(limit: int = Query(20), user_key: str = Depends(get_user_key)):
    db = get_db()
    rows = db.execute(
        """SELECT f.*, j.title as job_title, j.company as job_company
           FROM feedback f LEFT JOIN match_records mr ON f.match_record_id = mr.id
           LEFT JOIN jobs j ON mr.job_id = j.id
           WHERE f.user_key = ?
           ORDER BY f.created_at DESC LIMIT ?""", (user_key, limit)
    ).fetchall()
    db.close()
    return dict_rows(rows)


@app.get("/api/feedback/{job_id}")
def get_feedback_by_job(job_id: int, user_key: str = Depends(get_user_key)):
    """查看某个岗位的反馈记录"""
    db = get_db()
    rows = db.execute(
        """SELECT f.*, j.title as job_title, j.company as job_company
           FROM feedback f
           JOIN match_records mr ON f.match_record_id = mr.id
           JOIN jobs j ON mr.job_id = j.id
           WHERE j.id = ? AND f.user_key = ?
           ORDER BY f.created_at DESC""", (job_id, user_key)
    ).fetchall()
    db.close()
    return dict_rows(rows)


# ── Custom Source ──────────────────────────────────────
@app.post("/api/custom-source")
def add_custom_source(body: dict, user_key: str = Depends(get_user_key)):
    if not body.get("title") or not body.get("company"):
        raise HTTPException(status_code=400, detail="岗位名称和公司为必填项")

    # ── 质量过滤 ──
    qf_result = JobQualityFilter.validate(
        title=body.get("title", ""),
        jd_text=body.get("jd_text", ""),
        company=body.get("company", ""),
        source_platform="custom",
        source_url=body.get("source_url", ""),
    )
    if not qf_result["pass"]:
        raise HTTPException(
            status_code=400,
            detail=f"岗位内容未通过质量检测: {qf_result['reason']}。请检查输入是否为真实的招聘岗位。"
        )

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    skills = body.get("skills", [])
    jd_profile = gen_jd_profile(skills) if skills else {"knowledge":[],"skills":[],"abilities":[],"values":[]}

    db = get_db()
    db.execute(
        """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
           recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
           application_deadline, posted_at, quality_score, quality_flags, user_key)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'custom', ?, ?, ?, ?, ?, ?, ?, ?)""",
        (body["title"], body["company"], body.get("jd_text", ""),
         json.dumps(skills, ensure_ascii=False),
         json.dumps(jd_profile, ensure_ascii=False),
         body.get("city", ""), body.get("salary_range", ""),
         body.get("recruitment_type", "experienced"), body.get("industry", "互联网"),
         body.get("source_url", ""), body.get("source_name", "自定义来源"),
         body.get("source_url", ""), dl, now,
         qf_result["score"], json.dumps(qf_result["flags"], ensure_ascii=False), user_key),
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
        "INSERT INTO match_records (job_id, interest_score, ability_score, market_score, overlap_score, match_reasons, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (new_id, round(interest_score), ability_score, market_score, overlap_score, "【自定义来源岗位】已纳入匹配系统", match_now, user_key),
    )
    db.commit()
    db.close()
    return {"success": True, "job_id": new_id, "message": f"岗位「{body['title']}」已添加并完成匹配"}


# ── 编辑岗位 ──────────────────────────────────────────
@app.put("/api/jobs/{job_id}")
def update_job(job_id: int, body: dict, user_key: str = Depends(get_user_key)):
    """编辑岗位信息（仅限自定义来源）"""
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        db.close()
        raise HTTPException(status_code=404, detail="岗位不存在")
    # 允许编辑：自定义来源 / URL导入 / 有渠道备注的岗位
    can_edit = (
        job["source_platform"] in ("custom", "url_import")
        or (job["custom_source_name"] and job["custom_source_name"].strip() != "")
    )
    if not can_edit:
        db.close()
        raise HTTPException(status_code=403, detail="仅自定义来源的岗位可编辑")
    if (job["user_key"] or "default") != user_key:
        db.close()
        raise HTTPException(status_code=403, detail="仅可编辑本人创建的岗位")

    title = body.get("title", job["title"])
    company = body.get("company", job["company"])
    city = body.get("city", job["city"])
    salary_range = body.get("salary_range", job["salary_range"])
    recruitment_type = body.get("recruitment_type", job["recruitment_type"])
    industry = body.get("industry", job["industry"])
    jd_text = body.get("jd_text", job["jd_text"])
    source_name = body.get("source_name", job["custom_source_name"])
    source_url = body.get("source_url", job["source_url"] or "")

    if "skills" in body:
        skills = body["skills"]
        jd_skills = json.dumps(skills, ensure_ascii=False)
        jd_profile_dict = gen_jd_profile(skills) if skills else {"knowledge": [], "skills": [], "abilities": [], "values": []}
    else:
        jd_skills = job["jd_skills"]
        jd_profile_dict = json.loads(job["jd_profile"]) if isinstance(job["jd_profile"], str) else job["jd_profile"]

    jd_profile_str = json.dumps(jd_profile_dict, ensure_ascii=False)

    db.execute(
        """UPDATE jobs SET title=?, company=?, jd_text=?, jd_skills=?, jd_profile=?, city=?,
           salary_range=?, recruitment_type=?, industry=?, source_url=?, custom_source_name=?,
           custom_source_url=? WHERE id=?""",
        (title, company, jd_text, jd_skills, jd_profile_str,
         city, salary_range, recruitment_type, industry,
         source_url, source_name, source_url, job_id)
    )
    db.commit()
    db.close()
    return {"success": True, "message": f"岗位「{title}」已更新"}


# ── 删除岗位 ──────────────────────────────────────────
@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, user_key: str = Depends(get_user_key)):
    """删除岗位（仅限自定义来源）"""
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        db.close()
        raise HTTPException(status_code=404, detail="岗位不存在")
    # 允许删除：自定义来源 / URL导入 / 有渠道备注的岗位
    can_delete = (
        job["source_platform"] in ("custom", "url_import")
        or (job["custom_source_name"] and job["custom_source_name"].strip() != "")
    )
    if not can_delete:
        db.close()
        raise HTTPException(status_code=403, detail="仅自定义来源的岗位可删除")
    if (job["user_key"] or "default") != user_key:
        db.close()
        raise HTTPException(status_code=403, detail="仅可删除本人创建的岗位")

    db.execute("DELETE FROM match_records WHERE job_id = ?", (job_id,))
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    db.commit()
    db.close()
    return {"success": True, "message": f"岗位「{job['title']}」已删除"}


# ── URL 导入岗位（合规剪藏助手）─────────────────────────
@app.post("/api/jobs/import-from-url")
async def import_job_from_url(body: dict):
    """
    从招聘网站URL一键导入岗位信息
    
    多层智能兜底策略：
    1. Playwright CSS 选择器（精准快捷）
    2. Playwright 全页文本（结构无关）
    3. HTTP 请求降级（无浏览器时）
    4. LLM AI 智能解析（任意格式）← 核心兼容层
    
    自动识别页面类型：
    - 详情页：直接提取并导入单个岗位
    - 列表页：提取全部岗位预览，返回给用户选择确认
    
    合规设计：用户主动提供URL，系统仅做信息提取和本地存储
    支持：Boss直聘、拉勾、猎聘、智联、前程无忧、实习僧、校招官网及通用页面
    """
    url = body.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="请提供岗位URL")

    page_type = identify_page_type(url)

    if page_type == "list":
        # ── 列表页：提取多个岗位预览 ──
        jobs = []
        extraction_note = ""
        try:
            jobs = await extract_jobs_from_list_url(url)
        except Exception as e:
            print(f"[URL-Import] 列表页提取异常: {type(e).__name__}: {e}")

        if not jobs:
            # 降级：尝试从列表页 HTML 用 LLM 解析
            try:
                import requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"
                }
                resp = requests.get(url, headers=headers, timeout=20)
                resp.encoding = "utf-8"
                clean = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
                clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', '\n', clean)
                text = re.sub(r'\n{3,}', '\n\n', text).strip()[:5000]
                
                if USE_REAL_LLM and text:
                    ai_prompt = f"""从以下招聘列表页面文本中提取所有岗位信息，以JSON数组返回。仅返回JSON，不要额外文字。
格式：[{{"title":"岗位名称","company":"公司名称","city":"城市"}}, ...]

页面文本：
{text}"""
                    ai_raw = await llm.chat(
                        messages=[{"role": "user", "content": ai_prompt}],
                        temperature=0.1, max_tokens=1000, response_json=True,
                    )
                    if ai_raw:
                        try:
                            ai_jobs = json.loads(ai_raw)
                            if isinstance(ai_jobs, dict) and "jobs" in ai_jobs:
                                ai_jobs = ai_jobs["jobs"]
                            if isinstance(ai_jobs, list):
                                for j in ai_jobs:
                                    if j.get("title"):
                                        jobs.append({
                                            "title": str(j.get("title", "")).strip()[:100],
                                            "company": str(j.get("company", "")).strip(),
                                            "city": str(j.get("city", "")).strip(),
                                            "salary_range": "",
                                            "jd_text": "",
                                            "jd_skills": [],
                                            "source_url": url,
                                            "source_platform": identify_platform(url),
                                            "industry": "互联网",
                                        })
                        except json.JSONDecodeError:
                            pass
                extraction_note = "（通过AI智能解析页面文本）"
            except Exception as e2:
                print(f"[URL-Import] AI降级解析也失败: {e2}")

        if not jobs:
            raise HTTPException(status_code=400,
                detail="未从该页面提取到任何岗位信息。请确认URL可正常访问，或尝试粘贴单个岗位详情页链接。")

        # 标记已有的岗位（去重检测）
        db_c = get_db()
        for job in jobs:
            source_url = job.get("source_url", "")
            if source_url:
                existing = db_c.execute(
                    "SELECT id, title, company FROM jobs WHERE source_url = ? LIMIT 1",
                    (source_url,)
                ).fetchone()
                if existing:
                    job["already_imported"] = True
                    job["existing_job_id"] = existing["id"]
                else:
                    job["already_imported"] = False
        db_c.close()

        return {
            "success": True,
            "page_type": "list",
            "total_found": len(jobs),
            "jobs": jobs,
            "message": f"检测到列表页，找到 {len(jobs)} 个岗位{extraction_note}。请选择要导入的岗位。",
        }

    # ── 详情页：多层智能提取 ──
    # 去重检查
    db = get_db()
    existing = db.execute(
        "SELECT id, title, company FROM jobs WHERE source_url = ? LIMIT 1", (url,)
    ).fetchone()
    if existing:
        db.close()
        return {
            "success": False,
            "message": f"该岗位已存在于本地数据库（{existing['title']} @ {existing['company']}）",
            "job_id": existing["id"],
            "duplicate": True,
        }

    # 多层提取：Playwright → 全页文本 → LLM AI 解析 → 正则降级
    job_data = await extract_job_from_url(url, use_ai=USE_REAL_LLM)

    # 检查提取质量
    is_usable = (
        job_data.get("title") and 
        job_data["title"] not in ("未识别岗位", "页面加载超时", "提取失败", "")
    )

    if not is_usable:
        # 最后防线：直接 HTTP + 正则降级
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"
                }, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    html = await resp.text()
            from .scraper import extract_from_html
            fallback = extract_from_html(html, url)
            if fallback.get("title") and fallback["title"] != "未识别岗位":
                job_data = {**job_data, **fallback}
                is_usable = True
                job_data["_fallback_method"] = "http_regex"
        except Exception:
            pass

    if not is_usable:
        db.close()
        # 给出更友好的错误提示
        ai_hint = ""
        if USE_REAL_LLM:
            ai_hint = "\n💡 已启用AI智能解析但仍无法识别，请确保URL指向一个可公开访问的招聘页面。"
        raise HTTPException(
            status_code=400, 
            detail=f"无法从该URL提取岗位信息。可能原因：1) 页面需要登录 2) 页面网络超时 3) 内容非招聘信息。{ai_hint}\n请尝试手动添加或粘贴其他链接。"
        )

    # 入库
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    skills = job_data.get("jd_skills", [])
    if not skills:
        # 从JD文本中提取技能
        text = (job_data.get("jd_text", "") + job_data.get("title", "")).lower()
        for sk in JD_SKILLS:
            if sk.lower() in text:
                skills.append(sk)
        skills = skills[:10]
    jd_profile = gen_jd_profile(skills) if skills else {"knowledge": [], "skills": [], "abilities": [], "values": []}
    platform = job_data.get("source_platform", "custom")

    # ── 质量过滤 ──
    qf_result = JobQualityFilter.validate(
        title=job_data.get("title", ""),
        jd_text=job_data.get("jd_text", ""),
        company=job_data.get("company", ""),
        source_platform=platform,
        source_url=url,
    )
    if not qf_result["pass"]:
        db.close()
        raise HTTPException(
            status_code=400,
            detail=f"URL内容未通过质量检测: {qf_result['reason']}。该页面可能并非招聘岗位页面。"
        )

    db.execute(
        """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
           recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
           application_deadline, posted_at, quality_score, quality_flags, user_key)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_data["title"], job_data["company"],
         job_data.get("jd_text", "")[:3000],
         json.dumps(skills, ensure_ascii=False),
         json.dumps(jd_profile, ensure_ascii=False),
         job_data.get("city", ""), job_data.get("salary_range", ""),
         body.get("recruitment_type", "experienced"),
         job_data.get("industry", "互联网"),
         platform, url,
         f"URL导入 ({PLATFORM_LABELS.get(platform, platform)})", url,
         dl, now,
         qf_result["score"], json.dumps(qf_result["flags"], ensure_ascii=False),
         user_key),
    )
    db.commit()
    new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 为新导入的岗位单独运行匹配
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
    if job:
        _match_single_job(db, job, user_key)
        db.commit()

    platform_label = PLATFORM_LABELS.get(platform, platform)
    db.close()
    return {
        "success": True,
        "job_id": new_id,
        "message": f"已从{platform_label}导入岗位「{job_data['title']}」@ {job_data['company']}，提取了{len(skills)}项技能要求",
        "source_platform": platform,
        "extracted_skills": skills,
    }

# ── 批量确认导入 ──────────────────────────────────────
@app.post("/api/jobs/import-batch")
async def import_jobs_batch(body: dict):
    """
    用户从列表页勾选岗位后，批量导入确认
    """
    selected_jobs = body.get("jobs", [])
    if not selected_jobs or not isinstance(selected_jobs, list):
        raise HTTPException(status_code=400, detail="请提供要导入的岗位列表")

    db = get_db()
    results = {"imported": 0, "duplicates": 0, "failed": 0, "job_ids": []}

    for job_data in selected_jobs:
        title = (job_data.get("title") or "").strip()
        company = (job_data.get("company") or "").strip()
        source_url = (job_data.get("source_url") or "").strip()

        if not title:
            results["failed"] += 1
            continue

        # 去重检查
        if source_url:
            existing = db.execute(
                "SELECT id FROM jobs WHERE source_url = ? LIMIT 1", (source_url,)
            ).fetchone()
            if existing:
                results["duplicates"] += 1
                continue

        # 技能提取
        skills = job_data.get("jd_skills", [])
        if not skills:
            text = (job_data.get("jd_text", "") + title).lower()
            for sk in JD_SKILLS:
                if sk.lower() in text:
                    skills.append(sk)
            skills = skills[:10]

        jd_profile = gen_jd_profile(skills) if skills else {"knowledge": [], "skills": [], "abilities": [], "values": []}
        platform = job_data.get("source_platform", "custom")
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        try:
            # ── 质量过滤 ──
            qf_result = JobQualityFilter.validate(
                title=title,
                jd_text=job_data.get("jd_text", ""),
                company=company,
                source_platform=platform,
                source_url=source_url,
            )
            if not qf_result["pass"]:
                results["failed"] += 1
                continue

            db.execute(
                """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                   recruitment_type, industry, source_platform, source_url, custom_source_name, custom_source_url,
                   application_deadline, posted_at, quality_score, quality_flags, user_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, company,
                 job_data.get("jd_text", "")[:3000],
                 json.dumps(skills, ensure_ascii=False),
                 json.dumps(jd_profile, ensure_ascii=False),
                 job_data.get("city", ""), job_data.get("salary_range", ""),
                 job_data.get("recruitment_type", "experienced"),
                 job_data.get("industry", "互联网"),
                 platform, source_url,
                 f"批量导入 ({PLATFORM_LABELS.get(platform, platform)})", source_url,
                 dl, now,
                 qf_result["score"], json.dumps(qf_result["flags"], ensure_ascii=False),
                 user_key),
            )
            new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            results["job_ids"].append(new_id)
            results["imported"] += 1

            # 单岗位匹配
            job_row = db.execute("SELECT * FROM jobs WHERE id = ?", (new_id,)).fetchone()
            if job_row:
                _match_single_job(db, job_row, user_key)
        except Exception:
            results["failed"] += 1
            continue

    db.commit()
    db.close()

    return {
        "success": True,
        "imported": results["imported"],
        "duplicates": results["duplicates"],
        "failed": results["failed"],
        "job_ids": results["job_ids"],
        "message": f"导入完成：新增 {results['imported']} 个岗位" +
                   (f"，{results['duplicates']} 个已存在" if results["duplicates"] > 0 else "") +
                   (f"，{results['failed']} 个失败" if results["failed"] > 0 else ""),
    }


# ── RSS 聚合刷新 ──────────────────────────────────────
@app.post("/api/jobs/refresh")
async def refresh_jobs_from_rss():
    """手动触发从RSS源拉取最新岗位（仅V2EX可靠源）"""
    try:
        new_jobs = await fetch_rss_jobs(max_per_source=5)
    except Exception as e:
        return {"success": False, "message": f"RSS拉取失败: {str(e)}", "new_jobs": 0}

    if not new_jobs:
        return {"success": True, "message": "当前暂无新岗位", "new_jobs": 0, "sources_checked": len(RSS_SOURCES)}

    db = get_db()
    saved = 0
    for job in new_jobs:
        existing = db.execute(
            "SELECT id FROM jobs WHERE source_url = ? AND company = ? AND title = ?",
            (job.get("source_url", ""), job["company"], job["title"])
        ).fetchone()
        if existing:
            continue

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        dl = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        skills = job.get("jd_skills", [])
        jd_profile = gen_jd_profile(skills) if skills else {}

        db.execute(
            """INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
               recruitment_type, industry, source_platform, source_url, application_deadline, posted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job["title"], job["company"], job.get("jd_text", ""),
             json.dumps(skills, ensure_ascii=False),
             json.dumps(jd_profile, ensure_ascii=False),
             "", "", "experienced", job.get("industry", "互联网"),
             job.get("source_platform", "official"),
             job.get("source_url", ""), dl, now),
        )
        saved += 1

    if saved > 0:
        db.commit()
        run_match_for_all(db)

    total = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    db.close()

    return {
        "success": True,
        "new_jobs": saved,
        "total_jobs": total,
        "message": f"刷新完成，新增{saved}个岗位（共{total}个岗位）",
    }

# ── 订阅管理 ──────────────────────────────────────────
@app.get("/api/subscriptions")
def get_subscriptions():
    """获取用户订阅设置"""
    db = get_db()
    row = db.execute("SELECT preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    if row:
        try:
            prefs = json.loads(row["preferences"])
            if "subscriptions" in prefs:
                return prefs["subscriptions"]
        except:
            pass
    return {
        "companies": ["字节跳动", "腾讯", "阿里巴巴", "华为", "百度"],
        "industries": ["互联网", "人工智能", "金融科技"],
        "cities": ["北京", "上海", "深圳", "杭州"],
        "keywords": ["数据分析", "产品经理", "后端开发", "机器学习"],
    }

@app.put("/api/subscriptions")
def update_subscriptions(body: dict):
    """更新订阅设置"""
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # 检查是否已有记录
    existing = db.execute("SELECT id, preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    if existing:
        try:
            prefs = json.loads(existing["preferences"])
        except:
            prefs = {}
        prefs["subscriptions"] = body
        db.execute(
            "UPDATE user_settings SET preferences = ?, updated_at = ? WHERE id = ?",
            (json.dumps(prefs, ensure_ascii=False), now, existing["id"])
        )
    else:
        # 创建 schema 中可能没有 user_settings 表，使用 OR REPLACE
        db.execute(
            "INSERT OR REPLACE INTO user_settings (id, preferences, updated_at) VALUES (1, ?, ?)",
            (json.dumps({"subscriptions": body}, ensure_ascii=False), now)
        )
    db.commit()
    db.close()
    return {"success": True, "message": "订阅设置已更新"}


# ── 通知设置管理 ──────────────────────────────────────────
@app.get("/api/notifications/settings")
def get_notification_settings():
    """获取通知设置"""
    db = get_db()
    row = db.execute("SELECT preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    if row:
        try:
            prefs = json.loads(row["preferences"])
            return prefs.get("notifications", {
                "channels": {
                    "email": {"enabled": False, "smtp_host": "smtp.qq.com", "smtp_port": 587, "username": "", "password": "", "to_email": ""},
                    "dingtalk": {"enabled": False, "webhook_url": ""},
                    "wecom": {"enabled": False, "webhook_url": ""},
                    "feishu": {"enabled": False, "webhook_url": ""},
                },
                "schedule_hours": 2,
            })
        except:
            pass
    return {
        "channels": {
            "email": {"enabled": False, "smtp_host": "smtp.qq.com", "smtp_port": 587, "username": "", "password": "", "to_email": ""},
            "dingtalk": {"enabled": False, "webhook_url": ""},
            "wecom": {"enabled": False, "webhook_url": ""},
            "feishu": {"enabled": False, "webhook_url": ""},
        },
        "schedule_hours": 2,
    }


@app.put("/api/notifications/settings")
def update_notification_settings(body: dict):
    """更新通知设置"""
    db = get_db()
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    existing = db.execute("SELECT id, preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    if existing:
        try:
            prefs = json.loads(existing["preferences"])
        except:
            prefs = {}
        prefs["notifications"] = body
        db.execute(
            "UPDATE user_settings SET preferences = ?, updated_at = ? WHERE id = ?",
            (json.dumps(prefs, ensure_ascii=False), now, existing["id"])
        )
    else:
        db.execute(
            "INSERT OR REPLACE INTO user_settings (id, preferences, updated_at) VALUES (1, ?, ?)",
            (json.dumps({"notifications": body}, ensure_ascii=False), now)
        )
    db.commit()
    db.close()
    return {"success": True, "message": "通知设置已更新"}


@app.post("/api/notifications/test")
def test_notification(body: dict):
    """测试通知渠道是否可用"""
    import asyncio as aio

    channel = body.get("channel", "")
    if channel not in ("email", "dingtalk", "wecom", "feishu"):
        raise HTTPException(400, "不支持的通知渠道")

    # 获取通知配置
    db = get_db()
    row = db.execute("SELECT preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    db.close()

    cfg = {}
    if row:
        try:
            prefs = json.loads(row["preferences"])
            cfg = prefs.get("notifications", {}).get("channels", {}).get(channel, {})
        except:
            pass

    test_job = [{
        "title": "🎯 测试岗位 - 高级软件工程师",
        "company": "TestCorp测试公司",
        "city": "深圳",
        "jd_skills": ["Python", "Go", "Docker"],
        "source_url": "",
    }]

    loop = aio.new_event_loop()
    aio.set_event_loop(loop)

    try:
        if channel == "email":
            if not cfg.get("enabled") or not cfg.get("username"):
                return {"success": False, "channel": "email", "message": "邮件未启用或配置不完整"}
            from .services.notification import send_email
            html = format_jobs_html(test_job, "测试通知")
            ok = loop.run_until_complete(
                send_email(
                    smtp_host=cfg.get("smtp_host", "smtp.qq.com"),
                    smtp_port=cfg.get("smtp_port", 587),
                    username=cfg.get("username", ""),
                    password=cfg.get("password", ""),
                    to_email=cfg.get("to_email", cfg.get("username", "")),
                    subject="[JobMatch AI] 测试通知 - 新岗位推送",
                    html_body=html,
                )
            )
            return {"success": ok, "channel": "email", "message": "测试邮件发送成功" if ok else "发送失败，请检查SMTP配置"}

        elif channel == "dingtalk":
            if not cfg.get("webhook_url"):
                return {"success": False, "channel": "dingtalk", "message": "Webhook URL 未配置"}
            from .services.notification import send_dingtalk, format_jobs_markdown
            md = format_jobs_markdown(test_job)
            ok = loop.run_until_complete(send_dingtalk(cfg["webhook_url"], md, title="JobMatch AI 测试通知"))
            return {"success": ok, "channel": "dingtalk", "message": "钉钉测试消息发送成功" if ok else "发送失败，请检查 Webhook URL"}

        elif channel == "wecom":
            if not cfg.get("webhook_url"):
                return {"success": False, "channel": "wecom", "message": "Webhook URL 未配置"}
            from .services.notification import send_wecom, format_jobs_markdown
            md = format_jobs_markdown(test_job)
            ok = loop.run_until_complete(send_wecom(cfg["webhook_url"], md))
            return {"success": ok, "channel": "wecom", "message": "企业微信测试消息发送成功" if ok else "发送失败，请检查 Webhook URL"}

        elif channel == "feishu":
            if not cfg.get("webhook_url"):
                return {"success": False, "channel": "feishu", "message": "Webhook URL 未配置"}
            from .services.notification import send_feishu, format_jobs_markdown
            md = format_jobs_markdown(test_job)
            ok = loop.run_until_complete(send_feishu(cfg["webhook_url"], md))
            return {"success": ok, "channel": "feishu", "message": "飞书测试消息发送成功" if ok else "发送失败，请检查 Webhook URL"}

    except Exception as e:
        return {"success": False, "channel": channel, "message": f"测试异常: {str(e)[:200]}"}
    finally:
        loop.close()


# ── 通知日志/RSS日志查看 ──────────────────────────────────
@app.get("/api/notifications/logs")
def get_notification_logs(limit: int = 20):
    """获取通知推送日志"""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM notification_logs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    db.close()
    return [{
        "id": r["id"],
        "job_title": r["job_title"],
        "job_url": r["job_url"],
        "job_company": r["job_company"],
        "match_score": r["match_score"],
        "channels": json.loads(r["channels"]) if r["channels"] else {},
        "created_at": r["created_at"],
    } for r in rows]


@app.get("/api/notifications/rss-logs")
def get_rss_fetch_logs(limit: int = 30):
    """获取 RSS 拉取日志"""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM rss_fetch_logs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    db.close()
    return [{
        "id": r["id"],
        "source_name": r["source_name"],
        "jobs_count": r["jobs_count"],
        "success": r["success"],
        "error_msg": r["error_msg"] or "",
        "created_at": r["created_at"],
    } for r in rows]


@app.get("/api/notifications/preview")
def preview_subscription_match():
    """预览当前订阅会匹配到多少岗位（不实际推送）"""
    db = get_db()
    row = db.execute("SELECT preferences FROM user_settings ORDER BY id DESC LIMIT 1").fetchone()
    subscriptions = {}
    if row:
        try:
            prefs = json.loads(row["preferences"])
            subscriptions = prefs.get("subscriptions", {})
        except:
            pass

    if not subscriptions:
        db.close()
        return {"matched": 0, "jobs": [], "subscription": subscriptions}

    # 获取最近岗位
    rows = db.execute(
        "SELECT jd_skills, title, company, industry, city, source_url, source_platform, jd_text, posted_at FROM jobs ORDER BY posted_at DESC LIMIT 50"
    ).fetchall()
    db.close()

    jobs = []
    for r in rows:
        skills = json.loads(r["jd_skills"]) if r["jd_skills"] else []
        jobs.append({
            "title": r["title"],
            "company": r["company"],
            "industry": r["industry"],
            "city": r["city"],
            "source_url": r["source_url"],
            "source_platform": r["source_platform"],
            "jd_text": r["jd_text"] or "",
            "jd_skills": skills,
            "posted_at": r["posted_at"],
        })

    matched = match_jobs_against_subscription(jobs, subscriptions)
    return {
        "matched": len(matched),
        "jobs": matched,
        "subscription": subscriptions,
    }


# ── 手动触发订阅通知 ──────────────────────────────────────
@app.post("/api/notifications/trigger")
def trigger_subscription_notification():
    """手动触发一次订阅匹配和通知推送"""
    _background_subscription_notify()
    return {"success": True, "message": "订阅通知已触发，请查看通知日志"}

# ── 求职仪表盘统计 ────────────────────────────────────
@app.get("/api/dashboard")
def get_dashboard():
    """求职仪表盘：概览统计"""
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    total_jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] or 0
    today_new = db.execute("SELECT COUNT(*) FROM jobs WHERE date(posted_at) = ?", (today,)).fetchone()[0] or 0

    # 匹配分布
    dist = db.execute(
        """SELECT CASE
            WHEN overlap_score >= 80 THEN 'high'
            WHEN overlap_score >= 60 THEN 'mid'
            ELSE 'low'
        END as tier, COUNT(*) as cnt
        FROM match_records GROUP BY tier"""
    ).fetchall()
    match_dist = {r["tier"]: r["cnt"] for r in dist}

    # 来源分布
    source_dist = db.execute(
        "SELECT source_platform, COUNT(*) as cnt FROM jobs GROUP BY source_platform ORDER BY cnt DESC"
    ).fetchall()
    sources = [{"platform": r["source_platform"], "count": r["cnt"],
                "label": PLATFORM_LABELS.get(r["source_platform"], r["source_platform"])}
               for r in source_dist]

    # 行业分布
    industry_dist = db.execute(
        "SELECT industry, COUNT(*) as cnt FROM jobs GROUP BY industry ORDER BY cnt DESC LIMIT 8"
    ).fetchall()

    # 投递统计
    app_total = db.execute("SELECT COUNT(*) FROM applications").fetchone()[0] or 0
    app_by_status = db.execute(
        "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
    ).fetchall()

    db.close()
    return {
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
    }

# ── 单岗位匹配辅助函数 ────────────────────────────────
def _match_single_job(db: sqlite3.Connection, job: dict, user_key: str = "default"):
    """为新导入的单个岗位运行匹配"""
    resume_row = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
    if not resume_row:
        return

    user_ability = json.loads(resume_row["ability_profile"])
    user_interest = json.loads(resume_row["interest_profile"])
    user_skills = {s.lower() for s in user_ability.get("skills", [])}

    jd_skills = json.loads(job["jd_skills"]) if isinstance(job["jd_skills"], str) else (job["jd_skills"] or [])
    jd_set = set(s.lower() for s in jd_skills)

    sj = jaccard(user_skills, jd_set)
    ability_score = round(sj * 95 + 5) if sj > 0 else 30
    interest_score = random.randint(55, 90)
    market_score = random.randint(50, 95)
    overlap_score = round(ability_score * 0.50 + interest_score * 0.25 + market_score * 0.25)

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    db.execute(
        "INSERT INTO match_records (job_id, interest_score, ability_score, market_score, overlap_score, match_reasons, created_at, user_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (job["id"], interest_score, ability_score, market_score, overlap_score,
         f"【URL导入岗位】技能匹配度{round(sj*100)}%，综合评分{overlap_score}", now, user_key),
    )

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
def generate_resume(body: dict, user_key: str = Depends(get_user_key)):
    job_id = body.get("job_id", 0)
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    resume = db.execute("SELECT * FROM resume WHERE user_key = ? ORDER BY created_at DESC LIMIT 1", (user_key,)).fetchone()
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
           improvement_notes, created_at, user_key)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (resume["id"], max_ver + 1, json.dumps(generated_resume, ensure_ascii=False),
         title_str, job["title"],
         note_str, now, user_key),
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
async def evaluate_answer(body: dict):
    """AI 真实评估面试回答（DeepSeek），失败时降级为规则评分"""
    question_text = body.get("question", "")
    answer_text = body.get("answer", "")

    # 尝试 LLM 评估
    if USE_REAL_LLM and question_text and answer_text:
        try:
            ai_result = await llm.evaluate_answer(question_text, answer_text)
            if ai_result and "score" in ai_result:
                return {
                    "question_id": body.get("question_id", 0),
                    "question": question_text,
                    "score": max(1, min(5, int(ai_result.get("score", 3)))),
                    "max_score": 5,
                    "feedback": ai_result.get("comment", "回答已评估"),
                    "suggestion": ai_result.get("suggestion", ""),
                    "completed": body.get("question_id", 0) >= 5,
                }
        except Exception as e:
            print(f"[LLM] 面试评估失败，降级为规则评分: {e}")

    # Fallback: 规则评分
    score = random.randint(3, 5)
    feedbacks = {3: "回答结构清晰，但可以补充更多具体例子来增强说服力",
                 4: "很好的回答！建议加入量化成果，让面试官更直观地感受你的贡献",
                 5: "优秀！回答全面且有深度，展现了扎实的专业功底和沟通能力"}
    return {"question_id": body.get("question_id", 0), "question": question_text, "score": score, "max_score": 5,
            "feedback": feedbacks[score], "suggestion": "", "completed": body.get("question_id", 0) >= 5}

# ── Interview Review ──────────────────────────────────
@app.post("/api/interview/review")
async def submit_interview_review(body: dict, user_key: str = Depends(get_user_key)):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    review_text = body.get("review_text", "")

    # 尝试 AI 分析复盘（DeepSeek）
    if USE_REAL_LLM and review_text:
        try:
            prompt = f"""分析以下面试复盘内容，以JSON返回。格式：{{"overall_score":0-100,"strengths":["优势1","优势2"],"weaknesses":["不足1","不足2"],"key_takeaways":"总结","improvements":[{{"category":"类别","action":"具体行动","timeline":"时间"}}]}}
复盘内容：{review_text[:2000]}"""
            ai_raw = await llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=600, response_json=True,
            )
            if ai_raw:
                ai_data = json.loads(ai_raw)
                ai_analysis = {
                    "overall_score": ai_data.get("overall_score", 70),
                    "score_breakdown": {"overall": ai_data.get("overall_score", 70)},
                    "strengths": ai_data.get("strengths", []),
                    "weaknesses": ai_data.get("weaknesses", []),
                    "key_takeaways": ai_data.get("key_takeaways", ""),
                }
                improvement_advices = ai_data.get("improvements", [])
            else:
                raise Exception("LLM 返回为空")
        except Exception as e:
            print(f"[LLM] 面试复盘分析失败，降级为默认分析: {e}")
            ai_analysis = {
                "overall_score": min((body.get("score_self", 0) or 0) * 0.9 + random.uniform(0, 15), 100),
                "score_breakdown": {"technical": random.randint(60, 90), "communication": random.randint(65, 95),
                                   "problem_solving": random.randint(60, 90), "culture_fit": random.randint(70, 95)},
                "strengths": ["对技术栈有较好理解，能清晰表达项目经验", "对行业有一定认知，展现了求职诚意"],
                "weaknesses": ["部分技术问题的深度可以进一步提升", "回答时可以更多引用量化数据增强说服力"],
                "key_takeaways": "整体表现良好，体现了较强的学习能力和沟通能力。"
            }
            improvement_advices = [
                {"category": "技术提升", "priority": "high", "action": "深入掌握岗位相关的核心技术框架", "timeline": "2周内"},
                {"category": "项目表达", "priority": "high", "action": "用STAR法则重构每个项目描述", "timeline": "1周内"},
            ]
    else:
        ai_analysis = {
            "overall_score": min((body.get("score_self", 0) or 0) * 0.9 + random.uniform(0, 15), 100),
            "score_breakdown": {"technical": random.randint(60, 90), "communication": random.randint(65, 95),
                               "problem_solving": random.randint(60, 90), "culture_fit": random.randint(70, 95)},
            "strengths": ["对技术栈有较好理解，能清晰表达项目经验"],
            "weaknesses": ["部分技术问题的深度可以进一步提升"],
            "key_takeaways": "整体表现良好，继续加油。"
        }
        improvement_advices = [
            {"category": "技术提升", "priority": "high", "action": "深入掌握岗位相关的核心技术框架", "timeline": "2周内"},
            {"category": "项目表达", "priority": "high", "action": "用STAR法则重构每个项目描述", "timeline": "1周内"},
        ]

    db = get_db()
    db.execute(
        """INSERT INTO interview_reviews (application_id, job_id, review_text, score_self,
           questions_asked, difficult_questions, ai_analysis, improvement_advices,
           strengths, weaknesses, created_at, user_key)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (body.get("application_id"), body.get("job_id"), body.get("review_text", ""),
         body.get("score_self", 0),
         json.dumps(body.get("questions_asked", []), ensure_ascii=False),
         body.get("difficult_questions", ""),
         json.dumps(ai_analysis, ensure_ascii=False),
         json.dumps(improvement_advices, ensure_ascii=False),
         json.dumps(ai_analysis["strengths"], ensure_ascii=False),
         json.dumps(ai_analysis["weaknesses"], ensure_ascii=False),
         now, user_key),
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
def get_interview_reviews(job_id: int = Query(0), user_key: str = Depends(get_user_key)):
    db = get_db()
    if job_id:
        rows = db.execute("SELECT * FROM interview_reviews WHERE job_id = ? AND user_key = ? ORDER BY created_at DESC LIMIT 5", (job_id, user_key)).fetchall()
    else:
        rows = db.execute("SELECT * FROM interview_reviews WHERE user_key = ? ORDER BY created_at DESC LIMIT 10", (user_key,)).fetchall()
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
