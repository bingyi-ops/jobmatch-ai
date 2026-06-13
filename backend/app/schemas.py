from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    jd_text: str
    jd_skills: list[str] = []
    jd_profile: Optional[dict] = None
    city: str
    salary_range: str
    recruitment_type: str
    industry: str
    source_platform: str
    source_url: str
    application_deadline: str
    posted_at: str


class JobOut(JobBase):
    id: int


class JobSearchParams(BaseModel):
    page: int = 1
    page_size: int = 20
    platform: Optional[str] = None
    type: Optional[str] = None
    search: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    min_score: int = 60


class MatchRecordOut(BaseModel):
    id: int
    job_id: int
    interest_score: float
    ability_score: float
    market_score: float
    overlap_score: float
    match_reasons: str
    created_at: str


class ApplicationBase(BaseModel):
    job_id: int
    match_record_id: Optional[int] = None
    notes: Optional[dict] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[dict] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    match_record_id: Optional[int] = None
    status: str
    notes: Optional[dict] = None
    applied_at: str
    updated_at: str
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    job_source_url: Optional[str] = None


class FeedbackIn(BaseModel):
    match_record_id: int
    action: str  # saved / ignored
    ignore_reason: Optional[str] = None


class FeedbackOut(BaseModel):
    success: bool
    preference_changes: list[dict] = []


class ResumeUploadOut(BaseModel):
    success: bool
    interest_profile: dict = {}
    ability_profile: dict = {}
    deal_breakers: list[str] = []
    message: str = ""


class StatsOut(BaseModel):
    total: int
    by_status: dict
    score_distribution: list[dict]
    weekly_trend: list[dict]


class CompanyInfoOut(BaseModel):
    company: str
    funding_stage: str
    employee_scale: str
    industry_position: str
    recent_news: str
    culture_keywords: list[str]
    disclaimer: str = "基于公开信息推断，仅供参考"


# ── 通知订阅 ──────────────────────────────────────────
class EmailChannelConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    to_email: str = ""


class WebhookChannelConfig(BaseModel):
    enabled: bool = False
    webhook_url: str = ""


class NotificationChannelsConfig(BaseModel):
    email: EmailChannelConfig = EmailChannelConfig()
    dingtalk: WebhookChannelConfig = WebhookChannelConfig()
    wecom: WebhookChannelConfig = WebhookChannelConfig()
    feishu: WebhookChannelConfig = WebhookChannelConfig()


class NotificationSettingsOut(BaseModel):
    channels: NotificationChannelsConfig = NotificationChannelsConfig()
    schedule_hours: int = 2  # 推送间隔（小时）


class SubscriptionOut(BaseModel):
    companies: list[str] = []
    industries: list[str] = []
    cities: list[str] = []
    keywords: list[str] = []


class NotificationLogOut(BaseModel):
    id: int
    job_title: str
    job_url: str
    job_company: str
    match_score: int
    channels: dict
    created_at: str


class RSSFetchLogOut(BaseModel):
    id: int
    source_name: str
    jobs_count: int
    success: int
    error_msg: str = ""
    created_at: str


class NotificationTestIn(BaseModel):
    channel: str  # email / dingtalk / wecom / feishu


class NotificationTestOut(BaseModel):
    success: bool
    channel: str
    message: str
