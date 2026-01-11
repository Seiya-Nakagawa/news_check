import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from youtube_client import YouTubeClient
from summarizer import Summarizer

from database import Channel, Video, KeyPoint, engine, Base, get_db

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="News Check API")

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

youtube_client = YouTubeClient(YOUTUBE_API_KEY)
summarizer = Summarizer(GEMINI_API_KEY)


@app.get("/")
def read_root():
    return {"message": "Welcome to News Check API"}


@app.post("/api/news/collect")
def collect_news(db: Session = Depends(get_db)):
    """
    動画を収集し、字幕を取得して要約を生成する。
    """
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

        processed_count = 0
        for v in videos:
            # 既に存在するかチェック
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
                db.flush() # ID確定のため
            elif not db_video.transcript or db_video.status == "failed_transcript":
                # 前回失敗していたか、字幕がない場合は再試行する
                db_video.status = "unprocessed"
                db.flush()

            # 未処理の場合に要約を行う
            if db_video.status == "unprocessed":
                transcript = youtube_client.get_transcript(db_video.youtube_id)
                if transcript:
                    db_video.transcript = transcript

                    # 429 RESOURCE_EXHAUSTED 回避のため待機
                    import time
                    time.sleep(5)

                    # AI要約の生成
                    summary_data = summarizer.summarize(transcript)
                    db_video.summary = summary_data.get("summary")

                    # 重要ポイントの保存
                    for pt in summary_data.get("key_points", []):
                        kp = KeyPoint(youtube_id=db_video.youtube_id, point=pt)
                        db.add(kp)

                    db_video.status = "processed"
                    processed_count += 1
                else:
                    db_video.status = "failed_transcript"

        db.commit()
        return {
            "status": "success",
            "processed_videos": processed_count,
            "total_found": len(videos),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/list")
def list_news(db: Session = Depends(get_db)):
    """全ニュース一覧を取得 (重要な情報を全て含める)"""
    videos = db.query(Video).order_by(Video.published_at.desc()).all()

    result = []
    for v in videos:
        # タイトルのクレンジング
        clean_title = v.title
        if "【ライブ】" in clean_title:
            clean_title = clean_title.replace("【ライブ】", "")

        # 「まとめ」以降を削除
        if "まとめ" in clean_title:
            clean_title = clean_title.split("まとめ")[0] + "まとめ"

        result.append({
            "youtube_id": v.youtube_id,
            "title": clean_title.strip(),
            "summary": v.summary,
            "thumbnail_url": v.thumbnail_url,
            "published_at": v.published_at,
            "status": v.status,
            "key_points": [kp.point for kp in v.key_points],
            "channel_name": v.channel.name if v.channel else "ANNnewsCH"
        })
    return result

@app.get("/api/news/daily/{date}")
def get_daily_news(date: str, db: Session = Depends(get_db)):
    """指定日のニュース一覧を取得 (date: YYYY-MM-DD)"""
    from datetime import datetime, timedelta
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        next_day = dt + timedelta(days=1)

        videos = db.query(Video).filter(
            Video.published_at >= dt,
            Video.published_at < next_day
        ).order_by(Video.published_at.desc()).all()

        # KeyPointsも含めて返すための簡易的な実装
        result = []
        for v in videos:
            result.append({
                "youtube_id": v.youtube_id,
                "title": v.title,
                "summary": v.summary,
                "thumbnail_url": v.thumbnail_url,
                "published_at": v.published_at,
                "status": v.status,
                "key_points": [kp.point for kp in v.key_points],
                "channel_name": v.channel.name
            })
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@app.get("/api/news/video/{video_id}")
def get_video_detail(video_id: str, db: Session = Depends(get_db)):
    """特定の動画の詳細情報を取得"""
    v = db.query(Video).filter(Video.youtube_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "youtube_id": v.youtube_id,
        "title": v.title,
        "summary": v.summary,
        "transcript": v.transcript,
        "published_at": v.published_at,
        "status": v.status,
        "key_points": [kp.point for kp in v.key_points],
        "channel_name": v.channel.name,
        "channel_url": v.channel.url
    }

@app.delete("/api/news/video/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """特定の動画を削除（管理者用）"""
    v = db.query(Video).filter(Video.youtube_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    db.delete(v)
    db.commit()
    return {"status": "deleted", "youtube_id": video_id}
