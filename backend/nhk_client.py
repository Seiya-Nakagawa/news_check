"""
NHKニュースRSSフィードからニュース記事を取得するクライアント
"""

import random
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import feedparser
import requests
from bs4 import BeautifulSoup


class NHKNewsClient:
    """NHKニュースRSSフィードからニュース記事を取得するクライアント"""

    # NHK RSSフィードのURL一覧
    RSS_FEEDS = {
        "main": "https://www3.nhk.or.jp/rss/news/cat0.xml",  # 主要ニュース
        "society": "https://www3.nhk.or.jp/rss/news/cat1.xml",  # 社会
        "science": "https://www3.nhk.or.jp/rss/news/cat3.xml",  # 科学・文化
        "politics": "https://www3.nhk.or.jp/rss/news/cat4.xml",  # 政治
        "business": "https://www3.nhk.or.jp/rss/news/cat5.xml",  # ビジネス
        "international": "https://www3.nhk.or.jp/rss/news/cat6.xml",  # 国際
        "sports": "https://www3.nhk.or.jp/rss/news/cat7.xml",  # スポーツ
    }

    def __init__(self):
        """クライアントの初期化"""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch_news(
        self, categories: Optional[List[str]] = None, max_articles: int = 20
    ) -> List[Dict]:
        """
        NHK RSSフィードからニュース記事を取得する

        Args:
            categories: 取得するカテゴリのリスト (デフォルトは主要ニュースのみ)
            max_articles: 取得する最大記事数

        Returns:
            ニュース記事のリスト
        """
        if categories is None:
            categories = ["main"]

        articles = []
        seen_urls = set()

        for category in categories:
            if category not in self.RSS_FEEDS:
                print(f"Unknown category: {category}")
                continue

            rss_url = self.RSS_FEEDS[category]
            print(f"Fetching RSS feed: {rss_url}")

            try:
                feed = feedparser.parse(rss_url)

                if not feed.entries:
                    print(f"No entries found in RSS feed for category: {category}")
                    continue

                for entry in feed.entries:
                    link = entry.get("link", "")

                    # 重複チェック
                    if link in seen_urls:
                        continue
                    seen_urls.add(link)

                    # 記事IDをURLから抽出 (例: k10015031561000)
                    article_id = self._extract_article_id(link)
                    if not article_id:
                        continue

                    # 公開日時をパース
                    published_at = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                        # タイムゾーンを付与 (JST)
                        jst = timezone(timedelta(hours=9))
                        published_at = published_at.replace(tzinfo=jst)

                    articles.append(
                        {
                            "article_id": article_id,
                            "title": entry.get("title", ""),
                            "link": link,
                            "description": entry.get("description", ""),
                            "published_at": published_at,
                            "category": category,
                            "source": "NHK",
                        }
                    )

                    if len(articles) >= max_articles:
                        break

            except Exception as e:
                print(f"Error fetching RSS feed {rss_url}: {e}")
                continue

        print(f"Found {len(articles)} news articles from NHK RSS feed")
        return articles

    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        記事ページから本文を取得する

        Args:
            url: 記事のURL

        Returns:
            記事本文のテキスト
        """
        try:
            # リクエスト間隔を空ける
            time.sleep(random.uniform(1.0, 3.0))

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # NHKニュースの記事本文を取得
            # 複数のセレクタを試す
            content_selectors = [
                "div._1i1d7sh0",  # 最新のNHK ONEレイアウト
                "div.content--detail-body",
                "div.body-content",
                "article",
                "div.content--summary",
            ]

            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # 不要な要素を削除
                    for unwanted in content_div.select(
                        "script, style, nav, footer, .related"
                    ):
                        unwanted.decompose()

                    text = content_div.get_text(separator="\n", strip=True)
                    if len(text) > 100:  # 十分な長さのテキストが取得できた場合
                        return text

            # フォールバック: 全体からテキストを抽出
            return None

        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
            return None

    def _extract_article_id(self, url: str) -> Optional[str]:
        """URLから記事IDを抽出する"""
        import re

        # 例: http://www3.nhk.or.jp/news/html/20260121/k10015031561000.html
        match = re.search(r"(k\d+)\.html", url)
        if match:
            return match.group(1)

        # URLをハッシュ化してIDとして使用
        import hashlib

        return hashlib.md5(url.encode()).hexdigest()[:16]
