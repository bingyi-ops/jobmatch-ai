CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    jd_text TEXT,
    jd_skills TEXT,
    jd_profile TEXT,
    city TEXT,
    salary_range TEXT,
    recruitment_type TEXT,
    industry TEXT,
    source_platform TEXT,
    source_url TEXT,
    custom_source_name TEXT DEFAULT '',
    custom_source_url TEXT DEFAULT '',
    embedding_json TEXT DEFAULT '[]',
    application_deadline TEXT,
    posted_at TEXT,
    quality_score INTEGER DEFAULT 0,
    quality_flags TEXT DEFAULT '[]',
    user_key TEXT DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS match_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    interest_score REAL DEFAULT 0,
    ability_score REAL DEFAULT 0,
    market_score REAL DEFAULT 0,
    overlap_score REAL DEFAULT 0,
    match_reasons TEXT,
    is_filtered INTEGER DEFAULT 0,
    filter_reason TEXT,
    created_at TEXT,
    user_key TEXT DEFAULT 'default',
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS resume (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interest_profile TEXT,
    ability_profile TEXT,
    deal_breakers TEXT,
    embedding_json TEXT DEFAULT '[]',
    raw_parsed TEXT,
    created_at TEXT,
    user_key TEXT DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_record_id INTEGER,
    action TEXT,
    ignore_reason TEXT,
    created_at TEXT,
    user_key TEXT DEFAULT 'default',
    FOREIGN KEY (match_record_id) REFERENCES match_records(id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    match_record_id INTEGER,
    status TEXT DEFAULT 'applied',
    notes TEXT DEFAULT '{}',
    applied_at TEXT,
    updated_at TEXT,
    user_key TEXT DEFAULT 'default',
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    FOREIGN KEY (match_record_id) REFERENCES match_records(id)
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_id INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    content_json TEXT,
    title TEXT,
    target_job_title TEXT,
    improvement_notes TEXT,
    based_on_feedback INTEGER,
    gap_analysis_result TEXT,
    created_at TEXT,
    user_key TEXT DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS interview_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER DEFAULT 0,
    job_id INTEGER,
    review_text TEXT,
    score_self REAL,
    questions_asked TEXT,
    difficult_questions TEXT,
    ai_analysis TEXT,
    improvement_advices TEXT,
    strengths TEXT,
    weaknesses TEXT,
    created_at TEXT,
    user_key TEXT DEFAULT 'default'
);

-- ── 用户设置表 ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY,
    preferences TEXT DEFAULT '{}',
    updated_at TEXT,
    user_key TEXT DEFAULT 'default'
);

-- ── RSS 通知记录表 ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT,
    job_url TEXT,
    job_company TEXT,
    match_score INTEGER DEFAULT 0,
    channels TEXT DEFAULT '{}',
    created_at TEXT
);

-- ── RSS 拉取日志表 ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS rss_fetch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    jobs_count INTEGER DEFAULT 0,
    success INTEGER DEFAULT 1,
    error_msg TEXT,
    created_at TEXT
);

-- ── 订阅表 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    companies TEXT DEFAULT '[]',
    industries TEXT DEFAULT '[]',
    cities TEXT DEFAULT '[]',
    keywords TEXT DEFAULT '[]',
    channels TEXT DEFAULT '{}',
    updated_at TEXT,
    user_key TEXT DEFAULT 'default'
);

-- ── 用户反馈表（bug / feature request，全局可见）──────────
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_type TEXT NOT NULL CHECK(feedback_type IN ('bug', 'feature')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    contact TEXT DEFAULT '',
    created_at TEXT
);
