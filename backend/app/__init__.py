"""JobMatch AI Backend - 启动时配置"""
import sys
import os
import asyncio
from pathlib import Path

# ── 加载 .env 文件（必须在 import config 之前）──
# 从 backend/ 目录向上查找 .env 文件
_env_search_dir = Path(__file__).resolve().parent.parent  # backend/
_env_file = _env_search_dir / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
        print(f"[Init] Loaded .env from {_env_file}")
    except ImportError:
        print("[Warn] python-dotenv not installed, .env not loaded (run: pip install python-dotenv)")
else:
    # 开发环境可能把 .env 放在其他位置，尝试当前工作目录
    _cwd_env = Path.cwd() / ".env"
    if _cwd_env.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_cwd_env)
            print(f"[Init] Loaded .env from {_cwd_env}")
        except ImportError:
            pass

# ── Windows + Python 3.14+: 修复 Playwright 子进程兼容性 ──
# ProactorEventLoop 不支持 subprocess transport，而 Playwright 需要它启动浏览器
# 必须在使用任何 event loop 之前设置。
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
