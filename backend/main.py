import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from youtube_client import YouTubeClient

from database import Channel, Video, get_db

load_dotenv()

app = FastAPI(title="News Check API")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube_client = YouTubeClient(YOUTUBE_API_KEY)


@app.get("/")
def read_root():
    return {"message": "Welcome to News Check API"}


@app.post("/news/collect")
def collect_news(db: Session = Depends(get_db)):
    try:
        # ANNnewsCH の情報を取得・保存
        handle = "@ANNnewsCH"
        channel_id = youtube_client.get_channel_id(handle)

        db_channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
        if not db_channel:
            db_channel = Channel(
                channel_id=channel_id,
                name="ANNnewsCH",
                url=f"https://www.youtube.com/{handle}",
            )
            db.add(db_channel)
            db.commit()

        # 動画を検索
        videos = youtube_client.search_news_videos(channel_id)

        collected_count = 0
        for v in videos:
            # 既に存在するかチェック
            exists = db.query(Video).filter(Video.youtube_id == v["id"]).first()
            if not exists:
                new_video = Video(
                    youtube_id=v["id"],
                    title=v["title"],
                    channel_id=channel_id,
                    published_at=v["published_at"],
                    status="unprocessed",
                )
                db.add(new_video)
                collected_count += 1

        db.commit()
        return {
            "status": "success",
            "collected_videos": collected_count,
            "total_found": len(videos),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/news/list")
def list_news(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.published_at.desc()).all()
    return videos
