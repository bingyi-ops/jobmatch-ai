import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "jobmatch.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "data", "schema.sql")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# LLM 配置（可选，不配置则使用 mock 数据）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# 是否使用真实 LLM（设置为 False 则全部使用 mock 数据，零成本运行）
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"
