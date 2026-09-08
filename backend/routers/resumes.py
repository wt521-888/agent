"""
简历管理：上传 / 列表 / 删除 / 优化
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.database import get_db
from backend.models import Resume
from backend.schemas import ResumeBase, ResumeContent
from backend.services.resume_parser import parse_resume

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {"pdf", "docx", "doc", "txt"}


class ModifyResumeRequest(BaseModel):
    """简历优化请求"""
    resume_id: int
    improvements: List[str] = Field(..., min_length=1, description="改进建议列表")
    score_record_id: Optional[int] = None


class ModifyResumeResponse(BaseModel):
    """简历优化响应"""
    resume_id: int
    original_filename: str
    modified_content: str
    applied_improvements: List[str]
    download_url: Optional[str] = None


@router.post("/upload", response_model=ResumeContent)
async def upload_resume(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """上传一份简历（multipart/form-data，字段名 file）"""
    if not file.filename:
        raise HTTPException(400, "文件名为空")

    # 解析扩展名
    if "." not in file.filename:
        raise HTTPException(400, "文件无扩展名")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"仅支持 {', '.join(sorted(ALLOWED_EXT))} 格式")

    # 读取 + 大小校验
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"文件超过 {MAX_FILE_SIZE // 1024 // 1024}MB")
    if not contents:
        raise HTTPException(400, "文件为空")

    # 落盘
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    # 解析文本（解析失败仍保留文件，但 content 为空字符串）
    try:
        text = parse_resume(file_path, ext)
    except Exception as e:
        text = ""
        # 记录错误但不抛
        print(f"[resume_parser] 解析失败: {e}")

    # 写库
    db_resume = Resume(
        filename=file.filename,
        file_path=file_path,
        file_type=ext,
        content=text,
        size=len(contents),
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


@router.get("", response_model=list[ResumeBase])
def list_resumes(db: Session = Depends(get_db)):
    """返回所有简历（按上传时间倒序）"""
    return db.query(Resume).order_by(Resume.created_at.desc()).all()


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """删除一份简历（含磁盘文件 + 数据库记录 + 关联打分记录）"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")

    # 尝试删除文件
    try:
        if resume.file_path and os.path.exists(resume.file_path):
            os.remove(resume.file_path)
    except Exception as e:
        print(f"[delete] 删除文件失败: {e}")

    db.delete(resume)
    db.commit()
    return {"message": "删除成功", "id": resume_id}


@router.post("/modify", response_model=ModifyResumeResponse)
async def modify_resume(req: ModifyResumeRequest, db: Session = Depends(get_db)):
    """
    一键优化简历：根据改进建议重写简历内容
    
    功能：
    1. 获取原简历内容
    2. 调用 LLM 根据改进建议重写简历
    3. 返回优化后的简历内容（不修改原文件）
    """
    # 获取简历
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")
    if not resume.content or not resume.content.strip():
        raise HTTPException(400, "简历内容为空，无法优化")

    try:
        # 调用 LLM 优化简历
        from backend.services.llm_service import optimize_resume
        result = optimize_resume(
            resume_content=resume.content,
            improvements=req.improvements
        )
        
        return ModifyResumeResponse(
            resume_id=resume.id,
            original_filename=resume.filename,
            modified_content=result.get("modified_content", ""),
            applied_improvements=result.get("applied_improvements", req.improvements),
            download_url=None  # 暂不支持下载，返回纯文本
        )
    except Exception as e:
        raise HTTPException(500, f"简历优化失败: {e}")

