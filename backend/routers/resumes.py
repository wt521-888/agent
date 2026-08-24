"""
简历管理：上传 / 列表 / 删除
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Resume
from schemas import ResumeBase, ResumeContent
from services.resume_parser import parse_resume

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {"pdf", "docx", "doc", "txt"}


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
