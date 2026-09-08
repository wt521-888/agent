"""
简历修改路由：根据打分建议重写简历，原文件备份后用相同格式输出新版本

设计要点：
1. **不直接修改原简历**：先把原文件复制为 `xxx_backup_yyyymmdd_HHMMSS.ext`
2. **沿用原模板（格式）**：根据原扩展名（pdf/docx/doc/txt）输出新文件
3. **基于建议修改**：调用 LLM 把 resume_improvements 应用到简历中
"""
import os
import re
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Resume
from schemas import ModifyResumeRequest, ModifyResumeResponse
from services.llm_service import modify_resume
from services.resume_writer import write_resume

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MODIFIED_SUBDIR = "modified"      # 修改后的简历放在 uploads/modified/
BACKUP_SUBDIR = "backups"         # 原文件备份放在 uploads/backups/


def _now_tag() -> str:
    """时间戳后缀，用于备份/新文件名"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    stem, ext = os.path.splitext(name)
    safe_stem = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", stem).strip().strip(".")
    return f"{safe_stem}{ext.lower()}" if safe_stem else f"resume{ext.lower()}"


def _split_stem_ext(filename: str) -> tuple[str, str]:
    """拆出 (stem, ext)，ext 带点；空 ext 返回 ('name', '')"""
    stem, ext = os.path.splitext(filename)
    return stem, ext.lower()


@router.post("/modify", response_model=ModifyResumeResponse)
async def modify_resume_endpoint(
    req: ModifyResumeRequest, db: Session = Depends(get_db)
):
    """
    根据改进建议重写简历：
    1) 备份原文件
    2) LLM 改写
    3) 用原格式写出新文件
    4) 返回新文件路径 + 修改后文本
    """
    # ---- 1) 校验简历 ----
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")
    if not resume.content or not resume.content.strip():
        raise HTTPException(
            400, "该简历文本为空（可能解析失败），无法修改。请检查文件或重新上传。"
        )
    if not req.improvements or not [s for s in req.improvements if s and s.strip()]:
        raise HTTPException(400, "改进建议为空，无法重写简历")

    # ---- 2) 准备目录 ----
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    backup_dir = os.path.join(UPLOAD_DIR, BACKUP_SUBDIR)
    modified_dir = os.path.join(UPLOAD_DIR, MODIFIED_SUBDIR)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(modified_dir, exist_ok=True)

    original_filename = _safe_filename(resume.filename)
    stem, ext = _split_stem_ext(original_filename)
    file_type = ext.lstrip(".") or resume.file_type or "txt"
    tag = _now_tag()

    # ---- 3) 备份原文件（copy，不动原文件） ----
    backup_filename = f"{stem}_backup_{tag}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)
    try:
        if resume.file_path and os.path.exists(resume.file_path):
            shutil.copy2(resume.file_path, backup_path)
        else:
            # 原文件丢失，但有文本内容：把 content 写成 txt 作为"事实上的备份"
            backup_path = os.path.join(backup_dir, f"{stem}_backup_{tag}.txt")
            with open(backup_path, "w", encoding="utf-8-sig") as f:
                f.write(resume.content or "")
    except Exception as e:
        raise HTTPException(500, f"备份原简历失败: {e}")

    # ---- 4) LLM 改写 ----
    try:
        modified_content = modify_resume(resume.content, req.improvements)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"LLM 改写失败: {e}")

    # ---- 5) 用原格式写出新文件 ----
    new_filename = f"{stem}_modified_{tag}{ext}"
    new_file_path = os.path.join(modified_dir, new_filename)
    try:
        write_resume(modified_content, file_type, new_file_path)
    except Exception as e:
        raise HTTPException(500, f"按原格式写新文件失败: {e}")

    # ---- 6) 构造下载 URL（uploads 已挂载为 /uploads 静态目录） ----
    # 数据库里存的是相对路径，便于跨平台
    rel_backup = os.path.relpath(backup_path, UPLOAD_DIR).replace(os.sep, "/")
    rel_new = os.path.relpath(new_file_path, UPLOAD_DIR).replace(os.sep, "/")

    applied = [s.strip() for s in req.improvements if s and s.strip()]

    return ModifyResumeResponse(
        resume_id=resume.id,
        original_filename=original_filename,
        backup_filename=backup_filename,
        new_filename=new_filename,
        backup_path=rel_backup,
        new_file_path=rel_new,
        new_file_url=f"/uploads/{rel_new}",
        modified_content=modified_content,
        applied_improvements=applied,
    )
