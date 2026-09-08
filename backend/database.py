"""
SQLite 数据库连接与初始化
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_agent.db")

# SQLite 多线程下需要 check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


# ---------- 仅对 SQLite 启用 WAL + 同步策略，防损坏 ----------
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")        # 写前日志，并发更安全
        cursor.execute("PRAGMA synchronous=NORMAL")      # 折中：性能 + 抗损坏
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：每次请求一个 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表（首次启动时自动建表，已存在则跳过）"""
    from backend.models import Resume, ScoreRecord, ScoreCache  # noqa: F401  延迟导入避免循环
    Base.metadata.create_all(bind=engine)

