"""
模拟面试路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.database import get_db
from backend.models import Resume
from backend.services.interview_service import generate_interview_questions, evaluate_answer

router = APIRouter()


class InterviewRequest(BaseModel):
    """面试请求"""
    resume_id: int
    job_description: str = Field(..., min_length=10, description="岗位描述")
    num_questions: int = Field(default=5, ge=1, le=10, description="问题数量")


class QuestionItem(BaseModel):
    """面试问题"""
    id: int
    category: str
    question: str
    difficulty: str
    key_points: List[str]


class InterviewResponse(BaseModel):
    """面试问题响应"""
    questions: List[QuestionItem]
    resume_filename: str


class EvaluateRequest(BaseModel):
    """评估请求"""
    question: str
    answer: str
    job_description: str = ""
    key_points: List[str] = []


class EvaluateResponse(BaseModel):
    """评估响应"""
    overall_score: int
    scores: dict
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    reference_answer: str


@router.post("/questions", response_model=InterviewResponse)
async def get_interview_questions(req: InterviewRequest, db: Session = Depends(get_db)):
    """生成面试问题"""
    # 获取简历
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")
    if not resume.content or not resume.content.strip():
        raise HTTPException(400, "简历内容为空，请重新上传")
    
    try:
        result = generate_interview_questions(
            resume_content=resume.content,
            job_description=req.job_description,
            num_questions=req.num_questions
        )
        return InterviewResponse(
            questions=result.get("questions", []),
            resume_filename=resume.filename
        )
    except Exception as e:
        raise HTTPException(500, f"生成面试问题失败: {e}")


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_interview_answer(req: EvaluateRequest):
    """评估面试回答"""
    try:
        result = evaluate_answer(
            question=req.question,
            answer=req.answer,
            job_description=req.job_description,
            key_points=req.key_points
        )
        return EvaluateResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"评估回答失败: {e}")

