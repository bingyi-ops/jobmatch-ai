import math
from fastapi import APIRouter, Query
from ..database import database
from ..schemas import JobOut, JobSearchParams

router = APIRouter()


@router.get("/jobs/all")
async def get_all_jobs(
    page: int = 1,
    page_size: int = 20,
    platform: str = "",
    type: str = "",
    search: str = "",
):
    conditions = []
    params = {}
    if platform:
        conditions.append("source_platform = :platform")
        params["platform"] = platform
    if type:
        conditions.append("recruitment_type = :type")
        params["type"] = type
    if search:
        conditions.append("(title LIKE :s OR company LIKE :s OR jd_text LIKE :s)")
        params["s"] = f"%{search}%"

    where = " AND ".join(conditions) if conditions else "1=1"
    count_query = f"SELECT COUNT(*) FROM jobs WHERE {where}"
    total = await database.fetch_val(count_query, values=params)
    offset = (page - 1) * page_size
    query = f"SELECT * FROM jobs WHERE {where} ORDER BY posted_at DESC LIMIT :limit OFFSET :offset"
    rows = await database.fetch_all(query, values={**params, "limit": page_size, "offset": offset})

    return {
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": offset + page_size < total,
    }


@router.get("/jobs/search")
async def search_jobs(q: str = "", page: int = 1, page_size: int = 20):
    params = {"s": f"%{q}%", "limit": page_size, "offset": (page - 1) * page_size}
    count = await database.fetch_val(
        "SELECT COUNT(*) FROM jobs WHERE title LIKE :s OR company LIKE :s OR jd_text LIKE :s",
        values={"s": f"%{q}%"},
    )
    rows = await database.fetch_all(
        "SELECT * FROM jobs WHERE title LIKE :s OR company LIKE :s OR jd_text LIKE :s ORDER BY posted_at DESC LIMIT :limit OFFSET :offset",
        values=params,
    )
    return {"items": [dict(r) for r in rows], "total": count, "page": page, "page_size": page_size}


@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: int):
    row = await database.fetch_one("SELECT * FROM jobs WHERE id = :id", values={"id": job_id})
    if not row:
        return {"error": "not found"}, 404
    job = dict(row)
    # Check for match record
    match = await database.fetch_one(
        "SELECT * FROM match_records WHERE job_id = :jid ORDER BY created_at DESC LIMIT 1",
        values={"jid": job_id},
    )
    job["match_record"] = dict(match) if match else None
    return job


@router.get("/jobs/{job_id}/similar")
async def get_similar_jobs(job_id: int, limit: int = 5):
    job = await database.fetch_one("SELECT * FROM jobs WHERE id = :id", values={"id": job_id})
    if not job:
        return {"items": []}

    # Priority: same company > same industry > same city > same salary range
    rows = await database.fetch_all(
        """
        SELECT j.*, COALESCE(mr.overlap_score, -1) as overlap
        FROM jobs j
        LEFT JOIN match_records mr ON j.id = mr.job_id
        WHERE j.id != :id
        ORDER BY
            CASE WHEN j.company = :company THEN 0 ELSE 1 END,
            CASE WHEN j.industry = :industry THEN 0 ELSE 1 END,
            CASE WHEN j.city = :city THEN 0 ELSE 1 END,
            j.posted_at DESC
        LIMIT :limit
        """,
        values={"id": job_id, "company": job["company"], "industry": job["industry"], "city": job["city"], "limit": limit},
    )
    return {"items": [dict(r) for r in rows]}


@router.get("/jobs/{job_id}/company-info")
async def get_company_info(job_id: int):
    job = await database.fetch_one("SELECT * FROM jobs WHERE id = :id", values={"id": job_id})
    if not job:
        return {"error": "not found"}, 404

    # Mock LLM-generated company info (in prod, use LLM inference)
    company_infos = {
        "字节跳动": {"funding": "Pre-IPO (估值$268B)", "scale": "100,000+人", "position": "全球最大独角兽，短视频/推荐系统领先", "news": "2025年海外TikTok Shop GMV突破$500亿", "culture": ["扁平化管理", "快速迭代", "数据驱动", "技术信仰"]},
        "阿里巴巴": {"funding": "纽交所+港交所上市 (NYSE:BABA)", "scale": "200,000+人", "position": "中国最大电商平台，云计算领先", "news": "2025Q1云业务营收同比增长6%", "culture": ["客户第一", "拥抱变化", "团队合作", "激情"]},
        "腾讯": {"funding": "港交所上市 (00700.HK)", "scale": "100,000+人", "position": "中国最大社交+游戏公司，投资版图广泛", "news": "2025年混元大模型全面接入微信生态", "culture": ["用户为本", "科技向善", "开放协作", "创新突破"]},
        "百度": {"funding": "纳斯达克上市 (NASDAQ:BIDU)", "scale": "40,000+人", "position": "中国AI先行者，自动驾驶领先", "news": "文心一言4.0发布，萝卜快跑覆盖20城", "culture": ["简单可依赖", "技术驱动", "创新突破"]},
        "华为": {"funding": "未上市 (员工持股)", "scale": "200,000+人", "position": "全球通信设备+手机巨头", "news": "鸿蒙生态设备超10亿台，昇腾AI芯片量产", "culture": ["以奋斗者为本", "狼性文化", "技术立身", "长期投入"]},
        "网易": {"funding": "纳斯达克+港交所上市", "scale": "30,000+人", "position": "头部游戏+在线教育公司", "news": "2025年多款新游全球上线", "culture": ["创新", "匠心", "和用户在一起"]},
        "拼多多": {"funding": "纳斯达克上市 (NASDAQ:PDD)", "scale": "15,000+人", "position": "中国增长最快电商，Temu全球化", "news": "Temu覆盖70+国家，2025年营收翻倍", "culture": ["本分", "极致效率", "消费者导向"]},
    }
    default_info = {"funding": "信息暂缺", "scale": "信息暂缺", "position": "信息暂缺", "news": "暂无近期动态", "culture": ["信息暂缺"]}
    info = company_infos.get(job["company"], default_info)

    return {
        "company": job["company"],
        "funding_stage": info["funding"],
        "employee_scale": info["scale"],
        "industry_position": info["position"],
        "recent_news": info["news"],
        "culture_keywords": info["culture"],
        "disclaimer": "基于公开信息推断，仅供参考",
    }
