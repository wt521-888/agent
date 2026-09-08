# 🎯 简历智能打分 Agent

基于 **FastAPI + React + SQLite** 的端到端简历打分应用，集成 OpenAI LLM 与 Tavily 联网搜索，提供多维度评分、改进建议和模拟面试功能。

## ✨ 功能特性

### 📄 简历管理
- 支持 **PDF / DOCX / PPTX / XLSX / HTML / 图片** 等多格式上传
- 智能文本解析：liteparse → markitdown → 原生解析 → OCR 兜底
- 简历列表管理、删除、预览

### 🤖 智能打分
- **四维度评分**：技能匹配 / 工作经验 / 教育背景 / 项目经历
- **总分计算**：综合加权评分（0-100分）
- **改进建议**：简历优化建议、知识领域补充
- **学习资源**：自动推荐相关学习资料（网站/视频/书籍/课程）
- **Token 统计**：实时显示 API 调用的 Token 消耗和成本

### 🌐 联网搜索
- 集成 **Tavily Search API**，自动搜索公司和岗位信息
- 为 LLM 提供更丰富的上下文信息

### 🎤 模拟面试
- 基于简历和岗位描述 **自动生成面试问题**
- 支持 **5-10 道题** 可配置
- 问题分类：技术题 / 项目题 / 行为题
- **AI 评估回答**：评分 + 优缺点分析 + 参考答案
- 支持从历史记录直接进入面试

### 📊 历史记录
- 保存所有打分记录
- 支持查看详细结果、删除记录
- 从历史记录直接跳转面试

### ⚙️ 在线配置
- **在线修改 API Key** 和模型配置
- 支持 OpenAI / 小米 MiMo / 其他兼容服务
- API 连接测试功能
- 无需重启服务即可生效

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **SQLite** - 轻量级数据库
- **OpenAI SDK** - LLM 调用
- **Tavily Search** - 联网搜索
- **liteparse** - 简历解析（LlamaIndex）
- **markitdown** - 微软文档转换
- **PyMuPDF** - PDF 渲染和 OCR

### 前端
- **React 18** - UI 框架
- **Vite** - 构建工具
- **TailwindCSS** - 样式框架
- **Axios** - HTTP 客户端

## 🚀 快速开始

### 1. 克隆项目
`ash
git clone https://github.com/wt521-888/agent.git
cd agent
`

### 2. 配置环境变量
`ash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
`

### 3. 启动后端
`ash
cd backend
pip install -r requirements.txt
python main.py
`

### 4. 启动前端
`ash
cd frontend
npm install
npm run dev
`

### 5. 访问应用
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 📁 项目结构

`
agent/
├── backend/                      # 后端服务
│   ├── main.py                   # FastAPI 入口
│   ├── database.py               # 数据库配置
│   ├── models.py                 # 数据模型
│   ├── schemas.py                # Pydantic 验证模型
│   ├── requirements.txt          # Python 依赖
│   ├── routers/                  # API 路由
│   │   ├── resumes.py            # 简历管理
│   │   ├── scoring.py            # 打分功能
│   │   ├── interview.py          # 模拟面试
│   │   ├── modify.py             # 简历修改
│   │   └── config.py             # 配置管理
│   ├── services/                 # 业务逻辑
│   │   ├── llm_service.py        # LLM 调用
│   │   ├── resume_parser.py      # 简历解析
│   │   ├── interview_service.py  # 面试服务
│   │   ├── resume_writer.py      # 简历写入
│   │   └── search_service.py     # 搜索服务
│   └── uploads/                  # 上传文件
│       ├── backups/              # 备份文件
│       └── modified/             # 修改后文件
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── App.jsx               # 主应用
│   │   └── components/           # UI 组件
│   │       ├── ResumeManager.jsx # 简历管理
│   │       ├── JobInput.jsx      # 岗位输入
│   │       ├── ScoreResult.jsx   # 打分结果
│   │       ├── HistoryModal.jsx  # 历史记录
│   │       ├── InterviewModal.jsx# 模拟面试
│   │       └── ConfigModal.jsx   # 配置管理
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── .env.example                  # 环境变量模板
├── .env                          # 环境变量（不提交）
├── .gitignore
├── setup-github.ps1              # GitHub 配置脚本
├── GITHUB_SETUP.md               # GitHub 配置说明
└── README.md
`

## 🔧 API 接口

### 简历管理
- POST /api/resumes/upload - 上传简历
- GET /api/resumes - 获取简历列表
- GET /api/resumes/{id} - 获取简历详情
- DELETE /api/resumes/{id} - 删除简历

### 打分
- POST /api/score - 简历打分
- GET /api/score/history - 获取历史记录
- DELETE /api/score/history/{id} - 删除历史记录

### 模拟面试
- POST /api/interview/questions - 生成面试问题
- POST /api/interview/evaluate - 评估面试回答

### 配置
- GET /api/config - 获取当前配置
- PUT /api/config - 更新配置
- POST /api/config/test-openai - 测试 API 连接

## 🔑 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| OPENAI_API_KEY | OpenAI API Key | sk-xxx |
| OPENAI_BASE_URL | API 基础 URL | https://api.openai.com/v1 |
| OPENAI_MODEL | 主模型 | gpt-4o-mini |
| VISION_MODEL | 视觉模型（OCR） | gpt-4o-mini |
| TAVILY_API_KEY | Tavily 搜索 Key | tvly-xxx |
| DATABASE_URL | 数据库连接 | sqlite:///./resume_agent.db |
| UPLOAD_DIR | 上传目录 | uploads |

## 📝 使用流程

1. **上传简历**：支持多种格式，自动解析文本
2. **输入岗位描述**：粘贴招聘 JD
3. **开始打分**：AI 多维度评估 + 联网搜索
4. **查看结果**：四维度评分 + 改进建议 + 学习资源
5. **模拟面试**：基于简历和岗位生成面试题
6. **查看历史**：所有打分记录可追溯

## 🤝 支持的模型

- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
- **小米 MiMo**: mimo-v2.5-pro, mimo-v2.5
- **其他兼容服务**: DeepSeek, Claude, 等

## 📄 License

MIT License

## 示例样图

<img width="1063" height="656" alt="屏幕截图 2026-09-08 095743" src="https://github.com/user-attachments/assets/4d74b5ea-ff7f-4290-9bb4-dbcc452b4eb1" />
<img width="1220" height="662" alt="屏幕截图 2026-09-08 100409" src="https://github.com/user-attachments/assets/a1e18346-e1b1-415b-ad23-b339e0a3cb33" />
<img width="666" height="395" alt="image" src="https://github.com/user-attachments/assets/bbb75d60-2931-43ff-9f47-fcaa4ff5923b" />
<img width="671" height="518" alt="image" src="https://github.com/user-attachments/assets/c6b42292-321a-4dec-a4d7-e07fc82919bb" />
<img width="573" height="535" alt="屏幕截图 2026-09-08 102550" src="https://github.com/user-attachments/assets/eafaa444-d301-4d2c-b0de-3a397e0a737e" />
<img width="491" height="511" alt="image" src="https://github.com/user-attachments/assets/c77df578-f001-4ca6-8d2c-2c0d3cb9ec05" />
<img width="659" height="566" alt="屏幕截图 2026-09-08 112533" src="https://github.com/user-attachments/assets/24b32744-0a3a-4d70-b2e4-3f291fcbc61e" />

## 🔗 链接

- [GitHub 仓库](https://github.com/wt521-888/agent)
- [问题反馈](https://github.com/wt521-888/agent/issues)
