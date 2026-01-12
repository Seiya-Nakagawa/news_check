import os
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from summarizer import Summarizer
from youtube_client import YouTubeClient

# 実際のファイル名 database.py に定義されているモデルをインポート
from database import Base, KeyPoint, SessionLocal, Video, engine

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
    """YouTubeからニュースを取得し、要約してDBに保存する"""
    try:
        youtube_client = YouTubeClient(os.getenv("YOUTUBE_API_KEY"))
        summarizer = Summarizer(os.getenv("GEMINI_API_KEY"))

        # ANNnewsCH のチャンネルID
        channel_id = "UCGCZAYq59byoQDfGzU496OQ"
        videos = youtube_client.search_news_videos(channel_id)

        # 1. YouTubeから見つかった動画をDBに保存
        for v in videos:
            db_video = db.query(Video).filter(Video.youtube_id == v["video_id"]).first()
            if not db_video:
                db_video = Video(
                    youtube_id=v["video_id"],
                    title=v["title"],
                    channel_id=channel_id,
                    thumbnail_url=v.get("thumbnail"),
                    published_at=v["published_at"],
                    status="unprocessed",
                )
                db.add(db_video)
                db.flush()
            elif db_video.status == "failed_transcript":
                db_video.status = "unprocessed"
                db.flush()

        db.commit()

        # 2. データベース内の「全ての未処理動画」を処理する
        pending_videos = (
            db.query(Video)
            .filter(
                (Video.status == "unprocessed")
                | (Video.summary.like("%要約の生成に失敗しました%"))
            )
            .all()
        )

        processed_count = 0
        for db_video in pending_videos:
            try:
                # 字幕または説明文を取得
                transcript = db_video.transcript or youtube_client.get_transcript(
                    db_video.youtube_id
                )
                if transcript:
                    db_video.transcript = transcript

                    # API制限回避
                    time.sleep(5)

                    # AI要約の生成
                    summary_data = summarizer.summarize(transcript)
                    db_video.summary = summary_data.get("summary")

                    # 重要ポイントの保存（既存分を削除して更新）
                    # models.py の定義に合わせて youtube_id と point カラムを使用
                    db.query(KeyPoint).filter(
                        KeyPoint.youtube_id == db_video.youtube_id
                    ).delete()
                    for pt in summary_data.get("key_points", []):
                        kp = KeyPoint(youtube_id=db_video.youtube_id, point=pt)
                        db.add(kp)

                    db_video.status = "processed"
                    db.commit()
                    processed_count += 1
                else:
                    db_video.status = "failed_transcript"
                    db.commit()
            except Exception as e:
                print(f"Error processing {db_video.youtube_id}: {e}")
                db.rollback()

        return {
            "status": "success",
            "processed_videos": processed_count,
            "total_found": len(videos),
        }
    except Exception as e:
        print(f"Global error in collect_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/list")
def list_news(db: Session = Depends(get_db)):
    """要約済みのニュース一覧を取得"""
    videos = (
        db.query(Video)
        .filter(Video.status == "processed")
        .order_by(Video.published_at.desc())
        .all()
    )
    result = []
    for v in videos:
        # key_points テーブルから内容を取得
        key_points = [kp.point for kp in v.key_points]
        result.append(
            {
                "id": v.youtube_id,
                "video_id": v.youtube_id,
                "title": v.title,
                "summary": v.summary,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "thumbnail": v.thumbnail_url,  # Frontend expects 'thumbnail'
                "key_points": key_points,
            }
        )
    return result
