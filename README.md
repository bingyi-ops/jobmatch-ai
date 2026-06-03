# JobMatch AI — 个性化岗位推荐系统

> 单用户 · 零成本 · 全链路求职助手

JobMatch AI 是一个面向学生/求职者的智能岗位管理系统，核心设计哲学是**「我喜欢 ∩ 我擅长 ∩ 公司需要」三圈交集模型**，配合**匹配反馈学习闭环**，实现"越用越准"的个性化推荐。


## 核心功能

| 模块 | 功能 |
|------|------|
| **全部岗位** | 多来源岗位信息流，按来源渠道 + 招聘类型两级筛选，关键词搜索，时间轴分组展示，**自动去重**（同一公司同一 JD 只展示最新一条） |
| **精选推荐** | 三圈交集匹配引擎，多层过滤漏斗（硬过滤 → 能力匹配 → 兴趣偏好 → 精排），仅展示交集分 ≥ 60 的高匹配岗位 |
| **简历管理** | 上传 PDF/Word 简历 → LLM 提取三圈画像 → 触发全量岗位匹配 |
| **岗位详情** | 差距分析面板（技能对比 + 四维能力蛛网图）、面试准备建议、公司背景快照、相似岗位推荐 |
| **我的投递** | 投递状态看板（已投递/面试中/Offer/已拒绝）、备注管理、投递统计面板 |
| **面试辅助** | 面试问题准备方向、模拟面试（LLM 实时评估）、面试复盘 + 改进路线图 |


## 快速启动

### 前置条件

- Python 3.11+
- Node.js 18+（前端）
- 无需数据库服务（SQLite 文件级）

### 第一步：启动后端（FastAPI）

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后访问：`http://localhost:8000/api/health`
→ 应返回 `{"status": "ok", "db": true}`

> **首次启动会自动 seed 40 条 mock 岗位并运行匹配**，约需 5-10 秒。

### 第二步：启动前端

```bash
cd frontend
npm install
npm run dev
```

启动成功后访问：`http://localhost:5173`

### 一键启动（Windows）

双击 `start_backend.bat` 启动后端，双击 `start_frontend.bat` 启动前端。


## 使用流程

```
1. 访问首页 → 浏览「全部岗位」（无需登录）
   ↓ 按来源/类型筛选，或搜索关键词
2. 点击「上传简历」→ 上传 PDF/Word 简历
   ↓ LLM 自动提取三圈画像（我喜欢/我擅长/不可接受项）
3. 进入「精选推荐」→ 查看个性化高匹配岗位
   ↓ 每个岗位附有三圈雷达图 + 匹配理由 + 投递倒计时
4. 点击岗位卡片 → 查看详情（差距分析 + 面试准备 + 公司快照）
   ↓ 点击「投递简历」记录投递行为
5. 进入「我的投递」→ 跟踪全流程状态
   ↓ 面试后填写复盘，获得改进建议
6. 对推荐岗位点「保存」（正向反馈）或「忽略」（选择原因）
   ↓ 系统动态调整后续推荐权重，"越用越准"
```


## 项目结构

```
jobmatch-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 主应用（全部 API 路由）
│   │   ├── config.py        # 配置（LLM_API_KEY 等）
│   │   └── database.py     # SQLite 连接 + 初始化
│   ├── requirements.txt
│   ├── jobmatch.db       # SQLite 数据库（自动生成）
│   └── uploads/
├── frontend/
│   └── src/
│       ├── api/client.ts   # API 请求封装
│       ├── components/      # UI 组件（JobCard / FeaturedJobCard / DeadlineBadge 等）
│       ├── pages/           # 页面（AllJobsPage / FeaturedPage / ApplicationsPage 等）
│       └── types/index.ts  # TypeScript 类型定义
├── data/
│   └── schema.sql        # 数据库建表 SQL
├── start_backend.bat
└── start_frontend.bat
```


## 配置说明（可选）

在 `backend/` 目录下创建 `.env` 文件：

```env
# 是否使用真实 LLM（默认 false = 全部 mock）
USE_REAL_LLM=true

# OpenAI 兼容 API 配置
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

> 设为 `USE_REAL_LLM=false`（默认）时，所有 AI 功能使用 mock 数据，**零成本运行**。


## API 端点概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/jobs/all` | 全部岗位（支持 platform / type / search 筛选，自动去重） |
| GET | `/api/jobs/{id}` | 岗位详情 |
| GET | `/api/jobs/{id}/similar` | 相似岗位推荐 |
| GET | `/api/featured` | 精选推荐（多层过滤漏斗） |
| POST | `/api/resume/upload` | 上传简历（触发匹配） |
| GET | `/api/resume/profile` | 获取当前简历画像 |
| POST | `/api/applications` | 创建投递记录 |
| PUT | `/api/applications/{id}` | 更新投递状态 |
| GET | `/api/applications/stats` | 投递统计面板 |
| POST | `/api/feedback` | 提交推荐反馈（保存/忽略 + 偏好学习） |


## 设计亮点

1. **零外部依赖后端选项**：纯标准库 / FastAPI 双模式可选
2. **去重逻辑**：同一公司同一 JD 自动合并，避免重复展示
3. **多层过滤漏斗**：硬过滤（地点/薪资/类型）→ 能力匹配（Jaccard 相似度）→ 兴趣偏好（LLM 语义）→ 精排（几何平均交集分）
4. **反馈学习闭环**：用户「忽略」原因 → 动态调整权重 → 后续推荐自动优化
5. **时间轴分组**：全部岗位按发布日期自动分组（今天/昨天/近X天），信息层次清晰


## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite 5 + TypeScript + Tailwind CSS 3 + shadcn/ui + Recharts |
| 后端 | FastAPI（Python 3.11+）+ SQLite（零配置） |
| AI 层 | OpenAI 兼容 API（可选，默认 mock） |
| 向量 | numpy + scikit-learn（余弦相似度） |


## 许可证

MIT License
