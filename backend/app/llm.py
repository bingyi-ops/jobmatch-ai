"""LLM 调用工具 — 统一封装 OpenAI 兼容协议调用，支持 DeepSeek / 通义千问 / Ollama 等"""
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from .config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, USE_REAL_LLM

MAX_RETRIES = 2
TIMEOUT = 25.0


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


async def chat(
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 600,
    response_json: bool = False,
) -> Optional[str]:
    """通用的 OpenAI 兼容 chat 调用（带重试）"""
    if not USE_REAL_LLM or not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-你的"):
        return None

    url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": model or LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}

    last_err = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(url, headers=_headers(), json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            last_err = str(e)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(1.5 * (attempt + 1))

    print(f"[LLM] 调用失败: {last_err}")
    return None


# ── 各场景封装（成本可控，每次调用约 0.1 分钱） ──────────

async def extract_resume_tags(jd_text: str) -> Optional[dict]:
    """从简历文本中 AI 提取：技能、经验、学历、意向岗位、意向行业"""
    prompt = f"""从以下简历文本中提取关键信息，以JSON返回。
仅返回JSON，不要任何额外文字。格式：
{{"skills":["技能1","技能2"],"experience":"x年","education":"学历","roles":["意向岗位"],"industries":["意向行业"]}}

简历：
{jd_text[:2500]}"""
    result = await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=400,
        response_json=True,
    )
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


async def generate_match_reasons(
    job_title: str,
    company: str,
    jd_text: str,
    user_skills: List[str],
    interests: List[str],
) -> Optional[str]:
    """AI 生成个性化匹配理由（代替模板硬拼接）"""
    skills_str = "、".join(user_skills[:10])
    interests_str = "、".join(interests[:8])
    prompt = f"""你是一个求职匹配助手。用1-2句话（不超过100字）总结这个岗位为什么适合该求职者。

岗位：{job_title} @ {company}
JD摘要：{jd_text[:800]}
求职者技能：{skills_str}
求职者兴趣：{interests_str}

直接返回中文理由，不要前缀。"""
    return await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150,
    )


async def evaluate_answer(
    question: str, answer: str, expected_keywords: str = ""
) -> Optional[dict]:
    """AI 评估面试回答"""
    prompt = f"""评估以下面试回答，以JSON返回。
格式：{{"score":1-5,"comment":"简短点评","suggestion":"改进建议"}}

问题：{question}
回答：{answer[:1200]}
{f"期望关键词：{expected_keywords}" if expected_keywords else ""}"""
    result = await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
        response_json=True,
    )
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


async def extract_job_info(page_text: str, url_hint: str = "") -> Optional[dict]:
    """从网页全文文本中 AI 智能提取岗位信息（最核心的兼容层）
    
    当 CSS 选择器无法匹配时，把整个页面的纯文本发给 LLM，
    LLM 能理解任意格式的自然语言，不受 HTML 结构变化影响。
    """
    if len(page_text) < 50:
        return None

    text = page_text[:3500]
    url_info = f"\n来源URL: {url_hint}" if url_hint else ""

    prompt = f"""从以下招聘页面文本中提取关键信息，以JSON返回。仅返回JSON，不要任何额外文字。
格式：
{{"job_title":"岗位名称","company":"公司名称","salary_range":"薪资范围","city":"工作城市","jd_summary":"岗位职责摘要(不超过150字)","skills":["技能1","技能2"],"industry":"所属行业","recruitment_type":"experienced|autumn_recruit|spring_recruit|summer_intern|daily_intern"}}

规则：
- 如果某项信息无法识别，使用空字符串或空数组
- skills 列出具体的技术栈或能力要求
- jd_summary 用简洁中文总结岗位核心职责

页面文本：
{text}{url_info}"""

    result = await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
        response_json=True,
    )
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


async def parse_jd_text(jd_text: str) -> Optional[dict]:
    """从用户粘贴的 JD 文本中 AI 智能提取岗位信息（不依赖网页爬取）"""
    if not jd_text or len(jd_text.strip()) < 20:
        return None

    text = jd_text.strip()[:3000]

    prompt = f"""从以下招聘JD文本中提取关键信息，以JSON返回。仅返回JSON，不要任何额外文字。
格式：
{{"job_title":"岗位名称","company":"公司名称","salary_range":"薪资范围","city":"工作城市","jd_summary":"岗位职责摘要(不超过100字)","skills":["技能1","技能2"],"industry":"所属行业","recruitment_type":"experienced|autumn_recruit|spring_recruit|summer_intern|daily_intern"}}

规则：
- 如果某项信息无法识别，使用空字符串或空数组
- skills 列出具体的技术栈或能力要求（如Python, SQL, Java, 数据分析等，最多12个）
- jd_summary 用简洁中文总结岗位核心职责
- recruitment_type 判断：校招相关→autumn_recruit或spring_recruit，实习相关→summer_intern或daily_intern，社招相关内容→experienced
- 薪资可能是月薪范围如"15k-25k"或年薪如"20万-35万"

JD文本：
{text}"""

    result = await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=600,
        response_json=True,
    )
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


async def generate_daily_insight(
    today_new: int,
    total_matched: int,
    top_gaps: List[Dict[str, Any]],
    weekly_apps: int,
) -> Optional[str]:
    """AI 生成每日求职洞察"""
    gaps_str = ", ".join([f"{g['skill']}(需求{g['demand_count']}个)" for g in (top_gaps or [])[:5]])
    prompt = f"""根据以下数据写一段50字左右的求职日报摘要：
今日新增岗位：{today_new}个
已匹配岗位：{total_matched}个
本周投递：{weekly_apps}次
技能缺口：{gaps_str}

直接返回中文摘要，简洁有力。"""
    return await chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150,
    )
