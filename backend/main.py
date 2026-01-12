import os
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Base, KeyPoint, Video
from sqlalchemy.orm import Session
from summarizer import Summarizer
from youtube_client import YouTubeClient

from database import SessionLocal, engine

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

        # 1. YouTubeから見つかった動画をDBに保存（または更新）
        for v in videos:
            db_video = db.query(Video).filter(Video.youtube_id == v["video_id"]).first()
            if not db_video:
                db_video = Video(
                    youtube_id=v["video_id"],
                    title=v["title"],
                    description=v["description"],
                    published_at=v["published_at"],
                    thumbnail=v["thumbnail"],
                    status="unprocessed",
                )
                db.add(db_video)
                db.flush()
            elif db_video.status == "failed_transcript":
                # 字幕取得に失敗していた場合は再試行対象にする
                db_video.status = "unprocessed"
                db.flush()

        db.commit()

        # 2. データベース内の「全ての未処理動画」を処理する
        # YouTubeの検索結果（上位件数）から漏れた古い動画も、DBに残っていればここで処理される
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
                    db.query(KeyPoint).filter(KeyPoint.video_id == db_video.id).delete()
                    for point in summary_data.get("key_points", []):
                        kp = KeyPoint(video_id=db_video.id, content=point)
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
        key_points = db.query(KeyPoint).filter(KeyPoint.video_id == v.id).all()
        result.append(
            {
                "id": v.id,
                "video_id": v.youtube_id,
                "title": v.title,
                "summary": v.summary,
                "published_at": v.published_at,
                "thumbnail": v.thumbnail,
                "key_points": [kp.content for kp in key_points],
            }
        )
    return result
