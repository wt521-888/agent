"""
Pydantic 数据校验模型（API 入参/出参）
"""
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field


# ---------------- Resume ----------------
class ResumeBase(BaseModel):
    id: int
    filename: str
    file_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeContent(ResumeBase):
    """详情：包含解析出的纯文本"""
    content: str


# ---------------- Scoring ----------------
class JobScoreRequest(BaseModel):
    resume_id: int
    job_description: str = Field(..., min_length=10, description="至少 10 字")


class DimensionScores(BaseModel):
    skills: int = Field(..., ge=0, le=100)
    experience: int = Field(..., ge=0, le=100)
    education: int = Field(..., ge=0, le=100)
    project: int = Field(..., ge=0, le=100)


class LearningResource(BaseModel):
    title: str
    type: str  # 网站/视频/书籍/课程
    url: str
    description: str


class ScoreResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    dimension_scores: DimensionScores
    strengths: List[str]
    weaknesses: List[str]
    resume_improvements: List[str]
    knowledge_areas: List[str]
    learning_resources: List[LearningResource]


class ScoreRecordOut(BaseModel):
    id: int
    resume_id: int
    resume_filename: str
    candidate_name: str = ""
    company: str = ""
    position: str = ""
    record_name: str = ""
    job_description: str
    overall_score: int
    result: ScoreResult
    search_summary: str = ""
    created_at: datetime

    class Config:
        from_attributes = True
