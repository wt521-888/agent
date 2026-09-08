"""
FastAPI 入口
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import resumes, scoring, interview, config

# 加载 .env
load_dotenv()

app = FastAPI(
    title="简历智能打分 Agent",
    description="上传简历 + 招聘信息 → LLM 多维度打分 + 改进建议 + 模拟面试",
    version="2.4.0",
)

# CORS（开发期全开；生产请收敛）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# uploads 目录作为静态资源（可选：前端展示缩略图）
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 路由
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(scoring.router, prefix="/api/score", tags=["scoring"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/")
def root():
    return {"message": "简历智能打分 Agent API", "version": "2.4.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

