"""
简历路由 - 旧版已废弃，所有功能已迁移至 main.py。
保留此文件以防止导入错误，但不注册任何路由。
"""

from fastapi import APIRouter

router = APIRouter()

# 此模块不再使用，所有简历相关端点已整合到 main.py 中
# 实际端点：
#   POST /api/resume/upload  -> main.py (真实解析)
#   GET  /api/resume/profile  -> main.py
#   POST /api/resume/advise   -> main.py
#   POST /api/resume/generate -> main.py

