"""
打分与历史记录
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Resume, ScoreRecord
from schemas import (
    JobScoreRequest,
    ScoreRecordOut,
    ScoreResult,
)

from services.search_service import search_company_info, format_search_summary
from services.llm_service import (
    score_resume,
    extract_job_info,
    extract_candidate_name,
    make_record_name,
)

router = APIRouter()


def _to_out(r: ScoreRecord) -> ScoreRecordOut:
    """把 ORM 记录转成响应模型"""
    return ScoreRecordOut(
        id=r.id,
        resume_id=r.resume_id,
        resume_filename=r.resume.filename,
        candidate_name=r.candidate_name or "",
        company=r.company or "",
        position=r.position or "",
        record_name=r.record_name or "",
        job_description=r.job_description,
        overall_score=r.overall_score,
        result=ScoreResult(**r.result_json),
        search_summary=r.search_summary or "",
        created_at=r.created_at,
    )


@router.post("", response_model=ScoreRecordOut)
async def score(req: JobScoreRequest, db: Session = Depends(get_db)):
    """
    核心打分接口：
    1) 取简历文本
    2) LLM 提取公司/岗位（用于命名 & 搜索关键词）
    3) Tavily 联网搜索（失败不阻塞）
    4) LLM 打分（失败抛 500）
    5) 落库，record_name = 人名_公司_岗位
    """
    # ---- 1) 校验简历 ----
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")
    if not resume.content or not resume.content.strip():
        raise HTTPException(
            400, "该简历文本为空（可能解析失败），无法打分。请检查文件或重新上传。"
        )

    # ---- 2) 提取公司/岗位（用于历史记录命名 + 搜索关键词） ----
    job_info = extract_job_info(req.job_description)
    company = job_info.get("company", "")
    position = job_info.get("position", "")
    candidate_name = extract_candidate_name(resume.content, resume.filename)
    record_name = make_record_name(candidate_name, company, position)

    # ---- 3) Tavily 搜索（失败不影响主流程） ----
    search_summary = ""
    try:
        query_kw = " ".join(
            x for x in (company, position, "公司介绍 面试要求") if x
        ) or req.job_description.strip()[:100]
        results = search_company_info(
            company=company or "未知",
            position=position or "未知",
            query_keywords=query_kw,
        )
        search_summary = format_search_summary(results)
    except Exception as e:
        print(f"[score] Tavily 搜索失败（不影响主流程）: {e}")
        search_summary = ""

    # ---- 4) LLM 打分 ----
    try:
        result = score_resume(
            job_description=req.job_description,
            search_summary=search_summary,
            resume_content=resume.content,
        )
    except Exception as e:
        raise HTTPException(500, f"LLM 打分失败: {e}")

    # ---- 5) 落库 ----
    record = ScoreRecord(
        resume_id=resume.id,
        candidate_name=candidate_name,
        company=company,
        position=position,
        record_name=record_name,
        job_description=req.job_description,
        overall_score=int(result.get("overall_score", 0)),
        result_json=result,
        search_summary=search_summary,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _to_out(record)


@router.get("/history", response_model=list[ScoreRecordOut])
def history(db: Session = Depends(get_db)):
    """返回最近 50 条打分记录（按时间倒序）"""
    records = (
        db.query(ScoreRecord)
        .order_by(ScoreRecord.created_at.desc())
        .limit(50)
        .all()
    )
    return [_to_out(r) for r in records]


@router.delete("/history/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    """删除单条打分记录"""
    rec = db.query(ScoreRecord).filter(ScoreRecord.id == record_id).first()
    if not rec:
        raise HTTPException(404, "记录不存在")
    db.delete(rec)
    db.commit()
    return {"ok": True}
