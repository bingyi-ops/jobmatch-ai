"""JobMatch AI 启动入口
在 uvicorn 创建 event loop 之前设置好 Windows 兼容配置。
"""
import sys
import asyncio

# ── Windows + Python 3.14+: 修复 Playwright 子进程兼容性 ──
# 必须在创建任何 event loop 之前调用！
if sys.platform == "win32":
    # Python 3.14 默认 ProactorEventLoop 不支持子进程传输
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("[OK] Windows SelectorEventLoop enabled")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
