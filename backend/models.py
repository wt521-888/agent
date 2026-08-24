"""
SQLAlchemy ORM 模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Resume(Base):
    """简历表"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)        # 原始文件名
    file_path = Column(String(500), nullable=False)       # 落盘路径
    file_type = Column(String(20), nullable=False)        # pdf/docx/txt
    content = Column(Text, default="")                    # 抽取出的纯文本
    size = Column(Integer, default=0)                     # 字节数
    created_at = Column(DateTime, default=datetime.utcnow)

    # 一份简历可以有多条打分记录
    scores = relationship(
        "ScoreRecord", back_populates="resume", cascade="all, delete-orphan"
    )


class ScoreRecord(Base):
    """打分记录表"""
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    # 新增：人名 / 公司 / 岗位 + 组合名
    candidate_name = Column(String(100), default="")    # 候选人姓名（从简历或文件名提取）
    company = Column(String(200), default="")           # 招聘公司（LLM 从 JD 提取）
    position = Column(String(200), default="")          # 招聘岗位（LLM 从 JD 提取）
    record_name = Column(String(500), default="")       # 组合名：人名_公司_岗位
    job_description = Column(Text, nullable=False)      # 招聘信息原文
    overall_score = Column(Integer, default=0)          # 总分
    result_json = Column(JSON, nullable=False)          # 完整打分结果
    search_summary = Column(Text, default="")           # Tavily 摘要
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="scores")
