import os
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from nhk_client import NHKNewsClient
from sqlalchemy.orm import Session
from summarizer import Summarizer

# 実際のファイル名 database.py に定義されているモデルをインポート
from database import (
    Article,
    ArticleKeyPoint,
    Base,
    SessionLocal,
    Video,
    engine,
)

# テーブル作成
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/news/collect")
def collect_news(db: Session = Depends(get_db)):
    """NHKニュースRSSから記事を取得し、要約してDBに保存する"""
    try:
        nhk_client = NHKNewsClient()
        summarizer = Summarizer(os.getenv("GEMINI_API_KEY"))

        # NHK RSSから記事を取得
        articles = nhk_client.fetch_news(categories=["main"], max_articles=20)

        # 1. RSSから見つかった記事をDBに保存
        new_count = 0
        for a in articles:
            db_article = (
                db.query(Article).filter(Article.article_id == a["article_id"]).first()
            )
            if not db_article:
                db_article = Article(
                    article_id=a["article_id"],
                    title=a["title"],
                    link=a["link"],
                    description=a["description"],
                    category=a.get("category"),
                    source=a.get("source", "NHK"),
                    published_at=a["published_at"],
                    status="unprocessed",
                )
                db.add(db_article)
                new_count += 1
        db.commit()

        # 2. データベース内の「全ての未処理記事」を処理する
        pending_articles = (
            db.query(Article)
            .filter(
                (Article.status == "unprocessed")
                | (Article.summary.like("%要約の生成に失敗しました%"))
            )
            .all()
        )

        processed_count = 0
        for db_article in pending_articles:
            try:
                # 要約に使うテキストを用意 (description または content)
                text_to_summarize = db_article.description or ""

                # contentがまだなく、descriptionが短い場合は記事本文を取得
                if not db_article.content and len(text_to_summarize) < 200:
                    content = nhk_client.fetch_article_content(db_article.link)
                    if content:
                        db_article.content = content
                        text_to_summarize = content
                        db.commit()

                # テキストがあれば要約を生成
                if text_to_summarize and len(text_to_summarize) > 50:
                    # API制限回避 (Free Tier: 15 RPM / 1M TPM)
                    time.sleep(5)

                    # AI要約の生成
                    summary_data = summarizer.summarize_article(text_to_summarize)
                    db_article.summary = summary_data.get("summary")

                    # 重要ポイントの保存（既存分を削除して更新）
                    db.query(ArticleKeyPoint).filter(
                        ArticleKeyPoint.article_id == db_article.article_id
                    ).delete()
                    for pt in summary_data.get("key_points", []):
                        kp = ArticleKeyPoint(article_id=db_article.article_id, point=pt)
                        db.add(kp)

                    db_article.status = "processed"
                    db.commit()
                    processed_count += 1
                else:
                    print(
                        f"Skipping {db_article.article_id}: Insufficient text for summarization"
                    )
                    db_article.status = "skipped"
                    db.commit()

            except Exception as e:
                print(f"Error processing {db_article.article_id}: {e}")
                db.rollback()

        return {
            "status": "success",
            "processed_articles": processed_count,
            "new_articles": new_count,
            "total_found": len(articles),
        }
    except Exception as e:
        print(f"Global error in collect_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/list")
def list_news(db: Session = Depends(get_db)):
    """要約済みのニュース一覧を取得 (NHK記事を優先、なければYouTube動画)"""
    result = []

    # NHK記事を取得
    articles = (
        db.query(Article)
        .filter(Article.status == "processed")
        .order_by(Article.published_at.desc())
        .limit(50)
        .all()
    )

    for a in articles:
        key_points = [kp.point for kp in a.key_points]
        result.append(
            {
                "id": a.article_id,
                "title": a.title,
                "summary": a.summary,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "link": a.link,
                "source": a.source,
                "category": a.category,
                "status": a.status,
                "key_points": key_points,
                "type": "article",
            }
        )

    # NHK記事が少ない場合、YouTube動画も含める (後方互換性)
    if len(result) < 10:
        videos = (
            db.query(Video)
            .filter(Video.status == "processed")
            .order_by(Video.published_at.desc())
            .limit(20)
            .all()
        )
        for v in videos:
            key_points = [kp.point for kp in v.key_points]
            result.append(
                {
                    "id": v.youtube_id,
                    "youtube_id": v.youtube_id,
                    "title": v.title,
                    "summary": v.summary,
                    "published_at": (
                        v.published_at.isoformat() if v.published_at else None
                    ),
                    "thumbnail_url": v.thumbnail_url,
                    "status": v.status,
                    "key_points": key_points,
                    "type": "video",
                }
            )

    # 公開日時でソート
    result.sort(key=lambda x: x.get("published_at") or "", reverse=True)

    return result


# =====================================================
# 旧YouTube用エンドポイント (後方互換性のため残す)
# =====================================================


@app.get("/api/news/videos")
def list_videos(db: Session = Depends(get_db)):
    """要約済みのYouTube動画一覧を取得 (旧API)"""
    videos = (
        db.query(Video)
        .filter(Video.status == "processed")
        .order_by(Video.published_at.desc())
        .all()
    )
    result = []
    for v in videos:
        key_points = [kp.point for kp in v.key_points]
        result.append(
            {
                "youtube_id": v.youtube_id,
                "title": v.title,
                "summary": v.summary,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "thumbnail_url": v.thumbnail_url,
                "status": v.status,
                "key_points": key_points,
            }
        )
    return result
