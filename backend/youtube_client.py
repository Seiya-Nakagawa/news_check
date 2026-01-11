import os
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
        # ANNnewsCH の形式「【ライブ】」を含む動画を検索
        # 日付指定を外して、直近のニュースも取得できるようにする
        search_query = "【ライブ】"

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
        seen_ids = set()
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            if video_id not in seen_ids:
                videos.append(
                    {
                        "video_id": video_id,
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                    }
                )
                seen_ids.add(video_id)

        return videos

    def get_transcript(self, video_id: str) -> Optional[str]:
        """動画の字幕を取得する"""
        try:
            # Cookieファイルの確認
            cookies = "/app/cookies.txt"
            if not os.path.exists(cookies):
                cookies = None
            else:
                print(f"DEBUG: Using cookies from {cookies}")

            # 利用可能な字幕一覧を取得
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookies)

            # 日本語字幕を優先的に取得
            try:
                transcript = transcript_list.find_transcript(["ja"])
            except:
                # 日本語がない場合は自動翻訳を試みる
                try:
                    transcript = transcript_list.find_generated_transcript(["ja"])
                except:
                    # どちらもない場合は英語などを探す
                    try:
                        transcript = transcript_list.find_transcript(["en"])
                    except:
                        print(f"No suitable transcript found for {video_id}")
                        return None

            data = transcript.fetch()
            return " ".join([t["text"] for t in data])

        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching transcript for {video_id}: {error_msg}")

            # IPブロックの場合の特別メッセージ
            if "YouTube is blocking requests from your IP" in error_msg or "IpBlocked" in error_msg:
                print("CRITICAL: YouTube is blocking this IP. Cookies might be expired or invalid.")

            return None
