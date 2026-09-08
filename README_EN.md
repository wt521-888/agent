<p align="center">
  <img src="assets/logo.svg" width="300" alt="Resume Score Agent Logo"/>
</p>

<h1 align="center">🎯 Resume Score Agent</h1>

<p align="center">
  An end-to-end resume scoring application built with <strong>FastAPI + React + SQLite</strong>, integrated with OpenAI LLM and Tavily web search
</p>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

---

## ✨ Features

- 📄 **Resume Management**: Upload PDF/DOCX/PPTX/XLSX/HTML/Images with smart text parsing
- 🤖 **AI Scoring**: 4-dimension scoring (Skills/Experience/Education/Projects) + overall score + improvement suggestions + learning resources + Token statistics
- 🌐 **Web Search**: Integrated Tavily Search API for automatic company and position research
- 🎤 **Mock Interview**: Auto-generate interview questions based on resume, AI evaluates answers with reference solutions
- 📊 **History**: Save all scoring records, support view/delete/interview transition
- ⚙️ **Online Config**: Modify API Key and model settings online, supports multiple LLM providers

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI / SQLAlchemy / SQLite / OpenAI SDK / Tavily Search / liteparse / markitdown / PyMuPDF |
| **Frontend** | React 18 / Vite / TailwindCSS / Axios |

## 🚀 Quick Start

```bash
# Clone project
git clone https://github.com/wt521-888/agent.git
cd agent

# Configure environment
cp .env.example .env

# Start backend
cd backend
pip install -r requirements.txt
python main.py

# Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173 | Backend API: http://localhost:8000

## 📁 Project Structure

```
agent/
├── backend/                      # Backend Service
│   ├── main.py                   # FastAPI Entry
│   ├── database.py               # Database Config
│   ├── models.py                 # Data Models
│   ├── schemas.py                # Pydantic Schemas
│   ├── routers/                  # API Routes
│   │   ├── resumes.py            # Resume Management
│   │   ├── scoring.py            # Scoring Logic
│   │   ├── interview.py          # Mock Interview
│   │   └── config.py             # Configuration
│   └── services/                 # Business Logic
│       ├── llm_service.py        # LLM Service
│       ├── resume_parser.py      # Resume Parser
│       ├── interview_service.py  # Interview Service
│       └── search_service.py     # Search Service
├── frontend/                     # Frontend Application
│   └── src/components/           # UI Components
└── README.md
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resumes/upload` | POST | Upload resume |
| `/api/resumes` | GET | List resumes |
| `/api/score` | POST | Score resume |
| `/api/score/history` | GET | Score history |
| `/api/interview/questions` | POST | Generate interview questions |
| `/api/interview/evaluate` | POST | Evaluate interview answer |
| `/api/config` | GET/PUT | Configuration |

## 📄 License

MIT License

---

<p align="center">Made with ❤️ by <a href="https://github.com/wt521-888">wt521-888</a></p>