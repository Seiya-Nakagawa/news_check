import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/news_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Channel(Base):
    __tablename__ = "channels"
    channel_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String)
    videos = relationship("Video", back_populates="channel")


class Video(Base):
    """YouTube動画用モデル (旧システム、後方互換性のため残す)"""

    __tablename__ = "videos"
    youtube_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    channel_id = Column(String, ForeignKey("channels.channel_id"))
    transcript = Column(Text)
    summary = Column(Text)
    thumbnail_url = Column(String)
    published_at = Column(DateTime(timezone=True))
    status = Column(String, default="unprocessed")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    channel = relationship("Channel", back_populates="videos")
    key_points = relationship(
        "KeyPoint", back_populates="video", cascade="all, delete-orphan"
    )


class KeyPoint(Base):
    __tablename__ = "key_points"
    id = Column(Integer, primary_key=True, index=True)
    youtube_id = Column(String, ForeignKey("videos.youtube_id"))
    point = Column(Text, nullable=False)

    video = relationship("Video", back_populates="key_points")


# =====================================================
# NHKニュース記事用の新モデル
# =====================================================


class Article(Base):
    """NHKニュース記事用モデル"""

    __tablename__ = "articles"
    article_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    description = Column(Text)  # RSSのdescription (概要)
    content = Column(Text)  # 記事本文 (スクレイピングで取得)
    summary = Column(Text)  # Geminiによる要約
    category = Column(String)  # ニュースカテゴリ
    source = Column(String, default="NHK")  # ニュースソース
    published_at = Column(DateTime(timezone=True))
    status = Column(String, default="unprocessed")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    key_points = relationship(
        "ArticleKeyPoint", back_populates="article", cascade="all, delete-orphan"
    )


class ArticleKeyPoint(Base):
    """NHKニュース記事の重要ポイント"""

    __tablename__ = "article_key_points"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String, ForeignKey("articles.article_id"))
    point = Column(Text, nullable=False)

    article = relationship("Article", back_populates="key_points")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
