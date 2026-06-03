"""Generate 40 mock job records and seed the database."""
import json
import random
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.database import database

random.seed(42)

COMPANIES = [
    ("字节跳动", "互联网"),
    ("阿里巴巴", "互联网"),
    ("腾讯", "互联网"),
    ("百度", "互联网"),
    ("华为", "互联网"),
    ("网易", "互联网"),
    ("拼多多", "互联网"),
    ("宁德时代", "制造业"),
    ("比亚迪", "制造业"),
    ("大疆", "制造业"),
    ("格力", "制造业"),
    ("美的", "制造业"),
    ("三一重工", "制造业"),
    ("招商银行", "金融"),
    ("中信证券", "金融"),
    ("平安科技", "金融"),
    ("蚂蚁集团", "金融"),
    ("京东金融", "金融"),
    ("微众银行", "金融"),
    ("好未来", "教育"),
    ("新东方", "教育"),
    ("高途", "教育"),
    ("猿辅导", "教育"),
    ("学而思", "教育"),
    ("迈瑞医疗", "医疗"),
    ("恒瑞医药", "医疗"),
    ("药明康德", "医疗"),
    ("联影医疗", "医疗"),
    ("华大基因", "医疗"),
    ("麦肯锡", "咨询"),
    ("波士顿咨询", "咨询"),
    ("贝恩", "咨询"),
    ("罗兰贝格", "咨询"),
    ("安永", "咨询"),
    ("宝洁", "快消"),
    ("联合利华", "快消"),
    ("玛氏", "快消"),
    ("百事", "快消"),
    ("可口可乐", "快消"),
    ("欧莱雅", "快消"),
]

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"]
RECRUITMENT_TYPES = ["daily_intern", "summer_intern", "autumn_recruit", "spring_recruit", "experienced"]
PLATFORMS = ["official", "boss_zhipin", "xiaohongshu", "wechat_public"]
SALARY_RANGES = ["15k-25k", "20k-35k", "25k-40k", "30k-50k", "18k-28k", "22k-32k", "12k-20k", "35k-55k"]

JOB_TITLES = [
    "数据分析师", "产品经理", "算法工程师", "后端开发工程师", "前端开发工程师",
    "运营专员", "市场推广经理", "HRBP", "软件测试工程师", "UI/UX设计师",
    "机器学习工程师", "数据挖掘工程师", "商业分析师", "战略分析师", "项目经理",
    "销售经理", "品牌经理", "供应链管理", "财务分析师", "投资者关系",
]

JD_SKILLS_POOL = [
    "Python", "SQL", "Excel", "Tableau", "机器学习", "深度学习", "PyTorch",
    "TensorFlow", "Spark", "Hadoop", "Docker", "Kubernetes", "AWS", "GCP",
    "React", "Vue", "TypeScript", "Node.js", "Go", "Java", "Spring Boot",
    "数据分析", "AB测试", "统计学", "Power BI", "Figma", "产品设计",
    "项目管理", "敏捷开发", "沟通能力", "团队协作", "英语流利",
    "市场营销", "SEO", "SEM", "内容运营", "用户增长",
]


def generate_jd(title, company, industry):
    skills = random.sample(JD_SKILLS_POOL, random.randint(4, 8))
    jd_text = f"""【岗位描述】
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
    return jd_text, skills


def generate_jd_profile(skills):
    return {
        "knowledge": [s for s in skills if s in ["Python", "SQL", "统计学", "机器学习"]],
        "skills": skills,
        "abilities": [s for s in skills if s in ["项目管理", "沟通能力", "团队协作"]],
        "values": ["数据驱动", "结果导向", "快速迭代", "团队合作"],
    }


async def seed():
    await database.connect()

    # Create tables
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql"), "r") as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            await database.execute(stmt)

    # Clear existing data
    await database.execute("DELETE FROM feedback")
    await database.execute("DELETE FROM match_records")
    await database.execute("DELETE FROM applications")
    await database.execute("DELETE FROM resume")
    await database.execute("DELETE FROM jobs")

    from datetime import datetime, timedelta

    now = datetime.now()
    post_dates = [
        (now - timedelta(hours=random.randint(1, 23))).strftime("%Y-%m-%dT%H:%M:%S")  # Today (6)
        for _ in range(6)
    ] + [
        (now - timedelta(days=1, hours=random.randint(1, 23))).strftime("%Y-%m-%dT%H:%M:%S")  # Yesterday (8)
        for _ in range(8)
    ] + [
        (now - timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%dT%H:%M:%S")  # 3-7 days (12)
        for _ in range(12)
    ] + [
        (now - timedelta(days=random.randint(8, 30))).strftime("%Y-%m-%dT%H:%M:%S")  # 7-30 days (14)
        for _ in range(14)
    ]
    random.shuffle(post_dates)

    jobs_data = []
    for i in range(40):
        company, industry = COMPANIES[i % len(COMPANIES)]
        title = random.choice(JOB_TITLES)
        city = random.choice(CITIES)
        rec_type = random.choice(RECRUITMENT_TYPES)
        platform = random.choice(PLATFORMS)
        salary = random.choice(SALARY_RANGES)
        posted = post_dates[i]

        # Deadline: 1-30 days from posted
        posted_dt = datetime.strptime(posted, "%Y-%m-%dT%H:%M:%S")
        deadline_days = random.choice([random.randint(1, 3), random.randint(4, 7), random.randint(8, 14), random.randint(15, 30)][:4])
        deadline = (posted_dt + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

        jd_text, skills = generate_jd(title, company, industry)
        jd_profile = generate_jd_profile(skills)

        source_url = f"https://www.example.com/jobs/{company}/{i+1}"

        await database.execute(
            """
            INSERT INTO jobs (title, company, jd_text, jd_skills, jd_profile, city, salary_range,
                            recruitment_type, industry, source_platform, source_url, embedding_json,
                            application_deadline, posted_at)
            VALUES (:t, :c, :jd, :jds, :jdp, :city, :sal, :rt, :ind, :sp, :su, '[]', :ad, :pa)
            """,
            values={
                "t": title, "c": company, "jd": jd_text,
                "jds": json.dumps(skills, ensure_ascii=False),
                "jdp": json.dumps(jd_profile, ensure_ascii=False),
                "city": city, "sal": salary, "rt": rec_type,
                "ind": industry, "sp": platform, "su": source_url,
                "ad": deadline, "pa": posted,
            },
        )

    print(f"✅ Seeded {40} jobs into database")

    # Save to JSON for reference
    rows = await database.fetch_all("SELECT * FROM jobs ORDER BY posted_at DESC")
    jobs_json = [dict(r) for r in rows]
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_jobs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(jobs_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(jobs_json)} jobs to {out_path}")

    await database.disconnect()


if __name__ == "__main__":
    asyncio.run(seed())
