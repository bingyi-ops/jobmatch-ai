"""
通用岗位内容过滤器 — 对所有入库路径生效

职责：
  ✅ 识别并拒绝非招聘内容（新闻/文章/早报等）
  ✅ 检测岗位信号（招聘/职责/薪资等关键词）
  ✅ 来源平台可信度评分
  ✅ 内容完整度评分
  ✅ 黑名单域名拦截

使用方式：
  from .quality_filter import JobQualityFilter
  result = JobQualityFilter.validate(title, jd_text, company, source_platform, source_url)
  if result["pass"]:
      quality_score = result["score"]
      quality_flags = result["flags"]
      # 正常入库
  else:
      # 拒绝或标记低质
"""

import json
import re
from typing import Optional


# ── 已知非招聘域名（黑名单）─────────────────────
BLACKLIST_DOMAINS = [
    "sspai.com",           # 少数派 — 科技文章
    "zhihu.com/column",    # 知乎专栏 — 非招聘
    "juejin.cn",           # 掘金 — 技术文章
    "cloud.tencent.com",   # 腾讯云社区 — 技术文章
    "infoq.cn",            # InfoQ — 技术资讯
    "36kr.com",            # 36氪 — 科技新闻
    "geekbang.org",        # 极客时间 — 技术课程
    "jianshu.com",         # 简书 — 内容社区
]

# ── 明确非岗位的黑名单内容模式 ───────────────
NON_JOB_TITLE_PATTERNS = [
    "派早报", "社区速递", "值得一看", "今日最佳",
    "少数派", "早报", "日报", "晚报", "周报", "速递",
    "盘点", "推荐阅读", "开源推荐", "技术博客",
    "每日一" , "本周最热", "年度盘点", "年终总结",
    "如何", "怎么", "什么是", "为什么", "分享",
    "教程", "指南", "推荐", "评测","体验报告",
    "深度解析", "干货", "收藏", "面试题",
]

# ── 岗位信号关键词 ─────────────────────────
JOB_SIGNAL_KEYWORDS = [
    "招聘", "招人", "内推", "校招", "社招", "实习",
    "岗位", "offer", "薪资", "急招", "诚聘", "全职",
    "职位", "任职", "职责", "要求", "学历", "经验",
    "兼职", "远程", "Remote", "Recruit", "Hiring",
    "We are hiring", "Join us", "加入我们",
]

# ── 来源平台基础分 ─────────────────────────
PLATFORM_BASE_SCORES: dict[str, int] = {
    "official": 90,        # 企业官网 — 最可靠
    "boss_zhipin": 85,     # Boss 直聘
    "lagou": 85,           # 拉勾
    "liepin": 85,          # 猎聘
    "51job": 80,           # 前程无忧
    "zhilian": 80,         # 智联
    "school_career": 85,   # 校招官网
    "wechat_public": 70,   # 公众号 — 中等可信
    "xiaohongshu": 60,     # 小红书
    "referral": 65,        # 内推
    "shixiseng": 80,       # 实习僧
    "v2ex": 55,            # V2EX 社区帖
    "douyin": 50,          # 抖音
    "bilibili": 50,        # B站
    "weibo": 45,           # 微博
    "zhihu": 50,           # 知乎
    "custom": 60,          # 用户自定义来源
    "url_import": 65,      # 用户主动 URL 导入
}


class JobQualityFilter:
    """
    岗位质量过滤器 — 单一职责：判断一条内容是否为真实招聘岗位并打分

    score 区间: 0–100
      - ≥ 70  → 高质量，直接入库
      - 40–69 → 中质量，入库但标记
      -  < 40 → 低质量/非岗位，拒绝入库
    """

    # ── 核心验证入口 ──────────────────────────
    @staticmethod
    def validate(
        title: str,
        jd_text: str = "",
        company: str = "",
        source_platform: str = "",
        source_url: str = "",
    ) -> dict:
        """
        返回:
          {
            "pass": bool,          # 是否通过质检
            "score": int,          # 0–100 质量分
            "flags": list[str],    # 标记列表，如 ["low_quality", "sspai_article"]
            "reason": str,         # 拒绝原因（仅 pass=False 时有效）
          }
        """
        title = (title or "").strip()
        jd_text = (jd_text or "").strip()
        company = (company or "").strip()
        source_url = (source_url or "").strip()
        source_platform = (source_platform or "").strip()

        combined = f"{title} {jd_text}".lower().strip()
        flags: list[str] = []

        # ── 第零层：黑名单域名直接拒绝 ───────────
        url_lower = source_url.lower()
        for banned_domain in BLACKLIST_DOMAINS:
            if banned_domain in url_lower:
                return {
                    "pass": False,
                    "score": 0,
                    "flags": ["blacklisted_domain"],
                    "reason": f"来源域名 {banned_domain} 为非招聘网站，已拒绝",
                }

        # ── 第一层：非岗位内容特征检测 ──────────
        non_job_hits: list[str] = []
        for pattern in NON_JOB_TITLE_PATTERNS:
            if pattern in combined:
                non_job_hits.append(pattern)

        # ── 第二层：岗位信号检测 ────────────────
        signal_hits: list[str] = []
        for kw in JOB_SIGNAL_KEYWORDS:
            if kw.lower() in combined:
                signal_hits.append(kw)

        # ── 决策 ────────────────────────────
        # 情况A：明确非岗位内容（匹配非岗位模式 且 无岗位信号）
        if len(non_job_hits) >= 2 and len(signal_hits) == 0:
            return {
                "pass": False,
                "score": 0,
                "flags": ["non_job_content"],
                "reason": f"内容包含非岗位特征: {', '.join(non_job_hits[:3])}",
            }

        # 情况B：只有非岗位特征，完全无岗位信号
        if len(non_job_hits) >= 1 and len(signal_hits) == 0 and len(title) < 20:
            return {
                "pass": False,
                "score": 10,
                "flags": ["likely_article"],
                "reason": f"标题疑似非招聘内容: '{title[:50]}'",
            }

        # ── 第三层：来源平台基础分 ──────────────
        base_score = PLATFORM_BASE_SCORES.get(source_platform, 50)

        # ── 第四层：内容完整度加分 ──────────────
        completeness_bonus = 0
        if title and len(title) >= 4:
            completeness_bonus += 5
        if company and len(company) >= 2:
            completeness_bonus += 5
        if jd_text and len(jd_text) >= 50:
            completeness_bonus += 5
        if jd_text and len(jd_text) >= 200:
            completeness_bonus += 5

        # 岗位信号加分
        signal_bonus = min(len(signal_hits) * 2, 10)

        # 非岗位特征扣分
        non_job_penalty = len(non_job_hits) * 5

        final_score = max(0, min(100, base_score + completeness_bonus + signal_bonus - non_job_penalty))

        # 标记
        if final_score < 40:
            flags.append("low_quality")
        elif final_score < 70:
            flags.append("medium_quality")
        else:
            flags.append("high_quality")

        if non_job_hits:
            flags.insert(0, "has_non_job_keywords")
        if source_platform == "v2ex":
            flags.append("community_source")
        if source_platform == "custom":
            flags.append("user_contributed")
        if source_platform == "url_import":
            flags.append("url_imported")

        return {
            "pass": final_score >= 30,  # 非常低的门槛，因为宁可多收也不要漏掉
            "score": final_score,
            "flags": flags,
            "reason": "",
        }

    # ── 现有岗位重评分 ──────────────────────
    @staticmethod
    def rescore_existing(title: str, jd_text: str, company: str,
                         source_platform: str, source_url: str) -> dict:
        """对已入库的岗位重新打分（用于数据库清理）"""
        return JobQualityFilter.validate(
            title, jd_text, company, source_platform, source_url
        )

    # ── 批量清理建议 ─────────────────────────
    @staticmethod
    def should_cleanup(flags: list[str], source_platform: str, source_url: str) -> bool:
        """判断一条已入库数据是否应被清理"""
        # 黑名单域名 — 一定清理
        url_lower = (source_url or "").lower()
        for banned in BLACKLIST_DOMAINS:
            if banned in url_lower:
                return True
        # 明确标记的非岗位内容
        if "non_job_content" in flags or "likely_article" in flags:
            return True
        if "blacklisted_domain" in flags:
            return True
        return False
