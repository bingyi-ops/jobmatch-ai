"""
Playwright 抓取子进程 worker

被 scraper.py 通过 subprocess.run() 调用，
在独立进程中执行 Playwright 浏览器自动化，
绕过 Python 3.14 Windows 的 asyncio 子进程传输限制。

用法：
    python _scrape_worker.py <mode> <url> [max_jobs]

mode: detail | list
"""
import sys
import json
import os
import re
from datetime import datetime


# ── 确保能导入 app 模块 ────────────────────────────────
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


def identify_platform(url: str) -> str:
    url_lower = url.lower()
    platform_map = {
        "boss_zhipin": ["zhipin.com", "boss直聘"],
        "lagou": ["lagou.com", "拉勾"],
        "liepin": ["liepin.com", "猎聘"],
        "zhilian": ["zhaopin.com", "智联"],
        "51job": ["51job.com", "前程无忧"],
        "shixiseng": ["shixiseng.com", "实习僧"],
        "school_career": ["edu.cn/career", "job.", "campus."],
    }
    for platform, domains in platform_map.items():
        for domain in domains:
            if domain in url_lower:
                return platform
    return "custom"


def extract_from_html(html, url):
    """降级提取：从 HTML 源码用正则提取岗位信息"""
    platform = identify_platform(url)
    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    page_title = title_match.group(1).strip() if title_match else ""
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', clean_html)
    text = re.sub(r'\s+', ' ', text).strip()
    job_title = ""
    company = ""
    if "-" in page_title or "|" in page_title or "\u2014" in page_title:
        parts = re.split(r'[-|\u2014]', page_title)
        job_title = parts[0].strip()
        if len(parts) > 1:
            company = parts[1].strip()
    city_match = re.search(r'(北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|长沙|苏州|厦门|天津|重庆|合肥)', text)
    city = city_match.group(1) if city_match else ""
    salary_match = re.search(r'(\d+[kK千]-?\d*[kK千]?|(\d+)-(\d+)万|(\d+)K-(\d+)K)', text)
    salary = salary_match.group(1) if salary_match else ""
    skill_keywords = [
        "Python", "Java", "Go", "SQL", "JavaScript", "TypeScript", "React", "Vue",
        "Docker", "Kubernetes", "机器学习", "深度学习", "数据分析",
    ]
    found_skills = [s for s in skill_keywords if s.lower() in text.lower()]
    return {
        "title": job_title or page_title or "未识别岗位",
        "company": company or "未识别公司",
        "salary_range": salary or "",
        "jd_text": text[:2000] if text else "",
        "city": city or "",
        "jd_skills": found_skills[:8],
        "source_url": url,
        "source_platform": platform,
        "industry": "互联网",
    }


def _safe_text(page, selectors, timeout=3000):
    """安全提取文本：多个选择器逐一尝试，不超时就取第一个匹配的"""
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                text = (el.text_content() or "").strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _safe_text_all(page, selector, timeout=3000):
    """安全提取多个元素文本列表"""
    try:
        elems = page.query_selector_all(selector)
        return [e.text_content().strip() for e in elems if e.text_content()]
    except Exception:
        return []


def _launch_browser(p):
    """启动浏览器"""
    # 设置更强的反反爬参数
    for channel in ("msedge", "chrome"):
        try:
            return p.chromium.launch(
                channel=channel,
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
        except Exception:
            continue
    return p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ],
    )


def scrape_detail(url: str) -> dict:
    """提取单个岗位详情（sync Playwright）—— 多层容错架构"""
    from playwright.sync_api import sync_playwright

    platform = identify_platform(url)
    html_result = None  # 用于浏览器完全失败时的 HTTP requests 降级

    try:
        with sync_playwright() as p:
            browser = _launch_browser(p)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            # ── 阶段1: 多级页面加载策略 ──
            html_fallback = ""
            for strategy in (
                ("networkidle", 20000),   # 先尝试 networkidle（较短超时）
                ("domcontentloaded", 15000),  # 降级到 domcontentloaded
                ("load", 10000),              # 最后试 load
            ):
                wait_until, timeout = strategy
                try:
                    page.goto(url, wait_until=wait_until, timeout=timeout)
                    page.wait_for_timeout(2000)  # 额外等待动态渲染
                    break
                except Exception:
                    continue
            else:
                # 所有策略都失败，尝试获取已渲染的 HTML
                try:
                    html_fallback = page.evaluate("() => document.documentElement.outerHTML") or ""
                except Exception:
                    pass

            # ── 阶段2: 获取全页文本（兜底数据） ──
            full_page_text = ""
            try:
                full_page_text = page.evaluate("() => document.body.innerText") or ""
            except Exception:
                try:
                    full_page_text = page.text_content("body") or ""
                except Exception:
                    pass

            # ── 阶段3: CSS 选择器精确提取（最佳效果） ──
            title = _safe_text(page, [
                "h1", ".job-title", ".job-name", ".position-name",
                "[class*='title']", "[class*='name'][class*='job']",
                ".cn h1", ".title-info h1",
            ]) or ""

            company = _safe_text(page, [
                ".company-name", ".company-info .name",
                ".cname a", ".com_name", ".company a",
                "[class*='company'][class*='name']",
                "[class*='company'] a",
            ]) or ""

            salary = _safe_text(page, [
                ".salary", ".salary-text", ".cn strong",
                ".job_salary", "[class*='salary']",
                ".job-item-title", ".job_money",
            ]) or ""

            jd_text = _safe_text(page, [
                ".job-detail", ".describtion", ".job-content",
                ".bmsg.job_msg", ".job_msg", ".job-sec.text",
                ".job-description", ".position-content",
                ".job-detail .text", ".detail-content",
                ".job_main_message",
            ]) or ""

            city = _safe_text(page, [
                ".city", ".location", ".lname", ".job-location",
                ".job-addr", ".work_addr", ".basic-infor",
                "[class*='location']", "[class*='city']",
                "[class*='addr']",
            ]) or ""

            # 技能标签
            skill_texts = _safe_text_all(page,
                "[class*='tag'], .job-tags span, .labels span, .skill-tags span")

            browser.close()

            # ── 阶段4: 组装结果 ──
            # 如果 CSS 提取的 JD 为空，用全页文本的前 3000 字符
            effective_jd = (jd_text or full_page_text or "")[:3000]
            # 如果标题还是空的，从 full_page_text 中尝试提取
            if not title and full_page_text:
                lines = full_page_text.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if 3 <= len(line) <= 80:
                        title = line[:100]
                        break

            result = {
                "title": (title or "未识别岗位").strip()[:100],
                "company": (company or "未识别公司").strip(),
                "salary_range": (salary or "").strip(),
                "jd_text": effective_jd.strip(),
                "city": (city or "").strip(),
                "jd_skills": [s.strip() for s in skill_texts if s.strip()][:15],
                "source_url": url,
                "source_platform": platform,
                "industry": "互联网",
                "full_page_text": (full_page_text or "")[:8000],
            }

            # 如果公司仍未识别，尝试从 URL 或页面标题推断
            if result["company"] == "未识别公司":
                # 从 URL 域名推断
                for well_known in {
                    "bytedance.com": "字节跳动", "tencent.com": "腾讯",
                    "alibaba.com": "阿里巴巴", "baidu.com": "百度",
                    "jd.com": "京东", "meituan.com": "美团",
                    "xiaohongshu.com": "小红书", "kuaishou.com": "快手",
                    "bilibili.com": "B站", "pinduoduo.com": "拼多多",
                    "netease.com": "网易", "huawei.com": "华为",
                    "xiaomi.com": "小米", "didi.com": "滴滴",
                    "antgroup.com": "蚂蚁集团",
                }.items():
                    if domain in url.lower():
                        result["company"] = well_known
                        break

            return result

    except ImportError:
        # Playwright 未安装，降级到 requests
        import requests
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            return extract_from_html(resp.text, url)
        except Exception as e:
            raise RuntimeError(f"HTTP请求失败: {type(e).__name__}: {e}")

    except Exception as e:
        # 最后兜底：返回带有错误标记的结果，不抛异常
        return {
            "title": "页面加载超时",
            "company": "未识别公司",
            "salary_range": "",
            "jd_text": "",
            "city": "",
            "jd_skills": [],
            "source_url": url,
            "source_platform": platform,
            "industry": "互联网",
            "full_page_text": "",
            "_error": f"{type(e).__name__}: {str(e)[:200]}",
        }


def scrape_list(url: str, max_jobs: int = 30) -> list[dict]:
    """提取列表页多个岗位（sync Playwright）—— 多层容错架构"""
    from playwright.sync_api import sync_playwright

    url_lower = url.lower()
    is_spa = any(kw in url_lower for kw in [
        "campus.", "school.", "career.", "#/", "#!/",
        "zhaopin.com", "liepin.com", "51job.com",
    ])

    jobs = []

    try:
        with sync_playwright() as p:
            browser = _launch_browser(p)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
            )
            page = context.new_page()

            # 多级加载策略
            loaded = False
            for strategy in (
                ("domcontentloaded", 30000) if is_spa else ("networkidle", 30000),
                ("domcontentloaded", 20000),
                ("load", 15000),
            ):
                wait_until, timeout = strategy
                try:
                    page.goto(url, wait_until=wait_until, timeout=timeout)
                    page.wait_for_timeout(3000)
                    loaded = True
                    break
                except Exception:
                    continue

            if not loaded:
                # 即使超时也尝试提取
                try:
                    page.wait_for_timeout(5000)
                except Exception:
                    pass

            try:
                if "campus.jd.com" in url_lower:
                    jobs = _extract_campus_jd(page)
                else:
                    jobs = _extract_generic_list(page, url_lower)
            except Exception as ext_err:
                # 提取失败不抛异常，尝试从全页文本解析
                try:
                    full_text = page.evaluate("() => document.body.innerText") or ""
                    jobs = _extract_from_flat_text(full_text, url)
                except Exception:
                    pass

            browser.close()

    except ImportError:
        # Playwright 不可用时用 HTTP 降级
        import requests
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            clean = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
            clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '\n', clean)
            text = re.sub(r'\n{3,}', '\n\n', text).strip()
            jobs = _extract_from_flat_text(text, url)
        except Exception:
            pass

    except Exception:
        pass

    # 去重
    seen = set()
    unique = []
    for job in jobs:
        key = (job.get("title", ""), job.get("company", ""))
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique[:max_jobs] if unique else []


def _extract_from_flat_text(text: str, url: str) -> list[dict]:
    """从纯文本中尝试解析岗位列表（兜底方案）"""
    jobs = []
    platform = identify_platform(url) if url else "custom"
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    skip_kw = [
        "首页", "登录", "注册", "关于", "联系", "隐私", "协议",
        "版权", "备案", "返回", "上一页", "下一页", "加载更多",
        "搜索", "筛选", "全部", "城市", "职位类型", "不限",
    ]

    for i, line in enumerate(lines):
        if any(k in line for k in skip_kw):
            continue
        # 常见标题格式：2-30字符，可能包含职位关键词
        if 2 <= len(line) <= 60:
            title = line[:50]
            city = ""
            # 检查下一行是否可能是城市
            if i + 1 < len(lines) and len(lines[i + 1]) <= 10:
                city_match = re.search(
                    r'(北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|长沙|苏州|厦门|天津|重庆|合肥)',
                    lines[i + 1])
                if city_match:
                    city = city_match.group(1)
            jobs.append({
                "title": title, "company": "", "city": city,
                "salary_range": "", "jd_text": "", "jd_skills": [],
                "source_url": url, "source_platform": platform,
                "industry": "互联网",
            })

    return jobs[:50]


def _extract_campus_jd(page) -> list[dict]:
    """campus.jd.com 列表页提取"""
    jobs = []
    
    try:
        page.wait_for_selector(
            ".job-item, .position-item, .recruit-list li, .job-card, "
            ".list-item, li, div[class]",
            timeout=10000)
    except Exception:
        pass

    selectors = [
        ".job-item", ".position-item", ".recruit-list li", ".job-card",
        "[class*='job-item']", "[class*='position-item']",
        "[class*='job'][class*='item']",
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

    skip_kw = [
        "首页", "登录", "注册", "关于", "联系", "隐私", "协议",
        "版权", "备案", "返回", "上一页", "下一页", "加载更多",
        "搜索", "筛选", "全部", "城市", "职位类型",
    ]

    for item in items:
        try:
            title_el = item.query_selector(
                "h3, h4, .job-name, .position-name, .title, .name, "
                "[class*='title'], [class*='name'], a, span")
            title = (title_el.text_content() if title_el else "").strip()

            if any(kw in title for kw in skip_kw):
                continue

            city_el = item.query_selector(
                ".city, .location, .work-place, .addr, [class*='city']")
            city = (city_el.text_content() if city_el else "").strip()

            link_el = item.query_selector("a[href]")
            href = ""
            if link_el:
                h = link_el.get_attribute("href")
                if h:
                    href = h
                    if not href.startswith("http"):
                        href = "https://campus.jd.com" + href

            if title and len(title) > 1:
                jobs.append({
                    "title": title, "company": "京东",
                    "city": city, "salary_range": "",
                    "jd_text": "", "jd_skills": [],
                    "source_url": href,
                    "source_platform": "school_career",
                    "industry": "互联网",
                })
        except Exception:
            continue

    return jobs


def _extract_generic_list(page, url_lower: str) -> list[dict]:
    """通用列表页提取"""
    jobs = []
    seen_titles = set()

    containers = page.query_selector_all(
        "li, .card, .item, [class*='card'], [class*='item']")

    skip_kw = ["首页", "登录", "注册", "关于", "联系我们", "隐私"]

    for container in containers:
        try:
            inner_links = container.query_selector_all(
                "a, h3, h4, .title, .name, [class*='title']")
            for inner in inner_links:
                text = (inner.text_content() or "").strip()
                if 3 <= len(text) <= 50 and text not in seen_titles \
                        and not any(kw in text for kw in skip_kw):
                    seen_titles.add(text)
                    href = inner.get_attribute("href") or ""
                    if not href:
                        pl = container.query_selector("a[href]")
                        href = (pl.get_attribute("href") or "") if pl else ""

                    ce = container.query_selector(
                        "[class*='city'], [class*='addr'], [class*='location']")
                    city = (ce.text_content() if ce else "").strip()

                    jobs.append({
                        "title": text, "company": "", "city": city,
                        "salary_range": "", "jd_text": "", "jd_skills": [],
                        "source_url": href, "source_platform": identify_platform(url_lower),
                        "industry": "互联网"})
        except Exception:
            continue

    # 链接兜底
    if len(jobs) < 3:
        all_links = page.query_selector_all("a")
        for link in all_links:
            text = (link.text_content() or "").strip()
            if 3 <= len(text) <= 50 and text not in seen_titles \
                    and not any(kw in text for kw in skip_kw) and len(jobs) < 50:
                seen_titles.add(text)
                href = link.get_attribute("href") or ""
                jobs.append({"title": text, "company": "", "city": "",
                            "salary_range": "", "jd_text": "", "jd_skills": [],
                            "source_url": href,
                            "source_platform": identify_platform(url_lower),
                            "industry": "互联网"})

    return jobs


# ── 主入口 ──────────────────────────────────────────────
if __name__ == "__main__":
    # 强制 stdout 使用 UTF-8，避免 Windows GBK 编码问题
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "detail"
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        max_jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 30

        if not url:
            print(json.dumps({"error": "缺少 URL 参数"}, ensure_ascii=False))
            sys.exit(1)

        if mode == "list":
            result = scrape_list(url, max_jobs)
        else:
            result = scrape_detail(url)

        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        error_output = {"error": f"{type(e).__name__}: {str(e)}"}
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
