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
            maxResults=20,
        )
        response = request.execute()

        import re

        # "【ライブ】" + "m/d" または "mm/dd" のパターン
        title_pattern = re.compile(r"【ライブ】\d{1,2}/\d{1,2}")

        videos = []
        seen_ids = set()
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            if video_id in seen_ids:
                continue

            title = item["snippet"]["title"]
            print(f"Checking title: {title}")  # Debug

            # タイトルのチェック
            # 1. 除外キーワードが含まれていないか確認
            exclude_keywords = [
                "街頭演説",
                "公明党",
                "維新",
                "共産",
                "立憲",
                "国民民主",
                "れいわ",
                "社民",
                "参政",
                "自民",
            ]
            if any(k in title for k in exclude_keywords):
                print(f"Skipping (excluded keyword): {title}")
                continue

            # 2. 条件:
            # - "【ライブ】m/d" の形式を含む (日付が入っている)
            # - または "ニュースまとめ" が含まれている (定時ニュースの場合)
            if title_pattern.search(title) or "ニュースまとめ" in title:
                videos.append(
                    {
                        "id": video_id,
                        "title": title,
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
            # Dockerコンテナ内での絶対パス
            cookies = "/app/cookies.txt"
            if os.path.exists(cookies):
                print(f"DEBUG: Found cookies at {cookies}")
            else:
                print(f"DEBUG: Cookies NOT found at {cookies}")
                cookies = None

            # 利用可能な字幕一覧を取得
            if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookies)
                    print(f"DEBUG: Passed cookies to list_transcripts: {cookies is not None}")
                except Exception as e:
                    print(f"DEBUG: YouTubeTranscriptApi.list_transcripts error for {video_id}: {str(e)}")
                    # Fallback to instance-based API if list_transcripts fails unexpectedly
                    api = YouTubeTranscriptApi()
                    transcript_list = api.list(video_id, cookies=cookies)
                    print(f"DEBUG: Fallback to instance-based API. Passed cookies: {cookies is not None}")
            else:
                # Fallback for instance-based API
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id, cookies=cookies)
                print(f"DEBUG: Using instance-based API. Passed cookies: {cookies is not None}")

            # デバッグ: 利用可能な字幕をすべて表示
            print(f"Available transcripts for {video_id}:")
            for t in transcript_list:
                print(
                    f" - {t.language_code} ({t.language}) [Generated: {t.is_generated}]"
                )

            # 日本語の手動作成 -> 日本語の自動生成 -> 英語 の順で探す
            transcript = None
            try:
                transcript = transcript_list.find_transcript(["ja"])
            except:
                try:
                    transcript = transcript_list.find_generated_transcript(["ja"])
                except:
                    try:
                        transcript = transcript_list.find_transcript(["en"])
                    except:
                        pass

            if transcript:
                # fetchして結合
                try:
                    result = transcript.fetch()
                except Exception as e:
                    print(f"Direct fetch failed: {e}. Trying translation strategy.")
                    try:
                        # 翻訳字幕として取得を試みる (自動生成字幕の取得エラー回避策)
                        result = transcript.translate("ja").fetch()
                    except:
                        try:
                            result = transcript.translate("en").fetch()
                        except Exception as e2:
                            print(f"Translation fetch also failed: {e2}")
                            raise e

                text_list = []
                for t in result:
                    if isinstance(t, dict):
                        text_list.append(t.get("text", ""))
                    elif hasattr(t, "text"):
                        text_list.append(t.text)
                    else:
                        print(f"Unknown transcript item type: {type(t)}")

                return " ".join(text_list)
            else:
                print(f"No suitable transcript found for {video_id}")
                return None

        except Exception as e:
            print(f"Error fetching transcript for {video_id}: [{type(e).__name__}] {str(e)}")
            import traceback
            traceback.print_exc()
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
