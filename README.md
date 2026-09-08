# 简历智能打分 Agent

基于 **FastAPI + React + SQLite** 的端到端简历打分应用。集成 OpenAI LLM 与 Tavily 联网搜索，自动对候选人与岗位的匹配度进行多维度评分并给出可操作的学习建议。

## ✨ 功能特性

- 📄 **简历管理**：上传 PDF / DOCX / TXT，自动解析文本并存库
- 🌐 **联网搜索**：调用 Tavily 自动获取公司与岗位背景
- 🤖 **多维打分**：技能 / 经验 / 教育 / 项目 四维评分 + 总分
- 💡 **改进建议**：优势、不足、简历改写、知识盲点、5+ 条学习资源
- 📚 **历史记录**：所有打分记录可回溯查看
- 🎨 **现代 UI**：React + TailwindCSS，左右分栏

## 🧱 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11 / FastAPI / SQLAlchemy 2 / SQLite |
| 简历解析 | PyPDF2 / python-docx / 纯文本 |
| 外部服务 | OpenAI API / Tavily Search API |
| 前端 | React 18 / Vite 5 / TailwindCSS 3 / Axios |

## 📁 目录结构

```
resume-agent/
├── .env.example          # 环境变量模板
├── README.md
├── backend/
│   ├── main.py           # FastAPI 入口
│   ├── database.py       # SQLite 连接
│   ├── models.py         # ORM 模型
│   ├── schemas.py        # Pydantic 模型
│   ├── requirements.txt
│   ├── routers/
│   │   ├── resumes.py    # 简历上传/列表/删除
│   │   └── scoring.py    # 打分 + 历史
│   └── services/
│       ├── resume_parser.py   # PDF/DOCX/TXT 解析
│       ├── search_service.py  # Tavily 搜索
│       └── llm_service.py     # OpenAI 提示词与调用
├── frontend/
│   ├── package.json
│   ├── vite.config.js    # /api 代理到 8000
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── ResumeManager.jsx
│           ├── JobInput.jsx
│           ├── ScoreResult.jsx
│           └── HistoryModal.jsx
└── uploads/              # 简历文件存储（自动创建）
```

## 🚀 快速开始

### 方式 1：一键启动（推荐）

双击项目根目录下的 [start-all.bat](file:///d:/python/agent/test-agent/resume-agent/start-all.bat)，会自动开两个窗口分别跑后端和前端。

启动后浏览器打开 <http://localhost:5173> 即可。

完成后想停服务，双击 [stop-all.bat](file:///d:/python/agent/test-agent/resume-agent/stop-all.bat)。

### 方式 2：手动启动

**2.1 准备环境**
- Python 3.10+
- Node.js 18+
- 注册并准备：
  - **OpenAI API Key**（[platform.openai.com](https://platform.openai.com/api-keys)）或任何 OpenAI 兼容服务（DeepSeek / 小米 MiMo / 通义千问等）
  - **Tavily API Key**（[tavily.com](https://tavily.com)，免费 1000 次/月）

**2.2 配置环境变量**

在项目根目录（`resume-agent/`）复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env`，填入真实 key：

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=tvly-...
```

> 💡 **小米 MiMo**：`BASE_URL=https://api.xiaomimimo.com/v1`，模型用 `mimo-v2.5-pro`（用 `GET /v1/models` 探真实可用列表）
> 💡 **DeepSeek**：`BASE_URL=https://api.deepseek.com/v1`，`OPENAI_MODEL=deepseek-chat`

**2.3 启动后端**

> Windows 上 `pip` / `python` 命令常因 App Execution Aliases 失效，建议直接用 `py` 启动器或调用绝对路径。

```powershell
cd resume-agent\backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8000
```

或直接双击 [start-backend.bat](file:///d:/python/agent/test-agent/resume-agent/start-backend.bat)。

后端运行在 <http://localhost:8000>，可访问 <http://localhost:8000/docs> 看 Swagger 文档。

**2.4 启动前端（新开一个终端）**

```powershell
cd resume-agent\frontend
npm install
npm run dev
```

或直接双击 [start-frontend.bat](file:///d:/python/agent/test-agent/resume-agent/start-frontend.bat)。

前端运行在 <http://localhost:5173>。

> 🔗 前端通过 Vite 代理（`/api → http://localhost:8000`）调用后端，无需关心跨域。

## 📡 API 速览

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/resumes/upload` | 上传简历（multipart，字段 `file`） |
| GET  | `/api/resumes` | 简历列表 |
| DELETE | `/api/resumes/{id}` | 删除简历 |
| POST | `/api/score` | 打分（JSON：`{resume_id, job_description}`） |
| GET  | `/api/score/history` | 历史打分记录 |
| GET  | `/uploads/{filename}` | 访问已上传文件 |

## 🧪 完整调用流程

1. 前端调 `POST /api/resumes/upload` 上传 PDF → 后端解析存库 → 返回 `resume_id`
2. 用户在前端粘贴招聘信息 + 选中简历 → 调 `POST /api/score`
3. 后端流程：
   - 读取简历文本
   - 调用 Tavily 搜索（**失败不阻塞**）
   - 组装 Prompt：`招聘信息 + 搜索摘要 + 简历文本`
   - 调 OpenAI（`response_format=json_object`）→ 解析 JSON
   - 写库 `score_records`
4. 前端把结果渲染为：总分 + 四维进度条 + 优势/不足 + 学习资源卡片

## ⚠️ 常见问题

**Q: 提示 `OPENAI_API_KEY 未配置`**
A: 检查项目根目录的 `.env` 是否存在并填了真 key；修改后重启后端。

**Q: 提示 `Tavily 搜索失败`**
A: 不会影响主流程，控制台会有 warning，LLM 仅基于 JD + 简历打分。

**Q: PDF 解析出来是空的**
A: 可能是扫描件（图片型 PDF），需要先用 OCR。代码会保留文件但 `content=""`，前端可看到提示。

**Q: 端口 8000 / 5173 被占用**
A: 后端改 `uvicorn main:app --port 8001`，同时改 `frontend/vite.config.js` 的 proxy 目标端口。

**Q: 想换 LLM**
A: 修改 `.env` 的 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 即可。DeepSeek、智谱、通义、Moonshot 都兼容 OpenAI 接口。

## 🔒 安全提示

- `.env` 不要提交到 git
- 当前 `CORS` 全部放行（开发期方便），生产请收敛 `allow_origins`
- 上传文件保存在 `uploads/`，生产建议放到对象存储并加病毒扫描

## 📜 License

MIT

##示例样图
<img width="1063" height="656" alt="屏幕截图 2026-09-08 095743" src="https://github.com/user-attachments/assets/4d74b5ea-ff7f-4290-9bb4-dbcc452b4eb1" />
<img width="1220" height="662" alt="屏幕截图 2026-09-08 100409" src="https://github.com/user-attachments/assets/a1e18346-e1b1-415b-ad23-b339e0a3cb33" />
<img width="666" height="395" alt="image" src="https://github.com/user-attachments/assets/bbb75d60-2931-43ff-9f47-fcaa4ff5923b" />
<img width="671" height="518" alt="image" src="https://github.com/user-attachments/assets/c6b42292-321a-4dec-a4d7-e07fc82919bb" />
<img width="573" height="535" alt="屏幕截图 2026-09-08 102550" src="https://github.com/user-attachments/assets/eafaa444-d301-4d2c-b0de-3a397e0a737e" />
<img width="491" height="511" alt="image" src="https://github.com/user-attachments/assets/c77df578-f001-4ca6-8d2c-2c0d3cb9ec05" />
<img width="659" height="566" alt="屏幕截图 2026-09-08 112533" src="https://github.com/user-attachments/assets/24b32744-0a3a-4d70-b2e4-3f291fcbc61e" />


