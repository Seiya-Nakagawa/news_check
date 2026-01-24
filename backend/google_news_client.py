"""
Google News RSSクライアント

Google News RSSフィードからニュースを取得するモジュール。
スクレイピング不要で、RSSフィードから直接タイトル・概要・リンク・日時を取得する。
"""

import html
import re
from datetime import datetime
from typing import List, Dict, Optional

import feedparser
import requests


class GoogleNewsClient:
    """Google News RSSフィードからニュースを取得するクライアント"""

    # メインフィード（日本語・日本向け）
    BASE_URL = "https://news.google.com/rss"
    DEFAULT_PARAMS = "?hl=ja&gl=JP&ceid=JP:ja"

    # トピック別フィードのID
    TOPICS = {
        "top": None,  # トップニュース（デフォルト）
        "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtcGhHZ0pLVUNnQVAB",
        "japan": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNRE5qWlRRU0FtcGhLQUFQAQ",
        "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtcGhHZ0pLVUNnQVAB",
        "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcGhHZ0pLVUNnQVAB",
        "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtcGhHZ0pLVUNnQVAB",
        "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtcGhHZ0pLVUNnQVAB",
        "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtcGhHZ0pLVUNnQVAB",
        "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtcGhLQUFQAQ",
    }

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout: HTTPリクエストのタイムアウト秒数
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })

    def _build_url(self, topic: Optional[str] = None) -> str:
        """フィードURLを構築する"""
        if topic and topic in self.TOPICS and self.TOPICS[topic]:
            return f"{self.BASE_URL}/topics/{self.TOPICS[topic]}{self.DEFAULT_PARAMS}"
        return f"{self.BASE_URL}{self.DEFAULT_PARAMS}"

    def _clean_html(self, text: str) -> str:
        """HTMLタグを除去し、エンティティをデコードする"""
        # HTMLエンティティのデコード
        text = html.unescape(text)
        # HTMLタグの除去
        text = re.sub(r"<[^>]+>", "", text)
        # 余分な空白の正規化
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """RSS日付文字列をdatetimeに変換"""
        try:
            # feedparserがパースした構造体からdatetimeを生成
            from time import mktime
            return datetime.fromtimestamp(mktime(feedparser._parse_date(date_str)))
        except Exception:
            return None

    def fetch_news(
        self,
        topics: Optional[List[str]] = None,
        max_articles: int = 20
    ) -> List[Dict]:
        """
        Google News RSSからニュースを取得する

        Args:
            topics: 取得するトピックのリスト（None の場合はトップニュース）
            max_articles: 取得する最大記事数

        Returns:
            記事情報のリスト
        """
        if topics is None:
            topics = ["top"]

        all_articles = []
        seen_links = set()

        for topic in topics:
            url = self._build_url(topic)
            print(f"Fetching Google News RSS: {url}")

            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                feed = feedparser.parse(response.content)

                print(f"Found {len(feed.entries)} articles from topic '{topic}'")

                for entry in feed.entries:
                    # 重複チェック
                    if entry.link in seen_links:
                        continue
                    seen_links.add(entry.link)

                    # 記事IDの生成（リンクのハッシュ）
                    article_id = f"gn_{hash(entry.link) & 0xFFFFFFFF:08x}"

                    # descriptionからテキストを抽出
                    description = ""
                    if hasattr(entry, "summary"):
                        description = self._clean_html(entry.summary)

                    # 公開日時のパース
                    published_at = None
                    if hasattr(entry, "published"):
                        published_at = self._parse_date(entry.published)

                    article = {
                        "article_id": article_id,
                        "title": self._clean_html(entry.title),
                        "link": entry.link,
                        "description": description,
                        "published_at": published_at,
                        "source": "Google News",
                        "topic": topic,
                    }
                    all_articles.append(article)

                    if len(all_articles) >= max_articles:
                        break

            except Exception as e:
                print(f"Error fetching Google News RSS ({topic}): {e}")
                continue

            if len(all_articles) >= max_articles:
                break

        return all_articles[:max_articles]


# テスト用
if __name__ == "__main__":
    client = GoogleNewsClient()
    articles = client.fetch_news(topics=["top"], max_articles=5)
    for i, article in enumerate(articles, 1):
        print(f"\n--- Article {i} ---")
        print(f"Title: {article['title']}")
        print(f"Description: {article['description'][:100]}...")
        print(f"Link: {article['link']}")
        print(f"Published: {article['published_at']}")
