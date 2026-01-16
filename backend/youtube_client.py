import random
import re
import time
from datetime import datetime, timedelta, timezone
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

    def get_video_description(self, video_id: str) -> Optional[str]:
        """動画の説明欄を取得する"""
        try:
            request = self.youtube.videos().list(part="snippet", id=video_id)
            response = request.execute()
            items = response.get("items", [])
            if items:
                return items[0]["snippet"]["description"]
            return None
        except Exception as e:
            print(f"Error fetching description for {video_id}: {e}")
            return None

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
            maxResults=15,
        )
        response = request.execute()

        videos = []
        seen_ids = set()
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]

            # #shorts は除外する
            if "#shorts" in title.lower():
                continue

            # タイトルが「【ライブ】mm/dd」の形式で始まっているか確認する
            # 例: 【ライブ】1/11 ANNニュース...
            if not re.match(r"^【ライブ】\d{1,2}/\d{1,2}", title):
                continue

            # 配信状況を確認し、アーカイブ（VOD）以外は除外する
            # liveBroadcastContent: 'upcoming', 'live', 'none'
            live_broadcast_content = item["snippet"].get("liveBroadcastContent", "none")
            if live_broadcast_content != "none":
                # 'upcoming' (配信予定) や 'live' (配信中) は除外
                continue

            # 未来の日付のニュースを除外する (タイトルに含まれる日付を確認)
            # 例: 今が 1/11 なのにタイトルが 1/12 の場合は除外
            date_match = re.search(r"(\d{1,2})/(\d{1,2})", title)
            if date_match:
                try:
                    title_month = int(date_match.group(1))
                    title_day = int(date_match.group(2))

                    # 日本時間 (JST) で現在時刻を取得
                    jst = timezone(timedelta(hours=9))
                    now = datetime.now(jst)

                    # タイトルの日付を現在と同じ年として仮定
                    title_date = now.replace(
                        month=title_month,
                        day=title_day,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )

                    # 年末年始の境界を考慮
                    if title_month == 12 and now.month == 1:
                        title_date = title_date.replace(year=now.year - 1)
                    elif title_month == 1 and now.month == 12:
                        title_date = title_date.replace(year=now.year + 1)

                    # 日付のみで比較（今日より後の日付ならスキップ）
                    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    if title_date > today:
                        continue
                except (ValueError, OverflowError):
                    # 不正な日付形式などは無視して次へ
                    pass

            if video_id not in seen_ids:
                videos.append(
                    {
                        "video_id": video_id,
                        "title": title,
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
            # 429回避のための待機 (ランダム化)
            sleep_time = random.uniform(5.0, 10.0)
            print(f"DEBUG: Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

            # v1.2.3: 匿名アクセスを使用 (Cookiesが無効な可能性があるため)
            api = YouTubeTranscriptApi()

            # 利用可能な字幕一覧を取得
            transcript_list = api.list(video_id)

            # 字幕の選択ロジックを強化
            try:
                # 1. 日本語字幕を優先 (手動・自動生成問わず)
                transcript = transcript_list.find_transcript(["ja"])
            except:
                try:
                    # 2. 他の言語（英語など）があれば日本語に翻訳
                    transcript = transcript_list.find_transcript(["en"]).translate("ja")
                except:
                    # 3. それでもダメなら、なんでもいいので日本語に翻訳を試みる
                    try:
                        transcript = list(
                            transcript_list._manually_created_transcripts.values()
                        )[0].translate("ja")
                    except:
                        try:
                            transcript = list(
                                transcript_list._generated_transcripts.values()
                            )[0].translate("ja")
                        except:
                            print(
                                f"No suitable transcript or translatable captions found for {video_id}"
                            )
                            return None

            print(
                f"DEBUG: Found transcript for {video_id} (Language: {transcript.language}, Generated: {transcript.is_generated})"
            )
            data = transcript.fetch()
            return " ".join([t.text for t in data])

        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching transcript for {video_id}: {error_msg}")

            # 字幕が無効化されている場合は、説明文にフォールバックせずにNoneを返す
            if (
                "Subtitles are disabled" in error_msg
                or "TranscriptsDisabled" in error_msg
            ):
                print(f"Subtitles are disabled for video: {video_id}. Skipping.")
                return None

            # IPブロックの場合の特別メッセージ
            if (
                "YouTube is blocking requests from your IP" in error_msg
                or "IpBlocked" in error_msg
            ):
                print(
                    "CRITICAL: YouTube is blocking this IP. Cookies might be expired or invalid."
                )
                return None

            # その他のエラーの場合もNoneを返す（説明文へのフォールバックを削除）
            print(f"Could not fetch transcript for {video_id}. Skipping.")
            return None
