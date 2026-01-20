import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeClient:
    def __init__(self, api_key: str = None):
        """
        YouTubeクライアントの初期化
        api_key: 現在は使用していないが、互換性のために残している
        """
        pass

    def search_news_videos(self, channel_id: str):
        """RSSフィードから最新のニュース動画を取得する (APIクォータ消費ゼロ)"""
        # YouTube公式RSSフィードのURL
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        # RSSフィードを取得
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"No entries found in RSS feed for channel: {channel_id}")
            return []

        videos = []
        seen_ids = set()

        # 日本時間 (JST) で現在時刻を取得
        jst = timezone(timedelta(hours=9))
        now = datetime.now(jst)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        for entry in feed.entries:
            # 動画IDを抽出 (yt:videoId タグから)
            video_id = entry.yt_videoid if hasattr(entry, "yt_videoid") else None
            if not video_id:
                continue

            title = entry.title

            # #shorts は除外する
            if "#shorts" in title.lower():
                continue

            # タイトルが「【ライブ】mm/dd 朝ニュースまとめ」「【ライブ】mm/dd 昼ニュースまとめ」「【ライブ】mm/dd 夜ニュースまとめ」のいずれかに一致するか確認
            if not re.match(
                r"^【ライブ】\d{1,2}/\d{1,2}\s+(朝|昼|夜)ニュースまとめ", title
            ):
                continue

            # 未来の日付のニュースを除外する (タイトルに含まれる日付を確認)
            date_match = re.search(r"(\d{1,2})/(\d{1,2})", title)
            if date_match:
                try:
                    title_month = int(date_match.group(1))
                    title_day = int(date_match.group(2))

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
                    if title_date > today:
                        continue
                except (ValueError, OverflowError):
                    pass

            # 重複チェック
            if video_id not in seen_ids:
                # サムネイルURLを取得 (media:group > media:thumbnail)
                thumbnail_url = None
                if hasattr(entry, "media_thumbnail"):
                    thumbnail_url = (
                        entry.media_thumbnail[0]["url"]
                        if entry.media_thumbnail
                        else None
                    )

                # 公開日時を取得
                published_at = entry.published if hasattr(entry, "published") else None

                # 説明文を取得
                description = entry.summary if hasattr(entry, "summary") else ""

                videos.append(
                    {
                        "video_id": video_id,
                        "title": title,
                        "description": description,
                        "published_at": published_at,
                        "thumbnail": thumbnail_url,
                    }
                )
                seen_ids.add(video_id)

        print(f"Found {len(videos)} news videos from RSS feed")
        return videos

    def get_transcript(self, video_id: str) -> Optional[str]:
        """動画の字幕を取得する"""
        try:
            # 429回避のための待機 (ランダム化)
            sleep_time = random.uniform(5.0, 15.0)  # さらに延長
            print(f"DEBUG: Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

            # v1.2.3: requests.Sessionを使用してクッキーとUser-Agentを適用
            import http.cookiejar

            import requests

            session = requests.Session()
            # ランダムなUser-Agentを選択してブロックを回避しやすくする
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            ]
            ua = random.choice(user_agents)
            session.headers.update({"User-Agent": ua})
            print(f"DEBUG: Using User-Agent: {ua}")

            cookies_path = "/app/cookies.txt"
            if os.path.exists(cookies_path):
                print(f"DEBUG: Loading cookies from {cookies_path}")
                try:
                    cj = http.cookiejar.MozillaCookieJar(cookies_path)
                    cj.load(ignore_discard=True, ignore_expires=True)
                    session.cookies = cj
                except Exception as e:
                    print(f"DEBUG: Failed to load cookies: {e}")
            else:
                print("DEBUG: No cookies.txt found, proceeding without authentication")

            api = YouTubeTranscriptApi(http_client=session)

            # 利用可能な字幕一覧を取得
            transcript_list = api.list(video_id)

            # 字幕の選択ロジックを強化
            try:
                # 1. 日本語字幕を優先 (手動・自動生成問わず)
                transcript = transcript_list.find_transcript(["ja"])
            except Exception:
                try:
                    # 2. 他の言語（英語など）があれば日本語に翻訳
                    transcript = transcript_list.find_transcript(["en"]).translate("ja")
                except Exception:
                    # 3. それでもダメなら、なんでもいいので日本語に翻訳を試みる
                    try:
                        transcript = list(
                            transcript_list._manually_created_transcripts.values()
                        )[0].translate("ja")
                    except Exception:
                        try:
                            transcript = list(
                                transcript_list._generated_transcripts.values()
                            )[0].translate("ja")
                        except Exception:
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
