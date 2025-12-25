import os
from datetime import datetime

from googleapiclient.discovery import build


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

    def search_news_videos(self, channel_id: str, days_back: int = 1):
        """特定のチャンネルからニュース動画を検索する"""
        # 今日の日付 mm/dd 形式
        target_date = (datetime.now()).strftime("%m/%d")
        search_query = f"【ライブ】{target_date}"

        # 直近の動画を検索
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
            # タイトルが「【ライブ】mm/dd」で始まるものに絞り込む
            if title.startswith(search_query):
                videos.append(
                    {
                        "id": item["id"]["videoId"],
                        "title": title,
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    }
                )

        return videos


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
    except Exception as e:
        print(f"Error: {e}")
