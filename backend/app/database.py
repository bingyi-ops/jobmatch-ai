import sqlite3
import json
import os
from pathlib import Path
from .config import DB_PATH, SCHEMA_PATH

def get_db():
    """获取 SQLite 数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

# JSON 字段列表：数据库中存储为 JSON 字符串，需解析为原生对象给前端
_JSON_FIELDS = {"jd_skills", "jd_profile", "quality_flags", "match_reasons",
                "interest_profile", "ability_profile", "deal_breakers",
                "notes", "ai_analysis", "improvement_advices", "strengths",
                "weaknesses", "questions_asked", "difficult_questions",
                "companies", "industries", "cities", "keywords", "channels",
                "content_json", "feedback", "score_breakdown"}

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

def init_db():
    """初始化数据库（执行 schema.sql + 兼容迁移）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = get_db()
    schema_file = Path(SCHEMA_PATH)
    if schema_file.exists():
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    db.execute(stmt)
                except Exception as e:
                    print(f"[DB] Skip: {e}")
        db.commit()
    # ── 兼容迁移：为旧数据库添加新字段 ──
    _migrate_add_column(db, "jobs", "quality_score", "INTEGER DEFAULT 0")
    _migrate_add_column(db, "jobs", "quality_flags", "TEXT DEFAULT '[]'")
    # ── 多用户隔离：为所有业务表添加 user_key ──
    _migrate_add_column(db, "jobs", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "match_records", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "resume", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "feedback", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "applications", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "resume_versions", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "interview_reviews", "user_key", "TEXT DEFAULT 'default'")
    _migrate_add_column(db, "user_settings", "user_key", "TEXT DEFAULT 'default'")
    db.close()

def _migrate_add_column(db, table: str, column: str, col_type: str):
    """安全添加列（列不存在时才加）"""
    try:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"[DB] 迁移：{table}.{column} 已添加")
    except Exception:
        pass  # 列已存在

def dict_row(row):
    if row is None:
        return None
    d = dict(row)
    return _parse_json_fields(d)

def dict_rows(rows):
    return [dict_row(r) for r in rows]
