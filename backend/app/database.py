import sqlite3
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

def init_db():
    """初始化数据库（执行 schema.sql）"""
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
    db.close()

def dict_row(row):
    if row is None:
        return None
    return dict(row)

def dict_rows(rows):
    return [dict(r) for r in rows]
