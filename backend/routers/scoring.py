"""
打分与历史记录（带缓存 + 内容瘦身 + 正则优先 + Token统计）
"""
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Resume, ScoreRecord, ScoreCache
from backend.schemas import (
    JobScoreRequest,
    ScoreRecordOut,
    ScoreResult,
    TokenUsage,
)

from backend.services.search_service import search_company_info, format_search_summary
from backend.services.resume_parser import slim_resume, slim_job_description
from backend.services.llm_service import (
    score_resume,
    extract_job_info,
    extract_candidate_name,
    extract_job_info_regex,
    make_record_name,
    validate_content,
)

router = APIRouter()


def _make_cache_key(resume_id: int, job_description: str) -> str:
    """生成缓存key：简历ID + JD内容的md5"""
    raw = f"{resume_id}:{job_description.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _to_out(r: ScoreRecord, token_usage: TokenUsage = None) -> ScoreRecordOut:
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
        token_usage=token_usage,
        created_at=r.created_at,
    )


@router.post("", response_model=ScoreRecordOut)
async def score(req: JobScoreRequest, db: Session = Depends(get_db)):
    """
    核心打分接口（带缓存 + 内容瘦身 + 正则优先 + Token统计）
    """
    # ---- 1) 校验简历存在 ----
    resume = db.query(Resume).filter(Resume.id == req.resume_id).first()
    if not resume:
        raise HTTPException(404, "简历不存在")
    if not resume.content or not resume.content.strip():
        raise HTTPException(
            400, "该简历文本为空（可能解析失败），无法打分。请检查文件或重新上传。"
        )

    # ---- 2) 内容质量校验 ----
    validation_error = validate_content(resume.content, req.job_description)
    if validation_error:
        raise HTTPException(400, validation_error)

    # ---- 3) 查缓存 ----
    cache_key = _make_cache_key(req.resume_id, req.job_description)
    cached = db.query(ScoreCache).filter(ScoreCache.cache_key == cache_key).first()
    
    if cached:
        # 缓存命中：直接返回，不调用任何 LLM
        cached.hit_count += 1
        cached.last_hit_at = datetime.utcnow()
        db.commit()
        
        # 用正则提取公司/岗位（零 token）
        job_info = extract_job_info_regex(req.job_description)
        company = job_info.get("company", "")
        position = job_info.get("position", "")
        candidate_name = extract_candidate_name(resume.content, resume.filename)
        record_name = make_record_name(candidate_name, company, position)
        
        record = ScoreRecord(
            resume_id=resume.id,
            candidate_name=candidate_name,
            company=company,
            position=position,
            record_name=record_name,
            job_description=req.job_description,
            overall_score=int(cached.result_json.get("overall_score", 0)),
            result_json=cached.result_json,
            search_summary=cached.search_summary or "",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # 缓存命中，token 消耗为 0
        token_usage = TokenUsage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            cache_hit=True,
            regex_extracted=True,
        )
        
        print(f"[score] 缓存命中 key={cache_key}, hit_count={cached.hit_count}")
        return _to_out(record, token_usage)

    # ---- 4) 缓存未命中，先瘦身 ----
    slim_resume_content = slim_resume(resume.content, max_length=2000)
    slim_jd = slim_job_description(req.job_description, max_length=800)
    
    print(f"[score] 简历瘦身: {len(resume.content)}字 -> {len(slim_resume_content)}字")
    print(f"[score] JD瘦身: {len(req.job_description)}字 -> {len(slim_jd)}字")

    # ---- 5) 提取公司/岗位（正则优先） ----
    regex_result = extract_job_info_regex(req.job_description)
    regex_extracted = bool(regex_result["company"] or regex_result["position"])
    
    job_info = extract_job_info(req.job_description)
    company = job_info.get("company", "")
    position = job_info.get("position", "")
    candidate_name = extract_candidate_name(resume.content, resume.filename)
    record_name = make_record_name(candidate_name, company, position)

    # ---- 6) Tavily 搜索 ----
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

    # ---- 7) LLM 打分 ----
    try:
        result, usage = score_resume(
            job_description=slim_jd,
            search_summary=search_summary,
            resume_content=slim_resume_content,
        )
    except Exception as e:
        raise HTTPException(500, f"LLM 打分失败: {e}")

    # 构建 token 使用量统计
    token_usage = TokenUsage(
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        estimated_cost_usd=usage.get("estimated_cost_usd", 0.0),
        cache_hit=False,
        regex_extracted=regex_extracted,
    )

    # ---- 8) 写缓存 ----
    new_cache = ScoreCache(
        cache_key=cache_key,
        resume_id=req.resume_id,
        job_description=req.job_description,
        result_json=result,
        search_summary=search_summary,
    )
    db.add(new_cache)
    
    # ---- 9) 写历史记录 ----
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

    print(f"[score] Token 消耗: {token_usage.total_tokens} (输入:{token_usage.prompt_tokens} 输出:{token_usage.completion_tokens})")
    print(f"[score] 预估成本: ")
    print(f"[score] 缓存已写入 key={cache_key}")
    
    return _to_out(record, token_usage)


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


@router.get("/cache/stats")
def cache_stats(db: Session = Depends(get_db)):
    """查看缓存统计"""
    total = db.query(ScoreCache).count()
    total_hits = sum(c.hit_count for c in db.query(ScoreCache).all())
    top_caches = (
        db.query(ScoreCache)
        .order_by(ScoreCache.hit_count.desc())
        .limit(10)
        .all()
    )
    return {
        "total_cached": total,
        "total_hits": total_hits,
        "top_caches": [
            {
                "cache_key": c.cache_key[:8] + "...",
                "resume_id": c.resume_id,
                "hit_count": c.hit_count,
                "created_at": c.created_at,
            }
            for c in top_caches
        ]
    }

