import os
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeClient:
    def __init__(self, api_key: str):
        self.youtube = build(
            "youtube", "v3", developerKey=api_key, static_discovery=False
        )

    def get_channel_id(self, handle: str) -> str:
        """ハンドル名からチャンネルIDを取得する"""
        request = self.youtube.channels().list(part="id", forHandle=handle)
        response = request.execute()
        items = response.get("items", [])
        if not items:
            raise Exception(f"Channel not found for handle: {handle}")
        return items[0]["id"]

    def search_news_videos(self, channel_id: str):
        """特定のチャンネルからニュース動画を検索する"""
        # 今日の日付 m/d 形式 (ゼロ埋めなし)
        now = datetime.now()
        target_date = f"{now.month}/{now.day}"
        # ANNnewsCH の形式に合わせる
        search_query = f"【ライブ】{target_date}"

        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            q=search_query,
            type="video",
            order="date",
            maxResults=10,
        )
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            title = item["snippet"]["title"]
            print(f"Checking title: {title}") # Debug
            # タイトルが「【ライブ】mm/dd」を含むものに絞り込む
            if search_query in title:
                videos.append(
                    {
                        "id": item["id"]["videoId"],
                        "title": title,
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    }
                )

        return videos

    def get_transcript(self, video_id: str) -> Optional[str]:
        """動画の字幕を取得する"""
        try:
            # v1.2.3 ではインスタンスの fetch メソッドを使用する
            transcript_list = YouTubeTranscriptApi().fetch(
                video_id, languages=["ja", "en"]
            )
            return " ".join([t.text for t in transcript_list])
        except Exception as e:
            print(f"Error fetching transcript for {video_id}: {str(e)}")
            return None


if __name__ == "__main__":
    # テスト用
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    client = YouTubeClient(api_key)
    try:
        ann_id = client.get_channel_id("@ANNnewsCH")
        print(f"ANN Channel ID: {ann_id}")
        videos = client.search_news_videos(ann_id)
        print(f"Found {len(videos)} videos:")
        for v in videos:
            print(f"- {v['title']} ({v['id']})")
            # transcript = client.get_transcript(v['id'])
            # print(f"  Transcript: {transcript[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
