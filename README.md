# 简历智能打分 Agent v2.0

基于 **FastAPI + React + SQLite** 的端到端简历打分应用。集成 OpenAI LLM 与 Tavily 联网搜索，自动对候选人与岗位的匹配度进行多维度评分并给出可操作的学习建议。

## ✨ 功能特性

- 📄 **简历管理**：上传 PDF / DOCX / TXT 等多种格式，自动解析
- 🌐 **联网搜索**：调用 Tavily 自动获取公司与岗位背景
- 🤖 **多维打分**：技能 / 经验 / 教育 / 项目 四维评分 + 总分
- 💡 **改进建议**：优势、不足、简历改写、学习资源
- 🎤 **模拟面试**：AI 生成面试问题，实时评估回答并打分
- ⚙️ **在线配置**：支持在线修改 API Key、切换大模型厂商
- 📚 **历史记录**：所有打分记录可回溯查看

## 🧱 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.14 / FastAPI / SQLAlchemy / SQLite |
| 简历解析 | LiteParse > markitdown > PyPDF2 > pdfplumber > 视觉 LLM |
| 外部服务 | OpenAI API / Tavily Search API |
| 前端 | React 18 / Vite 5 / TailwindCSS 3 |

## 🚀 快速开始

### 1. 配置环境变量

复制 .env.example 为 .env，填入 API Key。

### 2. 启动服务

`powershell
# 终端 1：启动后端
cd resume-agent/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 终端 2：启动前端
cd resume-agent/frontend
npm install  # 首次运行
npm run dev
`

### 3. 访问应用

打开浏览器访问 http://localhost:5173

## 📡 API 接口

### 简历管理
| Method | Path | 说明 |
|---|---|---|
| POST | /api/resumes/upload | 上传简历 |
| GET | /api/resumes | 简历列表 |
| DELETE | /api/resumes/{id} | 删除简历 |

### 打分功能
| Method | Path | 说明 |
|---|---|---|
| POST | /api/score | 打分 |
| GET | /api/score/history | 历史记录 |
| DELETE | /api/score/history/{id} | 删除记录 |

### 模拟面试
| Method | Path | 说明 |
|---|---|---|
| POST | /api/interview/questions | 生成面试问题 |
| POST | /api/interview/evaluate | 评估回答 |

### 配置管理
| Method | Path | 说明 |
|---|---|---|
| GET | /api/config | 获取配置 |
| PUT | /api/config | 更新配置 |
| POST | /api/config/test-openai | 测试连接 |

## 🎤 模拟面试功能

1. 上传简历并完成打分
2. 点击「🎤 模拟面试」按钮（或从历史记录进入）
3. 输入目标岗位描述
4. AI 根据简历和岗位生成面试问题
5. 逐题回答，AI 实时评估打分
6. 查看综合评分、优缺点和参考答案

### 评估维度
- **准确性**：答案是否正确
- **完整性**：是否覆盖关键点
- **深度**：理解是否深入
- **表达**：逻辑是否清晰

## ⚙️ 在线配置

支持在线修改以下配置：
- OpenAI API Key
- API Base URL（支持任意 OpenAI 兼容接口）
- 主模型名称
- 视觉模型名称
- Tavily API Key

### 支持的大模型厂商
| 厂商 | Base URL | 推荐模型 |
|------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| 小米 MiMo | https://api.xiaomimimo.com/v1 | mimo-v2.5-pro |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |

## 🔍 简历解析策略

采用**五级兜底**解析策略：

| 优先级 | 解析器 | 适用场景 |
|--------|--------|----------|
| 1 | LiteParse | 文本型 PDF、Office 文档 |
| 2 | markitdown | Office 文档、HTML |
| 3 | PyPDF2 | 简单 PDF |
| 4 | pdfplumber | 复杂布局 PDF |
| 5 | 视觉 LLM OCR | 扫描件、图片型 PDF |

## 📁 项目结构

`
resume-agent/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── database.py             # 数据库连接
│   ├── models.py               # ORM 模型
│   ├── routers/
│   │   ├── resumes.py          # 简历管理
│   │   ├── scoring.py          # 打分功能
│   │   ├── interview.py        # 模拟面试
│   │   └── config.py           # 配置管理
│   └── services/
│       ├── llm_service.py      # LLM 调用
│       ├── resume_parser.py    # 文档解析
│       ├── search_service.py   # 联网搜索
│       └── interview_service.py # 面试服务
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ResumeManager.jsx
│           ├── JobInput.jsx
│           ├── ScoreResult.jsx
│           ├── HistoryModal.jsx
│           ├── InterviewModal.jsx
│           └── ConfigModal.jsx
├── .env.example
└── README.md
`

## 常见问题

**Q: 打分超时？**
A: LLM 服务响应较慢，已将超时时间设为 3 分钟。

**Q: 如何切换大模型？**
A: 点击右上角「⚙️ 配置」按钮，在线修改 API Key 和模型。

**Q: PDF 解析为空？**
A: 可能是扫描件，系统会自动使用视觉 LLM 进行 OCR。

## License

MIT
