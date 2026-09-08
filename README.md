# 🎯 简历智能打分 Agent

基于 **FastAPI + React + SQLite** 的端到端简历打分应用，集成 OpenAI LLM 与 Tavily 联网搜索，提供多维度评分、改进建议和模拟面试功能。

## ✨ 功能特性

- 📄 **简历管理**：支持 PDF/DOCX/PPTX/XLSX/HTML/图片等多格式上传，智能文本解析
- 🤖 **智能打分**：四维度评分（技能/经验/教育/项目）+ 总分 + 改进建议 + 学习资源 + Token统计
- 🌐 **联网搜索**：集成 Tavily Search API，自动搜索公司和岗位信息
- 🎤 **模拟面试**：基于简历自动生成面试问题，AI 评估回答并给出参考答案
- 📊 **历史记录**：保存所有打分记录，支持查看/删除/跳转面试
- ⚙️ **在线配置**：在线修改 API Key 和模型配置，支持多家 LLM 服务商

## 🛠️ 技术栈

**后端**：FastAPI / SQLAlchemy / SQLite / OpenAI SDK / Tavily Search / liteparse / markitdown / PyMuPDF

**前端**：React 18 / Vite / TailwindCSS / Axios

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/wt521-888/agent.git
cd agent

# 配置环境变量
cp .env.example .env

# 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问前端：http://localhost:5173 | 后端API：http://localhost:8000

## 📁 项目结构

```
agent/
├── backend/                      # 后端服务
│   ├── main.py                   # FastAPI 入口
│   ├── database.py               # 数据库配置
│   ├── models.py                 # 数据模型
│   ├── schemas.py                # Pydantic 验证模型
│   ├── routers/                  # API 路由
│   │   ├── resumes.py            # 简历管理
│   │   ├── scoring.py            # 打分功能
│   │   ├── interview.py          # 模拟面试
│   │   ├── modify.py             # 简历修改
│   │   └── config.py             # 配置管理
│   └── services/                 # 业务逻辑
│       ├── llm_service.py        # LLM 调用
│       ├── resume_parser.py      # 简历解析
│       ├── interview_service.py  # 面试服务
│       ├── resume_writer.py      # 简历写入
│       └── search_service.py     # 搜索服务
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── App.jsx               # 主应用
│   │   └── components/           # UI 组件
│   └── index.html
├── .env.example                  # 环境变量模板
├── setup-github.ps1              # GitHub 配置脚本
└── GITHUB_SETUP.md               # GitHub 配置说明
```

## 🔧 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/resumes/upload | POST | 上传简历 |
| /api/resumes | GET | 简历列表 |
| /api/score | POST | 简历打分 |
| /api/score/history | GET | 历史记录 |
| /api/interview/questions | POST | 生成面试问题 |
| /api/interview/evaluate | POST | 评估面试回答 |
| /api/config | GET/PUT | 配置管理 |

## 🔑 环境变量

| 变量名 | 说明 |
|--------|------|
| OPENAI_API_KEY | OpenAI API Key |
| OPENAI_BASE_URL | API 基础 URL |
| OPENAI_MODEL | 主模型 |
| TAVILY_API_KEY | Tavily 搜索 Key |

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

## 📄 License

MIT License