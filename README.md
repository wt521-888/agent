# 简历智能打分 Agent v2.4

基于 **FastAPI + React + SQLite** 的端到端简历打分应用。集成 OpenAI LLM 与 Tavily 联网搜索，自动对候选人与岗位的匹配度进行多维度评分并给出可操作的学习建议。

## ✨ 功能特性

- 📄 **简历管理**：上传 PDF / DOCX / TXT 等多种格式，自动解析
- 🌐 **联网搜索**：调用 Tavily 自动获取公司与岗位背景
- 🤖 **多维打分**：技能 / 经验 / 教育 / 项目 四维评分 + 总分
- 💡 **改进建议**：优势、不足、简历改写、学习资源
- ✨ **一键优化**：根据改进建议，LLM 自动重写简历
- 🎤 **模拟面试**：AI 生成面试问题，实时评估回答并打分
- ⚙️ **在线配置**：支持在线修改 API Key、切换大模型厂商
- 📚 **历史记录**：所有打分记录可回溯查看
- 💰 **智能缓存**：相同简历+JD组合自动缓存，节省 token
- 📊 **Token统计**：实时显示每次打分的 token 消耗和预估成本

## 🧱 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.13 / FastAPI / SQLAlchemy / SQLite |
| 简历解析 | PyPDF2 / python-docx |
| 外部服务 | OpenAI API / Tavily Search API |
| 前端 | React 18 / Vite 5 / TailwindCSS 3 |

## 📁 项目结构

`
D:\python\agent\简历打分agent\
├── .venv/                # Python 虚拟环境
├── backend/              # 后端代码
│   ├── main.py           # FastAPI 入口
│   ├── models.py         # 数据库模型
│   ├── schemas.py        # Pydantic 模型
│   ├── routers/          # API 路由
│   └── services/         # 业务逻辑
├── frontend/             # 前端代码
├── uploads/              # 简历文件存储
├── .env                  # 环境变量配置
├── .env.example          # 环境变量模板
├── resume_agent.db       # SQLite 数据库
├── start.py              # 启动脚本
└── README.md
`

## 🚀 快速开始

### 1. 配置环境变量

复制 .env.example 为 .env，填入 API Key。

### 2. 启动服务

`powershell
# 进入项目目录
cd D:\python\agent\简历打分agent

# 启动后端
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 新终端，启动前端
cd frontend
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
| POST | /api/resumes/modify | 一键优化简历 |

### 打分功能
| Method | Path | 说明 |
|---|---|---|
| POST | /api/score | 打分（返回 Token 统计） |
| GET | /api/score/history | 历史记录 |
| DELETE | /api/score/history/{id} | 删除记录 |
| GET | /api/score/cache/stats | 查看缓存统计 |

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

## 💰 成本优化策略

### 1. 智能缓存
- 相同简历+JD组合自动缓存，缓存命中时零 token 消耗

### 2. 正则优先提取
- 公司名/岗位名先用正则提取，成功则零 token

### 3. 内容瘦身
- 简历和 JD 自动提取关键字段，减少 50-70% 输入 token

### 4. 智能重试限制
- LLM 输出异常时最多重试 2 次，避免无效消耗

## 📊 Token 消耗统计

打分完成后会显示：
- 输入/输出/总计 Token 数
- 预估成本（美元）
- 是否命中缓存
- 是否正则提取成功

## ⚙️ 支持的大模型

| 厂商 | Base URL | 推荐模型 |
|------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| 小米 MiMo | https://api.xiaomimimo.com/v1 | mimo-v2.5-pro |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |

## 🔧 GitHub 加速

`powershell
.\setup-github.ps1 -Method mirror
`

## 常见问题

**Q: 如何切换大模型？**
A: 点击右上角「⚙️ 配置」按钮。

**Q: 缓存什么时候命中？**
A: 同一份简历 + 完全相同的 JD = 命中。

**Q: 如何查看 Token 节省？**
A: 打分结果页面会显示统计。

## License

MIT
