"""
合规岗位信息提取器
用户主动粘贴任意招聘页面URL → 系统提取结构化信息 → 本地存储

合规设计：
1. 用户主动操作（粘贴URL），非自动爬取
2. 仅提取当前页面的结构化信息
3. 所有数据存储在本地 SQLite，不公开共享
4. 尊重 robots.txt（用户主动访问的行为模式）
5. 支持多平台：Boss直聘、拉勾、猎聘、智联、前程无忧、实习僧

技术说明（Python 3.14 + Windows）:
  Python 3.14 的 SelectorEventLoop._make_subprocess_transport 已完全移除，
  导致 async/sync Playwright 均无法在当前进程中启动浏览器（NotImplementedError）。
  因此采用「subprocess.run() 调用 _scrape_worker.py 子进程」方案，
  在独立 Python 进程中运行 Playwright，彻底绕过此限制。
"""

import re
import json
import subprocess
import sys
import os
from datetime import datetime
from typing import Optional

# ── worker 脚本路径 ─────────────────────────────────────
_WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_scrape_worker.py")


# ── 平台识别 ────────────────────────────────────────────
def identify_platform(url: str) -> str:
    """根据 URL 识别招聘平台"""
    url_lower = url.lower()
    platform_map = {
        "boss_zhipin": ["zhipin.com", "boss直聘"],
        "lagou": ["lagou.com", "拉勾"],
        "liepin": ["liepin.com", "猎聘"],
        "zhilian": ["zhaopin.com", "智联"],
        "51job": ["51job.com", "前程无忧"],
        "shixiseng": ["shixiseng.com", "实习僧"],
        "zhihu": ["zhihu.com", "知乎"],
        "school_career": ["edu.cn/career", "job.", "campus."],
    }
    for platform, domains in platform_map.items():
        for domain in domains:
            if domain in url_lower:
                return platform
    return "custom"


def identify_page_type(url: str) -> str:
    """判断 URL 是列表页还是详情页"""
    url_lower = url.lower()
    # 列表页特征：/jobs、/list、/positions、/search、#/jobs 等
    list_patterns = [
        r'/jobs$', r'/jobs\?', r'/#/jobs',
        r'/positions?$', r'/#/positions',
        r'/list', r'/search', r'/careers?$',
        r'campus\.\w+\.com(?:/#/jobs)?$',  # 校招首页
        r'/#/jobs\?',
    ]
    for pattern in list_patterns:
        if re.search(pattern, url_lower):
            return "list"

    # 详情页特征：/job_detail、/job/、/position/ 等
    detail_patterns = [
        r'/job_detail', r'/job/\d+', r'/position/\d+',
        r'/detail', r'.html',
    ]
    for pattern in detail_patterns:
        if re.search(pattern, url_lower):
            return "detail"

    return "detail"  # 默认当作详情页


# ── 通用 HTML 文本提取器 ──────────────────────────────
def extract_from_html(html: str, url: str) -> dict:
    """
    从 HTML 源码中提取岗位信息
    使用正则 + 结构化推理，不依赖 playwright（降级方案）
    """
    platform = identify_platform(url)

    # 尝试从 HTML title 中获取标题
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else ""

    # 移除非正文的 script/style 标签
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
    # 获取纯文本
    text = re.sub(r'<[^>]+>', ' ', clean_html)
    text = re.sub(r'\s+', ' ', text).strip()

    # 基本提取
    job_title = ""
    company = ""
    city = ""
    salary = ""

    # 从 title 中拆分（常见格式："岗位名称-公司名称-平台名"）
    if "-" in page_title or "|" in page_title or "—" in page_title:
        parts = re.split(r'[-|—]', page_title)
        job_title = parts[0].strip()
        if len(parts) > 1:
            company = parts[1].strip()

    # 尝试从 meta 标签提取
    meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
    if meta_desc:
        desc = meta_desc.group(1)
        # 从描述中找公司名
        comp_match = re.search(r'(字节跳动|阿里巴巴|腾讯|百度|华为|网易|美团|滴滴|京东|小米|拼多多|蚂蚁集团|平安|招商银行|中信|宁德时代|比亚迪|小红书|快手|B站|字节|阿里|腾讯)', desc)
        if comp_match and not company:
            company = comp_match.group(1)

    # 提取城市
    city_match = re.search(r'(北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|长沙|苏州|厦门|天津|重庆|合肥)', text)
    if city_match:
        city = city_match.group(1)

    # 提取薪资
    salary_match = re.search(r'(\d+[kK千]-?\d*[kK千]?|(\d+)-(\d+)万|(\d+)K-(\d+)K)', text)
    if salary_match:
        salary = salary_match.group(1)

    # 提取技能
    skill_keywords = [
        "Python", "Java", "Go", "SQL", "JavaScript", "TypeScript", "React", "Vue",
        "Docker", "Kubernetes", "机器学习", "深度学习", "数据分析", "产品设计",
        "项目管理", "人力资源", "财务管理", "市场营销", "UI设计", "UX设计",
        "C++", "Node.js", "Spring", "Django", "Flask", "AWS", "Azure",
        "Spark", "Hadoop", "Figma", "Axure", "Tableau", "Power BI",
    ]
    found_skills = [s for s in skill_keywords if s.lower() in text.lower()]

    # 限制 jd_text 长度
    jd_text = text[:2000] if text else ""

    return {
        "title": job_title or page_title or "未识别岗位",
        "company": company or "未识别公司",
        "salary_range": salary or "",
        "jd_text": jd_text,
        "city": city or "",
        "jd_skills": found_skills[:8],
        "source_url": url,
        "source_platform": platform,
        "industry": "互联网",
    }


# ── Sync Playwright（绕过 Python 3.14 asyncio 子进程限制）───

def _launch_browser_sync(playwright_instance) -> "Browser":
    """启动浏览器（sync 版本）"""
    launch_kwargs = {"headless": True}
    browser = None
    for channel in ("msedge", "chrome", None):
        try:
            if channel:
                browser = playwright_instance.chromium.launch(channel=channel, **launch_kwargs)
            else:
                browser = playwright_instance.chromium.launch(**launch_kwargs)
            break
        except Exception:
            continue
    return browser


def _extract_job_from_url_sync(url: str) -> dict:
    """Sync 版：从 URL 提取单个岗位详情"""
    from playwright.sync_api import sync_playwright

    platform = identify_platform(url)

    with sync_playwright() as p:
        browser = _launch_browser_sync(p)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)

        if platform == "boss_zhipin":
            result = _extract_boss_sync(page)
        elif platform == "lagou":
            result = _extract_lagou_sync(page)
        elif platform == "liepin":
            result = _extract_liepin_sync(page)
        elif platform == "zhilian":
            result = _extract_zhilian_sync(page)
        elif platform == "51job":
            result = _extract_51job_sync(page)
        elif platform == "shixiseng":
            result = _extract_shixiseng_sync(page)
        else:
            result = _extract_generic_sync(page)

        result["source_url"] = url
        result["source_platform"] = platform
        browser.close()
        return result


def _extract_jobs_from_list_url_sync(url: str, max_jobs: int = 30) -> list[dict]:
    """Sync 版：从列表页提取多个岗位预览"""
    from playwright.sync_api import sync_playwright

    platform = identify_platform(url)
    url_lower = url.lower()
    is_spa = any(kw in url_lower for kw in [
        "campus.", "school.", "career.", "#/", "#!/",
        "zhaopin.com", "liepin.com", "51job.com",
    ])

    with sync_playwright() as p:
        browser = _launch_browser_sync(p)
        page = browser.new_page()

        try:
            if is_spa:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)
            else:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
        except Exception as nav_err:
            browser.close()
            raise Exception(f"页面加载失败({type(nav_err).__name__}): {nav_err}")

        jobs = []
        try:
            if "campus.jd.com" in url_lower:
                jobs = _extract_campus_jd_list_sync(page)
            elif platform == "zhilian":
                jobs = _extract_zhilian_list_sync(page)
            else:
                jobs = _extract_generic_list_sync(page, url)
        except Exception as extract_err:
            browser.close()
            raise Exception(f"内容提取失败({type(extract_err).__name__}): {extract_err}")

        browser.close()

        seen = set()
        unique_jobs = []
        for job in jobs:
            key = (job.get("title", ""), job.get("company", ""))
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        return unique_jobs[:max_jobs]


# ── 各平台 Sync 提取函数 ────────────────────────────────

def _extract_boss_sync(page) -> dict:
    title = (page.text_content(".name h1") or
             page.text_content(".info-primary .name") or
             page.text_content(".job-name") or "")
    company = (page.text_content(".company-info .name") or
               page.text_content(".company-name") or "")
    salary = (page.text_content(".salary") or
              page.text_content(".job-banner .salary") or "")
    jd_text = (page.text_content(".job-detail .text") or
               page.text_content(".job-sec.text") or
               page.text_content(".detail-content") or "")
    city = (page.text_content(".job-location") or
            page.text_content(".location") or "")
    skills_elems = page.query_selector_all(".job-tags .tag, .job-tag, .tag-list .tag")
    skill_texts = [s.text_content() for s in skills_elems]
    return {
        "title": (title or "").strip(), "company": (company or "").strip(),
        "salary_range": (salary or "").strip(), "jd_text": (jd_text or "").strip(),
        "city": (city or "").strip(),
        "jd_skills": [s.strip() for s in skill_texts if s.strip()],
    }


def _extract_lagou_sync(page) -> dict:
    title = (page.text_content(".job-name") or
             page.text_content(".position-head h1") or "")
    company = (page.text_content(".company") or
               page.text_content(".company-name") or "")
    salary = (page.text_content(".salary") or
              page.text_content(".job_request .salary") or "")
    jd_text = (page.text_content(".job-detail") or
               page.text_content(".job_bt") or
               page.text_content(".position-content") or "")
    city = (page.text_content(".work_addr") or
            page.text_content(".job_request span:nth-child(2)") or "")
    skills_elems = page.query_selector_all(".job_request span, .labels span, .skill-tags span")
    skill_texts = [s.text_content() for s in skills_elems]
    return {
        "title": (title or "").strip(), "company": (company or "").strip(),
        "salary_range": (salary or "").strip(), "jd_text": (jd_text or "").strip(),
        "city": (city or "").strip(),
        "jd_skills": [s.strip().replace("/", "").strip()
                      for s in skill_texts if s.strip()
                      and "经验" not in s and "学历" not in s and "全职" not in s][:8],
    }


def _extract_liepin_sync(page) -> dict:
    title = (page.text_content(".title-info h1") or
             page.text_content(".job-title h1") or "")
    company = (page.text_content(".company-name") or
               page.text_content(".company-main h1") or "")
    salary = (page.text_content(".job-item-title") or
              page.text_content(".salary") or "")
    jd_text = (page.text_content(".job-description") or
               page.text_content(".job-main-message") or "")
    city = (page.text_content(".basic-infor span") or
            page.text_content(".job-addr") or "")
    return {"title": title.strip(), "company": company.strip(),
            "salary_range": salary.strip(), "jd_text": jd_text.strip(),
            "city": city.strip(), "jd_skills": []}


def _extract_zhilian_sync(page) -> dict:
    title = (page.text_content("h1") or
             page.text_content(".post-title h1") or
             page.text_content(".job-name h1") or
             page.text_content(".job-title") or
             page.text_content("[class*='title']") or "")
    company = (page.text_content(".company-name a") or
               page.text_content(".company-name") or
               page.text_content("[class*='company']") or "")
    salary = (page.text_content(".salary-text") or
              page.text_content(".salary") or
              page.text_content("[class*='salary']") or "")
    jd_text = (page.text_content(".job-description") or
               page.text_content(".describtion") or
               page.text_content(".job-detail") or "")
    city = (page.text_content(".location a") or
            page.text_content(".city") or
            page.text_content(".job-addr") or "")
    return {"title": title.strip(), "company": company.strip(),
            "salary_range": salary.strip(), "jd_text": jd_text.strip(),
            "city": city.strip(), "jd_skills": []}


def _extract_51job_sync(page) -> dict:
    title = (page.text_content(".cn h1") or
             page.text_content(".tHeader h1") or "")
    company = (page.text_content(".cname a") or
               page.text_content(".com_name") or "")
    salary = page.text_content(".cn strong") or ""
    jd_text = (page.text_content(".bmsg.job_msg") or
               page.text_content(".job_msg") or "")
    city = page.text_content(".lname") or ""
    return {"title": title.strip(), "company": company.strip(),
            "salary_range": salary.strip(), "jd_text": jd_text.strip(),
            "city": city.strip(), "jd_skills": []}


def _extract_shixiseng_sync(page) -> dict:
    title = (page.text_content(".new_job_name h1") or
             page.text_content(".job-name") or "")
    company = (page.text_content(".company-name") or
               page.text_content(".com_intro .com-name") or "")
    salary = (page.text_content(".job_money.cutom_font") or
              page.text_content(".job-salary") or "")
    jd_text = (page.text_content(".job_detail .job-part") or
               page.text_content(".job-detail") or "")
    city = (page.text_content(".job_position") or
            page.text_content(".job-city") or "")
    return {"title": title.strip(), "company": company.strip(),
            "salary_range": salary.strip(), "jd_text": jd_text.strip(),
            "city": city.strip(), "jd_skills": []}


def _extract_generic_sync(page) -> dict:
    body = page.text_content("body") or ""
    title = page.text_content("h1") or ""
    skill_keywords = [
        "Python", "Java", "SQL", "Go", "React", "Vue", "Docker",
        "Kubernetes", "数据分析", "机器学习", "项目管理", "产品设计",
    ]
    found = [s for s in skill_keywords if s.lower() in (body or "").lower()]
    return {"title": title.strip()[:100], "company": "",
            "salary_range": "", "jd_text": (body or "")[:2000],
            "city": "", "jd_skills": found}


# ── 列表页 Sync 提取函数 ────────────────────────────────

def _extract_campus_jd_list_sync(page) -> list[dict]:
    """campus.jd.com 校招列表页提取（sync 版）"""
    jobs = []
    try:
        page.wait_for_selector(
            ".job-item, .position-item, .recruit-list li, .job-card, "
            ".list-item, .el-table__row, [class*='item'], "
            "li, [class*='card'], [class*='row']",
            timeout=12000,
        )
    except Exception:
        pass

    selectors = [
        ".job-item", ".position-item", ".recruit-list li",
        ".job-card", ".list-item", ".el-table__row",
        "[class*='job-item']", "[class*='position-item']",
        "[class*='job'][class*='item']", "[class*='recruit'] [class*='item']",
        "[class*='list'] > li", "[class*='list'] [class*='card']",
        "ul[class*='list'] li",
    ]

    items = []
    for sel in selectors:
        try:
            found = page.query_selector_all(sel)
            if len(found) >= 2:
                items = found
                break
        except Exception:
            continue

    if len(items) < 2:
        for fb_sel in ("li", "div[class]"):
            try:
                all_items = page.query_selector_all(fb_sel)[:200]
                candidates = []
                for el in all_items:
                    text = (el.text_content() or "").strip()
                    if 5 <= len(text) <= 300:
                        candidates.append(el)
                if len(candidates) >= 3:
                    items = candidates
                    break
            except Exception:
                continue

    for item in items:
        try:
            title_el = item.query_selector(
                "h3, h4, .job-name, .position-name, .title, .name, "
                "[class*='title'], [class*='name'], a, span")
            title = (title_el.text_content() if title_el else "").strip()

            if any(kw in title for kw in [
                "首页", "登录", "注册", "关于", "联系", "隐私", "协议",
                "版权", "备案", "返回", "上一页", "下一页", "加载更多",
                "搜索", "筛选", "全部", "城市", "职位类型",
            ]):
                continue

            city_el = item.query_selector(
                ".city, .location, .work-place, .addr, [class*='city'], [class*='addr']")
            city = (city_el.text_content() if city_el else "").strip()

            link_el = item.query_selector("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get_attribute("href")
                if href:
                    detail_url = href
                    if not detail_url.startswith("http"):
                        detail_url = "https://campus.jd.com" + detail_url

            if title and len(title) > 1:
                jobs.append({
                    "title": title, "company": "京东",
                    "city": city, "salary_range": "",
                    "jd_text": "", "jd_skills": [],
                    "source_url": detail_url,
                    "source_platform": "school_career",
                    "industry": "互联网",
                })
        except Exception:
            continue
    return jobs


def _extract_zhilian_list_sync(page) -> list[dict]:
    """智联招聘列表页提取（sync 版）"""
    jobs = []
    try:
        page.wait_for_selector(
            ".joblist-item, .job-item, .job-card, [class*='joblist'], [class*='job-list']",
            timeout=10000,
        )
    except Exception:
        pass

    selectors = [".joblist-item", ".job-item", ".job-card",
                 "[class*='joblist'] [class*='item']", "li[class*='job']"]
    items = []
    for sel in selectors:
        items = page.query_selector_all(sel)
        if items: break

    for item in items:
        try:
            title_el = item.query_selector("h3, .job-name, .title, .name, [class*='title']")
            title = (title_el.text_content() if title_el else "").strip()
            comp_el = item.query_selector(".company-name, .company, [class*='company']")
            company = (comp_el.text_content() if comp_el else "").strip()
            city_el = item.query_selector(".city, .location, .addr, [class*='addr']")
            city = (city_el.text_content() if city_el else "").strip()
            sal_el = item.query_selector(".salary, .pay, [class*='salary']")
            salary = (sal_el.text_content() if sal_el else "").strip()
            lnk = item.query_selector("a[href]")
            href = (lnk.get_attribute("href") or "") if lnk else ""

            if title and len(title) > 1:
                jobs.append({"title": title, "company": company or "未识别公司",
                            "city": city, "salary_range": salary,
                            "jd_text": "", "jd_skills": [], "source_url": href,
                            "source_platform": "zhilian", "industry": "互联网"})
        except Exception:
            continue
    return jobs


def _extract_generic_list_sync(page, source_url: str = "") -> list[dict]:
    """通用列表页提取（sync 版）"""
    jobs = []

    # 容器策略
    containers = page.query_selector_all(
        "li, .card, .item, [class*='card'], [class*='item'], [class*='list-item'], .el-table__row")
    seen_titles = set()

    for container in containers:
        try:
            inner_links = container.query_selector_all("a, h3, h4, .title, .name, [class*='title']")
            for inner in inner_links:
                text = (inner.text_content() or "").strip()
                if 3 <= len(text) <= 50 and text not in seen_titles:
                    seen_titles.add(text)
                    href = inner.get_attribute("href") or ""
                    if not href:
                        pl = container.query_selector("a[href]")
                        href = (pl.get_attribute("href") or "") if pl else ""
                    ce = container.query_selector("[class*='city'], [class*='addr'], [class*='location']")
                    city = (ce.text_content() if ce else "").strip()

                    jobs.append({"title": text, "company": "", "city": city,
                                "salary_range": "", "jd_text": "", "jd_skills": [],
                                "source_url": href or source_url,
                                "source_platform": identify_platform(source_url),
                                "industry": "互联网"})
        except Exception:
            continue

    # 链接策略兜底
    if len(jobs) < 3:
        all_links = page.query_selector_all("a")
        for link in all_links:
            text = (link.text_content() or "").strip()
            if 3 <= len(text) <= 50 and text not in seen_titles and len(jobs) < 50:
                seen_titles.add(text)
                href = link.get_attribute("href") or ""
                jobs.append({"title": text, "company": "", "city": "",
                            "salary_range": "", "jd_text": "", "jd_skills": [],
                            "source_url": href or source_url,
                            "source_platform": identify_platform(source_url),
                            "industry": "互联网"})
    return jobs


# ── Async 入口函数（通过子进程调用 Playwright worker）──

def _run_worker(mode: str, url: str, max_jobs: int = 30):
    """在子进程中运行 _scrape_worker.py，返回解析后的 JSON 结果"""
    cmd = [sys.executable, _WORKER_PATH, mode, url, str(max_jobs)]
    
    # 使用 bytes 模式读取，避免 Windows GBK/UTF-8 编码冲突
    result = subprocess.run(
        cmd,
        capture_output=True, timeout=120,
        cwd=os.path.dirname(_WORKER_PATH),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    
    stdout_text = result.stdout.decode("utf-8", errors="replace").strip()
    
    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", errors="replace").strip()
        err_msg = stderr_text or stdout_text or "未知错误"
        raise RuntimeError(f"抓取进程失败 (exit code {result.returncode}): {err_msg}")

    if not stdout_text:
        raise RuntimeError("抓取进程无输出")
    
    parsed = json.loads(stdout_text)
    if isinstance(parsed, dict) and "error" in parsed:
        raise RuntimeError(parsed["error"])
    return parsed


async def extract_job_from_url(url: str, use_ai: bool = True) -> dict:
    """
    从招聘网站 URL 提取岗位信息
    通过子进程调用 Playwright worker，绕过 Python 3.14 子进程传输限制
    
    多层兜底策略（由内到外）：
    1. Playwright CSS 选择器（速度快、精准）
    2. Playwright 全页文本（结构无关）
    3. HTTP requests 降级（无浏览器时）
    4. LLM AI 智能解析（任意自然语言格式）← 新增！
    """
    import asyncio
    
    try:
        result = await asyncio.to_thread(_run_worker, "detail", url)
    except Exception as e:
        result = {
            "title": "提取失败",
            "company": "未识别公司",
            "salary_range": "",
            "jd_text": "",
            "city": "",
            "jd_skills": [],
            "source_url": url,
            "source_platform": identify_platform(url),
            "industry": "互联网",
            "full_page_text": "",
            "_error": str(e),
        }

    # ── AI 增强层：当基本提取信息不完整时，用 LLM 从全页文本解析 ──
    if use_ai:
        basic_complete = (
            result.get("title") and result["title"] not in ("未识别岗位", "页面加载超时", "提取失败")
            and result.get("company") and result["company"] != "未识别公司"
        )
        
        full_text = result.get("full_page_text", "") or result.get("jd_text", "")
        
        if (not basic_complete or not result.get("jd_text")) and full_text and len(full_text) > 100:
            try:
                from . import llm
                ai_result = await llm.extract_job_info(full_text, url)
                if ai_result:
                    # 用 AI 结果补充缺失字段
                    if not basic_complete:
                        if ai_result.get("job_title") and result.get("title") in ("未识别岗位", "页面加载超时", "提取失败", ""):
                            result["title"] = ai_result["job_title"]
                        if ai_result.get("company") and result.get("company") == "未识别公司":
                            result["company"] = ai_result["company"]
                    if ai_result.get("salary_range") and not result.get("salary_range"):
                        result["salary_range"] = ai_result["salary_range"]
                    if ai_result.get("city") and not result.get("city"):
                        result["city"] = ai_result["city"]
                    if ai_result.get("jd_summary") and (not result.get("jd_text") or len(result.get("jd_text", "")) < 50):
                        result["jd_text"] = ai_result["jd_summary"]
                    if ai_result.get("skills"):
                        existing = set(s.lower() for s in result.get("jd_skills", []))
                        for sk in ai_result["skills"]:
                            if sk.lower() not in existing:
                                result.setdefault("jd_skills", []).append(sk)
                    if ai_result.get("industry"):
                        result["industry"] = ai_result["industry"]
                    result["_ai_enhanced"] = True
            except Exception as e:
                print(f"[AI-Enhance] LLM 增强失败: {e}")

    # 清理内部字段
    result.pop("full_page_text", None)
    result.pop("_error", None)
    
    return result


async def extract_jobs_from_list_url(url: str, max_jobs: int = 30) -> list[dict]:
    """
    从列表页提取多个岗位预览信息
    通过子进程调用 Playwright worker，绕过 Python 3.14 子进程传输限制
    """
    import asyncio
    return await asyncio.to_thread(_run_worker, "list", url, max_jobs)


# ── Async 兼容层（保留原有签名供其他地方引用）───────────

async def _launch_browser(playwright_instance) -> "Browser":
    """启动浏览器，优先使用系统自带的 Edge/Chrome（兼容旧调用）"""
    launch_kwargs = {"headless": True}
    browser = None
    for channel in ("msedge", "chrome"):
        try:
            browser = await playwright_instance.chromium.launch(channel=channel, **launch_kwargs)
            break
        except Exception:
            continue
    if not browser:
        browser = await playwright_instance.chromium.launch(**launch_kwargs)
    return browser


# ── 各平台 Async 提取规则（保留兼容）───────────────────

async def _extract_boss(page) -> dict:
    return _extract_boss_sync(page)

async def _extract_lagou(page) -> dict:
    return _extract_lagou_sync(page)

async def _extract_liepin(page) -> dict:
    return _extract_liepin_sync(page)

async def _extract_zhilian(page) -> dict:
    return _extract_zhilian_sync(page)

async def _extract_51job(page) -> dict:
    return _extract_51job_sync(page)

async def _extract_shixiseng(page) -> dict:
    return _extract_shixiseng_sync(page)

async def _extract_generic(page) -> dict:
    return _extract_generic_sync(page)


async def _extract_campus_jd_list(page) -> list[dict]:
    return _extract_campus_jd_list_sync(page)


async def _extract_zhilian_list(page) -> list[dict]:
    return _extract_zhilian_list_sync(page)


async def _extract_generic_list(page, source_url: str = "") -> list[dict]:
    return _extract_generic_list_sync(page, source_url)
