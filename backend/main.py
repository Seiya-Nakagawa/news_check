"""
News Check バックエンドAPI

Google News RSSからニュースを取得し、バッチ処理で要約して日別ダイジェストを生成する。
"""

import os
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google_news_client import GoogleNewsClient
from sqlalchemy.orm import Session
from summarizer import Summarizer

from database import (
    Article,
    ArticleKeyPoint,
    Base,
    DailyDigest,
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
    """
    Google News RSSからニュースを取得し、バッチ処理で要約してDailyDigestに保存する。
    1回のAPI呼び出しで複数記事を要約するため、API使用量を大幅に削減。
    """
    try:
        news_client = GoogleNewsClient()
        summarizer = Summarizer(os.getenv("GEMINI_API_KEY"))
        today = date.today()

        # Google News RSSから記事を取得
        articles = news_client.fetch_news(topics=["top"], max_articles=5)

        if not articles:
            return {
                "status": "success",
                "message": "No articles found",
                "articles_count": 0,
            }

        print(f"Fetched {len(articles)} articles from Google News")

        # 既存のダイジェストを確認
        existing_digest = db.query(DailyDigest).filter(DailyDigest.date == today).first()

        # バッチ要約を実行
        summaries = summarizer.summarize_batch(articles)

        # ダイジェストデータを構築
        headlines = []
        for i, article in enumerate(articles):
            summary_text = ""
            if i < len(summaries):
                summary_item = summaries[i]
                if isinstance(summary_item, dict):
                    summary_text = summary_item.get("summary", "")
                else:
                    summary_text = str(summary_item)

            headlines.append({
                "title": article.get("title", ""),
                "summary": summary_text,
                "link": article.get("link", ""),
                "source": "Google News",
                "published_at": article.get("published_at").isoformat() if article.get("published_at") else None,
            })

        # DailyDigestを保存または更新
        if existing_digest:
            existing_digest.headlines = headlines
            existing_digest.updated_at = datetime.utcnow()
        else:
            new_digest = DailyDigest(
                date=today,
                headlines=headlines,
            )
            db.add(new_digest)

        db.commit()

        return {
            "status": "success",
            "date": today.isoformat(),
            "articles_count": len(headlines),
            "api_calls": 1,  # バッチ処理により1回のAPI呼び出しのみ
        }

    except Exception as e:
        print(f"Error in collect_news: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/daily")
def get_daily_digest(
    target_date: Optional[str] = Query(None, description="対象日 (YYYY-MM-DD形式、省略時は今日)"),
    db: Session = Depends(get_db),
):
    """
    指定日の日別ダイジェストを取得する。
    1日分のニュースを箇条書き形式で返す。
    """
    try:
        if target_date:
            try:
                query_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        else:
            query_date = date.today()

        digest = db.query(DailyDigest).filter(DailyDigest.date == query_date).first()

        if not digest:
            return {
                "date": query_date.isoformat(),
                "headlines": [],
                "message": "No digest found for this date",
            }

        return {
            "date": digest.date.isoformat(),
            "headlines": digest.headlines,
            "updated_at": digest.updated_at.isoformat() if digest.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_daily_digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/list")
def list_news(db: Session = Depends(get_db)):
    """
    要約済みのニュース一覧を取得 (後方互換性のため残す)
    新しいシステムではDailyDigestを使用するが、旧フロントエンドのためにこのエンドポイントも維持。
    """
    result = []

    # まずDailyDigestから今日のデータを取得
    today_digest = db.query(DailyDigest).filter(DailyDigest.date == date.today()).first()
    if today_digest and today_digest.headlines:
        for i, headline in enumerate(today_digest.headlines):
            result.append({
                "id": f"gn_{i}",
                "title": headline.get("title", ""),
                "summary": headline.get("summary", ""),
                "published_at": headline.get("published_at"),
                "link": headline.get("link", ""),
                "source": headline.get("source", "Google News"),
                "category": None,
                "status": "processed",
                "key_points": [],
                "type": "article",
            })

    # DailyDigestがなければ旧Articleテーブルから取得
    if not result:
        articles = (
            db.query(Article)
            .filter(Article.status == "processed")
            .order_by(Article.published_at.desc())
            .limit(50)
            .all()
        )

        for a in articles:
            key_points = [kp.point for kp in a.key_points]
            result.append({
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
            })

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
            result.append({
                "id": v.youtube_id,
                "youtube_id": v.youtube_id,
                "title": v.title,
                "summary": v.summary,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "thumbnail_url": v.thumbnail_url,
                "status": v.status,
                "key_points": key_points,
                "type": "video",
            })

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
        result.append({
            "youtube_id": v.youtube_id,
            "title": v.title,
            "summary": v.summary,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "thumbnail_url": v.thumbnail_url,
            "status": v.status,
            "key_points": key_points,
        })
    return result
