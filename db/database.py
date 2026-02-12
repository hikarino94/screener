"""データベース接続・初期化"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import config
from models.schemas import Base


engine = create_engine(config.db_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """テーブル作成"""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """セッション取得"""
    return SessionLocal()
