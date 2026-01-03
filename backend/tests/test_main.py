from datetime import datetime
import pytest

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to News Check API"}

def test_get_news_list_empty(client):
    response = client.get("/api/news/list")
    assert response.status_code == 200
    assert response.json() == []

def test_create_and_get_video(client, db_session):
    # テストデータを直接DBに入れる
    from database import Video, Channel

    # チャンネルがないとForeignKeyエラーになるため作成
    channel = Channel(channel_id="UC123", name="Test Channel", url="http://test.com")
    db_session.add(channel)
    db_session.commit() # commitしてIDを確定

    video = Video(
        youtube_id="vid001",
        title="Test Video",
        channel_id="UC123",
        published_at=datetime(2024, 1, 1, 10, 0, 0),
        status="processed",
        summary="Summary text."
    )
    db_session.add(video)
    db_session.commit()

    response = client.get("/api/news/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["youtube_id"] == "vid001"
    assert data[0]["title"] == "Test Video"

def test_get_video_detail_not_found(client):
    response = client.get("/api/news/video/nonexistent")
    assert response.status_code == 404

def test_get_video_detail(client, db_session):
    from database import Video, Channel

    # 重複エラーを防ぐためチェックまたは一意なIDを使う
    # conftestで毎回クリアされている前提だが、念のため
    channel = Channel(channel_id="UC_DETAIL", name="Detail Channel", url="http://detail.com")
    db_session.add(channel)
    db_session.commit()

    video = Video(
        youtube_id="vid_detail",
        title="Detail Video",
        channel_id="UC_DETAIL",
        published_at=datetime.utcnow(),
        status="processed",
        summary="Summary text.",
        transcript="Full transcript"
    )
    db_session.add(video)
    db_session.commit()

    response = client.get("/api/news/video/vid_detail")
    assert response.status_code == 200
    assert response.json()["youtube_id"] == "vid_detail"
    assert response.json()["transcript"] == "Full transcript"
